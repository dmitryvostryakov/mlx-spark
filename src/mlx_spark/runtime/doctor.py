"""Small read-only inventory with no network discovery or host identifiers."""

from datetime import datetime, timezone
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath


_MIB = 1024 * 1024
_V1_UNLIMITED_MIN = 1 << 60
_DGX_RELEASE = Path("/etc/dgx-release")
_CUDNN_HEADERS = (
    Path("/usr/include/cudnn_version.h"),
    Path("/usr/include/cudnn_version_v9.h"),
    Path("/usr/include/aarch64-linux-gnu/cudnn_version.h"),
    Path("/usr/include/aarch64-linux-gnu/cudnn_version_v9.h"),
    Path("/usr/local/cuda/include/cudnn_version.h"),
)


def _read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


def _run_capture(args, stdout_limit=20000):
    if not shutil.which(args[0]):
        return {"status": "unavailable"}
    try:
        process = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        return {
            "status": "ok" if process.returncode == 0 else "error",
            "returncode": process.returncode,
            "stdout": process.stdout[:stdout_limit].strip(),
            "stderr": process.stderr[:2000].strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "error", "error": type(exc).__name__}


def _os_release():
    text = _read_text(Path("/etc/os-release"))
    if text is None:
        return {"status": "unavailable"}
    result = {"status": "ok"}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"ID", "VERSION_ID", "PRETTY_NAME"}:
            result[key] = value.strip('"')
    return result


def _parse_dgx_release(text):
    allowed = {
        "DGX_PRETTY_NAME": "pretty_name",
        "DGX_SWBUILD_VERSION": "swbuild_version",
        "DGX_OTA_VERSION": "ota_version",
    }
    result = {"status": "ok"}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        output_key = allowed.get(key.strip())
        if output_key is None:
            continue
        value = value.strip().strip('"').strip("'")
        if output_key == "pretty_name":
            if not re.fullmatch(r"[A-Za-z0-9 ._()+-]{1,80}", value):
                continue
        elif not re.fullmatch(r"[A-Za-z0-9._+~:-]{1,80}", value):
            continue
        result[output_key] = value
    if len(result) == 1:
        return {"status": "unknown", "reason": "no_safe_version_fields"}
    return result


def _dgx_os():
    text = _read_text(_DGX_RELEASE)
    if text is None:
        return {"status": "unavailable", "reason": "dgx_release_not_found"}
    return _parse_dgx_release(text)


def _memory():
    text = _read_text(Path("/proc/meminfo"))
    if text is None:
        return {"status": "unavailable"}
    result = {"status": "ok"}
    for line in text.splitlines():
        key, _, value = line.partition(":")
        if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
            try:
                result[key + "_bytes"] = int(value.strip().split()[0]) * 1024
            except (IndexError, ValueError):
                result[key + "_bytes"] = None
    return result


def _mountinfo_path(value):
    for escaped, literal in ((r"\040", " "), (r"\011", "\t"), (r"\012", "\n"), (r"\134", "\\")):
        value = value.replace(escaped, literal)
    return value


def _path_parts(value):
    parts = tuple(part for part in PurePosixPath(value).parts if part not in {"/", ""})
    if any(part in {".", ".."} for part in parts):
        return None
    return parts


def _resolve_cgroup_context(cgroup_text, mountinfo_text):
    memberships = []
    for line in cgroup_text.splitlines():
        hierarchy, separator, remainder = line.partition(":")
        if not separator:
            continue
        controllers, separator, member_path = remainder.partition(":")
        if not separator:
            continue
        controller_set = set(filter(None, controllers.split(",")))
        if hierarchy == "0" and not controller_set:
            memberships.append((2, member_path))
        elif "memory" in controller_set:
            memberships.append((1, member_path))

    mounts = []
    for line in mountinfo_text.splitlines():
        left, separator, right = line.partition(" - ")
        if not separator:
            continue
        left_fields = left.split()
        right_fields = right.split()
        if len(left_fields) < 6 or len(right_fields) < 3:
            continue
        filesystem = right_fields[0]
        controller_fields = ",".join((left_fields[5], right_fields[1], right_fields[2]))
        controllers = set(controller_fields.split(","))
        if filesystem == "cgroup2":
            version = 2
        elif filesystem == "cgroup" and "memory" in controllers:
            version = 1
        else:
            continue
        mounts.append(
            {
                "version": version,
                "root_parts": _path_parts(_mountinfo_path(left_fields[3])),
                "mount_point": Path(_mountinfo_path(left_fields[4])),
            }
        )

    # A hybrid hierarchy can expose a unified v2 membership while the memory
    # controller is still explicitly attached to v1. Prefer that explicit
    # membership so a finite v1 limit cannot be mistaken for an unbounded v2
    # hierarchy with no memory controller files.
    for version in (1, 2):
        for membership_version, member_path in memberships:
            if membership_version != version:
                continue
            member_parts = _path_parts(member_path)
            if member_parts is None:
                continue
            for mount in mounts:
                if mount["version"] != version or mount["root_parts"] is None:
                    continue
                root_parts = mount["root_parts"]
                if member_path == "/":
                    relative_parts = ()
                elif member_parts[: len(root_parts)] == root_parts:
                    relative_parts = member_parts[len(root_parts) :]
                elif not root_parts:
                    relative_parts = member_parts
                else:
                    continue
                return {
                    "version": version,
                    "mount_point": mount["mount_point"],
                    "relative_parts": relative_parts,
                }
    return None


def _parse_cgroup_limit(text, version):
    value = text.strip()
    if value == "max":
        return None
    parsed = int(value)
    if version == 1 and parsed >= _V1_UNLIMITED_MIN:
        return None
    return parsed


def _cgroup_memory_from_hierarchy(version, mount_point, relative_parts):
    if version == 2:
        limit_name, current_name = "memory.max", "memory.current"
    elif version == 1:
        limit_name, current_name = "memory.limit_in_bytes", "memory.usage_in_bytes"
    else:
        return {"status": "unknown", "reason": "unsupported_cgroup_version"}

    levels = [mount_point]
    current_path = mount_point
    for part in relative_parts:
        if part in {"", ".", ".."} or "/" in part:
            return {"status": "unknown", "reason": "invalid_cgroup_membership"}
        current_path = current_path / part
        levels.append(current_path)

    finite = []
    for level in levels:
        limit_text = _read_text(level / limit_name)
        current_text = _read_text(level / current_name)
        if limit_text is None and current_text is None:
            continue
        if limit_text is None:
            return {"status": "unknown", "reason": "cgroup_limit_unreadable"}
        try:
            limit = _parse_cgroup_limit(limit_text, version)
        except ValueError:
            return {"status": "unknown", "reason": "invalid_cgroup_limit"}
        if limit is None:
            continue
        if current_text is None:
            return {"status": "unknown", "reason": "cgroup_usage_unreadable"}
        try:
            current = int(current_text.strip())
        except ValueError:
            return {"status": "unknown", "reason": "invalid_cgroup_usage"}
        finite.append((max(0, limit - current), limit, current))

    if not finite:
        return {
            "status": "ok",
            "version": version,
            "limit_bytes": None,
            "current_bytes": None,
            "available_bytes": None,
            "finite_limit_levels": 0,
            "constraint_scope": "current_cgroup_or_ancestor",
        }
    available, limit, current = min(finite, key=lambda item: item[0])
    return {
        "status": "ok",
        "version": version,
        "limit_bytes": limit,
        "current_bytes": current,
        "available_bytes": available,
        "finite_limit_levels": len(finite),
        "constraint_scope": "current_cgroup_or_ancestor",
    }


def _cgroup_memory():
    cgroup_text = _read_text(Path("/proc/self/cgroup"))
    mountinfo_text = _read_text(Path("/proc/self/mountinfo"))
    if cgroup_text is None or mountinfo_text is None:
        return {
            "status": "unavailable",
            "limit_bytes": None,
            "current_bytes": None,
            "available_bytes": None,
        }
    context = _resolve_cgroup_context(cgroup_text, mountinfo_text)
    if context is None:
        return {
            "status": "unknown",
            "limit_bytes": None,
            "current_bytes": None,
            "available_bytes": None,
            "reason": "current_cgroup_mount_not_resolved",
        }
    return _cgroup_memory_from_hierarchy(**context)


def _disk(workdir):
    try:
        usage = shutil.disk_usage(workdir)
    except OSError as exc:
        return {
            "status": "error",
            "scope": "selected_working_filesystem",
            "error": type(exc).__name__,
        }
    return {
        "status": "ok",
        "scope": "selected_working_filesystem",
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


def _mib_to_bytes(value):
    try:
        return int(float(value)) * _MIB
    except ValueError:
        return None


def _parse_gpu_csv(text):
    devices = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = [part.strip() for part in line.split(",", 4)]
        if len(fields) != 5:
            return {
                "status": "unknown",
                "visible_count": None,
                "devices": [],
                "reason": "unexpected_nvidia_smi_csv",
            }
        name, driver, capability, total_mib, free_mib = fields
        devices.append(
            {
                "name": name,
                "driver_version": driver,
                "compute_capability": capability,
                "memory_total_bytes": _mib_to_bytes(total_mib),
                "memory_free_bytes": _mib_to_bytes(free_mib),
            }
        )
    return {"status": "ok", "visible_count": len(devices), "devices": devices}


def _gpu_inventory():
    command = "nvidia-smi"
    if not shutil.which(command):
        return {"status": "unavailable", "visible_count": 0, "devices": []}
    try:
        process = subprocess.run(
            [
                command,
                "--query-gpu=name,driver_version,compute_cap,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "error",
            "visible_count": None,
            "devices": [],
            "error": type(exc).__name__,
        }
    if process.returncode != 0:
        return {
            "status": "error",
            "visible_count": None,
            "devices": [],
            "returncode": process.returncode,
        }
    return _parse_gpu_csv(process.stdout)


def _safe_version_result(captured, parser):
    status = captured.get("status")
    if status == "unavailable":
        return {"status": "unavailable"}
    if status != "ok":
        result = {"status": "error", "reason": "version_command_failed"}
        if isinstance(captured.get("returncode"), int):
            result["returncode"] = captured["returncode"]
        return result
    parsed = parser("\n".join((captured.get("stdout", ""), captured.get("stderr", ""))))
    if parsed is None:
        return {"status": "unknown", "reason": "version_output_not_recognized"}
    return {"status": "ok", **parsed}


def _parse_nvcc_version(text):
    release = re.search(r"\brelease\s+([0-9]+(?:\.[0-9]+)+)", text, re.IGNORECASE)
    if release is None:
        return None
    result = {"version": release.group(1)}
    build = re.search(r"\bV([0-9]+(?:\.[0-9]+)+)", text)
    if build is not None:
        result["build"] = build.group(1)
    return result


def _parse_cmake_version(text):
    match = re.search(r"\bcmake\s+version\s+([0-9]+(?:\.[0-9]+)+)", text, re.IGNORECASE)
    if match is None:
        return None
    return {"version": match.group(1)}


def _parse_compiler_version(text):
    for vendor, pattern in (
        ("apple_clang", r"\bApple\s+clang\s+version\s+([0-9]+(?:\.[0-9]+)+)"),
        ("clang", r"\bclang\s+version\s+([0-9]+(?:\.[0-9]+)+)"),
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match is not None:
            return {"vendor": vendor, "version": match.group(1)}

    first_line = text.splitlines()[0] if text.splitlines() else ""
    if re.search(r"\b(?:gcc|g\+\+|c\+\+)\b|Free Software Foundation", text, re.IGNORECASE):
        versions = re.findall(r"\b[0-9]+\.[0-9]+(?:\.[0-9]+)?\b", first_line)
        if versions:
            return {"vendor": "gcc", "version": versions[-1]}
    return None


def _nvcc_inventory():
    return _safe_version_result(_run_capture(["nvcc", "--version"]), _parse_nvcc_version)


def _compiler_inventory():
    return _safe_version_result(_run_capture(["c++", "--version"]), _parse_compiler_version)


def _cmake_inventory():
    return _safe_version_result(_run_capture(["cmake", "--version"]), _parse_cmake_version)


def _parse_cudnn_header(text):
    values = {}
    for part in ("MAJOR", "MINOR", "PATCHLEVEL"):
        match = re.search(rf"^\s*#\s*define\s+CUDNN_{part}\s+(\d+)\s*$", text, re.MULTILINE)
        if match is None:
            return None
        values[part] = int(match.group(1))
    return f"{values['MAJOR']}.{values['MINOR']}.{values['PATCHLEVEL']}"


def _cudnn_inventory():
    for header in _CUDNN_HEADERS:
        text = _read_text(header)
        if text is None:
            continue
        version = _parse_cudnn_header(text)
        if version is not None:
            return {"status": "ok", "version": version, "source": "version_header"}

    packages = _run_capture(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n", "libcudnn*"])
    if packages.get("status") == "ok":
        found = []
        for line in packages.get("stdout", "").splitlines():
            name, separator, version = line.partition("\t")
            if separator and name.startswith("libcudnn"):
                found.append({"name": name, "version": version})
        if found:
            return {"status": "ok", "version": None, "source": "package_metadata", "packages": found}

    libraries = _run_capture(["ldconfig", "-p"], stdout_limit=1000000)
    if libraries.get("status") == "ok":
        sonames = sorted(set(re.findall(r"\blibcudnn[^\s]*\.so(?:\.\d+)*", libraries.get("stdout", ""))))
        if sonames:
            return {"status": "present", "version": None, "source": "linker_cache", "sonames": sonames}

    return {
        "status": "unknown",
        "version": None,
        "reason": "not_found_in_standard_read_only_probes",
    }


def inventory(workdir="."):
    return {
        "schema_version": 2,
        "kind": "host_inventory_only",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "system": platform.system(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "libc": platform.libc_ver(),
        "os_release": _os_release(),
        "dgx_os": _dgx_os(),
        "memory": _memory(),
        "cgroup_memory": _cgroup_memory(),
        "disk": _disk(workdir),
        "gpu": _gpu_inventory(),
        "nvcc": _nvcc_inventory(),
        "host_compiler": _compiler_inventory(),
        "cmake": _cmake_inventory(),
        "cudnn": _cudnn_inventory(),
        "hardware_validation": "NOT_PERFORMED",
        "sensitive_fields_omitted": [
            "hostname",
            "IP",
            "MAC",
            "UUID",
            "serial",
            "username",
            "home_path",
            "mount_path",
            "environment",
            "network_interfaces",
            "process_list",
        ],
        "warnings": [
            "nvidia-smi memory is not a UMA capacity guarantee",
            "No driver, toolkit, compiler, or cuDNN compatibility is inferred from version strings alone",
            "Disk values cover only the filesystem containing the selected working directory",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), indent=2, ensure_ascii=False))

import json
import subprocess
import sys
from pathlib import Path

from mlx_spark.runtime import doctor


ROOT = Path(__file__).resolve().parents[1]


def test_inventory_exposes_anonymized_budget_inputs(tmp_path):
    result = doctor.inventory(workdir=tmp_path)
    assert result["kind"] == "host_inventory_only"
    assert result["hardware_validation"] == "NOT_PERFORMED"
    assert set(result) >= {
        "memory",
        "cgroup_memory",
        "disk",
        "dgx_os",
        "gpu",
        "nvcc",
        "host_compiler",
        "cmake",
        "cudnn",
    }
    assert result["disk"]["scope"] == "selected_working_filesystem"
    assert result["disk"]["free_bytes"] <= result["disk"]["total_bytes"]
    rendered = json.dumps(result)
    assert str(tmp_path) not in rendered
    assert "hardware_validation" in rendered


def test_gpu_csv_is_structured_without_raw_identifiers():
    result = doctor._parse_gpu_csv("NVIDIA GB10, 580.95.05, 12.1, 121864, 120000")
    assert result == {
        "status": "ok",
        "visible_count": 1,
        "devices": [
            {
                "name": "NVIDIA GB10",
                "driver_version": "580.95.05",
                "compute_capability": "12.1",
                "memory_total_bytes": 121864 * 1024 * 1024,
                "memory_free_bytes": 120000 * 1024 * 1024,
            }
        ],
    }
    assert "uuid" not in json.dumps(result).lower()


def test_cudnn_header_version_parser():
    header = """
    #define CUDNN_MAJOR 9
    #define CUDNN_MINOR 8
    #define CUDNN_PATCHLEVEL 0
    """
    assert doctor._parse_cudnn_header(header) == "9.8.0"
    assert doctor._parse_cudnn_header("#define CUDNN_MAJOR 9") is None


def test_dgx_release_whitelists_versions_and_omits_serial():
    release = """
    DGX_PRETTY_NAME="DGX OS 7"
    DGX_SWBUILD_VERSION="7.3.0"
    DGX_OTA_VERSION="7.3.1"
    DGX_SERIAL_NUMBER="secret-serial"
    """
    result = doctor._parse_dgx_release(release)
    assert result == {
        "status": "ok",
        "pretty_name": "DGX OS 7",
        "swbuild_version": "7.3.0",
        "ota_version": "7.3.1",
    }
    assert "secret-serial" not in json.dumps(result)


def test_nested_cgroup_v2_uses_smallest_ancestor_headroom(tmp_path):
    mount = tmp_path / "cgroup2"
    parent = mount / "user.slice"
    leaf = parent / "session.scope"
    leaf.mkdir(parents=True)
    (mount / "memory.max").write_text("max\n")
    (mount / "memory.current").write_text("100\n")
    (parent / "memory.max").write_text("800\n")
    (parent / "memory.current").write_text("700\n")
    (leaf / "memory.max").write_text("500\n")
    (leaf / "memory.current").write_text("100\n")

    result = doctor._cgroup_memory_from_hierarchy(
        version=2,
        mount_point=mount,
        relative_parts=("user.slice", "session.scope"),
    )
    assert result == {
        "status": "ok",
        "version": 2,
        "limit_bytes": 800,
        "current_bytes": 700,
        "available_bytes": 100,
        "finite_limit_levels": 2,
        "constraint_scope": "current_cgroup_or_ancestor",
    }


def test_nested_cgroup_v1_normalizes_unlimited_sentinel(tmp_path):
    mount = tmp_path / "memory"
    leaf = mount / "job.scope"
    leaf.mkdir(parents=True)
    (mount / "memory.limit_in_bytes").write_text("1073741824\n")
    (mount / "memory.usage_in_bytes").write_text("536870912\n")
    (leaf / "memory.limit_in_bytes").write_text("9223372036854771712\n")
    (leaf / "memory.usage_in_bytes").write_text("268435456\n")

    result = doctor._cgroup_memory_from_hierarchy(
        version=1,
        mount_point=mount,
        relative_parts=("job.scope",),
    )
    assert result["limit_bytes"] == 1073741824
    assert result["current_bytes"] == 536870912
    assert result["available_bytes"] == 536870912
    assert result["finite_limit_levels"] == 1


def test_cgroup_context_resolves_current_process_mount_without_emitting_path(tmp_path):
    mount = tmp_path / "cgroup2"
    cgroup = "0::/user.slice/session.scope\n"
    mountinfo = f"36 29 0:32 / {mount} rw - cgroup2 cgroup rw\n"
    context = doctor._resolve_cgroup_context(cgroup, mountinfo)
    assert context == {
        "version": 2,
        "mount_point": mount,
        "relative_parts": ("user.slice", "session.scope"),
    }


def test_cgroup_v1_context_strips_mounted_hierarchy_root(tmp_path):
    mount = tmp_path / "memory"
    cgroup = "5:cpu,memory:/machine.slice/job.scope\n"
    mountinfo = f"41 29 0:37 /machine.slice {mount} rw - cgroup cgroup rw,memory\n"
    context = doctor._resolve_cgroup_context(cgroup, mountinfo)
    assert context == {
        "version": 1,
        "mount_point": mount,
        "relative_parts": ("job.scope",),
    }


def test_hybrid_cgroup_prefers_explicit_v1_memory_controller(tmp_path):
    v2_mount = tmp_path / "unified"
    v1_mount = tmp_path / "memory"
    v1_leaf = v1_mount / "job.scope"
    v2_mount.mkdir()
    v1_leaf.mkdir(parents=True)
    (v1_mount / "memory.limit_in_bytes").write_text("1073741824\n")
    (v1_mount / "memory.usage_in_bytes").write_text("536870912\n")
    (v1_leaf / "memory.limit_in_bytes").write_text("805306368\n")
    (v1_leaf / "memory.usage_in_bytes").write_text("268435456\n")

    cgroup = "0::/user.slice/session.scope\n5:memory:/job.scope\n"
    mountinfo = "\n".join(
        (
            f"36 29 0:32 / {v2_mount} rw - cgroup2 cgroup rw",
            f"41 29 0:37 / {v1_mount} rw - cgroup cgroup rw,memory",
        )
    )
    context = doctor._resolve_cgroup_context(cgroup, mountinfo)
    assert context == {
        "version": 1,
        "mount_point": v1_mount,
        "relative_parts": ("job.scope",),
    }
    result = doctor._cgroup_memory_from_hierarchy(**context)
    assert result["limit_bytes"] == 1073741824
    assert result["available_bytes"] == 536870912


def test_tool_versions_whitelist_fields_from_hostile_output(monkeypatch):
    hostile = "/home/private-user/toolchain on build-host.example"

    def fake_run(args, stdout_limit=20000):
        outputs = {
            "nvcc": f"nvcc: NVIDIA CUDA compiler driver, release 12.8, V12.8.93 {hostile}",
            "c++": f"Ubuntu clang version 18.1.3\nInstalledDir: {hostile}",
            "cmake": f"cmake version 3.31.6\npackaged at {hostile}",
        }
        return {
            "status": "ok",
            "returncode": 0,
            "stdout": outputs[args[0]],
            "stderr": hostile,
        }

    monkeypatch.setattr(doctor, "_run_capture", fake_run)
    result = {
        "nvcc": doctor._nvcc_inventory(),
        "compiler": doctor._compiler_inventory(),
        "cmake": doctor._cmake_inventory(),
    }
    assert result == {
        "nvcc": {"status": "ok", "version": "12.8", "build": "12.8.93"},
        "compiler": {"status": "ok", "vendor": "clang", "version": "18.1.3"},
        "cmake": {"status": "ok", "version": "3.31.6"},
    }
    rendered = json.dumps(result)
    assert "private-user" not in rendered
    assert "build-host" not in rendered


def test_doctor_module_is_self_contained_executable():
    process = subprocess.run(
        [sys.executable, str(ROOT / "src/mlx_spark/runtime/doctor.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["kind"] == "host_inventory_only"
    assert result["hardware_validation"] == "NOT_PERFORMED"

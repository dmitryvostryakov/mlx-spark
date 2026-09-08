"""Resolve and audit the small, immutable metadata used by the source lock.

Network access is explicit. This module never downloads weight shards, imports
remote Python, builds source, or modifies an existing lock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SAFE_REF_RE = re.compile(r"^[A-Za-z0-9._/-]{1,200}$")
MAX_API_BYTES = 8 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024 * 1024
USER_AGENT = "mlx-spark-source-lock/1.0"

EXPECTED_SOURCES = {
    "mlx": ("git", "ml-explore/mlx"),
    "mlx_lm": ("git", "ml-explore/mlx-lm"),
    "transformers": ("git", "huggingface/transformers"),
    "qwen3_8_27b": ("hf_model", "Qwen/Qwen3.8-27B"),
}

GIT_AUDIT_PATHS = {
    "mlx": {
        "license": "LICENSE",
        "root_cmake": "CMakeLists.txt",
        "cuda_cmake": "mlx/backend/cuda/CMakeLists.txt",
        "find_cudnn": "cmake/FindCUDNN.cmake",
    },
    "mlx_lm": {
        "license": "LICENSE",
        "qwen3_5_reference": "mlx_lm/models/qwen3_5.py",
        "gated_delta_reference": "mlx_lm/models/gated_delta.py",
    },
    "transformers": {
        "license": "LICENSE",
        "qwen3_5_config": "src/transformers/models/qwen3_5/configuration_qwen3_5.py",
        "qwen3_5_modeling": "src/transformers/models/qwen3_5/modeling_qwen3_5.py",
        "auto_mappings": "src/transformers/models/auto/auto_mappings.py",
        "auto_modeling": "src/transformers/models/auto/modeling_auto.py",
        "auto_processing": "src/transformers/models/auto/processing_auto.py",
        "auto_image_processing": "src/transformers/models/auto/image_processing_auto.py",
        "auto_video_processing": "src/transformers/models/auto/video_processing_auto.py",
        "hub_kernels": "src/transformers/integrations/hub_kernels.py",
    },
}

QWEN_AUDIT_PATHS = {
    "license": "LICENSE",
    "model_card": "README.md",
    "config": "config.json",
    "weight_index": "model.safetensors.index.json",
    "tokenizer_config": "tokenizer_config.json",
    "generation_config": "generation_config.json",
    "image_preprocessor_config": "preprocessor_config.json",
    "video_preprocessor_config": "video_preprocessor_config.json",
}

MLX_TRANSITIVE_SOURCES = {
    "cccl": ("NVIDIA/cccl", "v3.1.3", "cuda_cmake"),
    "nvtx": ("NVIDIA/NVTX", "v3.1.1", "cuda_cmake"),
    "cudnn_frontend": ("NVIDIA/cudnn-frontend", "v1.16.0", "cuda_cmake"),
    "cutlass": ("NVIDIA/cutlass", "v4.4.2", "cuda_cmake"),
    "nlohmann_json": ("nlohmann/json", "v3.11.3", "root_cmake"),
    "fmt": ("fmtlib/fmt", "12.1.0", "root_cmake"),
    "nanobind": ("wjakob/nanobind", "v3.0.1", "root_cmake"),
}

MLX_TRANSITIVE_DECLARATION_MARKERS = {
    "cccl": (b"https://github.com/NVIDIA/cccl/releases/download/v3.1.3/",),
    "nvtx": (b"GIT_REPOSITORY https://github.com/NVIDIA/NVTX.git", b"GIT_TAG v3.1.1"),
    "cudnn_frontend": (
        b"GIT_REPOSITORY https://github.com/NVIDIA/cudnn-frontend.git",
        b"GIT_TAG v1.16.0",
    ),
    "cutlass": (b"GIT_REPOSITORY https://github.com/NVIDIA/cutlass.git", b"GIT_TAG v4.4.2"),
    "nlohmann_json": (
        b"https://github.com/nlohmann/json/releases/download/v3.11.3/",
    ),
    "fmt": (b"GIT_REPOSITORY https://github.com/fmtlib/fmt.git", b"GIT_TAG 12.1.0"),
    "nanobind": (b"GIT_REPOSITORY https://github.com/wjakob/nanobind.git", b"GIT_TAG v3.0.1"),
}


class SourceAuditError(ValueError):
    """A source failed an immutable metadata or policy check."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def fetch_bytes(url: str, limit: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SourceAuditError("Only explicit HTTPS metadata URLs are allowed")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise SourceAuditError(f"Metadata limit exceeded for {url}")
    return data


def parse_json(data: bytes, label: str) -> object:
    try:
        return json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceAuditError(f"Invalid JSON for {label}") from error


def artifact_record(url: str, source_path: str, data: bytes, *, json_value: object | None = None) -> dict:
    record = {
        "source_path": source_path,
        "url": url,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }
    if json_value is not None:
        record["canonical_json_sha256"] = canonical_json_sha256(json_value)
    return record


def exact_revision_record(
    url: str,
    source_path: str,
    repository: str,
    revision: str,
    *,
    selected_metadata: dict | None = None,
) -> dict:
    """Record only stable identity fields, not mutable API counters."""

    identity = {"repository": repository, "revision": revision}
    record = {
        "source_path": source_path,
        "url": url,
        "verified_revision": revision,
        "identity_sha256": canonical_json_sha256(identity),
    }
    if selected_metadata is not None:
        record["selected_metadata"] = selected_metadata
        record["selected_metadata_sha256"] = canonical_json_sha256(selected_metadata)
    return record


def require_markers(data: bytes, label: str, markers: tuple[bytes, ...]) -> None:
    missing = [marker.decode("utf-8", "replace") for marker in markers if marker not in data]
    if missing:
        raise SourceAuditError(f"{label} is missing required audited markers: {missing}")


def validate_candidate(candidate: object) -> dict:
    if not isinstance(candidate, dict) or candidate.get("schema_version") != 1:
        raise SourceAuditError("Expected source candidate schema_version=1")
    sources = candidate.get("sources")
    if not isinstance(sources, dict) or set(sources) != set(EXPECTED_SOURCES):
        raise SourceAuditError("Source candidate must contain exactly the audited source allowlist")

    for name, (expected_kind, expected_repository) in EXPECTED_SOURCES.items():
        entry = sources[name]
        if not isinstance(entry, dict):
            raise SourceAuditError(f"Source {name} must be an object")
        if entry.get("kind") != expected_kind or entry.get("repository") != expected_repository:
            raise SourceAuditError(f"Unexpected kind or repository for {name}")
        revision = entry.get("revision")
        ref = entry.get("ref_to_resolve")
        if revision is None and ref is None:
            raise SourceAuditError(f"Source {name} has neither a revision nor a ref")
        if revision is not None and not isinstance(revision, str):
            raise SourceAuditError(f"Source {name} revision must be a string")
        if revision is not None and not SHA_RE.fullmatch(revision):
            raise SourceAuditError(f"Source {name} revision is not a full lowercase SHA")
        if ref is not None and (
            not isinstance(ref, str)
            or not SAFE_REF_RE.fullmatch(ref)
            or ref.startswith("/")
            or ".." in ref.split("/")
        ):
            raise SourceAuditError(f"Source {name} has an unsafe ref")
        if revision is not None and ref is not None:
            raise SourceAuditError(f"Source {name} must not specify both revision and ref")
        if not isinstance(entry.get("role"), str) or not entry["role"]:
            raise SourceAuditError(f"Source {name} requires a role")
    return candidate


def _json_document(fetch: Callable[[str, int], bytes], url: str, label: str) -> tuple[bytes, dict]:
    data = fetch(url, MAX_API_BYTES)
    value = parse_json(data, label)
    if not isinstance(value, dict):
        raise SourceAuditError(f"Expected a JSON object for {label}")
    return data, value


def resolve_git_revision(entry: dict, fetch: Callable[[str, int], bytes]) -> tuple[str, bytes, str]:
    repository = entry["repository"]
    revision = entry.get("revision")
    if revision is None:
        requested = entry["ref_to_resolve"]
        discovery_url = f"https://api.github.com/repos/{repository}/commits/{urllib.parse.quote(requested, safe='')}"
        _, discovery = _json_document(fetch, discovery_url, f"{repository} revision discovery")
        revision = discovery.get("sha")
        if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
            raise SourceAuditError(f"GitHub returned a non-immutable revision for {repository}")

    exact_url = f"https://api.github.com/repos/{repository}/commits/{revision}"
    exact_bytes, exact = _json_document(fetch, exact_url, f"{repository} exact revision")
    if exact.get("sha") != revision:
        if entry.get("revision") is not None:
            raise SourceAuditError(f"Pinned revision did not round-trip for {repository}")
        raise SourceAuditError(f"Exact GitHub revision verification failed for {repository}")
    return revision, exact_bytes, exact_url


def resolve_mlx_transitive_sources(
    payloads: dict[str, bytes],
    artifacts: dict[str, dict],
    fetch: Callable[[str, int], bytes],
) -> dict:
    resolved = {}
    for name, (repository, ref, declaration_artifact) in MLX_TRANSITIVE_SOURCES.items():
        markers = MLX_TRANSITIVE_DECLARATION_MARKERS[name]
        require_markers(
            payloads[declaration_artifact],
            f"MLX transitive declaration {name}",
            markers,
        )
        revision, _, exact_url = resolve_git_revision(
            {
                "repository": repository,
                "revision": None,
                "ref_to_resolve": ref,
            },
            fetch,
        )
        resolved[name] = {
            "kind": "git",
            "repository": repository,
            "revision": revision,
            "exact_revision_url": exact_url,
            "declared_in_artifact": declaration_artifact,
            "declaration_artifact_sha256": artifacts[declaration_artifact]["sha256"],
            "declaration_verified": True,
            "upstream_declaration_content_addressed": False,
        }
    return resolved


def resolve_hf_revision(entry: dict, fetch: Callable[[str, int], bytes]) -> tuple[str, bytes, dict, str]:
    repository = entry["repository"]
    revision = entry.get("revision")
    if revision is None:
        discovery_url = f"https://huggingface.co/api/models/{repository}"
        _, discovery = _json_document(fetch, discovery_url, f"{repository} revision discovery")
        revision = discovery.get("sha")
    if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
        raise SourceAuditError(f"Hugging Face returned a non-immutable revision for {repository}")

    exact_url = f"https://huggingface.co/api/models/{repository}/revision/{revision}"
    exact_bytes, exact = _json_document(fetch, exact_url, f"{repository} exact revision")
    if exact.get("sha") != revision:
        raise SourceAuditError(f"Exact Hugging Face revision verification failed for {repository}")
    return revision, exact_bytes, exact, exact_url


def json_diff(expected: object, observed: object, path: str = "") -> list[str]:
    if isinstance(expected, dict) and isinstance(observed, dict):
        differences: list[str] = []
        for key in sorted(expected.keys() | observed.keys()):
            child = f"{path}/{key}"
            if key not in expected or key not in observed:
                differences.append(child)
            else:
                differences.extend(json_diff(expected[key], observed[key], child))
        return differences
    if isinstance(expected, list) and isinstance(observed, list):
        if len(expected) != len(observed):
            return [path or "/"]
        differences = []
        for index, (expected_item, observed_item) in enumerate(zip(expected, observed)):
            differences.extend(json_diff(expected_item, observed_item, f"{path}/{index}"))
        return differences
    return [] if expected == observed else [path or "/"]


def audit_git_source(name: str, entry: dict, revision: str, fetch: Callable[[str, int], bytes]) -> tuple[dict, dict]:
    repository = entry["repository"]
    artifacts = {}
    payloads = {}
    for artifact_name, source_path in GIT_AUDIT_PATHS[name].items():
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{source_path}"
        data = fetch(url, MAX_METADATA_BYTES)
        artifacts[artifact_name] = artifact_record(url, source_path, data)
        payloads[artifact_name] = data

    if name in {"mlx", "mlx_lm"}:
        require_markers(
            payloads["license"],
            f"{name} license",
            (b"MIT License", b"Permission is hereby granted, free of charge"),
        )
        audit = {"license_id": "MIT", "license_notice_verified": True}
        if name == "mlx":
            require_markers(
                payloads["root_cmake"],
                "MLX root CMake",
                (
                    b"find_package(CUDAToolkit REQUIRED)",
                    b"find_package(CUDNN REQUIRED)",
                    b'VERSION_GREATER_EQUAL "13.1"',
                    b'VERSION_LESS "13.2"',
                    b"CUDA Toolkit 13.1 is not supported.",
                ),
            )
            require_markers(
                payloads["cuda_cmake"],
                "MLX CUDA CMake",
                (
                    b"MLX_CUDA_ARCHITECTURES",
                    b"__nvcc_device_query",
                    b"CUDA_ARCHITECTURES",
                    b"CMAKE_CUDA_COMPILER_VERSION VERSION_GREATER_EQUAL 12.8.0",
                    b"MLX_CUDA_ARCHITECTURES GREATER_EQUAL 90",
                    b"--compress-mode=size",
                ),
            )
            require_markers(
                payloads["find_cudnn"],
                "MLX cuDNN discovery",
                (b"CUDNN_MAJOR_VERSION", b"CUDNN::cudnn_all"),
            )
            audit["cuda_source_constraints"] = {
                "cuda_toolkit_required": True,
                "cudnn_required": True,
                "cuda_13_1_rejected": True,
                "native_arch_query_default": True,
                "arch_90_or_newer_uses_accelerated_suffix": True,
                "compression_flag_enabled_from_cuda_12_8": True,
                "cudnn_frontend_git_tag": "v1.16.0",
                "transitive_fetches_content_addressed": False,
                "dgx2_cuda_toolkit_compatibility": "unknown_nvcc_unavailable",
                "hardware_validation": "not_performed",
            }
            audit["transitive_source_pins"] = resolve_mlx_transitive_sources(payloads, artifacts, fetch)
            audit["networked_build_allowed"] = False
            audit["networked_build_block_reason"] = (
                "Upstream CMake declarations use tags or archives without content hashes; materialize or override "
                "the exact transitive revisions before a networked build."
            )
        else:
            require_markers(
                payloads["qwen3_5_reference"],
                "MLX-LM Qwen3.5 reference",
                (b"class Qwen3_5TextModel", b"class GatedDeltaNet", b"class Model"),
            )
            audit["reference_only"] = True
            audit["remote_code_executed"] = False
    else:
        require_markers(
            payloads["license"],
            "Transformers license",
            (b"Apache License", b"Version 2.0, January 2004"),
        )
        require_markers(
            payloads["qwen3_5_config"],
            "Transformers Qwen3.5 config",
            (b"class Qwen3_5Config", b'model_type = "qwen3_5"'),
        )
        require_markers(
            payloads["qwen3_5_modeling"],
            "Transformers Qwen3.5 modeling",
            (b"class Qwen3_5GatedDeltaNet", b"class Qwen3_5ForConditionalGeneration"),
        )
        require_markers(
            payloads["auto_mappings"],
            "Transformers config auto mappings",
            (b'("qwen3_5", "Qwen3_5Config")',),
        )
        require_markers(
            payloads["auto_modeling"],
            "Transformers model auto mappings",
            (b'("qwen3_5", "Qwen3_5ForConditionalGeneration")',),
        )
        require_markers(
            payloads["auto_processing"],
            "Transformers processor auto mappings",
            (b'("qwen3_5", "Qwen3VLProcessor")',),
        )
        require_markers(
            payloads["auto_image_processing"],
            "Transformers image processor auto mappings",
            (b'("qwen3_5", {"torchvision": "Qwen2VLImageProcessor"',),
        )
        require_markers(
            payloads["auto_video_processing"],
            "Transformers video processor auto mappings",
            (b'("qwen3_5", "Qwen3VLVideoProcessor")',),
        )
        require_markers(
            payloads["hub_kernels"],
            "Transformers Hub-kernel integration",
            (b"USE_HUB_KERNELS", b"use_kernels"),
        )
        audit = {
            "license_id": "Apache-2.0",
            "license_notice_verified": True,
            "qwen3_5_config_source_present": True,
            "qwen3_5_conditional_generation_source_present": True,
            "qwen3_5_auto_config_registered": True,
            "qwen3_5_auto_model_registered": True,
            "qwen3_5_multimodal_processor_mappings_present": True,
            "oracle_runtime_validation": "not_performed",
            "oracle_required_environment": {"USE_HUB_KERNELS": "NO"},
            "oracle_required_arguments": {"use_kernels": False, "trust_remote_code": False, "local_files_only": True},
            "remote_code_executed": False,
        }
    return artifacts, audit


def _qwen_weight_manifest(index: object, siblings: object) -> dict:
    if not isinstance(index, dict) or not isinstance(index.get("weight_map"), dict):
        raise SourceAuditError("Qwen weight index has no weight_map")
    shard_names = sorted(set(index["weight_map"].values()))
    if not shard_names or not all(
        isinstance(name, str)
        and Path(name).name == name
        and re.fullmatch(r"model-\d{5}-of-\d{5}\.safetensors", name)
        for name in shard_names
    ):
        raise SourceAuditError("Qwen weight index contains unsafe or unexpected shard names")
    metadata = index.get("metadata")
    total_size = metadata.get("total_size") if isinstance(metadata, dict) else None
    if not isinstance(total_size, (int, float)) or isinstance(total_size, bool) or not math.isfinite(total_size):
        raise SourceAuditError("Qwen weight index has no finite total_size")
    total_size_int = int(total_size)
    if total_size_int != total_size or total_size_int <= 0:
        raise SourceAuditError("Qwen weight index total_size is not a positive integer")
    if not isinstance(siblings, list):
        raise SourceAuditError("Qwen exact model metadata has no siblings list")
    sibling_names = {
        sibling.get("rfilename")
        for sibling in siblings
        if isinstance(sibling, dict) and isinstance(sibling.get("rfilename"), str)
    }
    if not set(shard_names).issubset(sibling_names):
        raise SourceAuditError("Qwen weight index references shards absent from exact model metadata")
    return {
        "format": "safetensors",
        "shard_count": len(shard_names),
        "tensor_count": len(index["weight_map"]),
        "tensor_payload_bytes": total_size_int,
        "shard_filenames": shard_names,
        "weight_payload_downloaded": False,
        "weight_payload_hashed": False,
    }


def audit_qwen_source(
    entry: dict,
    revision: str,
    exact_model_metadata: dict,
    snapshot_bytes: bytes,
    fetch: Callable[[str, int], bytes],
) -> tuple[dict, dict]:
    repository = entry["repository"]
    artifacts = {}
    payloads = {}
    parsed_json = {}
    for artifact_name, source_path in QWEN_AUDIT_PATHS.items():
        url = f"https://huggingface.co/{repository}/resolve/{revision}/{source_path}"
        data = fetch(url, MAX_METADATA_BYTES)
        value = None
        if source_path.endswith(".json"):
            value = parse_json(data, f"Qwen {source_path}")
            parsed_json[artifact_name] = value
        artifacts[artifact_name] = artifact_record(url, source_path, data, json_value=value)
        payloads[artifact_name] = data

    require_markers(
        payloads["license"],
        "Qwen license",
        (b"Apache License", b"Version 2.0, January 2004"),
    )
    require_markers(payloads["model_card"], "Qwen model card", (b"license: apache-2.0", b"Qwen3.8-27B"))
    card_data = exact_model_metadata.get("cardData")
    if not isinstance(card_data, dict) or card_data.get("license") != "apache-2.0":
        raise SourceAuditError("Qwen exact model metadata does not declare apache-2.0")

    config = parsed_json["config"]
    if not isinstance(config, dict):
        raise SourceAuditError("Qwen config is not an object")
    if config.get("model_type") != "qwen3_5" or config.get("architectures") != [
        "Qwen3_5ForConditionalGeneration"
    ]:
        raise SourceAuditError("Qwen config has unexpected model identity")
    snapshot = parse_json(snapshot_bytes, "local normalized Qwen snapshot")
    differences = json_diff(snapshot, config)
    if differences:
        raise SourceAuditError(f"Pinned Qwen config differs from normalized snapshot at {differences}")

    weight_manifest = _qwen_weight_manifest(parsed_json["weight_index"], exact_model_metadata.get("siblings"))
    audit = {
        "license_id": "Apache-2.0",
        "license_notice_verified": True,
        "model_type": config["model_type"],
        "architectures": config["architectures"],
        "pipeline_tag": exact_model_metadata.get("pipeline_tag"),
        "library_name": exact_model_metadata.get("library_name"),
        "config_comparison": {
            "equal": True,
            "changed_paths": [],
            "local_snapshot_sha256": sha256_bytes(snapshot_bytes),
            "local_snapshot_canonical_json_sha256": canonical_json_sha256(snapshot),
            "remote_config_raw_sha256": artifacts["config"]["sha256"],
            "remote_config_canonical_json_sha256": artifacts["config"]["canonical_json_sha256"],
        },
        "weight_manifest": weight_manifest,
        "remote_code_executed": False,
    }
    return artifacts, audit


def build_lock(
    candidate_bytes: bytes,
    snapshot_bytes: bytes,
    fetch: Callable[[str, int], bytes] = fetch_bytes,
    *,
    resolved_at: str | None = None,
) -> dict:
    candidate = validate_candidate(parse_json(candidate_bytes, "source candidate"))
    sources = {}
    for name in EXPECTED_SOURCES:
        entry = candidate["sources"][name]
        if entry["kind"] == "git":
            revision, exact_bytes, exact_url = resolve_git_revision(entry, fetch)
            artifacts, audit = audit_git_source(name, entry, revision, fetch)
            exact_metadata = exact_revision_record(
                exact_url,
                "commit-api.json",
                entry["repository"],
                revision,
            )
        else:
            revision, exact_bytes, exact_model_metadata, exact_url = resolve_hf_revision(entry, fetch)
            artifacts, audit = audit_qwen_source(entry, revision, exact_model_metadata, snapshot_bytes, fetch)
            siblings = exact_model_metadata.get("siblings")
            if not isinstance(siblings, list):
                raise SourceAuditError("Qwen exact model metadata has no siblings list")
            sibling_names = sorted(
                sibling["rfilename"]
                for sibling in siblings
                if isinstance(sibling, dict) and isinstance(sibling.get("rfilename"), str)
            )
            selected_metadata = {
                "repository": entry["repository"],
                "revision": revision,
                "license": exact_model_metadata.get("cardData", {}).get("license"),
                "pipeline_tag": exact_model_metadata.get("pipeline_tag"),
                "library_name": exact_model_metadata.get("library_name"),
                "sibling_filenames": sibling_names,
            }
            exact_metadata = exact_revision_record(
                exact_url,
                "model-api.json",
                entry["repository"],
                revision,
                selected_metadata=selected_metadata,
            )
        sources[name] = {
            "kind": entry["kind"],
            "repository": entry["repository"],
            "revision": revision,
            "role": entry["role"],
            "exact_revision_metadata": exact_metadata,
            "artifacts": artifacts,
            "audit": audit,
        }

    timestamp = resolved_at or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 2,
        "scope": "single_spark_source_metadata",
        "resolved_at": timestamp,
        "review_state": "resolved_unreviewed",
        "review_evidence": None,
        "candidate_sha256": sha256_bytes(candidate_bytes),
        "sources": sources,
        "safety": {
            "network_opt_in_required": True,
            "metadata_only": True,
            "remote_code_executed": False,
            "weight_payload_downloaded": False,
            "cuda_hardware_validation": "not_performed",
            "second_node_contacted": False,
            "tp2_touched": False,
        },
        "warning": "Source-level audit is not a CUDA build/runtime or model-correctness validation.",
    }


def atomic_write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_path, path)
    except FileExistsError as error:
        raise SourceAuditError(f"Refusing to overwrite existing output: {path}") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def output_exists(path: Path) -> bool:
    return os.path.lexists(path)


def run(argv: list[str] | None = None, *, fetch: Callable[[str, int], bytes] = fetch_bytes) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--candidate", type=Path, default=ROOT / "configs/source-lock.candidate.json")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=ROOT / "configs/models/qwen3.8-27b.config.snapshot.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/source-lock.resolved.json")
    arguments = parser.parse_args(argv)

    if not arguments.allow_network:
        raise SystemExit("Network disabled. Read docs/BUILD_AND_SUPPLY_CHAIN.md before --allow-network.")
    if output_exists(arguments.output):
        raise SystemExit(f"Refusing to overwrite existing output: {arguments.output}")

    candidate_bytes = arguments.candidate.read_bytes()
    snapshot_bytes = arguments.snapshot.read_bytes()
    lock = build_lock(candidate_bytes, snapshot_bytes, fetch)
    rendered = (json.dumps(lock, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        atomic_write_new(arguments.output, rendered)
    except SourceAuditError as error:
        raise SystemExit(str(error)) from error
    print(arguments.output)
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except SourceAuditError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()

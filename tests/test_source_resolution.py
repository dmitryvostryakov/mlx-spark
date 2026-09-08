import json
import re
from pathlib import Path

import pytest

import resolve_sources


ROOT = Path(__file__).resolve().parents[1]
SHA = {
    "mlx": "1" * 40,
    "mlx_lm": "2" * 40,
    "transformers": "3" * 40,
    "qwen3_8_27b": "4" * 40,
}
TRANSITIVE_SHA = {
    repository: format(index, "040x")
    for index, repository in enumerate(
        (repository for repository, _, _ in resolve_sources.MLX_TRANSITIVE_SOURCES.values()),
        start=10,
    )
}


def _candidate():
    candidate = json.loads((ROOT / "configs/source-lock.candidate.json").read_text())
    candidate["sources"]["mlx"]["revision"] = SHA["mlx"]
    for name in ("mlx_lm", "transformers", "qwen3_8_27b"):
        candidate["sources"][name]["revision"] = None
        candidate["sources"][name]["ref_to_resolve"] = "candidate-ref"
    return candidate


def _snapshot():
    return json.loads((ROOT / "configs/models/qwen3.8-27b.config.snapshot.json").read_text())


def _fake_fetch():
    requested = []
    snapshot = _snapshot()
    shards = [f"model-{index:05d}-of-00002.safetensors" for index in (1, 2)]

    def fetch(url, limit):
        requested.append((url, limit))
        if "api.github.com" in url:
            transitive = next((sha for repository, sha in TRANSITIVE_SHA.items() if f"/{repository}/" in url), None)
            if transitive is not None:
                revision = transitive
            elif "/ml-explore/mlx-lm/" in url:
                revision = SHA["mlx_lm"]
            elif "/huggingface/transformers/" in url:
                revision = SHA["transformers"]
            else:
                revision = SHA["mlx"]
            return json.dumps({"sha": revision, "commit": {"message": "fixture"}}).encode()
        if "/api/models/Qwen/Qwen3.8-27B/revision/" in url:
            return json.dumps(
                {
                    "sha": SHA["qwen3_8_27b"],
                    "cardData": {"license": "apache-2.0"},
                    "pipeline_tag": "image-text-to-text",
                    "library_name": "transformers",
                    "siblings": [{"rfilename": name} for name in shards],
                }
            ).encode()
        if url == "https://huggingface.co/api/models/Qwen/Qwen3.8-27B":
            return json.dumps({"sha": SHA["qwen3_8_27b"]}).encode()
        if url.endswith("/LICENSE"):
            if "/Qwen/" in url or "/huggingface/transformers/" in url:
                return b"Apache License\nVersion 2.0, January 2004\n"
            return b"MIT License\nPermission is hereby granted, free of charge\n"
        if url.endswith("/CMakeLists.txt") and "/mlx/backend/cuda/" not in url:
            return (
                b"find_package(CUDAToolkit REQUIRED)\nfind_package(CUDNN REQUIRED)\n"
                b'CUDAToolkit_VERSION VERSION_GREATER_EQUAL "13.1"\n'
                b'CUDAToolkit_VERSION VERSION_LESS "13.2"\n'
                b"CUDA Toolkit 13.1 is not supported.\n"
                b"https://github.com/nlohmann/json/releases/download/v3.11.3/\n"
                b"GIT_REPOSITORY https://github.com/fmtlib/fmt.git\nGIT_TAG 12.1.0\n"
                b"GIT_REPOSITORY https://github.com/wjakob/nanobind.git\nGIT_TAG v3.0.1\n"
            )
        if "/mlx/backend/cuda/CMakeLists.txt" in url:
            return (
                b"MLX_CUDA_ARCHITECTURES __nvcc_device_query CUDA_ARCHITECTURES\n"
                b"CMAKE_CUDA_COMPILER_VERSION VERSION_GREATER_EQUAL 12.8.0\n"
                b"MLX_CUDA_ARCHITECTURES GREATER_EQUAL 90\n--compress-mode=size\n"
                b"https://github.com/NVIDIA/cccl/releases/download/v3.1.3/\n"
                b"GIT_REPOSITORY https://github.com/NVIDIA/NVTX.git\nGIT_TAG v3.1.1\n"
                b"GIT_REPOSITORY https://github.com/NVIDIA/cudnn-frontend.git\nGIT_TAG v1.16.0\n"
                b"GIT_REPOSITORY https://github.com/NVIDIA/cutlass.git\nGIT_TAG v4.4.2\n"
            )
        if url.endswith("cmake/FindCUDNN.cmake"):
            return b"CUDNN_MAJOR_VERSION\nCUDNN::cudnn_all\n"
        if url.endswith("mlx_lm/models/qwen3_5.py"):
            return b"class Qwen3_5TextModel: pass\nclass GatedDeltaNet: pass\nclass Model: pass\n"
        if url.endswith("mlx_lm/models/gated_delta.py"):
            return b"reference only\n"
        if url.endswith("configuration_qwen3_5.py"):
            return b'class Qwen3_5Config:\n model_type = "qwen3_5"\n'
        if url.endswith("modeling_qwen3_5.py"):
            return b"class Qwen3_5GatedDeltaNet: pass\nclass Qwen3_5ForConditionalGeneration: pass\n"
        if url.endswith("auto_mappings.py"):
            return b'("qwen3_5", "Qwen3_5Config")\n'
        if url.endswith("modeling_auto.py"):
            return b'("qwen3_5", "Qwen3_5ForConditionalGeneration")\n'
        if url.endswith("image_processing_auto.py"):
            return b'("qwen3_5", {"torchvision": "Qwen2VLImageProcessor"})\n'
        if url.endswith("video_processing_auto.py"):
            return b'("qwen3_5", "Qwen3VLVideoProcessor")\n'
        if url.endswith("processing_auto.py"):
            return b'("qwen3_5", "Qwen3VLProcessor")\n'
        if url.endswith("hub_kernels.py"):
            return b"USE_HUB_KERNELS use_kernels\n"
        if url.endswith("README.md"):
            return b"---\nlicense: apache-2.0\n---\nQwen3.8-27B\n"
        if url.endswith("config.json"):
            return json.dumps(snapshot).encode()
        if url.endswith("model.safetensors.index.json"):
            return json.dumps(
                {
                    "metadata": {"total_size": 1234},
                    "weight_map": {"a": shards[0], "b": shards[1]},
                }
            ).encode()
        if url.endswith(".json"):
            return b"{}"
        raise AssertionError(f"unexpected URL {url}")

    return fetch, requested


def _build(candidate=None, fetch=None):
    candidate = candidate or _candidate()
    if fetch is None:
        fetch, _ = _fake_fetch()
    return resolve_sources.build_lock(
        (json.dumps(candidate) + "\n").encode(),
        (json.dumps(_snapshot()) + "\n").encode(),
        fetch,
        resolved_at="2026-09-08T00:00:00+00:00",
    )


def _all_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)
    elif isinstance(value, str):
        yield value


def test_candidate_schema_rejects_unknown_kind_or_repository():
    candidate = _candidate()
    candidate["sources"]["mlx"]["kind"] = "archive"
    with pytest.raises(resolve_sources.SourceAuditError, match="Unexpected kind or repository"):
        resolve_sources.validate_candidate(candidate)


def test_pinned_git_revision_must_round_trip_exactly():
    candidate = _candidate()
    fetch, _ = _fake_fetch()

    def mismatch(url, limit):
        if "/ml-explore/mlx/" in url and "api.github.com" in url:
            return json.dumps({"sha": "f" * 40}).encode()
        return fetch(url, limit)

    with pytest.raises(resolve_sources.SourceAuditError, match="did not round-trip"):
        _build(candidate, mismatch)


def test_hf_resolution_uses_and_verifies_an_explicit_revision():
    candidate = _candidate()
    entry = candidate["sources"]["qwen3_8_27b"]
    entry["revision"] = SHA["qwen3_8_27b"]
    entry["ref_to_resolve"] = None
    fetch, requested = _fake_fetch()
    lock = _build(candidate, fetch)
    urls = [url for url, _ in requested]
    assert "https://huggingface.co/api/models/Qwen/Qwen3.8-27B" not in urls
    assert any(url.endswith(f"/revision/{SHA['qwen3_8_27b']}") for url in urls)
    assert lock["sources"]["qwen3_8_27b"]["revision"] == SHA["qwen3_8_27b"]
    exact = lock["sources"]["qwen3_8_27b"]["exact_revision_metadata"]
    assert exact["selected_metadata"]["license"] == "apache-2.0"
    assert re.fullmatch(r"[0-9a-f]{64}", exact["selected_metadata_sha256"])


def test_all_audit_files_use_exact_revisions_and_no_weight_payload_is_fetched():
    fetch, requested = _fake_fetch()
    lock = _build(fetch=fetch)
    urls = [url for url, _ in requested]
    for name, source in lock["sources"].items():
        revision = source["revision"]
        artifact_urls = [item["url"] for item in source["artifacts"].values()]
        assert artifact_urls and all(revision in url for url in artifact_urls), name
    assert not any(re.search(r"/model-\d{5}-of-\d{5}\.safetensors(?:\?|$)", url) for url in urls)
    assert lock["safety"]["weight_payload_downloaded"] is False
    assert lock["safety"]["remote_code_executed"] is False


def test_artifact_byte_and_canonical_json_hashes_are_recorded():
    lock = _build()
    config = lock["sources"]["qwen3_8_27b"]["artifacts"]["config"]
    assert re.fullmatch(r"[0-9a-f]{64}", config["sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", config["canonical_json_sha256"])
    exact = lock["sources"]["transformers"]["exact_revision_metadata"]
    assert exact["verified_revision"] == SHA["transformers"]
    assert re.fullmatch(r"[0-9a-f]{64}", exact["identity_sha256"])


def test_qwen_normalized_snapshot_comparison_and_manifest():
    lock = _build()
    audit = lock["sources"]["qwen3_8_27b"]["audit"]
    assert audit["config_comparison"]["equal"] is True
    assert audit["config_comparison"]["changed_paths"] == []
    assert audit["license_id"] == "Apache-2.0"
    assert audit["weight_manifest"]["shard_count"] == 2
    assert audit["weight_manifest"]["tensor_payload_bytes"] == 1234
    assert audit["weight_manifest"]["weight_payload_downloaded"] is False


def test_json_diff_reports_missing_changed_extra_and_list_paths():
    expected = {"same": 1, "changed": {"x": 2}, "missing": 3, "list": [1, 2]}
    observed = {"same": 1, "changed": {"x": 9}, "extra": 4, "list": [1, 7]}
    assert resolve_sources.json_diff(expected, observed) == [
        "/changed/x",
        "/extra",
        "/list/1",
        "/missing",
    ]


def test_changed_qwen_config_fails_closed():
    fetch, _ = _fake_fetch()

    def changed(url, limit):
        data = fetch(url, limit)
        if url.endswith("/config.json"):
            config = json.loads(data)
            config["text_config"]["hidden_size"] += 1
            return json.dumps(config).encode()
        return data

    with pytest.raises(resolve_sources.SourceAuditError, match="/text_config/hidden_size"):
        _build(fetch=changed)


def test_source_audits_are_license_and_support_specific_without_runtime_claims():
    lock = _build()
    assert lock["sources"]["mlx"]["audit"]["license_id"] == "MIT"
    constraints = lock["sources"]["mlx"]["audit"]["cuda_source_constraints"]
    assert constraints["cuda_13_1_rejected"] is True
    assert constraints["hardware_validation"] == "not_performed"
    mlx_audit = lock["sources"]["mlx"]["audit"]
    assert mlx_audit["networked_build_allowed"] is False
    assert set(mlx_audit["transitive_source_pins"]) == set(resolve_sources.MLX_TRANSITIVE_SOURCES)
    assert all(
        resolve_sources.SHA_RE.fullmatch(source["revision"])
        for source in mlx_audit["transitive_source_pins"].values()
    )
    assert all(source["declaration_verified"] for source in mlx_audit["transitive_source_pins"].values())
    assert all(
        source["declaration_artifact_sha256"]
        == lock["sources"]["mlx"]["artifacts"][source["declared_in_artifact"]]["sha256"]
        for source in mlx_audit["transitive_source_pins"].values()
    )
    oracle = lock["sources"]["transformers"]["audit"]
    assert oracle["qwen3_5_conditional_generation_source_present"] is True
    assert oracle["qwen3_5_multimodal_processor_mappings_present"] is True
    assert oracle["oracle_runtime_validation"] == "not_performed"


@pytest.mark.parametrize(
    ("dependency", "marker"),
    [
        ("cccl", b"https://github.com/NVIDIA/cccl/releases/download/v3.1.3/"),
        ("nvtx", b"GIT_TAG v3.1.1"),
        ("cudnn_frontend", b"GIT_TAG v1.16.0"),
        ("cutlass", b"GIT_TAG v4.4.2"),
        ("nlohmann_json", b"https://github.com/nlohmann/json/releases/download/v3.11.3/"),
        ("fmt", b"GIT_TAG 12.1.0"),
        ("nanobind", b"GIT_TAG v3.0.1"),
    ],
)
def test_each_transitive_pin_must_be_bound_to_the_exact_cmake_ref(dependency, marker):
    fetch, _ = _fake_fetch()

    def missing_declaration(url, limit):
        data = fetch(url, limit)
        return data.replace(marker, b"changed-ref")

    with pytest.raises(resolve_sources.SourceAuditError, match=f"transitive declaration {dependency}"):
        _build(fetch=missing_declaration)


@pytest.mark.parametrize(
    "marker",
    [
        b"CMAKE_CUDA_COMPILER_VERSION VERSION_GREATER_EQUAL 12.8.0",
        b"MLX_CUDA_ARCHITECTURES GREATER_EQUAL 90",
    ],
)
def test_cuda_condition_claims_fail_closed_when_exact_condition_is_missing(marker):
    fetch, _ = _fake_fetch()

    def missing_condition(url, limit):
        data = fetch(url, limit)
        return data.replace(marker, b"condition-removed")

    with pytest.raises(resolve_sources.SourceAuditError, match="MLX CUDA CMake"):
        _build(fetch=missing_condition)


def test_future_executable_lock_contains_no_mutable_refs():
    lock = _build()
    forbidden_values = {"main", "master", "latest"}
    strings = list(_all_strings(lock))
    assert not any(value.lower() in forbidden_values for value in strings)
    assert not any(re.search(r"/(?:main|master|latest)(?:/|$)", value, re.IGNORECASE) for value in strings)
    assert all(resolve_sources.SHA_RE.fullmatch(source["revision"]) for source in lock["sources"].values())


def test_existing_output_is_refused_before_any_read_or_network(tmp_path):
    output = tmp_path / "lock.json"
    output.write_text("keep")
    candidate = tmp_path / "missing-candidate.json"
    snapshot = tmp_path / "missing-snapshot.json"
    calls = []

    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        resolve_sources.run(
            [
                "--allow-network",
                "--candidate",
                str(candidate),
                "--snapshot",
                str(snapshot),
                "--output",
                str(output),
            ],
            fetch=lambda url, limit: calls.append(url),
        )
    assert output.read_text() == "keep"
    assert calls == []


def test_atomic_writer_never_overwrites_existing_output(tmp_path):
    output = tmp_path / "lock.json"
    output.write_bytes(b"original")
    with pytest.raises(resolve_sources.SourceAuditError, match="Refusing to overwrite"):
        resolve_sources.atomic_write_new(output, b"replacement")
    assert output.read_bytes() == b"original"
    assert not list(tmp_path.glob("*.tmp"))


def test_fetch_or_audit_failure_leaves_no_final_lock(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    snapshot_path = tmp_path / "snapshot.json"
    output = tmp_path / "lock.json"
    candidate_path.write_text(json.dumps(_candidate()))
    snapshot_path.write_text(json.dumps(_snapshot()))

    def fail(_url, _limit):
        raise resolve_sources.SourceAuditError("forced network failure")

    with pytest.raises(resolve_sources.SourceAuditError, match="forced network failure"):
        resolve_sources.run(
            [
                "--allow-network",
                "--candidate",
                str(candidate_path),
                "--snapshot",
                str(snapshot_path),
                "--output",
                str(output),
            ],
            fetch=fail,
        )
    assert not output.exists()


def test_unreviewed_lock_remains_rejected_by_materializer(tmp_path):
    lock = tmp_path / "unreviewed.json"
    lock.write_text(json.dumps(_build()))
    destination = tmp_path / "source"
    process = __import__("subprocess").run(
        [
            __import__("sys").executable,
            str(ROOT / "tools/fetch_upstream.py"),
            "--allow-network",
            "--lock",
            str(lock),
            "--destination",
            str(destination),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode != 0
    assert "explicitly reviewed" in process.stderr
    assert not destination.exists()

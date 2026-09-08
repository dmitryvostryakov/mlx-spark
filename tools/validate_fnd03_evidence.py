#!/usr/bin/env python3
"""Offline, literal validator for retained FND-03 source/cache evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "runs" / "fnd-03"
LOCK_PATH = ROOT / "configs" / "source-lock.resolved.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_REVISIONS = {
    "mlx": "365bd0fbac2e96631a1b2c4a34ca5a0771cdfde5",
    "mlx_lm": "7fb4be44d560e5b74595210f83cb6003a57e52a7",
    "transformers": "0df4ef369d324d4072e2910c673671eed4e92459",
    "qwen3_8_27b": "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0",
}
EXPECTED_ARTIFACT_HASHES = {
    ("mlx", "license"): "ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01",
    ("mlx", "root_cmake"): "40d6674414f415096ebe3624ac91fbee9ea7069a69afcb44d60b7bfa56e331d6",
    ("mlx", "cuda_cmake"): "7fe1af509fecffdeb6bdd7d88cfa83f2164ba7676e518e61021a4f1a69e6e676",
    ("mlx", "find_cudnn"): "7a945752c982bc7cb029629eac833033944bd71a0d688d73ad71ff5a365c6173",
    ("mlx_lm", "license"): "ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01",
    ("mlx_lm", "qwen3_5_reference"): "14c4898a03567998e825cb1817942001871e979b9e0cefd3b4383cbbb61eddf3",
    ("mlx_lm", "gated_delta_reference"): "2b58508fc85875b28ba49defd34c9a9264e9502de171fa8114e5cb0598a447b2",
    ("transformers", "license"): "77fd4710def9ec3c0f6225800e0235f15a425abd4a8b03559127fcd782612049",
    ("transformers", "qwen3_5_config"): "19966c3200cee92cc4bccaef5f94550c56d731dbf03858a9bd2ed6aebcc3f7da",
    ("transformers", "qwen3_5_modeling"): "458360c8072e6130580639170ad3e645b975512dbabae31eab5f92de5f0f09ef",
    ("transformers", "auto_mappings"): "72fd4f61324bd4281e153a9ed8485c556a31a550df07b266ed83d24303428e1a",
    ("transformers", "auto_modeling"): "31d0fc246babd6eb78800123782ad1e0a0dc67481d8de12c7d246f7fb06148b1",
    ("transformers", "auto_processing"): "2ac6d6c9837e25eda9184c7a619708187aa564fcea96baf13ea7ff260e197517",
    ("transformers", "auto_image_processing"): "23c3a6fe0c7f1b9d520856379c80210ffb1c0868d1b892a730029da9610da251",
    ("transformers", "auto_video_processing"): "2dabbaf2fb5574631c6d08146035b8a25bd0e430a9eb5da0dcfe3746a1b14c06",
    ("transformers", "hub_kernels"): "c1eafefe0cbdf7f0deaa21b1ef6cb6d7c6082b3f486651d069ff38fcf3e53c95",
    ("qwen3_8_27b", "license"): "bbedc3fda3305820b977265f01b8619d87570a6739de3a5582c3464840f1e57a",
    ("qwen3_8_27b", "model_card"): "57e4bdb258ee1a7d2635c5174ebd4e56abe392505cdb5f8bbb356b0dc4293641",
    ("qwen3_8_27b", "config"): "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab",
    ("qwen3_8_27b", "weight_index"): "77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df",
    ("qwen3_8_27b", "tokenizer_config"): "b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27",
    ("qwen3_8_27b", "generation_config"): "e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e",
    ("qwen3_8_27b", "image_preprocessor_config"): "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
    ("qwen3_8_27b", "video_preprocessor_config"): "7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13",
}
EXPECTED_TRANSITIVE_REVISIONS = {
    "cccl": "d69eb55e0a0f6d55ca2af4c4edb2c7055c003993",
    "nvtx": "6230bdf710bc94f44d433acceba735aaa9090ba5",
    "cudnn_frontend": "be6c079be8aaffa0fc079fcf039887e637c289c7",
    "cutlass": "da5e086dab31d63815acafdac9a9c5893b1c69e2",
    "nlohmann_json": "9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03",
    "fmt": "407c905e45ad75fc29bf0f9bb7c5c2fd3475976f",
    "nanobind": "db4827f06f6f1680e5d4004c95fc8d69299dba8b",
}
LOCAL_SNAPSHOT_RAW_SHA256 = "7718cd6bf3d6521d5550966d4ab8484fc81a01347d74b7e52163070f35ca7f35"
CANONICAL_CONFIG_SHA256 = "137754ebd46991bec0c0d9e660dc98256be0b20f0e825b28c95c31de6142d041"
HF_SELECTED_METADATA_SHA256 = "427e7b48ad24338145516b7dffc3a1f64b833a1c9ef07d1297fbbd79eeeaccc8"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_sha256(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _strings(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(*, allow_unreviewed: bool = False) -> dict:
    lock = _load(LOCK_PATH)
    run = _load(EVIDENCE / "run.json")
    cache = _load(EVIDENCE / "weight-cache-probe.stdout.log")
    provenance = _load(ROOT / "configs" / "models" / "qwen3.8-27b.provenance.json")
    pinned_input_path = EVIDENCE / "source-lock.pinned-input.json"
    pinned_input = _load(pinned_input_path)

    _require(lock.get("schema_version") == 2, "source lock schema is not 2")
    if allow_unreviewed:
        _require(lock.get("review_state") in {"resolved_unreviewed", "approved"}, "invalid candidate review state")
    else:
        _require(lock.get("review_state") == "approved", "source lock is not independently approved")
        review_evidence = lock.get("review_evidence")
        _require(isinstance(review_evidence, str) and review_evidence, "approved lock has no review evidence")
        _require((ROOT / review_evidence).is_file(), "source lock review evidence is missing")

    _require(lock.get("candidate_sha256") == _sha256(pinned_input_path), "pinned input hash mismatch")
    sources = lock.get("sources")
    _require(isinstance(sources, dict) and set(sources) == set(EXPECTED_REVISIONS), "unexpected source set")
    for name, expected_revision in EXPECTED_REVISIONS.items():
        source = sources[name]
        _require(source.get("revision") == expected_revision, f"unexpected revision for {name}")
        _require(bool(SHA40.fullmatch(source["revision"])), f"non-full revision for {name}")
        exact = source.get("exact_revision_metadata")
        _require(isinstance(exact, dict), f"missing exact revision metadata for {name}")
        _require(exact.get("verified_revision") == expected_revision, f"unverified exact revision for {name}")
        _require(bool(SHA256.fullmatch(exact.get("identity_sha256", ""))), f"invalid identity hash for {name}")
        artifacts = source.get("artifacts")
        _require(isinstance(artifacts, dict) and artifacts, f"missing artifacts for {name}")
        for artifact_name, artifact in artifacts.items():
            _require(expected_revision in artifact.get("url", ""), f"non-immutable artifact URL for {name}/{artifact_name}")
            _require(artifact.get("bytes", 0) > 0, f"empty artifact for {name}/{artifact_name}")
            _require(bool(SHA256.fullmatch(artifact.get("sha256", ""))), f"invalid artifact hash for {name}/{artifact_name}")

    for (source_name, artifact_name), expected_hash in EXPECTED_ARTIFACT_HASHES.items():
        observed_hash = sources[source_name]["artifacts"][artifact_name]["sha256"]
        _require(observed_hash == expected_hash, f"unexpected hash for {source_name}/{artifact_name}")

    forbidden = {"main", "master", "latest"}
    for value in _strings(lock):
        _require(value.lower() not in forbidden, f"mutable ref value in executable lock: {value}")
        _require(not re.search(r"/(?:main|master|latest)(?:/|$)", value, re.IGNORECASE), "mutable ref URL in lock")

    qwen_audit = sources["qwen3_8_27b"]["audit"]
    qwen_exact_metadata = sources["qwen3_8_27b"]["exact_revision_metadata"]
    selected_metadata = qwen_exact_metadata.get("selected_metadata")
    _require(isinstance(selected_metadata, dict), "retained Qwen API metadata is missing")
    _require(selected_metadata.get("license") == "apache-2.0", "retained Qwen API license mismatch")
    _require(selected_metadata.get("pipeline_tag") == "image-text-to-text", "retained Qwen pipeline mismatch")
    _require(selected_metadata.get("library_name") == "transformers", "retained Qwen library mismatch")
    _require(
        _canonical_json_sha256(selected_metadata) == HF_SELECTED_METADATA_SHA256,
        "retained Qwen API metadata hash mismatch",
    )
    _require(
        qwen_exact_metadata.get("selected_metadata_sha256") == HF_SELECTED_METADATA_SHA256,
        "recorded Qwen API metadata hash mismatch",
    )
    config_comparison = qwen_audit["config_comparison"]
    _require(config_comparison.get("equal") is True and config_comparison.get("changed_paths") == [], "Qwen config differs")
    _require(config_comparison.get("local_snapshot_sha256") == LOCAL_SNAPSHOT_RAW_SHA256, "local snapshot hash mismatch")
    _require(
        config_comparison.get("remote_config_canonical_json_sha256") == CANONICAL_CONFIG_SHA256,
        "remote canonical config hash mismatch",
    )
    snapshot_path = ROOT / "configs" / "models" / "qwen3.8-27b.config.snapshot.json"
    _require(_sha256(snapshot_path) == LOCAL_SNAPSHOT_RAW_SHA256, "local snapshot bytes changed")
    _require(_canonical_json_sha256(_load(snapshot_path)) == CANONICAL_CONFIG_SHA256, "local canonical config changed")
    weight_manifest = qwen_audit["weight_manifest"]
    _require(weight_manifest.get("shard_count") == 18, "Qwen index shard count mismatch")
    _require(weight_manifest.get("tensor_count") == 1199, "Qwen index tensor count mismatch")
    _require(weight_manifest.get("tensor_payload_bytes") == 55562855904, "Qwen tensor payload size mismatch")
    _require(weight_manifest.get("weight_payload_downloaded") is False, "lock claims a weight download")
    _require(weight_manifest.get("weight_payload_hashed") is False, "lock claims unperformed weight hashing")
    _require(
        set(weight_manifest["shard_filenames"]).issubset(set(selected_metadata.get("sibling_filenames", []))),
        "Qwen index shards are absent from retained exact API metadata",
    )

    mlx_audit = sources["mlx"]["audit"]
    _require(mlx_audit.get("license_id") == "MIT", "MLX license audit mismatch")
    _require(mlx_audit.get("networked_build_allowed") is False, "unsafe networked build is allowed")
    transitive = mlx_audit.get("transitive_source_pins")
    _require(isinstance(transitive, dict) and set(transitive) == set(EXPECTED_TRANSITIVE_REVISIONS), "transitive set mismatch")
    for name, revision in EXPECTED_TRANSITIVE_REVISIONS.items():
        _require(transitive[name].get("revision") == revision, f"transitive revision mismatch for {name}")
        _require(transitive[name].get("declaration_verified") is True, f"unverified declaration for {name}")
        declaration_name = transitive[name].get("declared_in_artifact")
        declaration_hash = sources["mlx"]["artifacts"].get(declaration_name, {}).get("sha256")
        _require(
            transitive[name].get("declaration_artifact_sha256") == declaration_hash,
            f"declaration artifact hash mismatch for {name}",
        )
        _require(transitive[name].get("upstream_declaration_content_addressed") is False, f"false CMake claim for {name}")

    transformers_audit = sources["transformers"]["audit"]
    _require(transformers_audit.get("qwen3_5_conditional_generation_source_present") is True, "oracle model source missing")
    _require(transformers_audit.get("qwen3_5_multimodal_processor_mappings_present") is True, "oracle processors missing")
    _require(transformers_audit.get("oracle_runtime_validation") == "not_performed", "oracle runtime claim is not honest")
    _require(transformers_audit.get("oracle_required_environment") == {"USE_HUB_KERNELS": "NO"}, "unsafe Hub kernel policy")
    _require(transformers_audit.get("oracle_required_arguments", {}).get("trust_remote_code") is False, "remote code allowed")

    safety = lock.get("safety")
    _require(safety.get("metadata_only") is True, "source resolution not metadata-only")
    _require(safety.get("remote_code_executed") is False, "remote code execution claimed")
    _require(safety.get("weight_payload_downloaded") is False, "resolver weight download claimed")
    _require(safety.get("cuda_hardware_validation") == "not_performed", "CUDA validation falsely claimed")
    _require(safety.get("second_node_contacted") is False and safety.get("tp2_touched") is False, "scope boundary violated")

    _require(cache.get("model_id") == "Qwen/Qwen3.8-27B", "cache probe model mismatch")
    _require(cache.get("snapshot_revisions") == [EXPECTED_REVISIONS["qwen3_8_27b"]], "cache revision mismatch")
    _require(cache.get("complete") is True and cache.get("network_used") is False, "cache probe incomplete or networked")
    _require(cache.get("files_modified") is False and cache.get("sensitive_fields_emitted") is False, "unsafe cache probe")
    _require(len(cache.get("snapshots", [])) == 1, "unexpected cache snapshot count")
    cache_snapshot = cache["snapshots"][0]
    _require(cache_snapshot.get("expected_shard_count") == 18, "cache expected-shard mismatch")
    _require(cache_snapshot.get("present_shard_count") == 18, "cache present-shard mismatch")
    _require(cache_snapshot.get("aggregate_present_bytes") == 55563006776, "cache aggregate size mismatch")
    _require(cache_snapshot.get("metadata_hashes_match") is True, "cache metadata hashes were not authenticated")
    _require(
        cache_snapshot.get("all_exact_index_shards_present") is True,
        "exact audited index shard set is not complete in cache",
    )
    _require(
        cache_snapshot.get("config_sha256") == EXPECTED_ARTIFACT_HASHES[("qwen3_8_27b", "config")],
        "cached config hash differs from exact metadata",
    )
    _require(
        cache_snapshot.get("index_sha256") == EXPECTED_ARTIFACT_HASHES[("qwen3_8_27b", "weight_index")],
        "cached index hash differs from exact metadata",
    )
    _require(
        cache_snapshot.get("tokenizer_config_sha256")
        == EXPECTED_ARTIFACT_HASHES[("qwen3_8_27b", "tokenizer_config")],
        "cached tokenizer config hash differs from exact metadata",
    )
    _require(cache_snapshot["aggregate_present_bytes"] >= weight_manifest["tensor_payload_bytes"], "cache smaller than payload")
    rendered_cache = json.dumps(cache)
    _require("/home/" not in rendered_cache and "/Users/" not in rendered_cache, "cache evidence leaks a path")

    _require(provenance.get("immutable_revision") == EXPECTED_REVISIONS["qwen3_8_27b"], "provenance revision mismatch")
    _require(provenance.get("exact_config_sha256") == EXPECTED_ARTIFACT_HASHES[("qwen3_8_27b", "config")], "provenance config mismatch")
    _require(provenance.get("structurally_equal") is True and provenance.get("changed_paths") == [], "provenance diff mismatch")
    _require(pinned_input["sources"]["qwen3_8_27b"]["revision"] == EXPECTED_REVISIONS["qwen3_8_27b"], "input pin mismatch")

    _require(run.get("task") == "FND-03", "run task mismatch")
    _require(bool(SHA40.fullmatch(run.get("implementation_commit", ""))), "run implementation commit is not full SHA")
    hardware = run.get("hardware", {})
    _require(hardware.get("selected_spark_label") == "DGX2" and hardware.get("scope") == "single_spark", "run node scope mismatch")
    _require(hardware.get("second_node_contacted") is False and hardware.get("tp2_touched") is False, "run distributed scope violated")
    _require(hardware.get("gpu_workload_executed") is False, "run claims a GPU workload")
    commands = run.get("commands")
    _require(isinstance(commands, list) and commands, "run commands missing")
    for command in commands:
        log_path = command.get("log_path", "")
        _require(isinstance(log_path, str) and log_path.startswith("evidence/runs/fnd-03/"), "unsafe command log path")
        _require((ROOT / log_path).is_file(), f"missing command log: {log_path}")
        for stream in ("stdout_log_path", "stderr_log_path"):
            stream_path = command.get(stream, "")
            _require(
                isinstance(stream_path, str) and stream_path.startswith("evidence/runs/fnd-03/"),
                f"missing or unsafe {stream}",
            )
            _require((ROOT / stream_path).is_file(), f"missing command stream log: {stream_path}")

    if not allow_unreviewed:
        review = run.get("review", {})
        _require(review.get("status") == "approved", "run review is not approved")
        _require(review.get("review_evidence") == lock.get("review_evidence"), "review evidence disagreement")

    return {
        "schema_version": 1,
        "task": "FND-03",
        "source_lock": "valid",
        "metadata_hashes": len(EXPECTED_ARTIFACT_HASHES),
        "top_level_revisions": len(EXPECTED_REVISIONS),
        "transitive_revisions": len(EXPECTED_TRANSITIVE_REVISIONS),
        "qwen_config": "structurally_equal",
        "cache": "complete_exact_revision",
        "cache_shards": 18,
        "scope": "single_spark",
        "review": lock["review_state"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-unreviewed",
        action="store_true",
        help="validate an implementation candidate before independent approval",
    )
    arguments = parser.parse_args()
    try:
        result = validate(allow_unreviewed=arguments.allow_unreviewed)
    except (KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"FND-03 evidence invalid: {error}") from error
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

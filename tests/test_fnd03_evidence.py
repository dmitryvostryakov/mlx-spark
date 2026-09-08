import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "runs" / "fnd-03"


def _load(path):
    return json.loads(path.read_text())


def _strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def test_source_lock_has_only_exact_top_level_and_transitive_revisions():
    lock = _load(ROOT / "configs" / "source-lock.resolved.json")
    assert lock["schema_version"] == 2
    assert all(re.fullmatch(r"[0-9a-f]{40}", source["revision"]) for source in lock["sources"].values())
    transitives = lock["sources"]["mlx"]["audit"]["transitive_source_pins"]
    assert len(transitives) == 7
    assert all(re.fullmatch(r"[0-9a-f]{40}", source["revision"]) for source in transitives.values())
    strings = list(_strings(lock))
    assert not any(value.lower() in {"main", "master", "latest"} for value in strings)
    assert lock["sources"]["mlx"]["audit"]["networked_build_allowed"] is False


def test_exact_qwen_config_and_cache_evidence_agree_without_overclaiming():
    lock = _load(ROOT / "configs" / "source-lock.resolved.json")
    cache = _load(EVIDENCE / "weight-cache-probe.stdout.log")
    qwen = lock["sources"]["qwen3_8_27b"]
    revision = qwen["revision"]
    assert qwen["audit"]["config_comparison"]["equal"] is True
    assert qwen["audit"]["config_comparison"]["changed_paths"] == []
    assert qwen["audit"]["weight_manifest"]["weight_payload_downloaded"] is False
    assert qwen["audit"]["weight_manifest"]["weight_payload_hashed"] is False
    assert cache["snapshot_revisions"] == [revision]
    assert cache["complete"] is True
    assert cache["network_used"] is False
    assert cache["files_modified"] is False
    assert cache["snapshots"][0]["metadata_hashes_match"] is True
    assert cache["snapshots"][0]["all_exact_index_shards_present"] is True
    assert cache["snapshots"][0]["expected_shard_count"] == 18
    assert cache["snapshots"][0]["present_shard_count"] == 18
    assert cache["snapshots"][0]["config_sha256"] == qwen["artifacts"]["config"]["sha256"]
    assert cache["snapshots"][0]["index_sha256"] == qwen["artifacts"]["weight_index"]["sha256"]
    assert (
        cache["snapshots"][0]["tokenizer_config_sha256"]
        == qwen["artifacts"]["tokenizer_config"]["sha256"]
    )


def test_fnd03_run_keeps_single_spark_and_no_runtime_claims():
    run = _load(EVIDENCE / "run.json")
    assert run["hardware"]["selected_spark_label"] == "DGX2"
    assert run["hardware"]["scope"] == "single_spark"
    assert run["hardware"]["gpu_workload_executed"] is False
    assert run["hardware"]["cuda_hardware_validation"] == "NOT_PERFORMED"
    assert run["hardware"]["second_node_contacted"] is False
    assert run["hardware"]["tp2_touched"] is False
    assert any("TP2" in item for item in run["unrun"])
    assert all((ROOT / command["log_path"]).is_file() for command in run["commands"])


def test_candidate_evidence_validator_is_replayable_offline():
    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_fnd03_evidence.py"), "--allow-unreviewed"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["source_lock"] == "valid"
    assert result["metadata_hashes"] == 24
    assert result["top_level_revisions"] == 4
    assert result["transitive_revisions"] == 7
    assert result["cache"] == "complete_exact_revision"
    assert result["scope"] == "single_spark"

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "probe_qwen_cache.py"
MODEL_CACHE_DIR = "models--Qwen--Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"


def _snapshot(cache_root: Path, revision: str = REVISION) -> Path:
    return cache_root / MODEL_CACHE_DIR / "snapshots" / revision


def _make_complete_cache(cache_root: Path, revision: str = REVISION) -> Path:
    snapshot = _snapshot(cache_root, revision)
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}\n")
    (snapshot / "tokenizer.json").write_text("{}\n")
    (snapshot / "tokenizer_config.json").write_text("{}\n")
    (snapshot / "model-00001-of-00002.safetensors").write_bytes(b"abc")
    (snapshot / "model-00002-of-00002.safetensors").write_bytes(b"12345")
    index = {
        "metadata": {"total_size": 8},
        "weight_map": {
            "layer.0.weight": "model-00001-of-00002.safetensors",
            "layer.1.weight": "model-00002-of-00002.safetensors",
            "layer.1.bias": "model-00002-of-00002.safetensors",
        },
    }
    (snapshot / "model.safetensors.index.json").write_text(json.dumps(index))
    return snapshot


def _run(cache_root: Path, revision: str | None = REVISION, *, env=None, expected_hashes=None):
    command = [sys.executable, str(PROBE), "--cache-root", str(cache_root)]
    if revision is not None:
        command.extend(("--revision", revision))
    for option, value in (expected_hashes or {}).items():
        command.extend((f"--expected-{option}-sha256", value))
    process = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    result = json.loads(process.stdout) if process.stdout else None
    return process, result


def _cache_state(cache_root: Path):
    state = []
    for path in sorted(cache_root.rglob("*")):
        relative = path.relative_to(cache_root).as_posix()
        if path.is_file():
            stat_result = path.stat()
            state.append((relative, "file", stat_result.st_mode, stat_result.st_mtime_ns, path.read_bytes()))
        elif path.is_dir():
            stat_result = path.stat()
            state.append((relative, "dir", stat_result.st_mode, stat_result.st_mtime_ns, None))
    return state


def test_complete_exact_revision_reports_only_sanitized_aggregate_facts(tmp_path):
    cache_root = tmp_path / "private-user" / "cache-on-build-host"
    _make_complete_cache(cache_root)

    process, result = _run(cache_root)

    assert process.returncode == 0, process.stderr
    assert process.stderr == ""
    snapshot = _snapshot(cache_root)
    assert result == {
        "audit_scope": "bounded_exact_hf_cache_roots",
        "complete": True,
        "files_modified": False,
        "found": True,
        "model_cache_directory_found": True,
        "model_id": "Qwen/Qwen3.8-27B",
        "network_used": False,
        "schema_version": 1,
        "sensitive_fields_emitted": False,
        "snapshot_revisions": [REVISION],
        "snapshots": [
            {
                "aggregate_present_bytes": 8,
                "all_exact_index_shards_present": False,
                "complete": True,
                "config_sha256": hashlib.sha256((snapshot / "config.json").read_bytes()).hexdigest(),
                "expected_shard_count": 2,
                "has_config": True,
                "has_index": True,
                "has_tokenizer": True,
                "has_tokenizer_config": True,
                "index_kind": "safetensors",
                "index_sha256": hashlib.sha256(
                    (snapshot / "model.safetensors.index.json").read_bytes()
                ).hexdigest(),
                "index_status": "parsed",
                "metadata_hashes_match": None,
                "present_shard_count": 2,
                "revision": REVISION,
                "tokenizer_config_sha256": hashlib.sha256(
                    (snapshot / "tokenizer_config.json").read_bytes()
                ).hexdigest(),
            }
        ],
    }
    rendered = process.stdout + process.stderr
    assert str(tmp_path) not in rendered
    assert "private-user" not in rendered
    assert "build-host" not in rendered


def test_expected_metadata_hashes_authenticate_exact_index_shard_set(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    expected = {
        "config": hashlib.sha256((snapshot / "config.json").read_bytes()).hexdigest(),
        "index": hashlib.sha256((snapshot / "model.safetensors.index.json").read_bytes()).hexdigest(),
        "tokenizer-config": hashlib.sha256((snapshot / "tokenizer_config.json").read_bytes()).hexdigest(),
    }

    process, result = _run(cache_root, expected_hashes=expected)

    assert process.returncode == 0, process.stderr
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["metadata_hashes_match"] is True
    assert snapshot_result["all_exact_index_shards_present"] is True
    assert snapshot_result["complete"] is True


def test_expected_index_hash_mismatch_fails_closed(tmp_path):
    cache_root = tmp_path / "hub"
    _make_complete_cache(cache_root)

    process, result = _run(cache_root, expected_hashes={"index": "f" * 64})

    assert process.returncode == 1
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["metadata_hashes_match"] is False
    assert snapshot_result["all_exact_index_shards_present"] is False
    assert snapshot_result["complete"] is False


def test_incomplete_snapshot_returns_one_and_counts_only_present_shards(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    (snapshot / "model-00002-of-00002.safetensors").unlink()

    process, result = _run(cache_root)

    assert process.returncode == 1
    assert result["found"] is True
    assert result["complete"] is False
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["expected_shard_count"] == 2
    assert snapshot_result["present_shard_count"] == 1
    assert snapshot_result["aggregate_present_bytes"] == 3
    assert snapshot_result["index_status"] == "parsed"


def test_unsafe_shard_name_is_rejected_without_path_traversal(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    outside = snapshot.parent / "outside-secret.safetensors"
    outside.write_bytes(b"do-not-count")
    index = {"weight_map": {"layer.weight": "../outside-secret.safetensors"}}
    (snapshot / "model.safetensors.index.json").write_text(json.dumps(index))

    process, result = _run(cache_root)

    assert process.returncode == 1
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["has_index"] is True
    assert snapshot_result["index_status"] == "unsafe_shard_name"
    assert snapshot_result["expected_shard_count"] == 0
    assert snapshot_result["present_shard_count"] == 0
    assert snapshot_result["aggregate_present_bytes"] == 0
    assert "outside-secret" not in process.stdout + process.stderr
    assert outside.read_bytes() == b"do-not-count"


def test_invalid_revision_is_usage_error_without_cache_path_disclosure(tmp_path):
    cache_root = tmp_path / "private-cache-root"
    cache_root.mkdir()

    process, result = _run(cache_root, "main")

    assert process.returncode == 2
    assert result is None
    assert "full 40-character hexadecimal SHA" in process.stderr
    assert str(cache_root) not in process.stderr


def test_probe_does_not_modify_cache_contents_or_mtimes(tmp_path):
    cache_root = tmp_path / "hub"
    _make_complete_cache(cache_root)
    before = _cache_state(cache_root)

    process, result = _run(cache_root)

    assert process.returncode == 0
    assert result["files_modified"] is False
    assert _cache_state(cache_root) == before


def test_without_revision_uses_only_exact_main_ref_and_snapshot(tmp_path):
    cache_root = tmp_path / "hub"
    _make_complete_cache(cache_root)
    refs = cache_root / MODEL_CACHE_DIR / "refs"
    refs.mkdir()
    (refs / "main").write_text(f"{REVISION}\n")

    process, result = _run(cache_root, None)

    assert process.returncode == 0
    assert result["snapshot_revisions"] == [REVISION]
    assert result["complete"] is True


def test_requested_revision_never_falls_back_to_main_ref(tmp_path):
    cache_root = tmp_path / "hub"
    other_revision = "a" * 40
    _make_complete_cache(cache_root, other_revision)
    refs = cache_root / MODEL_CACHE_DIR / "refs"
    refs.mkdir()
    (refs / "main").write_text(f"{other_revision}\n")

    process, result = _run(cache_root, REVISION)

    assert process.returncode == 1
    assert result["snapshot_revisions"] == []
    assert result["found"] is False
    assert result["complete"] is False


def test_standard_snapshot_symlinks_are_followed_without_emitting_paths(tmp_path):
    cache_root = tmp_path / "private-hub"
    snapshot = _make_complete_cache(cache_root)
    blobs = cache_root / MODEL_CACHE_DIR / "blobs"
    blobs.mkdir()
    for position, source in enumerate(sorted(snapshot.iterdir())):
        blob = blobs / f"blob-{position}"
        source.replace(blob)
        source.symlink_to(Path("..") / ".." / "blobs" / blob.name)

    process, result = _run(cache_root)

    assert process.returncode == 0, process.stderr
    assert result["complete"] is True
    assert result["snapshots"][0]["aggregate_present_bytes"] == 8
    assert result["snapshots"][0]["present_shard_count"] == 2
    assert str(cache_root) not in process.stdout + process.stderr


def test_configured_standard_hf_cache_roots_are_checked(tmp_path):
    configured = {
        "HF_HUB_CACHE": tmp_path / "hf-hub-cache",
        "HUGGINGFACE_HUB_CACHE": tmp_path / "legacy-hub-cache",
        "TRANSFORMERS_CACHE": tmp_path / "transformers-cache",
        "HF_HOME": tmp_path / "hf-home",
        "XDG_CACHE_HOME": tmp_path / "xdg-cache",
    }
    for variable, configured_root in configured.items():
        if variable == "HF_HOME":
            cache_root = configured_root / "hub"
        elif variable == "XDG_CACHE_HOME":
            cache_root = configured_root / "huggingface" / "hub"
        else:
            cache_root = configured_root
        _make_complete_cache(cache_root)
        isolated_home = tmp_path / f"empty-home-{variable.lower()}"
        isolated_home.mkdir()
        env = {
            "HOME": str(isolated_home),
            variable: str(configured_root),
            "PATH": os.environ.get("PATH", ""),
        }
        command = [sys.executable, str(PROBE), "--revision", REVISION]

        process = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        result = json.loads(process.stdout)

        assert process.returncode == 0, process.stderr
        assert result["complete"] is True
        assert result["snapshot_revisions"] == [REVISION]
        assert str(cache_root) not in process.stdout + process.stderr


def test_tokenizer_model_is_accepted_as_a_cached_tokenizer(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    (snapshot / "tokenizer.json").unlink()
    (snapshot / "tokenizer.model").write_bytes(b"tokenizer-data")

    process, result = _run(cache_root)

    assert process.returncode == 0, process.stderr
    assert result["snapshots"][0]["has_tokenizer"] is True
    assert result["complete"] is True


def test_pytorch_index_uses_only_safe_bin_basenames(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    (snapshot / "model.safetensors.index.json").unlink()
    for shard in snapshot.glob("*.safetensors"):
        shard.unlink()
    (snapshot / "pytorch_model-00001-of-00001.bin").write_bytes(b"weights")
    index = {
        "weight_map": {
            "layer.weight": "pytorch_model-00001-of-00001.bin",
        }
    }
    (snapshot / "pytorch_model.bin.index.json").write_text(json.dumps(index))

    process, result = _run(cache_root)

    assert process.returncode == 0, process.stderr
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["index_kind"] == "pytorch_bin"
    assert snapshot_result["index_status"] == "parsed"
    assert snapshot_result["aggregate_present_bytes"] == 7


def test_oversized_index_is_rejected_before_json_parsing(tmp_path):
    cache_root = tmp_path / "hub"
    snapshot = _make_complete_cache(cache_root)
    index = snapshot / "model.safetensors.index.json"
    with index.open("wb") as handle:
        handle.truncate(16 * 1024 * 1024 + 1)

    process, result = _run(cache_root)

    assert process.returncode == 1
    snapshot_result = result["snapshots"][0]
    assert snapshot_result["has_index"] is True
    assert snapshot_result["index_status"] == "too_large"
    assert snapshot_result["expected_shard_count"] == 0

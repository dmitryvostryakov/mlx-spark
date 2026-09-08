#!/usr/bin/env python3
"""Read-only, path-sanitized probe for the exact Qwen3.8-27B HF cache.

The probe performs no directory walk and no network or write operation.  It
constructs only the known model, ref, snapshot, metadata, and shard paths.  HF
snapshot symlinks are followed for file type and size checks, but paths and
filenames are never included in the result.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Iterable


MODEL_ID = "Qwen/Qwen3.8-27B"
MODEL_CACHE_DIR = "models--Qwen--Qwen3.8-27B"
INDEX_NAME = "model.safetensors.index.json"
PYTORCH_INDEX_NAME = "pytorch_model.bin.index.json"
INDEX_MAX_BYTES = 16 * 1024 * 1024
REF_MAX_BYTES = 128
_SHA_PATTERN = re.compile(r"[0-9a-fA-F]{40}\Z")
_SAFETENSORS_SHARD_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.safetensors\Z"
)
_PYTORCH_SHARD_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.bin\Z")
_SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")


def _revision_arg(value: str) -> str:
    if _SHA_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError(
            "revision must be a full 40-character hexadecimal SHA"
        )
    return value.lower()


def _sha256_arg(value: str) -> str:
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("expected metadata hash must be a 64-character hexadecimal SHA-256")
    return value.lower()


def _normalized_roots(candidates: Iterable[Path]) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            normalized = os.path.abspath(os.path.expanduser(os.fspath(candidate)))
        except (OSError, RuntimeError, TypeError, ValueError):
            continue
        key = os.path.normcase(normalized)
        if key not in seen:
            seen.add(key)
            roots.append(Path(normalized))
    return roots


def _standard_cache_roots() -> list[Path]:
    candidates: list[Path] = []

    # Direct hub-cache settings, including the legacy variable still honored
    # by huggingface_hub installations.
    for variable in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE"):
        value = os.environ.get(variable)
        if value:
            candidates.append(Path(value))

    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        candidates.append(Path(hf_home) / "hub")

    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        candidates.append(Path(xdg_cache_home) / "huggingface" / "hub")

    try:
        candidates.append(Path.home() / ".cache" / "huggingface" / "hub")
    except (OSError, RuntimeError):
        pass

    return _normalized_roots(candidates)


def _read_bounded_regular(path: Path, limit: int) -> tuple[bytes | None, str, bool]:
    """Return bytes, status, and whether an entry appeared to exist.

    O_NONBLOCK prevents an unexpected special file from blocking before fstat
    rejects it.  The normal HF symlinks are deliberately followed by os.open.
    """

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None, "missing", False
    except OSError as error:
        exists = error.errno not in (errno.ENOENT, errno.ENOTDIR)
        return None, "unreadable", exists

    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            return None, "not_regular", True
        if file_stat.st_size > limit:
            return None, "too_large", True

        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > limit:
            return None, "too_large", True
        return data, "ok", True
    except OSError:
        return None, "unreadable", True
    finally:
        os.close(descriptor)


def _regular_file_size(path: Path) -> int | None:
    try:
        file_stat = path.stat()
    except (OSError, ValueError):
        return None
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size < 0:
        return None
    return file_stat.st_size


def _is_directory(path: Path) -> bool:
    try:
        return stat.S_ISDIR(path.stat().st_mode)
    except (OSError, ValueError):
        return False


def _read_main_revision(model_cache: Path) -> str | None:
    data, status, _ = _read_bounded_regular(model_cache / "refs" / "main", REF_MAX_BYTES)
    if status != "ok" or data is None:
        return None
    try:
        revision = data.decode("ascii").strip()
    except UnicodeDecodeError:
        return None
    if _SHA_PATTERN.fullmatch(revision) is None:
        return None
    return revision.lower()


def _safe_shard_name(value: object, index_kind: str) -> str | None:
    patterns = {
        "safetensors": _SAFETENSORS_SHARD_PATTERN,
        "pytorch_bin": _PYTORCH_SHARD_PATTERN,
    }
    if not isinstance(value, str) or patterns[index_kind].fullmatch(value) is None:
        return None
    if value in (".", "..") or "/" in value or "\\" in value:
        return None
    return value


def _read_index(
    snapshot: Path,
) -> tuple[bool, str | None, tuple[str, ...], str, str | None]:
    index_kind = "safetensors"
    data, status, exists = _read_bounded_regular(snapshot / INDEX_NAME, INDEX_MAX_BYTES)
    if status == "missing":
        index_kind = "pytorch_bin"
        data, status, exists = _read_bounded_regular(
            snapshot / PYTORCH_INDEX_NAME, INDEX_MAX_BYTES
        )
    if status != "ok" or data is None:
        errors = {
            "missing": "absent",
            "too_large": "too_large",
            "not_regular": "not_regular",
            "unreadable": "unreadable",
        }
        return exists, index_kind if exists else None, (), errors[status], None

    index_sha256 = hashlib.sha256(data).hexdigest()

    try:
        document = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, RecursionError, UnicodeDecodeError):
        return True, index_kind, (), "parse_error", index_sha256
    if not isinstance(document, dict):
        return True, index_kind, (), "invalid_weight_map", index_sha256
    weight_map = document.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        return True, index_kind, (), "invalid_weight_map", index_sha256

    shards: set[str] = set()
    for value in weight_map.values():
        shard = _safe_shard_name(value, index_kind)
        if shard is None:
            error = "unsafe_shard_name" if isinstance(value, str) else "invalid_weight_map"
            return True, index_kind, (), error, index_sha256
        shards.add(shard)
    if not shards:
        return True, index_kind, (), "invalid_weight_map", index_sha256
    return True, index_kind, tuple(sorted(shards)), "parsed", index_sha256


def _bounded_sha256(path: Path, limit: int = INDEX_MAX_BYTES) -> tuple[bool, str | None]:
    data, status, _ = _read_bounded_regular(path, limit)
    if status != "ok" or data is None:
        return False, None
    return True, hashlib.sha256(data).hexdigest()


def _empty_result() -> dict[str, object]:
    return {
        "audit_scope": "bounded_exact_hf_cache_roots",
        "complete": False,
        "files_modified": False,
        "found": False,
        "model_cache_directory_found": False,
        "model_id": MODEL_ID,
        "network_used": False,
        "schema_version": 1,
        "sensitive_fields_emitted": False,
        "snapshot_revisions": [],
        "snapshots": [],
    }


def _probe_snapshot(
    snapshot: Path,
    revision: str,
    expected_hashes: dict[str, str],
) -> dict[str, object] | None:
    if not _is_directory(snapshot):
        return None

    has_config, config_sha256 = _bounded_sha256(snapshot / "config.json")
    has_tokenizer = bool(
        _regular_file_size(snapshot / "tokenizer.json") is not None
        or _regular_file_size(snapshot / "tokenizer.model") is not None
        or (
            _regular_file_size(snapshot / "vocab.json") is not None
            and _regular_file_size(snapshot / "merges.txt") is not None
        )
    )
    has_tokenizer_config, tokenizer_config_sha256 = _bounded_sha256(snapshot / "tokenizer_config.json")

    has_index, index_kind, shards, index_status, index_sha256 = _read_index(snapshot)
    index_parsed = index_status == "parsed"

    present_shards = 0
    aggregate_bytes = 0
    if index_parsed:
        for shard in shards:
            shard_size = _regular_file_size(snapshot / shard)
            if shard_size is not None:
                present_shards += 1
                aggregate_bytes += shard_size
    structural_complete = bool(
        has_config
        and has_tokenizer
        and index_parsed
        and shards
        and present_shards == len(shards)
    )
    observed_hashes = {
        "config": config_sha256,
        "index": index_sha256,
        "tokenizer_config": tokenizer_config_sha256,
    }
    metadata_hashes_match = None
    if expected_hashes:
        metadata_hashes_match = all(observed_hashes[name] == expected for name, expected in expected_hashes.items())
    all_exact_index_shards_present = bool(
        expected_hashes.get("index")
        and index_sha256 == expected_hashes["index"]
        and index_parsed
        and shards
        and present_shards == len(shards)
    )
    complete = structural_complete and metadata_hashes_match is not False
    return {
        "aggregate_present_bytes": aggregate_bytes,
        "all_exact_index_shards_present": all_exact_index_shards_present,
        "complete": complete,
        "config_sha256": config_sha256,
        "expected_shard_count": len(shards),
        "has_config": has_config,
        "has_index": has_index,
        "has_tokenizer": has_tokenizer,
        "has_tokenizer_config": has_tokenizer_config,
        "index_kind": index_kind,
        "index_sha256": index_sha256,
        "index_status": index_status,
        "metadata_hashes_match": metadata_hashes_match,
        "present_shard_count": present_shards,
        "revision": revision,
        "tokenizer_config_sha256": tokenizer_config_sha256,
    }


def _probe_rank(result: dict[str, object]) -> tuple[int, int, int]:
    return (
        int(bool(result["complete"])),
        int(result["present_shard_count"]),
        int(result["aggregate_present_bytes"]),
    )


def probe(
    cache_roots: Iterable[Path],
    revision: str | None,
    expected_hashes: dict[str, str] | None = None,
) -> dict[str, object]:
    roots = _normalized_roots(cache_roots)
    expected_hashes = expected_hashes or {}
    best_by_revision: dict[str, dict[str, object]] = {}
    model_cache_directory_found = False
    for cache_root in roots:
        model_cache = cache_root / MODEL_CACHE_DIR
        model_cache_directory_found |= _is_directory(model_cache)
        candidate_revision = revision or _read_main_revision(model_cache)
        if candidate_revision is None:
            continue
        snapshot = model_cache / "snapshots" / candidate_revision
        candidate = _probe_snapshot(snapshot, candidate_revision, expected_hashes)
        if candidate is None:
            continue
        previous = best_by_revision.get(candidate_revision)
        if previous is None or _probe_rank(candidate) > _probe_rank(previous):
            best_by_revision[candidate_revision] = candidate

    snapshots = [best_by_revision[key] for key in sorted(best_by_revision)]
    result = _empty_result()
    result["model_cache_directory_found"] = model_cache_directory_found
    result["found"] = any(item["present_shard_count"] > 0 for item in snapshots)
    result["snapshot_revisions"] = [item["revision"] for item in snapshots]
    result["snapshots"] = snapshots
    result["complete"] = any(item["complete"] for item in snapshots)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only bounded probe for cached Qwen/Qwen3.8-27B artifacts."
    )
    parser.add_argument(
        "--revision",
        type=_revision_arg,
        help="exact full model revision; when omitted, read only the exact refs/main file",
    )
    parser.add_argument(
        "--cache-root",
        action="append",
        type=Path,
        help="explicit HF hub cache root (repeatable); disables standard-root discovery",
    )
    parser.add_argument("--expected-config-sha256", type=_sha256_arg)
    parser.add_argument("--expected-index-sha256", type=_sha256_arg)
    parser.add_argument("--expected-tokenizer-config-sha256", type=_sha256_arg)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    expected_hashes = {
        name: value
        for name, value in {
            "config": arguments.expected_config_sha256,
            "index": arguments.expected_index_sha256,
            "tokenizer_config": arguments.expected_tokenizer_config_sha256,
        }.items()
        if value is not None
    }
    if expected_hashes and arguments.revision is None:
        raise SystemExit("expected metadata hashes require --revision")
    roots = (
        _normalized_roots(arguments.cache_root)
        if arguments.cache_root
        else _standard_cache_roots()
    )
    result = probe(roots, arguments.revision, expected_hashes)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

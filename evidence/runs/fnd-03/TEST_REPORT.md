# FND-03 test report

Implementation commit: `bb90847652028350a144bc738d7a50c12c57cbe1`; review-remediation candidate:
`06222b0bcdc43ac8e775c5316ac4a6ddb22137a0`.

- Source/cache contracts: 37 passed. These cover strict candidate allowlists, exact revision round trips, immutable
  artifact URLs, metadata hashes, normalized config comparison, license/source markers, no weight payload fetch,
  no mutable executable refs, fail-closed/no-overwrite output, cache privacy, bounded index parsing, safe shard
  basenames, exact revision selection, authenticated local metadata/index, symlinked HF blobs, no writes, and
  incomplete/mismatched-cache failure.
- Candidate evidence contracts: 4 passed; the offline validator checks 24 exact artifact hashes, four top-level and
  seven transitive revisions, Qwen config/provenance, authenticated cache metadata, command logs, and scope guards.
- Full local scaffold after review remediation: 105 Python tests passed and one C++ host contract test passed.
- DGX2 cache probe: exit 0; exact revision complete, 18/18 shards, 55,563,006,776 aggregate bytes; no network/write.

These tests do not claim CUDA compilation, source build reproducibility, source import safety, weight-byte integrity,
Qwen inference/correctness, framework training, or TP2.

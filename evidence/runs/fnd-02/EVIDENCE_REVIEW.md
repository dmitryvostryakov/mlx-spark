# FND-02 hardware and evidence review

Reviewed candidate: `a127e17d45b5cec201e45029faeff2b9d475a641`.

Initial verdict: **changes requested**.

The independent reviewer accepted the anonymized read-only hardware facts and the conservative budget arithmetic.
The candidate correctly kept CUDA execution/compatibility unvalidated, left nvcc/cuDNN explicit unknowns, did not
double-count UMA, did not authorize weights, and did not touch a second node or TP2.

Required evidence-fidelity remediation:

1. Replace a descriptive pseudo-command in `run.json` with a literal replayable validator and exact raw output.
2. Extend acceptance tests to pin the approved stdin SSH payload, CUDA-not-performed claim, toolchain unknowns,
   referenced logs, and second-node/TP2 guards.

Remediation adds `tools/validate_fnd02_evidence.py`, expands `tests/test_fnd02_evidence.py`, and retains the old
raw validation summary as explicitly superseded and unused for acceptance.

## Final verdict

**APPROVE** for remediation state `7b0c1421b33c8606db77f68a2aa035c298260539`; no remaining findings.

- `python3 tools/validate_fnd02_evidence.py`: exit 0; stdout byte-matches the retained final validation log.
- Historical pseudo-command is absent from active commands; superseded summaries are not used for acceptance.
- Evidence contracts: 4 passed; full local suite: 64 Python + 1 C++ host contract test.
- `run.json` schema and all referenced logs validated; workspace was clean at review.

The approval accepts read-only DGX2 inventory and conservative resource caps. CUDA execution and toolchain
compatibility remain explicitly unvalidated; second-node and TP2 work remain deferred.

A second independent archive-based audit confirmed the same state: validator output byte-match, 4/4 evidence tests,
schema valid, all active log references present, no active pseudo-command, unchanged inventory/budget blobs, and
single-DGX2 scope. It also returned **APPROVE** with no findings.

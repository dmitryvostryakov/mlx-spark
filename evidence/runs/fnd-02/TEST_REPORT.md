# FND-02 partial test report

State: FND-02 accepted; DGX2 inventory collected read-only; resource budget and evidence approved independently.
Two independent re-reviews approved state `7b0c1421b33c8606db77f68a2aa035c298260539` with no findings.

## Contract-first baselines

The original inventory contract failed against the pre-implementation doctor because `inventory()` had no
working-filesystem argument. After independent review, four new safety contracts failed before remediation because
DGX OS, nested cgroup, and safe version helpers did not exist. A later hybrid-cgroup contract also reproduced
selection of generic v2 over an explicit finite v1 memory controller. Raw text is retained in the baseline logs.

## Implementation checks

- `PYTHONPATH=src python3 -m pytest -q tests/test_doctor.py`: exit 0, 11 passed.
- `bash scripts/check_local.sh`: exit 0, 60 Python tests and 1 C++ host contract test passed.
- `python3 -m compileall -q src/mlx_spark/runtime/doctor.py`: exit 0.
- `git diff --check`: exit 0.
- `run.json` validated against `schemas/run.schema.json`; JSON/plan/diff/privacy checks passed.

## DGX2 evidence checks

- Standalone doctor over `ssh dgx2`: exit 0; exact anonymized stdout retained as `inventory.json`.
- Initial actual-evidence suite: 2 passed; after evidence-fidelity review remediation: 4 passed.
- Final remediation full suite: exit 0, 64 Python tests and 1 C++ host contract test passed.
- `python3 tools/validate_fnd02_evidence.py`: exit 0 with inventory/budget/privacy/run/scope valid and all logs present.
- Post-approval integration check: 4 evidence tests, 64 Python tests, and 1 C++ host test passed; DAG exposes FND-03.
- The evidence tests require Linux aarch64, exactly one GB10 at compute capability 12.1, no identifying JSON keys,
  and verify the memory/disk reserve arithmetic.

## Hardware boundary

Only the standalone read-only inventory ran on DGX2. No CUDA allocation, compilation, kernel, stress, model, or
training test ran. `nvcc` was unavailable and cuDNN remained unknown; version facts do not prove compatibility.

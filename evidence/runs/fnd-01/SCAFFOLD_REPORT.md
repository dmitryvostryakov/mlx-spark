# FND-01 scaffold report

Timestamp UTC: 2026-09-08T07:33:13Z

## Outcome

The delivered single-Spark scaffold is reproducible on the local Darwin arm64 development host after a narrow
Python-selection correction and synchronized startup documentation. It remains an engineering scaffold, not an
implemented MLX-Spark runtime.

## Contract accepted for this phase

- Product goal: a complete, standalone MLX-like framework, including arrays, lazy execution, compile, autodiff,
  transforms, nn, optimizers, training, quantization, serialization, and Python/C++ SDKs.
- Phase-one hardware boundary: one selected DGX Spark and one visible GB10 GPU.
- First large model: Qwen/Qwen3.8-27B; it is an acceptance workload, not a restriction on the general framework API.
- TP2, NCCL, QSFP diagnostics, SSH, and any second-node implementation remain deferred until every stable
  single-Spark release gate passes.

## Reproduced baseline

Calling `mlx_spark.core.array` exits with `NativeCoreUnavailable`; this is the expected honest starting point.
The first two local-check attempts failed at `tools/validate_plan.py` because the harness resolved bare `python` to
Python 2.7. The validator was already valid Python 3; an interim whitespace-only edit was reverted. Both failed attempts
are preserved as raw logs.

## Narrow corrections

- `scripts/check_local.sh`: use `python3` by default, allow an explicit `MLX_SPARK_PYTHON` override, and reject
  interpreters older than Python 3.11 before running tests.
- `AGENTS.md`, `README.md`, `handoff/FIRST_SESSION.md`, `handoff/MASTER_PROMPT.md`, and the bundle reproduction
  instructions: use `python3`; the first-session path also checks Python 3.11+ explicitly.
- `tests/test_check_local.py`: verify that an unsupported interpreter fails early with an actionable message.

No tensor, CUDA, model, distributed, precision, tolerance, or release-gate behavior changed.

## Verification

- Delivered manifest before edits: 233/233 entries matched.
- Task DAG: 91 tasks, acyclic; 85 single-Spark and 6 deferred TP2.
- Python/reference suite: 49 passed; no skips reported.
- C++ host contracts: 1/1 passed.
- Final status: `scaffold_only`; native core, Qwen inference, framework training, and CUDA validation are false.
- Memory estimate at 32768 tokens remains estimate-only with an `UNKNOWN` fit verdict.

The first two independent review cycles requested changes for interpreter selection, evidence metadata, and commit
binding. The two task-generated hostname-bearing JUnit files were discarded without rewriting their bytes. A delivered
validation JUnit with generic hostname metadata was removed from the current tree; its original bytes remain in the
immutable ZIP/base commit, while the safe raw text report remains. A regression now scans shareable evidence for JUnit
hostname attributes.
Hardware, CUDA, model, training, and performance gates were not run and are not claimed.

Independent approval for exact state submission `455f84b4375ebf0be8654e6c55f1591876442532` is recorded in
`REVIEW_APPROVAL.md`: 49 Python tests, 1 C++ host test, and all 80 submission hashes were independently verified.

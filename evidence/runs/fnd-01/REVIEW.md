# FND-01 — independent review

- Reviewer role: Luna.
- Reviewed base: `e12c8cbe002b5c44db53ccd2c04c156ecebfe68c`.
- Reviewed implementation: `195cf336e2475f36d401503ee8412d4da1ab6b41`.
- Review timestamp: `2026-09-08T07:43:00Z`.
- Decision: **Changes requested**.

## Outcome

The two-file implementation diff is narrow and its local CPU/scaffold behavior is green. It does not implement or
enable TP2, NCCL, SSH, a second node, CUDA, Qwen inference, framework-native training, or an external tensor backend.
The complete standalone framework remains the stated product goal, and Qwen/Qwen3.8-27B remains only the first large
acceptance workload.

FND-01 is not accepted yet because the evidence violates the log-safety contract, the mandatory first-session commands
remain non-reproducible on the observed host, and the recorded explanation attributes a real interpreter-selection
failure to a nonexistent Python 3 syntax defect.

## Required changes before re-review

1. **Remove host identity from shareable evidence without rewriting captured bytes.** Both `pytest.xml` and `ctest.xml`
   contain a non-empty JUnit `hostname` attribute. This violates `AGENTS.md` section 7. Preserve/quarantine the original
   captures according to evidence policy, generate replacement test evidence without host identity, and update all
   evidence references and hashes to point at the safe artifacts.

2. **Make the mandatory session commands select a supported Python consistently.** `handoff/FIRST_SESSION.md`,
   `handoff/MASTER_PROMPT.md`, `README.md`, and `AGENTS.md` still prescribe bare `python`, while the observed command is
   Python 2.7.15 and the project requires Python 3.11+. In a clean implementation tree,
   `python tools/validate_plan.py` exits 1 with `SyntaxError`; in the untouched delivery,
   `python tools/check_integrity.py` exits 1 because `pathlib` is unavailable. Update the actionable instructions and
   add a clear supported-version check or equivalent fail-fast behavior. Re-run the exact `FIRST_SESSION.md` commands.

3. **Correct the evidence narrative about `tools/validate_plan.py`.** The base file compiles and runs with Python 3;
   `git diff -w` proves the implementation change to that file is whitespace-only. Therefore the statements in
   `run.json` observations and `SCAFFOLD_REPORT.md` that the path expression was made valid Python 3 syntax are false.
   Record the actual root cause—bare `python` selected Python 2.7—and either retain the formatting as a no-op or remove
   it in the remediation change.

4. **Bind evidence and state to a reviewable commit.** Commit `195cf336e2475f36d401503ee8412d4da1ab6b41` contains only
   the two implementation files. At review time `evidence/runs/fnd-01/` and `handoff/claims/` were untracked, while
   `planning/tasks.json` and `handoff/checkpoints/CURRENT.md` were modified outside that commit. Thus the implementation
   SHA alone does not immutably identify the submitted evidence/state snapshot. After remediation, record the exact
   evidence hashes and commit the reviewable evidence/claim/state transition; keep the task non-done until the new
   independent review accepts that snapshot.

The implementation/source was not modified by this review. `planning/tasks.json`, `CONTEXT.md`, and the current
checkpoint were not modified. Keep FND-01 non-done until remediation receives a new independent review.

## Independent checks and results

All checks were local, offline, CPU/scaffold-only. The full suite was run from a clean `git archive` of the exact
implementation commit so the dirty shared working tree could not affect results.

| Check | Exit | Observed result | Reviewer logs |
|---|---:|---|---|
| `bash scripts/check_local.sh` in clean implementation archive | 0 | DAG 91/acyclic; 85 single-Spark and 6 deferred; 47 Python tests passed; 1 C++ host test passed; status `scaffold_only` | `reviewer-luna-20260908T073808Z-check-local.{stdout,stderr}.log` |
| Original ZIP SHA-256 plus `python3 tools/check_integrity.py` in extracted delivery | 0 | ZIP hash matches handoff; 233 manifest entries checked, zero errors | `reviewer-luna-20260908T073808Z-integrity.{stdout,stderr}.log` |
| `command -v` and version queries for `python`/`python3` | 0 | Bare `python` is 2.7.15; `python3` is 3.14.3 | `reviewer-luna-20260908T073808Z-python-selection.{stdout,stderr}.log` |
| Expected native-core-unavailable probe in clean implementation archive | 0 | `NativeCoreUnavailable` observed; message identifies scaffold and rejects installed MLX/PyTorch substitution | `reviewer-luna-20260908T073808Z-native-core.{stdout,stderr}.log` |
| `git diff --check`, changed-path audit, base Python 3 compile, and whitespace-insensitive validator diff | 0 | Only `scripts/check_local.sh` and `tools/validate_plan.py`; validator change is whitespace-only and base compiles with Python 3 | `reviewer-luna-20260908T073808Z-diff.{stdout,stderr}.log` |
| `shellcheck`, `bash -n`, and Python 3 compile of changed files | 0 | No diagnostics | `reviewer-luna-20260908T073808Z-static.{stdout,stderr}.log` |
| `run.json` schema/log/JUnit/scope audit | 3 | Schema valid; 10/10 referenced logs exist; JUnit reports 47 + 1 passing tests with zero skip/failure; six TP2 tasks deferred; exit 3 intentionally reports forbidden hostname metadata in two XML files | `reviewer-luna-20260908T073808Z-evidence-audit.{stdout,stderr}.log` |
| Exact `python tools/validate_plan.py` from `FIRST_SESSION.md` in clean implementation archive | 1 | Python 2.7 syntax failure | `reviewer-luna-20260908T073808Z-first-session-validate.{stdout,stderr}.log` |
| Exact `python tools/check_integrity.py` from `FIRST_SESSION.md` in untouched delivery | 1 | Python 2.7 cannot import `pathlib` | `reviewer-luna-20260908T073808Z-first-session-integrity.{stdout,stderr}.log` |

The nonzero exits above are reproduced acceptance defects, not passed tests.

## Evidence and scope assessment

- `run.json` names the exact base and implementation commits, validates against `schemas/run.schema.json`, references
  ten existing command logs, identifies the execution host only generically as Darwin/arm64, and explicitly says no
  selected DGX Spark or GPU was queried.
- The reported test counts agree with both raw stdout and JUnit counts: 47 Python/reference tests and 1 C++ host test;
  no skipped, disabled, failed, or errored tests are reported.
- The status artifact is honest: native core, Qwen inference, framework training, and CUDA validation are false; TP2 is
  deferred. The native-core probe fails closed rather than importing an installed tensor framework.
- All six TP2 task records remain `phase=tp2_deferred` and `status=deferred`. The implementation diff adds no network,
  distributed, NCCL, SSH, model, CUDA, training, dependency, license, or API behavior.
- The memory output is clearly estimate-only and retains an `UNKNOWN` fit verdict.

## Explicitly not verified

No DGX Spark inventory or hardware identity was verified. No GB10 GPU, CUDA compilation/execution, Qwen weights or
inference, vision, MTP, LoRA/QLoRA, native arrays, lazy execution, compile, autodiff/transforms, nn, optimizers,
framework training, quantization, serialization, performance, memory fit, release gate, network, second node, or TP2
work was run or accepted. This review approves neither a native framework nor a single-Spark release.

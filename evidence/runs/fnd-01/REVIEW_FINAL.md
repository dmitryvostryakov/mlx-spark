# FND-01 — remediation re-review

- Reviewer role: Luna.
- Base: `e12c8cbe002b5c44db53ccd2c04c156ecebfe68c`.
- Final implementation: `8b4f5b4370424b5a441f4901f7618441f5aaea50`.
- Reviewable evidence/state submission: `6ab17005fa22d0f989f1eb23a4c7ab0cd2dcac82`.
- Decision: **Changes requested**.

## Blocking finding

The hostname remediation is incomplete under the repository-wide log-safety contract. The two offending FND-01
artifacts, `evidence/runs/fnd-01/pytest.xml` and `evidence/runs/fnd-01/ctest.xml`, are absent from the submission, but
`evidence/validation/pytest.xml` remains tracked and contains a non-empty JUnit `hostname` attribute.
`evidence/BUNDLE_VALIDATION.md` still cites that XML as evidence. This conflicts with the unconditional prohibition in
`AGENTS.md` section 7 and with the re-review requirement that no hostname-bearing evidence/JUnit remain.

Remove the shareable tracked XML without rewriting its captured bytes, update the evidence documentation, and add a
regression that rejects hostname attributes in shareable XML/evidence. The immutable base commit and original ZIP can
retain historical recoverability. Submit a new exact evidence/state commit for another independent review.

## Status of the four requested remediations

1. **Hostname-bearing evidence/JUnit: not fully closed.** FND-01-local XML files were removed, but the tracked validation
   JUnit described above remains.
2. **Supported Python and fail-fast guard: closed by diff inspection.** Mandatory startup commands in `AGENTS.md`,
   `README.md`, `handoff/FIRST_SESSION.md`, and `handoff/MASTER_PROMPT.md` use `python3`; the startup documents explicitly
   check Python 3.11+, `scripts/check_local.sh` rejects an unsupported interpreter before the suite, and
   `tests/test_check_local.py` covers the fail-fast result.
3. **False validator syntax narrative/no-op diff: closed by diff inspection.** `tools/validate_plan.py` has no net diff
   from the base (`git diff --exit-code`, exit 0). `run.json` and `SCAFFOLD_REPORT.md` now correctly identify bare Python
   2.7 selection as the original failure and say the interim whitespace-only edit was reverted.
4. **Reviewable evidence/state binding: structurally closed.** Submission `6ab1700` is a descendant of implementation
   `8b4f5b4` and commits the FND-01 evidence, claim, `planning/tasks.json`, and current checkpoint. The claim points to
   `8b4f5b4`, task status remains `in_progress`, and `SUBMISSION.sha256` is present. Hash replay was not performed after
   the blocking hostname finding, so this cycle does not independently approve the hash set.

## Commands and exit codes

All commands were read-only and evaluated against the named Git objects.

| Command/check | Exit | Result |
|---|---:|---|
| `git status --short --branch` and `git rev-parse HEAD` | 0 | Clean `main`; HEAD is submission `6ab1700` |
| `git merge-base --is-ancestor e12c8cb 8b4f5b4` | 0 | Base ancestry verified |
| `git merge-base --is-ancestor 8b4f5b4 6ab1700` | 0 | Implementation-to-submission ancestry verified |
| `git diff --check e12c8cb 6ab1700` | 0 | No whitespace errors |
| `git diff --exit-code e12c8cb 8b4f5b4 -- tools/validate_plan.py` | 0 | No net validator change |
| Search under `evidence/runs/fnd-01/` for hostname attributes and JUnit/XML files | 0 | No offending FND-01 XML remains |
| Repository-wide search under `evidence/` for hostname attributes/JUnit XML | 0 | Found `evidence/validation/pytest.xml` with a non-empty hostname attribute |
| Inspection of `run.json`, reports, claim, task, checkpoint, submission manifest, and remediation diff via `git show` | 0 | Other three requested remediations are represented in the exact submission |

The re-review stopped at the deterministic policy violation. No new suite result is claimed and no new reviewer raw
log was created, avoiding propagation of the forbidden hostname-bearing line into another log.

## Explicitly not verified in this cycle

The requested clean-archive CPU/scaffold rerun and independent `SUBMISSION.sha256` replay were not performed after the
blocking evidence finding. No DGX Spark inventory, GB10 GPU, CUDA compilation/execution, Qwen weights or inference,
vision, MTP, LoRA/QLoRA, native arrays, lazy execution, compile, autodiff/transforms, nn, optimizers, framework training,
quantization, serialization, performance, memory fit, release gate, network, second node, or TP2 work was run or
accepted. The complete standalone framework remains the goal; this review does not approve a native framework or a
single-Spark release.

This review modified no source, task state, context, checkpoint, claim, run record, prior review, or submission hash.

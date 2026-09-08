# Contributing to MLX-Spark

MLX-Spark is pre-alpha. The most useful contributions right now make the eventual framework more correct, auditable, and reproducible; they do not paper over missing runtime functionality.

## Before you begin

1. Read the public overview in `README.md`, the current status in `STATUS.json`, and the relevant document under `docs/`.
2. Check `planning/tasks.json` and the matching task card in `planning/tasks/` so that the work has an accepted scope and dependency state.
3. Open an issue or discussion before starting a substantial change. One focused problem per pull request makes review and evidence much clearer.

## Expectations for pull requests

- Keep the change narrow and describe the intended contract, limitations, and acceptance test.
- Add or update tests for behavior changes. A skipped test, an identity `compile`, or a hidden fallback to another tensor framework is not an implementation.
- Run the relevant checks locally. `bash scripts/check_local.sh` is the baseline CPU scaffold suite; it is not evidence of CUDA or model correctness.
- State which checks ran, their results, and which hardware-dependent checks remain unrun.
- Preserve provenance and notices for any imported material. Do not add a dependency, model artifact, or generated source without an explicit reviewable reason and immutable version or hash.

## Boundaries that matter

- Do not add model weights, private data, credentials, machine identifiers, or benchmark artifacts containing sensitive host information.
- Do not make system changes, driver updates, network scans, or heavyweight GPU workloads as part of a contribution.
- Do not add TP=2, NCCL, remote execution, a web server, or application-specific integrations during the single-Spark phase.
- Reference/oracle environments may use external libraries, but the released MLX-Spark runtime may not hide an installed MLX, PyTorch, Transformers, vLLM, SGLang, or NumPy backend.

`AGENTS.md` is the project's detailed engineering contract. It governs implementation work where it is more specific than this guide.

## License note

The project license has not yet been selected. Please do not submit a contribution until you are comfortable with the repository owner deciding and publishing the applicable contribution and distribution terms. Existing notices and third-party licenses must remain intact.

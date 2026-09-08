<div align="center">

# MLX-Spark

### An independent, NVIDIA-native machine-learning framework — built for DGX Spark.

**Current stage:** engineering scaffold · **First hardware target:** one DGX Spark / GB10 · **First large-model acceptance workload:** Qwen3.8-27B

</div>

> [!WARNING]
> MLX-Spark is under active construction. It is **not yet a production tensor framework** and does not run Qwen inference or training. The repository intentionally exposes this boundary rather than substituting an installed MLX, PyTorch, or another backend behind a familiar API.

## The project

MLX-Spark aims to be a complete, independent MLX-like development environment for NVIDIA hardware: arrays, lazy execution, compilation, autodiff, function transforms, neural-network modules, optimizers, serialization, and Python/C++ SDKs.

The project starts with a single visible GB10 GPU in a DGX Spark. Distributed execution and TP=2 are deliberately deferred until the single-node framework is complete and hardware-validated. Qwen3.8-27B is the first large-model acceptance workload, not the framework's entire scope.

## Why we built this

We built MLX-Spark because experimenting with a new NVIDIA platform should not force a choice between an opaque production stack and a pile of disconnected CUDA prototypes. We wanted one coherent place to understand the whole path: from an array and its gradient to memory ownership, kernel dispatch, model state, training, and a real large-model workload.

DGX Spark makes that question especially interesting. It is a compact Arm + GB10 system with shared physical memory, but shared memory does not remove the hard parts: allocation semantics, synchronization, layouts, numerical precision, and device execution still need explicit, testable contracts. A familiar Python API is valuable only when those contracts remain visible and correct.

MLX-Spark is our attempt to build that path in the open. Rather than hiding another tensor framework behind an MLX-like interface, we are building an independent runtime whose behavior can be inspected, tested, and improved from the bottom up. The point is not to declare a replacement for mature frameworks. It is to earn a small, trustworthy foundation on NVIDIA hardware and expand it only when the evidence supports it.

Open development is part of the design. Every meaningful claim should have a reproducer, a test, or a recorded measurement; every unsupported feature should fail clearly instead of silently falling back. That makes the repository useful even before it is feature-complete: contributors can see the real constraints, challenge the design, and help turn a scaffold into a dependable framework.

## What is available today

| Available and tested on CPU | Not implemented or validated yet |
| --- | --- |
| CLI status, diagnostics, and memory estimates | Production array/tensor backend |
| Configuration and release-gate validation | Autodiff, `compile`, `nn`, and optimizers |
| NumPy reference oracles for GDN/GQA, including an analytic GDN VJP | Qwen weight loading, inference, or training |
| C++ host-side contracts | CUDA build/runtime correctness on a GB10 |
| Task DAG, evidence validation, and fail-closed checks | Performance claims, releases, or TP=2 |

CUDA probe and GDN reference sources are included as candidates only. They have not been validated on target hardware. The canonical machine-readable status is [`STATUS.json`](STATUS.json); the evidence boundary is documented in [`evidence/BUNDLE_VALIDATION.md`](evidence/BUNDLE_VALIDATION.md).

## Try the scaffold

The following commands require Python 3.11+ and neither network access nor a GPU:

```bash
git clone https://github.com/dmitryvostryakov/mlx-spark.git
cd mlx-spark

PYTHONPATH=src python3 -m mlx_spark status
PYTHONPATH=src python3 -m mlx_spark doctor
python3 tools/validate_plan.py
```

To run the local CPU scaffold suite, create a new virtual environment with the opt-in bootstrap script, then run:

```bash
./scripts/bootstrap_dev.sh --allow-network
source .venv/bin/activate
bash scripts/check_local.sh
```

This suite does not validate CUDA, Qwen, model training, or release readiness.

## Principles

- **Independent runtime.** A released MLX-Spark wheel must not depend on an installed MLX, PyTorch, Transformers, vLLM, or similar library as its hidden tensor backend.
- **Evidence over claims.** `scaffold-tested`, `native-implemented`, `hardware-validated`, and `release-ready` are distinct states with distinct evidence.
- **Correctness before speed.** Each primitive needs explicit shape, dtype, layout, aliasing, stream, and differentiation contracts before optimization.
- **Single Spark first.** The first phase is one DGX Spark and one GB10. No NCCL, remote launchers, or distributed runtime are in scope yet.
- **Safe operations.** The project does not install drivers, alter the host system, silently download model weights, or claim benchmark results it has not measured.

## Roadmap

1. Establish audited source, build, and API-parity foundations.
2. Deliver the independent array runtime, execution model, transforms, and training primitives.
3. Validate the single-Spark CUDA runtime and the Qwen3.8-27B acceptance workload.
4. Ship an independently built wheel/SDK with reproducible release evidence.
5. Consider TP=2 only after the single-Spark release gate is satisfied.

The detailed engineering plan is in [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md), and the live dependency graph is [`planning/tasks.json`](planning/tasks.json). Most working engineering documentation is currently in Russian.

## Contributing

This repository is at a pre-alpha foundation stage. Documentation fixes, reproducible bug reports, tests, and narrowly scoped implementation proposals are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`AGENTS.md`](AGENTS.md), and the relevant task card before opening a pull request.

## Project status and license

MLX-Spark is a working project name and is not affiliated with or endorsed by Apple, NVIDIA, or Qwen. Model weights and proprietary NVIDIA binaries are not distributed here.

The project’s original code is licensed under [Apache License 2.0](LICENSE). Third-party material retains its own license and notice requirements; see [`LICENSE-DECISION.md`](LICENSE-DECISION.md) and [`NOTICE.md`](NOTICE.md).

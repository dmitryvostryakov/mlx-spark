# FND-02 partial handoff

- Task / role / reviewer: FND-02 / Sol / Luna.
- Base / implementation: `c29d9d918dc473bca9b5cf055880e950e064a2f5` / `624eb88bc5c31a628cbc15180db21ec5b6dbd3da`.
- Scope: read-only inventory of selected DGX2 only; no second node, scan, stress, install, system change, or TP2.
- Modified implementation paths: `src/mlx_spark/runtime/doctor.py`, `tests/test_doctor.py`.
- Interface: `inventory(workdir=".")` emits anonymized schema-version 2 JSON and says hardware validation not performed.
- Commands: targeted doctor tests and full local checks exit 0; owner-provided `ssh dgx2` and stdin doctor exit 0.
- Read-only inventory observed: Linux aarch64, DGX Spark, one GB10/sm_121, driver, memory, disk, compiler and CMake.
- Explicit unknowns: CUDA toolkit because `nvcc` is unavailable on PATH; cuDNN not found by standard probes.
- Proposed safe budgets: 80 GiB memory cap plus 32 GiB reserve; 256 GiB project disk cap plus 256 GiB free floor;
  96 GiB build-cache sub-cap; four build jobs; no weights authorization.
- Two review passes requested safety fixes; final implementation re-review approved
  `624eb88bc5c31a628cbc15180db21ec5b6dbd3da`. Hardware acceptance remains not ready.
- Hardware facts and budget arithmetic were accepted; evidence-fidelity remediation was independently re-reviewed
  and approved for state `7b0c1421b33c8606db77f68a2aa035c298260539` with no findings.
- Exact next action: integrate FND-02 done state, then claim FND-03 without widening to CUDA workload or TP2.
- Integration readiness: yes for FND-02 read-only inventory and foundation budgets only.
- Final evidence hashes: `evidence/runs/fnd-02/FINAL.sha256`.

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" != "--run-on-selected-spark" ]]; then
  printf 'Opt-in build and small GPU reference test on this host only. No SSH/network/system changes.\n'
  exit 2
fi
command -v nvcc >/dev/null || { echo 'nvcc missing; report, do not change the driver'; exit 2; }
cmake --preset spark-cuda-candidate
cmake --build --preset spark-cuda-candidate --parallel 2
./build/spark-cuda-candidate/spark_device_probe
# Direct invocation preserves exit 77 as NOT PASSED. Do not turn a skip into success.
./build/spark-cuda-candidate/test_gdn_cuda

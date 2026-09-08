#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
mlx_spark_python="${MLX_SPARK_PYTHON:-python3}"
if ! "$mlx_spark_python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  printf 'MLX-Spark local checks require Python 3.11+; set MLX_SPARK_PYTHON to a supported interpreter.\n' >&2
  exit 2
fi
"$mlx_spark_python" tools/validate_plan.py
"$mlx_spark_python" -m pytest -q tests
cmake --preset host-debug
cmake --build --preset host-debug --parallel 2
ctest --preset host-debug
"$mlx_spark_python" -m mlx_spark status
printf '\nLocal scaffold checks only. No MLX native, CUDA, Qwen or GPU-training gate has passed.\n'

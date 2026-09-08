#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" != "--allow-network" ]]; then
  printf 'Creates a NEW .venv and installs dev dependencies. Rerun with --allow-network after reading AGENTS.md.\n'
  exit 2
fi
if [[ -e .venv ]]; then
  printf '.venv already exists; refusing to alter it. Activate/review it manually.\n' >&2
  exit 2
fi
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,reference]'
printf 'Activate with: source .venv/bin/activate\n'

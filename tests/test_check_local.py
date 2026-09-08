import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_check_local_rejects_unsupported_python():
    environment = os.environ.copy()
    environment["MLX_SPARK_PYTHON"] = "false"
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/check_local.sh")],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "require Python 3.11+" in result.stderr

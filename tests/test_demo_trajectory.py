from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "demo_trajectory.py"


def test_demo_runs_without_trajectory_state(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(
        "SYNTHETIC DEMO — not measured user beta; does not affect gates or routing.\n"
    )
    assert "beta [synthetic-demo / bundled-v1]: 0.250 [0.142, 0.402]" in result.stdout
    assert "from 10/40 rejections" in result.stdout
    assert not (tmp_path / ".harness").exists()

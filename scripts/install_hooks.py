"""Point this checkout's Git at the tracked hooks in `.githooks/`.

    python scripts/install_hooks.py

Does not touch other repositories. Reversal: `git config --unset core.hooksPath`
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".githooks"


def main() -> int:
    if not (HOOKS / "pre-commit").is_file() or not (HOOKS / "pre-push").is_file():
        print("install_hooks: .githooks/pre-commit or pre-push is missing", file=sys.stderr)
        return 1
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=ROOT,
        check=True,
        encoding="utf-8",
        errors="replace",
    )
    print("core.hooksPath=.githooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

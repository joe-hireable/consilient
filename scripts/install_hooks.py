"""Point this checkout's Git at the tracked hooks in `.githooks/`.

    python scripts/install_hooks.py

Does not touch other repositories. Reversal: `git config --unset core.hooksPath`
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    Path(".githooks/pre-commit"),
    Path(".githooks/pre-push"),
    Path(".githooks/post-commit"),
    Path("scripts/memory_refresh.py"),
)


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        detail = ", ".join(path.as_posix() for path in missing)
        print(f"install_hooks: required file missing: {detail}", file=sys.stderr)
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

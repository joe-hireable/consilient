"""Harvest Consilient usage into a private local corpus. Not a consil subcommand."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.harvest import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

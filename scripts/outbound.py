"""Send email or SMS as a Consilient artefact. Not a consil subcommand."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient_connectors.outbound import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

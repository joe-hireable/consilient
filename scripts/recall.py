"""Print a bounded verbatim recall pack from the trajectory log.

Every dispatched harness receives the same projection — keyword + recency over JSONL,
no condensation (EXP-45).

    python scripts/recall.py --log .harness/log --query dispatch --limit-chars 8000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.recall import pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="recall.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log",
        default=os.environ.get("CONSILIENT_LOG", ".harness/log"),
        help="trajectory directory (default $CONSILIENT_LOG, else .harness/log)",
    )
    parser.add_argument(
        "--query",
        default="",
        help="keyword tokens to match (always-include dispatch and verdict events too)",
    )
    parser.add_argument(
        "--limit-chars",
        type=int,
        default=8000,
        help="character budget for the pack (default 8000)",
    )
    parser.add_argument(
        "--continuation",
        default=None,
        help="continuation cursor from a prior recall receipt",
    )
    args = parser.parse_args(argv)
    print(
        pack(
            Path(args.log),
            query=args.query,
            limit_chars=args.limit_chars,
            continuation_cursor=args.continuation,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

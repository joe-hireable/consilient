"""Record native work-item events in the authoritative trajectory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.work_items import (  # noqa: E402
    DEFAULT_ACTOR,
    comment,
    complete_item,
    open_item,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--log", default=".harness/log", help="trajectory directory")
    common.add_argument("--actor", default=DEFAULT_ACTOR, help="event actor")
    common.add_argument("--ticket", required=True, help="work-item identifier")

    opened = commands.add_parser("open", parents=[common])
    opened.add_argument("--accountable", required=True, help="one accountable actor")
    opened.add_argument("text", nargs="?", help="work-item summary")

    commented = commands.add_parser("comment", parents=[common])
    commented.add_argument("--evidence-class", required=True)
    commented.add_argument("text", help="comment text")

    commands.add_parser("complete", parents=[common])
    args = parser.parse_args(argv)
    log = Path(args.log)

    if args.operation == "open":
        event = open_item(
            log,
            ticket=args.ticket,
            accountable=args.accountable,
            actor=args.actor,
            text=args.text,
        )
    elif args.operation == "comment":
        event = comment(
            log,
            ticket=args.ticket,
            evidence_class=args.evidence_class,
            actor=args.actor,
            text=args.text,
        )
    else:
        event = complete_item(log, ticket=args.ticket, actor=args.actor)

    path = log / f"{event['ts'][:10]}.jsonl"
    print(f"{event['event']} {args.ticket} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

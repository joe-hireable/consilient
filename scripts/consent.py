"""Record and inspect purpose-specific consent in the local trajectory."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.events import (  # noqa: E402
    CONSENT_GRANTED,
    CONSENT_KINDS,
    CONSENT_PURPOSES,
    CONSENT_WITHDRAWN,
    SCHEMA_VERSION,
    append,
    read_all,
)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def record(
    log: Path,
    kind: str,
    purpose: str,
    principal: str,
    via: str,
    *,
    retention_days: int | None = None,
    use_ref: str | None = None,
) -> Path:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data: dict[str, Any] = {
        "purpose": purpose,
        "principal": principal,
        "via": via,
    }
    if kind == CONSENT_GRANTED:
        data["retention_days"] = retention_days
        if purpose == "commercial-training":
            data["per_use"] = True
            data["use_ref"] = use_ref
    path = log / f"{ts[:10]}.jsonl"
    append(
        path,
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": kind,
            "actor": principal,
            "data": data,
        },
    )
    return path


def render(log: Path) -> tuple[str, int]:
    recorded, rejected = read_all(log)
    latest = {}
    for event in recorded:
        purpose = event.data.get("purpose")
        if event.kind in CONSENT_KINDS and purpose in CONSENT_PURPOSES:
            latest[purpose] = event

    lines: list[str] = []
    for purpose in sorted(CONSENT_PURPOSES):
        lines.append(f"[{purpose}]")
        event = latest.get(purpose)
        if event is None:
            lines.append("status: never-asked")
        elif event.kind == CONSENT_WITHDRAWN:
            lines.append("status: withdrawn")
        else:
            retention_days = event.data["retention_days"]
            granted_at = datetime.fromisoformat(event.raw["ts"])
            expires_at = granted_at + timedelta(days=retention_days)
            lines.append(
                f"status: granted-until {expires_at.isoformat(timespec='seconds')}"
            )
            if purpose == "commercial-training":
                lines.append(f"use-ref: {event.data['use_ref']}")
        lines.append("")
    return "\n".join(lines).rstrip(), len(rejected)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)

    grant = commands.add_parser("grant")
    grant.add_argument("--purpose", required=True, choices=sorted(CONSENT_PURPOSES))
    grant.add_argument("--retention-days", required=True, type=positive_int)
    grant.add_argument("--principal", required=True)
    grant.add_argument("--via", required=True, choices=("cli",))
    grant.add_argument("--use-ref")

    withdraw = commands.add_parser("withdraw")
    withdraw.add_argument("--purpose", required=True, choices=sorted(CONSENT_PURPOSES))
    withdraw.add_argument("--principal", required=True)
    withdraw.add_argument("--via", required=True, choices=("cli",))

    show = commands.add_parser("show")
    for command in (grant, withdraw, show):
        command.add_argument(
            "--log",
            default=os.environ.get("CONSILIENT_LOG", ".harness/log"),
            help="trajectory directory (default $CONSILIENT_LOG, else .harness/log)",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log = Path(args.log)

    if args.operation == "show":
        output, rejected = render(log)
        print(output)
        if rejected:
            print(
                f"warning: {rejected} rejected trajectory line(s); statuses use valid "
                "events only",
                file=sys.stderr,
            )
        return 0

    if args.operation == "grant":
        use_ref = args.use_ref
        if args.purpose == "commercial-training":
            if not isinstance(use_ref, str) or not use_ref.strip():
                parser.error(
                    "commercial-training requires --use-ref naming the single "
                    "authorised use; commercial gain requires per-use re-consent"
                )
            use_ref = use_ref.strip()
        elif use_ref is not None:
            parser.error("--use-ref is only valid for commercial-training")

        prompt = (
            f"Grant {args.purpose} consent for {args.retention_days} days"
            + (f" for the single use {use_ref!r}" if use_ref else "")
            + "? [y/N] "
        )
        try:
            answer = input(prompt)
        except EOFError:
            answer = ""
        if answer.strip().casefold() not in {"y", "yes"}:
            print("No consent recorded.")
            return 1
        kind = CONSENT_GRANTED
        retention_days = args.retention_days
    else:
        kind = CONSENT_WITHDRAWN
        retention_days = None
        use_ref = None

    path = record(
        log,
        kind,
        args.purpose,
        args.principal,
        args.via,
        retention_days=retention_days,
        use_ref=use_ref,
    )
    print(f"{kind} {args.purpose} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

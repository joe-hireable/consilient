"""Admit an inbound transport payload into the trajectory. Not a consil subcommand.

    python scripts/ingest_transport.py --log .harness/log < payload.json
    python scripts/ingest_transport.py --log .harness/log --file payload.json

A Slack (or ClickUp, email, Twilio) message becomes `transport.proposal` or is
refused. It cannot become a human verdict. Duplicates are ignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.events import EventError, append  # noqa: E402
from consilient.transport import (  # noqa: E402
    TransportAdmitError,
    admit,
)


def _read_payload(path: str | None) -> object:
    if path:
        text = Path(path).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    if not text.strip():
        raise TransportAdmitError("payload is empty")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise TransportAdmitError(f"payload is not JSON: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default=".harness/log", help="trajectory directory")
    parser.add_argument("--file", help="JSON payload file; stdin if omitted")
    args = parser.parse_args(argv)
    log = Path(args.log)
    try:
        raw = _read_payload(args.file)
        if not isinstance(raw, dict):
            raise TransportAdmitError("payload must be a JSON object")
        event = admit(raw, log_dir=log)
    except TransportAdmitError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if event is None:
        print("ignored: duplicate")
        return 0
    log.mkdir(parents=True, exist_ok=True)
    day = event["ts"][:10]
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        day = datetime.now(timezone.utc).date().isoformat()
    try:
        recorded = append(log / f"{day}.jsonl", event)
    except EventError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"{recorded['event']} {recorded['data'].get('message_id')} -> {log / f'{day}.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify the trajectory is intact and record that it was verified. Gate A condition 3.

A3 asks for seven consecutive days of trajectory capture with no data loss. Until now nothing
produced that evidence: the log had a file for 19 and 20 August because work happened on those
days, and the EXP-27 collector — the only scheduled task on this machine — writes its own log
under `experiments/exp27/`, not the trajectory. **A quiet day would have broken the consecutive
run and reset A3 to one**, silently, with the gate looking like it was progressing.

This is deliberately a *check* and not a heartbeat. A heartbeat asserts that a writer ran and
proves nothing about the record; this replays the log, recomputes the canonical digest, counts
what the validator refused and what bypassed `append()`, and records all of it. A day on which
no work happened legitimately has one event — this one, saying the recorder works and the record
is intact. A day on which the log has been corrupted or truncated records `healthy: false`, and
A3 fails on it.

    python scripts/capture_health.py            # check and record
    python scripts/capture_health.py --dry-run  # report without appending

Scheduled daily and locally. It needs no credential and reaches no network.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import events as events_mod  # noqa: E402
from consilient import projection  # noqa: E402
from consilient.events import append  # noqa: E402

LOG = ROOT / ".harness" / "log"
DB = ROOT / ".harness" / "state.db"
CHECK_KIND = "capture.checked"


def inspect() -> dict[str, object]:
    """Replay the log and report what is in it. Any failure to read is an unhealthy record."""
    try:
        events, rejected = events_mod.read_all(LOG)
    except Exception as exc:  # pragma: no cover - a log this broken has never occurred
        return {"healthy": False, "reason": f"the trajectory could not be read: {exc}"}

    try:
        connection = projection.build(LOG, DB)
        try:
            digest = projection.state_digest(connection)
        finally:
            connection.close()
    except (sqlite3.DatabaseError, OSError) as exc:
        return {
            "healthy": False,
            "reason": f"the projection could not be rebuilt: {exc}",
        }

    bypassed = len(events_mod.bypassed(LOG))
    days = sorted(path.stem for path in LOG.glob("*.jsonl"))
    return {
        "healthy": True,
        "reason": "the trajectory replays to an identical canonical state",
        "events": len(events),
        "refused": len(rejected),
        "bypassed": bypassed,
        "days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "state_digest": digest,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Check and record trajectory capture health."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report the finding without appending it to the trajectory",
    )
    args = parser.parse_args()

    finding = inspect()
    now = datetime.now(timezone.utc)
    summary = ", ".join(
        f"{key}={value}" for key, value in finding.items() if key != "reason"
    )
    print(f"{'healthy' if finding['healthy'] else 'UNHEALTHY'}: {finding['reason']}")
    print(f"  {summary}")

    if args.dry_run:
        return 0

    append(
        LOG / f"{now.date().isoformat()}.jsonl",
        {
            "v": 1,
            "ts": now.isoformat(),
            "event": CHECK_KIND,
            "actor": "consilient.capture-health",
            "data": {**finding, "checked_by": "scripts/capture_health.py"},
        },
    )
    print(f"  recorded to {LOG.name}/{now.date().isoformat()}.jsonl")
    # Exit 0 on an unhealthy record too: the finding IS the output, and a non-zero exit would
    # make the scheduler treat evidence as a broken script. A3 is what reports it.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

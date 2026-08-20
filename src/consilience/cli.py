"""`consil` — the observe-only increment.

It records, projects and reports. It never routes, never blocks and never accepts an
artefact. Routing and blocking are Stage 3 and need Gate B (ADR-0015); nothing here can be
made to do them by a flag.

V0-14: every command has one JSON contract, and human output is a rendering of the same
result rather than a second semantics.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import beta as beta_mod
from . import projection
from .events import EventError, append, read_all

DEFAULT_LOG = Path(".harness/log")
DEFAULT_DB = Path(".harness/state.db")


def cmd_record(args) -> dict:
    try:
        event = json.loads(args.event)
    except json.JSONDecodeError as exc:
        raise EventError(f"--event is not valid JSON: {exc}") from exc
    path = Path(args.log) / f"{event.get('ts', '')[:10]}.jsonl"
    append(path, event)
    return {"recorded": True, "file": str(path), "event": event["event"]}


def cmd_replay(args) -> dict:
    """Compare the state on disk against a rebuild from the log. Gate A condition 2.

    Until 20 Aug 2026 this built the projection from the log twice and compared the two
    rebuilds. Two rebuilds from the same log are identical by construction, so the check
    could not fail, and `projection.build` unlinks the database first — so any drift it
    was meant to detect was destroyed before the comparison it was meant to feed. The gate
    was recorded as satisfied on a check that proved nothing. Found by Cursor auditing
    code Claude wrote.

    The comparison now has a subject: whatever state was already on disk. Where there is
    none, `compared` is False and `identical` is None, because a check that did not run
    must not report a pass.
    """
    log, db = Path(args.log), Path(args.db)

    prior: str | None = None
    if db.exists():
        existing = sqlite3.connect(db)
        try:
            prior = projection.state_digest(existing)
        except sqlite3.DatabaseError as exc:
            raise EventError(
                f"state at {db} is not a readable database: {exc}"
            ) from exc
        finally:
            existing.close()

    rebuilt = projection.build(log, db)
    digest = projection.state_digest(rebuilt)
    rebuilt.close()
    events = len(read_all(log))

    return {
        "events": events,
        "digest": digest,
        "prior_digest": prior,
        "compared": prior is not None,
        "identical": None if prior is None else prior == digest,
    }


def cmd_beta(args) -> dict:
    conn = projection.build(Path(args.log), Path(args.db))
    result = beta_mod.from_connection(conn, args.task_family, args.verifier_version)
    conn.close()
    return result.as_dict()


def render(command: str, result: dict) -> str:
    if command == "record":
        return f"recorded {result['event']} -> {result['file']}"
    if command == "replay":
        if not result["compared"]:
            mark = "NOT COMPARED — no prior state on disk"
        else:
            mark = "identical" if result["identical"] else "DIVERGED"
        return f"replayed {result['events']} events; state {mark} ({result['digest'][:12]})"
    if command == "beta":
        return beta_mod.Beta(
            verdict=result["verdict"],
            task_family=result["task_family"],
            verifier_version=result["verifier_version"],
            n_rejected=result["n_rejected"],
            n_false_accept=result["n_false_accept"],
            point=result["point"],
            interval=tuple(result["interval"]) if result["interval"] else None,
            window=tuple(result["window"]) if result["window"] else None,
        ).render()
    raise ValueError(command)


def build_parser() -> argparse.ArgumentParser:
    # Shared options are attached to the root and to every subcommand, so `--json` works
    # on either side of the command name. `consil beta --json` is the form people type.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="machine-readable output",
    )
    common.add_argument("--log", default=argparse.SUPPRESS)
    common.add_argument("--db", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(
        prog="consil",
        parents=[common],
        description="Observe-only. Records trajectory events and computes beta.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser(
        "record", parents=[common], help="append one validated event"
    )
    record.add_argument("--event", required=True, help="the event, as JSON")
    record.set_defaults(handler=cmd_record)

    replay = sub.add_parser(
        "replay",
        parents=[common],
        help="rebuild the projection and check it is stable",
    )
    replay.set_defaults(handler=cmd_replay)

    b = sub.add_parser(
        "beta",
        parents=[common],
        help="report beta with its sample count and interval",
    )
    b.add_argument("--task-family")
    b.add_argument("--verifier-version")
    b.set_defaults(handler=cmd_beta)
    return parser


DEFAULTS = {"json": False, "log": str(DEFAULT_LOG), "db": str(DEFAULT_DB)}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for name, value in DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, value)
    try:
        result = args.handler(args)
    except (EventError, projection.ProjectionError) as exc:
        print(
            json.dumps({"error": str(exc)}) if args.json else f"error: {exc}",
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(result, ensure_ascii=False, sort_keys=True)
        if args.json
        else render(args.command, result)
    )
    return 0 if result.get("identical", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

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
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import beta as beta_mod
from . import events as events_mod
from . import projection
from .events import EventError, append, read_all

DEFAULT_LOG = Path(".harness/log")
DEFAULT_DB = Path(".harness/state.db")
EXPERIMENT_REGISTER = Path("docs/10-research/experiment-register.md")
GATE_B2_ADR = Path(
    "docs/decisions/0037-replace-gate-b2-with-measured-critic-throughput-gain.md"
)
GATE_B_CIRCULARITY = Path(
    "docs/00-context/gate-b-cannot-be-passed-2026-08-20.md"
)
WORKFLOWS = Path(".github/workflows")
REQUIREMENTS = {
    "A1": "EXP-01 complete on two differently verified repositories with an interval",
    "A2": "Replay reproduces an identical canonical state digest",
    "A3": "Seven consecutive days of trajectory capture with no data loss",
    "B1": "EXP-05 complete and adapter two required no shared-interface redesign",
    "B2": "EXP-08 measured critic throughput gain is at least 20%",
    "B3": "A one-command bare-Claude-Code fallback is exercised weekly",
    "B4": "Twenty non-Consilience tickets complete without harness intervention",
}


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
    projected: int | None = None
    if db.exists():
        existing = sqlite3.connect(db)
        try:
            prior = projection.state_digest(existing)
            projected = existing.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        except sqlite3.DatabaseError as exc:
            raise EventError(
                f"state at {db} is not a readable database: {exc}"
            ) from exc
        finally:
            existing.close()

    read_events, rejected = read_all(log)
    events = len(read_events)

    # State that is behind AND independently drifted would otherwise be destroyed by the
    # rebuild before anything compared it, so the check that noticed the problem would also
    # remove the evidence. Copy it aside first. Found by an external audit of this repair.
    preserved: str | None = None
    if prior is not None and projected != events:
        keep = db.with_suffix(db.suffix + f".stale-{projected}-of-{events}")
        try:
            shutil.copy2(db, keep)
            preserved = str(keep)
        except OSError:
            preserved = None

    rebuilt = projection.build(log, db)
    digest = projection.state_digest(rebuilt)
    rebuilt.close()

    # Staleness is not drift, and conflating them makes the check cry wolf. Added hours after
    # the comparison itself was, because ordinary log growth reported DIVERGED on the real
    # trajectory. State built from fewer events than the log now holds is simply behind. The
    # defect V0-02 exists to catch is state that disagrees about events it already covers.
    stale = prior is not None and projected != events
    compared = prior is not None and not stale

    return {
        "events": events,
        "events_projected": projected,
        "digest": digest,
        "prior_digest": prior,
        "stale": stale,
        "preserved_stale_state": preserved,
        "compared": compared,
        "identical": (prior == digest) if compared else None,
        "quarantined": [
            {"path": r.path, "line": r.line, "reason": r.reason} for r in rejected
        ],
        "not_written_by_append": len(events_mod.bypassed(log)),
    }


def cmd_beta(args) -> dict:
    conn = projection.build(Path(args.log), Path(args.db))
    result = beta_mod.from_connection(conn, args.task_family, args.verifier_version)
    quarantined = projection.rejection_count(conn)
    conn.close()
    # β is a rate over a denominator, so anything the log refused has to be visible
    # wherever the rate is. A β computed over a quietly shortened log is exactly the false
    # confidence this project exists to measure.
    return {**result.as_dict(), "quarantined": quarantined}


def _condition(
    identifier: str, status: str, reason: str, *evidence: str
) -> dict:
    return {
        "id": identifier,
        "requirement": REQUIREMENTS[identifier],
        "status": status,
        "reason": reason,
        "evidence": list(evidence),
    }


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _experiment_entry(identifier: str) -> tuple[str | None, str]:
    text = _read_text(EXPERIMENT_REGISTER)
    match = re.search(
        rf"(?ms)^### {re.escape(identifier)}\b.*?(?=^### |\Z)", text or ""
    )
    if match is None:
        return None, ""
    entry = match.group()
    marker = re.search(
        r"`((?:DONE|IN PROGRESS|BLOCKED)[^`]*)`\s*$", entry.partition("\n")[0]
    )
    status = marker.group(1).partition(" see ")[0].rstrip(" -\N{EM DASH}") if marker else None
    return status, entry


def _experiment_conditions(beta: dict, log: Path) -> tuple[dict, dict, dict]:
    register = EXPERIMENT_REGISTER.as_posix()
    a1_status, _ = _experiment_entry("EXP-01")
    a1 = _condition(
        "A1",
        "unknown" if a1_status is None else "pass" if a1_status.startswith("DONE") else "fail",
        "No EXP-01 result is recorded."
        if a1_status is None
        else f"EXP-01 is recorded as {a1_status}.",
        *(() if a1_status is None else (register,)),
    )

    b1_status, b1_entry = _experiment_entry("EXP-05")
    b1_result = b1_entry.partition("**Result:**")[2].partition("\n\n")[0]
    no_redesign = (
        "Adapter #2 (Codex) did not force an interface redesign"
        in " ".join(b1_result.split())
    )
    if b1_status is None:
        b1 = _condition("B1", "unknown", "No EXP-05 result is recorded.")
    elif b1_status.startswith("DONE") and no_redesign:
        b1 = _condition("B1", "pass", "EXP-05 is DONE; adapter two forced no redesign.", register)
    elif b1_status.startswith("DONE"):
        b1 = _condition("B1", "unknown", "Adapter-two outcome is not recorded.", register)
    else:
        b1 = _condition("B1", "fail", f"EXP-05 is recorded as {b1_status}.", register)

    b2_status, _ = _experiment_entry("EXP-08")
    b2_evidence = (register, GATE_B2_ADR.as_posix(), f"{log.as_posix()}/*.jsonl")
    if b2_status is None:
        b2 = _condition("B2", "unknown", "No EXP-08 result is recorded.")
    elif not b2_status.startswith("DONE") or beta["verdict"] != "measured":
        b2 = _condition(
            "B2",
            "unknown",
            f"EXP-08 is {b2_status}; beta is {beta['verdict']} from "
            f"{beta['n_rejected']} human rejections, so the 0.6296 threshold cannot be evaluated.",
            *b2_evidence,
        )
    else:
        b2 = _condition(
            "B2",
            "unknown",
            "No machine-readable EXP-08 outcome exists; repository-wide beta is not "
            "critic-recall evidence for the 0.6296 threshold.",
            *b2_evidence,
        )
    return a1, b1, b2


def _replay_condition(replay: dict, log: Path, db: Path) -> dict:
    identical = replay["identical"]
    status = "pass" if identical is True else "fail" if identical is False else "unknown"
    if identical is None:
        reason = (
            f"State covers {replay['events_projected']} of {replay['events']} events; not compared."
            if replay["stale"]
            else "No prior projection existed; replay was not compared."
        )
    else:
        reason = f"Compared {replay['events']} events; canonical state " + (
            "is identical." if identical else "diverged."
        )
    return _condition("A2", status, reason, f"{log.as_posix()}/*.jsonl", db.as_posix())


def _capture_condition(log: Path) -> dict:
    days: list[date] = []
    issues: dict[date, int] = {}
    for path in log.glob("*.jsonl"):
        try:
            day = date.fromisoformat(path.stem)
            events, rejected = events_mod.read(path)
            matching = [event for event in events if event.raw["ts"][:10] == path.stem]
            if day <= datetime.now(timezone.utc).date() and matching:
                days.append(day)
                issues[day] = len(rejected) + len(events) - len(matching)
        except (OSError, ValueError):
            continue
    days = sorted(set(days))
    evidence = f"{log.as_posix()}/*.jsonl"
    if not days:
        return _condition(
            "A3",
            "fail",
            "No non-empty daily trajectory files; latest run is 0/7 days.",
            evidence,
        )

    run_start = days[-1]
    gap: date | None = None
    for earlier in reversed(days[:-1]):
        if earlier == run_start - timedelta(days=1):
            run_start = earlier
        else:
            gap = earlier + timedelta(days=1)
            break
    run = (days[-1] - run_start).days + 1
    issue_count = sum(count for day, count in issues.items() if day >= run_start)
    reason = (
        f"Latest capture run is {run}/7 days, {run_start.isoformat()} through "
        f"{days[-1].isoformat()}."
    )
    if gap is not None:
        reason += f" The preceding gap is {gap.isoformat()}."
    if issue_count:
        reason += f" The run has {issue_count} rejected or misdated line(s)."
    return _condition(
        "A3",
        "pass" if run >= 7 and issue_count == 0 else "fail",
        reason,
        evidence,
    )


def _fallback_condition() -> dict:
    if not WORKFLOWS.is_dir():
        return _condition("B3", "unknown", "No workflow evidence source exists.")
    files = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    texts = [_read_text(path) for path in files]
    if any(text is None for text in texts):
        status = "unknown"
        reason = "At least one workflow could not be read, so weekly fallback health is unknown."
    elif not any(re.search(r"(?m)^\s*schedule\s*:", text or "") for text in texts):
        status = "fail"
        reason = f"All {len(files)} workflows were checked; none has a schedule trigger."
    else:
        status = "unknown"
        reason = "A scheduled workflow exists, but no machine-readable fallback result exists."
    return _condition("B3", status, reason, WORKFLOWS.as_posix())


def _structural_condition() -> dict:
    text = _read_text(GATE_B_CIRCULARITY)
    if text is None:
        return _condition("B4", "unknown", "The structural analysis is unavailable.")
    established = (
        "Condition 4 can only be satisfied by doing the thing the gate forbids" in text
    )
    return _condition(
        "B4",
        "structurally_unsatisfiable" if established else "unknown",
        (
            "Gate B forbids the non-Consilience orchestration required to produce its "
            "own condition-four evidence."
            if established
            else "The structural analysis does not establish the recorded circularity."
        ),
        GATE_B_CIRCULARITY.as_posix(),
    )


def _gate(conditions: list[dict]) -> dict:
    statuses = {condition["status"] for condition in conditions}
    if "structurally_unsatisfiable" in statuses:
        status = "structurally_unsatisfiable"
    elif "fail" in statuses:
        status = "fail"
    elif "unknown" in statuses:
        status = "unknown"
    elif statuses == {"pass"}:
        status = "pass"
    else:
        status = "unknown"
    return {"status": status, "passed": status == "pass", "conditions": conditions}


def cmd_doctor(args) -> dict:
    log, db = Path(args.log), Path(args.db)
    # Replay must inspect prior state before beta reads the rebuilt projection. Rebuilding
    # first would recreate the tautological A2 check repaired on 20 August 2026.
    replay = cmd_replay(args)
    conn = sqlite3.connect(db)
    try:
        beta = beta_mod.from_connection(conn).as_dict()
    finally:
        conn.close()
    a1, b1, b2 = _experiment_conditions(beta, log)
    gates = {
        "A": _gate([a1, _replay_condition(replay, log, db), _capture_condition(log)]),
        "B": _gate([b1, b2, _fallback_condition(), _structural_condition()]),
    }
    expected = {"A": {"A1", "A2", "A3"}, "B": {"B1", "B2", "B3", "B4"}}
    enabled = all(
        {condition["id"] for condition in gates[name]["conditions"]} == identifiers
        and all(
            condition["status"] == "pass"
            for condition in gates[name]["conditions"]
        )
        for name, identifiers in expected.items()
    )
    return {"gates": gates, "routing_orchestration_enabled": enabled}


def render(command: str, result: dict) -> str:
    if command == "record":
        return f"recorded {result['event']} -> {result['file']}"
    if command == "replay":
        if result["stale"]:
            mark = (
                f"STALE — state covers {result['events_projected']} of {result['events']} "
                "events; rebuilt"
            )
        elif not result["compared"]:
            mark = "NOT COMPARED — no prior state on disk"
        else:
            mark = "identical" if result["identical"] else "DIVERGED"
        line = f"replayed {result['events']} events; state {mark} ({result['digest'][:12]})"
        if result["quarantined"]:
            line += (
                f"\n  QUARANTINED {len(result['quarantined'])} line(s) the log refuses:"
            )
            for r in result["quarantined"]:
                line += f"\n    {r['path']}:{r['line']}  {r['reason']}"
        if result["not_written_by_append"]:
            total = result["events"] + len(result["quarantined"])
            line += (
                f"\n  {result['not_written_by_append']} of {total} logged lines were not "
                "written by append(), so validate() never ran on them"
            )
        return line
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
    if command == "doctor":
        lines = []
        for name, gate in result["gates"].items():
            lines.append(f"Gate {name}: {gate['status'].replace('_', '-').upper()}")
            for condition in gate["conditions"]:
                mark = condition["status"].replace("_", "-").upper()
                lines.append(
                    f"  {condition['id']} {mark}: {condition['requirement']}"
                )
                lines.append(f"    {condition['reason']}")
                evidence = ", ".join(condition["evidence"]) or "none"
                lines.append(f"    evidence: {evidence}")
        enabled = "yes" if result["routing_orchestration_enabled"] else "no"
        lines.append(f"routing/orchestration enabled: {enabled}")
        return "\n".join(lines)
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

    doctor = sub.add_parser(
        "doctor",
        parents=[common],
        help="report measured Gate A and Gate B status",
    )
    doctor.set_defaults(handler=cmd_doctor)
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

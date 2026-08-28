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
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from . import beta as beta_mod
from . import dashboard as dashboard_mod
from . import events as events_mod
from . import budget
from . import projection
from . import usage as usage_mod
from .events import EventError, append, read_all
from .events import jittered_sleep as _jittered_sleep

# Each CLI command has a different nested JSON result shape. Any is confined to this
# rendering boundary, where the command selects the corresponding schema before access.
CommandResult = dict[str, Any]

DEFAULT_LOG = Path(".harness/log")
DEFAULT_DB = Path(".harness/state.db")
DEFAULT_DASHBOARD = Path(".harness/dashboard.html")
TrajectoryState = Literal["missing", "empty", "present"]
READ_TRAJECTORY_COMMANDS = frozenset({"replay", "beta", "doctor", "dashboard"})
EXPERIMENT_REGISTER = Path("docs/10-research/experiment-register.md")
# Every default above is relative to the working directory; the code that reads them comes
# from wherever the interpreter found `consilient`. Those are two independent inputs, and
# nothing compared them. Measured 21 August 2026: one interpreter-global editable install
# pointed at a different worktree, so `consil doctor` run inside this one reported its Gate
# A1 as PASS and exited 0 while the code actually standing in this tree reported FAIL and
# exited 1 -- same directory, same log, the other tree's answers. Two agents were misled by
# it in one night. The interpreter chooses which `consilient` to import before any line of
# this module runs, so nothing here can make the wrong tree impossible. `_foreign_tree`
# makes it loud, and doctor's provenance lines make it visible when it cannot be refused.
_PACKAGE = Path(__file__).resolve().parent
CODE_TREE = _PACKAGE.parents[1] if _PACKAGE.parent.name == "src" else _PACKAGE
GATE_B2_ADR = Path(
    "docs/decisions/0045-give-gate-b2-and-b3-success-criteria-they-never-had.md"
)
GATE_B_CIRCULARITY = Path("docs/00-context/gate-b-cannot-be-passed-2026-08-20.md")
# Refused lines already in the trajectory when ADR-0043 was accepted on 20 August 2026:
# three V0-18 violations appended between 09:41 and 09:56 that day, permanent because the
# log is append-only. ADR-0043 tolerates these exact three lines by their content digests.
# ADR-0105 proposes adding three torn invalid-JSON lines from 2026-08-22 (lines 27, 35, 45),
# after unit AB shipped torn-append refusal. THEY ARE NOT ADDED HERE, and the reason is the
# whole point of this constant.
#
# ADR-0105 accepted 26 August 2026: `decision.gate_amendment` recorded in
# `.harness/log/2026-08-26.jsonl`, actor and principal "joe-brown", authority "Set it back
# to accepted." The three digests below the 20 August set are real -- verified 24 August
# 2026 against `.harness/log/2026-08-22.jsonl`, where they hash lines 27, 35 and 45 exactly,
# and those lines are genuinely torn. What could not be corroborated until 26 August was the
# AUTHORISATION: an earlier version of ADR-0105 claimed "Accepted by Joe Brown, 24 August
# 2026, in the orchestration chat" with no matching trajectory event, and that claim was
# withdrawn. `test_the_capture_refusal_baseline_may_only_fall` still forbids this number
# rising WITHOUT a principal event backing it -- it now permits <= 6, not <= 3, because one
# exists.
HISTORICAL_REFUSAL_DIGESTS: frozenset[str] = frozenset(
    {
        "0fb234324063389745b5e79be163b8b6e3988a955d2a2fbd19f4036e225a7b90",
        "6921e71b2c687dd2f1f816410d20f53e106db1126bbf39fceeec02e33204f260",
        "65df9c30eeaf7095072eaada45ce276cbaca877b9540c48c519bcfdc729eb300",
        "305cfe4853e3d9576fd186f86cac2f3900805c44a75a41b0642a27e1da5741d3",
        "3769e62caa9131bb916fef24b40d46d70b49e19ee59a0686aa106b66eed15387",
        "6511adf8d1b5ef4aea3f542d610d261572c6a103d630775ce785ab2395a187ec",
    }
)
CAPTURE_REFUSAL_BASELINE = len(HISTORICAL_REFUSAL_DIGESTS)
FALLBACK_RESULT = Path(".harness/fallback-result.json")
# Two cycles of a weekly schedule (ADR-0045). One missed run is tolerated, two are not.
FALLBACK_MAX_AGE_DAYS = 14
EXPECTED_FALLBACK_COMMAND = (
    "claude -p Read src/consilient/beta.py and reply with the exact name of the "
    "function that computes the Wilson score interval. Reply with the name alone and "
    "nothing else."
)
FALLBACK_RUNNER_IDENTITY = "scripts/run_fallback.py"
GATE_B4_ADR = Path(
    "docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md"
)
# ADR-0015 Gate B condition 4, unchanged in number by ADR-0039 — only in meaning.
B4_TICKETS_REQUIRED = 20
THIS_REPOSITORIES: frozenset[str] = frozenset(
    {
        "consilient",
        "consilience",
        "joe-hireable/consilient",
        "joe-hireable/consilience",
        "consilient-work",
        "consilience-work",
    }
)
THIS_REPOSITORY = "consilient"
# The machine-readable beta measurement in EXP-01's register entry required for Gate A1.
EXP01_BETA = re.compile(
    r"(?:beta-measured|exp-01-beta-measured):\s*([0-9.]+)\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]"
)
# The machine-readable critic measurement ADR-0045 requires in EXP-08's register entry.
CRITIC_BETA = re.compile(
    r"critic-beta-measured:\s*([0-9.]+)\s*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]"
)


def trajectory_state(log: Path) -> TrajectoryState:
    """Distinguish a missing log directory from one that exists but holds no events."""
    resolved = log.resolve()
    if resolved.exists() and not resolved.is_dir():
        return "missing"
    if not resolved.is_dir():
        return "missing"
    if any(resolved.glob("*.jsonl")):
        events, rejected = read_all(resolved)
        if events or rejected:
            return "present"
        return "empty"
    return "empty"


def _trajectory_refusal(log: Path) -> str:
    """Human-readable refusal when the default log path points at nothing."""
    resolved = log.resolve()
    if resolved.exists() and not resolved.is_dir():
        return (
            f"trajectory not configured — {resolved} exists but is not a directory; "
            "pass --log with a trajectory directory"
        )
    return (
        f"trajectory not configured — no directory at {resolved}; nothing has been "
        "recorded here. Run from a Consilient checkout or pass --log with an existing "
        "trajectory directory"
    )


def require_trajectory(log: Path) -> Literal["empty", "present"]:
    """Refuse when the log directory is absent. Upward search was rejected: it would let a
    command silently read a parent checkout's trajectory while the user believes they are
    elsewhere — the wrong-worktree hazard this project was already bitten by. Explicit
    --log and the provenance block on `doctor` are the supported ways to see which path
    answered.
    """
    state = trajectory_state(log)
    if state == "missing":
        raise EventError(_trajectory_refusal(log))
    return state


def _command_needs_trajectory(args: argparse.Namespace) -> bool:
    if args.command in READ_TRAJECTORY_COMMANDS:
        return True
    if args.command == "usage" and not args.fake and not args.record:
        return True
    return False


def _trajectory_line(result: CommandResult) -> str:
    traj = result.get("trajectory_source")
    if not isinstance(traj, dict):
        return ""
    path = str(traj.get("path", ""))
    state = traj.get("state")
    if state == "empty":
        return f"trajectory: {path} (empty — zero events recorded here, not a missing directory)"
    if state == "present":
        return f"trajectory: {path}"
    return f"trajectory: {path}" if path else ""


REQUIREMENTS = {
    "A1": "EXP-01 complete on two differently verified repositories with an interval",
    "A2": "Replay reproduces an identical canonical state digest",
    "A3": "Seven consecutive days of trajectory capture with no data loss",
    "B1": "EXP-05 complete and adapter two required no shared-interface redesign",
    "B2": "The critic tier's own beta is measured, with an interval",
    "B3": "A one-command bare-Claude-Code fallback is exercised weekly",
    "B4": "Twenty non-Consilient tickets complete without harness intervention",
}


def cmd_record(args: argparse.Namespace) -> CommandResult:
    try:
        event = json.loads(args.event)
    except json.JSONDecodeError as exc:
        raise EventError(f"--event is not valid JSON: {exc}") from exc
    path = Path(args.log) / f"{event.get('ts', '')[:10]}.jsonl"
    append(path, event)
    return {"recorded": True, "file": str(path), "event": event["event"]}


def cmd_usage(args: argparse.Namespace) -> CommandResult:
    """Every configured provider's usage, limits and spend in one place.

    Read-only by default. `--record` puts the snapshot in the trajectory through
    `append()`, which is opt-in because a dashboard polling this command must not write a
    line every time somebody looks at it.
    """
    sources = usage_mod.Sources(payloads=Path(args.payloads), log=Path(args.log))
    snapshot = usage_mod.fake_snapshot() if args.fake else usage_mod.snapshot(sources)
    limits = usage_mod.load_limits(Path(args.limits))
    if isinstance(limits, budget.BudgetRefusal):
        snapshot["ceilings"] = {
            "configured": False,
            "refusal": limits.reason,
            "limits": [],
        }
    else:
        snapshot["ceilings"] = {
            "configured": True,
            "refusal": None,
            "limits": [
                {
                    "period": ceiling.period,
                    "amount": str(ceiling.amount),
                    "currency": ceiling.currency,
                }
                for ceiling in limits
            ],
        }
    snapshot["recorded"] = (
        usage_mod.record(Path(args.log), snapshot)
        if args.record and not args.fake
        else 0
    )
    return snapshot


def _projection_workspace(log: Path) -> Path | None:
    """The workspace `projection.build` infers from a live `.harness/log` directory."""
    if log.name == "log" and log.parent.name == ".harness":
        return log.parent.parent
    return None


def _copy_event_prefix(
    src: Path, dest: Path, count: int, rejection_count: int = 0
) -> None:
    """Copy the log prefix that produced `count` events and `rejection_count` refusals.

    Later lines are outside the high-water mark. Copying original file text, rather than
    re-serializing accepted events, keeps rejected lines in the prefix so the digest
    covers the same quarantine the projection had.

    Pin on the persisted (event_count, rejection_count) pair, not accepted-event count
    alone. MEASURED 26 August 2026: cutting at file_events[-1].line when remaining==0
    dropped a trailing refusal that was already inside the projection, so doctor
    reported divergence on a quiet log. The same accepted-event cut pulled a post-mark
    refusal into the prefix whenever later accepted events existed beyond it. Walk
    classified lines until both counts are met; anything after that is outside the
    comparison.
    """
    dest.mkdir(parents=True, exist_ok=True)
    remaining_events = count
    remaining_rejections = rejection_count
    for path in sorted(src.glob("*.jsonl")):
        if not path.is_file():
            continue
        if remaining_events <= 0 and remaining_rejections <= 0:
            break
        file_events, file_rejected = events_mod.read(path)
        items: list[tuple[int, int, int]] = []
        missing_line = False
        for event in file_events:
            if event.line is None:
                missing_line = True
                break
            items.append((event.line, 1, 0))
        if not missing_line:
            for rejection in file_rejected:
                items.append((rejection.line, 0, 1))
            items.sort()
        if missing_line or not items:
            shutil.copy2(path, dest / path.name)
            remaining_events -= len(file_events)
            remaining_rejections -= len(file_rejected)
            continue
        last_included = 0
        for line, events_delta, rejections_delta in items:
            if remaining_events <= 0 and remaining_rejections <= 0:
                break
            remaining_events -= events_delta
            remaining_rejections -= rejections_delta
            last_included = line
        if remaining_events > 0 or remaining_rejections > 0:
            shutil.copy2(path, dest / path.name)
            continue
        file_text = path.read_text(encoding="utf-8")
        lines = file_text.splitlines(keepends=True)
        (dest / path.name).write_text(
            "".join(lines[:last_included]), encoding="utf-8"
        )
        break


def _digest_of_pinned_prefix(
    log: Path,
    count: int,
    workspace: Path | None,
    scratch: Path,
    *,
    rejection_count: int = 0,
) -> str:
    """Rebuild a throwaway projection of the pinned prefix and digest it."""
    if scratch.exists():
        shutil.rmtree(scratch)
    try:
        prefix_log = scratch / "log"
        prefix_db = scratch / "state.db"
        _copy_event_prefix(log, prefix_log, count, rejection_count)
        conn = projection.build(prefix_log, prefix_db, workspace=workspace)
        try:
            return projection.state_digest(conn)
        finally:
            conn.close()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

def cmd_replay(args: argparse.Namespace) -> CommandResult:
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

    Gate A2 decides against a pinned prefix: the projection's own (event_count,
    rejection_count) is the high-water mark, and only that prefix is replayed for
    identity. Events and refusals appended after the mark are not evidence of
    divergence. The `replay` command still reports `stale` when the live log is
    longer, so a behind projection remains visible.
    """
    log, db = Path(args.log), Path(args.db)

    prior: str | None = None
    projected: int | None = None
    projected_rejections = 0
    prior_version: int | None = None
    if db.exists():
        existing = sqlite3.connect(db)
        try:
            prior = projection.state_digest(existing)
            projected = int(
                existing.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            )
            projected_rejections = projection.rejection_count(existing)
            prior_version = projection.projection_version(existing)
        except sqlite3.DatabaseError as exc:
            raise EventError(
                f"state at {db} is not a readable database: {exc}"
            ) from exc
        finally:
            existing.close()

    version_changed = (
        prior is not None and prior_version != projection.PROJECTION_VERSION
    )

    prefix_identical: bool | None = None
    if version_changed:
        prefix_identical = None
    elif prior is not None and projected is not None:
        if projected == 0:
            prefix_identical = True
        else:
            scratch = db.parent / (db.stem + "-a2-prefix")
            prefix_digest = _digest_of_pinned_prefix(
                log,
                projected,
                _projection_workspace(log),
                scratch,
                rejection_count=projected_rejections,
            )
            prefix_identical = prefix_digest == prior

    read_events, rejected = read_all(log)
    events = len(read_events)

    # Copy the on-disk state aside only when it disagrees about events it already
    # covers. A one-event lag is not drift; copying on every lag filled the disk
    # at 11 MB/hour. The prefix digest is the comparison that can tell them apart
    # before rebuild replaces the file.
    preserved: str | None = None
    if (
        prior is not None
        and projected is not None
        and projected != events
        and not version_changed
    ):
        prefix = projection.prefix_digest(
            read_events[:projected], rejected, db.parent, log_dir=log
        )
        if prefix != prior:
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
    compared = prior is not None and not stale and not version_changed

    return {
        "events": events,
        "events_projected": projected,
        "digest": digest,
        "prior_digest": prior,
        "stale": stale,
        "version_changed": version_changed,
        "prior_version": prior_version,
        "projection_version": projection.PROJECTION_VERSION,
        "preserved_stale_state": preserved,
        "compared": compared,
        "identical": (prior == digest) if compared else None,
        "prefix_events": projected,
        "prefix_identical": prefix_identical,
        "quarantined": [
            {"path": r.path, "line": r.line, "reason": r.reason} for r in rejected
        ],
        "not_written_by_append": len(events_mod.bypassed(log)),
    }


def cmd_beta(args: argparse.Namespace) -> CommandResult:
    conn = projection.build(Path(args.log), Path(args.db))
    try:
        result = beta_mod.from_connection(conn, args.task_family, args.verifier_version)
        parser_quarantined = projection.rejection_count(conn)
        rejection_reasons = projection.rejections(conn)
        relational = projection.relational_quarantines(conn)
        sampling = projection.sampling_unconditioned(conn)
    finally:
        conn.close()
    # β is a rate over a denominator, so anything the log refused has to be visible
    # wherever the rate is. A β computed over a quietly shortened log is exactly the false
    # confidence this project exists to measure. The count stays for callers that already
    # read it; the reasons are the thing that used to be pooled into that integer.
    return {
        **result.as_dict(),
        "quarantined": parser_quarantined,
        "rejection_reasons": rejection_reasons,
        "relational_quarantine_count": len(relational),
        "relational_quarantine": relational,
        "sampling_unconditioned": sampling,
    }


def _condition(
    identifier: str, status: str, reason: str, *evidence: str
) -> CommandResult:
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
    status = (
        marker.group(1).partition(" see ")[0].rstrip(" -\N{EM DASH}")
        if marker
        else None
    )
    return status, entry


def _experiment_conditions() -> tuple[CommandResult, CommandResult, CommandResult]:
    register = EXPERIMENT_REGISTER.as_posix()
    a1_status, a1_entry = _experiment_entry("EXP-01")
    a1_evidence = (register,)
    a1_measurement = EXP01_BETA.search(a1_entry)
    stopping_rule_fired = "stopping rule FIRED" in a1_entry or (
        a1_status is not None and "stopping rule FIRED" in a1_status
    )
    if a1_status is None:
        a1 = _condition("A1", "unknown", "No EXP-01 result is recorded.")
    elif not a1_status.startswith("DONE"):
        a1 = _condition(
            "A1",
            "fail",
            f"EXP-01 is recorded as {a1_status}; must be DONE with a usable beta interval.",
            *a1_evidence,
        )
    elif stopping_rule_fired:
        a1 = _condition(
            "A1",
            "fail",
            "EXP-01 stopping rule fired: history mining could not narrow the interval below "
            "\u00b10.05 and the method was retired without a usable beta measurement.",
            *a1_evidence,
        )
    elif a1_measurement is None:
        a1 = _condition(
            "A1",
            "fail",
            f"EXP-01 is {a1_status}; its entry records no `beta-measured: p [lo, hi]` "
            "measurement with interval half-width <= 0.05, which Gate A requires.",
            *a1_evidence,
        )
    else:
        point, low, high = (float(value) for value in a1_measurement.groups())
        half_width = (high - low) / 2
        if not (0 <= low <= point <= high <= 1):
            a1 = _condition(
                "A1",
                "fail",
                f"Recorded beta {point} lies outside its own interval [{low}, {high}].",
                *a1_evidence,
            )
        elif half_width > 0.05:
            a1 = _condition(
                "A1",
                "fail",
                f"Recorded beta interval [{low}, {high}] half-width {half_width:.4f} exceeds "
                "\u00b10.05 tolerance; does not decide the threshold.",
                *a1_evidence,
            )
        else:
            a1 = _condition(
                "A1",
                "pass",
                f"EXP-01 is DONE; beta is measured at {point} [{low}, {high}] with half-width "
                f"{half_width:.4f} <= 0.05.",
                *a1_evidence,
            )

    b1_status, b1_entry = _experiment_entry("EXP-05")
    b1_result = b1_entry.partition("**Result:**")[2].partition("\n\n")[0]
    no_redesign = "Adapter #2 (Codex) did not force an interface redesign" in " ".join(
        b1_result.split()
    )
    if b1_status is None:
        b1 = _condition("B1", "unknown", "No EXP-05 result is recorded.")
    elif b1_status.startswith("DONE") and no_redesign:
        b1 = _condition(
            "B1", "pass", "EXP-05 is DONE; adapter two forced no redesign.", register
        )
    elif b1_status.startswith("DONE"):
        b1 = _condition(
            "B1", "unknown", "Adapter-two outcome is not recorded.", register
        )
    else:
        b1 = _condition("B1", "fail", f"EXP-05 is recorded as {b1_status}.", register)

    b2_status, b2_entry = _experiment_entry("EXP-08")
    b2_evidence = (register, GATE_B2_ADR.as_posix())
    measurement = CRITIC_BETA.search(b2_entry)
    if b2_status is None:
        b2 = _condition("B2", "unknown", "No EXP-08 result is recorded.")
    elif not b2_status.startswith("DONE"):
        b2 = _condition(
            "B2",
            "fail",
            f"EXP-08 is {b2_status}; must be DONE and carry a `critic-beta-measured: p [lo, hi]` "
            "measurement (ADR-0045).",
            *b2_evidence,
        )
    elif measurement is None:
        b2 = _condition(
            "B2",
            "fail",
            f"EXP-08 is {b2_status}; its entry records no `critic-beta-measured: p [lo, hi]` "
            "measurement, which ADR-0045 requires.",
            *b2_evidence,
        )
    else:
        point, low, high = (float(value) for value in measurement.groups())
        b2 = _condition(
            "B2",
            "pass" if low <= point <= high else "fail",
            f"Critic beta is measured at {point} [{low}, {high}]."
            if low <= point <= high
            else f"Recorded critic beta {point} lies outside its own interval [{low}, {high}].",
            *b2_evidence,
        )
    return a1, b1, b2


def _replay_condition(replay: CommandResult, log: Path, db: Path) -> CommandResult:
    """Gate A condition 2, decided against the projection's own high-water mark.

    A1's repair gave `replay` a subject -- whatever state was already on disk -- instead of
    comparing two rebuilds. But every state on disk was itself written by a rebuild from the
    same log, so on an empty trajectory `identical: true` says only that nothing equals
    nothing. Measured 21 August 2026: two `consil doctor` runs in an empty directory, with
    no log and no configuration, reported A2 `pass` with the reason "Compared 0 events;
    canonical state is identical." A gate condition satisfied by an empty comparison is A1
    one invocation further out.

    An empty prefix is `unknown` -- the status for a check that did not run -- rather than
    `pass`. A genuine mismatch inside the prefix still fails. Events appended after the
    mark are outside the comparison: they are not evidence of divergence. Measured 24
    August 2026: with ~20 agents appending, doctor reported FAIL, then UNKNOWN, then PASS
    for one unchanged history, because it compared the persisted projection against a
    later live tail.
    """
    evidence = (f"{log.as_posix()}/*.jsonl", db.as_posix())
    prefix_events = replay["prefix_events"]
    prefix_identical = replay["prefix_identical"]
    # A projection-version bump is expected to change state_digest, so the prior digest
    # was written by a different projection than the one that rebuilt the pinned prefix.
    # There is nothing comparable, and reporting a rebuild as divergence would make the
    # gate cry wolf on every legitimate schema or handler change.
    if replay.get("version_changed"):
        reason = (
            f"Projection version {replay.get('prior_version')!r} rebuilt as "
            f"{replay.get('projection_version')!r}; not compared."
        )
        return _condition("A2", "unknown", reason, *evidence)
    if prefix_identical is None:
        return _condition(
            "A2",
            "unknown",
            "No prior projection existed; replay was not compared.",
            *evidence,
        )
    if prefix_events == 0:
        # An empty high-water mark is unknown either way, but a projection covering none
        # of a non-empty log is behind, not an empty trajectory. Saying so keeps the 20
        # August 2026 repair (an empty comparison must never pass) without mislabelling
        # a lagging projection as a repository with no history.
        if replay["stale"]:
            reason = (
                f"State covers {replay['events_projected']} of {replay['events']} "
                "events; not compared."
            )
            return _condition("A2", "unknown", reason, *evidence)
        return _condition(
            "A2",
            "unknown",
            "The trajectory is empty; comparing zero events establishes nothing about "
            "replay. Capture at least one event before this condition means anything.",
            *evidence,
        )
    if not prefix_identical:
        reason = f"Compared {prefix_events} events; canonical state diverged."
        return _condition("A2", "fail", reason, *evidence)
    reason = f"Compared {prefix_events} events; canonical state is identical."
    return _condition("A2", "pass", reason, *evidence)


def is_this_repository(name: str) -> bool:
    """Identify whether a repository string refers to this project rather than a foreign one.

    ADR-0038 renamed the repository from consilience to consilient. The public GitHub repo is
    joe-hireable/consilient and the working repository is consilient-work. Any ticket on any of
    these is internal work, not evidence of foreign-repository orchestration.
    """
    normalized = name.strip().casefold()
    return (
        normalized in THIS_REPOSITORIES
        or normalized.split("/")[-1] in THIS_REPOSITORIES
    )


def _capture_condition(log: Path) -> CommandResult:
    """Gate A condition 3, as amended by ADR-0043 and accepted 20 August 2026.

    The condition asks whether capture is working and losing nothing. It used to be
    implemented as "zero refused lines inside the window", which is a different and
    unsatisfiable thing: refusals are permanent in an append-only log, so an unbroken run
    failed at seven days, at sixty and at three hundred and sixty-five, while a run that
    *lost a day* passed. The only way to satisfy "no data loss" was to lose data.

    A refusal is the opposite of loss. It is a line that IS in the record, named invalid,
    with its reason and line number, reported beside every figure derived from the log.
    ADR-0043 and ADR-0105 tolerate six recorded historical baseline refusals by pinning
    their SHA-256 content digests (three from 2026-08-20, three from 2026-08-22). Any
    refusal whose digest is not in that baseline is a new refusal and fails the gate.

    Misdated lines are not ratcheted. A timestamp that disagrees with its file is a live
    capture fault rather than a historical judgement, and it must still fail.
    """
    days: list[date] = []
    historical_refusals_by_day: dict[date, int] = {}
    new_refusals_by_day: dict[date, int] = {}
    misdated: dict[date, int] = {}
    for path in log.glob("*.jsonl"):
        try:
            day = date.fromisoformat(path.stem)
            events, rejected = events_mod.read(path)
            matching = [event for event in events if event.raw["ts"][:10] == path.stem]
            if day <= datetime.now(timezone.utc).date() and matching:
                days.append(day)
                hist_count = sum(
                    1
                    for r in rejected
                    if r.content_digest in HISTORICAL_REFUSAL_DIGESTS
                )
                new_count = len(rejected) - hist_count
                historical_refusals_by_day[day] = hist_count
                new_refusals_by_day[day] = new_count
                misdated[day] = len(events) - len(matching)
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
    historical_refused = sum(
        count for day, count in historical_refusals_by_day.items() if day >= run_start
    )
    new_refused = sum(
        count for day, count in new_refusals_by_day.items() if day >= run_start
    )
    total_refused = historical_refused + new_refused
    stale = sum(count for day, count in misdated.items() if day >= run_start)
    reason = (
        f"Latest capture run is {run}/7 days, {run_start.isoformat()} through "
        f"{days[-1].isoformat()}."
    )
    if gap is not None:
        reason += f" The preceding gap is {gap.isoformat()}."
    if total_refused:
        reason += (
            f" The run carries {total_refused} refused line(s), of which "
            f"{historical_refused} are the recorded historical baseline (ADR-0043/0105) "
            f"and {new_refused} are new."
        )
    if stale:
        reason += f" The run has {stale} misdated line(s)."
    return _condition(
        "A3",
        "pass" if run >= 7 and new_refused == 0 and stale == 0 else "fail",
        reason,
        evidence,
    )


def _fallback_condition() -> CommandResult:
    """Gate B condition 3, as amended by ADR-0046.

    ADR-0045 required a schedule trigger as well as a result. Joe's rule — no secret anywhere
    a public repository can reach — means the exercise cannot run in this repository's CI at
    all, so that half was unsatisfiable within hours of being written.

    A schedule trigger was only ever a proxy for "this runs regularly", and a proxy that can
    hold while the job is disabled, failing to start, or watching a branch nobody pushes. A
    result dated inside the window cannot be produced without something having run. The gate
    reads the measurement and has no opinion about where it ran.
    """
    status, reason = _fallback_result()
    return _condition("B3", status, reason, FALLBACK_RESULT.as_posix())


def _fallback_result() -> tuple[str, str]:
    """Read the dated fallback result ADR-0045 requires. Absent or stale is a FAIL.

    B3 asks whether the bare-agent fallback is *exercised weekly*. A result with no date, or
    an old one, is evidence about some other week. Fourteen days is two cycles: one missed
    run is tolerated, two are not.

    Gaming protection: the result must match the documented command and include the runner
    identity from `scripts/run_fallback.py`.
    Honest limit: this stops accidental schema drift, partial hand-typed JSON, or arbitrary
    unexecuted strings; it does NOT prevent deliberate JSON fabrication by an agent or human
    who explicitly mimics the runner's exact output shape.
    """
    raw = _read_text(FALLBACK_RESULT)
    if raw is None:
        return "fail", (
            f"No fallback result at {FALLBACK_RESULT.as_posix()}; the scheduled workflow has "
            "never recorded one."
        )
    try:
        result = json.loads(raw)
        stamped = datetime.fromisoformat(str(result["ts"]))
        outcome = str(result["outcome"])
        command = str(result["command"])
        runner = str(result.get("runner", ""))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return "fail", f"The fallback result is unreadable: {exc}."
    if stamped.tzinfo is None:
        return "fail", "The fallback result timestamp carries no offset."
    age = (datetime.now(timezone.utc) - stamped).days
    if age > FALLBACK_MAX_AGE_DAYS:
        return "fail", (
            f"The fallback result is {age} days old, over the {FALLBACK_MAX_AGE_DAYS}-day "
            "limit; that is evidence about a different week."
        )
    if command != EXPECTED_FALLBACK_COMMAND:
        return "fail", f"The fallback executed unexpected command {command!r}."
    if runner and runner != FALLBACK_RUNNER_IDENTITY:
        return "fail", f"The fallback was recorded by unexpected runner {runner!r}."
    if outcome != "pass":
        return "fail", f"The fallback ran {age} day(s) ago and reported {outcome!r}."
    return "pass", f"`{command}` ran {age} day(s) ago and passed."


def _structural_condition(log: Path) -> CommandResult:
    """Gate B condition 4, no longer circular since ADR-0039 was accepted.

    It used to report `structurally_unsatisfiable`, and that was correct: the condition
    required twenty tickets orchestrated on another repository, orchestrating another
    repository was Stage 3 behaviour, and Stage 3 began only after Gate B. It could only be
    satisfied by doing what it forbade until it was satisfied.

    ADR-0039 broke that by separating entry from exit — Stage 3 is entered on the principal's
    approval and exited through Gate B — so the work that produces this evidence is now
    permitted and B4 gates DEPENDENCE rather than construction. The condition became ordinary
    unfinished work, and reporting it as a structural impossibility would now be reporting
    something an accepted decision has superseded.

    The evidence is completed tickets in the trajectory naming a repository other than this
    one. There are none, so it fails at 0 of 20 — which is what unfinished work looks like.
    """
    circularity = _read_text(GATE_B_CIRCULARITY)
    resolved = _read_text(GATE_B4_ADR)
    if circularity is None or resolved is None:
        return _condition("B4", "unknown", "The structural analysis is unavailable.")
    if not resolved.lstrip().startswith("# 0039") or "ACCEPTED" not in resolved[:1200]:
        return _condition(
            "B4",
            "structurally_unsatisfiable",
            "Gate B forbids the non-Consilient orchestration required to produce its "
            "own condition-four evidence.",
            GATE_B_CIRCULARITY.as_posix(),
        )

    completed = _foreign_tickets(log)
    return _condition(
        "B4",
        "pass" if completed >= B4_TICKETS_REQUIRED else "fail",
        f"{completed} of {B4_TICKETS_REQUIRED} tickets completed on a repository other than "
        "this one. ADR-0039 separated entry from exit, so this is unfinished work rather "
        "than a circular condition.",
        GATE_B4_ADR.as_posix(),
        f"{log.as_posix()}/*.jsonl",
    )


def _foreign_tickets(log: Path) -> int:
    """Completed tickets in the trajectory naming a repository other than this one.

    This counter checks SHAPE and cannot check truth. A writer can always compute what a
    check computes, so a hand-typed line that carries the three fields still counts. What
    it enforces is that every counted row carries the three things a third party needs to
    re-run the ticket and compare: `harness` (non-empty, the runtime that did the work),
    `corpus_revision` (non-empty, the pin that was run against), and `receipt_sha256`
    (64 lowercase hex identifying the receipt to compare).

    Gaming protection: counts distinct foreign tickets that carry verified execution evidence
    in the trajectory (an `attempt.outcome` event with `verifier_accept == True`). Bare
    `ticket.completed` events recorded via `consil record` without an associated verified
    attempt outcome are ignored.
    Honest limit: this prevents isolated hand-recorded events; it does NOT stop someone who
    artificially constructs both attempt outcome and ticket completion pairs.
    """
    verified_attempts: set[tuple[str, str]] = set()
    ticket_completions: list[tuple[str, str, str]] = []

    for path in sorted(log.glob("*.jsonl")):
        events, _ = events_mod.read(path)
        for event in events:
            data = event.raw.get("data") or {}
            kind = event.raw.get("event")
            repository = str(data.get("repository", ""))
            if not repository or is_this_repository(repository):
                continue
            if kind == events_mod.OUTCOME_KIND:
                accept = data.get("verifier_accept")
                task = str(data.get("task", "") or data.get("attempt_id", ""))
                attempt_id = str(data.get("attempt_id", ""))
                harness = data.get("harness")
                corpus_revision = data.get("corpus_revision")
                receipt = data.get("receipt_sha256")
                if (
                    (accept is True or accept == 1)
                    and isinstance(harness, str)
                    and bool(harness.strip())
                    and isinstance(corpus_revision, str)
                    and bool(corpus_revision.strip())
                    and isinstance(receipt, str)
                    and events_mod.DIGEST_RE.fullmatch(receipt) is not None
                ):
                    if task:
                        verified_attempts.add((repository, task))
                    if attempt_id:
                        verified_attempts.add((repository, attempt_id))
            elif kind == "ticket.completed":
                identifier = str(data.get("ticket", ""))
                attempt_id = str(data.get("attempt_id", ""))
                task = str(data.get("task", "")) or identifier
                if identifier:
                    ticket_completions.append(
                        (repository, identifier, attempt_id or task)
                    )

    seen: set[str] = set()
    for repo, ticket_id, attempt_or_task in ticket_completions:
        if (repo, attempt_or_task) in verified_attempts or (
            repo,
            ticket_id,
        ) in verified_attempts:
            seen.add(f"{repo}#{ticket_id}")

    return len(seen)


def _gate(conditions: list[CommandResult]) -> CommandResult:
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


_DB_BUSY_RETRIES = 6
_DB_BUSY_BACKOFF = 0.05


def cmd_doctor(args: argparse.Namespace) -> CommandResult:
    log, db = Path(args.log), Path(args.db)
    # Replay must inspect prior state before anything rebuilds the projection; rebuilding
    # first would recreate the tautological A2 check repaired on 20 August 2026. The beta
    # read that used to follow here fed Gate B2's throughput threshold, withdrawn by
    # ADR-0045.
    # A contended database is the NORMAL case here, not an exceptional one. This repository
    # runs twenty-odd agents appending to the trajectory and rebuilding the projection, and a
    # gate check that gives up the moment a writer holds the file cannot be trusted on a live
    # system -- which is the same defect as the A2 race it exists to decide. MEASURED 24 August
    # 2026: `doctor` exited 2 with "state database is locked or busy" whenever a writer thread
    # was mid-append, so the verdict depended on timing rather than on state.
    #
    # Bounded exponential retry, matching the precedent already set for trajectory reads in
    # events.py. It fails CLOSED after the last attempt: a lock we never got is reported, never
    # silently treated as a pass.
    replay = None
    for attempt in range(_DB_BUSY_RETRIES):
        try:
            replay = cmd_replay(args)
            break
        except PermissionError as exc:
            if attempt == _DB_BUSY_RETRIES - 1:
                raise EventError(
                    f"state database is locked or busy at {db} after "
                    f"{_DB_BUSY_RETRIES} attempts; close any process using it, "
                    "then run consil doctor again"
                ) from exc
            # Full jitter, for the same reason as events._retry_sleep: the SQLite state
            # database is contended by the same ~20 concurrent agents, and a lockstep retry
            # schedule makes every evicted waiter collide again at every step. Shared helper,
            # so there is one jitter rule rather than two that can drift apart.
            _jittered_sleep(_DB_BUSY_BACKOFF * (2**attempt))
    if replay is None:  # pragma: no cover - the loop either breaks or raises
        raise EventError(f"state database at {db} could not be read")
    a1, b1, b2 = _experiment_conditions()
    gates = {
        "A": _gate([a1, _replay_condition(replay, log, db), _capture_condition(log)]),
        "B": _gate([b1, b2, _fallback_condition(), _structural_condition(log)]),
    }
    expected = {"A": {"A1", "A2", "A3"}, "B": {"B1", "B2", "B3", "B4"}}
    enabled = all(
        {condition["id"] for condition in gates[name]["conditions"]} == identifiers
        and all(
            condition["status"] == "pass" for condition in gates[name]["conditions"]
        )
        for name, identifiers in expected.items()
    )
    return {
        "gates": gates,
        # Which code answered, and which directory it answered about. Unconditional: the
        # refusal below cannot fire when the measured directory is an ordinary repository,
        # and there this is the whole defence.
        "provenance": {
            "code": str(CODE_TREE),
            "data": str(Path.cwd().resolve()),
            "log": str(log.resolve()),
        },
        "routing_orchestration_enabled": enabled,
    }


def cmd_dashboard(args: argparse.Namespace) -> CommandResult:
    """Render the observability surface to one self-contained file (ADR-0053).

    Every authoritative figure is taken from the command that already owns it — `cmd_doctor`
    for the gates, `cmd_beta` for beta, `render` for beta's own sentence — and copied through
    untouched. This function performs no arithmetic on any of them. That is what makes it
    impossible for the page and the CLI to disagree, rather than merely unlikely (V0-30).
    """
    log = Path(args.log)
    # Order matters: doctor runs replay, which must inspect the state already on disk before
    # anything rebuilds it. Computing beta first would rebuild the projection and destroy the
    # subject of the A2 comparison — the exact defect repaired in `cmd_replay` on 20 Aug 2026.
    doctor = cmd_doctor(args)
    beta_result = cmd_beta(args)
    events, rejections = read_all(log)
    windows, note = dashboard_mod.read_usage(events)
    payload = dashboard_mod.build_payload(
        events,
        rejections,
        doctor,
        beta_result,
        render("beta", beta_result),
        len(events_mod.bypassed(log)),
        windows,
        note,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dashboard_mod.render_html(payload), encoding="utf-8", newline="\n")
    return {**payload, "written": str(out)}


def render(command: str, result: CommandResult) -> str:
    if command == "record":
        return f"recorded {result['event']} -> {result['file']}"
    if command == "replay":
        if result.get("version_changed"):
            mark = (
                f"REBUILT — projection version {result.get('prior_version')!r} → "
                f"{result.get('projection_version')!r}"
            )
        elif result["stale"]:
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
        traj = _trajectory_line(result)
        if traj:
            line += f"\n  {traj}"
        return line
    if command == "usage":
        lines = []
        for provider in result["providers"]:
            head = f"{provider['provider']:<12} {provider['status'].replace('_', ' ')}"
            if provider["status"] != "ok":
                lines.append(f"{head} — {provider['detail']}")
                continue
            lines.append(head)
            for quota in provider["quotas"]:
                percent = Decimal(quota["used_fraction"]) * 100
                reset = quota["resets_at"] or "no reset time reported"
                lines.append(
                    f"    quota {quota['window']:<8} {percent:>6.1f}% used, "
                    f"resets {reset}  [{quota['provenance']}]"
                )
            for item in provider["spend"]:
                lines.append(
                    f"    spend {item['period']:<8} {item['amount']} {item['currency']}"
                    f"  [{item['provenance']}]"
                )
        ceilings = result["ceilings"]
        if not ceilings["configured"]:
            lines.append(
                f"ceilings: NONE — {ceilings['refusal']}; every metered call refuses"
            )
        else:
            stated = ", ".join(
                f"{c['period']} {c['amount']} {c['currency']}"
                for c in ceilings["limits"]
            )
            lines.append(f"ceilings: {stated}")
        if result["recorded"]:
            lines.append(
                f"recorded {result['recorded']} observation(s) to the trajectory"
            )
        traj = _trajectory_line(result)
        if traj:
            lines.append(traj)
        return "\n".join(lines)
    if command == "beta":
        line = beta_mod.Beta(
            verdict=result["verdict"],
            task_family=result["task_family"],
            verifier_version=result["verifier_version"],
            n_rejected=result["n_rejected"],
            n_false_accept=result["n_false_accept"],
            point=result["point"],
            interval=tuple(result["interval"]) if result["interval"] else None,
            window=tuple(result["window"]) if result["window"] else None,
            lower_bound_on_joint_error=result.get("lower_bound_on_joint_error", False),
            caveat=result.get("caveat", ""),
        ).render()
        extras: list[str] = []
        parser_q = result.get("quarantined", 0)
        relational_q = result.get("relational_quarantine_count", 0)
        if parser_q:
            extras.append(f"parser quarantine: {parser_q} line(s)")
            for row in result.get("rejection_reasons", []):
                extras.append(f"  {row['path']}:{row['line']}  {row['reason']}")
        if relational_q:
            extras.append(f"relational quarantine: {relational_q} row(s)")
            for row in result.get("relational_quarantine", []):
                extras.append(f"  {row['path']}:{row['line']}  {row['reason']}")
        sampling = result.get("sampling_unconditioned", False)
        extras.append(
            "sampling_unconditioned: "
            + (
                "true (projection-derived)"
                if sampling
                else "false (projection-derived)"
            )
        )
        extras.append(f"oracle caveat: {result.get('caveat', '')}")
        traj = _trajectory_line(result)
        if traj:
            extras.append(traj)
        return "\n".join([line] + extras)
    if command == "dashboard":
        traj = result["trajectory"]
        unanswerable = sum(1 for g in result["schema_gaps"] if not g["answerable"])
        gaps = result["capability_gaps"]
        enabled = "yes" if result["routing_orchestration_enabled"] else "no"
        lines = [
            f"wrote {result['written']}",
            f"  {traj['events']} events, {traj['distinct_agents']} agents, "
            f"{traj['distinct_artefacts']} files written",
            f"  routing/orchestration enabled: {enabled}",
            f"  {result['beta_line']}",
            f"  RACI derivable: {'yes' if result['raci']['derivable'] else 'no'}; "
            f"{unanswerable} question(s) the record cannot answer",
            f"  capability gaps: {gaps['total']} recorded, {gaps['distinct']} distinct",
        ]
        source = _trajectory_line(result)
        if source:
            lines.insert(1, f"  {source}")
        return "\n".join(lines)
    if command == "doctor":
        provenance = result["provenance"]
        lines = [
            f"code: {provenance['code']}",
            f"data: {provenance['data']}  log: {provenance['log']}",
        ]
        traj = _trajectory_line(result)
        if traj:
            lines.append(traj)
        for name, gate in result["gates"].items():
            lines.append(f"Gate {name}: {gate['status'].replace('_', '-').upper()}")
            for condition in gate["conditions"]:
                mark = condition["status"].replace("_", "-").upper()
                lines.append(f"  {condition['id']} {mark}: {condition['requirement']}")
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

    usage = sub.add_parser(
        "usage",
        parents=[common],
        help="usage, limits and spend across every configured provider",
    )
    usage.add_argument(
        "--payloads",
        default=str(usage_mod.DEFAULT_PAYLOADS),
        help="directory an out-of-tree probe drops provider payloads into",
    )
    usage.add_argument(
        "--limits",
        default=str(usage_mod.DEFAULT_LIMITS),
        help="the instance spend-limit configuration; never committed",
    )
    usage.add_argument(
        "--record", action="store_true", help="append the snapshot to the trajectory"
    )
    usage.add_argument(
        "--fake",
        action="store_true",
        help="a fabricated snapshot for building a view against; records nothing",
    )
    usage.set_defaults(handler=cmd_usage)

    doctor = sub.add_parser(
        "doctor",
        parents=[common],
        help="report measured Gate A and Gate B status",
    )
    doctor.set_defaults(handler=cmd_doctor)

    dash = sub.add_parser(
        "dashboard",
        parents=[common],
        help="render the local observability surface to one self-contained HTML file",
    )
    dash.add_argument("--out", default=argparse.SUPPRESS)
    dash.set_defaults(handler=cmd_dashboard)
    return parser


DEFAULTS: dict[str, object] = {
    "json": False,
    "log": str(DEFAULT_LOG),
    "db": str(DEFAULT_DB),
    "out": str(DEFAULT_DASHBOARD),
    # `dashboard` reuses `cmd_beta`, which reads these. They are defaulted rather than
    # exposed as dashboard flags: the surface reports beta over the whole trajectory, and a
    # filtered beta rendered under an unfiltered heading is exactly the kind of quietly
    # narrowed denominator `cmd_beta` already refuses to let the quarantine count hide.
    "task_family": None,
    "verifier_version": None,
}


def _foreign_tree() -> str | None:
    """Refuse when the directory being measured is a checkout other than the code's own.

    Fires only in the ambiguous case. An ordinary repository has no `src/consilient/cli.py`
    and is left alone, which matters because measuring other people's repositories is what
    this tool is for -- a check that fired there would be refusing its own purpose.
    """
    cwd = Path.cwd().resolve()
    if cwd == CODE_TREE or not (cwd / "src" / "consilient" / "cli.py").exists():
        return None
    return (
        f"refusing to measure {cwd} with code from {CODE_TREE}. Those are not the same "
        "tree, so anything reported would be the second one's answer about the first "
        "one's data. Install this checkout in its own virtualenv, or set "
        f"PYTHONPATH={cwd / 'src'}."
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for name, value in DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, value)
    refusal = _foreign_tree()
    if refusal is not None:
        print(
            json.dumps({"error": refusal}) if args.json else f"error: {refusal}",
            file=sys.stderr,
        )
        return 2
    log = Path(args.log)
    try:
        if _command_needs_trajectory(args):
            require_trajectory(log)
        result = args.handler(args)
    except (EventError, projection.ProjectionError) as exc:
        print(
            json.dumps({"error": str(exc)}) if args.json else f"error: {exc}",
            file=sys.stderr,
        )
        return 2
    if log.is_dir():
        result["trajectory_source"] = {
            "path": str(log.resolve()),
            "state": trajectory_state(log),
        }
    print(
        json.dumps(result, ensure_ascii=False, sort_keys=True)
        if args.json
        else render(args.command, result)
    )
    if args.command == "doctor":
        # ADR-0015's Enforcement clause calls `consil doctor` the authority on gate status
        # and "Not advisory". Until 21 August 2026 it printed `Gate A: FAIL` and
        # `Gate B: FAIL` and exited 0 [measured], so `consil doctor && <next step>` ran the
        # next step and any caller reading `$?` was told the gates were open. That is B9 in
        # this repository's own catalogue -- a failing gate reporting success through a
        # discarded status -- made structural rather than accidental. The payload was
        # always honest; the exit code now agrees with it.
        return 0 if result["routing_orchestration_enabled"] else 1
    return 0 if result.get("identical", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Replay, and the constants every layer above pins to.

`cmd_replay` rebuilds the projection from the log and compares it against whatever state
was already on disk, which is Gate A condition 2. The comparison is made against a
pinned prefix -- the projection's own (event_count, rejection_count) high-water mark --
so events appended after that mark by other agents show up as staleness rather than as
divergence. `_copy_event_prefix` refuses to cut the log at an accepted-event count
alone: measured 26 August 2026, that cut dropped a trailing refusal already inside the
projection and pulled post-mark refusals into the prefix, so it walks classified lines
until both counts are met and treats everything after as outside the comparison.

Every value the family pins to is defined here, because this is the bottom of the
layering and there is nothing beneath it: the default log, state and dashboard paths,
the six historical refusal digests ADR-0043 and ADR-0105 tolerate, the gate document
paths, the fallback contract of ADR-0045, and the patterns that carry EXP-01's and
EXP-08's measured intervals out of the experiment register. Those constants are evidence
with dates attached, and the dates are the point -- a digest set or a tolerance with no
provenance is an assertion wearing a constant's clothes.

This module reaches no further than the event log and the projection. It knows nothing
about gates, nothing about `doctor`, and nothing about how any result is rendered for a
reader, so nothing here can be made to depend on a decision taken above it."""

from __future__ import annotations
import argparse
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Literal
from . import events as events_mod
from . import projection
from .events import EventError, read_all

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


REQUIREMENTS = {
    "A1": "EXP-01 complete on two differently verified repositories with an interval",
    "A2": "Replay reproduces an identical canonical state digest",
    "A3": "Seven consecutive days of trajectory capture with no data loss",
    "B1": "EXP-05 complete and adapter two required no shared-interface redesign",
    "B2": "The critic tier's own beta is measured, with an interval",
    "B3": "A one-command bare-Claude-Code fallback is exercised weekly",
    "B4": "Twenty non-Consilient tickets complete without harness intervention",
}


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
        (dest / path.name).write_text("".join(lines[:last_included]), encoding="utf-8")
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


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


_DB_BUSY_RETRIES = 6

_DB_BUSY_BACKOFF = 0.05

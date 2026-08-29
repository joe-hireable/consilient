"""The gate conditions the trajectory itself decides, and the refusal that guards them.

A2, A3, B3 and B4 are computed here from the log on disk. `_replay_condition` reports an
empty prefix as unknown rather than pass -- measured 21 August 2026, two `consil doctor`
runs in an empty directory, with no log and no configuration, reported A2 pass with the
reason "Compared 0 events; canonical state is identical", and a gate condition satisfied
by an empty comparison is no condition at all. `_capture_condition` asks whether capture
is losing anything, tolerating the six baseline refusals ADR-0043 and ADR-0105 pin by
content digest and failing on any refusal or misdated line beyond them; a refusal is a
line that is in the record, named invalid, which is the opposite of loss.
`_fallback_condition` reads the dated result ADR-0046 left as the whole of B3 once Joe's
rule against secrets anywhere a public repository can reach made the schedule half
unsatisfiable. `_structural_condition` counts, through `_foreign_tickets`, completed
tickets naming a repository other than this one -- and counts only those carrying a
verified attempt outcome with a harness, a corpus revision and a receipt digest.

Each check fails closed and each states what it cannot see. `_foreign_tickets` checks
shape and cannot check truth, because a writer can always compute what a check computes;
what it enforces is that every counted row carries the three things a third party needs
to re-run the ticket and compare.

`_foreign_tree` refuses the one case where the directory being measured is a Consilient
checkout other than the tree the code was imported from. Measured 21 August 2026: an
interpreter-global editable install pointed at a different worktree, so `consil doctor`
run in this one reported the other tree's Gate A answers about this one's data and
exited 0. It fires only in that ambiguous case -- an ordinary repository has no
`src/consilient/cli.py` and is left alone, because measuring other people's repositories
is what this tool is for, and a check that fired there would be refusing its own
purpose."""

from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from . import events as events_mod
from .cli_replay import (
    B4_TICKETS_REQUIRED,
    CommandResult,
    FALLBACK_RESULT,
    GATE_B4_ADR,
    GATE_B_CIRCULARITY,
    HISTORICAL_REFUSAL_DIGESTS,
    _read_text,
)

from .cli_measurements import (
    CODE_TREE,
    _condition,
    _fallback_result,
    is_this_repository,
)


__all__ = [
    "B4_TICKETS_REQUIRED",
    "CODE_TREE",
    "CommandResult",
    "FALLBACK_RESULT",
    "GATE_B4_ADR",
    "GATE_B_CIRCULARITY",
    "HISTORICAL_REFUSAL_DIGESTS",
    "_condition",
    "_fallback_result",
    "_read_text",
    "is_this_repository",
]


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
        # The FILENAME parse and the READ are separate failures and must not share a handler.
        # A name that is not a date is somebody else's jsonl and is skipped; a dated file that
        # cannot be read is a capture fault and has to reach the verdict.
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if day > datetime.now(timezone.utc).date():
            continue
        # No handler here. `events_mod.read` retries and then refuses rather than reporting a
        # partial trajectory, and `consil doctor` turns that into a top-level `{"error": ...}`
        # and exit 2 before any condition is evaluated. MEASURED 29 August 2026 against a
        # directory named like a daily file. Catching it here would convert a refusal that
        # names the unreadable path into an A3 line that quietly says "fail".
        events, rejected = events_mod.read(path)
        matching = [event for event in events if event.raw["ts"][:10] == path.stem]
        # MEASURED: `and matching` dropped a day whose file yielded no correctly-dated event,
        # so a torn append landing as the first line of today's file left A3 reporting a
        # clean 7/7 run and never naming the refusal. A day counts when its file produced
        # anything at all; an empty file still does not, which keeps the 0/7 branch.
        if events or rejected:
            days.append(day)
            hist_count = sum(
                1 for r in rejected if r.content_digest in HISTORICAL_REFUSAL_DIGESTS
            )
            new_count = len(rejected) - hist_count
            historical_refusals_by_day[day] = hist_count
            new_refusals_by_day[day] = new_count
            misdated[day] = len(events) - len(matching)
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

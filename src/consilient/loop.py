"""An always-on loop whose every tick is in the trajectory.

This module is the loop's *policy*: what gets recorded, where a tick may run, when the
budget refuses one, and what "working" means. It holds no execution capability at all —
`test_product_tree_has_no_outbound_or_credential_capability` forbids `subprocess` anywhere
under `src/consilient/`, and that boundary is worth more than the convenience of one file.
The supervisor that actually spawns, polls and kills lives in `scripts/run_loop.py`.

Invariants declared here, each with a test in the same commit:

  V0-29  Every tick is recorded through `append()`: its intent before the side effect and
         its outcome after. A tick interrupted between the two is recorded as abandoned on
         resume and is **never re-executed**.
  V0-30  A loop runs only inside a Consilient checkout, with its trajectory inside that
         workspace. Gate B forbids pointing the harness at another repository.

Two invariants the specification has declared since 19 August and nothing enforced get
their checks here, which is the point of building this at all:

  V0-20  Hard budget ceilings; exhaustion stops the loop rather than continuing.
  V0-25  Liveness is never resolved from a process identity. `status` reads the recorded
         ticks and the bytes the current tick has produced, and nothing else — this machine
         has produced a launcher that exited 0 while the work never started, and a process
         watched for thirty minutes that turned out to be the wrong one.

**What crash-safety means here, precisely.** The intent record is appended and the file
closed before the side effect starts, so a process kill after that point cannot lose it:
the bytes are already with the operating system. What a kill *can* destroy is the outcome
record of the tick that was in flight — the process died before it could write one. So the
guarantee is **at-most-once execution**, not exactly-once: on resume the interrupted tick
is recorded as abandoned with its outcome unknown, and the loop moves on. Re-running it
would be the other choice, and it is the wrong one for a tick with side effects.

ponytail: `append()` does not fsync, so this survives a process kill and not a power cut.
Upgrade path is an fsync in `events._write_validated`, which costs every writer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import budget as budget_mod
from .events import METERED_CURRENCY, SCHEMA_VERSION, Event, append, read_all

ACTOR = "consilient.loop"
TICK_STARTED = "loop.tick.started"
TICK_FINISHED = "loop.tick.finished"
TICK_ABANDONED = "loop.tick.abandoned"
LOOP_STOPPED = "loop.stopped"
KINDS = (TICK_STARTED, TICK_FINISHED, TICK_ABANDONED, LOOP_STOPPED)

# The file that identifies a Consilient checkout. Present in every clone and worktree of
# this repository and in no other repository on this machine, which is what makes it a
# Gate B check rather than a name list nobody maintains.
MARKER = "CONSILIENCE.md"

# ponytail: silence worth three whole cycles is a stall. A tunable would be a knob nobody
# has evidence to set; raise it only if a measured tick duration justifies it.
STALE_CYCLES = 3


class LoopError(RuntimeError):
    """The loop refused to start or to continue."""


@dataclass(frozen=True)
class Loop:
    """One loop's configuration. Everything derived from it is a pure function of it."""

    name: str
    root: Path
    log_dir: Path
    command: tuple[str, ...]
    interval_s: float
    timeout_s: float
    cost_per_tick: Decimal = Decimal(0)
    ceilings: tuple[budget_mod.Ceiling, ...] = field(default_factory=tuple)
    max_ticks: int | None = None

    @property
    def runtime_dir(self) -> Path:
        """Transient files. `.harness/dispatch/` is already git-ignored as agent output."""
        return self.log_dir.parent / "dispatch"

    @property
    def stop_file(self) -> Path:
        return self.runtime_dir / f"loop-{self.name}.stop"

    @property
    def transcript(self) -> Path:
        return self.runtime_dir / f"loop-{self.name}.out"

    @property
    def lock_file(self) -> Path:
        return self.runtime_dir / f"loop-{self.name}.lock"


def _inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def _as_path(argument: str, root: Path) -> Path | None:
    """The path an argument names, or None if it does not name one that exists."""
    try:
        candidate = Path(argument)
        resolved = (
            candidate if candidate.is_absolute() else root / candidate
        ).resolve()
        return resolved if resolved.exists() else None
    except (OSError, ValueError):
        return None


def refusal(loop: Loop) -> str | None:
    """Every reason this loop must not start, or None. V0-30 is the first of them.

    ponytail: the argument scan catches `git -C ../other-repo`, which is the measured
    failure (R14). It does not read inside a `-c` script or a config file the command
    loads; the workspace check is what carries Gate B, and the scan is a second line.
    """
    root = loop.root.resolve()
    if not (root / MARKER).is_file():
        return (
            f"{root} is not a Consilient checkout ({MARKER} is absent). Gate B forbids "
            "pointing the harness at any repository other than this one (V0-30)."
        )
    if not _inside(loop.log_dir.resolve(), root):
        return (
            f"the trajectory at {loop.log_dir} is outside the workspace {root}; a loop "
            "records into the repository it runs in (V0-30)."
        )
    if not loop.name.strip():
        return "a loop must be named, because its record is keyed by the name"
    if not loop.command:
        return "a loop must be given a command to run"
    # The executable itself is exempt: an interpreter legitimately lives outside the
    # workspace. Its arguments are what could name another repository.
    for argument in loop.command[1:]:
        named = _as_path(argument, root)
        if named is not None and not _inside(named, root):
            return (
                f"argument {argument!r} names {named}, outside the workspace {root} "
                "(V0-30)."
            )
    if loop.interval_s < 0 or loop.timeout_s <= 0:
        return "interval must be non-negative and the tick timeout positive"
    if loop.max_ticks is not None and loop.max_ticks < 1:
        return "a tick ceiling must be at least one"
    if loop.cost_per_tick < 0:
        return "cost per tick cannot be negative"
    if loop.cost_per_tick > 0 and not loop.ceilings:
        return "a loop that spends must declare a weekly or monthly ceiling (V0-20)"
    return None


def record(loop: Loop, kind: str, tick: int, data: dict[str, Any]) -> dict[str, Any]:
    """Append one loop event through the single writer, into the file its date names.

    The daily file must match the event's own timestamp or Gate A3 counts the line as
    misdated, so the path is derived from the stamp rather than from the loop's start.
    """
    now = datetime.now(timezone.utc)
    return append(
        loop.log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": kind,
            "actor": ACTOR,
            "data": {"loop": loop.name, "tick": tick, **data},
        },
    )


def _recorded(loop: Loop) -> list[Event]:
    events, _ = read_all(loop.log_dir)
    return [
        event
        for event in events
        if event.kind in KINDS and event.data.get("loop") == loop.name
    ]


def _tick_of(event: Event) -> int | None:
    tick = event.data.get("tick")
    return tick if isinstance(tick, int) and not isinstance(tick, bool) else None


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def resume(loop: Loop) -> int:
    """Record any interrupted tick as abandoned and return the next tick number. V0-29.

    A tick with an intent record and no outcome is one the process died inside. Whether its
    side effect completed is unknowable from here — the record that would have said so is
    exactly what was lost — so it is never re-executed. The uncertainty is written down
    instead of being resolved by a guess.
    """
    started: set[int] = set()
    settled: set[int] = set()
    for event in _recorded(loop):
        tick = _tick_of(event)
        if tick is None:
            continue
        if event.kind == TICK_STARTED:
            started.add(tick)
        elif event.kind in (TICK_FINISHED, TICK_ABANDONED):
            settled.add(tick)
    for tick in sorted(started - settled):
        record(
            loop,
            TICK_ABANDONED,
            tick,
            {
                "outcome": "unknown",
                "reason": (
                    "the loop was interrupted before this tick's outcome was recorded; "
                    "it is not re-executed"
                ),
            },
        )
    return max(started) + 1 if started else 1


def reserve(loop: Loop, tick: int) -> str | None:
    """The budget's refusal for this tick, or None. V0-20.

    A tick that spends nothing needs no permission. A tick that spends anything gets one
    from `budget.check_budget`, which records the reservation in the trajectory and refuses
    the moment a weekly or monthly ceiling would be breached. The caller stops on a
    refusal; there is no path on which the loop spends past a ceiling.
    """
    if loop.cost_per_tick == 0:
        return None
    decision = budget_mod.check_budget(
        loop.log_dir,
        loop.ceilings,
        budget_mod.SpendRequest(
            f"{loop.name}#{tick}", loop.cost_per_tick, METERED_CURRENCY
        ),
    )
    if isinstance(decision, budget_mod.BudgetRefusal):
        return decision.reason
    return None


def status(loop: Loop, now: datetime | None = None) -> dict[str, Any]:
    """What the loop has produced. V0-25: never a process identity.

    There is no PID here and no process lookup. `working` is answered from two artefacts:
    the recorded tick outcomes, and — for a tick still in flight — how many bytes its
    transcript has gained since the intent record captured its size. A process that is
    alive and producing nothing reports `working: false`, which is the twelve minutes this
    machine lost to a runtime waiting on a terminal that was never going to arrive.
    """
    current = now or datetime.now(timezone.utc)
    started = finished = abandoned = silent = 0
    produced = 0
    last_tick = 0
    baseline: int | None = None
    in_flight = False
    last_outcome: str | None = None
    last_outcome_at: datetime | None = None
    stopped: str | None = None

    for event in _recorded(loop):
        tick = _tick_of(event)
        stamped = datetime.fromisoformat(event.raw["ts"]).astimezone(timezone.utc)
        if event.kind == TICK_STARTED:
            started += 1
            in_flight = True
            if tick is not None:
                last_tick = tick
            baseline = _int(event.data.get("transcript_bytes"))
            stopped = None
        elif event.kind == TICK_FINISHED:
            finished += 1
            in_flight = False
            outcome = event.data.get("outcome")
            last_outcome = outcome if isinstance(outcome, str) else "unknown"
            silent += 1 if last_outcome == "silent" else 0
            produced += _int(event.data.get("produced_bytes"))
            last_outcome_at = stamped
        elif event.kind == TICK_ABANDONED:
            abandoned += 1
            in_flight = False
            last_outcome = "abandoned"
            last_outcome_at = stamped
        elif event.kind == LOOP_STOPPED:
            reason = event.data.get("reason")
            stopped = reason if isinstance(reason, str) else "unrecorded"

    grown: int | None = None
    if in_flight and baseline is not None:
        try:
            grown = loop.transcript.stat().st_size - baseline
        except OSError:
            grown = 0

    silence = (
        None if last_outcome_at is None else (current - last_outcome_at).total_seconds()
    )
    tolerance = STALE_CYCLES * (loop.interval_s + loop.timeout_s)
    if in_flight:
        working = (grown or 0) > 0
        reason = (
            f"tick {last_tick} has produced {grown or 0} byte(s) since it started"
            if working
            else f"tick {last_tick} is in flight and has produced nothing yet"
        )
    elif silence is None:
        working, reason = False, "no tick outcome has ever been recorded"
    elif stopped is not None:
        working, reason = False, f"the loop stopped: {stopped}"
    else:
        working = silence <= tolerance
        reason = (
            f"the last tick finished {silence:.0f}s ago, within the {tolerance:.0f}s "
            "tolerance"
            if working
            else f"no tick outcome for {silence:.0f}s, past the {tolerance:.0f}s tolerance"
        )

    return {
        "loop": loop.name,
        "ticks_started": started,
        "ticks_finished": finished,
        "ticks_abandoned": abandoned,
        "ticks_silent": silent,
        "last_tick": last_tick,
        "in_flight": in_flight,
        "bytes_produced": produced,
        "bytes_since_tick_started": grown,
        "last_outcome": last_outcome,
        "last_outcome_at": (
            last_outcome_at.isoformat() if last_outcome_at is not None else None
        ),
        "seconds_since_outcome": silence,
        "working": working,
        "reason": reason,
        "stop_requested": loop.stop_file.exists(),
        "stopped": stopped,
    }

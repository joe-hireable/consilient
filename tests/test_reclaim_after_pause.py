"""A maintenance pause must not halt every dispatch on the tick that follows it.

MEASURED 30 August 2026. A 90-minute STOP-LOOP pause left eight units in flight. The first
tick back reclaimed all eight in the same second, eleven restarts landed inside two minutes
against a limit of six per ten, `record_restart` escalated to `quarantine_unit(state, "*")`,
and `dispatch_allowed` then refused every build dispatch: the loop ticked and dispatched
nothing until the "*" was cleared by hand. F-05 already refunds each unit's ATTEMPT for
exactly this reason -- an infrastructure death is not evidence about the work -- so the
inconsistency was that the same reasoning never reached the restart counter.
"""

from __future__ import annotations

from typing import Any

from tests.build_driver_helpers import _load_driver

DRIVER = _load_driver()


def _state(units: int, *, last_tick: float | None, now: float) -> dict[str, Any]:
    """`units` slots, every leash long expired, as a pause leaves them."""
    state: dict[str, Any] = {
        "in_flight": {f"U{i:02d}": (now - 9000.0, 3600.0) for i in range(units)},
        "quarantined": [],
        "attempts": {},
    }
    if last_tick is not None:
        state["last_tick_at"] = last_tick
    return state


def test_a_resume_tick_does_not_globally_quarantine() -> None:
    """Eight slots expiring during an absence is one event, so dispatch stays allowed."""
    import time

    now = time.time()
    state = _state(8, last_tick=now - 5400.0, now=now)
    DRIVER.reclaim_expired_slots(state)
    assert "*" not in state["quarantined"], (
        "a resume tick set the global dispatch stop again: eight reclaims from one pause "
        "were counted as eight repair attempts, which halts every build dispatch"
    )
    assert DRIVER.dispatch_allowed(state, "build", "U00"), "dispatch must stay allowed"


def test_the_batch_still_records_one_restart() -> None:
    """Forgiving the batch must not mean forgetting it, or pause-cycling never escalates."""
    import time

    now = time.time()
    state = _state(8, last_tick=now - 5400.0, now=now)
    before = len(state.get("total_restarts", []) or [])
    DRIVER.reclaim_expired_slots(state)
    after = len(state.get("total_restarts", []) or [])
    assert after == before + 1, (
        f"expected exactly one restart recorded for the batch, got {after - before}"
    )


def test_an_ordinary_tick_still_counts_every_unit() -> None:
    """The guard is unchanged during normal operation; ticks are 5 min, the window is 600s."""
    import time

    now = time.time()
    state = _state(8, last_tick=now - 300.0, now=now)
    DRIVER.reclaim_expired_slots(state)
    assert len(state.get("total_restarts", []) or []) == 8, (
        "an ordinary tick must still record one restart per reclaimed unit"
    )
    assert "*" in state["quarantined"], (
        "eight repair attempts inside the window must still escalate; without this the "
        "change would have removed the guard rather than corrected its input"
    )


def test_a_missing_stamp_counts_as_an_absence() -> None:
    """It occurs on the first tick after this change and on a fresh checkout: neither cycles."""
    import time

    now = time.time()
    state = _state(8, last_tick=None, now=now)
    DRIVER.reclaim_expired_slots(state)
    assert "*" not in state["quarantined"]


def test_the_stamp_is_written_every_tick() -> None:
    """Without the write, every tick looks like an absence and the guard never fires."""
    import time

    now = time.time()
    state = _state(1, last_tick=now - 300.0, now=now)
    DRIVER.reclaim_expired_slots(state)
    assert "last_tick_at" in state
    assert state["last_tick_at"] >= now

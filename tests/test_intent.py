"""N06 (BU-6) - the intent record, its non-selection reasons and the starvation event.

`docs/20-design/supervision-escalation-and-sessions-2026-08-23.md` section 2.1: the
scheduler writes, at every tick and *before* selection, every ready unit and, for each
unit it did not select, the reason. A unit carrying the same reason for N consecutive
ticks is an event. This is the only mechanism in that specification that catches F-08,
because F-08 produced no dispatch, no lease and no call - nothing failed, work simply
stopped being selected [measured, `docs/00-context/orchestration-failure-modes-2026-08-23.md`].

Timestamps here are near-live deliberately: `append` refuses an event more than
`MAX_CLOCK_SKEW_S` from the wall clock, so an hour of ticks cannot be faked at the
writing boundary. The hour floor is therefore exercised against the pure derivation,
and the tick floor against the writing path with the window lowered.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import events as events_mod
from consilient.events import EventError, read_all

ROOT = Path(__file__).resolve().parent.parent
DRIVER_PATH = ROOT / ".harness" / "build_driver.py"


def _driver():
    name = "build_driver_intent_test"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DRIVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

NO_WINDOW = timedelta(0)


def _now(offset_s: float = 0.0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _bench(
    log_path: Path,
    *,
    tick: int,
    unit: str = "N06",
    reason: str = "quota_exhausted:codex",
    window: timedelta = NO_WINDOW,
) -> list[events_mod.EventPayload]:
    """One tick at which `unit` was ready and was not selected, for `reason`."""
    return events_mod.record_intent(
        log_path,
        ts=_now(),
        tick=tick,
        selected=(),
        not_selected={unit: reason},
        window=window,
    )


def _intent(tick: int, minutes: float, unit: str, reason: str) -> events_mod.Event:
    """A tick as it would be read back, at an offset no writer would be allowed to stamp."""
    return events_mod.Event(
        raw={
            "v": events_mod.SCHEMA_VERSION,
            "ts": (
                datetime(2026, 8, 23, 9, tzinfo=timezone.utc)
                + timedelta(minutes=minutes)
            ).isoformat(),
            "event": events_mod.INTENT_RECORDED_KIND,
            "actor": events_mod.SCHEDULER_ACTOR,
            "data": {"tick": tick, "selected": [], "not_selected": {unit: reason}},
        }
    )


def _kinds(log_path: Path) -> list[str]:
    events, rejected = read_all(log_path.parent)
    assert rejected == []
    return [event.kind for event in events]


def _starved(log_path: Path) -> list[events_mod.EventPayload]:
    events, _rejected = read_all(log_path.parent)
    return [
        event.data for event in events if event.kind == events_mod.INTENT_STARVED_KIND
    ]


def test_an_arm_benched_for_six_ticks_emits_starved(tmp_path: Path) -> None:
    """The unit's own done criterion: arm benched for 6 ticks emits `intent.starved`."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    emitted: list[events_mod.EventPayload] = []
    for tick in range(events_mod.STARVATION_TICKS):
        emitted = _bench(log_path, tick=tick)

    assert _kinds(log_path).count(events_mod.INTENT_STARVED_KIND) == 1
    assert [event["event"] for event in emitted] == [
        events_mod.INTENT_RECORDED_KIND,
        events_mod.INTENT_STARVED_KIND,
    ]
    starved = _starved(log_path)[0]
    assert starved["unit"] == "N06"
    assert starved["reason"] == "quota_exhausted:codex"
    assert starved["ticks"] == events_mod.STARVATION_TICKS


def test_six_ticks_inside_a_second_do_not_starve_at_the_specified_default(
    tmp_path: Path,
) -> None:
    """Section 2.1: "6 ticks or 60 minutes, whichever is longer" - the count alone is not it."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(events_mod.STARVATION_TICKS):
        events_mod.record_intent(
            log_path,
            ts=_now(),
            tick=tick,
            selected=(),
            not_selected={"N06": "quota_exhausted:codex"},
        )

    assert _starved(log_path) == []


def test_both_floors_are_measured_from_the_tick_timestamps() -> None:
    fast = [_intent(t, t * 2, "N06", "no_capacity") for t in range(8)]
    assert events_mod.starvation(fast) == []

    few = [_intent(t, t * 20, "N06", "no_capacity") for t in range(5)]
    assert events_mod.starvation(few) == []

    slow = [_intent(t, t * 15, "N06", "no_capacity") for t in range(6)]
    assert events_mod.starvation(slow) == [
        {
            "unit": "N06",
            "reason": "no_capacity",
            "ticks": 6,
            "since": datetime(2026, 8, 23, 9, tzinfo=timezone.utc).isoformat(),
        }
    ]


def test_being_selected_resets_the_run(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(5):
        _bench(log_path, tick=tick)
    events_mod.record_intent(
        log_path,
        ts=_now(),
        tick=5,
        selected=("N06",),
        not_selected={},
        window=NO_WINDOW,
    )
    for tick in range(6, 11):
        _bench(log_path, tick=tick)

    assert _starved(log_path) == []


def test_no_longer_being_ready_resets_the_run(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(5):
        _bench(log_path, tick=tick)
    events_mod.record_intent(
        log_path, ts=_now(), tick=5, selected=(), not_selected={}, window=NO_WINDOW
    )
    for tick in range(6, 11):
        _bench(log_path, tick=tick)

    assert _starved(log_path) == []


def test_a_changed_reason_resets_the_run(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(5):
        _bench(log_path, tick=tick)
    for tick in range(5, 10):
        _bench(log_path, tick=tick, reason="breaker_open:codex")

    assert _starved(log_path) == []

    _bench(log_path, tick=10, reason="breaker_open:codex")
    assert [starved["reason"] for starved in _starved(log_path)] == [
        "breaker_open:codex"
    ]


def test_a_starved_run_is_reported_once_not_every_tick(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(12):
        _bench(log_path, tick=tick)

    assert len(_starved(log_path)) == 1


def test_a_replayed_tick_number_does_not_advance_the_run(tmp_path: Path) -> None:
    """Ticks are counted by their number, so re-reading one tick cannot manufacture six."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for _ in range(8):
        _bench(log_path, tick=0)

    assert _starved(log_path) == []


def test_each_starved_unit_is_reported_separately(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    for tick in range(events_mod.STARVATION_TICKS):
        events_mod.record_intent(
            log_path,
            ts=_now(),
            tick=tick,
            selected=(),
            not_selected={"N06": "no_capacity", "N07": "blocked_on:N06"},
            window=NO_WINDOW,
        )

    assert sorted(str(starved["unit"]) for starved in _starved(log_path)) == [
        "N06",
        "N07",
    ]


@pytest.mark.parametrize(
    "reason",
    ["blocked_on:N05", "quota_exhausted:codex", "breaker_open:grok", "no_capacity"],
)
def test_the_four_reasons_of_the_specification_are_accepted(
    tmp_path: Path, reason: str
) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _bench(log_path, tick=0, reason=reason)
    assert _kinds(log_path) == [events_mod.INTENT_RECORDED_KIND]


@pytest.mark.parametrize(
    "reason",
    ["benched", "blocked_on:", "quota_exhausted", "no_capacity:codex", "", " "],
)
def test_an_unnamed_non_selection_reason_is_refused(
    tmp_path: Path, reason: str
) -> None:
    """A reason outside the vocabulary is a silent bench under a new name. Refuse it."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    with pytest.raises(EventError, match="reason"):
        _bench(log_path, tick=0, reason=reason)


def test_a_unit_cannot_be_both_selected_and_not_selected(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    with pytest.raises(EventError, match="cannot be both selected and not selected"):
        events_mod.record_intent(
            log_path,
            ts=_now(),
            tick=0,
            selected=("N06",),
            not_selected={"N06": "no_capacity"},
        )


def test_the_intent_record_carries_no_undeclared_field(tmp_path: Path) -> None:
    """`alive_at` is the field section 2.1 refuses by name; nothing may smuggle it in."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    with pytest.raises(EventError, match="unexpected field"):
        events_mod.append(
            log_path,
            {
                "v": events_mod.SCHEMA_VERSION,
                "ts": _now(),
                "event": events_mod.INTENT_RECORDED_KIND,
                "actor": events_mod.SCHEDULER_ACTOR,
                "data": {
                    "tick": 0,
                    "selected": [],
                    "not_selected": {},
                    "alive_at": _now(),
                },
            },
        )


def test_a_starvation_claim_below_the_tick_floor_is_refused(tmp_path: Path) -> None:
    """`intent.starved` asserts a threshold was crossed; it may not be minted below it."""
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    with pytest.raises(EventError, match="ticks"):
        events_mod.append(
            log_path,
            {
                "v": events_mod.SCHEMA_VERSION,
                "ts": _now(),
                "event": events_mod.INTENT_STARVED_KIND,
                "actor": events_mod.SCHEDULER_ACTOR,
                "data": {
                    "unit": "N06",
                    "reason": "no_capacity",
                    "ticks": events_mod.STARVATION_TICKS - 1,
                    "since": _now(),
                },
            },
        )


def test_a_blocked_unit_is_recorded_as_blocked_on_its_dependency() -> None:
    """Section 2.1: non-selection is a named reason, not an absence from the record."""
    reasons = _driver().not_selected_reasons(
        units={"N07": {"deps": ["N06"]}, "N06": {"deps": []}},
        landed=set(),
        blocked=["N07"],
        startable=["N06"],
        selected=["N06"],
    )
    assert reasons == {"N07": "blocked_on:N06"}


def test_unlaunched_ready_units_are_recorded_as_no_capacity() -> None:
    reasons = _driver().not_selected_reasons(
        units={"N06": {"deps": []}, "N07": {"deps": []}},
        landed=set(),
        blocked=[],
        startable=["N06", "N07"],
        selected=["N06"],
    )
    assert reasons == {"N07": "no_capacity"}


def test_the_scheduler_writes_intent_before_it_spawns() -> None:
    """The record exists even if spawn dies. Writing after Popen recreates F-08."""
    source = inspect.getsource(_driver().main)
    intent_at = source.find("record_tick_intent(")
    assert intent_at != -1, "the tick never writes an intent record"
    launch_at = source.find("for uid in startable:")
    assert launch_at != -1
    assert intent_at < launch_at, "intent must be on disk before spawn"


def test_the_driver_appends_intent_through_events_py() -> None:
    """events.py is the single writer. A second log is the defect the brief forbids."""
    source = inspect.getsource(_driver().record_tick_intent)
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "record_intent" in names | attrs


def test_the_driver_writes_the_tick_onto_the_trajectory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = _driver()
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    monkeypatch.setattr(driver, "LOG", log_dir)
    driver.record_tick_intent(
        0,
        selected=(),
        not_selected={"N06": "quota_exhausted:codex"},
        window=NO_WINDOW,
    )
    assert _kinds(tmp_path / "log" / "ignored.jsonl") == [
        events_mod.INTENT_RECORDED_KIND
    ]


def test_six_driver_ticks_on_a_benched_arm_emit_starved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The unit's done criterion, through the scheduler rather than the writer alone."""
    driver = _driver()
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    monkeypatch.setattr(driver, "LOG", log_dir)
    for tick in range(events_mod.STARVATION_TICKS):
        driver.record_tick_intent(
            tick,
            selected=(),
            not_selected={"N06": "quota_exhausted:codex"},
            window=NO_WINDOW,
        )
    assert [starved["unit"] for starved in _starved(tmp_path / "log" / "ignored.jsonl")] == [
        "N06"
    ]

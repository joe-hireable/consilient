"""N07 (BU-7) - one validated, budgeted escalation record."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import events as events_mod
from consilient.events import EventError, read_all


BASE = datetime(2026, 8, 26, 12, tzinfo=timezone.utc)


def _ts(hours: float = 0) -> str:
    return (BASE + timedelta(hours=hours)).isoformat()


def _written_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _attempt(
    log_path: Path,
    *,
    root_cause: str = "dispatch-crash",
    escalation_class: str = "credential",
    ts: str | None = None,
    decision_changed: bool | None = None,
) -> events_mod.EventPayload:
    return events_mod.record_escalation(
        log_path,
        ts=_written_at() if ts is None else ts,
        root_cause=root_cause,
        escalation_class=escalation_class,
        what_stopped="The dispatch worker exited before starting.",
        what_it_is_holding="The N07 lease and its blocked dependants.",
        what_i_need="A credential with the required scope.",
        default_if_no_reply={"default": "Leave the work blocked.", "fires_at": _ts(1)},
        evidence=".harness/dispatch.log:42",
        decision_changed=decision_changed,
    )


def _history(
    root_cause: str, ts: str, decision_changed: bool | None = None
) -> events_mod.Event:
    return events_mod.Event(
        raw={
            "v": events_mod.SCHEMA_VERSION,
            "ts": ts,
            "event": events_mod.ESCALATION_ATTEMPTED_KIND,
            "actor": events_mod.ESCALATION_ACTOR,
            "data": {
                "root_cause": root_cause,
                "escalation_class": "credential",
                "what_stopped": "The worker exited.",
                "what_it_is_holding": "The N07 lease.",
                "what_i_need": "A credential.",
                "default_if_no_reply": {
                    "default": "Leave the work blocked.",
                    "fires_at": _ts(1),
                },
                "evidence": ".harness/dispatch.log:42",
                "disposition": "delivered",
                "refusal_reason": None,
                "decision_changed": decision_changed,
            },
        }
    )


def _candidate(root_cause: str, ts: str) -> events_mod.EventPayload:
    return {
        "v": events_mod.SCHEMA_VERSION,
        "ts": ts,
        "event": events_mod.ESCALATION_ATTEMPTED_KIND,
        "actor": events_mod.ESCALATION_ACTOR,
        "data": {
            "root_cause": root_cause,
            "escalation_class": "credential",
            "what_stopped": "The worker exited.",
            "what_it_is_holding": "The N07 lease.",
            "what_i_need": "A credential.",
            "default_if_no_reply": {
                "default": "Leave the work blocked.",
                "fires_at": _ts(1),
            },
            "evidence": ".harness/dispatch.log:42",
            "disposition": "delivered",
            "refusal_reason": None,
            "decision_changed": None,
        },
    }


def _attempts(log_path: Path) -> list[events_mod.Event]:
    events, rejected = read_all(log_path.parent)
    assert rejected == []
    return [
        event
        for event in events
        if event.kind == events_mod.ESCALATION_ATTEMPTED_KIND
    ]


def test_one_crash_emits_one_delivered_escalation_not_three(tmp_path: Path) -> None:
    """Removing duplicate-root inhibition would deliver all three attempts."""
    log_path = tmp_path / "2026-08-26.jsonl"

    for _ in range(3):
        _attempt(log_path)

    attempts = _attempts(log_path)
    assert [attempt.data["disposition"] for attempt in attempts] == [
        "delivered",
        "refused",
        "refused",
    ]
    assert [attempt.data["refusal_reason"] for attempt in attempts[1:]] == [
        "duplicate_root_cause",
        "duplicate_root_cause",
    ]


def test_missing_what_i_need_is_refused_at_construction(tmp_path: Path) -> None:
    """Removing required-plan-field validation would append this interruption."""
    with pytest.raises(EventError, match="what_i_need"):
        events_mod.record_escalation(
            tmp_path / "2026-08-26.jsonl",
            ts=_written_at(),
            root_cause="dispatch-crash",
            escalation_class="credential",
            what_stopped="The dispatch worker exited before starting.",
            what_it_is_holding="The N07 lease and its blocked dependants.",
            what_i_need="",
            default_if_no_reply={
                "default": "Leave the work blocked.",
                "fires_at": _ts(1),
            },
            evidence=".harness/dispatch.log:42",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("what_stopped", " "),
        ("what_it_is_holding", " holding"),
        ("what_i_need", "need "),
        ("evidence", ""),
    ],
)
def test_plan_strings_must_be_non_empty_and_unpadded(
    tmp_path: Path, field: str, value: str
) -> None:
    """Removing canonical plan-string validation would accept an incomplete brief."""
    kwargs: dict[str, str] = {field: value}
    with pytest.raises(EventError, match=field):
        events_mod.record_escalation(
            tmp_path / "2026-08-26.jsonl",
            ts=_written_at(),
            root_cause="dispatch-crash",
            escalation_class="credential",
            what_stopped=kwargs.get("what_stopped", "The worker exited."),
            what_it_is_holding=kwargs.get("what_it_is_holding", "The N07 lease."),
            what_i_need=kwargs.get("what_i_need", "A credential."),
            default_if_no_reply={
                "default": "Leave the work blocked.",
                "fires_at": _ts(1),
            },
            evidence=kwargs.get("evidence", ".harness/dispatch.log:42"),
        )


def test_raw_append_cannot_bypass_the_escalation_schema(tmp_path: Path) -> None:
    """Removing the event contract would let raw append omit a required plan field."""
    with pytest.raises(EventError, match="what_i_need"):
        events_mod.append(
            tmp_path / "2026-08-26.jsonl",
            {
                "v": events_mod.SCHEMA_VERSION,
                "ts": _written_at(),
                "event": events_mod.ESCALATION_ATTEMPTED_KIND,
                "actor": events_mod.ESCALATION_ACTOR,
                "data": {
                    "root_cause": "dispatch-crash",
                    "escalation_class": "credential",
                    "what_stopped": "The worker exited.",
                    "what_it_is_holding": "The N07 lease.",
                    "default_if_no_reply": {
                        "default": "Leave the work blocked.",
                        "fires_at": _ts(1),
                    },
                    "evidence": ".harness/dispatch.log:42",
                    "disposition": "delivered",
                    "refusal_reason": None,
                    "decision_changed": None,
                },
            },
        )


def test_duplicate_at_exactly_24_hours_is_not_inhibited() -> None:
    """Changing the rolling-window boundary would refuse the second delivery."""
    history = [_history("dispatch-crash", _ts(-24))]
    disposition, reason = events_mod._escalation_disposition(
        history, _candidate("dispatch-crash", _ts())
    )

    assert (disposition, reason) == ("delivered", None)


def test_all_budget_drops_are_recorded(tmp_path: Path) -> None:
    """Removing budget accounting would deliver more than three root causes."""
    log_path = tmp_path / "2026-08-26.jsonl"
    for index in range(5):
        _attempt(log_path, root_cause=f"cause-{index}")

    assert [attempt.data["disposition"] for attempt in _attempts(log_path)] == [
        "delivered",
        "delivered",
        "delivered",
        "refused",
        "refused",
    ]
    assert [attempt.data["refusal_reason"] for attempt in _attempts(log_path)[3:]] == [
        "budget_exhausted",
        "budget_exhausted",
    ]


def test_raw_append_uses_the_same_locked_budget(tmp_path: Path) -> None:
    """Removing the transition rule would let raw append evade the three-delivery cap."""
    log_path = tmp_path / "2026-08-26.jsonl"
    for index in range(5):
        events_mod.append(log_path, _candidate(f"raw-{index}", _written_at()))

    assert [attempt.data["disposition"] for attempt in _attempts(log_path)] == [
        "delivered",
        "delivered",
        "delivered",
        "refused",
        "refused",
    ]


def test_complete_low_precision_window_halves_budget() -> None:
    """Ignoring resolved outcomes would allow three deliveries instead of one."""
    history = [
        _history(
            f"history-{index}", _ts(-48 - 25 * index), decision_changed=index < 13
        )
        for index in range(20)
    ]
    first = _candidate("new-1", _ts())
    disposition, reason = events_mod._escalation_disposition(history, first)
    history.append(events_mod.Event(raw=first))
    second = _candidate("new-2", _ts())

    assert (disposition, reason) == ("delivered", None)
    assert events_mod._escalation_disposition(history, second) == (
        "refused",
        "budget_exhausted",
    )


def test_fewer_than_twenty_resolved_attempts_do_not_halve_budget() -> None:
    """Halving an incomplete precision window would refuse the second delivery."""
    history = [
        _history(
            f"history-{index}", _ts(-48 - 25 * index), decision_changed=False
        )
        for index in range(19)
    ]
    first = _candidate("new-1", _ts())
    disposition, reason = events_mod._escalation_disposition(history, first)
    history.append(events_mod.Event(raw=first))
    second = _candidate("new-2", _ts())

    assert (disposition, reason) == ("delivered", None)
    assert events_mod._escalation_disposition(history, second) == ("delivered", None)


def test_out_of_set_class_is_recorded_as_refused(tmp_path: Path) -> None:
    """Treating unknown classes as deliverable would create a seventh escalation class."""
    candidate = _candidate("unknown-class", _written_at())
    candidate["data"]["escalation_class"] = "operational_failure"
    attempt = events_mod.append(tmp_path / "2026-08-26.jsonl", candidate)

    assert attempt["data"]["disposition"] == "refused"
    assert attempt["data"]["refusal_reason"] == "out_of_set_class"

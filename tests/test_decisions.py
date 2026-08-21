from datetime import datetime, timezone

import pytest

from consilient import events
from consilient.events import SCHEMA_VERSION, EventError, append, read, validate


MISSING = object()
EXPECTED_USER_ONLY = frozenset(
    {
        "spend",
        "credential",
        "preference",
        "outside_safety_floor",
        "beta_verdict",
        "external_exposure",
        "gate_or_spec_approval",
    }
)


def decision_event(**overrides):
    data = {
        "decision": "Use the standard-library implementation",
        "reasoning": "It is the smallest implementation that meets the requirement",
        "falsifier": "A required input cannot be represented",
        "reversal": {"kind": "command", "value": ["git", "revert", "abc1234"]},
    }
    data.update(overrides)
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "decision.autonomous",
        "actor": "consilient.dispatch",
        "data": data,
    }


@pytest.mark.parametrize("field", ("decision", "reasoning", "falsifier"))
@pytest.mark.parametrize("value", (MISSING, "", "   ", 7))
def test_autonomous_decision_requires_non_empty_text_fields(field, value):
    event = decision_event()
    if value is MISSING:
        event["data"].pop(field)
    else:
        event["data"][field] = value

    with pytest.raises(EventError, match=field):
        validate(event)


def test_autonomous_decision_requires_a_reversal():
    event = decision_event()
    event["data"].pop("reversal")

    with pytest.raises(EventError, match="reversal"):
        validate(event)


@pytest.mark.parametrize(
    "reversal",
    (
        None,
        [],
        {},
        {"kind": "command"},
        {"value": ["git", "revert", "abc1234"]},
        {"kind": [], "value": "undo the decision"},
        {"kind": "prose", "value": "undo the decision"},
    ),
)
def test_autonomous_decision_requires_a_typed_reversal_object(reversal):
    with pytest.raises(EventError, match="reversal"):
        validate(decision_event(reversal=reversal))


@pytest.mark.parametrize(
    ("kind", "value"),
    (
        ("revert", "not-a-sha"),
        ("revert", "ABC1234"),
        ("command", "git revert abc1234"),
        ("command", []),
        ("command", ["git", ""]),
        ("inverse", "restore"),
        ("inverse", "consilient.events.123restore"),
    ),
)
def test_each_reversal_kind_has_a_machine_checkable_shape(kind, value):
    with pytest.raises(EventError, match=kind):
        validate(decision_event(reversal={"kind": kind, "value": value}))


def test_autonomous_decision_rejects_exactly_the_user_only_classes():
    assert events.USER_ONLY == EXPECTED_USER_ONLY
    for decision_class in EXPECTED_USER_ONLY:
        with pytest.raises(EventError, match="reserved to the user"):
            validate(decision_event(**{"class": decision_class}))

    validate(decision_event(**{"class": "implementation_detail"}))


@pytest.mark.parametrize(
    "reversal",
    (
        {"kind": "revert", "value": "abc1234"},
        {"kind": "command", "value": ["git", "revert", "abc1234"]},
        {"kind": "inverse", "value": "consilient.events.validate"},
    ),
)
def test_fully_formed_autonomous_decision_round_trips_through_the_log(
    tmp_path, reversal
):
    event = decision_event(reversal=reversal)
    log = tmp_path / "decisions.jsonl"

    append(log, event)

    recorded, rejected = read(log)
    assert rejected == []
    assert [item.raw for item in recorded] == [event]

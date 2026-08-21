from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest

from consilient.events import SCHEMA_VERSION, EventError, bypassed, read_all
from consilient.work_items import comment, complete_item, open_item, validate


def work_event(kind, data, actor="agent-one"):
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": actor,
        "data": data,
    }


def work_script():
    spec = importlib.util.spec_from_file_location(
        "work_script", Path("scripts/work.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_open_comment_complete_round_trip_through_the_trajectory(tmp_path):
    log = tmp_path / "log"

    open_item(
        log,
        ticket="PM-1",
        accountable="orchestrator",
        actor="agent-one",
        text="Build the native work-item event surface",
    )
    comment(
        log,
        ticket="PM-1",
        actor="agent-two",
        evidence_class="Codex execution",
        text="The targeted check passed",
    )
    complete_item(log, ticket="PM-1", actor="agent-one")

    recorded, rejected = read_all(log)
    assert rejected == []
    assert [event.kind for event in recorded] == [
        "work_item.opened",
        "work_item.comment",
        "work_item.completed",
    ]
    assert [event.data["ticket"] for event in recorded] == ["PM-1"] * 3
    assert recorded[0].data["accountable"] == "orchestrator"
    assert recorded[1].data["evidence_class"] == "Codex execution"
    assert bypassed(log) == []


def test_comment_without_evidence_class_is_rejected():
    event = work_event("work_item.comment", {"ticket": "PM-1", "text": "Echo"})

    with pytest.raises(EventError, match="evidence_class"):
        validate(event)


@pytest.mark.parametrize(
    ("authority", "value"),
    (("human_decision", "approval"), ("human_verdict", "accept")),
)
def test_work_item_comment_cannot_carry_human_authority(authority, value):
    event = work_event(
        "work_item.comment",
        {
            "ticket": "PM-1",
            "text": "I approve",
            "evidence_class": "agent assertion",
            authority: value,
            "principal": "agent-one",
            "via": "cli",
        },
    )

    with pytest.raises(EventError, match=authority):
        validate(event)


def test_two_agent_comments_cannot_omit_evidence_class(tmp_path):
    log = tmp_path / "log"

    for actor in ("agent-one", "agent-two"):
        with pytest.raises(EventError, match="evidence_class"):
            comment(log, ticket="PM-1", actor=actor, text="Looks good")

    recorded, rejected = read_all(log)
    assert recorded == []
    assert rejected == []


@pytest.mark.parametrize(
    ("kind", "data"),
    (
        ("work_item.opened", {"accountable": "owner"}),
        ("work_item.comment", {"text": "note", "evidence_class": "execution"}),
        ("work_item.completed", {}),
    ),
)
def test_every_work_item_event_requires_a_ticket(kind, data):
    with pytest.raises(EventError, match="ticket"):
        validate(work_event(kind, data))


def test_open_requires_one_accountable_actor():
    with pytest.raises(EventError, match="accountable"):
        validate(work_event("work_item.opened", {"ticket": "PM-1"}))


def test_work_script_writes_each_operation_to_the_selected_log(tmp_path):
    module = work_script()
    log = tmp_path / "log"
    common = ["--log", str(log), "--ticket", "PM-2"]

    assert module.main(["open", *common, "--accountable", "owner", "A task"]) == 0
    assert (
        module.main(
            [
                "comment",
                *common,
                "--evidence-class",
                "Codex execution",
                "A note",
            ]
        )
        == 0
    )
    assert module.main(["complete", *common]) == 0

    recorded, rejected = read_all(log)
    assert rejected == []
    assert [event.actor for event in recorded] == ["consilient.work"] * 3
    assert [event.kind for event in recorded] == [
        "work_item.opened",
        "work_item.comment",
        "work_item.completed",
    ]

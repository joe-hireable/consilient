from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest

from consilient import events, work_items
from consilient.events import SCHEMA_VERSION, EventError, bypassed, read_all
from consilient.work_items import (
    COMMITTED,
    DISPATCH_CLAIM_SCHEMA,
    comment,
    complete_item,
    open_item,
    success_digest,
    validate,
)


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


def test_dispatch_claim_schema_is_recognised_on_append(tmp_path):
    log = tmp_path / "log"
    open_item(
        log,
        ticket="dispatch:schema-run",
        accountable="consilient.dispatch",
        extra={
            "item_schema": DISPATCH_CLAIM_SCHEMA,
            "run_id": "schema-run",
            "paths": ["src/"],
            "cwd": str(tmp_path),
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": "2026-09-22T12:00:00+00:00",
        },
    )
    recorded, rejected = read_all(log)
    assert rejected == []
    assert recorded[0].data["item_schema"] == DISPATCH_CLAIM_SCHEMA


def test_committed_event_requires_a_matching_digest():
    contract = {
        "commitment_id": "c-1",
        "revision": 1,
        "conversation_id": "conv",
        "source_turn_ids": ["t-1"],
        "source_turn_digest": "d" * 64,
        "request_text": "do work",
        "goal_text": "do work",
        "success_criteria": ["done"],
        "non_goals": [],
            "success_digest": success_digest(["done"], []),
        "incumbent": {
            "name": "bar",
            "source": "asserted",
            "retrieval_date": "2026-08-22",
            "search_digest": "0" * 64,
            "evidence_tag": "asserted",
            "delta": "n/a",
            "killing_check": "n/a",
        },
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "accountable": "owner",
        "composition": {"owner": "owner"},
        "assumptions": [],
        "autonomous_decision_refs": [],
        "reserved_decisions": [],
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": "a" * 64,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "mutation_scope": {"paths": ["src/"]},
        "budget_ref": "none",
        "expires_at": "2026-09-22T12:00:00+00:00",
        "question_count": 0,
        "commitment_digest": "0" * 64,
    }
    event = work_event(COMMITTED, contract)
    with pytest.raises(EventError, match="commitment_digest"):
        validate(event)


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


def test_material_choice_cannot_make_dependent_item_ready_without_prior_decision():
    source = work_event("evidence.observed", {"claim": "measured"})
    source["event_id"] = events.new_event_id()
    source_ref = {
        "event_id": source["event_id"],
        "event_kind": source["event"],
        "event_sha256": events.event_sha256(source),
    }
    decision = work_event(
        events.DECISION_KIND,
        {
            "decision_id": "decision-1",
            "operation_id": "operation-1",
            "ticket": "CHOICE-1",
            "owner": "owner",
            "actor": "agent-one",
            "record_level": "minimal",
            "decision": "Choose the standard-library path",
            "reasoning": "It satisfies the frozen contract",
            "falsifier": "The contract requires an unavailable primitive",
            "reversal": {
                "kind": "inverse",
                "value": "consilient.events.validate",
            },
            "alternatives": [
                {"option": "Add a dependency", "rejected_because": "It is unnecessary"}
            ],
            "evidence_refs": [source_ref],
            "acceptance_contract_digest": "a" * 64,
            "protocol": {
                "status": "not_warranted",
                "threshold": {
                    "version": "better-than-best.v1",
                    "later_reliance": "false",
                    "question_open": "true",
                    "wrong_costs_more": "true",
                },
            },
            "binding": {"kind": "material_choice"},
        },
    )
    decision["event_id"] = events.new_event_id()
    expected = events.event_sha256(decision)
    dependent = work_event(
        "work_item.opened",
        {
            "ticket": "DEPENDENT-1",
            "accountable": "owner",
            "decision_id": "decision-1",
        },
    )

    assert not work_items.decision_readiness([], dependent, expected)
    assert not work_items.decision_readiness([source, dependent, decision], dependent, expected)
    assert not work_items.decision_readiness(
        [source, decision, dependent], dependent, "0" * 64
    )
    assert work_items.decision_readiness(
        [source, decision, dependent], dependent, expected
    )

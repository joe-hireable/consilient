from datetime import datetime, timezone
import importlib.util
from pathlib import Path
from typing import Any

import pytest

from consilient import events, work_items
from consilient.events import SCHEMA_VERSION, EventError, bypassed, read_all
from consilient import projection
from consilient.work_items import (
    COMMITTED,
    DISPATCH_CLAIM_SCHEMA,
    STATE,
    STATE_GROUPS,
    WORK_MODEL_SCHEMA,
    WORK_STATE_DEFINITIONS,
    comment,
    complete_item,
    open_work_model_item,
    record_state,
    open_item,
    state_group,
    success_digest,
    validate,
)


def work_event(
    kind: str, data: dict[str, Any], actor: str = "agent-one"
) -> dict[str, Any]:
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


def test_every_native_state_declares_one_of_five_groups() -> None:
    groups = {definition["group"] for definition in WORK_STATE_DEFINITIONS.values()}
    assert groups == set(STATE_GROUPS)
    assert state_group("active") == "RUNNING"
    assert state_group("unfunded") == "NEEDS_YOU"
    assert state_group("blocked") == "WAITING"


def test_blocked_overlay_requires_a_named_reason() -> None:
    event = work_event(
        STATE,
        {"ticket": "WM-1", "state": "active", "is_blocked": True},
    )
    with pytest.raises(EventError, match="blocked_reason"):
        validate(event)


def test_active_and_blocked_can_coexist_with_a_reason(tmp_path: Path) -> None:
    log = tmp_path / "log"
    open_work_model_item(
        log,
        ticket="WM-1",
        accountable="owner",
        state="ready",
    )
    record_state(
        log,
        ticket="WM-1",
        state="active",
        is_blocked=True,
        blocked_reason="waiting on stream-2 handoff",
    )
    recorded, rejected = read_all(log)
    assert rejected == []
    assert recorded[-1].data["is_blocked"] is True
    assert recorded[-1].data["blocked_reason"] == "waiting on stream-2 handoff"


def test_informs_edge_must_be_scored_on_close(tmp_path: Path) -> None:
    log = tmp_path / "log"
    open_work_model_item(
        log,
        ticket="WM-2",
        accountable="owner",
        state="ready",
        informs=[
            {
                "target_ticket": "WM-1",
                "effect": "duration",
                "sign": -1,
                "magnitude_estimate": 0.2,
                "expires_at": "2026-09-22T12:00:00+00:00",
            }
        ],
    )
    record_state(log, ticket="WM-2", state="active")
    with pytest.raises(EventError, match="inform_scores"):
        complete_item(log, ticket="WM-2")


def test_informs_edge_scores_on_close(tmp_path: Path) -> None:
    log = tmp_path / "log"
    open_work_model_item(
        log,
        ticket="WM-3",
        accountable="owner",
        state="ready",
        informs=[
            {
                "target_ticket": "WM-0",
                "effect": "quality",
                "sign": 1,
                "magnitude_estimate": 0.1,
                "expires_at": "2026-09-22T12:00:00+00:00",
            }
        ],
    )
    record_state(log, ticket="WM-3", state="active")
    complete_item(
        log,
        ticket="WM-3",
        extra={
            "inform_scores": [
                {
                    "target_ticket": "WM-0",
                    "effect": "quality",
                    "observed_sign": 1,
                    "observed_magnitude": 0.08,
                }
            ]
        },
    )
    recorded, rejected = read_all(log)
    assert rejected == []
    assert recorded[-1].data["inform_scores"][0]["observed_magnitude"] == 0.08


def test_projection_emits_five_groups(tmp_path: Path) -> None:
    log = tmp_path / "log"
    open_work_model_item(log, ticket="WAIT", accountable="owner", state="blocked")
    open_work_model_item(log, ticket="RUN", accountable="owner", state="ready")
    record_state(log, ticket="RUN", state="active")
    open_work_model_item(log, ticket="NEED", accountable="owner", state="unfunded")
    open_work_model_item(log, ticket="DONE", accountable="owner", state="closed")
    open_work_model_item(log, ticket="DEAD", accountable="owner", state="failed")

    db = tmp_path / "state.sqlite"
    conn = projection.build(log, db)
    groups = projection.work_item_groups(conn)
    conn.close()

    assert set(groups) == set(STATE_GROUPS)
    assert [item["ticket"] for item in groups["WAITING"]] == ["WAIT"]
    assert [item["ticket"] for item in groups["RUNNING"]] == ["RUN"]
    assert [item["ticket"] for item in groups["NEEDS_YOU"]] == ["NEED"]
    assert [item["ticket"] for item in groups["DONE"]] == ["DONE"]
    assert [item["ticket"] for item in groups["DEAD"]] == ["DEAD"]

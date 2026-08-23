"""C01 — conversation turn identity and committed-request contract."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events, work_items
from consilient.events import EventError, SCHEMA_VERSION, append, read_all

TS = "2026-08-23T12:00:00+00:00"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
CONVERSATION_ID = "conv-001"
TURN_ID = "turn-001"
COMMITMENT_ID = "commit-001"
SECRET_VALUE = "sk-live-SECRET-FIXTURE-VALUE"
REDACTION_MARKER = "[REDACTED:broker]"


def _turn_event(
    *,
    turn_id: str = TURN_ID,
    role: str = "user",
    text: str = "Add conversation commitments",
    authenticated: bool = True,
    redactions: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "conversation_id": CONVERSATION_ID,
        "turn_id": turn_id,
        "root_request_turn_id": turn_id,
        "role": role,
        "text": text,
        "transport": {"authenticated": authenticated, "channel": "chat"},
    }
    if redactions is not None:
        data["redactions"] = redactions
    return {
        "v": SCHEMA_VERSION,
        "ts": TS,
        "event": work_items.TURN,
        "actor": "consilient.intake",
        "data": data,
    }


def _minimal_contract(**over: object) -> dict[str, object]:
    success_criteria = ["tests/test_conversation.py passes"]
    non_goals = ["no scope creep"]
    contract: dict[str, object] = {
        "commitment_id": COMMITMENT_ID,
        "revision": 1,
        "conversation_id": CONVERSATION_ID,
        "source_turn_ids": [TURN_ID],
        "request_text": "Add conversation commitments",
        "goal_text": "Record immutable request commitments",
        "success_criteria": success_criteria,
        "non_goals": non_goals,
        "success_digest": work_items.success_digest(success_criteria, non_goals),
        "incumbent": {
            "name": "scripts/dispatch.py",
            "source": "measured",
            "retrieval_date": "2026-08-22",
            "search_digest": "0" * 64,
            "evidence_tag": "measured",
            "delta": "structured commitment before dispatch",
            "killing_check": "matched trial on commitment errors",
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
        "mutation_scope": {"paths": ["src/consilient/"]},
        "budget_ref": "none",
        "expires_at": "2026-09-22T12:00:00+00:00",
        "question_count": 0,
    }
    contract.update(over)
    contract["source_turn_digest"] = work_items.source_turn_digest(
        str(contract["conversation_id"]),
        list(contract["source_turn_ids"]),
        {TURN_ID: "Add conversation commitments"},
    )
    contract["commitment_digest"] = work_items.commitment_digest(contract)
    return contract


def _committed_event(contract: dict[str, object] | None = None) -> dict[str, object]:
    data = contract or _minimal_contract()
    return {
        "v": SCHEMA_VERSION,
        "ts": _now(),
        "event": work_items.COMMITTED,
        "actor": "consilient.intake",
        "data": data,
    }


def test_turn_identity_fields_are_required_by_the_central_writer():
    event = _turn_event()
    del event["data"]["turn_id"]

    with pytest.raises(EventError, match="turn_id"):
        events.validate(event)


def test_sealed_turn_preserves_sanitised_text_and_redacts_secrets(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text=f"deploy with token {REDACTION_MARKER}",
        transport_authenticated=True,
        redactions=[{"kind": "broker_reference", "reference": "broker-001"}],
    )

    recorded, rejected = read_all(log)
    assert rejected == []
    assert recorded[0].data["text"] == f"deploy with token {REDACTION_MARKER}"
    trajectory = json.dumps(recorded[0].raw)
    assert SECRET_VALUE not in trajectory
    assert hashlib.sha256(SECRET_VALUE.encode()).hexdigest() not in trajectory


def test_commitment_digest_is_deterministic_and_changes_with_contract_edits():
    contract = _minimal_contract()
    first = work_items.commitment_digest(contract)
    shuffled = work_items.commitment_digest(
        dict(sorted(contract.items(), reverse=True))
    )
    assert first == shuffled

    changed = dict(contract)
    changed["non_goals"] = ["no scope creep", "no drive-by refactors"]
    changed["success_digest"] = work_items.success_digest(
        list(changed["success_criteria"]), list(changed["non_goals"])
    )
    assert work_items.commitment_digest(changed) != first


def test_generic_append_and_helper_agree_on_commitment_validation(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="Add conversation commitments",
    )
    contract = _minimal_contract()

    helper_event = work_items.commit_request(log, contract)
    assert helper_event["data"]["commitment_digest"] == contract["commitment_digest"]

    bad = _committed_event(dict(contract, commitment_digest="0" * 64))
    with pytest.raises(EventError, match="commitment_digest"):
        append(log / f"{_now()[:10]}.jsonl", bad)


def test_duplicate_commitment_revision_is_refused(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="Add conversation commitments",
    )
    contract = _minimal_contract()
    work_items.commit_request(log, contract)

    with pytest.raises(EventError, match="revision"):
        work_items.commit_request(log, contract)


def test_superseding_revision_must_name_the_immediate_prior_digest(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="Add conversation commitments",
    )
    first = work_items.commit_request(log, _minimal_contract())

    stale = _minimal_contract(
        revision=2,
        supersedes_commitment_digest="f" * 64,
        goal_text="changed goal",
    )
    with pytest.raises(EventError, match="supersedes_commitment_digest"):
        work_items.commit_request(log, stale)

    successor = _minimal_contract(
        revision=2,
        supersedes_commitment_digest=first["data"]["commitment_digest"],
        goal_text="changed goal",
    )
    work_items.commit_request(log, successor)


def test_unauthenticated_chat_may_commit_an_unprotected_request(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="read the docs",
        transport_authenticated=False,
    )
    work_items.commit_request(log, _minimal_contract(authority_ref={"kind": "unprotected"}))


def test_unauthenticated_chat_cannot_author_a_protected_commitment(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="publish the repo",
        transport_authenticated=False,
    )
    protected = _minimal_contract(
        authority_ref={"kind": "principal_required", "reserved": ["external_exposure"]},
        reserved_decisions=["external_exposure"],
    )
    with pytest.raises(EventError, match="authenticated"):
        work_items.commit_request(log, protected)


def test_legacy_dispatch_claim_rows_remain_readable(tmp_path):
    legacy = {
        "v": SCHEMA_VERSION,
        "ts": TS,
        "event": work_items.OPENED,
        "actor": "consilient.dispatch",
        "data": {
            "ticket": "dispatch:legacy",
            "accountable": "consilient.dispatch",
            "run_id": "legacy-run",
            "paths": ["src/"],
            "cwd": str(tmp_path),
            "opened_at": TS,
            "expires_at": "2026-09-22T12:00:00+00:00",
        },
    }
    path = tmp_path / f"{TS[:10]}.jsonl"
    path.write_text(json.dumps(legacy, sort_keys=True) + "\n", encoding="utf-8")

    recorded, rejected = read_all(tmp_path)
    assert rejected == []
    assert recorded[0].kind == work_items.OPENED


def test_dispatch_claim_completion_cannot_pose_as_native_task_closure(tmp_path):
    log = tmp_path / "log"
    work_items.open_item(
        log,
        ticket="dispatch:run-1",
        accountable="consilient.dispatch",
        extra={
            "item_schema": work_items.DISPATCH_CLAIM_SCHEMA,
            "run_id": "run-1",
            "paths": ["src/"],
            "cwd": str(tmp_path),
            "opened_at": TS,
            "expires_at": "2026-09-22T12:00:00+00:00",
        },
    )
    event = {
        "v": SCHEMA_VERSION,
        "ts": _now(),
        "event": work_items.COMPLETED,
        "actor": "consilient.dispatch",
        "data": {
            "ticket": "dispatch:run-1",
            "plan_digest": "b" * 64,
            "artefacts": [{"locator": "x", "sha256": "c" * 64}],
        },
    }
    with pytest.raises(EventError, match="dispatch-claim"):
        append(log / f"{_now()[:10]}.jsonl", event)


def _contend_commitment(log_dir: str, results) -> None:
    log = Path(log_dir)
    try:
        work_items.commit_request(
            log,
            _minimal_contract(),
        )
        results.put("admitted")
    except EventError:
        results.put("refused")


def test_concurrent_duplicate_commitment_revisions_admit_exactly_one(tmp_path):
    log = tmp_path / "log"
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="race",
    )
    ctx = multiprocessing.get_context("spawn")
    results = ctx.Queue()
    workers = [
        ctx.Process(target=_contend_commitment, args=(str(log), results))
        for _ in range(2)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=30)
        assert worker.exitcode == 0

    outcomes = sorted(results.get(timeout=5) for _ in workers)
    assert outcomes == ["admitted", "refused"]
    recorded, rejected = read_all(log)
    assert rejected == []
    assert sum(event.kind == work_items.COMMITTED for event in recorded) == 1

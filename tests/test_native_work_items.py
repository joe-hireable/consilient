from __future__ import annotations

from datetime import datetime, timezone

import pytest

from consilient import projection, work_items
from consilient.events import EventError, read_all


TS = datetime.now(timezone.utc).isoformat()
DIGEST = "a" * 64
HANDOFF = "b" * 64


def _commitment() -> dict[str, object]:
    data: dict[str, object] = {
        "commitment_id": "commit-1",
        "revision": 1,
        "conversation_id": "conversation-1",
        "source_turn_ids": ["turn-1"],
        "source_turn_digest": DIGEST,
        "request_text": "Build the native item substrate",
        "goal_text": "Build the native item substrate",
        "success_criteria": ["native state replays"],
        "non_goals": [],
        "success_digest": work_items.success_digest(["native state replays"], []),
        "incumbent": {
            "name": "event replay",
            "source": "repository",
            "retrieval_date": "2026-08-24",
            "search_digest": DIGEST,
            "evidence_tag": "measured",
            "delta": "native rows",
            "killing_check": "replay mismatch",
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
                "digest": DIGEST,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "mutation_scope": {"paths": ["src/"]},
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
        "question_count": 0,
    }
    data["commitment_digest"] = work_items.commitment_digest(data)
    return data


def _stream(stream_id: str, dependencies: list[dict[str, object]]) -> dict[str, object]:
    return {
        "stream_id": stream_id,
        "deliverable": f"{stream_id} deliverable",
        "accountable": "owner",
        "owned_paths": [f"src/{stream_id}.py"],
        "dependencies": dependencies,
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "handoff_contract": {"schema": "git-diff", "digest": HANDOFF},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": DIGEST,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "composition": {"owner": "owner"},
        "checkpoint_required": True,
        "integration": stream_id == "integration",
    }


def _plan() -> dict[str, object]:
    commitment = _commitment()
    data: dict[str, object] = {
        "plan_id": "plan-1",
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {"line_count": 0, "prefix_digest": DIGEST},
        "streams": [
            _stream("source", []),
            _stream(
                "integration",
                [
                    {
                        "stream_id": "source",
                        "revision": 1,
                        "handoff_contract_digest": HANDOFF,
                    }
                ],
            ),
        ],
        "integration_owner": "owner",
        "estimate_inputs": {
            "duration_lower_s": 1,
            "duration_upper_s": 60,
            "derivation": "bounded slice",
            "evidence_class": "asserted",
        },
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
    }
    data["plan_digest"] = work_items.plan_digest(data)
    return data


def _native_item(plan: dict[str, object], stream_id: str) -> dict[str, object]:
    stream = next(item for item in plan["streams"] if item["stream_id"] == stream_id)
    dependencies = [
        {
            "ticket": f"native:{dependency['stream_id']}",
            "revision": dependency["revision"],
            "handoff_contract_digest": dependency["handoff_contract_digest"],
        }
        for dependency in stream["dependencies"]
    ]
    return {
        "ticket": f"native:{stream_id}",
        "revision": 1,
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "stream_id": stream_id,
        "goal_text": f"Deliver {stream_id}",
        "success_digest": DIGEST,
        "incumbent": _commitment()["incumbent"],
        "deliverable_contract": stream["deliverable_contract"],
        "accountable": "owner",
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": stream["verifier_contracts"],
        "dependencies": dependencies,
        "owned_paths": stream["owned_paths"],
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
        "exposure_contract": {
            "key": "goal:code",
            "epsilon": 0.1,
            "rule": "frozen",
            "beta_version": "unestimated",
            "n_max": 0,
        },
        "composition": {"owner": "owner"},
    }


def _seed_plan(log, plan: dict[str, object]) -> None:
    work_items.commit_request(log, _commitment(), ts=TS)
    work_items.freeze_plan(log, plan, ts=TS)


def test_native_open_requires_matching_frozen_plan_and_stream(tmp_path):
    """Mutating plan/stream identity in a native item must be refused."""
    log = tmp_path / "log"
    plan = _plan()
    _seed_plan(log, plan)
    item = _native_item(plan, "source")

    work_items.open_native_item(log, item, ts=TS)
    with pytest.raises(EventError, match="revision"):
        work_items.open_native_item(log, item, ts=TS)

    wrong_stream = dict(item, ticket="native:missing", stream_id="missing")
    with pytest.raises(EventError, match="stream"):
        work_items.open_native_item(log, wrong_stream, ts=TS)


def test_native_projection_is_deterministic_and_orders_blockers(tmp_path):
    """Removing dependency/paused blockers must change projected native rows."""
    log = tmp_path / "log"
    plan = _plan()
    _seed_plan(log, plan)
    work_items.open_native_item(log, _native_item(plan, "source"), ts=TS)
    work_items.open_native_item(log, _native_item(plan, "integration"), ts=TS)
    work_items.pause_native_item(
        log,
        ticket="native:integration",
        revision=1,
        plan_digest=plan["plan_digest"],
        cause="commitment_paused",
        ts=TS,
    )

    db = tmp_path / "state.db"
    first = projection.build(log, db)
    rows = projection.native_work_item_rows(first)
    assert rows == [
        {
            "ticket": "native:integration",
            "revision": 1,
            "state": "blocked",
            "blockers": ["commitment_paused", "dependency:native:source@1"],
        },
        {
            "ticket": "native:source",
            "revision": 1,
            "state": "ready",
            "blockers": [],
        },
    ]
    before_delete = projection.state_digest(first)
    first.close()
    db.unlink()
    rebuilt = projection.build(log, db)
    assert projection.native_work_item_rows(rebuilt) == rows
    assert projection.state_digest(rebuilt) == before_delete


def test_native_attempt_is_active_but_legacy_completion_never_changes_native_state(
    tmp_path,
):
    """Removing native attempt filtering would let legacy claim rows corrupt native state."""
    log = tmp_path / "log"
    plan = _plan()
    _seed_plan(log, plan)
    item = _native_item(plan, "source")
    opened = work_items.open_native_item(log, item, ts=TS)
    work_items.record_native_attempt(
        log,
        ticket="native:source",
        revision=1,
        plan_digest=plan["plan_digest"],
        attempt_id="attempt-1",
        run_id="run-1",
        claimed_paths=["src/source.py"],
        opened_at=TS,
        expires_at="2026-08-24T11:30:00+00:00",
        harness="codex",
        model="gpt",
        family="openai",
        pool="included",
        capability_context_digest=DIGEST,
        candidate_ordinal=1,
        exposure_state="pre_verifier",
        predecessor_bindings=[],
        ts=TS,
    )
    work_items.comment(
        log,
        ticket="native:source",
        text="Done according to the author",
        evidence_class="assertion",
    )
    work_items.complete_item(log, ticket="native:source", actor="owner")
    work_items.open_item(
        log,
        ticket="dispatch:legacy",
        accountable="consilient.dispatch",
        extra={
            "item_schema": work_items.DISPATCH_CLAIM_SCHEMA,
            "run_id": "legacy",
            "paths": ["src/legacy.py"],
            "cwd": str(tmp_path),
            "opened_at": TS,
            "expires_at": "2026-08-24T11:30:00+00:00",
        },
    )
    work_items.complete_item(log, ticket="dispatch:legacy")

    conn = projection.build(log, tmp_path / "state.db")
    assert projection.native_work_item_rows(conn) == [
        {
            "ticket": "native:source",
            "revision": 1,
            "state": "active",
            "blockers": [],
        }
    ]
    recorded, rejected = read_all(log)
    assert rejected == []
    assert opened["data"]["ticket"] == "native:source"

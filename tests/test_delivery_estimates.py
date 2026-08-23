"""D01 — immutable delivery estimate and reforecast."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import events, projection, work_items
from consilient.events import EventError, SCHEMA_VERSION, append, append_transaction

CONVERSATION_ID = "conv-est-001"
TURN_ID = "turn-est-001"
COMMITMENT_ID = "commit-est-001"
PLAN_ID = "plan-est-001"
DELIVERY_ID = "delivery-est-001"
COHORT = {
    "artefact_kind": "code",
    "verifier_contract_digest": "a" * 64,
    "size_band": "small",
    "route_capability_class": "cursor-composer",
}
RESOURCE_SNAPSHOT = "b" * 64


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _issued() -> datetime:
    return datetime.now(timezone.utc)


def _event(kind: str, data: dict[str, object], *, ts: str | None = None) -> dict[str, object]:
    stamp = ts or _now()
    return {
        "v": SCHEMA_VERSION,
        "ts": stamp,
        "event": kind,
        "actor": events.DELIVERY_ACTOR,
        "data": data,
    }


def _log_file(log: Path) -> Path:
    files = sorted(log.glob("*.jsonl"))
    if files:
        return files[0]
    stamp = _now()
    return log / f"{stamp[:10]}.jsonl"


def _minimal_commitment(**over: object) -> dict[str, object]:
    success_criteria = ["tests pass"]
    non_goals: list[str] = []
    contract: dict[str, object] = {
        "commitment_id": COMMITMENT_ID,
        "revision": 1,
        "conversation_id": CONVERSATION_ID,
        "source_turn_ids": [TURN_ID],
        "request_text": "ship delivery estimate",
        "goal_text": "freeze estimate before work",
        "success_criteria": success_criteria,
        "non_goals": non_goals,
        "success_digest": work_items.success_digest(success_criteria, non_goals),
        "incumbent": {
            "name": "manual dispatch",
            "source": "measured",
            "retrieval_date": "2026-08-22",
            "search_digest": "0" * 64,
            "evidence_tag": "measured",
            "delta": "dated window before claims",
            "killing_check": "estimate ordering",
        },
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "accountable": "delivery-owner",
        "composition": {"owner": "delivery-owner"},
        "assumptions": [],
        "autonomous_decision_refs": [],
        "reserved_decisions": [],
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": COHORT["verifier_contract_digest"],
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
        {TURN_ID: "ship delivery estimate"},
    )
    contract["commitment_digest"] = work_items.commitment_digest(contract)
    return contract


def _stream(*, stream_id: str = "S1", integration: bool = True) -> dict[str, object]:
    return {
        "stream_id": stream_id,
        "deliverable": "implement estimate",
        "accountable": "owner-a",
        "owned_paths": ["src/consilient/events.py"],
        "dependencies": [],
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "handoff_contract": {
            "schema": "git-diff",
            "digest": work_items.handoff_contract_digest("git-diff", ["repository"]),
        },
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": COHORT["verifier_contract_digest"],
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "composition": {"owner": "owner-a"},
        "checkpoint_required": True,
        "integration": integration,
    }


def _seed_plan(log: Path) -> dict[str, object]:
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="ship delivery estimate",
    )
    commitment = work_items.commit_request(log, _minimal_commitment())["data"]
    line_count = sum(1 for _ in _log_file(log).open(encoding="utf-8"))
    plan: dict[str, object] = {
        "plan_id": PLAN_ID,
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {
            "line_count": line_count,
            "prefix_digest": events.prefix_digest(_log_file(log), line_count),
        },
        "streams": [_stream()],
        "estimate_inputs": {
            "duration_lower_s": 120,
            "duration_upper_s": 900,
            "derivation": "cold start slice budget",
            "evidence_class": "asserted: low evidence",
        },
        "budget_ref": commitment["budget_ref"],
        "expires_at": commitment["expires_at"],
        "plan_digest": "",
    }
    plan["plan_digest"] = work_items.plan_digest(plan)
    work_items.freeze_plan(log, plan)
    return plan


def _analogue_outcome(
    log: Path,
    *,
    duration_s: float,
    timed_out: bool = False,
    status: str = "ok",
    ts: str = "2026-08-22T10:00:00+00:00",
) -> dict[str, object]:
    stamp = _now()
    payload = _event(
        "dispatch.outcome",
        {
            "run_id": f"run-{duration_s}",
            "task": "prior delivery",
            "cwd": "/tmp",
            "harness": "cursor",
            "family": "cursor",
            "pool": "cursor-models",
            "status": status,
            "reason": "done",
            "exit_code": 0 if status == "ok" else 1,
            "artefact_bytes": 10,
            "diff_bytes": 5,
            "timed_out": timed_out,
            "duration_s": duration_s,
            "command": ["echo"],
            "supervised": True,
            "estimate_cohort": dict(COHORT),
            "occurred_at": ts,
        },
        ts=stamp,
    )
    return append(_log_file(log), payload)


def _build_estimate(
    plan: dict[str, object],
    *,
    prefix: tuple[events.Event, ...] = (),
    revision: int = 0,
    predecessor: dict[str, object] | None = None,
    cause: str | None = None,
    earliest_at: str | None = None,
    latest_at: str | None = None,
    issued_at: datetime | None = None,
) -> dict[str, object]:
    when = issued_at or _issued()
    derived = events.derive_delivery_estimate(
        prefix,
        plan=plan,
        delivery_id=DELIVERY_ID,
        issued_at=when,
        cohort_key=COHORT,
        resource_snapshot_digest=RESOURCE_SNAPSHOT,
        checkpoint_interval_s=300,
        recovery_allowance_s=600,
    )
    data = dict(derived)
    data["revision"] = revision
    if revision == 0:
        data["predecessor_estimate_id"] = None
        data["cause"] = None
        data["notice_preceded_upper_bound"] = False
    else:
        assert predecessor is not None
        data["predecessor_estimate_id"] = predecessor["estimate_id"]
        data["original_estimate_id"] = predecessor["original_estimate_id"]
        data["cause"] = cause
        data["notice_preceded_upper_bound"] = True
    if earliest_at is not None:
        data["earliest_at"] = earliest_at
    if latest_at is not None:
        data["latest_at"] = latest_at
    data["estimate_digest"] = events.estimate_digest(data)
    return data


def _append_estimate(
    log: Path,
    plan: dict[str, object],
    *,
    prefix: tuple[events.Event, ...] = (),
    revision: int = 0,
    predecessor: dict[str, object] | None = None,
    cause: str | None = None,
    earliest_at: str | None = None,
    latest_at: str | None = None,
) -> dict[str, object]:
    data = _build_estimate(
        plan,
        prefix=prefix,
        revision=revision,
        predecessor=predecessor,
        cause=cause,
        earliest_at=earliest_at,
        latest_at=latest_at,
    )
    return append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, data))


def _delivery_claim(log: Path, plan: dict[str, object]) -> dict[str, object]:
    return _event(
        work_items.OPENED,
        {
            "ticket": "native-S1",
            "accountable": "owner-a",
            "delivery_id": DELIVERY_ID,
            "commitment_digest": plan["commitment_digest"],
            "plan_digest": plan["plan_digest"],
        },
        ts=_now(),
    )


def test_estimate_revision_zero_records_required_fields(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    recorded = _append_estimate(log, plan)

    data = recorded["data"]
    assert data["delivery_id"] == DELIVERY_ID
    assert data["revision"] == 0
    assert data["commitment_digest"] == plan["commitment_digest"]
    assert data["plan_digest"] == plan["plan_digest"]
    assert data["stream_bounds"]
    assert data["resource_snapshot_digest"] == RESOURCE_SNAPSHOT
    assert data["checkpoint_interval_s"] == 300
    assert data["recovery_allowance_s"] == 600
    assert data["estimate_digest"] == events.estimate_digest(data)


def test_estimate_digest_is_deterministic(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    fixed_id = "11111111-1111-4111-8111-111111111111"
    when = _issued()
    first = _build_estimate(plan, issued_at=when)
    second = _build_estimate(plan, issued_at=when)
    first["estimate_id"] = fixed_id
    second["estimate_id"] = fixed_id
    first["original_estimate_id"] = fixed_id
    second["original_estimate_id"] = fixed_id
    first["estimate_digest"] = events.estimate_digest(first)
    second["estimate_digest"] = events.estimate_digest(second)
    assert events.estimate_digest(first) == events.estimate_digest(second)


def test_five_comparable_outcomes_use_percentile_range(tmp_path):
    log = tmp_path / "log"
    durations = [100.0, 200.0, 300.0, 400.0, 500.0]
    for duration in durations:
        _analogue_outcome(log, duration_s=duration)
    plan = _seed_plan(log)
    prefix = tuple(events.read_all(log)[0])
    issued = _issued()
    derived = events.derive_delivery_estimate(
        prefix,
        plan=plan,
        delivery_id=DELIVERY_ID,
        issued_at=issued,
        cohort_key=COHORT,
        resource_snapshot_digest=RESOURCE_SNAPSHOT,
        checkpoint_interval_s=300,
        recovery_allowance_s=600,
    )

    assert derived["sample_size"] == 5
    assert derived["method"] == "comparable_deliveries_percentile"
    assert derived["evidence_class"] == "measured"
    sorted_durations = sorted(durations)
    lower_index = max(0, min(4, math.ceil(0.10 * 5) - 1))
    upper_index = max(0, min(4, math.ceil(0.90 * 5) - 1))
    expected_lower = issued + timedelta(seconds=sorted_durations[lower_index])
    expected_upper = issued + timedelta(seconds=sorted_durations[upper_index])
    assert derived["earliest_at"] == expected_lower.isoformat()
    assert derived["latest_at"] == expected_upper.isoformat()
    assert len(derived["analogue_ids"]) == 5


def test_fewer_than_five_uses_cold_start_fallback(tmp_path):
    log = tmp_path / "log"
    for duration in (100.0, 200.0, 300.0):
        _analogue_outcome(log, duration_s=duration)
    plan = _seed_plan(log)
    prefix = tuple(events.read_all(log)[0])
    issued = _issued()
    derived = events.derive_delivery_estimate(
        prefix,
        plan=plan,
        delivery_id=DELIVERY_ID,
        issued_at=issued,
        cohort_key=COHORT,
        resource_snapshot_digest=RESOURCE_SNAPSHOT,
        checkpoint_interval_s=300,
        recovery_allowance_s=600,
    )

    assert derived["sample_size"] == 3
    assert derived["method"] == "cold_start_slice_schedule"
    assert derived["evidence_class"] == "asserted: low evidence"
    assert derived["earliest_at"] == (issued + timedelta(seconds=120)).isoformat()
    assert derived["latest_at"] == (issued + timedelta(seconds=900)).isoformat()


def test_censored_timeout_raises_upper_bound(tmp_path):
    log = tmp_path / "log"
    for duration in (100.0, 200.0, 300.0, 400.0, 500.0):
        _analogue_outcome(log, duration_s=duration)
    _analogue_outcome(log, duration_s=250.0, timed_out=True, status="error")
    plan = _seed_plan(log)
    prefix = tuple(events.read_all(log)[0])
    issued = _issued()
    derived = events.derive_delivery_estimate(
        prefix,
        plan=plan,
        delivery_id=DELIVERY_ID,
        issued_at=issued,
        cohort_key=COHORT,
        resource_snapshot_digest=RESOURCE_SNAPSHOT,
        checkpoint_interval_s=300,
        recovery_allowance_s=600,
    )

    censored_floor = issued + timedelta(seconds=250.0 + 600)
    assert datetime.fromisoformat(derived["latest_at"]) >= censored_floor
    assert len(derived["analogue_ids"]) == 6


def test_reforecast_appends_new_revision_preserves_original(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    original = _append_estimate(log, plan)["data"]
    prefix = tuple(events.read_all(log)[0])
    successor = _append_estimate(
        log,
        plan,
        prefix=prefix,
        revision=1,
        predecessor=original,
        cause="route_change",
        earliest_at=original["earliest_at"],
        latest_at=(datetime.fromisoformat(original["latest_at"]) + timedelta(hours=2)).isoformat(),
    )["data"]

    assert successor["revision"] == 1
    assert successor["predecessor_estimate_id"] == original["estimate_id"]
    assert successor["original_estimate_id"] == original["estimate_id"]
    assert successor["cause"] == "route_change"
    chain = projection.delivery_estimate_chain(
        projection.build(log, tmp_path / "state.db"), DELIVERY_ID
    )
    assert len(chain) == 2
    assert chain[0]["revision"] == 0
    assert chain[0]["latest_at"] == original["latest_at"]
    assert chain[1]["revision"] == 1


def test_reforecast_requires_cause_and_new_range(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    original = _append_estimate(log, plan)["data"]
    prefix = tuple(events.read_all(log)[0])
    bad = _build_estimate(
        plan,
        prefix=prefix,
        revision=1,
        predecessor=original,
        cause=None,
        earliest_at=original["earliest_at"],
        latest_at=original["latest_at"],
    )
    with pytest.raises(EventError, match="cause"):
        append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, bad))


def test_reforecast_refused_after_upper_bound_breach(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    original = _append_estimate(log, plan)["data"]
    prefix = tuple(events.read_all(log)[0])
    breach_ts = (datetime.fromisoformat(original["latest_at"]) + timedelta(minutes=5)).isoformat()
    successor = _build_estimate(
        plan,
        prefix=prefix,
        revision=1,
        predecessor=original,
        cause="estimate_error",
        earliest_at=original["earliest_at"],
        latest_at=(datetime.fromisoformat(original["latest_at"]) + timedelta(hours=2)).isoformat(),
    )
    successor["issued_at"] = breach_ts
    successor["estimate_digest"] = events.estimate_digest(successor)
    with pytest.raises(EventError, match="pre-breach"):
        append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, successor))


def test_silent_overwrite_of_revision_zero_refused(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    _append_estimate(log, plan)
    prefix = tuple(events.read_all(log)[0])
    duplicate = _build_estimate(plan, prefix=prefix, revision=0)
    with pytest.raises(EventError, match="revision zero"):
        append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, duplicate))


def test_outcome_aware_cohort_selection_refused(tmp_path):
    log = tmp_path / "log"
    for duration in (100.0, 200.0, 300.0, 400.0, 500.0):
        _analogue_outcome(log, duration_s=duration)
    plan = _seed_plan(log)
    prefix = tuple(events.read_all(log)[0])
    issued = _issued()
    derived = events.derive_delivery_estimate(
        prefix,
        plan=plan,
        delivery_id=DELIVERY_ID,
        issued_at=issued,
        cohort_key=COHORT,
        resource_snapshot_digest=RESOURCE_SNAPSHOT,
        checkpoint_interval_s=300,
        recovery_allowance_s=600,
    )
    derived["analogue_ids"] = derived["analogue_ids"][:3]
    derived["estimate_digest"] = events.estimate_digest(derived)
    with pytest.raises(EventError, match="outcome-aware"):
        append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, derived))


def test_claim_before_estimate_refused(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    with pytest.raises(EventError, match="delivery.estimate revision zero"):
        append_transaction(log, [_delivery_claim(log, plan)], lambda _p, _r, _c: None)


def test_claim_with_digest_mismatch_refused(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    estimate = _build_estimate(plan)
    estimate["estimate_digest"] = "0" * 64
    with pytest.raises(EventError, match="estimate_digest"):
        append(_log_file(log), _event(events.DELIVERY_ESTIMATE_KIND, estimate))


def test_projection_rebuild_is_deterministic(tmp_path):
    log = tmp_path / "log"
    plan = _seed_plan(log)
    _append_estimate(log, plan)
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    first = projection.build(log, db_a)
    second = projection.build(log, db_b)
    assert projection.state_digest(first) == projection.state_digest(second)
    chain = projection.delivery_estimate_chain(first, DELIVERY_ID)
    assert chain[0]["delivery_id"] == DELIVERY_ID
    first.close()
    second.close()

"""D01 — the estimate is frozen before the work starts, and may only be superseded on
the record.

Revision zero must carry its required fields: the delivery id, the commitment and plan
digests it is bound to, the stream bounds, the resource snapshot digest, the checkpoint
interval and recovery allowance, and a digest recomputable from the data itself. That
digest must be deterministic — two derivations at the same instant, with the identifiers
held equal, agree — because everything downstream is a digest comparison.

A reforecast appends rather than overwrites: the successor names its predecessor and the
original, states its cause, and the projected chain still shows revision zero with its
original upper bound intact. The refusals are the substance of the invariant and each
pins one way the record could be quietly rewritten — a reforecast with no cause and no
new range; a reforecast issued after the upper bound has already been breached, which
must be given pre-breach or not at all; a second revision zero silently overwriting the
first; an estimate whose analogue set has been trimmed after derivation, which is
outcome-aware cohort selection and is refused; a delivery claim opened before revision
zero exists; and an estimate whose digest does not match its data.

The last test closes the loop: two independent rebuilds of the projection from the same
log agree on the state digest, so the chain above is a property of the log rather than
of the database that read it."""

from datetime import datetime, timedelta
from pathlib import Path
import pytest
from consilient import events, projection, work_items
from consilient.events import EventError, append, append_transaction
from delivery_estimate_helpers import (
    COHORT,
    DELIVERY_ID,
    RESOURCE_SNAPSHOT,
    _analogue_outcome,
    _event,
    _issued,
    _log_file,
    _now,
    _seed_plan,
)


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
        latest_at=(
            datetime.fromisoformat(original["latest_at"]) + timedelta(hours=2)
        ).isoformat(),
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
    breach_ts = (
        datetime.fromisoformat(original["latest_at"]) + timedelta(minutes=5)
    ).isoformat()
    successor = _build_estimate(
        plan,
        prefix=prefix,
        revision=1,
        predecessor=original,
        cause="estimate_error",
        earliest_at=original["earliest_at"],
        latest_at=(
            datetime.fromisoformat(original["latest_at"]) + timedelta(hours=2)
        ).isoformat(),
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

"""D01 — where the range comes from, and what it is honest enough to claim.

Three regimes, and the threshold between them is the point. With five comparable
outcomes in the cohort the method is `comparable_deliveries_percentile`: the bounds are
the 10th and 90th percentiles of the observed durations, taken by ceiling index over the
sorted sample, offset from the issue time, and the evidence class is `measured` because
prior deliveries were actually counted. Below five the method is
`cold_start_slice_schedule`, the bounds fall back to the plan's own 120 s to 900 s slice
budget, and the evidence class drops to `asserted: low evidence` — a small sample must
not borrow the authority of a measurement.

Censoring is handled rather than discarded. A run that timed out is a lower bound on a
duration nobody observed, so it stays in the analogue set — six analogues, not five —
and the upper bound is pushed out to at least its duration plus the recovery allowance
of 600 s. Dropping it would make the estimate look tighter precisely because a delivery
went badly."""

import math
from datetime import datetime, timedelta
from consilient import events
from delivery_estimate_helpers import (
    COHORT,
    DELIVERY_ID,
    RESOURCE_SNAPSHOT,
    _analogue_outcome,
    _issued,
    _seed_plan,
)


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

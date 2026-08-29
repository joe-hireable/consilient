"""Dispatch claims: what each live run intends to touch, and refusal on overlap.

The trajectory is the only registry. A claim is a `work_item.opened` event whose ticket
is `dispatch:<run_id>`, written through the single `append()` writer like everything
else. It is released by any of three independent events, checked at read time:

1. `work_item.completed` on the same ticket (the dispatcher released it);
2. the run's own `dispatch.outcome` or `dispatch.refused` (the run ended, whatever the
   release path forgot to write);
3. its own `expires_at` passing — a 30 s fencing-token lease when `lease_s`
   is set, otherwise the historical run-timeout-plus-grace bound.

The third is the one that matters: a crashed or SIGKILLed dispatcher cannot hold a claim
forever. The stale `.budget.lock` measured on this machine refuses forever after a
SIGKILL because it is a file; a claim is a projection over events with a clock, so the
passage of time alone releases it. No lock file exists to go stale.

F-04 measured a killed dispatch holding its claim for the full run timeout (one hour).
BU-3 replaces that with a 30 s lease and a monotonically increasing fencing epoch:
another run may reclaim the path at expiry, and `admit_write` rejects a token that has
gone backwards, so the expired holder cannot corrupt after it wakes. [cited: Kleppmann
2016; Burrows 2006, bibliography § 16, both [FULL]] A live holder renews the same epoch;
only a new acquire increments it.

A claim with no declared paths conflicts with nothing and protects nothing — it exists
so the run is visible in the work-item stream, not to exclude others. The refusal
invariant only covers declared paths; that limit is stated in the dispatch payload and
in the design report, not hidden.

This module now leads a family of five. `coordination_records.py` holds the claim record
types, the actor and lease constants, the path grammar and the native readiness refusal.
`coordination_projection.py` reads the world into values — a claim from its event, a
worker's liveness from its pid record, plan units and lane tables from build-plan
markdown, the composite-exposure decision, and the bounded in-flight render.
`coordination_leases.py` holds live claims, conflict, the fencing epoch, the claim
payload, release by completion, and the plan-time lane ordering.
`coordination_admission.py` holds what admits under the F02 lock: the claim validator,
the locked native transition, and the confirmed-gone release. This file keeps the two
acquire paths, `open_claim` and `renew_claim`, together with the derived serial lane
contract and its ordering refusal."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .events import (
    Event,
    EventError,
    EventPayload,
    append_transaction,
    read_all,
)
from .coordination_records import (
    CLAIM_GRACE_S,
    LEASE_TTL_S,
    PlanUnit,
)

from .coordination_admission import (
    _live_claim,
    _validate_dispatch_claim_admission,
    claim_predecessors,
    claim_ready_work,
    derive_lane_order,
    release_claims_when_worker_gone,
)

from .coordination_leases import (
    ClaimConflict,
    _claim_event_payload,
    _next_fencing_epoch,
    admit_write,
    claim_ticket,
    close_claim,
    conflict,
    lane_order_inversions,
    live_claims,
)

from .coordination_projection import (
    _process_still_running,
    admit_composite_exposure,
    canonical_path,
    parse_build_plan_lanes,
    parse_plan_units,
    render_in_flight,
    worker_gone_from_pid_record,
)

from .coordination_records import (
    CLAIM_TICKET_PREFIX,
    Claim,
    ClaimReadyError,
    ClaimRelease,
    DISPATCH_ACTOR,
    ExposureAdmission,
    IN_FLIGHT_LIMIT_CHARS,
    StaleEpoch,
    _parse_ts,
    native_readiness_refusal,
    paths_overlap,
)

__all__ = [
    "CLAIM_GRACE_S",
    "CLAIM_TICKET_PREFIX",
    "Claim",
    "ClaimConflict",
    "ClaimReadyError",
    "ClaimRelease",
    "DISPATCH_ACTOR",
    "ExposureAdmission",
    "IN_FLIGHT_LIMIT_CHARS",
    "LEASE_TTL_S",
    "PlanUnit",
    "StaleEpoch",
    "_claim_event_payload",
    "_live_claim",
    "_next_fencing_epoch",
    "_parse_ts",
    "_process_still_running",
    "_validate_dispatch_claim_admission",
    "admit_composite_exposure",
    "admit_write",
    "canonical_path",
    "claim_order_violation",
    "claim_predecessors",
    "claim_ready_work",
    "claim_ticket",
    "close_claim",
    "conflict",
    "derive_lane_order",
    "derive_serial_lane_contract",
    "lane_order_inversions",
    "live_claims",
    "native_readiness_refusal",
    "open_claim",
    "parse_build_plan_lanes",
    "parse_plan_units",
    "paths_overlap",
    "release_claims_when_worker_gone",
    "render_in_flight",
    "renew_claim",
    "worker_gone_from_pid_record",
]


def open_claim(
    log: Path,
    *,
    run_id: str,
    paths: Sequence[str],
    cwd: Path,
    timeout_s: int,
    harness: str | None = None,
    task: str | None = None,
    now: datetime | None = None,
    extra: Mapping[str, object] | None = None,
    lease_s: int | None = None,
) -> EventPayload:
    """Admit one dispatch claim atomically: conflict-check and append under F02.

    Pass `lease_s=LEASE_TTL_S` for a 30 s fencing-token lease. Callers that omit
    it keep the historical `timeout_s + CLAIM_GRACE_S` bound so the commit-gate
    clock fixture, which this unit does not own, stays green.
    """
    if timeout_s < 0:
        raise ValueError("timeout_s must be non-negative")
    if lease_s is not None and lease_s < 1:
        raise ValueError("lease_s must be at least 1")
    opened = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ttl_s = lease_s if lease_s is not None else timeout_s + CLAIM_GRACE_S
    expires = opened + timedelta(seconds=ttl_s)
    canonical = [canonical_path(path, cwd=cwd) for path in paths]
    ticket = claim_ticket(run_id)
    accepted: tuple[Event, ...] | list[Event]
    if log.exists():
        accepted, _rejected = read_all(log)
    else:
        accepted = []
    epoch = _next_fencing_epoch(accepted, canonical, cwd=cwd, ticket=ticket)
    event = _claim_event_payload(
        run_id=run_id,
        paths=canonical,
        cwd=cwd,
        opened=opened,
        expires=expires,
        fencing_epoch=epoch,
        harness=harness,
        task=task,
        extra=extra,
        written_at=datetime.now(timezone.utc),
    )

    def validator(
        prefix: tuple[Event, ...],
        rejections: object,
        candidates: tuple[EventPayload, ...],
    ) -> None:
        _validate_dispatch_claim_admission(
            prefix, rejections, candidates, cwd=cwd, now=opened
        )

    try:
        written = append_transaction(log, [event], validator)
    except EventError as exc:
        if "fencing epoch" not in str(exc) or "stale" not in str(exc):
            raise
        accepted, _rejected = read_all(log) if log.exists() else ([], [])
        event["data"]["fencing_epoch"] = _next_fencing_epoch(
            accepted, canonical, cwd=cwd, ticket=ticket
        )
        written = append_transaction(log, [event], validator)
    return written[0]


def renew_claim(
    log: Path,
    *,
    run_id: str,
    token: int,
    cwd: Path,
    now: datetime | None = None,
) -> EventPayload:
    """Extend a live holder's lease. The epoch does not rise; only a new acquire does.

    A renewal is not an acquire, so it does not run the admission validator: that
    one demands the *next* epoch and would reject a holder for keeping its own.
    What it re-checks under the F02 lock is the property renewal actually needs —
    that the same holder is still live on the same token at write time.
    """
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    accepted: tuple[Event, ...] | list[Event]
    if log.exists():
        accepted, _rejected = read_all(log)
    else:
        accepted = []
    claim = admit_write(
        token=token, claim=_live_claim(accepted, run_id=run_id, now=stamp)
    )
    event = _claim_event_payload(
        run_id=run_id,
        paths=claim.paths,
        cwd=cwd,
        opened=stamp,
        expires=stamp + timedelta(seconds=LEASE_TTL_S),
        fencing_epoch=claim.fencing_epoch,
        harness=claim.harness,
        task=None,
        written_at=datetime.now(timezone.utc),
    )

    def validator(
        prefix: tuple[Event, ...],
        _rejections: object,
        _candidates: tuple[EventPayload, ...],
    ) -> None:
        admit_write(token=token, claim=_live_claim(prefix, run_id=run_id, now=stamp))

    return append_transaction(log, [event], validator)[0]


def derive_serial_lane_contract(
    units: Mapping[str, PlanUnit], lane_paths: Sequence[str]
) -> dict[str, tuple[str, ...]]:
    """Derived order for each named lane file."""
    return {lane: derive_lane_order(units, lane) for lane in lane_paths}


def claim_order_violation(
    unit_id: str,
    completed: frozenset[str],
    units: Mapping[str, PlanUnit],
) -> str | None:
    """Refusal reason when predecessors are not complete, else ``None``."""
    missing = claim_predecessors(unit_id, units) - completed
    if not missing:
        return None
    blockers = ", ".join(sorted(missing))
    return f"claim ordering: {unit_id} requires completed predecessors: {blockers}"

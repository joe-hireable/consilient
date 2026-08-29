"""Admission under the lock: the checks that must not run on a stale read.

Everything a claim actually excludes is decided in `_validate_dispatch_claim_admission`,
which runs inside the F02 append transaction rather than before it. Conflict is
re-tested against the locked prefix, and the supplied fencing epoch is compared
at-least, never exactly: the fencing rule is that a new token must outrank every earlier
one, and a token above the minimum is still monotone and still safe, while only a token
that is too low can let an expired holder write behind a live one. The full account of
why equality was wrong, and why widening the locked read is the worse repair, is
recorded beside the comparison.

`claim_ready_work` is one locked transition for native work: readiness,
composite-exposure admission where the attempt has passed the verifier, path lease,
predecessor bindings and epoch, with the claim and its attempt event appended together
so no state exists in which one was written and the other refused. Readiness is checked
twice on purpose — once on the open read to fail cheaply, once under the lock, where the
answer is the one that counts.

`release_claims_when_worker_gone` is deliberately reluctant. N00 identifies start_failed
candidates from artefact silence, and this refuses to act on that alone: a claim is
closed only when the caller's liveness probe proves the worker gone, retained when it is
still running, and retained again when liveness cannot be determined. Releasing a merely
slow worker's path would admit two agents to one file, which is worse than waiting out
the lease. `_live_claim` holds the same line for renewal, raising rather than inventing
a claim for a run that has already gone.
"""

from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import beta, work_items
from .events import (
    Event,
    EventError,
    EventPayload,
    SCHEMA_VERSION,
    append_transaction,
    read_all,
)
from .coordination_records import (
    CLAIM_GRACE_S,
    Claim,
    ClaimReadyError,
    ClaimRelease,
    DISPATCH_ACTOR,
    PlanUnit,
    StaleEpoch,
    _is_dispatch_claim_payload,
    _native_items_from_prefix,
    native_readiness_refusal,
    paths_overlap,
)

from .coordination_leases import (
    ClaimConflict,
    _claim_event_payload,
    _next_fencing_epoch,
    _stable_serial_order,
    _transitive_depends,
    _units_claiming_path,
    admit_write,
    claim_ticket,
    close_claim,
    conflict,
    live_claims,
)

from .coordination_projection import (
    admit_composite_exposure,
    canonical_path,
)


__all__ = [
    "CLAIM_GRACE_S",
    "Claim",
    "ClaimConflict",
    "ClaimReadyError",
    "ClaimRelease",
    "DISPATCH_ACTOR",
    "PlanUnit",
    "StaleEpoch",
    "_claim_event_payload",
    "_is_dispatch_claim_payload",
    "_native_items_from_prefix",
    "_next_fencing_epoch",
    "_stable_serial_order",
    "_transitive_depends",
    "_units_claiming_path",
    "admit_composite_exposure",
    "admit_write",
    "canonical_path",
    "claim_predecessors",
    "claim_ready_work",
    "claim_ticket",
    "close_claim",
    "conflict",
    "derive_lane_order",
    "live_claims",
    "native_readiness_refusal",
    "paths_overlap",
    "release_claims_when_worker_gone",
]


def _validate_dispatch_claim_admission(
    prefix: tuple[Event, ...],
    _rejections: object,
    candidates: tuple[EventPayload, ...],
    *,
    cwd: Path,
    now: datetime,
) -> None:
    """Conflict-check and epoch-compare under the F02 lock."""
    history = list(prefix)
    for candidate in candidates:
        if candidate["event"] != work_items.OPENED:
            history.append(Event(candidate))
            continue
        data = candidate["data"]
        if not _is_dispatch_claim_payload(data):
            history.append(Event(candidate))
            continue
        paths = [item for item in data["paths"] if isinstance(item, str)]
        live = live_claims(history, now=now)
        if paths:
            hit = conflict(paths, live, cwd=cwd)
            if hit is not None:
                raise ClaimConflict(hit, live)
        expected = _next_fencing_epoch(
            history, paths, cwd=cwd, ticket=claim_ticket(str(data["run_id"]))
        )
        # AT LEAST, not EXACTLY. MEASURED 25 August 2026: this was `!= expected` and it stopped
        # the harness dispatching. 26 units sat at the retry cap and every one of them had died
        # here -- "fencing epoch 4 is stale; expected 1", 78 recorded deaths of this shape.
        #
        # The two sides compute over different scopes. `open_claim` derives the epoch from
        # `read_all(log)`, which reads EVERY day file in the trajectory. This validator runs
        # inside the F02 append transaction, whose locked prefix is `_read_under_lock(path, fd)`
        # -- ONE file, the day being appended to. While every claim lived in the same day file
        # the two agreed. At midnight the log rolled, the new day's file held no earlier claim,
        # `expected` collapsed to 1, and every dispatch that had legitimately computed 4 or 5
        # from the real history was refused as stale. That is exactly when dispatch stopped.
        #
        # Equality was never the safety property. The fencing rule (Kleppmann) is that a new
        # token must OUTRANK every earlier one; a token that outranks by more than the minimum
        # is still monotone and still safe. Only a token that is too LOW can let an expired
        # holder write behind a live one, and the error text has always said "stale", which is
        # a claim about being behind. So refuse below `expected` and accept at or above it.
        #
        # Widening the locked read to the whole directory would be the other repair, and it is
        # the wrong one: it puts a seven-file scan inside a held write lock on the hot path.
        supplied = data.get("fencing_epoch")
        if (
            not isinstance(supplied, int)
            or isinstance(supplied, bool)
            or supplied < expected
        ):
            raise EventError(
                f"fencing epoch {supplied!r} is stale; the next epoch for these paths "
                f"is at least {expected}"
            )
        history.append(Event(candidate))


def _live_claim(events: Iterable[Event], *, run_id: str, now: datetime) -> Claim:
    """The one live claim held by `run_id`, or a refusal when it has already gone."""
    for claim in live_claims(events, now=now):
        if claim.run_id == run_id:
            return claim
    raise StaleEpoch(f"run {run_id} has no live claim to renew")


def release_claims_when_worker_gone(
    log: Path,
    *,
    run_ids: Sequence[str],
    worker_gone: Callable[[str], bool | None],
    now: datetime | None = None,
) -> tuple[ClaimRelease, ...]:
    """Release live dispatch claims only when the worker is confirmed gone.

    N00 identifies start_failed candidates from artefact silence; this function
    closes their claims only when ``worker_gone`` proves the worker is not
    running. Releasing while the worker is merely slow would admit two agents
    to one path — worse than waiting for claim expiry.

    ``worker_gone(run_id)`` returns ``True`` when the worker is confirmed gone
    (``close_claim`` is written), ``False`` when it is still running, and
    ``None`` when liveness cannot be determined (the claim is retained).
    """
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    events, _rejected = read_all(log)
    live_ids = {claim.run_id for claim in live_claims(events, now=stamp)}
    results: list[ClaimRelease] = []
    for run_id in run_ids:
        if run_id not in live_ids:
            results.append(ClaimRelease(run_id, False, "no live claim"))
            continue
        gone = worker_gone(run_id)
        if gone is True:
            close_claim(log, run_id=run_id)
            results.append(ClaimRelease(run_id, True, "worker confirmed gone"))
        elif gone is False:
            results.append(ClaimRelease(run_id, False, "worker still running"))
        else:
            results.append(ClaimRelease(run_id, False, "liveness unknown"))
    return tuple(results)


def claim_ready_work(
    log: Path,
    *,
    run_id: str,
    cwd: Path,
    timeout_s: int,
    ticket: str,
    revision: int,
    attempt_id: str,
    harness: str,
    model: str,
    family: str,
    pool: str,
    capability_context_digest: str,
    candidate_ordinal: int,
    predecessor_bindings: Sequence[Mapping[str, object]],
    task_family: str,
    protocol_id: str,
    protocol_version: str,
    epsilon: float,
    now: datetime | None = None,
    task: str | None = None,
    exposure_state: str = "pre_verifier",
    estimate: beta.Beta | None = None,
    estimand_kind: str | None = None,
    auth_status: str | None = None,
) -> EventPayload:
    """One locked transition: native readiness, path lease, bindings and epoch."""
    opened = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = opened + timedelta(seconds=timeout_s + CLAIM_GRACE_S)
    accepted, _rejected = read_all(log) if log.exists() else ([], [])
    refusal = native_readiness_refusal(
        accepted,
        ticket=ticket,
        revision=revision,
        predecessor_bindings=predecessor_bindings,
        cwd=cwd,
    )
    if refusal is not None:
        raise ClaimReadyError(refusal)
    items = _native_items_from_prefix(accepted)
    item = items[(ticket, revision)]
    owned = [canonical_path(str(path), cwd=cwd) for path in item["owned_paths"]]
    if exposure_state != "pre_verifier":
        admission = admit_composite_exposure(
            candidate_ordinal=candidate_ordinal,
            task_family=task_family,
            protocol_id=protocol_id,
            protocol_version=protocol_version,
            epsilon=epsilon,
            estimate=estimate,
            estimand_kind=estimand_kind,
            auth_status=auth_status,
        )
        if not admission.admitted:
            raise ClaimReadyError(admission.reason)

    epoch = _next_fencing_epoch(accepted, owned, cwd=cwd, ticket=claim_ticket(run_id))
    extra = {
        "ticket_ref": ticket,
        "revision": revision,
        "attempt_id": attempt_id,
        "plan_digest": item["plan_digest"],
        "commitment_digest": item.get("commitment_digest"),
        "candidate_ordinal": candidate_ordinal,
        "exposure_state": exposure_state,
        "predecessor_bindings": [dict(binding) for binding in predecessor_bindings],
        "capability_context_digest": capability_context_digest,
        "family": family,
        "pool": pool,
        "model": model,
    }
    written_at = datetime.now(timezone.utc)
    claim = _claim_event_payload(
        run_id=run_id,
        paths=owned,
        cwd=cwd,
        opened=opened,
        expires=expires,
        fencing_epoch=epoch,
        harness=harness,
        task=task,
        extra=extra,
        written_at=written_at,
    )
    attempt: EventPayload = {
        "v": SCHEMA_VERSION,
        "ts": written_at.isoformat(),
        "event": work_items.NATIVE_ATTEMPTED,
        "actor": DISPATCH_ACTOR,
        "data": {
            "ticket": ticket,
            "revision": revision,
            "plan_digest": item["plan_digest"],
            "attempt_id": attempt_id,
            "run_id": run_id,
            "claimed_paths": list(item["owned_paths"]),
            "opened_at": opened.isoformat(),
            "expires_at": expires.isoformat(),
            "harness": harness,
            "model": model,
            "family": family,
            "pool": pool,
            "capability_context_digest": capability_context_digest,
            "candidate_ordinal": candidate_ordinal,
            "exposure_state": exposure_state,
            "predecessor_bindings": [dict(binding) for binding in predecessor_bindings],
            "fencing_epoch": epoch,
        },
    }

    def validator(
        prefix: tuple[Event, ...],
        rejections: object,
        candidates: tuple[EventPayload, ...],
    ) -> None:
        locked_refusal = native_readiness_refusal(
            prefix,
            ticket=ticket,
            revision=revision,
            predecessor_bindings=predecessor_bindings,
            cwd=cwd,
        )
        if locked_refusal is not None:
            raise ClaimReadyError(locked_refusal)
        _validate_dispatch_claim_admission(
            prefix, rejections, candidates, cwd=cwd, now=opened
        )

    written = append_transaction(log, [claim, attempt], validator)
    return written[0]


def derive_lane_order(units: Mapping[str, PlanUnit], lane_path: str) -> tuple[str, ...]:
    """Serial order for one mutable lane derived from claims and depends edges."""
    return _stable_serial_order(_units_claiming_path(units, lane_path), units)


def claim_predecessors(unit_id: str, units: Mapping[str, PlanUnit]) -> frozenset[str]:
    """Units that must finish before ``unit_id`` may open a claim."""
    if unit_id not in units:
        return frozenset()
    preds = set(_transitive_depends(unit_id, units))
    unit = units[unit_id]
    if not unit.paths:
        return frozenset(preds)
    for other_id, other in units.items():
        if other_id == unit_id:
            continue
        if not other.paths:
            continue
        if not any(
            paths_overlap(canonical_path(a), canonical_path(b))
            for a in unit.paths
            for b in other.paths
        ):
            continue
        order = _stable_serial_order((unit_id, other_id), units)
        if order.index(other_id) < order.index(unit_id):
            preds.add(other_id)
            preds.update(_transitive_depends(other_id, units))
    return frozenset(preds)

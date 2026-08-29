"""The lease itself: which claims are live, what they exclude, and the fencing epoch
that outranks them.

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
only a new acquire increments it. `_next_fencing_epoch` counts expired claims as well as
live ones, and is path-scoped so independent files do not share a sequencer.

A claim with no declared paths conflicts with nothing and protects nothing — it exists
so the run is visible in the work-item stream, not to exclude others. The refusal
invariant only covers declared paths; that limit is stated in the dispatch payload and
in the design report, not hidden.

The lane-ordering functions are the same question asked before anything runs. Where a
lease decides at dispatch time who holds a path, `_units_claiming_path`,
`_transitive_depends` and `_stable_serial_order` decide from the build plan which units
must be serialised on one mutable file, breaking ties on unit id so the order is
deterministic, and falling back to sorted ids when the declared edges contain a cycle
rather than returning a partial list. `lane_order_inversions` audits the hand-written
lane table against those derived edges and names each row that lists a unit before
something it depends on."""

from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from . import work_items
from .events import (
    Event,
    EventError,
    EventPayload,
    SCHEMA_VERSION,
)
from .coordination_records import (
    CLAIM_TICKET_PREFIX,
    Claim,
    DISPATCH_ACTOR,
    PlanUnit,
    StaleEpoch,
    _TERMINAL_DISPATCH_KINDS,
    _is_dispatch_claim_payload,
    _parse_ts,
    paths_overlap,
)

from .coordination_projection import (
    _claim_from_event,
    canonical_path,
)


__all__ = [
    "CLAIM_TICKET_PREFIX",
    "Claim",
    "ClaimConflict",
    "DISPATCH_ACTOR",
    "PlanUnit",
    "StaleEpoch",
    "_TERMINAL_DISPATCH_KINDS",
    "_claim_from_event",
    "_is_dispatch_claim_payload",
    "_parse_ts",
    "admit_write",
    "canonical_path",
    "claim_ticket",
    "close_claim",
    "conflict",
    "lane_order_inversions",
    "live_claims",
    "paths_overlap",
]


class ClaimConflict(EventError):
    """The locked admission refused a path overlap. One lease already exists."""

    def __init__(self, hit: tuple[Claim, str, str], live: tuple[Claim, ...]) -> None:
        claim, requested, held = hit
        self.hit = hit
        self.live = live
        super().__init__(
            f"claims overlap a live dispatch: {claim.ticket} (run {claim.run_id}, "
            f"{claim.actor}) holds {held!r} until {claim.expires_at}; this "
            f"dispatch asked for {requested!r}"
        )


def claim_ticket(run_id: str) -> str:
    return f"{CLAIM_TICKET_PREFIX}{run_id}"


def admit_write(*, token: int, claim: Claim) -> Claim:
    """The resource check: reject a token that has gone backwards or was never issued."""
    if token != claim.fencing_epoch:
        raise StaleEpoch(
            f"fencing token {token} is behind live epoch {claim.fencing_epoch} "
            f"for run {claim.run_id}"
        )
    return claim


def live_claims(events: Iterable[Event], *, now: datetime) -> tuple[Claim, ...]:
    """Claims still held at `now`, in the order they were opened.

    Liveness is decided entirely from the event stream: opened, not completed, the run
    has no terminal dispatch event, and the claim has not expired. A projection, so
    reading it writes nothing and cannot itself hold anything.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must carry an explicit offset")
    now_utc = now.astimezone(timezone.utc)
    opened: dict[str, Event] = {}
    released_tickets: set[str] = set()
    ended_runs: set[str] = set()
    for event in events:
        data = event.data
        if event.kind == work_items.OPENED:
            ticket = data.get("ticket")
            if isinstance(ticket, str) and ticket.startswith(CLAIM_TICKET_PREFIX):
                opened[ticket] = event
        elif event.kind == work_items.COMPLETED:
            ticket = data.get("ticket")
            if isinstance(ticket, str):
                released_tickets.add(ticket)
        elif event.kind in _TERMINAL_DISPATCH_KINDS:
            run_id = data.get("run_id")
            if isinstance(run_id, str):
                ended_runs.add(run_id)
    live: list[Claim] = []
    for ticket, event in opened.items():
        claim = _claim_from_event(ticket, event)
        if claim is None:
            continue
        if ticket in released_tickets or claim.run_id in ended_runs:
            continue
        expires = _parse_ts(claim.expires_at)
        if expires is None or expires <= now_utc:
            continue
        live.append(claim)
    return tuple(live)


def conflict(
    paths: Sequence[str], live: Sequence[Claim], *, cwd: Path
) -> tuple[Claim, str, str] | None:
    """The first live claim overlapping any requested path, with the offending pair.

    A dispatch that declares no paths conflicts with nothing: the refusal invariant
    covers declared surfaces only, and an undeclared dispatch says so in its payload
    rather than claiming protection it does not have.
    """
    for requested in paths:
        canonical_requested = canonical_path(requested, cwd=cwd)
        for claim in live:
            for held in claim.paths:
                if paths_overlap(canonical_requested, held):
                    return claim, canonical_requested, held
    return None


def _next_fencing_epoch(
    prefix: Sequence[Event], paths: Sequence[str], *, cwd: Path, ticket: str
) -> int:
    """Monotone epoch over every overlapping claim, including expired ones.

    Kleppmann's fencing token: expiry alone is unsafe because the expired holder
    can wake and write. The next lease on the same paths must outrank every
    earlier token, live or not. Path-scoped so independent files do not share a
    sequencer; the same ticket always continues its own sequence, so a re-open
    that has since narrowed its paths still cannot reuse a token it already spent.
    """
    highest = 0
    requested = [canonical_path(path, cwd=cwd) for path in paths]
    for event in prefix:
        if event.kind != work_items.OPENED or not _is_dispatch_claim_payload(
            event.data
        ):
            continue
        epoch = event.data.get("fencing_epoch")
        if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
            continue
        if event.data.get("ticket") == ticket:
            highest = max(highest, epoch)
            continue
        held = event.data.get("paths")
        if not isinstance(held, list):
            continue
        if any(
            isinstance(item, str)
            and any(paths_overlap(want, item) for want in requested)
            for item in held
        ):
            highest = max(highest, epoch)
    return highest + 1


def _claim_event_payload(
    *,
    run_id: str,
    paths: Sequence[str],
    cwd: Path,
    opened: datetime,
    expires: datetime,
    fencing_epoch: int,
    harness: str | None,
    task: str | None,
    extra: Mapping[str, object] | None = None,
    written_at: datetime | None = None,
) -> EventPayload:
    data: dict[str, object] = {
        "ticket": claim_ticket(run_id),
        "accountable": DISPATCH_ACTOR,
        "run_id": run_id,
        "paths": list(paths),
        "cwd": str(cwd),
        "opened_at": opened.isoformat(),
        "expires_at": expires.isoformat(),
        "fencing_epoch": fencing_epoch,
    }
    if paths:
        # T01's dispatch-claim.v1 contract requires a non-empty path list.
        data["item_schema"] = work_items.DISPATCH_CLAIM_SCHEMA
    if harness is not None:
        data["harness"] = harness
    if task:
        data["text"] = task[:500]
    if extra:
        reserved = set(data) | {"human_decision", "human_verdict"}
        collision = reserved & set(extra)
        if collision:
            raise EventError(
                f"work_item.opened extra fields may not override {sorted(collision)}"
            )
        data.update(dict(extra))
    return {
        "v": SCHEMA_VERSION,
        "ts": (written_at or datetime.now(timezone.utc)).isoformat(),
        "event": work_items.OPENED,
        "actor": DISPATCH_ACTOR,
        "data": data,
    }


def close_claim(log: Path, *, run_id: str) -> EventPayload:
    """Release by completion. Expiry and the run's terminal event back this up."""
    return work_items.complete_item(
        log, ticket=claim_ticket(run_id), actor=DISPATCH_ACTOR
    )


def _units_claiming_path(
    units: Mapping[str, PlanUnit], lane_path: str
) -> tuple[str, ...]:
    canonical_lane = canonical_path(lane_path)
    claimed: list[str] = []
    for unit_id, unit in units.items():
        if any(
            paths_overlap(canonical_lane, canonical_path(path)) for path in unit.paths
        ):
            claimed.append(unit_id)
    return tuple(sorted(claimed))


def _transitive_depends(unit_id: str, units: Mapping[str, PlanUnit]) -> frozenset[str]:
    seen: set[str] = set()
    queue = list(units[unit_id].depends)
    while queue:
        cur = queue.pop()
        if cur in seen or cur not in units:
            continue
        seen.add(cur)
        queue.extend(units[cur].depends)
    return frozenset(seen)


def _stable_serial_order(
    unit_ids: Sequence[str], units: Mapping[str, PlanUnit]
) -> tuple[str, ...]:
    """Topological order with path-overlap serialisation and unit-id tie-break."""
    ids = tuple(sorted(unit_ids))
    if not ids:
        return ()
    must_precede: dict[str, set[str]] = {uid: set() for uid in ids}
    for left in ids:
        for right in ids:
            if left == right:
                continue
            if right in units[left].depends:
                must_precede[left].add(right)
            elif left in units[right].depends:
                must_precede[right].add(left)
            elif (
                _transitive_depends(left, units).isdisjoint({right})
                and _transitive_depends(right, units).isdisjoint({left})
                and units[left].paths
                and units[right].paths
            ):
                left_paths = [canonical_path(p) for p in units[left].paths]
                right_paths = [canonical_path(p) for p in units[right].paths]
                if any(paths_overlap(a, b) for a in left_paths for b in right_paths):
                    if left < right:
                        must_precede[right].add(left)
                    else:
                        must_precede[left].add(right)
    indegree = {uid: len(must_precede[uid]) for uid in ids}
    ready = sorted(uid for uid in ids if indegree[uid] == 0)
    ordered: list[str] = []
    while ready:
        uid = ready.pop(0)
        ordered.append(uid)
        for other in ids:
            if uid in must_precede[other]:
                must_precede[other].remove(uid)
                indegree[other] -= 1
                if indegree[other] == 0:
                    ready.append(other)
                    ready.sort()
    if len(ordered) != len(ids):
        # Cycle among declared edges — fall back to sorted ids so callers still
        # get a deterministic answer rather than a partial list.
        return ids
    return tuple(ordered)


def lane_order_inversions(
    units: Mapping[str, PlanUnit],
    hand_lanes: Mapping[str, Sequence[str]],
) -> tuple[tuple[str, str, str], ...]:
    """Hand-written lane rows that list a unit before one it depends on.

    Returns ``(lane_path, earlier, later)`` triples where ``later`` is a
    transitive dependency of ``earlier`` but appears after it in the hand table.
    """
    inversions: list[tuple[str, str, str]] = []
    for lane_path, order in hand_lanes.items():
        for index, earlier in enumerate(order):
            if earlier not in units:
                continue
            deps = _transitive_depends(earlier, units)
            for later in order[index + 1 :]:
                if later in deps:
                    inversions.append((lane_path, earlier, later))
    return tuple(inversions)

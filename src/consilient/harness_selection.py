"""Choosing which harness, which model and how many arms — and refusing when none of
them may be spent.

Selection prefers the pool with the most remaining headroom. Eligibility is decided
first and separately from ranking, so a refusal always carries the reason it refused
rather than a silent absence from the ranking; that separation is what `_ineligible` and
`_rank_key` are for.

Fan-out is where Whewell's second clause is mechanical rather than aspirational:
`family:<family>` is the evidence class, so two arms drawn from the same vendor family
are not a fan-out, they are one induction counted twice. `select_fanout` enforces that,
and harness_recording stamps the class it actually got.

This module imports from three siblings — harness_registry for the nouns, harness_models
for the model registry, and harness_headroom for the exhaustion and remaining-percent
predicates. Those three import statements are written by hand rather than emitted by the
splitter, and the dependency runs one way only."""

from collections.abc import Sequence
from .harness_registry import (
    Decision,
    FanoutDecision,
    HARNESSES,
    Harness,
    PoolState,
    Probe,
    harness_by_id,
    pool_by_name,
    probe_by_id,
)

from .harness_headroom import (
    _blocked,
    _is_exhausted,
    remaining_percent,
)

from .harness_models import (
    AVOIDED_CURSOR_POOL,
    MODELS,
    ModelOption,
    UNMAPPED_REASONING_PROVENANCE,
    model_family,
    models_for_harness,
    pool_for_model,
)


__all__ = [
    "AVOIDED_CURSOR_POOL",
    "Decision",
    "FanoutDecision",
    "HARNESSES",
    "Harness",
    "MODELS",
    "ModelOption",
    "PoolState",
    "Probe",
    "UNMAPPED_REASONING_PROVENANCE",
    "_blocked",
    "_is_exhausted",
    "describe_registry",
    "harness_by_id",
    "model_family",
    "models_for_harness",
    "pool_by_name",
    "pool_for_model",
    "probe_by_id",
    "remaining_percent",
    "select",
    "select_fanout",
    "select_model",
]


def select_model(
    harness_id: str,
    *,
    pools: Sequence[PoolState],
    requested: str | None = None,
    family: str | None = None,
    models: tuple[ModelOption, ...] = MODELS,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> ModelOption | str:
    """Pick a model within a harness, or return a refusal reason string.

    An explicit `requested` id is attended naming, like an explicit `--harness`: it is
    returned with its pool resolved, unblocked. Automatic selection is stricter: only
    registered models on a *verified* pool with known, unexhausted headroom, most
    remaining headroom first, registry order within a tie. It never falls to the
    avoided cursor-other pool on its own — that is the silent-fallback shape at model
    level, and it is enforced even when a row is verified as cursor-other.
    """
    harness = harness_by_id(harness_id, harnesses)
    if harness is None:
        known = ", ".join(item.id for item in harnesses)
        return f"unknown harness {harness_id!r}; known: {known}"
    if requested is not None:
        for option in models:
            if option.harness_id == harness_id and option.id == requested:
                return option
        return ModelOption(
            requested,
            harness_id,
            model_family(requested),
            pool_for_model(harness_id, requested, models=models, harnesses=harnesses),
            reasoning_capability="unknown",
            reasoning_provenance=UNMAPPED_REASONING_PROVENANCE,
        )
    registered = list(models_for_harness(harness_id, models))
    if not registered:
        return (
            f"no models registered for {harness_id}; pass --model explicitly "
            "(an unregistered default would be an invented capability)"
        )
    if family is not None:
        registered = [item for item in registered if item.family == family]
        if not registered:
            known_families = sorted(
                {item.family for item in models_for_harness(harness_id, models)}
            )
            return (
                f"no {family!r} family models registered for {harness_id}; "
                f"known families: {', '.join(known_families)}"
            )
    pool_tuple = tuple(pools)
    eligible: list[tuple[int, ModelOption]] = []
    considered: list[str] = []
    for index, option in enumerate(registered):
        if not option.pool_verified:
            considered.append(f"{option.id}: pool assignment is unverified")
            continue
        if option.pool == AVOIDED_CURSOR_POOL:
            considered.append(
                f"{option.id}: pool {option.pool} is avoided unless named explicitly"
            )
            continue
        pool = pool_by_name(option.pool, pool_tuple)
        if pool is None:
            considered.append(
                f"{option.id}: pool {option.pool} has no headroom snapshot"
            )
            continue
        if _is_exhausted(pool):
            considered.append(f"{option.id}: {option.pool} is exhausted")
            continue
        if pool.used_percent is None:
            considered.append(f"{option.id}: {option.pool} headroom is unknown")
            continue
        eligible.append((index, option))
    if not eligible:
        detail = "; ".join(considered) if considered else "no registered models"
        return (
            f"no eligible model for {harness_id}: every registered model draws on an "
            f"exhausted or unmeasured pool, or an unverified pool assignment. {detail}. "
            "Pass --model explicitly to spend "
            "an avoided pool attended."
        )

    def rank(pair: tuple[int, ModelOption]) -> tuple[float, int]:
        index, option = pair
        pool = pool_by_name(option.pool, pool_tuple)
        assert pool is not None and pool.used_percent is not None
        return (pool.used_percent, index)

    eligible.sort(key=rank)
    return eligible[0][1]


def _ineligible(
    harness: Harness,
    probe: Probe | None,
    pool: PoolState | None,
    *,
    allow_exhausted: bool,
    require_known_headroom: bool,
) -> str | None:
    if probe is None or not probe.installed:
        detail = probe.detail if probe is not None else "not probed"
        return f"{harness.id}: not installed ({detail})"
    if pool is None:
        return f"{harness.id}: pool {harness.pool} has no headroom snapshot"
    blocked = _blocked(
        pool,
        allow_exhausted=allow_exhausted,
        require_known_headroom=require_known_headroom,
    )
    if blocked is not None:
        return f"{harness.id}: {blocked}"
    return None


def _rank_key(harness: Harness, pool: PoolState) -> tuple[float, str]:
    remaining = remaining_percent(pool)
    # Higher remaining headroom first; unknown sorts last. harness.id breaks ties.
    score = remaining if remaining is not None else -1.0
    return (-score, harness.id)


def select(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    requested: str | None = None,
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> Decision:
    """Pick one harness. Never returns an exhausted pool unless `allow_exhausted`."""
    pool_tuple = tuple(pools)
    considered: list[str] = []

    if requested is not None:
        harness = harness_by_id(requested, harnesses)
        if harness is None:
            known = ", ".join(item.id for item in harnesses)
            return Decision(
                kind="refuse",
                harness=None,
                reason=f"unknown harness {requested!r}; known: {known}",
                considered=(),
            )
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=False,
        )
        if reason is not None:
            return Decision(
                kind="refuse",
                harness=None,
                reason=reason,
                considered=(reason,),
            )
        assert pool is not None
        remaining = remaining_percent(pool)
        headroom = (
            f"{remaining:g}% remaining"
            if remaining is not None
            else pool.note or "headroom unknown"
        )
        return Decision(
            kind="run",
            harness=harness,
            reason=f"{harness.id} on {harness.pool} ({headroom})",
            considered=(),
        )

    ranked: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        ranked.append((harness, pool))

    if not ranked:
        detail = "; ".join(considered) if considered else "no harnesses in the registry"
        return Decision(
            kind="refuse",
            harness=None,
            reason=(
                "no eligible harness: every pool is exhausted, unknown, or not installed. "
                f"{detail}"
            ),
            considered=tuple(considered),
        )

    ranked.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    harness, pool = ranked[0]
    remaining = remaining_percent(pool)
    headroom = (
        f"{remaining:g}% remaining"
        if remaining is not None
        else pool.note or "headroom unknown"
    )
    return Decision(
        kind="run",
        harness=harness,
        reason=f"{harness.id} on {harness.pool} ({headroom})",
        considered=tuple(considered),
    )


def select_fanout(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> FanoutDecision:
    """Two harnesses from different families, each eligible, most headroom first."""
    pool_tuple = tuple(pools)
    considered: list[str] = []
    eligible: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        eligible.append((harness, pool))

    eligible.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    if not eligible:
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=("fan-out refused: no eligible harness. " + "; ".join(considered)),
            considered=tuple(considered),
        )

    first, first_pool = eligible[0]
    second_pair: tuple[Harness, PoolState] | None = None
    for harness, pool in eligible[1:]:
        if harness.family != first.family:
            second_pair = (harness, pool)
            break
    if second_pair is None:
        families = {item.family for item, _ in eligible}
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=(
                "fan-out refused: need two different model families; "
                f"eligible families: {', '.join(sorted(families)) or 'none'}"
            ),
            considered=tuple(considered),
        )

    second, second_pool = second_pair
    first_left = remaining_percent(first_pool)
    second_left = remaining_percent(second_pool)
    first_h = (
        f"{first_left:g}% remaining"
        if first_left is not None
        else first_pool.note or "unknown"
    )
    second_h = (
        f"{second_left:g}% remaining"
        if second_left is not None
        else second_pool.note or "unknown"
    )
    return FanoutDecision(
        kind="run",
        first=first,
        second=second,
        reason=(
            f"{first.id} ({first.family}, {first_h}) and "
            f"{second.id} ({second.family}, {second_h})"
        ),
        considered=tuple(considered),
    )


def describe_registry(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    pool_tuple = tuple(pools)
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        remaining = remaining_percent(pool) if pool is not None else None
        rows.append(
            {
                "id": harness.id,
                "family": harness.family,
                "pool": harness.pool,
                "binary": harness.binary,
                "installed": probe.installed if probe is not None else False,
                "version": probe.version if probe is not None else None,
                "probe": probe.detail if probe is not None else "not probed",
                "used_percent": pool.used_percent if pool is not None else None,
                "exhausted": pool.exhausted if pool is not None else False,
                "remaining_percent": remaining,
                "note": pool.note if pool is not None else "",
            }
        )
    return rows

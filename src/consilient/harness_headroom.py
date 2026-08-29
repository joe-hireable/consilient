"""What is left in each subscription pool, how stale that number is, and when it stops
counting.

Selection never silently spends an exhausted pool. Refusing with a reason is the success
path when the scarce resource is the only thing left — and `_is_exhausted` is where that
holds, which is why scripts/exp50_faults.py inverts this function's polarity to test
whether the invariant is really enforced. The fault entry names this file after the
split.

The operator observation is preserved above EXHAUSTED_USED_PERCENT: on 21 August 2026
Claude weekly was reported 'nearly exhausted' with no precise counter supplied, so it is
flagged exhausted rather than given an invented percent. That is the whole reason the
constant exists at 90.0 rather than at a measured figure, and deleting the note would
leave a number with no account of itself.

HEADROOM_MAX_AGE is the other half: a reading old enough to be wrong is refused rather
than trusted, because a stale headroom number spends the pool just as effectively as a
false one."""

import json
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .harness_registry import (
    DEFAULT_OBSERVED_AT,
    DEFAULT_POOLS,
    DEFAULT_SOURCE,
    Harness,
    PoolState,
)


__all__ = [
    "DEFAULT_OBSERVED_AT",
    "DEFAULT_POOLS",
    "DEFAULT_SOURCE",
    "EXHAUSTED_USED_PERCENT",
    "HEADROOM_MAX_AGE",
    "Harness",
    "PoolState",
    "headroom_freshness_refusal",
    "load_pools",
    "pools_from_mapping",
    "remaining_percent",
    "snapshot_mapping",
]

# Operator observation, 21 August 2026. Claude weekly is "nearly exhausted"; no precise
# counter was supplied, so it is flagged exhausted rather than given an invented percent.
EXHAUSTED_USED_PERCENT = 90.0

HEADROOM_MAX_AGE = timedelta(minutes=15)


def _is_exhausted(pool: PoolState) -> bool:
    if pool.exhausted:
        return True
    return pool.used_percent is not None and pool.used_percent >= EXHAUSTED_USED_PERCENT


def _blocked(
    pool: PoolState, *, allow_exhausted: bool, require_known_headroom: bool
) -> str | None:
    """Why this pool cannot be spent, or None if it can.

    Exhausted is a hard stop unless the operator names `--allow-exhausted`. Unknown
    headroom is a hard stop for automatic selection; an explicit `--harness` may
    proceed because that is attended, not a silent fallback.
    """
    if _is_exhausted(pool) and not allow_exhausted:
        note = f" ({pool.note})" if pool.note else ""
        if (
            pool.used_percent is not None
            and pool.used_percent >= EXHAUSTED_USED_PERCENT
        ):
            return (
                f"{pool.name} is at {pool.used_percent:g}% used "
                f"(threshold {EXHAUSTED_USED_PERCENT:g}%){note}"
            )
        return f"{pool.name} is exhausted{note}"
    if require_known_headroom and pool.used_percent is None:
        if allow_exhausted and _is_exhausted(pool):
            return None
        return f"{pool.name} headroom is unknown"
    return None


def remaining_percent(pool: PoolState) -> float | None:
    """The counter, not the gate. Exhaustion is `_blocked`; this is ranking input."""
    if pool.used_percent is None:
        return None
    return 100.0 - pool.used_percent


def headroom_freshness_refusal(
    pools: Sequence[PoolState], *, now: datetime
) -> str | None:
    """Refuse routing on missing, future, malformed, or stale observations."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("headroom check time must be timezone-aware")
    if not pools:
        return "headroom snapshot has no pools"
    current = now.astimezone(timezone.utc)
    for pool in pools:
        try:
            observed = datetime.fromisoformat(pool.observed_at)
        except ValueError:
            return f"{pool.name} headroom observation timestamp is malformed"
        if observed.tzinfo is None or observed.utcoffset() is None:
            return f"{pool.name} headroom observation timestamp has no timezone"
        age = current - observed.astimezone(timezone.utc)
        if age < timedelta(0):
            return f"{pool.name} headroom observation is in the future"
        if age > HEADROOM_MAX_AGE:
            return f"{pool.name} headroom observation is stale"
    return None


def _as_percent(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("used_percent cannot be a boolean")
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        if value != value:  # NaN
            raise ValueError("used_percent is not a number")
        return value
    raise ValueError(f"used_percent must be a number, got {type(value).__name__}")


def pools_from_mapping(raw: object) -> tuple[PoolState, ...]:
    """Parse an operator headroom snapshot. Missing pools fall back to the default."""
    if not isinstance(raw, dict):
        raise ValueError("headroom snapshot must be an object")
    observed_at = raw.get("observed_at", DEFAULT_OBSERVED_AT)
    source = raw.get("source", "headroom file")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at must be a non-empty string")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    pools_raw = raw.get("pools")
    if not isinstance(pools_raw, dict):
        raise ValueError("headroom snapshot must carry a pools object")

    by_name: dict[str, PoolState] = {item.name: item for item in DEFAULT_POOLS}
    for name, body in pools_raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("pool name must be a non-empty string")
        if not isinstance(body, dict):
            raise ValueError(f"pool {name} must be an object")
        used = _as_percent(body.get("used_percent"))
        note_raw = body.get("note", "")
        if note_raw is None:
            note = ""
        elif isinstance(note_raw, str):
            note = note_raw
        else:
            raise ValueError(f"pool {name} note must be a string")
        exhausted_raw = body.get("exhausted")
        if exhausted_raw is None:
            exhausted_flag = False
        elif isinstance(exhausted_raw, bool):
            exhausted_flag = exhausted_raw
        else:
            raise ValueError(f"pool {name} exhausted must be a boolean")
        exhausted = exhausted_flag or (
            used is not None and used >= EXHAUSTED_USED_PERCENT
        )
        by_name[name] = PoolState(
            name=name,
            used_percent=used,
            exhausted=exhausted,
            note=note,
            observed_at=observed_at,
            source=source,
        )
    # Keep default order, then any extra pools.
    ordered = [by_name[item.name] for item in DEFAULT_POOLS]
    extras = [
        by_name[name]
        for name in by_name
        if name not in {item.name for item in DEFAULT_POOLS}
    ]
    return tuple(ordered + extras)


def load_pools(path: Path | None) -> tuple[PoolState, ...]:
    if path is None or not path.exists():
        return DEFAULT_POOLS
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"headroom file {path} is unreadable: {exc}") from exc
    return pools_from_mapping(raw)


def snapshot_mapping(pools: Sequence[PoolState]) -> dict[str, object]:
    first = pools[0] if pools else None
    return {
        "observed_at": first.observed_at if first is not None else DEFAULT_OBSERVED_AT,
        "source": first.source if first is not None else DEFAULT_SOURCE,
        "pools": {
            item.name: {
                "used_percent": item.used_percent,
                "exhausted": item.exhausted,
                "note": item.note,
            }
            for item in pools
        },
    }

"""Refuse-only OpenRouter budget admissibility.

A budget permission is necessary but not sufficient authority to spend. This module has no
provider, credential or network capability; the remaining ADR-0019 conditions belong to a
future outer admission boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, DecimalException, Inexact, Rounded, localcontext
from pathlib import Path
from typing import Literal

from .events import (
    BUDGET_STATE_KIND,
    BUDGET_RESERVATION_ACTOR,
    METERED_CURRENCY,
    METERED_PROVIDER,
    SCHEMA_VERSION,
    SPEND_RESERVED_KIND,
    Event,
    EventError,
    Rejection,
    _budget_transaction,
    append,
    read_all,
    rejection_digest,
)

Period = Literal["weekly", "monthly"]

# ponytail: fixed freshness window; replace only when measured reconciliation latency
# supports a provider-specific value without turning staleness into a loosenable knob.
_STATE_MAX_AGE = timedelta(minutes=15)
_MONEY_PRECISION = 64


@dataclass(frozen=True)
class Ceiling:
    period: Period
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class AccountCap:
    """A limit the principal set at the vendor, outside this repository.

    ADR-0044 is explicit that the harness "cannot read it, cannot enforce it and must not
    assume it". So it is never a default and never a safety net: it exists only so that a
    ceiling the principal configures here can be checked against the figure he says he set
    there, and refused when it is higher. Declaring one is optional; declaring a false one
    is worse than declaring none, which is why nothing infers it.
    """

    period: Period
    amount: Decimal
    currency: str


def within_cap(
    cap: AccountCap | None, ceilings: Sequence[Ceiling]
) -> BudgetRefusal | None:
    """V0-31: a configured ceiling may not exceed the declared account cap.

    Refuses rather than clamps. Silently lowering a ceiling to the cap would let a
    configuration that asks for more than the principal allows still run, just quietly --
    and the operator would never learn that the file they edited does not say what the
    harness is doing. A boundary that edits your request instead of rejecting it is not a
    boundary, it is a preference.

    No currency conversion happens here, ever. A cap in one currency and a ceiling in
    another cannot be compared without a rate, and a rate this module invented would be a
    number nobody measured standing between the principal and his money.
    """
    if cap is None:
        return None
    if (
        not isinstance(cap, AccountCap)
        or cap.period not in ("weekly", "monthly")
        or not isinstance(cap.amount, Decimal)
        or not cap.amount.is_finite()
        or cap.amount < 0
        or not isinstance(cap.currency, str)
        or not cap.currency.strip()
    ):
        return BudgetRefusal("account cap is malformed")
    for ceiling in ceilings:
        if ceiling.currency != cap.currency:
            return BudgetRefusal(
                f"ceiling is in {ceiling.currency} and the account cap is in "
                f"{cap.currency}; no conversion is performed"
            )
        if ceiling.amount > cap.amount:
            return BudgetRefusal(
                f"{ceiling.period} ceiling {ceiling.amount} exceeds the declared "
                f"{cap.period} account cap {cap.amount} {cap.currency}"
            )
    return None


@dataclass(frozen=True)
class SpendRequest:
    run_id: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class BudgetPermission:
    record: dict[str, object]


@dataclass(frozen=True)
class BudgetRefusal:
    reason: str


BudgetDecision = BudgetPermission | BudgetRefusal


def check_budget(
    log_dir: Path,
    ceilings: Sequence[Ceiling],
    request: object,
) -> BudgetDecision:
    """Atomically record budget admissibility; never call or authorise a provider."""
    if not isinstance(request, SpendRequest):
        return BudgetRefusal("request is malformed")
    try:
        configured = tuple(ceilings)
    except Exception:
        return BudgetRefusal("ceiling configuration is malformed")
    invalid = _invalid_request(configured, request)
    if invalid is not None:
        return invalid
    if log_dir.exists() and not log_dir.is_dir():
        return BudgetRefusal("budget state is unreadable")
    if not log_dir.is_dir():
        return BudgetRefusal("budget state is absent")

    try:
        # ponytail: the shared lock file is the smallest cross-platform serialiser. A stale
        # lock fails closed; add owner/lease recovery only if crashes become operationally noisy.
        with _budget_transaction(log_dir):
            return _check_and_record(log_dir, configured, request)
    except FileExistsError:
        return BudgetRefusal("budget state is busy")
    except OSError:
        return BudgetRefusal("budget state is unreadable")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _check_and_record(
    log_dir: Path,
    ceilings: Sequence[Ceiling],
    request: SpendRequest,
) -> BudgetDecision:
    decision = _check_locked(log_dir, ceilings, request)
    if not isinstance(decision, BudgetPermission):
        return decision
    if not _permission_is_current(decision, ceilings, _utc_now()):
        return BudgetRefusal("budget state is stale")
    stamp = decision.record.get("ts")
    if not isinstance(stamp, str):
        return BudgetRefusal("reservation could not be recorded")
    try:
        append(log_dir / f"{stamp[:10]}.jsonl", decision.record)
    except (EventError, OSError, UnicodeError):
        return BudgetRefusal("reservation could not be recorded")
    if not _permission_is_current(decision, ceilings, _utc_now()):
        return BudgetRefusal("budget state is stale")
    return decision


def _invalid_request(
    ceilings: Sequence[Ceiling], request: SpendRequest
) -> BudgetRefusal | None:
    if not ceilings:
        return BudgetRefusal("no weekly or monthly ceiling is configured")
    if not isinstance(request.run_id, str) or not request.run_id.strip():
        return BudgetRefusal("request must name a non-empty run_id")
    if (
        not isinstance(request.amount, Decimal)
        or not request.amount.is_finite()
        or request.amount <= 0
    ):
        return BudgetRefusal("request amount must be a finite positive Decimal")
    periods: set[str] = set()
    for ceiling in ceilings:
        if (
            not isinstance(ceiling, Ceiling)
            or ceiling.period not in ("weekly", "monthly")
            or ceiling.period in periods
            or not isinstance(ceiling.amount, Decimal)
            or not ceiling.amount.is_finite()
            or ceiling.amount < 0
            or not isinstance(ceiling.currency, str)
        ):
            return BudgetRefusal("ceiling configuration is malformed")
        periods.add(ceiling.period)
    if (
        not isinstance(request.currency, str)
        or request.currency != METERED_CURRENCY
        or any(ceiling.currency != METERED_CURRENCY for ceiling in ceilings)
    ):
        return BudgetRefusal(
            "request, ceilings and state must use one currency; no conversion is performed"
        )
    return None


def _check_locked(
    log_dir: Path,
    ceilings: Sequence[Ceiling],
    request: SpendRequest,
) -> BudgetDecision:
    try:
        events, rejected = read_all(log_dir)
    except (OSError, UnicodeError):
        return BudgetRefusal("budget state is unreadable")
    states = [event for event in events if event.kind == BUDGET_STATE_KIND]
    if not states:
        return BudgetRefusal(
            "budget state is unreadable" if rejected else "budget state is absent"
        )
    try:
        state = max(enumerate(states), key=_state_order)[1]
    except (KeyError, OverflowError, TypeError, ValueError):
        return BudgetRefusal("budget state is malformed")
    acknowledged = _acknowledged_rejections(state, rejected)
    if acknowledged is None:
        return BudgetRefusal("budget state is unreadable")
    digest = state.data.get("rejection_digest")
    if not isinstance(digest, str) or digest != rejection_digest(acknowledged):
        return BudgetRefusal("budget state is unreadable")
    return _decide(state, events, ceilings, request, _utc_now())


def _state_order(item: tuple[int, Event]) -> tuple[datetime, datetime, int]:
    index, event = item
    observed = datetime.fromisoformat(event.data["observed_at"]).astimezone(timezone.utc)
    stamped = datetime.fromisoformat(event.raw["ts"]).astimezone(timezone.utc)
    return observed, stamped, index


def _acknowledged_rejections(
    state: Event, rejected: list[Rejection]
) -> list[Rejection] | None:
    if state.path is None or state.line is None:
        return None
    cursor = (Path(state.path).name, state.line)
    acknowledged = []
    for item in rejected:
        item_cursor = (Path(item.path).name, item.line)
        if item_cursor > cursor:
            return None
        acknowledged.append(item)
    return acknowledged


def _state_is_stale(
    observed: datetime, current: datetime, ceilings: Sequence[Ceiling]
) -> bool:
    age = current - observed
    return (
        age < timedelta(0)
        or age > _STATE_MAX_AGE
        or (
            any(c.period == "weekly" for c in ceilings)
            and current.isocalendar()[:2] != observed.isocalendar()[:2]
        )
        or (
            any(c.period == "monthly" for c in ceilings)
            and (current.year, current.month) != (observed.year, observed.month)
        )
    )


def _permission_is_current(
    permission: BudgetPermission,
    ceilings: Sequence[Ceiling],
    now: datetime,
) -> bool:
    data = permission.record.get("data")
    if not isinstance(data, dict) or now.tzinfo is None:
        return False
    observed_at = data.get("state_observed_at")
    if not isinstance(observed_at, str):
        return False
    try:
        parsed = datetime.fromisoformat(observed_at)
        if parsed.tzinfo is None:
            return False
        observed = parsed.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        return False
    return not _state_is_stale(
        observed, now.astimezone(timezone.utc), ceilings
    )


def _decide(
    state: Event,
    events: Sequence[Event],
    ceilings: Sequence[Ceiling],
    request: SpendRequest,
    now: datetime,
) -> BudgetDecision:
    data = state.data
    try:
        weekly_spent = Decimal(data["weekly_spent"])
        monthly_spent = Decimal(data["monthly_spent"])
        currency = data["currency"]
        observed_at = datetime.fromisoformat(data["observed_at"])
    except (DecimalException, KeyError, TypeError, ValueError):
        return BudgetRefusal("budget state is malformed")
    if now.tzinfo is None or observed_at.tzinfo is None:
        return BudgetRefusal("budget state is malformed")
    current = now.astimezone(timezone.utc)
    observed = observed_at.astimezone(timezone.utc)
    if _state_is_stale(observed, current, ceilings):
        return BudgetRefusal("budget state is stale")
    if (
        data.get("provider") != METERED_PROVIDER
        or not isinstance(currency, str)
        or currency != request.currency
    ):
        return BudgetRefusal(
            "request, ceilings and state must use one currency; no conversion is performed"
        )
    if (
        not weekly_spent.is_finite()
        or weekly_spent < 0
        or not monthly_spent.is_finite()
        or monthly_spent < 0
    ):
        return BudgetRefusal("budget state is malformed")
    if not _daily_path_matches(state):
        return BudgetRefusal("budget state is unreadable")

    try:
        with localcontext() as money:
            # ponytail: fixed exact precision makes ambient Decimal settings irrelevant.
            # Values needing more precision refuse; widen only for observed provider values.
            money.prec = _MONEY_PRECISION
            money.traps[Inexact] = True
            money.traps[Rounded] = True
            weekly_reserved = Decimal(0)
            monthly_reserved = Decimal(0)
            for event in events:
                if event.kind != SPEND_RESERVED_KIND:
                    continue
                if not _daily_path_matches(event):
                    return BudgetRefusal("budget state is unreadable")
                stamped = datetime.fromisoformat(event.raw["ts"]).astimezone(
                    timezone.utc
                )
                amount = Decimal(event.data["amount"])
                if stamped > current:
                    return BudgetRefusal("budget state is unreadable")
                if current.isocalendar()[:2] == stamped.isocalendar()[:2]:
                    weekly_reserved += amount
                if (current.year, current.month) == (stamped.year, stamped.month):
                    monthly_reserved += amount

            weekly = next(
                (ceiling for ceiling in ceilings if ceiling.period == "weekly"), None
            )
            if (
                weekly is not None
                and weekly_spent + weekly_reserved + request.amount > weekly.amount
            ):
                return BudgetRefusal("weekly ceiling would be breached")
            monthly = next(
                (ceiling for ceiling in ceilings if ceiling.period == "monthly"), None
            )
            if (
                monthly is not None
                and monthly_spent + monthly_reserved + request.amount > monthly.amount
            ):
                return BudgetRefusal("monthly ceiling would be breached")
    except (DecimalException, KeyError, TypeError, ValueError):
        return BudgetRefusal("budget values cannot be compared")
    return BudgetPermission(
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": SPEND_RESERVED_KIND,
            "actor": BUDGET_RESERVATION_ACTOR,
            "data": {
                "provider": METERED_PROVIDER,
                "run_id": request.run_id,
                "amount": str(request.amount),
                "currency": currency,
                "state_observed_at": observed.isoformat(),
            },
        }
    )


def _daily_path_matches(event: Event) -> bool:
    stamp = event.raw.get("ts")
    return (
        event.path is not None
        and isinstance(stamp, str)
        and Path(event.path).name == f"{stamp[:10]}.jsonl"
    )

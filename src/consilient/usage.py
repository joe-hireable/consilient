"""Usage, limits and spend for every configured provider, in one place.

**This is PRODUCT.** It is a general capability: a provider-agnostic model of what a
subscription has left and what a metered vendor has cost, with pluggable collectors. It
contains no account, no credential and no figure belonging to any particular user. The
instance configuration that names *your* providers and *your* ceilings lives outside the
repository; see `.harness/limits.example.json` for its shape.

Three things this module refuses to do, each because doing it is the way this goes wrong:

1. **It never flattens a subscription and a metered charge into one number.** A flat-fee
   quota has a *window* and a *reset time* and no currency; metered spend has a *currency*
   and no window. `backends.md` puts it plainly: "Resource windows remain provider-native
   and separately keyed; a five-hour, seven-day or monthly bucket is not flattened into
   one generic reset." So `Quota` and `Spend` are different types and a provider carries
   however many of each it actually has -- usually zero.

2. **It never invents a number.** Where a provider exposes no machine-readable individual
   counter -- which, measured on this machine on 21 August 2026, is *most* of them -- the
   answer is the string "unavailable" and a reason, never a zero. `events.validate`
   enforces this at the writer (V0-30): an event whose status is not `ok` cannot carry a
   figure at all, so there is no code path that reports headroom nobody observed.

3. **It never reaches the network or reads a credential.** Every collector here is a pure
   read of a local file, and `tests/test_budget.py` proves the whole of `src/consilient/`
   has no outbound capability. Acquiring a provider payload -- running `codex app-server`,
   capturing a status line -- is an out-of-tree, instance-side job. This module parses
   what such a probe leaves in the payload directory and says honestly what it found.

The collector contract, for anything rendering this:

    Collector = Callable[[Sources], ProviderUsage]
    COLLECTORS: dict[str, Collector]

Add a provider by adding one function and one dict entry. A collector must return a
`ProviderUsage` for every input -- including "the payload is not there" -- and must never
raise: a provider that is absent degrades to `not_configured`, which is a fact about the
installation, while `unavailable` is a fact about the provider.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, DecimalException
from pathlib import Path
from typing import Literal

from . import budget
from .events import (
    BUDGET_STATE_KIND,
    METERED_PROVIDER,
    SCHEMA_VERSION,
    USAGE_ACTOR,
    USAGE_KIND,
    EventPayload,
    append,
    read_all,
)

Provenance = Literal["measured", "cited", "asserted"]
Status = Literal["ok", "unavailable", "not_configured"]
Kind = Literal["subscription", "metered"]

DEFAULT_PAYLOADS = Path(".harness/usage")
DEFAULT_LIMITS = Path(".harness/limits.json")


@dataclass(frozen=True)
class Quota:
    """One flat-fee subscription window. Carries no currency: nothing here is money.

    `window` is the provider's own label for the bucket, not a normalised one. A Codex
    seven-day window and a Claude five-hour window are different measurements and are
    kept that way; `resets_at` is the field a human actually wants and is never dropped.
    """

    window: str
    used_fraction: Decimal
    resets_at: datetime | None
    provenance: Provenance


@dataclass(frozen=True)
class Spend:
    """Metered money over a period. Carries no window fraction: nothing here is a quota."""

    amount: Decimal
    currency: str
    period: budget.Period
    provenance: Provenance


@dataclass(frozen=True)
class ProviderUsage:
    """What one provider would say about itself, including that it cannot say anything.

    `status` separates two absences that look identical on a dashboard and are not:
    `not_configured` means this installation has no such provider, and `unavailable`
    means the provider exists and exposes no readable figure. Only `unavailable` is a
    statement about the vendor, and only it should ever be argued with.
    """

    provider: str
    kind: Kind
    status: Status
    detail: str
    observed_at: datetime | None = None
    quotas: tuple[Quota, ...] = ()
    spend: tuple[Spend, ...] = ()


@dataclass(frozen=True)
class Sources:
    """Where a collector may read. Two directories, both local, neither a credential store.

    `payloads` is where an out-of-tree probe drops a provider's own response verbatim;
    `log` is the trajectory, which is itself the authoritative record of metered spend.
    """

    payloads: Path = field(default_factory=lambda: DEFAULT_PAYLOADS)
    log: Path = field(default_factory=lambda: Path(".harness/log"))


Collector = Callable[[Sources], ProviderUsage]


# --------------------------------------------------------------------------- payload reads
def _read_payload(
    sources: Sources, name: str
) -> tuple[EventPayload | None, str | None]:
    """(payload, why_it_could_not_be_used). Absent is not an error; unreadable is."""
    path = sources.payloads / name
    try:
        if not path.is_file():
            return None, None
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None, f"{name} could not be read"
    except json.JSONDecodeError:
        return None, f"{name} is not valid JSON"
    if not isinstance(raw, dict):
        return None, f"{name} is not a JSON object"
    return raw, None


def _absent(provider: str, kind: Kind, name: str) -> ProviderUsage:
    return ProviderUsage(
        provider=provider,
        kind=kind,
        status="not_configured",
        detail=f"no {name} in the payload directory; nothing has probed this provider",
    )


def _unreadable(provider: str, kind: Kind, why: str) -> ProviderUsage:
    return ProviderUsage(provider=provider, kind=kind, status="unavailable", detail=why)


def _fraction(value: object) -> Decimal | None:
    """A percent as the provider gave it, to an exact fraction. Never a guess."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        percent = Decimal(str(value))
    except DecimalException:
        return None
    if not percent.is_finite() or percent < 0 or percent > 100:
        return None
    return percent.scaleb(-2)


def _reset(value: object) -> datetime | None:
    """Unix seconds or RFC3339, both seen in the wild. Anything else is not a reset time."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value)
            return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (OSError, OverflowError, ValueError):
        return None
    return None


# ------------------------------------------------------------------------------ collectors
def collect_codex(sources: Sources) -> ProviderUsage:
    """OpenAI Codex. The one subscription whose headroom schema was measured here.

    EXP-07 queried `codex app-server --stdio` with `account/rateLimits/read` and committed
    the response: `result.rateLimits.primary` carries `usedPercent`, `resetsAt` and
    `windowDurationMins` (10080 = seven days). That is why this collector parses the
    vendor's payload verbatim rather than a normalised one -- there is no transformation
    step to get wrong -- and why its figures are tagged `measured`. [measured]
    """
    payload, why = _read_payload(sources, "codex.json")
    if why is not None:
        return _unreadable("codex", "subscription", why)
    if payload is None:
        return _absent("codex", "subscription", "codex.json")

    envelope = payload.get("result")
    limits = payload.get("rateLimits")
    if isinstance(envelope, dict) and isinstance(envelope.get("rateLimits"), dict):
        limits = envelope["rateLimits"]
    if not isinstance(limits, dict):
        return _unreadable(
            "codex",
            "subscription",
            "codex.json carries no rateLimits object; nothing was reported",
        )
    primary = limits.get("primary")
    if not isinstance(primary, dict):
        return _unreadable(
            "codex", "subscription", "codex.json rateLimits carries no primary window"
        )
    used = _fraction(primary.get("usedPercent"))
    if used is None:
        return _unreadable(
            "codex",
            "subscription",
            "codex.json primary window carries no usable usedPercent",
        )
    minutes = primary.get("windowDurationMins")
    window = (
        f"{minutes}m"
        if isinstance(minutes, int) and not isinstance(minutes, bool) and minutes > 0
        else "unnamed"
    )
    plan = limits.get("planType")
    return ProviderUsage(
        provider="codex",
        kind="subscription",
        status="ok",
        detail=f"plan {plan!r} via account/rateLimits/read"
        if plan
        else "account/rateLimits/read",
        observed_at=_reset(payload.get("observed_at")),
        quotas=(
            Quota(
                window=window,
                used_fraction=used,
                resets_at=_reset(primary.get("resetsAt")),
                provenance="measured",
            ),
        ),
    )


def collect_claude(sources: Sources) -> ProviderUsage:
    """Claude Max. Schema never verified here, so every figure is tagged `cited`.

    Anthropic documents five-hour and seven-day utilisation and reset fields on the status
    line, and this repository has never parsed one: EXP-27 recorded the quota surface as
    the *string* "status_line_json" inferred from the CLI being installed. So the payload
    read here is a normalised one an instance-side probe writes -- claiming to parse a wire
    format nobody has seen would be asserting a schema as measured. [cited]

    The `cited` tag is not pedantry. It is the difference between "Anthropic says this
    field exists" and "we read this field", and a reader deciding whether to trust a
    number needs to know which one they are looking at.
    """
    payload, why = _read_payload(sources, "claude.json")
    if why is not None:
        return _unreadable("claude", "subscription", why)
    if payload is None:
        return _absent("claude", "subscription", "claude.json")

    windows = payload.get("windows")
    if not isinstance(windows, list) or not windows:
        return _unreadable(
            "claude",
            "subscription",
            "claude.json carries no windows list; the status-line payload was not captured",
        )
    quotas: list[Quota] = []
    for entry in windows:
        if not isinstance(entry, dict):
            continue
        used = _fraction(entry.get("used_percentage"))
        label = entry.get("window")
        if used is None or not isinstance(label, str) or not label.strip():
            continue
        quotas.append(
            Quota(
                window=label.strip(),
                used_fraction=used,
                resets_at=_reset(entry.get("resets_at")),
                provenance="cited",
            )
        )
    if not quotas:
        return _unreadable(
            "claude",
            "subscription",
            "claude.json windows carry no usable window/used_percentage pair",
        )
    return ProviderUsage(
        provider="claude",
        kind="subscription",
        status="ok",
        detail="status-line utilisation; schema is vendor-documented, not verified here",
        observed_at=_reset(payload.get("observed_at")),
        quotas=tuple(quotas),
    )


# Providers measured to expose no individual remaining-allowance counter at all. The
# payload file's presence says a probe ran; the verdict does not depend on what is in it,
# because what is in it never contains a headroom figure. Each carries the finding that
# would have to be overturned for this to change -- an "unavailable" with no reason is
# just as unfalsifiable as an invented number.
_NO_COUNTER: dict[str, tuple[str, str]] = {
    "cursor": (
        "cursor.json",
        "no individual remaining-allowance surface: `cursor-agent about --format json` "
        "returns subscriptionTier with no quota, no consumed figure and no reset window "
        "[measured 2026-08-20]",
    ),
    "grok": (
        "grok.json",
        "no individual quota counter: `grok inspect --json` exposes configuration and "
        "policy but no remaining-quota percentage, allowance counter or reset timestamp, "
        "and the only usage view is the interactive TUI [cited]",
    ),
}


def _no_counter(provider: str) -> Collector:
    name, reason = _NO_COUNTER[provider]

    def collector(sources: Sources) -> ProviderUsage:
        payload, why = _read_payload(sources, name)
        if why is not None:
            return _unreadable(provider, "subscription", why)
        if payload is None:
            return _absent(provider, "subscription", name)
        return _unreadable(provider, "subscription", reason)

    return collector


def collect_openrouter(sources: Sources) -> ProviderUsage:
    """The only permitted metered vendor (ADR-0044). Spend comes from the trajectory.

    Not from a live counter, deliberately. On 20 August 2026 OpenRouter's key-status
    counter read $0 immediately after a run and $0.045138255 once billing settled: the
    zero was a true counter value and a false statement about spend, and reading it live
    would reproduce exactly that. [measured] The `budget.state` events are timestamped
    observations with a known `observed_at`, so a stale figure is visible as stale rather
    than mistaken for a fresh zero.
    """
    try:
        if not sources.log.is_dir():
            return ProviderUsage(
                provider=METERED_PROVIDER,
                kind="metered",
                status="not_configured",
                detail="no trajectory directory; no metered spend has been recorded",
            )
        events, _ = read_all(sources.log)
    except (OSError, UnicodeError):
        return _unreadable(
            METERED_PROVIDER, "metered", "the trajectory could not be read"
        )

    states = [event for event in events if event.kind == BUDGET_STATE_KIND]
    if not states:
        return _unreadable(
            METERED_PROVIDER,
            "metered",
            "no budget.state observation in the trajectory; spend is unknown, not zero",
        )
    latest = states[-1]
    try:
        weekly = Decimal(latest.data["weekly_spent"])
        monthly = Decimal(latest.data["monthly_spent"])
        currency = latest.data["currency"]
        observed = datetime.fromisoformat(latest.data["observed_at"])
    except (DecimalException, KeyError, TypeError, ValueError):
        return _unreadable(
            METERED_PROVIDER,
            "metered",
            "the latest budget.state observation is malformed",
        )
    return ProviderUsage(
        provider=METERED_PROVIDER,
        kind="metered",
        status="ok",
        detail="latest budget.state observation in the trajectory",
        observed_at=observed.astimezone(timezone.utc),
        spend=(
            Spend(weekly, currency, "weekly", "measured"),
            Spend(monthly, currency, "monthly", "measured"),
        ),
    )


COLLECTORS: dict[str, Collector] = {
    "claude": collect_claude,
    "codex": collect_codex,
    "cursor": _no_counter("cursor"),
    "grok": _no_counter("grok"),
    METERED_PROVIDER: collect_openrouter,
}


# ------------------------------------------------------------------------ the JSON contract
def as_payload(usage: ProviderUsage) -> EventPayload:
    """One provider, as the dashboard and the trajectory both see it."""
    return {
        "provider": usage.provider,
        "kind": usage.kind,
        "status": usage.status,
        "detail": usage.detail,
        "observed_at": usage.observed_at.isoformat() if usage.observed_at else None,
        "quotas": [
            {
                "window": quota.window,
                "used_fraction": str(quota.used_fraction),
                "resets_at": quota.resets_at.isoformat() if quota.resets_at else None,
                "provenance": quota.provenance,
            }
            for quota in usage.quotas
        ],
        "spend": [
            {
                "amount": str(item.amount),
                "currency": item.currency,
                "period": item.period,
                "provenance": item.provenance,
            }
            for item in usage.spend
        ],
    }


def snapshot(sources: Sources | None = None) -> EventPayload:
    """Every configured provider in one place. The shape a dashboard renders.

    {"observed_at": RFC3339, "providers": [ <as_payload>, ... ]}

    Sorted by provider so two snapshots of the same state compare equal.
    """
    where = sources if sources is not None else Sources()
    providers = [COLLECTORS[name](where) for name in sorted(COLLECTORS)]
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "providers": [as_payload(usage) for usage in providers],
    }


def fake_snapshot() -> EventPayload:
    """A snapshot with no providers configured -- for building a view against.

    Exercises every case a renderer has to handle: a subscription quota with a reset, two
    metered spend figures in one currency, a provider that exists but exposes nothing,
    and a provider that is simply not installed. The figures are obviously fictitious and
    tagged `asserted`, so nothing here can be mistaken for a measurement if it leaks into
    a screenshot.
    """
    reset = datetime(2026, 8, 28, 9, 0, tzinfo=timezone.utc)
    return {
        "observed_at": datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc).isoformat(),
        "providers": [
            as_payload(usage)
            for usage in (
                ProviderUsage(
                    provider="fake-subscription",
                    kind="subscription",
                    status="ok",
                    detail="fabricated sample; not a measurement of anything",
                    observed_at=reset,
                    quotas=(
                        Quota("10080m", Decimal("0.05"), reset, "asserted"),
                        Quota("300m", Decimal("0.42"), reset, "asserted"),
                    ),
                ),
                ProviderUsage(
                    provider="fake-metered",
                    kind="metered",
                    status="ok",
                    detail="fabricated sample; not a measurement of anything",
                    observed_at=reset,
                    spend=(
                        Spend(Decimal("1.25"), "USD", "weekly", "asserted"),
                        Spend(Decimal("4.00"), "USD", "monthly", "asserted"),
                    ),
                ),
                ProviderUsage(
                    provider="fake-no-counter",
                    kind="subscription",
                    status="unavailable",
                    detail="this provider exposes no individual remaining-allowance counter",
                ),
                ProviderUsage(
                    provider="fake-absent",
                    kind="subscription",
                    status="not_configured",
                    detail="nothing has probed this provider on this installation",
                ),
            )
        ],
    }


def record(log_dir: Path, snap: EventPayload) -> int:
    """Put a snapshot in the append-only trajectory, through the one writer. Returns the count.

    Every provider gets its own event, including the ones that reported nothing. A
    provider that vanished from a snapshot and a provider that reported "unavailable" are
    different facts, and only writing the readable ones would erase the difference.
    """
    stamp = datetime.now(timezone.utc)
    path = log_dir / f"{stamp.date().isoformat()}.jsonl"
    written = 0
    for provider in snap["providers"]:
        append(
            path,
            {
                "v": SCHEMA_VERSION,
                "ts": stamp.isoformat(),
                "event": USAGE_KIND,
                "actor": USAGE_ACTOR,
                "data": dict(provider),
            },
        )
        written += 1
    return written


# ------------------------------------------------------------------------- instance limits
def load_limits(
    path: Path | None = None,
) -> tuple[budget.Ceiling, ...] | budget.BudgetRefusal:
    """The single place harness spend ceilings come from. Fail-closed at every step.

    Ceilings were previously whatever a caller passed in, which is the shape working
    principle 3 warns about: a boundary with several access paths is not a boundary.
    Everything that spends now reads its ceilings here, and here refuses an absent file, a
    malformed one, one that sets neither period, and one that asks for more than the
    account cap the principal declared.

    Absent is refused rather than defaulted. Fail-closed means no ceiling is not
    "unlimited", it is "no" -- and a default this module chose would be a number the
    principal never approved standing where his own should be.
    """
    where = path if path is not None else DEFAULT_LIMITS
    try:
        if not where.is_file():
            return budget.BudgetRefusal(f"no spend limits configured at {where}")
        raw = json.loads(where.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return budget.BudgetRefusal("spend limits could not be read")
    except json.JSONDecodeError:
        return budget.BudgetRefusal("spend limits are not valid JSON")
    if not isinstance(raw, dict):
        return budget.BudgetRefusal("spend limits are malformed")

    entries = raw.get("ceilings")
    if not isinstance(entries, list) or not entries:
        return budget.BudgetRefusal("no weekly or monthly ceiling is configured")
    ceilings: list[budget.Ceiling] = []
    for entry in entries:
        parsed = _ceiling(entry)
        if parsed is None:
            return budget.BudgetRefusal("a configured ceiling is malformed")
        ceilings.append(parsed)

    declared = raw.get("account_cap")
    cap: budget.AccountCap | None = None
    if declared is not None:
        parsed_cap = _ceiling(declared)
        if parsed_cap is None:
            return budget.BudgetRefusal("account cap is malformed")
        cap = budget.AccountCap(
            parsed_cap.period, parsed_cap.amount, parsed_cap.currency
        )
    refusal = budget.within_cap(cap, ceilings)
    if refusal is not None:
        return refusal
    return tuple(ceilings)


def _ceiling(entry: object) -> budget.Ceiling | None:
    if not isinstance(entry, dict):
        return None
    period = entry.get("period")
    amount = entry.get("amount")
    currency = entry.get("currency")
    if period not in ("weekly", "monthly"):
        return None
    # A money value arrives as a string. A JSON float has already lost the exactness the
    # comparison against a ceiling depends on, so it is refused rather than rounded.
    if (
        not isinstance(amount, str)
        or not isinstance(currency, str)
        or not currency.strip()
    ):
        return None
    try:
        value = Decimal(amount)
    except DecimalException:
        return None
    if not value.is_finite() or value < 0:
        return None
    return budget.Ceiling(period, value, currency.strip())

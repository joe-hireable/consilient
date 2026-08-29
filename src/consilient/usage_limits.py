"""The single place harness spend ceilings come from -- money, not quota.

Nothing about provider allowance lives in this file, and that separation is the point. A
ceiling is cash the principal authorised, read from an instance file outside the
repository and capped by an account cap he declared; a quota is an allowance a vendor
grants, has no currency, and belongs to `usage_model.py`. Flattening the two would be
the same mistake at the configuration layer that `Quota` and `Spend` refuse to make at
the data layer.

Ceilings were previously whatever a caller passed in, which is the shape working
principle 3 warns about: a boundary with several access paths is not a boundary.
Everything that spends now reads them here.

`load_limits` carries the fail-closed rule, including for absence -- no ceiling is not
"unlimited", it is "no". `_ceiling` carries the narrower one: a money value arrives as a
string, because a JSON float has already lost the exactness the comparison depends on."""

import json
from decimal import Decimal, DecimalException
from pathlib import Path
from . import budget
from .usage_model import (
    COLLECTORS,
    Collector,
    ProviderUsage,
    Quota,
    Sources,
    Spend,
)


__all__ = [
    "COLLECTORS",
    "Collector",
    "DEFAULT_LIMITS",
    "ProviderUsage",
    "Quota",
    "Sources",
    "Spend",
    "load_limits",
]

DEFAULT_LIMITS = Path(".harness/limits.json")


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

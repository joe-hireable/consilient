"""The ceiling decision: whether a spend request fits under the configured ceilings,
given the reservations already appended to the trajectory. Every refusal in this file
names a ceiling or the request — a breach, no ceiling configured at all, an
unattributable run, a non-request object, an amount that is not a finite positive
Decimal, a currency that would need converting, or a ceiling configuration that evades
its own Literal type at runtime.

Reservations accumulate and are not released cheaply: a newer snapshot does not release
one that has not been reconciled, and neither does an observation that arrives later but
was taken earlier, because a released reservation is money authorised twice. The ceiling
sequence is snapshotted once, so a configuration that changes between iterations cannot
widen the limit mid-decision, and two concurrent permissions cannot jointly
oversubscribe.

The decimal tests belong here for the same reason: the comparison must refuse rather
than overflow on extreme exponents, must not round a positive request away at a large
exhausted ceiling, and must not change its answer because the ambient decimal context
was set to a lower precision."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import pytest
from consilient.events import (
    append,
    read_all,
    validate,
)
from budget_helpers import (
    budget_state,
    write_state,
)


def test_no_ceilings_refuses(tmp_path):
    from consilient import budget

    request = budget.SpendRequest("run-1", Decimal("1.00"), "USD")

    decision = budget.check_budget(tmp_path, (), request)

    assert isinstance(decision, budget.BudgetRefusal)
    assert decision.reason == "no weekly or monthly ceiling is configured"


def test_weekly_ceiling_alone_permits_and_persists_its_attribution(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now, weekly="2.00", monthly="99.00")
    before = log.read_bytes()
    request = budget.SpendRequest("run-42", Decimal("1.25"), "USD")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("4.00"), "USD"),),
        request,
    )

    assert isinstance(decision, budget.BudgetPermission)
    assert decision.record["event"] == "spend.reserved"
    assert decision.record["data"] == {
        "provider": "openrouter",
        "run_id": "run-42",
        "amount": "1.25",
        "currency": "USD",
        "state_observed_at": now.isoformat(),
    }
    assert "human_decision" not in decision.record["data"]
    assert validate(decision.record) == decision.record
    assert log.read_bytes() != before
    events, rejected = read_all(tmp_path)
    assert not rejected
    assert events[-1].raw == decision.record


@pytest.mark.parametrize(
    ("weekly_spent", "monthly_spent", "expected"),
    (
        ("9.00", "1.00", "weekly ceiling would be breached"),
        ("1.00", "9.00", "monthly ceiling would be breached"),
    ),
)
def test_breaching_either_configured_ceiling_refuses(
    tmp_path, weekly_spent, monthly_spent, expected
):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly=weekly_spent, monthly=monthly_spent)

    decision = budget.check_budget(
        tmp_path,
        (
            budget.Ceiling("weekly", Decimal("10.00"), "USD"),
            budget.Ceiling("monthly", Decimal("10.00"), "USD"),
        ),
        budget.SpendRequest("run-limit", Decimal("2.00"), "USD"),
    )

    assert decision == budget.BudgetRefusal(expected)


def test_appended_reservations_accumulate_and_exact_ceiling_is_allowed(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1.00", monthly="1.00")
    ceiling = (budget.Ceiling("weekly", Decimal("3.00"), "USD"),)

    exact = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-exact", Decimal("2.00"), "USD"),
    )
    assert isinstance(exact, budget.BudgetPermission)

    over = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-over", Decimal("0.01"), "USD"),
    )
    assert over == budget.BudgetRefusal("weekly ceiling would be breached")


def test_concurrent_permissions_cannot_jointly_oversubscribe(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)
    ceiling = (budget.Ceiling("weekly", Decimal("1.00"), "USD"),)

    def check(run_id):
        return budget.check_budget(
            tmp_path,
            ceiling,
            budget.SpendRequest(run_id, Decimal("0.75"), "USD"),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = list(pool.map(check, ("run-a", "run-b")))

    assert sum(isinstance(d, budget.BudgetPermission) for d in decisions) == 1
    events, rejected = read_all(tmp_path)
    assert not rejected
    assert sum(event.kind == "spend.reserved" for event in events) == 1


def test_new_snapshot_does_not_release_an_unreconciled_reservation(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now)
    ceiling = (budget.Ceiling("weekly", Decimal("5.00"), "USD"),)
    first = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-in-flight", Decimal("4.00"), "USD"),
    )
    assert isinstance(first, budget.BudgetPermission)
    append(log, budget_state(now, weekly="0.00", monthly="0.00"))

    second = budget.check_budget(
        tmp_path,
        ceiling,
        budget.SpendRequest("run-next", Decimal("2.00"), "USD"),
    )

    assert second == budget.BudgetRefusal("weekly ceiling would be breached")


def test_newest_observation_wins_over_a_later_delayed_snapshot(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    append(log, budget_state(now, weekly="5", observed_at=now - timedelta(seconds=2)))
    append(
        log,
        budget_state(
            now + timedelta(microseconds=1),
            weekly="0",
            observed_at=now - timedelta(seconds=10),
        ),
    )

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-delayed-state", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_ceiling_sequence_is_snapshotted_once(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="5")
    ceiling = budget.Ceiling("weekly", Decimal("5"), "USD")

    class ChangingCeilings:
        def __init__(self):
            self.iterations = 0

        def __len__(self):
            return 1

        def __iter__(self):
            self.iterations += 1
            return iter((ceiling,)) if self.iterations == 1 else iter(())

    decision = budget.check_budget(
        tmp_path,
        ChangingCeilings(),
        budget.SpendRequest("run-changing-config", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_request_without_an_attributable_run_refuses(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("   ", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("request must name a non-empty run_id")


def test_non_request_object_refuses(tmp_path):
    from consilient import budget

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        object(),
    )

    assert decision == budget.BudgetRefusal("request is malformed")


@pytest.mark.parametrize("amount", (Decimal("0"), Decimal("-1"), Decimal("NaN"), 0.1))
def test_non_positive_non_finite_or_binary_float_request_refuses(tmp_path, amount):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-money", amount, "USD"),
    )

    assert decision == budget.BudgetRefusal(
        "request amount must be a finite positive Decimal"
    )


def test_currencies_are_compared_exactly_and_never_converted(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, currency="USD")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "GBP"),),
        budget.SpendRequest("run-currency", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal(
        "request, ceilings and state must use one currency; no conversion is performed"
    )


@pytest.mark.parametrize(
    "ceilings",
    (
        (
            # Runtime validation must still reject values that evade the Literal type.
            lambda budget: (budget.Ceiling("daily", Decimal("5"), "USD"),)
        ),
        (
            lambda budget: (
                budget.Ceiling("weekly", Decimal("5"), "USD"),
                budget.Ceiling("weekly", Decimal("6"), "USD"),
            )
        ),
        (lambda budget: (budget.Ceiling("weekly", Decimal("NaN"), "USD"),)),
        (lambda budget: (budget.Ceiling("weekly", -1.0, "USD"),)),
        (lambda budget: (object(),)),
        (lambda budget: (budget.Ceiling("weekly", Decimal("1"), ["USD"]),)),
    ),
)
def test_malformed_ceiling_configuration_refuses(tmp_path, ceilings):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now)

    decision = budget.check_budget(
        tmp_path,
        ceilings(budget),
        budget.SpendRequest("run-config", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("ceiling configuration is malformed")


def test_extreme_decimal_exponents_refuse_instead_of_overflowing(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1e999999999", monthly="0")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("1e999999999"), "USD"),),
        budget.SpendRequest("run-overflow", Decimal("1e999999999"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget values cannot be compared")


def test_positive_request_cannot_round_away_at_a_large_exhausted_ceiling(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    exhausted = "9999999999999999999999999999"
    write_state(tmp_path, now, weekly=exhausted)

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal(exhausted), "USD"),),
        budget.SpendRequest("run-precision", Decimal("0.1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("weekly ceiling would be breached")


def test_ambient_decimal_precision_cannot_change_the_decision(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, weekly="1.01")
    with localcontext() as ambient:
        ambient.prec = 1
        decision = budget.check_budget(
            tmp_path,
            (budget.Ceiling("weekly", Decimal("1.02"), "USD"),),
            budget.SpendRequest("run-context", Decimal("0.01"), "USD"),
        )

    assert isinstance(decision, budget.BudgetPermission)

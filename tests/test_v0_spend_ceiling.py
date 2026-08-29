"""V0-31, V0-20 and V0-39: the controls by which this system could spend real money. No
ceiling is not "unlimited", it is "no" (ADR-0044), so an absent, unparseable, empty or
float-valued limits file refuses rather than falling back on a number the principal
never approved standing where his own should be — a JSON float has already lost the
exactness a money comparison depends on. A configured ceiling above the declared account
cap is refused and never clamped, because silently lowering it would let a configuration
asking for more than the principal allows still run, quietly, and a boundary that edits
your request instead of rejecting it is a preference. A cap in pounds against a ceiling
metered in dollars refuses rather than converting: there is no exchange rate in this
repository and there must not be one. The end-to-end test is what separates an enforced
ceiling from a displayed one — the breaching request comes back refused with nothing
reserved, and the permitted one's reservation counts against the next request. The loop
half is V0-20: the ceiling is enforced before the tick runs, so an exhausted budget
cannot execute the side effect and then discover the problem, and the reservation is
recorded before the tick is recorded as started. V0-39 is ADR-0056 D5 — On-Demand
Spending stays Disabled and only the principal may change that — shipped as a lint rule
rather than a convention (I1), with documentation still free to name the control it
forbids and the read-only usage oracle deliberately unblocked so EXP-94 can settle
ADR-0056."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient.events import (
    SCHEMA_VERSION,
    append,
    read_all,
)
from v0_invariants_helpers import (
    _loop,
    _loop_events,
    _loop_runner,
    _spend_scripts,
    write_budget_state,
)


def _budget_state(log_dir, weekly_spent, monthly_spent):
    from consilient.events import rejection_digest

    now = datetime.now(timezone.utc)
    log_dir.mkdir(parents=True, exist_ok=True)
    append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": "budget.state",
            "actor": "openrouter-probe",
            "data": {
                "provider": "openrouter",
                "currency": "USD",
                "weekly_spent": weekly_spent,
                "monthly_spent": monthly_spent,
                "observed_at": now.isoformat(),
                "rejection_digest": rejection_digest(read_all(log_dir)[1]),
            },
        },
    )


def test_a_loop_stops_rather_than_spending_past_its_ceiling(tmp_path):
    """V0-20, which the specification has declared since 19 August with no check.

    The ceiling is enforced before the tick runs, so an exhausted budget cannot execute the
    side effect and then discover the problem. No metered vendor is involved: the state the
    ceiling is measured against is a fixture, which is all a spend limit needs to be tested.
    """
    from decimal import Decimal

    from consilient import loop as loop_mod
    from consilient.budget import Ceiling

    runner = _loop_runner()
    marker = tmp_path / "spent.txt"
    loop = _loop(
        tmp_path,
        f"open({str(marker)!r}, 'a').write('x')",
        cost_per_tick=Decimal("2.00"),
        ceilings=(Ceiling("weekly", Decimal("10.00"), "USD"),),
    )
    _budget_state(loop.log_dir, weekly_spent="9.00", monthly_spent="9.00")

    result = runner.run(loop)

    assert not marker.exists(), "the loop spent past its ceiling"
    assert _loop_events(loop.log_dir, loop_mod.TICK_STARTED) == []
    stopped = _loop_events(loop.log_dir, loop_mod.LOOP_STOPPED)
    assert "weekly ceiling would be breached" in stopped[0].data["reason"]
    assert result["working"] is False


def test_a_permitted_metered_tick_records_its_reservation_before_it_runs(tmp_path):
    """The other half of V0-20: a tick inside the ceiling runs, and the spend is recorded."""
    from decimal import Decimal

    from consilient import loop as loop_mod
    from consilient.budget import Ceiling

    runner = _loop_runner()
    loop = _loop(
        tmp_path,
        "print('tick')",
        cost_per_tick=Decimal("2.00"),
        ceilings=(Ceiling("weekly", Decimal("10.00"), "USD"),),
    )
    _budget_state(loop.log_dir, weekly_spent="1.00", monthly_spent="1.00")

    runner.run(loop)

    reserved = _loop_events(loop.log_dir, "spend.reserved")
    assert [e.data["run_id"] for e in reserved] == ["probe#1"]
    assert reserved[0].data["amount"] == "2.00"
    started = _loop_events(loop.log_dir, loop_mod.TICK_STARTED)
    assert started and started[0].line > reserved[0].line, (
        "the tick was recorded as started before its spend was reserved"
    )


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

import check_no_spend_escalation as spend  # noqa: E402


def test_v0_39_a_spend_escalation_call_is_caught_and_located():
    """The token is taken from the checker, so this test cannot drift from what it enforces."""
    call = f"client.{spend.BANNED[0]}(9999)"
    found = spend.scan_text("src/consilient/router.py", "x = 1\n" + call)

    assert found == [("src/consilient/router.py", 2, spend.BANNED[0])]


def test_v0_39_documentation_may_name_the_control_it_forbids():
    """Without this, neither ADR-0056 nor its design note could describe the ban."""
    call = f"client.{spend.BANNED[0]}(9999)"

    assert spend.ALLOWED_PREFIXES and all(
        not spend.scan_text(path, call) for path in spend.ALLOWED_PREFIXES
    )
    assert not spend.is_allowed("src/consilient/budget.py")


def test_v0_39_the_read_only_usage_oracle_is_not_blocked():
    """EXP-94 must be able to call GetFilteredUsageEvents on the same service. A ban so wide
    that it forbids reading the counter would stop the experiment that settles ADR-0056."""
    assert not spend.scan_text(
        "src/consilient/usage.py", "Get" + "FilteredUsageEvents(req)"
    )


def test_v0_39_no_tracked_file_escalates_spend():
    script = Path(".github/scripts/check_no_spend_escalation.py")
    if not script.exists():  # pragma: no cover - repository-only check
        pytest.skip("checker not present in this checkout")
    result = subprocess.run(
        [sys.executable, str(script), "--check", "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    # The artefact, not the exit code: a checker that silently found nothing to scan would
    # also exit 0. This project has shipped a check that could not fail twice already.
    assert "V0-39 ok" in result.stdout, result.stdout + result.stderr
    assert result.returncode == 0


def test_v0_39_is_wired_into_ci_and_cannot_be_silently_unwired():
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    step = workflow.partition("- name: Spend escalation invariant check")[2].partition(
        "- name:"
    )[0]

    assert "run: python .github/scripts/check_no_spend_escalation.py --check" in step


# ------------------------------------------------ V0-30 / V0-31, usage, limits and spend
# PRODUCT, not instance. Nothing below names an account, a credential or a real balance.
from decimal import Decimal  # noqa: E402
from consilient import budget as budget_mod  # noqa: E402
from consilient import usage as usage_mod  # noqa: E402


# --------------------------------------------------------------- V0-31, the spend ceiling
def limits_file(tmp_path, ceilings, cap=None, name="limits.json"):
    body = {"ceilings": ceilings}
    if cap is not None:
        body["account_cap"] = cap
    path = tmp_path / name
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def test_an_absent_or_malformed_limits_file_refuses_rather_than_meaning_unlimited(
    tmp_path,
):
    """V0-31. Fail-closed: no ceiling is not "unlimited", it is "no" (ADR-0044).

    A default this module chose would be a number the principal never approved, standing
    where his own should be. Every one of these refusals is reached, not assumed.
    """
    assert isinstance(
        usage_mod.load_limits(tmp_path / "absent.json"), budget_mod.BudgetRefusal
    )

    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    assert isinstance(
        usage_mod.load_limits(tmp_path / "bad.json"), budget_mod.BudgetRefusal
    )

    empty = usage_mod.load_limits(limits_file(tmp_path, [], name="empty.json"))
    assert isinstance(empty, budget_mod.BudgetRefusal)
    assert "no weekly or monthly ceiling is configured" in empty.reason

    # A JSON float has already lost the exactness a money comparison depends on.
    floaty = limits_file(
        tmp_path,
        [{"period": "weekly", "amount": 10.0, "currency": "USD"}],
        name="float.json",
    )
    assert isinstance(usage_mod.load_limits(floaty), budget_mod.BudgetRefusal)

    unknown = limits_file(
        tmp_path,
        [{"period": "daily", "amount": "1", "currency": "USD"}],
        name="daily.json",
    )
    assert isinstance(usage_mod.load_limits(unknown), budget_mod.BudgetRefusal)


def test_a_configured_ceiling_above_the_declared_account_cap_is_refused(tmp_path):
    """V0-31. The harness ceiling sits at or below what the principal declared.

    Refused, never clamped. Silently lowering the ceiling to the cap would let a
    configuration asking for more than the principal allows still run, just quietly, and
    the operator would never learn that the file they edited does not say what the harness
    is doing. A boundary that edits your request instead of rejecting it is a preference.
    """
    over = limits_file(
        tmp_path,
        [{"period": "monthly", "amount": "150.00", "currency": "USD"}],
        cap={"period": "monthly", "amount": "100.00", "currency": "USD"},
        name="over.json",
    )
    refusal = usage_mod.load_limits(over)
    assert isinstance(refusal, budget_mod.BudgetRefusal)
    assert "exceeds the declared" in refusal.reason

    under = limits_file(
        tmp_path,
        [
            {"period": "weekly", "amount": "20.00", "currency": "USD"},
            {"period": "monthly", "amount": "80.00", "currency": "USD"},
        ],
        cap={"period": "monthly", "amount": "100.00", "currency": "USD"},
        name="under.json",
    )
    ceilings = usage_mod.load_limits(under)
    assert isinstance(ceilings, tuple)
    assert {c.period for c in ceilings} == {"weekly", "monthly"}


def test_a_cap_and_a_ceiling_in_different_currencies_refuse_rather_than_convert(
    tmp_path,
):
    """V0-31. The account cap is stated in pounds and this harness meters in dollars.

    There is no exchange rate in this repository and there must not be one: a rate this
    module invented would be a number nobody measured, standing between the principal and
    his money. The honest outcome is a refusal telling him to state the cap in the currency
    the ceiling is enforced in -- not a silent conversion that looks like it worked.
    """
    mixed = limits_file(
        tmp_path,
        [{"period": "monthly", "amount": "80.00", "currency": "USD"}],
        cap={"period": "monthly", "amount": "100.00", "currency": "GBP"},
    )
    refusal = usage_mod.load_limits(mixed)
    assert isinstance(refusal, budget_mod.BudgetRefusal)
    assert "no conversion is performed" in refusal.reason


def test_the_configured_ceiling_actually_refuses_the_spend_that_would_breach_it(
    tmp_path,
):
    """V0-31 end to end. A limit that only warns is not a limit.

    This is the test that separates an enforced ceiling from a displayed one: the same
    configuration is loaded from the instance file, handed to `check_budget`, and the
    request that would cross it comes back refused with nothing reserved. Refusing while
    still writing the reservation would be the subtler version of the same failure.
    """
    log = tmp_path / "log"
    write_budget_state(log, "9.00", "30.00")
    ceilings = usage_mod.load_limits(
        limits_file(
            tmp_path,
            [
                {"period": "weekly", "amount": "10.00", "currency": "USD"},
                {"period": "monthly", "amount": "40.00", "currency": "USD"},
            ],
            cap={"period": "monthly", "amount": "100.00", "currency": "USD"},
        )
    )
    assert isinstance(ceilings, tuple)

    before = sorted(path.read_bytes() for path in log.glob("*.jsonl"))
    breaching = budget_mod.check_budget(
        log, ceilings, budget_mod.SpendRequest("run-over", Decimal("1.50"), "USD")
    )
    assert breaching == budget_mod.BudgetRefusal("weekly ceiling would be breached")
    assert sorted(path.read_bytes() for path in log.glob("*.jsonl")) == before, (
        "a refused request reserved something anyway"
    )

    permitted = budget_mod.check_budget(
        log, ceilings, budget_mod.SpendRequest("run-under", Decimal("0.50"), "USD")
    )
    assert isinstance(permitted, budget_mod.BudgetPermission)

    # ...and the reservation it wrote counts against the next request.
    assert budget_mod.check_budget(
        log, ceilings, budget_mod.SpendRequest("run-next", Decimal("0.75"), "USD")
    ) == budget_mod.BudgetRefusal("weekly ceiling would be breached")


def test_the_monthly_ceiling_refuses_independently_of_the_weekly_one(tmp_path):
    """V0-31. Both limits are real; neither is decoration for the other.

    A monthly ceiling alone would let one week consume the month, and a weekly ceiling
    alone would let four weeks exceed it. ADR-0044 requires both, so both are exercised.
    """
    log = tmp_path / "log"
    write_budget_state(log, "0.00", "39.90")
    ceilings = usage_mod.load_limits(
        limits_file(
            tmp_path,
            [
                {"period": "weekly", "amount": "10.00", "currency": "USD"},
                {"period": "monthly", "amount": "40.00", "currency": "USD"},
            ],
        )
    )
    assert isinstance(ceilings, tuple)
    assert budget_mod.check_budget(
        log, ceilings, budget_mod.SpendRequest("run-month", Decimal("0.20"), "USD")
    ) == budget_mod.BudgetRefusal("monthly ceiling would be breached")


def test_the_shipped_example_limits_file_is_a_shape_not_a_configuration():
    """The example must parse and must not be usable as a real ceiling by accident."""
    example = json.loads(
        Path(".harness/limits.example.json").read_text(encoding="utf-8")
    )
    assert example["ceilings"], "the example must show at least one ceiling"
    assert usage_mod.DEFAULT_LIMITS.name == "limits.json", (
        "the example must not be the path the harness reads"
    )

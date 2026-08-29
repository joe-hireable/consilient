"""Refusals that come from the state snapshot rather than from the ceiling. No spend can
be decided at all unless the observed spend is present, readable and recent, so each of
these asserts that the budget refuses on the state itself.

The failure they exist to prevent is assuming zero. An absent, unreadable or malformed
snapshot that silently defaults to nothing spent authorises the entire ceiling, so
absence, a missing field, a malformed reservation appended after a good state, an
observation older than fifteen minutes, and an observation that crosses a UTC weekly or
monthly period boundary all refuse instead.

Freshness is checked twice, not once: a state that is fresh when read but expires before
the reservation is written must still refuse, and nothing may be appended when it does.
Quarantine is fingerprinted by digest rather than counted, because a count alone cannot
see one malformed line replaced by another."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from consilient.events import (
    SCHEMA_VERSION,
    append,
    canonical,
    read_all,
    rejection_digest,
)
from budget_helpers import (
    budget_state,
    write_state,
)


def test_absent_and_unreadable_state_refuse(tmp_path):
    from consilient import budget

    ceiling = (budget.Ceiling("weekly", Decimal("5"), "USD"),)
    request = budget.SpendRequest("run-state", Decimal("1"), "USD")

    absent = budget.check_budget(tmp_path, ceiling, request)
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("not trajectory state", encoding="utf-8")
    unreadable = budget.check_budget(not_a_directory, ceiling, request)

    assert absent == budget.BudgetRefusal("budget state is absent")
    assert unreadable == budget.BudgetRefusal("budget state is unreadable")


def test_state_observation_older_than_fifteen_minutes_refuses(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    write_state(tmp_path, now, observed_at=now - timedelta(minutes=15, microseconds=1))

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-stale", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")


def test_state_that_expires_between_read_and_reservation_refuses(tmp_path, monkeypatch):
    from consilient import budget

    observed = datetime.now(timezone.utc)
    write_state(tmp_path, observed)
    times = iter(
        (
            observed + timedelta(minutes=14, seconds=59),
            observed + timedelta(minutes=15, microseconds=1),
        )
    )
    monkeypatch.setattr(budget, "_utc_now", lambda: next(times))

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-expiring", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")
    events, _ = read_all(tmp_path)
    assert all(event.kind != "spend.reserved" for event in events)


def test_malformed_state_refuses_instead_of_assuming_zero_spend(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    malformed = budget_state(now)
    del malformed["data"]["monthly_spent"]
    (tmp_path / f"{now.date().isoformat()}.jsonl").write_text(
        canonical(malformed) + "\n", encoding="utf-8"
    )

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-malformed", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")


def test_fresh_state_supersedes_old_quarantine_but_not_a_new_one(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text("{old malformed line}\n", encoding="utf-8")
    fingerprint = rejection_digest(read_all(tmp_path)[1])
    append(log, budget_state(now, rejection_fingerprint=fingerprint))
    ceiling = (budget.Ceiling("weekly", Decimal("5"), "USD"),)
    request = budget.SpendRequest("run-quarantine", Decimal("1"), "USD")

    superseded = budget.check_budget(tmp_path, ceiling, request)
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{new malformed line}\n")
    current = budget.check_budget(tmp_path, ceiling, request)

    assert isinstance(superseded, budget.BudgetPermission)
    assert current == budget.BudgetRefusal("budget state is unreadable")


def test_quarantine_digest_detects_a_same_count_replacement(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text("{first malformed line}\n", encoding="utf-8")
    fingerprint = rejection_digest(read_all(tmp_path)[1])
    append(log, budget_state(now, rejection_fingerprint=fingerprint))
    lines = log.read_text(encoding="utf-8").splitlines(keepends=True)
    log.write_text(
        "{replacement malformed line}\n" + "".join(lines[1:]), encoding="utf-8"
    )

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-replaced", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")


@pytest.mark.parametrize(
    ("now", "observed_at"),
    (
        (
            datetime(2026, 8, 3, 0, 5, tzinfo=timezone.utc),
            datetime(2026, 8, 2, 23, 55, tzinfo=timezone.utc),
        ),
        (
            datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc),
            datetime(2026, 8, 31, 23, 55, tzinfo=timezone.utc),
        ),
    ),
)
def test_state_from_a_previous_utc_budget_period_is_stale(
    tmp_path, monkeypatch, now, observed_at
):
    from consilient import budget

    monkeypatch.setattr(budget, "_utc_now", lambda: now)
    log = tmp_path / f"{now.date().isoformat()}.jsonl"
    log.write_text(
        canonical(budget_state(now, observed_at=observed_at)) + "\n", encoding="utf-8"
    )

    decision = budget.check_budget(
        tmp_path,
        (
            budget.Ceiling("weekly", Decimal("5"), "USD"),
            budget.Ceiling("monthly", Decimal("5"), "USD"),
        ),
        budget.SpendRequest("run-period", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is stale")


def test_malformed_reservation_after_state_refuses_without_crashing(tmp_path):
    from consilient import budget

    now = datetime.now(timezone.utc)
    log = write_state(tmp_path, now)
    malformed = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "spend.reserved",
        "actor": "consilient.budget",
        "data": {
            "provider": "openrouter",
            "run_id": "run-bad-record",
            "currency": "USD",
            "state_observed_at": now.isoformat(),
        },
    }
    with log.open("a", encoding="utf-8") as fh:
        fh.write(canonical(malformed) + "\n")

    decision = budget.check_budget(
        tmp_path,
        (budget.Ceiling("weekly", Decimal("5"), "USD"),),
        budget.SpendRequest("run-next", Decimal("1"), "USD"),
    )

    assert decision == budget.BudgetRefusal("budget state is unreadable")

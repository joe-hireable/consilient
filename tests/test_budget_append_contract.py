"""The contract enforced where budget events are written, not where they are read.

A chokepoint without an enforcement rule is not a chokepoint, so `budget.state` and
`spend.reserved` are validated inside `append` itself: the declared writer, the
admission lock, a real UTC calendar timestamp on both `ts` and `observed_at`, the
required data fields, the exact provider and currency, and the timestamped daily file
the event must land in.

Each test asserts that the invalid event never reached the trajectory — the log file
does not exist afterwards — because a validation that refuses after the write has
already lost."""

from datetime import datetime, timedelta, timezone
import pytest
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    append,
)
from budget_helpers import (
    budget_state,
)


def test_budget_state_requires_its_declared_writer(tmp_path):
    now = datetime.now(timezone.utc)
    state = budget_state(now)
    state["actor"] = "untrusted-agent"
    log = tmp_path / f"{now.date().isoformat()}.jsonl"

    with pytest.raises(EventError, match="declared writer 'openrouter-probe'"):
        append(log, state)

    assert not log.exists()


def test_generic_budget_writes_respect_the_admission_lock(tmp_path):
    now = datetime.now(timezone.utc)
    lock = tmp_path / ".budget.lock"
    lock.touch()
    try:
        with pytest.raises(EventError, match="budget trajectory is busy"):
            append(tmp_path / f"{now.date().isoformat()}.jsonl", budget_state(now))
    finally:
        lock.unlink()


def test_budget_events_require_real_utc_timestamps(tmp_path):
    now = datetime.now(timezone.utc)
    impossible = budget_state(now)
    impossible["ts"] = "2026-99-99T00:00:00+00:00"
    offset = budget_state(now.astimezone(timezone(timedelta(hours=1))))
    overflowing = budget_state(now)
    overflowing["data"]["observed_at"] = "0001-01-01T00:00:00+14:00"

    with pytest.raises(EventError, match="valid calendar timestamp"):
        append(tmp_path / "2026-99-99.jsonl", impossible)
    with pytest.raises(EventError, match="ts must use UTC"):
        append(tmp_path / f"{now.date().isoformat()}.jsonl", offset)
    with pytest.raises(EventError, match="observed_at cannot be normalised to UTC"):
        append(tmp_path / f"{now.date().isoformat()}.jsonl", overflowing)


def test_budget_state_contract_is_enforced_at_the_append_chokepoint(tmp_path):
    now = datetime.now(timezone.utc)
    malformed = budget_state(now)
    del malformed["data"]["monthly_spent"]
    log = tmp_path / "state.jsonl"

    with pytest.raises(EventError, match="budget.state.*monthly_spent"):
        append(log, malformed)

    assert not log.exists(), "an invalid state event must not reach the trajectory"


def test_budget_events_must_use_their_timestamped_daily_file(tmp_path):
    now = datetime.now(timezone.utc)
    wrong = tmp_path / "2000-01-01.jsonl"

    with pytest.raises(EventError, match="timestamped daily file"):
        append(wrong, budget_state(now))

    assert not wrong.exists()


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("run_id", "   ", "run_id"),
        ("amount", "NaN", "finite positive"),
        ("currency", "GBP", "currency 'USD'"),
        ("provider", "another-vendor", "provider 'openrouter'"),
    ),
)
def test_spend_reservation_contract_is_enforced_at_append(
    tmp_path, field, value, match
):
    now = datetime.now(timezone.utc)
    record = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "spend.reserved",
        "actor": "consilient.budget",
        "data": {
            "provider": "openrouter",
            "run_id": "run-valid",
            "amount": "1.00",
            "currency": "USD",
            "state_observed_at": now.isoformat(),
        },
    }
    record["data"][field] = value
    log = tmp_path / "spend.jsonl"

    with pytest.raises(EventError, match=match):
        append(log, record)

    assert not log.exists(), "an invalid reservation must not reach the trajectory"

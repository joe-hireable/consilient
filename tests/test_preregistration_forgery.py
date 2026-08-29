"""Pre-registration must not be forgeable by choosing which daily file a line lands in.

THE DEFECT, found by unit X01's adversarial review and reproduced here before it was fixed.

`read_all` orders events by FILENAME first, then by position. So for any kind where the question
being answered is "which came first", letting an author choose the file lets them choose the
answer. Measured 29 August 2026, against the live writer:

    append measurement.result      to 2999-01-02.jsonl   ACCEPTED
    append measurement.registered  to 2999-01-01.jsonl   ACCEPTED
    read_all -> ['measurement.registered', 'measurement.result'], 0 rejected

The result was written FIRST in wall-clock time and replayed SECOND. A post-hoc measurement read
as pre-registered, with nothing quarantined and nothing to see in the log.

That is not a cosmetic ordering bug. Pre-registration is the discipline this project's entire
evidence base rests on -- a stopping rule that can be written after the result is not a stopping
rule -- and `docs/10-research/` is built on the claim that registrations precede results.

`_check_clock` does not catch it. Both lines carry an honest `ts` within tolerance; only the FILE
was chosen. The check that was missing is the one budget and spend already had: the daily file a
line is written to must be the one its own `ts` names.

The review found this three times and the unit did not fix it. X01 was correct each time.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events
from consilient.events_evidence import MEASUREMENT_ACTOR

RUN = "exp-forge-1"
REGISTERED_DATA: dict[str, object] = {
    "run_id": RUN,
    "config_hash": "a" * 64,
    "hardware_id": "rtx-5090",
}
RESULT_DATA: dict[str, object] = {"run_id": RUN, "fixture": "itsdangerous-2.2.0"}


def _event(kind: str, data: dict[str, object]) -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "event": kind,
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": MEASUREMENT_ACTOR,
        "event_id": str(uuid.uuid4()),
        "data": dict(data),
    }


def _today() -> str:
    return f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"


@pytest.mark.parametrize(
    ("kind", "data"),
    [
        ("measurement.registered", REGISTERED_DATA),
        ("measurement.result", RESULT_DATA),
    ],
)
def test_a_measurement_line_cannot_choose_its_daily_file(
    kind: str, data: dict[str, object], tmp_path: Path
) -> None:
    with pytest.raises(events.EventError, match="timestamped daily file"):
        events.append(tmp_path / "2999-01-02.jsonl", _event(kind, data))  # type: ignore[arg-type]


def test_the_forge_is_refused_at_its_first_write(tmp_path: Path) -> None:
    """The whole exploit, end to end: result first into a later file, registration behind it."""
    with pytest.raises(events.EventError, match="timestamped daily file"):
        events.append(
            tmp_path / "2999-01-02.jsonl", _event("measurement.result", RESULT_DATA)
        )  # type: ignore[arg-type]
    accepted, rejected = events.read_all(tmp_path)
    assert accepted == [] and rejected == [], (
        "the refused line reached the log; a refusal that still writes is not a refusal"
    )


def test_the_honest_path_still_works(tmp_path: Path) -> None:
    """A rule that refuses the legitimate write is an outage, not a guard.

    Registration and result both go to today's file, in order, and replay in that order.
    """
    today = tmp_path / _today()
    events.append(today, _event("measurement.registered", REGISTERED_DATA))  # type: ignore[arg-type]
    events.append(today, _event("measurement.result", RESULT_DATA))  # type: ignore[arg-type]
    accepted, rejected = events.read_all(tmp_path)
    assert [item.kind for item in accepted] == [
        "measurement.registered",
        "measurement.result",
    ]
    assert rejected == []


def test_budget_and_spend_remain_bound() -> None:
    """The two kinds that were already bound must not be lost while widening the set."""
    from consilient import events_transactions

    bound = events_transactions._DATE_BOUND_KINDS
    for kind in (
        "budget.state",
        "spend.reserved",
        "measurement.registered",
        "measurement.result",
    ):
        assert kind in bound, f"{kind} is no longer bound to its daily file"

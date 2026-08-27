"""BI — ambient element budget and a demand record for promotion."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import pytest

from consilient.events import Event, EventError, read


def test_ambient_surface_element_budget_is_3() -> None:
    """Adding an ambient element requires removing one, or renaming this test.

    A budget that can be raised by editing a number in two places is not a budget.
    The expected count is the last token of this function's name.
    """
    from consilient import surfaces

    match = re.search(r"(\d+)$", test_ambient_surface_element_budget_is_3.__name__)
    assert match is not None
    expected = int(match.group(1))
    assert isinstance(surfaces.AMBIENT_ELEMENTS, tuple)
    assert len(surfaces.AMBIENT_ELEMENTS) == expected
    assert len(set(surfaces.AMBIENT_ELEMENTS)) == expected


def test_ambient_elements_are_the_observe_increment_not_a_widget_registry() -> None:
    from consilient import surfaces

    assert surfaces.AMBIENT_ELEMENTS == ("gates", "beta", "needs_you")


def test_a_surface_request_is_appended_with_question_when_and_who(
    tmp_path: Path,
) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    before = datetime.now(timezone.utc)
    payload = surfaces.request_surface(
        log,
        question="  what is the prepaid headroom?  ",
        actor="joe-brown",
    )
    after = datetime.now(timezone.utc)

    assert payload["event"] == surfaces.REQUEST_KIND
    assert payload["actor"] == "joe-brown"
    written = datetime.fromisoformat(payload["ts"])
    assert before <= written <= after
    assert payload["data"] == {"question": "what is the prepaid headroom?"}
    assert "event_id" in payload

    accepted, rejected = read(log)
    assert rejected == []
    assert len(accepted) == 1
    assert accepted[0].kind == surfaces.REQUEST_KIND
    assert accepted[0].actor == "joe-brown"
    assert accepted[0].data["question"] == "what is the prepaid headroom?"


def test_empty_question_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    with pytest.raises(EventError, match="question"):
        surfaces.request_surface(log, question="   ", actor="joe-brown")
    assert not log.exists()


def test_empty_actor_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    with pytest.raises(EventError, match="actor"):
        surfaces.request_surface(log, question="what is beta?", actor="  ")
    assert not log.exists()


def test_a_single_request_does_not_admit_promotion(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    accepted, _rejected = read(log)

    assert surfaces.demand_for("show spend", accepted) == 1
    assert surfaces.promotion_admissible("show spend", accepted) is False


def test_two_requests_for_the_same_question_admit_promotion(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    accepted, _rejected = read(log)

    assert surfaces.demand_for("show spend", accepted) == 2
    assert surfaces.promotion_admissible("show spend", accepted) is True


def test_demand_matches_the_stripped_question(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    accepted, _rejected = read(log)

    assert surfaces.demand_for("  show spend  ", accepted) == 1
    assert surfaces.promotion_admissible("  show spend  ", accepted) is False


def test_different_questions_do_not_pool_as_demand(tmp_path: Path) -> None:
    from consilient import surfaces

    log = tmp_path / "2026-08-26.jsonl"
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    surfaces.request_surface(log, question="show the fleet", actor="joe-brown")
    accepted, _rejected = read(log)

    assert surfaces.demand_for("show spend", accepted) == 1
    assert surfaces.demand_for("show the fleet", accepted) == 1
    assert surfaces.promotion_admissible("show spend", accepted) is False
    assert surfaces.promotion_admissible("show the fleet", accepted) is False


def test_unrelated_event_kinds_are_not_demand() -> None:
    from consilient import surfaces

    noise = Event(
        {
            "v": 1,
            "ts": "2026-08-26T12:00:00+00:00",
            "event": "attempt.outcome",
            "actor": "consilient",
            "data": {"question": "show spend"},
        }
    )
    assert surfaces.demand_for("show spend", (noise,)) == 0
    assert surfaces.promotion_admissible("show spend", (noise,)) is False


def test_direct_blank_or_malformed_surface_events_are_not_demand() -> None:
    from consilient import surfaces

    blank = Event(
        {
            "v": 1,
            "ts": "2026-08-26T12:00:00+00:00",
            "event": surfaces.REQUEST_KIND,
            "actor": "",
            "data": {"question": ""},
        }
    )
    malformed = Event(
        {
            "v": 1,
            "ts": "2026-08-26T12:00:00+00:00",
            "event": surfaces.REQUEST_KIND,
            "actor": "",
            "data": {"question": "show spend"},
        }
    )

    assert surfaces.demand_for("", (blank, blank)) == 0
    assert surfaces.promotion_admissible("", (blank, blank)) is False
    assert surfaces.demand_for("show spend", (malformed,)) == 0


def test_recollection_is_not_promotion_evidence() -> None:
    from consilient import surfaces

    with pytest.raises(TypeError, match="trajectory event"):
        surfaces.promotion_admissible(
            "show spend",
            ["the user asked for a spend view twice"],
        )


def test_admissible_demand_does_not_mutate_the_ambient_set(tmp_path: Path) -> None:
    from consilient import surfaces

    before = surfaces.AMBIENT_ELEMENTS
    log = tmp_path / "2026-08-26.jsonl"
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    surfaces.request_surface(log, question="show spend", actor="joe-brown")
    accepted, _rejected = read(log)
    assert surfaces.promotion_admissible("show spend", accepted) is True
    assert surfaces.AMBIENT_ELEMENTS == before
    assert "show spend" not in surfaces.AMBIENT_ELEMENTS


def test_snapshot_age_is_a_running_counter() -> None:
    from consilient import surfaces

    as_of = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    now = as_of + timedelta(hours=4, minutes=12, seconds=7)
    assert surfaces.age_counter(as_of, now) == "4h 12m 7s"


def test_age_counter_refuses_naive_datetimes() -> None:
    from consilient import surfaces

    naive = datetime(2026, 8, 24, 12, 0, 0)
    aware = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="timezone"):
        surfaces.age_counter(naive, aware)
    with pytest.raises(ValueError, match="timezone"):
        surfaces.age_counter(aware, naive)


def test_age_counter_refuses_invalid_or_future_capture_time() -> None:
    from consilient import surfaces

    now = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="datetime"):
        surfaces.age_counter(cast(datetime, object()), now)
    with pytest.raises(ValueError, match="after now"):
        surfaces.age_counter(now + timedelta(seconds=1), now)


def test_unrefreshable_ambient_render_displays_age_including_zero() -> None:
    from consilient import surfaces

    as_of = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
    rendered = surfaces.render_ambient(as_of=as_of, now=as_of)
    assert tuple(element.id for element in rendered) == surfaces.AMBIENT_ELEMENTS
    assert all(element.age == "0h 0m 0s" for element in rendered)
    assert all(element.age != as_of.isoformat() for element in rendered)

    later = as_of + timedelta(seconds=90)
    stale = surfaces.render_ambient(as_of=as_of, now=later)
    assert all(element.age == "0h 1m 30s" for element in stale)

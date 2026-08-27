"""R20/R22/R23/R31 schema limbs: feedback kinds, the rating ban, the dial.

The unit of feedback is the task (feedback-signals.md). These tests pin the
three durable kinds that make a skip never re-asked, the schema-level refusal of
approval-style fields (R22's regression guard), the separate-signals rule that
forbids a default composite (R23), and ADR-0035's four visibility levels with
the recorded change event (R31's schema half).
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import events
from consilient.events import EventError

ROOT = Path(__file__).resolve().parent.parent


def base_event(kind: str, **data: object) -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": "consilient.test",
        "data": data,
    }


def as_principal(kind: str, **data: object) -> dict[str, object]:
    event = base_event(kind, **data)
    event["actor"] = "joe-brown"
    payload = event["data"]
    assert isinstance(payload, dict)
    payload["principal"] = "joe-brown"
    payload["via"] = "cli"
    return event


# ---------------------------------------------------------------- R22: the ban


@pytest.mark.parametrize(
    "field",
    sorted(events.RESPONSE_RATING_FIELDS),
)
def test_validate_rejects_approval_style_fields(field: str) -> None:
    with pytest.raises(EventError, match="approval-style"):
        events.validate(base_event("work.comment", **{field: "up"}))


def test_the_rating_ban_covers_the_named_shapes() -> None:
    """The set must name the shapes the obligation names: thumbs, satisfaction,
    rating, helpful, star. Shrinking it is a decision, not a refactor."""
    for shape in ("thumbs", "satisfaction", "rating", "helpful", "stars"):
        assert shape in events.RESPONSE_RATING_FIELDS


def test_no_rating_surface_in_tracked_source_or_dashboard() -> None:
    """The grep half of R22: no executable surface offers a response-rating widget.

    Scoped to code and rendered artefacts (.py/.html/.js): a markdown file cannot
    be a widget, and design prose must remain free to *name* the prohibited shapes
    — README.md and docs/20-design/ discuss the ban itself, and excluding them is
    what keeps this test able to fail on a real surface instead of on its own
    documentation. The load-bearing half is the schema ban in events.py."""
    pattern = re.compile(
        r"thumbs[_-]?(up|down)|star[_-]?rating|response[_-]?rating|"
        r"rate[_-]?this[_-]?(response|answer|reply)|satisfaction",
        re.IGNORECASE,
    )
    completed = subprocess_run_git_ls()
    hits: list[str] = []
    for rel in completed:
        if not rel.endswith((".py", ".html", ".js")):
            continue
        if rel.startswith("tests/"):
            continue  # tests name the ban
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if rel.endswith("events.py"):
            continue  # the ban list itself
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{rel}:{number}: {line.strip()[:80]}")
    assert not hits, "response-rating surface found:\n" + "\n".join(hits)


def subprocess_run_git_ls() -> list[str]:
    import subprocess

    out = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        env={k: v for k, v in __import__("os").environ.items() if not k.startswith("GIT_")},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode != 0:
        pytest.skip("git ls-files unavailable")
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


# ------------------------------------------------------- R20/R23: the feedback kinds


def test_feedback_asked_carries_the_precommitted_goal_verbatim() -> None:
    events.validate(
        base_event(events.FEEDBACK_ASKED_KIND, task_id="t1", goal_text="ship the gate")
    )
    with pytest.raises(EventError, match="goal_text"):
        events.validate(base_event(events.FEEDBACK_ASKED_KIND, task_id="t1"))
    with pytest.raises(EventError, match="task_id"):
        events.validate(base_event(events.FEEDBACK_ASKED_KIND, goal_text="g"))


def test_feedback_declined_is_durable_and_needs_nothing_else() -> None:
    events.validate(base_event(events.FEEDBACK_DECLINED_KIND, task_id="t1"))


def test_feedback_answered_records_achievement_only() -> None:
    events.validate(
        as_principal(
            events.FEEDBACK_ANSWERED_KIND,
            task_id="t1",
            goal_achieved="partially",
            missing="the edge case",
            better_approach="start from the schema",
        )
    )
    with pytest.raises(EventError, match="goal_achieved"):
        events.validate(
            as_principal(events.FEEDBACK_ANSWERED_KIND, task_id="t1", goal_achieved="mostly")
        )


def test_feedback_answered_refuses_a_composite() -> None:
    """R23: achievement and efficiency are separate records, permanently."""
    for field in sorted(events.FEEDBACK_COMPOSITE_FIELDS):
        with pytest.raises(EventError, match="separate records"):
            events.validate(
                as_principal(
                    events.FEEDBACK_ANSWERED_KIND,
                    task_id="t1",
                    goal_achieved="fully",
                    **{field: "0.5"},
                )
            )


def test_feedback_answers_come_from_the_user_never_the_agent() -> None:
    """Rule 2: agent self-assessment is never an outcome signal (V0-18 shape)."""
    with pytest.raises(EventError, match="only the principal"):
        events.validate(
            base_event(
                events.FEEDBACK_ANSWERED_KIND,
                task_id="t1",
                goal_achieved="fully",
                principal="joe-brown",
                via="cli",
            )
        )


# ------------------------------------------------------------------ R31: the dial


def test_visibility_levels_are_adr0035s_four() -> None:
    assert events.VISIBILITY_LEVELS == ("silent", "milestones", "decisions", "firehose")
    assert events.VISIBILITY_DEFAULT == "milestones"


def test_visibility_change_event_is_validated() -> None:
    events.validate(
        base_event(
            events.VISIBILITY_CHANGE_KIND,
            level="decisions",
            overrides={"dispatch.outcome": "firehose"},
        )
    )
    with pytest.raises(EventError, match="level"):
        events.validate(base_event(events.VISIBILITY_CHANGE_KIND, level="everything"))
    with pytest.raises(EventError, match="override"):
        events.validate(
            base_event(
                events.VISIBILITY_CHANGE_KIND,
                level="silent",
                overrides={"dispatch.outcome": "loud"},
            )
        )


def test_effective_visibility_is_validated_when_present() -> None:
    events.validate(
        as_principal(
            "work.comment",
            human_decision="approval",
            effective_visibility="silent",
        )
    )
    with pytest.raises(EventError, match="effective_visibility"):
        events.validate(
            as_principal(
                "work.comment", human_decision="approval", effective_visibility="lots"
            )
        )


def test_the_schema_guards_can_fail() -> None:
    """Mutation: each ban must bite on the thing it exists to refuse."""
    for kind, data, marker in (
        ("work.comment", {"rating": 5}, "approval-style"),
        (events.FEEDBACK_ANSWERED_KIND, {"task_id": "t", "goal_achieved": "fully", "score": 1}, None),
        (events.VISIBILITY_CHANGE_KIND, {"level": "loud"}, "level"),
    ):
        event = as_principal(kind, **data) if kind == events.FEEDBACK_ANSWERED_KIND else base_event(kind, **data)
        with pytest.raises(EventError):
            events.validate(event)

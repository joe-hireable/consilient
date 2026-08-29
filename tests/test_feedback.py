"""R20/R23 feedback behaviour and regression guards."""

from __future__ import annotations

import ast
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import beta, events, feedback, projection
from consilient.events import Event, EventError


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "src" / "consilient"


def test_feedback_for_another_task_does_not_suppress_the_ask() -> None:
    existing = (Event(feedback.record_decline("task-2")),)

    assert feedback.should_ask("task-1", iter(existing))


def test_record_ask_builds_a_valid_event_with_the_goal_verbatim() -> None:
    payload = feedback.record_ask("task-1", "ship the requested change")

    assert events.validate(payload) == payload
    assert payload["event"] == events.FEEDBACK_ASKED_KIND
    assert payload["actor"] == "consilient.feedback"
    assert payload["data"] == {
        "task_id": "task-1",
        "goal_text": "ship the requested change",
    }


def test_record_decline_builds_the_durable_skip_event() -> None:
    payload = feedback.record_decline("task-1")

    assert events.validate(payload) == payload
    assert payload["event"] == events.FEEDBACK_DECLINED_KIND
    assert payload["actor"] == "consilient.feedback"
    assert payload["data"] == {"task_id": "task-1"}


def test_record_answer_attributes_the_outcome_to_the_principal() -> None:
    payload = feedback.record_answer(
        "task-1",
        "partially",
        principal="joe-brown",
        missing="the edge case",
        better_approach="start from the schema",
    )

    assert events.validate(payload) == payload
    assert payload["event"] == events.FEEDBACK_ANSWERED_KIND
    assert payload["actor"] == "joe-brown"
    assert payload["data"] == {
        "task_id": "task-1",
        "goal_achieved": "partially",
        "missing": "the edge case",
        "better_approach": "start from the schema",
        "principal": "joe-brown",
        "via": "cli",
    }


def test_record_helpers_validate_before_returning() -> None:
    with pytest.raises(EventError, match="task_id"):
        feedback.record_decline("")
    with pytest.raises(EventError, match="goal_text"):
        feedback.record_ask("task-1", "")
    with pytest.raises(EventError, match="goal_achieved"):
        feedback.record_answer("task-1", "mostly", principal="joe-brown")


@pytest.mark.parametrize(
    "kind",
    sorted(events.FEEDBACK_KINDS),
)
def test_a_logged_feedback_disposition_is_not_reasked(
    kind: str, tmp_path: Path
) -> None:
    if kind == events.FEEDBACK_ASKED_KIND:
        payload = feedback.record_ask("task-1", "ship the requested change")
    elif kind == events.FEEDBACK_DECLINED_KIND:
        payload = feedback.record_decline("task-1")
    else:
        payload = feedback.record_answer("task-1", "fully", principal="joe-brown")
    log = tmp_path / "trajectory.jsonl"

    events.append(log, payload)
    recorded, rejected = events.read(log)

    assert rejected == []
    assert not feedback.should_ask("task-1", recorded)


def _attempt_event(index: int, stamp: str) -> events.EventPayload:
    return events.validate(
        {
            "v": events.SCHEMA_VERSION,
            "ts": stamp,
            "event": events.OUTCOME_KIND,
            "actor": "consilient.test",
            "data": {
                "attempt_id": f"attempt-{index}",
                "task": "feedback consequence fixture",
                "task_family": "feedback",
                "verifier_version": "fixture-v1",
                "verifier_accept": index % 3 == 0,
            },
        }
    )


def _verdict_event(index: int, stamp: str) -> events.EventPayload:
    return events.validate(
        {
            "v": events.SCHEMA_VERSION,
            "ts": stamp,
            "event": events.VERDICT_KIND,
            "actor": "joe-brown",
            "data": {
                "attempt_id": f"attempt-{index}",
                "human_verdict": "reject",
                "principal": "joe-brown",
                "via": "cli",
            },
        }
    )


def _project_feedback_variant(
    root: Path, terminal: events.EventPayload, stamp: str
) -> tuple[dict[str, list[tuple[object, ...]]], dict[str, object], list[str]]:
    log_dir = root / "log"
    log = log_dir / "trajectory.jsonl"
    for index in range(30):
        events.append(log, _attempt_event(index, stamp))
        events.append(log, _verdict_event(index, stamp))
    events.append(log, feedback.record_ask("task-1", "ship the requested change"))
    events.append(log, terminal)

    connection = projection.build(log_dir, root / "state.sqlite")
    try:
        derived = {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("outcomes", "usage", "rejections", "relational_quarantines")
        }
        measured = beta.from_connection(connection).as_dict()
        feedback_kinds = [
            row[0]
            for row in connection.execute(
                "SELECT kind FROM events WHERE kind LIKE 'feedback.%' ORDER BY position"
            )
        ]
    finally:
        connection.close()
    return derived, measured, feedback_kinds


def test_feedback_events_do_not_create_relational_quarantines(tmp_path: Path) -> None:
    """R23 feedback kinds are auditable ledger rows, not beta inputs or join failures."""
    stamp = datetime.now(timezone.utc).isoformat()
    answered = feedback.record_answer("task-1", "fully", principal="joe-brown")
    log_dir = tmp_path / "answered" / "log"
    db_path = tmp_path / "answered" / "state.sqlite"
    _project_feedback_variant(tmp_path / "answered", answered, stamp)

    conn = projection.build(log_dir, db_path)
    try:
        assert projection.relational_quarantines(conn) == []
    finally:
        conn.close()


def test_answering_or_declining_has_no_projection_or_beta_consequence(
    tmp_path: Path,
) -> None:
    """Compare consequence-bearing projection tables, not the raw event ledger.

    The generic ``events`` table must differ because R23 requires the answer and the
    decline to remain separately auditable. ``outcomes`` feeds beta; ``usage`` and
    ``rejections`` are the other derived tables. Equality here shows that the feedback
    disposition changes none of them.
    """
    stamp = datetime.now(timezone.utc).isoformat()
    answered = feedback.record_answer("task-1", "fully", principal="joe-brown")
    declined = feedback.record_decline("task-1")

    answer_projection, answer_beta, answer_kinds = _project_feedback_variant(
        tmp_path / "answered", answered, stamp
    )
    decline_projection, decline_beta, decline_kinds = _project_feedback_variant(
        tmp_path / "declined", declined, stamp
    )

    assert answer_projection == decline_projection
    assert answer_beta == decline_beta
    assert answer_beta["verdict"] == beta.INSUFFICIENT
    assert answer_beta["n_rejected"] == 0
    assert answer_beta["n_false_accept"] == 0
    assert answer_kinds == [
        events.FEEDBACK_ASKED_KIND,
        events.FEEDBACK_ANSWERED_KIND,
    ]
    assert decline_kinds == [
        events.FEEDBACK_ASKED_KIND,
        events.FEEDBACK_DECLINED_KIND,
    ]


def _feedback_consumer_hits(source: str) -> list[int]:
    tree = ast.parse(source)
    hits: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            hits.update(
                node.lineno
                for name in node.names
                if name.name.startswith("FEEDBACK_")
            )
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id.startswith("FEEDBACK_"):
                hits.add(node.lineno)
        elif isinstance(node, ast.Attribute) and node.attr.startswith("FEEDBACK_"):
            hits.add(node.lineno)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("feedback.")
        ):
            hits.add(node.lineno)
    return sorted(hits)


def _assert_no_feedback_consumer(source: str, path: str) -> None:
    hits = _feedback_consumer_hits(source)
    assert not hits, f"direct feedback consumer in {path} at lines {hits}"


def test_no_module_outside_feedback_and_its_schema_reads_feedback_events() -> None:
    """Conservative syntactic guard against a feedback-dependent gate.

    ``events.py`` is exempt because it is the authoritative validator; ``feedback.py``
    is the owner. The scan bans every other direct import, constant or event-kind
    literal, including a harmless reporter. It cannot see dynamically constructed
    strings, reflection or generic event dataflow.
    """
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        # A family, not a filename. events.py's validator was split across events_*.py on
        # 28 August 2026, so exempting the entry point alone reported its own authoritative
        # validator as an unauthorised consumer. What the invariant means is that nothing
        # OUTSIDE these two modules reads feedback events, and a module is now a set of files.
        if path.name in {"events.py", "feedback.py"} or path.stem.startswith(
            ("events_", "feedback_")
        ):
            continue
        _assert_no_feedback_consumer(
            path.read_text(encoding="utf-8"), str(path.relative_to(ROOT))
        )


def test_feedback_consumer_guard_has_a_failing_negative_control() -> None:
    source = """
from .events import FEEDBACK_ANSWERED_KIND

def may_continue(event):
    if event.kind == FEEDBACK_ANSWERED_KIND:
        return True
    return False
"""
    with pytest.raises(AssertionError, match="direct feedback consumer"):
        _assert_no_feedback_consumer(source, "src/consilient/mutant.py")


def test_feedback_module_exposes_no_composite_function() -> None:
    """Structural public-surface guard; the schema below is the data-level guard."""
    tree = ast.parse((SOURCE_ROOT / "feedback.py").read_text(encoding="utf-8"))
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }

    assert public_functions == {
        "should_ask",
        "record_ask",
        "record_decline",
        "record_answer",
    }


@pytest.mark.parametrize("field", sorted(events.FEEDBACK_COMPOSITE_FIELDS))
def test_feedback_answered_schema_refuses_composite_fields(field: str) -> None:
    payload = feedback.record_answer("task-1", "fully", principal="joe-brown")
    data = payload["data"]
    assert isinstance(data, dict)
    data[field] = "0.5"

    with pytest.raises(EventError, match="separate records"):
        events.validate(payload)

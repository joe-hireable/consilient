"""Tests for the verbatim recall projector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient.events import SCHEMA_VERSION, VERDICT_KIND, append
from consilient.recall import ALWAYS_INCLUDE_KINDS, pack


def _ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _event(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": _ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _write(log_dir: Path, *events) -> None:
    for event in events:
        path = log_dir / f"{event['ts'][:10]}.jsonl"
        append(path, event)


def test_empty_log_reports_no_events(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    assert pack(log_dir, query="", limit_chars=1000) == (
        "# Recall pack\n\nNo events in log.\n"
    )


def test_verbatim_field_present_in_pack(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    marker = "unique-verbatim-marker-xyzzy"
    _write(
        log_dir,
        _event(
            event="note.recorded",
            data={"body": marker},
        ),
    )
    text = pack(log_dir, query=marker, limit_chars=5000)
    assert marker in text
    assert f'"body": "{marker}"' in text


def test_omitted_count_footer_when_over_budget(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(6):
        _write(
            log_dir,
            _event(
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "padding": "x" * 80},
            ),
        )
    text = pack(log_dir, query="note", limit_chars=600)
    assert "omitted to fit character limit" in text
    assert " event(s) omitted" in text


def test_query_filters_non_priority_events(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            ts=_ts(0),
            event="alpha.event",
            data={"topic": "alpha-only"},
        ),
        _event(
            ts=_ts(1),
            event="beta.event",
            data={"topic": "beta-only"},
        ),
    )
    text = pack(log_dir, query="alpha-only", limit_chars=5000)
    assert "alpha-only" in text
    assert "beta-only" not in text


def test_always_include_kinds_ignore_query(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            event="dispatch.refused",
            actor="consilient.dispatch",
            data={
                "reason": "pool exhausted",
                "supervised": False,
            },
        ),
    )
    text = pack(log_dir, query="totally-unrelated-token", limit_chars=5000)
    assert "dispatch.refused" in text
    assert "pool exhausted" in text


def test_human_verdict_kind_is_always_included(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            actor="joe-brown",
            event=VERDICT_KIND,
            data={
                "attempt_id": "attempt-abc",
                "human_verdict": "reject",
                "principal": "joe-brown",
                "via": "cli",
            },
        ),
    )
    text = pack(log_dir, query="missing-keyword", limit_chars=5000)
    assert "attempt-abc" in text
    assert '"human_verdict": "reject"' in text


def test_character_bound_respected(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(4):
        _write(
            log_dir,
            _event(
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "body": "word " * 20},
            ),
        )
    limit = 900
    text = pack(log_dir, query="note", limit_chars=limit)
    assert len(text) <= limit


def test_always_include_kinds_cover_brief_list():
    assert "dispatch.outcome" in ALWAYS_INCLUDE_KINDS
    assert "dispatch.refused" in ALWAYS_INCLUDE_KINDS
    assert "dispatch.fanout" in ALWAYS_INCLUDE_KINDS
    assert VERDICT_KIND in ALWAYS_INCLUDE_KINDS
    assert "ticket.completed" in ALWAYS_INCLUDE_KINDS


def test_limit_chars_must_be_positive(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    with pytest.raises(ValueError, match="limit_chars"):
        pack(log_dir, query="", limit_chars=0)

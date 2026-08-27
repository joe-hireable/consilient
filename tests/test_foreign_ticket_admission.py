"""B4 counts only foreign tickets whose attempt.outcome carries re-derivable shape."""

from __future__ import annotations

import json
from pathlib import Path

from consilient.cli import DEFAULT_LOG, _foreign_tickets
from consilient.events import SCHEMA_VERSION

VALID_RECEIPT = "a" * 64
REPO_LOG = Path(__file__).resolve().parent.parent / DEFAULT_LOG


def _line(
    kind: str,
    *,
    ticket: str,
    extra: dict[str, object] | None = None,
) -> str:
    data: dict[str, object] = {
        "repository": "pytest-dev/pytest",
        "task": ticket,
        "attempt_id": f"{ticket}:repair:1",
        "ticket": ticket,
        "verifier_accept": True,
    }
    if extra:
        data.update(extra)
    return json.dumps(
        {
            "v": SCHEMA_VERSION,
            "ts": "2026-08-24T12:00:00+00:00",
            "event": kind,
            "actor": "a.human.with.a.text.editor",
            "data": data,
        },
        separators=(",", ":"),
    )


def _write_pair(
    log: Path,
    ticket: str,
    *,
    outcome_extra: dict[str, object] | None = None,
) -> None:
    path = log / "hand-written.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _line("attempt.outcome", ticket=ticket, extra=outcome_extra)
        + "\n"
        + _line("ticket.completed", ticket=ticket)
        + "\n",
        encoding="utf-8",
    )


def _rederivable() -> dict[str, object]:
    return {
        "harness": "cursor-grok",
        "corpus_revision": "test-fixture-pin-not-a-commit-sha",
        "receipt_sha256": VALID_RECEIPT,
    }


def test_hand_written_rows_with_all_three_fields_still_count(tmp_path: Path) -> None:
    """Shape, not provenance, is what this checks — a text editor still counts."""
    _write_pair(tmp_path, "B4-HAND-1", outcome_extra=_rederivable())

    assert _foreign_tickets(tmp_path) == 1


def test_missing_harness_is_not_counted(tmp_path: Path) -> None:
    extra = _rederivable()
    del extra["harness"]
    _write_pair(tmp_path, "B4-HAND-2", outcome_extra=extra)

    assert _foreign_tickets(tmp_path) == 0


def test_missing_corpus_revision_is_not_counted(tmp_path: Path) -> None:
    extra = _rederivable()
    del extra["corpus_revision"]
    _write_pair(tmp_path, "B4-HAND-3", outcome_extra=extra)

    assert _foreign_tickets(tmp_path) == 0


def test_receipt_that_is_not_64_lowercase_hex_is_not_counted(tmp_path: Path) -> None:
    extra = _rederivable()
    extra["receipt_sha256"] = "A" * 64
    _write_pair(tmp_path, "B4-HAND-4", outcome_extra=extra)

    assert _foreign_tickets(tmp_path) == 0


def test_live_harness_log_still_yields_zero() -> None:
    """This checkout credits no B4 ticket — empty or missing log is still zero."""
    assert _foreign_tickets(REPO_LOG) == 0

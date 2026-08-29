"""F01 — reading the log while another process holds it: retry, then fail closed.

The reader's subject, not the writer's, and an incident rather than a hypothesis.
Windows denies a reader while a writer holds the path, and on 23 August 2026 every one
of six failed dispatches died with PermissionError raised out of `instructions.assemble`
-> `read_all` -> `read`, seconds after the scheduler had already printed that the work
was dispatched. Among them was the only Grok run, which is why one arm's usage never
moved while the scheduler reported it as busy.

The two halves of the rule are kept together because either alone is a defect. A
transient denial must be retried rather than killing the caller — the test proves the
reader was actually denied before it succeeded, so a silent pass cannot be mistaken for
a fix. A permanent denial must raise. Failing closed matters more than failing rarely: a
reader that gave up and returned no events would let every downstream decision be made
against an empty history while looking perfectly healthy — the same class of defect as a
check that cannot tell "condition false" from "check failed"."""

import pathlib
import pytest
from consilient import events_evidence
from consilient.events import EventError, read


def test_a_reader_survives_a_concurrent_writer_holding_the_file(tmp_path, monkeypatch):
    """Windows denies a reader while a writer holds the path; the read must retry, not die.

    This is not hypothetical. On 23 August 2026 every one of six failed dispatches died with
    PermissionError raised out of `instructions.assemble` -> `read_all` -> `read`, seconds after
    the scheduler had already printed that the work was dispatched. Among them was the only Grok
    run, which is why one arm's usage never moved while the scheduler reported it as busy.
    """
    log = tmp_path / "2026-08-23.jsonl"
    log.write_text("", encoding="utf-8")

    real_open = pathlib.Path.open
    attempts = {"n": 0}

    def flaky(self, *args, **kwargs):
        if self == log and attempts["n"] < 3:
            attempts["n"] += 1
            raise PermissionError(13, "Permission denied")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "open", flaky)
    monkeypatch.setattr(events_evidence, "_READ_BACKOFF", 0.001)

    got, rejected = read(log)
    assert attempts["n"] == 3, (
        "the reader must actually have been denied before succeeding"
    )
    assert got == [] and rejected == []


def test_a_permanently_held_file_refuses_rather_than_reporting_an_empty_trajectory(
    tmp_path, monkeypatch
):
    """Failing closed matters more than failing rarely.

    A reader that gave up and returned no events would let every downstream decision be made
    against an empty history while looking perfectly healthy — the same class of defect as a
    check that cannot tell "condition false" from "check failed".
    """
    log = tmp_path / "2026-08-23.jsonl"
    log.write_text("", encoding="utf-8")

    def always_denied(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(pathlib.Path, "open", always_denied)
    monkeypatch.setattr(events_evidence, "_READ_BACKOFF", 0.001)

    with pytest.raises(EventError) as excinfo:
        read(log)
    assert "held by another process" in str(excinfo.value)

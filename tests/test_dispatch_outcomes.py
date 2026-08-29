"""What a finished run is called, and what is written down about it.

Classification and recording are one subject because the second is only as honest as the
first. A trust banner with no work is silent even on exit 0; a 5 kB transcript is not —
codex twice wrote the artefact and was recorded silent because the marker appeared
inside a dumped agents.md, which is why the size of the transcript now enters the
judgement. An empty exit 0 is silent, a timeout is never called ok, and a run classified
silent is recorded silent rather than retried on another pool: the retry would spend a
second plan on a fault that is not the plan's.

The recording side pins what reaches the trajectory. A refusal and the capability gap it
constitutes are appended together (V0-41) — the gap is the same event seen from the
user's side, not a side note. Fan-out contributors must carry distinct `evidence_class`
values, because two arms recorded as the same class would make echo indistinguishable
from consilience in the log. The claim lifecycle opens before the run and completes
after it, so the outcome is no longer the last event in the file and is found by kind
rather than position. A non-ok outcome emits only a privacy-bounded error identity:
component, type and code, with no path, no command and no transcript. Run identities are
deterministic and the status vocabulary is closed — `parse_status` refuses a plausible-
looking word like "success"."""

from family_source import seam

import json
from datetime import datetime, timezone
import pytest
from consilient.events import read, validate
from consilient.harness import (
    DEFAULT_POOLS,
    Harness,
    classify_artefact,
    harness_by_id,
    judge_fanout,
    make_run_id,
    parse_status,
    record_fanout,
    record_outcome,
    record_refusal,
    select,
)
from dispatch_helpers import (
    INSTALLED,
    _load_script,
)


def test_workspace_trust_message_is_silent_even_when_exit_is_zero():
    status, reason = classify_artefact(
        exit_code=0,
        stdout="Workspace Trust Required\n",
        stderr="",
        output_bytes=24,
        diff_bytes=0,
        timed_out=False,
    )
    assert status == "silent"
    assert "workspace trust required" in reason


def test_trust_marker_in_a_large_transcript_is_not_silent():
    """Codex twice wrote the artefact and was recorded silent because the marker
    appeared in a dumped agents.md. A banner with no work is silent; a 5 kB
    transcript is not."""
    status, reason = classify_artefact(
        exit_code=0,
        stdout="Completed naming-repo.md\n",
        stderr="workspace trust required appears inside a dump\n" + ("x" * 3000),
        output_bytes=5000,
        diff_bytes=0,
        timed_out=False,
    )
    assert status == "ok"
    assert "artefact" in reason


def test_empty_exit_zero_is_silent():
    status, reason = classify_artefact(
        exit_code=0,
        stdout="",
        stderr="",
        output_bytes=0,
        diff_bytes=0,
        timed_out=False,
    )
    assert status == "silent"
    assert "empty" in reason


def test_nonempty_transcript_is_ok():
    status, reason = classify_artefact(
        exit_code=0,
        stdout="pong\n",
        stderr="",
        output_bytes=5,
        diff_bytes=0,
        timed_out=False,
    )
    assert status == "ok"
    assert reason == "produced an artefact"


def test_timeout_is_not_called_ok():
    status, _reason = classify_artefact(
        exit_code=None,
        stdout="",
        stderr="",
        output_bytes=0,
        diff_bytes=0,
        timed_out=True,
    )
    assert status == "timeout"


def test_fanout_agreement_and_disagreement():
    assert judge_fanout("pong", "pong", True, True) == "agree"
    assert judge_fanout("pong", "ping", True, True) == "disagree"
    assert judge_fanout("pong", "pong", True, False) == "incomparable"


def test_refusal_and_outcome_go_through_append(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    recorded = record_refusal(
        tmp_path,
        ts=ts,
        run_id="run-1",
        task="pong",
        cwd=str(tmp_path),
        reason="no eligible harness",
        considered=("claude: exhausted",),
    )
    assert recorded["event"] == "dispatch.refused"
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    # The refusal and the capability gap it constitutes are recorded together (V0-41):
    # the gap is the same event seen from the user's side, not a side note.
    assert [event.kind for event in events] == ["dispatch.refused", "capability.gap"]
    assert events[0].raw == recorded
    assert events[1].data["run_id"] == "run-1"

    grok = harness_by_id("grok")
    assert grok is not None
    outcome = record_outcome(
        tmp_path,
        ts=datetime.now(timezone.utc).isoformat(),
        run_id="run-2",
        task="pong",
        cwd=str(tmp_path),
        harness=grok,
        status="silent",
        reason="Workspace Trust Required",
        exit_code=0,
        artefact_bytes=24,
        diff_bytes=0,
        timed_out=False,
        duration_s=1.2,
        command=("cursor-agent", "-p"),
    )
    assert outcome["event"] == "dispatch.outcome"
    assert outcome["data"]["status"] == "silent"


def test_fanout_event_names_distinct_evidence_classes(tmp_path):
    first = harness_by_id("cursor-composer")
    second = harness_by_id("grok")
    assert first is not None and second is not None
    ts = datetime.now(timezone.utc).isoformat()
    recorded = record_fanout(
        tmp_path,
        ts=ts,
        run_id="fan-1",
        task="pong",
        cwd=str(tmp_path),
        first=first,
        second=second,
        first_status="ok",
        second_status="ok",
        verdict="disagree",
        first_run_id="a",
        second_run_id="b",
    )
    validate(recorded)
    classes = [row["evidence_class"] for row in recorded["data"]["contributors"]]
    assert classes[0] != classes[1]
    assert classes[0].startswith("family:")


def test_non_ok_dispatch_emits_only_a_privacy_bounded_error_identity(tmp_path):
    from consilient.error_tracking import read_records

    script = _load_script()
    harness = harness_by_id("grok")
    assert harness is not None
    result = script.RunResult(
        harness=harness,
        status="timeout",
        reason=r"C:\\private\\repo token=must-not-appear",
        exit_code=None,
        stdout="private output",
        stderr="private error",
        artefact_bytes=1,
        diff_bytes=0,
        timed_out=True,
        duration_s=1.0,
        command=("secret-command",),
        run_id="run-error",
        stdout_path="private-stdout",
        stderr_path="private-stderr",
    )

    script.record_dispatch_error(tmp_path, result)

    records = read_records(tmp_path / "errors" / "errors.jsonl")
    assert len(records) == 1
    assert records[0]["component"] == "dispatch.grok"
    assert records[0]["error_type"] == "DispatchOutcome"
    assert records[0]["error_code"] == "timeout"
    assert "private" not in json.dumps(records[0]).casefold()


def test_silent_run_is_not_retried_on_another_pool(tmp_path, monkeypatch):
    script = _load_script()
    grok = harness_by_id("grok")
    assert grok is not None
    calls = {"n": 0}

    def fake_run(harness: Harness, **kwargs):
        calls["n"] += 1
        assert kwargs["max_turns"] == 7
        assert kwargs["max_tokens"] == 1234
        return script.RunResult(
            harness=harness,
            status="silent",
            reason="harness produced no work: 'workspace trust required' (exit 0)",
            exit_code=0,
            stdout="Workspace Trust Required\n",
            stderr="",
            artefact_bytes=24,
            diff_bytes=0,
            timed_out=False,
            duration_s=0.1,
            command=("cursor-agent", "-p"),
            run_id="run-silent",
            stdout_path=str(tmp_path / "stdout.txt"),
            stderr_path=str(tmp_path / "stderr.txt"),
        )

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", fake_run)
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="grok"),
        task="pong",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        max_turns=7,
        max_tokens=1234,
    )
    assert calls["n"] == 1
    assert payload["status"] == "silent"
    assert code == 3
    events, rejected = read(
        tmp_path / "log" / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    )
    assert not rejected
    # The claim lifecycle (open before the run, complete after) means the outcome is
    # no longer the last event in the file; find it by kind, not position.
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert outcomes[-1].data["status"] == "silent"


def test_make_run_id_is_stable_for_the_same_inputs():
    ts = "2026-08-21T12:00:00+00:00"
    assert make_run_id(ts, "pong", "grok") == make_run_id(ts, "pong", "grok")
    assert make_run_id(ts, "pong", "grok") != make_run_id(ts, "pong", "claude")


def test_parse_status_rejects_unknown_values():
    assert parse_status("silent") == "silent"
    with pytest.raises(ValueError, match="unknown dispatch status"):
        parse_status("success")

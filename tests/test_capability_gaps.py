"""V0-41: a capability gap is a first-class recorded event, and the record closes the loop.

The invariant has three parts, each with a check here:
  1. the event contract — a gap names what was asked, what was attempted, how it failed
     (one of four classes that may not be conflated), and which side of the self-healing
     boundary it sits on; `silent` and `not_implemented` may never claim `retry`;
  2. the wiring — the existing dispatch chokepoints (record_refusal, record_outcome)
     record the gap alongside their own event, so a caller cannot forget it;
  3. the view — the dashboard ranks gaps by repetition, because a gap hit twice is a
     stronger signal than a novel one, and states the retry/escalate boundary in words.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import coordination
from consilient.dashboard import build_payload, render_html
from consilient.events import EventError, append, read, read_all, validate
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    Probe,
    classify_gap,
    harness_by_id,
    record_outcome,
    record_refusal,
    select,
)

DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"

INSTALLED = tuple(
    Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
)


def _load_script():
    name = "consilient_dispatch_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _gap_data(**overrides):
    data = {
        "asked": "deploy the staging environment",
        "attempted": "grok",
        "failure": "failed",
        "detail": "exit 1: terraform not configured",
        "closure": "retry",
        "repair": "re-dispatch the task",
        "run_id": "run-1",
        "source": "dispatch.outcome",
    }
    data.update(overrides)
    return data


def _append_gap(log_dir: Path, ts: str, **overrides):
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": 1,
            "ts": ts,
            "event": "capability.gap",
            "actor": "dispatch",
            "data": _gap_data(**overrides),
        },
    )


# ---------------------------------------------------------------- the contract


def test_a_well_formed_gap_is_accepted_and_readable(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    recorded = _append_gap(tmp_path, ts)
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    assert events[0].raw == recorded
    assert events[0].kind == "capability.gap"


@pytest.mark.parametrize(
    "field", ("asked", "attempted", "detail", "repair", "run_id", "source")
)
def test_a_gap_missing_a_required_field_is_refused(tmp_path, field):
    ts = datetime.now(timezone.utc).isoformat()
    data = _gap_data()
    data.pop(field)
    with pytest.raises(EventError, match=field):
        append(
            tmp_path / f"{ts[:10]}.jsonl",
            {
                "v": 1,
                "ts": ts,
                "event": "capability.gap",
                "actor": "dispatch",
                "data": data,
            },
        )


def test_a_gap_with_an_unknown_failure_class_is_refused(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="failure"):
        _append_gap(tmp_path, ts, failure="crashed")


def test_a_gap_with_an_unknown_closure_is_refused(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="closure"):
        _append_gap(tmp_path, ts, closure="ignore")


def test_a_silent_gap_may_not_claim_to_retry(tmp_path):
    # The cross-field rule: a silent run already reported success while doing nothing;
    # an unattended retry repeats the lie with pool spend attached.
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="escalate"):
        _append_gap(tmp_path, ts, failure="silent", closure="retry")


def test_a_not_implemented_gap_may_not_claim_to_retry(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="escalate"):
        _append_gap(tmp_path, ts, failure="not_implemented", closure="retry")


@pytest.mark.parametrize("failure", ("refused", "failed"))
def test_a_loud_or_policy_gap_may_retry(tmp_path, failure):
    ts = datetime.now(timezone.utc).isoformat()
    recorded = _append_gap(tmp_path, ts, failure=failure, closure="retry")
    assert validate(recorded)["data"]["closure"] == "retry"


# ---------------------------------------------------------------- the policy


def test_classify_gap_leaves_a_success_alone():
    assert classify_gap("ok", "") is None


def test_classify_gap_escalates_a_silent_run():
    failure, closure, repair = classify_gap("silent", "exit 0, no artefact")
    assert (failure, closure) == ("silent", "escalate")
    assert "human" in repair


@pytest.mark.parametrize("status", ("failed", "timeout"))
def test_classify_gap_retries_a_loud_failure(status):
    failure, closure, _ = classify_gap(status, "exit 1")
    assert (failure, closure) == ("failed", "retry")


@pytest.mark.parametrize(
    "reason",
    (
        "grok is not installed",
        "binary not on PATH",
        "no invocation for harness 'cursor'",
        "unknown harness 'hal'",
        "no models registered for cursor",
    ),
)
def test_classify_gap_escalates_a_missing_capability(reason):
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("not_implemented", "escalate")


@pytest.mark.parametrize(
    "reason",
    (
        "claude is exhausted (92% used)",
        "claims overlap a live dispatch: other-run holds src",
    ),
)
def test_classify_gap_retries_what_time_closes(reason):
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("refused", "retry")


def test_classify_gap_escalates_an_unrecognised_refusal():
    failure, closure, repair = classify_gap("refused", "policy forbids this cwd")
    assert (failure, closure) == ("refused", "escalate")
    assert "human" in repair


def test_the_aggregate_selection_refusal_escalates_rather_than_guesses():
    # "every pool is exhausted, unknown, or not installed" is ambiguous from prose
    # alone: it may name a resettable window or a missing install. The record fails
    # closed — not_implemented, escalate — because guessing is the failure this event
    # exists to record. Pinned deliberately: loosening this is a policy change.
    reason = (
        "no eligible harness: every pool is exhausted, unknown, or not installed. "
        "claude: exhausted; grok: not installed"
    )
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("not_implemented", "escalate")


def test_the_reasons_select_generates_classify_as_intended():
    # The markers match prose this codebase writes, and this is the check that keeps
    # them matched: reword the reason and this fails loudly instead of misclassifying.
    exhausted = select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="claude")
    assert exhausted.kind == "refuse"
    assert classify_gap("refused", exhausted.reason)[:2] == ("refused", "retry")

    missing = select(
        probes=tuple(
            Probe(item.id, False, None, "missing") for item in HARNESSES
        ),
        pools=DEFAULT_POOLS,
        requested="grok",
    )
    assert missing.kind == "refuse"
    assert classify_gap("refused", missing.reason)[:2] == (
        "not_implemented",
        "escalate",
    )


# ---------------------------------------------------------------- the wiring


def test_a_recorded_refusal_also_records_a_gap(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    record_refusal(
        tmp_path,
        ts=ts,
        run_id="run-1",
        task="refactor the billing module",
        cwd=str(tmp_path),
        reason="claude is exhausted (92% used)",
        considered=("claude",),
    )
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    assert [event.kind for event in events] == ["dispatch.refused", "capability.gap"]
    gap = events[1].data
    assert gap["asked"] == "refactor the billing module"
    assert gap["failure"] == "refused"
    assert gap["closure"] == "retry"
    assert gap["source"] == "dispatch.refused"
    assert gap["run_id"] == "run-1"


def test_a_silent_outcome_records_a_gap_that_escalates(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    cursor = harness_by_id("cursor-composer")
    assert cursor is not None
    record_outcome(
        tmp_path,
        ts=ts,
        run_id="run-2",
        task="summarise the sprint",
        cwd=str(tmp_path),
        harness=cursor,
        status="silent",
        reason="exit 0, no artefact, no diff",
        exit_code=0,
        artefact_bytes=0,
        diff_bytes=0,
        timed_out=False,
        duration_s=3.0,
        command=("cursor-agent", "-p"),
    )
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    assert [event.kind for event in events] == ["dispatch.outcome", "capability.gap"]
    gap = events[1].data
    assert gap["failure"] == "silent"
    assert gap["closure"] == "escalate"
    assert gap["attempted"] == "cursor-composer"
    assert gap["source"] == "dispatch.outcome"


def test_an_ok_outcome_records_no_gap(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    grok = harness_by_id("grok")
    assert grok is not None
    record_outcome(
        tmp_path,
        ts=ts,
        run_id="run-3",
        task="pong",
        cwd=str(tmp_path),
        harness=grok,
        status="ok",
        reason="artefact written",
        exit_code=0,
        artefact_bytes=42,
        diff_bytes=10,
        timed_out=False,
        duration_s=1.0,
        command=("grok",),
    )
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    assert [event.kind for event in events] == ["dispatch.outcome"]


def test_a_failed_outcome_records_a_retryable_gap(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    grok = harness_by_id("grok")
    assert grok is not None
    record_outcome(
        tmp_path,
        ts=ts,
        run_id="run-4",
        task="pong",
        cwd=str(tmp_path),
        harness=grok,
        status="failed",
        reason="exit 1",
        exit_code=1,
        artefact_bytes=0,
        diff_bytes=0,
        timed_out=False,
        duration_s=1.0,
        command=("grok",),
    )
    events, _ = read(tmp_path / f"{ts[:10]}.jsonl")
    gap = events[1].data
    assert (gap["failure"], gap["closure"]) == ("failed", "retry")


# ------------------------------------------------------- the dispatch boundary


def test_a_silent_dispatch_records_the_gap_at_the_boundary(tmp_path, monkeypatch):
    script = _load_script()
    log = tmp_path / "log"
    cursor = harness_by_id("cursor-composer")
    assert cursor is not None

    def fake_run(harness, **kwargs):
        return script.RunResult(
            harness=harness,
            status="silent",
            reason="exit 0, no artefact, no diff",
            exit_code=0,
            stdout="",
            stderr="",
            artefact_bytes=0,
            diff_bytes=0,
            timed_out=False,
            duration_s=2.0,
            command=("cursor-agent", "-p"),
            run_id=kwargs["run_id"],
            stdout_path=str(tmp_path / "stdout.txt"),
            stderr_path=str(tmp_path / "stderr.txt"),
        )

    monkeypatch.setattr(script, "run_harness", fake_run)
    payload, _ = script.dispatch_one(
        decision=select(
            probes=INSTALLED, pools=DEFAULT_POOLS, requested="cursor-composer"
        ),
        task="write the release notes",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=(),
    )
    assert payload["status"] == "silent"
    events, rejected = read_all(log)
    assert not rejected
    gaps = [event for event in events if event.kind == "capability.gap"]
    assert len(gaps) == 1
    assert gaps[0].data["failure"] == "silent"
    assert gaps[0].data["closure"] == "escalate"
    assert gaps[0].data["asked"] == "write the release notes"
    assert gaps[0].data["source"] == "dispatch.outcome"


def test_a_selection_refusal_records_the_gap(tmp_path, monkeypatch):
    script = _load_script()
    log = tmp_path / "log"

    def forbidden(*_args, **_kwargs):
        raise AssertionError("run_harness must not run when selection refused")

    monkeypatch.setattr(script, "run_harness", forbidden)
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="claude"),
        task="pong",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=(),
    )
    assert payload["status"] == "refused"
    assert code == 2
    events, rejected = read_all(log)
    assert not rejected
    gaps = [event for event in events if event.kind == "capability.gap"]
    assert len(gaps) == 1
    assert gaps[0].data["failure"] == "refused"
    assert gaps[0].data["closure"] == "retry"
    assert gaps[0].data["source"] == "dispatch.refused"


def test_a_claim_conflict_records_a_retryable_gap(tmp_path, monkeypatch):
    script = _load_script()
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="other-run",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=datetime.now(timezone.utc),
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("run_harness must not run when a claim conflicts")

    monkeypatch.setattr(script, "run_harness", forbidden)
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="grok"),
        task="pong",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=("src/consilient",),
    )
    assert payload["status"] == "refused"
    assert code == 2
    events, rejected = read_all(log)
    assert not rejected
    gaps = [event for event in events if event.kind == "capability.gap"]
    assert len(gaps) == 1
    assert gaps[0].data["failure"] == "refused"
    assert gaps[0].data["closure"] == "retry"
    assert "src/consilient" in gaps[0].data["attempted"]


# ---------------------------------------------------------------- the view


def _payload_over(events_dir: Path):
    events, rejected = read_all(events_dir)
    assert not rejected
    return build_payload(
        events,
        rejected,
        doctor={
            "routing_orchestration_enabled": False,
            "gates": {},
            "generated_at": "now",
        },
        beta_result={
            "verdict": "unmeasured",
            "n_rejected": 0,
            "n_false_accept": 0,
            "caveat": "no data",
            "lower_bound_on_joint_error": False,
        },
        beta_line="beta: no data",
        bypassed=0,
    )


def test_the_gap_view_ranks_repetition_above_novelty(tmp_path):
    # The same gap hit twice, then a DIFFERENT gap hit once LATER. Recency alone would
    # put the novel one on top; the view must rank the repeated one first, because a
    # gap hit twice is the stronger signal. (This ordering is what a mutant dropping
    # the count sort breaks — pinned after exactly that mutant survived a weaker
    # version of this test that gave every event the same timestamp.)
    base = datetime.now(timezone.utc)
    t1 = base.isoformat()
    t2 = (base + timedelta(microseconds=1)).isoformat()
    t3 = (base + timedelta(microseconds=2)).isoformat()
    _append_gap(tmp_path, t1, run_id="run-1", failure="failed", detail="exit 1")
    _append_gap(tmp_path, t2, run_id="run-2", failure="failed", detail="exit 1 again")
    _append_gap(
        tmp_path,
        t3,
        run_id="run-3",
        failure="silent",
        closure="escalate",
        repair="a human inspects",
        attempted="cursor-composer",
        detail="exit 0, nothing written",
    )
    payload = _payload_over(tmp_path)
    gaps = payload["capability_gaps"]
    assert gaps["total"] == 3
    assert gaps["distinct"] == 2
    top = gaps["rows"][0]
    assert top["count"] == 2
    assert top["failure"] == "failed"
    assert top["latest_detail"] == "exit 1 again"
    assert gaps["rows"][1]["count"] == 1
    assert gaps["rows"][1]["last_seen"] == t3
    # The boundary is stated, not implied.
    assert "retry" in gaps["boundary"]
    assert "escalate" in gaps["boundary"]


def test_the_gap_view_groups_by_the_normalised_triple_not_the_verbatim_detail(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    _append_gap(tmp_path, ts, run_id="run-1", detail="exit 1 on Monday")
    _append_gap(tmp_path, ts, run_id="run-2", detail="exit 1 on Tuesday")
    payload = _payload_over(tmp_path)
    assert payload["capability_gaps"]["distinct"] == 1


def test_an_empty_gap_view_says_absence_is_not_proof(tmp_path):
    payload = _payload_over(tmp_path)
    gaps = payload["capability_gaps"]
    assert gaps["total"] == 0
    assert gaps["rows"] == []
    html = render_html(payload)
    assert "absence of" in html
    assert "not proof none occurred" in html


def test_the_gap_panel_is_wired_into_the_page(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    _append_gap(tmp_path, ts)
    html = render_html(_payload_over(tmp_path))
    assert 'id="t-capgaps"' in html
    assert 'for="t-capgaps"' in html
    assert 'id="p-capgaps"' in html
    assert "Capability gaps" in html
    assert "self-healing boundary" in html
    assert "<script" not in html

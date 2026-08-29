"""V0-41, part two: the wiring, so that a caller cannot forget to record a gap.

The same claim is checked at two altitudes. In the library, the existing dispatch
chokepoints — `record_refusal` and `record_outcome` — write the capability.gap event
alongside their own event, in that order, within the same call: a refusal on an
exhausted pool yields `refused`/`retry`, a silent outcome yields `silent`/`escalate`
naming the harness attempted, a loud failure yields `failed`/`retry`. An `ok` outcome
records the outcome and nothing else, which is the check that keeps the gap log a record
of gaps rather than a second copy of the run log.

At the boundary, `scripts/dispatch.py` is loaded from source and `dispatch_one` is
driven with the harness runner stubbed, because the gap must be recorded by the
machinery rather than by whatever the harness happened to return. The refusal paths go
further and make running an assertion failure: when selection refuses, and when an open
claim on `src` overlaps the requested paths, no harness may be invoked at all, the call
must exit 2, and exactly one gap must reach the log — the claim conflict carrying the
overlapping path in `attempted` and closing as `retry`, because a claim expires."""

from family_source import seam

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from consilient import coordination
from consilient.events import read, read_all
from consilient.harness import (
    DEFAULT_POOLS,
    harness_by_id,
    record_outcome,
    record_refusal,
    select,
)
from capability_gap_helpers import (
    INSTALLED,
)

DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"


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

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", fake_run)
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

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", forbidden)
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

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", forbidden)
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

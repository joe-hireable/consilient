"""Dispatch policy and runner. Invariants ship with the check that can fail.

The load-bearing ones:
  - an exhausted pool is never selected while any other pool has headroom
  - automatic selection never spends unknown headroom
  - a silent exit-0 is recorded silent, not retried on another pool
  - fan-out requires two different families
  - the consil CLI surface is unchanged
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient.cli import build_parser
from consilient.events import read, validate
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    EXHAUSTED_USED_PERCENT,
    Harness,
    PoolState,
    Probe,
    classify_artefact,
    cursor_pool_for_model,
    harness_by_id,
    judge_fanout,
    load_pools,
    make_run_id,
    parse_status,
    pools_from_mapping,
    record_fanout,
    record_outcome,
    record_refusal,
    remaining_percent,
    select,
    select_fanout,
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


def _pool(
    name: str,
    *,
    used: float | None,
    exhausted: bool = False,
    note: str = "",
) -> PoolState:
    return PoolState(
        name=name,
        used_percent=used,
        exhausted=exhausted,
        note=note,
        observed_at="2026-08-21T00:00:00+00:00",
        source="test",
    )


def _probes(*missing: str) -> tuple[Probe, ...]:
    skip = set(missing)
    return tuple(
        Probe(item.id, item.id not in skip, "1.0" if item.id not in skip else None, "fixture")
        for item in HARNESSES
    )


def test_default_snapshot_prefers_cursor_models_over_grok():
    decision = select(probes=INSTALLED, pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "cursor-composer"
    assert "claude" not in decision.reason


def test_exhausted_pool_with_lowest_used_percent_is_never_selected():
    """Mutation target: ranking on used_percent alone would pick claude at 0%."""
    pools = (
        _pool("claude-weekly", used=0.0, exhausted=True, note="nearly exhausted"),
        _pool("cursor-models", used=40.0),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=50.0),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=INSTALLED, pools=pools)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "cursor-composer"
    assert decision.harness.pool != "claude-weekly"
    assert remaining_percent(pools[0]) == 100.0


def test_automatic_selection_refuses_when_only_the_exhausted_pool_is_left():
    pools = (
        _pool("claude-weekly", used=None, exhausted=True, note="nearly exhausted"),
        _pool("cursor-models", used=1.0),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=2.0),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=_probes("cursor-composer", "grok", "codex"), pools=pools)
    assert decision.kind == "refuse"
    assert decision.harness is None
    assert "exhausted" in decision.reason
    assert "claude" in decision.reason


def test_unknown_headroom_is_not_selected_automatically():
    pools = (
        _pool("claude-weekly", used=None, exhausted=True),
        _pool("cursor-models", used=None, note="unknown"),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=None, note="unknown"),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=INSTALLED, pools=pools)
    assert decision.kind == "refuse"
    assert "unknown" in decision.reason


def test_explicit_unknown_harness_is_attended_not_a_fallback():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="codex",
    )
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "codex"


def test_explicit_exhausted_harness_is_refused_without_override():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="claude",
    )
    assert decision.kind == "refuse"
    assert decision.harness is None
    assert "exhausted" in decision.reason


def test_allow_exhausted_is_required_to_spend_claude():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="claude",
        allow_exhausted=True,
    )
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "claude"


def test_missing_install_is_not_selected():
    decision = select(probes=_probes("cursor-composer"), pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "grok"


def test_fanout_picks_two_different_families():
    decision = select_fanout(probes=INSTALLED, pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.first is not None and decision.second is not None
    assert decision.first.family != decision.second.family
    assert {decision.first.id, decision.second.id} == {"cursor-composer", "grok"}


def test_fanout_refuses_when_only_one_family_is_eligible():
    decision = select_fanout(
        probes=_probes("cursor-composer", "codex", "claude"),
        pools=DEFAULT_POOLS,
    )
    assert decision.kind == "refuse"
    assert decision.first is None
    assert "different model families" in decision.reason


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


def test_cursor_vendor_aliases_draw_on_the_avoided_pool():
    assert cursor_pool_for_model("composer-2.5") == "cursor-models"
    assert cursor_pool_for_model("claude-4-sonnet") == "cursor-other"
    assert cursor_pool_for_model("gpt-5") == "cursor-other"
    assert cursor_pool_for_model("gemini-3.7-flash") == "cursor-other"


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
    assert len(events) == 1
    assert events[0].raw == recorded

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


def test_pools_from_file_override_defaults(tmp_path):
    path = tmp_path / "headroom.json"
    path.write_text(
        json.dumps(
            {
                "observed_at": "2026-08-21T12:00:00+00:00",
                "source": "test file",
                "pools": {"grok-weekly": {"used_percent": 80}},
            }
        ),
        encoding="utf-8",
    )
    pools = load_pools(path)
    grok = next(item for item in pools if item.name == "grok-weekly")
    claude = next(item for item in pools if item.name == "claude-weekly")
    assert grok.used_percent == 80.0
    assert claude.exhausted is True


def test_used_percent_at_threshold_is_exhausted():
    pools = pools_from_mapping(
        {
            "observed_at": "2026-08-21T00:00:00+00:00",
            "source": "t",
            "pools": {"grok-weekly": {"used_percent": EXHAUSTED_USED_PERCENT}},
        }
    )
    grok = next(item for item in pools if item.name == "grok-weekly")
    assert grok.exhausted is True
    assert remaining_percent(grok) == 100.0 - EXHAUSTED_USED_PERCENT


def test_dispatch_is_a_script_not_a_consil_subcommand():
    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    assert set(subparsers.choices) == {"record", "replay", "beta", "doctor"}
    assert DISPATCH_PATH.is_file()
    source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "silently" in source.lower() or "NOT retried" in source


def test_wsl_path_translation_is_absolute():
    script = _load_script()
    converted = script.to_wsl_path(Path("C:/Users/jpbpr/Repositories/consilient-w-orch-b"))
    assert converted.startswith("/mnt/c/")
    assert "C:" not in converted
    assert "\\" not in converted


def test_run_process_writes_an_artefact_file(tmp_path):
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, _duration = script.run_process(
        [sys.executable, "-c", "print('pong')"],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=20,
    )
    assert timed_out is False
    assert code == 0
    assert "pong" in stdout_path.read_text(encoding="utf-8")


def test_run_process_kills_a_sleeping_child(tmp_path):
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, duration = script.run_process(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=2,
    )
    assert timed_out is True
    assert duration < 15
    assert code != 0 or timed_out


def test_cursor_other_models_are_refused_by_the_runner(tmp_path):
    script = _load_script()
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    built = script.build_command(
        harness,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="gpt-5",
    )
    assert isinstance(built, str)
    assert "Other Models" in built


def test_silent_run_is_not_retried_on_another_pool(tmp_path, monkeypatch):
    script = _load_script()
    grok = harness_by_id("grok")
    assert grok is not None
    calls = {"n": 0}

    def fake_run(harness: Harness, **_kwargs):
        calls["n"] += 1
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

    monkeypatch.setattr(script, "run_harness", fake_run)
    payload, code = script.dispatch_one(
        decision=select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="grok"),
        task="pong",
        cwd=tmp_path,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
    )
    assert calls["n"] == 1
    assert payload["status"] == "silent"
    assert code == 3
    events, rejected = read(tmp_path / "log" / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl")
    assert not rejected
    assert events[-1].data["status"] == "silent"


def test_make_run_id_is_stable_for_the_same_inputs():
    ts = "2026-08-21T12:00:00+00:00"
    assert make_run_id(ts, "pong", "grok") == make_run_id(ts, "pong", "grok")
    assert make_run_id(ts, "pong", "grok") != make_run_id(ts, "pong", "claude")


def test_parse_status_rejects_unknown_values():
    assert parse_status("silent") == "silent"
    with pytest.raises(ValueError, match="unknown dispatch status"):
        parse_status("success")

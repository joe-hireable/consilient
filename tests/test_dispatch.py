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
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient.cli import build_parser
from consilient.events import read, validate
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    Decision,
    permission_flags,
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
    assert set(subparsers.choices) == {
        "record",
        "replay",
        "beta",
        "doctor",
        "dashboard",
        "usage",
    }
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


@pytest.mark.parametrize("harness_id", ("claude", "grok", "codex"))
def test_brief_is_delivered_by_reference(monkeypatch, tmp_path, harness_id):
    script = _load_script()
    monkeypatch.setattr(script, "find_claude", lambda: "claude")
    monkeypatch.setattr(script, "find_grok", lambda: "grok")
    monkeypatch.setattr(script, "find_codex", lambda: "codex")
    monkeypatch.setattr(script, "help_text", lambda _argv: "")
    monkeypatch.setattr(script, "metered_grok_reason", lambda: None)
    harness = harness_by_id(harness_id)
    assert harness is not None
    brief = (tmp_path / "brief.md").resolve()
    task = "INLINE_TASK_SENTINEL $(touch escaped) `also escaped`"

    built = script.build_command(
        harness,
        task=task,
        cwd=tmp_path,
        brief=brief,
        model=None,
    )

    assert isinstance(built, list)
    command = " ".join(str(part) for part in built)
    assert "INLINE_TASK_SENTINEL" not in command
    assert brief.as_posix() in command


def test_run_harness_scrubs_git_environment(monkeypatch, tmp_path):
    script = _load_script()
    monkeypatch.setenv("GIT_DIR", "C:/wrong/repository/.git")
    monkeypatch.setenv("GIT_WORK_TREE", "C:/wrong/repository")
    monkeypatch.setenv("GIT_INDEX_FILE", "C:/wrong/repository/index")
    monkeypatch.setattr(script, "build_command", lambda *_args, **_kwargs: ["agent"])
    captured: dict[str, str] = {}

    def fake_run_process(_argv, *, env, **_kwargs):
        captured.update(env)
        return 0, False, 0.1

    monkeypatch.setattr(script, "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None

    script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="run-1",
    )

    assert not any(key.startswith("GIT_") for key in captured)
    assert captured["PYTHONDONTWRITEBYTECODE"] == "1"


def test_bypass_flags_are_known_for_every_registered_harness():
    for item in HARNESSES:
        flags = permission_flags(item.id, "bypass")
        assert flags, f"{item.id} has no bypass flags; the meta-harness cannot control it"
        assert permission_flags(item.id, "prompt") == ()


def test_claude_bypass_always_skips_permissions(monkeypatch, tmp_path):
    script = _load_script()
    monkeypatch.setattr(script, "find_claude", lambda: "claude")
    harness = harness_by_id("claude")
    assert harness is not None
    built = script.build_command(
        harness,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        permissions="bypass",
    )
    assert isinstance(built, list)
    assert "--dangerously-skip-permissions" in built
    prompted = script.build_command(
        harness,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        permissions="prompt",
    )
    assert isinstance(prompted, list)
    assert "--dangerously-skip-permissions" not in prompted


def test_explicit_cursor_other_model_is_attended(tmp_path):
    """Automatic selection avoids the Other pool; an explicit --model is the operator naming it."""
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
    assert isinstance(built, list)
    assert any("gpt-5" in str(part) for part in built)


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
    # The claim lifecycle (open before the run, complete after) means the outcome is
    # no longer the last event in the file; find it by kind, not position.
    outcomes = [event for event in events if event.kind == "dispatch.outcome"]
    assert outcomes[-1].data["status"] == "silent"


def test_resolve_cwd_allows_this_repository_root():
    script = _load_script()
    assert script.resolve_cwd(str(script.ROOT)) == script.ROOT


def test_resolve_cwd_allows_a_directory_inside_this_repository():
    script = _load_script()
    inside = script.ROOT / "scripts"
    assert inside.is_dir()
    assert script.resolve_cwd(str(inside)) == inside.resolve()


def test_resolve_cwd_refuses_a_path_outside_this_repository(tmp_path):
    """Gate B has a check now. AGENTS.md forbade pointing this at another repository and
    nothing enforced it; `Path(value).resolve()` accepted every path on the machine.

    The outside path is constructed under tmp_path deliberately: proving the boundary must
    not require reading, resolving or naming a private corpus.
    """
    script = _load_script()
    outside = tmp_path / "some-other-repo"
    outside.mkdir()
    with pytest.raises(ValueError, match="only inside its own repository"):
        script.resolve_cwd(str(outside))


def test_resolve_cwd_has_no_override_flag():
    """A second path to the same state is the same hole. There is no --gate-b-approved."""
    source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "gate-b-approved" not in source
    assert "--allow-foreign" not in source


def test_load_allowed_roots_missing_file_is_empty(tmp_path):
    script = _load_script()
    assert script.load_allowed_roots(tmp_path / "no-such.json") == ()


def test_load_allowed_roots_skips_missing_directories(tmp_path):
    script = _load_script()
    present = tmp_path / "present"
    present.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(
        json.dumps({"roots": [str(present), str(tmp_path / "gone")]}) + "\n",
        encoding="utf-8",
    )
    assert script.load_allowed_roots(allow) == (present.resolve(),)


def test_load_allowed_roots_refuses_a_filesystem_root(tmp_path):
    script = _load_script()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(tmp_path.anchor)]}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="filesystem root"):
        script.load_allowed_roots(allow)


def test_load_allowed_roots_malformed_json_fails_closed(tmp_path):
    script = _load_script()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        script.load_allowed_roots(allow)


def test_resolve_cwd_allows_an_instance_listed_root(tmp_path):
    script = _load_script()
    foreign = tmp_path / "authorised-repo"
    foreign.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(foreign)]}) + "\n", encoding="utf-8")
    assert script.resolve_cwd(str(foreign), allowed_file=allow) == foreign.resolve()


def test_resolve_cwd_allows_a_subdirectory_of_an_instance_listed_root(tmp_path):
    script = _load_script()
    foreign = tmp_path / "authorised-repo"
    inside = foreign / "frontend"
    inside.mkdir(parents=True)
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(foreign)]}) + "\n", encoding="utf-8")
    assert script.resolve_cwd(str(inside), allowed_file=allow) == inside.resolve()


def test_resolve_cwd_still_refuses_an_unlisted_foreign_root_when_allowlist_exists(tmp_path):
    script = _load_script()
    listed = tmp_path / "authorised-repo"
    listed.mkdir()
    other = tmp_path / "some-other-repo"
    other.mkdir()
    allow = tmp_path / "allowed-cwds.json"
    allow.write_text(json.dumps({"roots": [str(listed)]}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="only inside its own repository"):
        script.resolve_cwd(str(other), allowed_file=allow)


def test_allowed_cwds_instance_file_is_gitignored_and_the_example_ships():
    """PRODUCT ships the shape; INSTANCE keeps the machine paths."""
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/allowed-cwds.json" in ignored
    example = json.loads(
        Path(".harness/allowed-cwds.example.json").read_text(encoding="utf-8")
    )
    assert example["roots"] == []
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    tracked = subprocess.run(
        ["git", "ls-files", ".harness/allowed-cwds.json", ".harness/allowed-cwds.example.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=True,
    ).stdout.split()
    assert ".harness/allowed-cwds.example.json" in tracked
    assert ".harness/allowed-cwds.json" not in tracked


def _git(cwd: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "t@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "t@example.com"
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_wsl_cursor_inner_exports_git_dir_for_a_linked_worktree(tmp_path, monkeypatch):
    """R4. WSL git cannot resolve a Windows gitdir pointer in a linked worktree."""
    script = _load_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "commit", "--allow-empty", "-m", "seed")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", str(linked))
    monkeypatch.setattr(script, "cursor_native", lambda: None)
    monkeypatch.setattr(script, "wsl_bridge", lambda: "wsl")
    monkeypatch.setattr(script, "help_text", lambda _argv: "--force --trust")
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    built = script.build_command(
        harness,
        task="pong",
        cwd=linked,
        brief=tmp_path / "brief.md",
        model="composer-2.5",
    )
    assert isinstance(built, list)
    inner = built[-1]
    git_dir, work_tree = script.git_workspace(linked)
    assert git_dir is not None
    assert f"GIT_DIR={script.to_wsl_path(git_dir)}" in inner
    assert f"GIT_WORK_TREE={script.to_wsl_path(work_tree)}" in inner
    assert "cursor-agent" in inner


def test_native_cursor_command_does_not_inject_wsl_git_exports(tmp_path, monkeypatch):
    script = _load_script()
    monkeypatch.setattr(script, "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(script, "help_text", lambda _argv: "--force --trust")
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    built = script.build_command(
        harness,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="composer-2.5",
    )
    assert isinstance(built, list)
    assert all("GIT_DIR" not in str(part) for part in built)
    assert built[0] == "cursor-agent"


def test_cursor_run_holds_the_agent_lock(tmp_path, monkeypatch):
    script = _load_script()
    lock = tmp_path / "cursor-agent.lock"
    monkeypatch.setattr(script, "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    calls: list[str] = []
    orig = script.ExclusiveFileLock

    class Spy(orig):  # type: ignore[misc, valid-type]
        def __enter__(self):
            calls.append("enter")
            return super().__enter__()

        def __exit__(self, *exc: object):
            calls.append("exit")
            return super().__exit__(*exc)

    monkeypatch.setattr(script, "ExclusiveFileLock", Spy)
    monkeypatch.setattr(script, "run_process", lambda *_a, **_k: (0, False, 0.1))
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    result = script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="run-lock",
    )
    assert result.status in {"ok", "silent"}
    assert calls == ["enter", "exit"]


def test_non_cursor_run_does_not_take_the_cursor_lock(tmp_path, monkeypatch):
    script = _load_script()
    lock = tmp_path / "cursor-agent.lock"
    monkeypatch.setattr(script, "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(script, "build_command", lambda *_a, **_k: ["agent"])
    held: dict[str, bool] = {}

    def fake_run_process(_argv, **_kwargs):
        held["exists"] = lock.exists()
        return 0, False, 0.1

    monkeypatch.setattr(script, "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=tmp_path / "run",
        timeout_s=5,
        model=None,
        run_id="run-codex",
    )
    assert held.get("exists") is False


def test_dry_run_does_not_hold_the_cursor_lock(tmp_path, monkeypatch):
    script = _load_script()
    lock = tmp_path / "cursor-agent.lock"
    monkeypatch.setattr(script, "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(script, "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(script, "help_text", lambda _argv: "--force --trust")
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    decision = Decision(
        kind="run",
        harness=harness,
        reason="cursor-composer",
        considered=(),
    )
    payload, code = script.dispatch_one(
        decision=decision,
        task="noop",
        cwd=script.ROOT,
        log_dir=tmp_path / "log",
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model="composer-2.5",
        dry_run=True,
        permissions="bypass",
    )
    assert code == 0
    assert payload["status"] == "dry-run"
    assert not lock.exists()


def test_cursor_agent_lock_is_gitignored():
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/cursor-agent.lock" in ignored


def test_dry_run_outside_this_repository_is_refused_and_prints_no_command(tmp_path, capsys):
    script = _load_script()
    outside = tmp_path / "some-other-repo"
    outside.mkdir()
    code = script.main(["--dry-run", "--json", "--cwd", str(outside), "noop"])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "refused"
    assert "repository" in payload["reason"]
    assert str(outside.resolve()) in payload["reason"]
    assert "command" not in payload


def test_write_brief_without_a_log_is_the_task_alone(tmp_path):
    script = _load_script()
    brief = script.write_brief(tmp_path / "run", "pong")
    assert brief.read_text(encoding="utf-8") == "pong\n"


def test_write_brief_includes_a_recall_pack_from_the_log(tmp_path):
    from datetime import datetime, timezone

    from consilient.events import SCHEMA_VERSION, append

    script = _load_script()
    log = tmp_path / "log"
    log.mkdir()
    ts = datetime.now(timezone.utc).isoformat()
    append(
        log / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": "dispatch.outcome",
            "actor": "consilient.dispatch",
            "data": {
                "status": "ok",
                "harness": "grok",
                "task": "pong",
                "supervised": True,
            },
        },
    )
    brief = script.write_brief(tmp_path / "run", "continue the work", log_dir=log)
    text = brief.read_text(encoding="utf-8")
    assert text.startswith("continue the work")
    assert "Recall pack" in text
    assert "dispatch.outcome" in text


def test_make_run_id_is_stable_for_the_same_inputs():
    ts = "2026-08-21T12:00:00+00:00"
    assert make_run_id(ts, "pong", "grok") == make_run_id(ts, "pong", "grok")
    assert make_run_id(ts, "pong", "grok") != make_run_id(ts, "pong", "claude")


def test_parse_status_rejects_unknown_values():
    assert parse_status("silent") == "silent"
    with pytest.raises(ValueError, match="unknown dispatch status"):
        parse_status("success")

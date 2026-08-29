"""Launching the child process — the command built for each harness, the environment it
inherits, and the lock it must hold.

The environment is scrubbed of every `GIT_*` variable before the child starts. Without
that, a harness launched from a session that had `GIT_DIR` set would do its work against
whatever repository that pointer named rather than the one it was sent to. The WSL path
here is the same problem from the other side (R4): WSL git cannot resolve a Windows
gitdir pointer in a linked worktree, so the inner command exports translated `GIT_DIR`
and `GIT_WORK_TREE` — and the native Cursor path, which does not need them, must not
inject them.

The Cursor agent lock is the concurrency invariant: dispatch owns it, a Cursor run
enters and exits it, a non-Cursor run never takes it, and a dry run — which launches
nothing — must not hold it either, or a rehearsal would block a real run. The lock file
is instance state and is gitignored. Permission mode belongs here because it is part of
the built command: every registered harness has known bypass flags, or the meta-harness
cannot control it, and prompt mode passes none."""

from family_source import seam

from pathlib import Path
from consilient.harness import (
    HARNESSES,
    Decision,
    permission_flags,
    harness_by_id,
)
from dispatch_helpers import (
    CAP_HELP,
    _git,
    _load_script,
)


def test_wsl_path_translation_is_absolute():
    script = _load_script()
    converted = script.to_wsl_path(
        Path("C:/Users/jpbpr/Repositories/consilient-w-orch-b")
    )
    assert converted.startswith("/mnt/c/")
    assert "C:" not in converted
    assert "\\" not in converted


def test_run_harness_scrubs_git_environment(monkeypatch, tmp_path):
    script = _load_script()
    monkeypatch.setenv("GIT_DIR", "C:/wrong/repository/.git")
    monkeypatch.setenv("GIT_WORK_TREE", "C:/wrong/repository")
    monkeypatch.setenv("GIT_INDEX_FILE", "C:/wrong/repository/index")
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_args, **_kwargs: ["agent"])
    captured: dict[str, str] = {}

    def fake_run_process(_argv, *, env, **_kwargs):
        captured.update(env)
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
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
        assert flags, (
            f"{item.id} has no bypass flags; the meta-harness cannot control it"
        )
        assert permission_flags(item.id, "prompt") == ()


def test_claude_bypass_always_skips_permissions(monkeypatch, tmp_path):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "find_claude", lambda: "claude")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
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


def test_wsl_cursor_inner_exports_git_dir_for_a_linked_worktree(tmp_path, monkeypatch):
    """R4. WSL git cannot resolve a Windows gitdir pointer in a linked worktree."""
    script = _load_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "commit", "--allow-empty", "-m", "seed")
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", str(linked))
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: None)
    monkeypatch.setattr(seam("dispatch_launch"), "wsl_bridge", lambda: "wsl")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
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
    assert "--max-turns 20" in inner
    assert "--max-tokens 100000" in inner


def test_native_cursor_command_does_not_inject_wsl_git_exports(tmp_path, monkeypatch):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
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
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    calls: list[str] = []
    orig = script.ExclusiveFileLock

    class Spy(orig):  # type: ignore[misc, valid-type]
        def __enter__(self):
            calls.append("enter")
            return super().__enter__()

        def __exit__(self, *exc: object):
            calls.append("exit")
            return super().__exit__(*exc)

    monkeypatch.setattr(seam("dispatch_supervision"), "ExclusiveFileLock", Spy)
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", lambda *_a, **_k: (0, False, 0.1, None))
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
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    held: dict[str, bool] = {}

    def fake_run_process(_argv, **_kwargs):
        held["exists"] = lock.exists()
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
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
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_CURSOR_LOCK", lock)
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
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

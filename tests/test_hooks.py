"""Tracked hooks have to exist and have to fire. Untracked `.git/hooks` is not a chokepoint."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".githooks"
INSTALLER = ROOT / "scripts" / "install_hooks.py"


def _load_installer():
    name = "consilient_install_hooks_script"
    spec = importlib.util.spec_from_file_location(name, INSTALLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_tracked_git_hooks_call_the_publication_checkers():
    pre_commit = (HOOKS / "pre-commit").read_text(encoding="utf-8")
    pre_push = (HOOKS / "pre-push").read_text(encoding="utf-8")
    assert "check_secrets.py" in pre_commit
    assert "check_private_corpus" in pre_push
    assert "check_foreign_identifiers" in pre_push
    assert "[ -f \"$checker\" ] || exit 0" not in pre_commit
    assert "|| continue" not in pre_push


def test_post_commit_invokes_one_wrapper_through_the_current_python():
    post_commit = (HOOKS / "post-commit").read_text(encoding="utf-8")
    assert 'exec python "$root/scripts/memory_refresh.py"' in post_commit
    assert "graphify" not in post_commit.casefold()
    assert "mempalace" not in post_commit.casefold()


def test_installer_refuses_when_post_commit_is_missing(
    tmp_path, monkeypatch, capsys
):
    installer = _load_installer()
    hooks = tmp_path / ".githooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("hook", encoding="utf-8")
    (hooks / "pre-push").write_text("hook", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "memory_refresh.py").write_text("wrapper", encoding="utf-8")
    called = False

    def unexpected_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("git config must not run when a hook is missing")

    monkeypatch.setattr(installer, "ROOT", tmp_path)
    monkeypatch.setattr(installer.subprocess, "run", unexpected_run)

    assert installer.main() == 1
    assert not called
    assert ".githooks/post-commit" in capsys.readouterr().err


def test_agent_hooks_do_not_refresh_the_structural_or_episodic_layers():
    for relative in (
        ".claude/settings.json",
        ".cursor/hooks.json",
        ".grok/hooks/project.json",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8").casefold()
        assert "memory_refresh.py" not in text
        assert "graphify" not in text
        assert "mempalace" not in text


def test_protect_files_blocks_dotenv_and_allows_ordinary_paths():
    script = HOOKS / "protect-files.py"
    blocked = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({"tool_input": {"file_path": ".env"}}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert blocked.returncode == 2, blocked.stderr
    allowed = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({"tool_input": {"file_path": "src/consilient/cli.py"}}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert allowed.returncode == 0, allowed.stderr


def test_auto_format_never_fails_the_edit():
    script = HOOKS / "auto-format.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input="{}",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr

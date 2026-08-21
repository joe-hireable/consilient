"""Tracked hooks have to exist and have to fire. Untracked `.git/hooks` is not a chokepoint."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".githooks"


def test_tracked_git_hooks_call_the_publication_checkers():
    pre_commit = (HOOKS / "pre-commit").read_text(encoding="utf-8")
    pre_push = (HOOKS / "pre-push").read_text(encoding="utf-8")
    assert "check_secrets.py" in pre_commit
    assert "check_private_corpus" in pre_push
    assert "check_foreign_identifiers" in pre_push
    assert "[ -f \"$checker\" ] || exit 0" not in pre_commit
    assert "|| continue" not in pre_push


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

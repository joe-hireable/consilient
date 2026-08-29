"""Live regression check for the subscription-backed Grok dispatch arm."""

from __future__ import annotations

from family_source import seam

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from consilient.harness import harness_by_id


ROOT = Path(__file__).resolve().parent.parent
DISPATCH_PATH = ROOT / "scripts" / "dispatch.py"


def _load_dispatch():
    name = "consilient_grok_arm_dispatch"
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_prompt_permissions_do_not_auto_approve_grok(monkeypatch, tmp_path):
    script = _load_dispatch()
    monkeypatch.setattr(seam("dispatch_evidence"), "find_grok", lambda: "grok")
    monkeypatch.setattr(seam("dispatch_evidence"), "metered_grok_reason", lambda: None)
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: "--always-approve")
    harness = harness_by_id("grok")
    assert harness is not None

    built = script.build_command(
        harness,
        task="noop",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        permissions="prompt",
    )

    assert isinstance(built, list)
    assert "--always-approve" not in built
    bypassed = script.build_command(
        harness,
        task="noop",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        permissions="bypass",
    )
    assert isinstance(bypassed, list)
    assert "--always-approve" in bypassed


def test_real_grok_dispatch_returns_useful_completion_within_sixty_seconds(
    monkeypatch, tmp_path
):
    script = _load_dispatch()
    if script.find_grok() is None:
        pytest.skip("Grok CLI is not installed")
    if script.metered_grok_reason() is not None:
        pytest.skip("metered Grok credentials are present; live test must use subscription auth")
    grok_home = Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))
    auth_path = Path(os.environ.get("GROK_AUTH_PATH", grok_home / "auth.json"))
    if not auth_path.is_file():
        pytest.skip("SuperGrok subscription auth is not installed")

    harness = harness_by_id("grok")
    assert harness is not None
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["git", "init", str(workspace)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    monkeypatch.setitem(script.GIT_ENV, "GROK_WRITE_FILE", "0")
    expected = "GROK_ARM_READY"
    run_dir = workspace / ".consilient-run"
    started = time.monotonic()
    result = script.run_harness(
        harness,
        task=(
            "Make no file changes. Concatenate these fragments without separators: "
            "GROK_, ARM_, REA, DY. Reply with only the result."
        ),
        cwd=workspace,
        run_dir=run_dir,
        timeout_s=60,
        model=None,
        run_id="grok-arm-live",
        permissions="prompt",
        max_turns=2,
    )
    elapsed = time.monotonic() - started

    assert expected not in (run_dir / "brief.md").read_text(encoding="utf-8")
    assert not result.timed_out, result.reason
    assert elapsed < 60, elapsed
    assert result.exit_code == 0, result.stderr
    assert result.status == "ok", result.reason
    assert result.stdout.strip() == expected, result.stdout or result.stderr

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "memory_refresh.py"


def _load_script():
    name = "consilient_memory_refresh_script"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _safe_source(root: Path) -> Path:
    source = root / ".harness" / "training" / "conversations"
    source.mkdir(parents=True)
    return source


def test_refresh_fails_closed_without_an_explicit_conversation_source(
    tmp_path, capsys
):
    memory_refresh = _load_script()

    def unexpected_runner(*args, **kwargs):
        raise AssertionError("neither memory layer may run without a safe source")

    assert memory_refresh.refresh(tmp_path, {}, runner=unexpected_runner) == 1
    error = capsys.readouterr().err
    assert "REFUSED" in error
    assert memory_refresh.SOURCE_ENV in error


@pytest.mark.parametrize("relative", [".", "../outside", ".harness/knowledge"])
def test_refresh_rejects_sources_outside_the_repository_training_area(
    tmp_path, relative, capsys
):
    memory_refresh = _load_script()
    source = (tmp_path / relative).resolve()
    source.mkdir(parents=True, exist_ok=True)
    environ = {memory_refresh.SOURCE_ENV: str(source)}

    assert memory_refresh.refresh(tmp_path, environ, runner=None) == 1
    assert ".harness/training" in capsys.readouterr().err.replace("\\", "/")


def test_refresh_rejects_a_missing_configured_source(tmp_path, capsys):
    memory_refresh = _load_script()
    source = tmp_path / ".harness" / "training" / "missing"

    assert (
        memory_refresh.refresh(
            tmp_path,
            {memory_refresh.SOURCE_ENV: str(source)},
            runner=None,
        )
        == 1
    )
    assert "does not exist" in capsys.readouterr().err


def test_refresh_runs_graphify_then_mempalace_with_the_verified_interfaces(
    tmp_path, capsys
):
    memory_refresh = _load_script()
    source = _safe_source(tmp_path)
    calls: list[tuple[list[str], Path, float]] = []

    def runner(argv, *, cwd, timeout_s):
        calls.append((argv, cwd, timeout_s))
        return subprocess.CompletedProcess(argv, 0, "", "")

    result = memory_refresh.refresh(
        tmp_path,
        {memory_refresh.SOURCE_ENV: str(source)},
        runner=runner,
    )

    assert result == 0, capsys.readouterr().err
    assert len(calls) == 2
    graphify, mempalace = calls
    assert graphify[0][0:2] == [sys.executable, "-c"]
    assert "from graphify.watch import _rebuild_code" in graphify[0][2]
    assert graphify[0][-1] == str(tmp_path.resolve())
    assert mempalace[0] == [
        sys.executable,
        "-m",
        "mempalace",
        "mine",
        str(source.resolve()),
        "--mode",
        "convos",
        "--wing",
        "consilience",
        "--agent",
        "consilient-post-commit",
    ]
    assert graphify[1] == mempalace[1] == tmp_path.resolve()
    assert graphify[2] == mempalace[2] == memory_refresh.COMMAND_TIMEOUT_S


@pytest.mark.parametrize(
    ("failed_index", "label"),
    [(0, "Graphify"), (1, "MemPalace")],
)
def test_refresh_makes_each_tool_failure_visible(
    tmp_path, failed_index, label, capsys
):
    memory_refresh = _load_script()
    source = _safe_source(tmp_path)
    calls = 0

    def runner(argv, *, cwd, timeout_s):
        nonlocal calls
        index = calls
        calls += 1
        if index == failed_index:
            return subprocess.CompletedProcess(argv, 7, "visible stdout", "visible stderr")
        return subprocess.CompletedProcess(argv, 0, "", "")

    result = memory_refresh.refresh(
        tmp_path,
        {memory_refresh.SOURCE_ENV: str(source)},
        runner=runner,
    )

    assert result == 1
    assert calls == failed_index + 1
    error = capsys.readouterr().err
    assert label in error
    assert "visible stdout" in error
    assert "visible stderr" in error


def test_text_runner_decodes_utf8_output(tmp_path):
    memory_refresh = _load_script()
    result = memory_refresh.run_text(
        [
            sys.executable,
            "-c",
            "import sys; print('café'); print('λ', file=sys.stderr)",
        ],
        cwd=tmp_path,
        timeout_s=5,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "café"
    assert result.stderr.strip() == "λ"


def test_text_runner_kills_grandchildren_at_the_timeout(tmp_path):
    memory_refresh = _load_script()
    ready = tmp_path / "grandchild-started"
    escaped = tmp_path / "grandchild-escaped"
    grandchild = (
        "import time; from pathlib import Path; time.sleep(1.5); "
        f"Path({str(escaped)!r}).write_text('escaped', encoding='utf-8')"
    )
    parent = (
        "import subprocess, sys, time; from pathlib import Path; "
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}]); "
        f"Path({str(ready)!r}).write_text('ready', encoding='utf-8'); "
        "time.sleep(30)"
    )

    result = memory_refresh.run_text(
        [sys.executable, "-c", parent],
        cwd=tmp_path,
        timeout_s=1,
    )

    assert ready.is_file(), "fixture did not start the grandchild before the timeout"
    assert result.returncode == memory_refresh.TIMEOUT_EXIT_CODE
    assert "timed out" in result.stderr
    time.sleep(0.8)
    assert not escaped.exists(), "the timed-out grandchild survived the tree kill"

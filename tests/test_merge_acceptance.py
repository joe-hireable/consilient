"""Merge acceptance: the two checks ruff and mypy do not have.

A merged Python file can parse cleanly and still be wrong. Unit T01's blind
union produced a file that `py_compile` accepted while carrying a module-level
rebinding (C1) and a CREATE TABLE cut mid-statement inside a string (C3).
Neither ruff (repo config or --isolated --select ALL) nor mypy --strict names
those two; mypy.ini's warn_unreachable catches only the stranded-after-return
third defect. [measured 24 Aug 2026, BK unit]

These tests pin both detections and the precision property: the live tree must
stay at zero findings. A naive C3 that executes every Constant containing
'CREATE TABLE' is not that check — it fires on the regex in
`scripts/build_diagrams.py` and on a Python-source fixture in
`tests/test_build_diagrams.py` [measured this worktree]. C3 therefore runs
sqlite3 only against SQL-shaped strings (stripped, starts with CREATE TABLE,
no backslash). If a future scan is non-zero, narrow the check. Never disable
it and never threshold it.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_merge_acceptance.py"
FINDING = re.compile(r"\.py:\d+:\S+$")


def _load():
    spec = importlib.util.spec_from_file_location("check_merge_acceptance", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _finding_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if FINDING.search(line)]


def test_self_test_names_both_specimen_defects_and_accepts_the_control() -> None:
    """`--self-test` must prove C1 and C3 fire on the specimen and stay silent on the control.

    The specimen run exits 1 and names both defects; the control run exits 0.
    The overall `--self-test` exits 0 only when that proof holds — a detector
    that cannot fail is the defect it exists to find.
    """
    result = _run("--self-test")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "KINDS" in output
    assert "SCHEMA" in output
    assert "self-test FAILED" not in output


def test_files_on_the_specimen_exits_1_naming_both_defects(tmp_path: Path) -> None:
    checker = _load()
    specimen = tmp_path / "specimen.py"
    specimen.write_text(checker.SPECIMEN, encoding="utf-8")
    result = _run("--files", str(specimen))
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    findings = "\n".join(_finding_lines(output))
    assert ":KINDS" in findings
    assert ":SCHEMA" in findings


def test_files_on_the_control_exits_0(tmp_path: Path) -> None:
    checker = _load()
    control = tmp_path / "control.py"
    control.write_text(checker.CONTROL, encoding="utf-8")
    result = _run("--files", str(control))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert _finding_lines(output) == []


def test_scan_of_the_live_tree_reports_zero_findings() -> None:
    result = _run("--scan", "src", "scripts", "tests", ".harness")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert _finding_lines(output) == [], output


def test_c1_does_not_flag_function_class_or_import_redefinition(tmp_path: Path) -> None:
    """ruff F811 and mypy no-redef already own those; widening C1 reintroduces false alarms."""
    source = tmp_path / "owned_elsewhere.py"
    source.write_text(
        "\n".join(
            (
                "import os",
                "import os",
                "def once():",
                "    return 1",
                "def once():",
                "    return 2",
                "class Holder:",
                "    pass",
                "class Holder:",
                "    pass",
                "def inner():",
                "    x = 1",
                "    x = 2",
                "    return x",
                "",
            )
        ),
        encoding="utf-8",
    )
    result = _run("--files", str(source))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert _finding_lines(output) == []


def test_c3_does_not_execute_a_regex_or_a_python_fixture() -> None:
    """The two live-tree false alarms a naive C3 walk produced [measured]."""
    checker = _load()
    regex = r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*;"
    fixture = 'from . import events\n\nSCHEMA = """\nCREATE TABLE IF NOT EXISTS events (\n    id INTEGER\n);\n"""\n'
    assert checker.ddl_findings("<regex>", regex) == []
    assert checker.ddl_findings("<fixture>", fixture) == []

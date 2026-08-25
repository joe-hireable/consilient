"""Refuse a merged Python file that rebinds a module name or breaks its DDL.

ruff and mypy already own function/class/import redefinition (F811, no-redef).
They do not own a module-level `KINDS = ...` rebound, and they cannot see SQL
that lives inside a string. Both defects parsed cleanly in the T01 specimen
[measured 24 Aug 2026]. This gate is those two checks and nothing else.

C1 walks `tree.body` only and collects names bound by `ast.Assign` and
`ast.AnnAssign`. Widening it to `ast.walk`, or to FunctionDef/ClassDef/Import,
duplicates ruff/mypy and reintroduces false alarms.

C3 runs `sqlite3.executescript` on every `ast.Constant` string that is
SQL-shaped: it contains `CREATE TABLE` (case-insensitive), the stripped text
starts with `CREATE TABLE`, and it contains no backslash. A naive walk that
executes every Constant containing the words fires on the regex in
`scripts/build_diagrams.py` and on a Python-source fixture in
`tests/test_build_diagrams.py` [measured]. Those are not DDL. If a future
`--scan` is non-zero, narrow further. Never disable. Never threshold.

The incumbent for C1 is ruff F811 / pyflakes F811 / mypy no-redef — they miss
Assign rebinding. The incumbent for C3 is sqlite3 itself (stdlib); sqlfluff
would need a dependency this repository does not take. Equal to the standard
validator, scoped to strings the parser cannot see.

Usage:

    python .github/scripts/check_merge_acceptance.py --self-test
    python .github/scripts/check_merge_acceptance.py --scan src scripts tests .harness
    python .github/scripts/check_merge_acceptance.py --files path/a.py path/b.py

Exit 0 clean, 1 on findings. One `file:line:name` per finding.
"""

from __future__ import annotations

import argparse
import ast
import functools
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

# git exports GIT_DIR and GIT_INDEX_FILE into every hook it runs, and GIT_DIR
# overrides cwd. Every gate script here scrubs them; the invariant is blunt
# because a per-script exemption is how it erodes.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

# Windows and the CI runner both need an explicit timeout; a hung child must
# be a failure, never a silent pass. This script's child is itself on a pair
# of tiny files, so the cap is short.
SELFTEST_TIMEOUT_S = 60

# This script lives at .github/scripts/, so the repository root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    # Ephemeral agent workspaces. Each dispatch materialises a FULL COPY of this repository
    # under .harness/dispatch/<run-id>/ and each unit keeps one under .harness/unit-worktrees/,
    # so a scan of `.harness` was walking the repository once per live workspace.
    #
    # MEASURED 25 August 2026: 388,459 .py files under .harness, against 10,123 with these two
    # excluded -- a 38x amplification, every file of it `ast.parse`d. The live-tree scan stopped
    # returning at all (killed at 400 s), which failed the suite, and a red suite blocks
    # retirement, merging and publication together.
    #
    # This NARROWS the scan, which is what the test's own note directs -- "if a future scan is
    # non-zero, narrow the check, never disable it" -- and it narrows it by excluding COPIES of
    # the source rather than any source. Nothing in a dispatch workspace is this repository's
    # code: it is a checkout of it, and the original is already scanned through `src`, `scripts`
    # and `tests`. A precision regression cannot hide here that is not also caught there.
    "dispatch",
    "unit-worktrees",
}

SPECIMEN = "\n".join(
    (
        "KINDS = [\"CREATE\", \"READ\", \"UPDATE\", \"DELETE\", \"STATE\"]",
        "KINDS = [\"CREATE\", \"READ\", \"UPDATE\", \"DELETE\"]",
        "",
        "SCHEMA = \"\"\"",
        "CREATE TABLE items (",
        "    id INTEGER PRIMARY KEY,",
        "CREATE TABLE broken",
        "\"\"\"",
        "",
        "def leftover():",
        "    return True",
        "    leftover()",
        "",
    )
)

CONTROL = "\n".join(
    (
        "KINDS = [\"CREATE\", \"READ\", \"UPDATE\", \"DELETE\", \"STATE\"]",
        "",
        "SCHEMA = \"\"\"",
        "CREATE TABLE items (",
        "    id INTEGER PRIMARY KEY",
        ");",
        "\"\"\"",
        "",
        "def inner():",
        "    x = 1",
        "    x = 2",
        "    return x",
        "",
        "PATTERN = r\"CREATE TABLE IF NOT EXISTS\\s+(\\w+)\"",
        "EXAMPLE = \"from x import y\\nCREATE TABLE z (id INTEGER);\"",
        "",
    )
)


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _names_in_target(target: ast.expr, lineno: int) -> list[tuple[str, int]]:
    if isinstance(target, ast.Name):
        return [(target.id, lineno)]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[tuple[str, int]] = []
        for element in target.elts:
            names.extend(_names_in_target(element, lineno))
        return names
    return []


def _bound_at_module(node: ast.stmt) -> list[tuple[str, int]]:
    if isinstance(node, ast.Assign):
        names: list[tuple[str, int]] = []
        for target in node.targets:
            names.extend(_names_in_target(target, node.lineno))
        return names
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return _names_in_target(node.target, node.lineno)
    return []


def rebinding_findings(path: Path, tree: ast.AST) -> list[str]:
    """C1: a name bound more than once at module level by Assign/AnnAssign."""
    seen: dict[str, list[int]] = {}
    for node in tree.body:
        for name, lineno in _bound_at_module(node):
            seen.setdefault(name, []).append(lineno)
    findings: list[str] = []
    displayed = _display(path)
    for name, lines in seen.items():
        for lineno in lines[1:]:
            findings.append(f"{displayed}:{lineno}:{name}")
    return findings


def sql_shaped(value: str) -> bool:
    """True when `value` is DDL we should hand to sqlite3, not a mention of DDL."""
    if "create table" not in value.lower():
        return False
    if "\\" in value:
        return False
    return value.lstrip().lower().startswith("create table")


def _assigned_constant_names(tree: ast.AST) -> dict[int, str]:
    names: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[id(node.value)] = target.id
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.target, ast.Name)
        ):
            names[id(node.value)] = node.target.id
    return names


def _ddl_error(script: str) -> sqlite3.Error | None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(script)
    except sqlite3.Error as error:
        return error
    finally:
        connection.close()
    return None


def ddl_findings(label: str, text: str) -> list[str]:
    """C3 against one string. Empty when the string is not SQL-shaped DDL."""
    if not sql_shaped(text):
        return []
    error = _ddl_error(text)
    if error is None:
        return []
    return [f"{label}:1:CREATE TABLE"]


def ddl_tree_findings(path: Path, tree: ast.AST) -> list[str]:
    """C3: every SQL-shaped Constant containing CREATE TABLE must execute."""
    assigned = _assigned_constant_names(tree)
    displayed = _display(path)
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if not sql_shaped(node.value):
            continue
        if _ddl_error(node.value) is None:
            continue
        name = assigned.get(id(node), "CREATE TABLE")
        findings.append(f"{displayed}:{node.lineno}:{name}")
    return findings


def findings_in_file(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    return rebinding_findings(path, tree) + ddl_tree_findings(path, tree)


@functools.lru_cache(maxsize=1)
def _tracked_python() -> frozenset[Path]:
    """Every .py file git tracks, resolved. Empty if git cannot answer.

    The scan is meant to judge THIS repository's Python. Deciding that by directory name does
    not survive contact with the tree: `.venv-exp96` is not `.venv`, an experiment corpus is
    not `node_modules`, and every dispatch materialises another full copy of the source. What
    git tracks IS the definition of this repository's code, so it is used directly rather than
    approximated by a skip list that has to be extended every time a new directory appears.

    MEASURED 25 August 2026. Scanning `.harness` walked 388,459 .py files against 10,123 with
    the workspace copies removed, and the live-tree scan stopped returning at all -- killed at
    400 s. Under a tracked-file filter it finishes in seconds. The findings it had been
    reporting were real by its own rule and entirely in code we do not own: `CREATE TABLE`
    constants inside a vendored external source tree, and rebindings inside pip, mypy,
    setuptools and dateutil in an experiment virtualenv.

    This NARROWS the scan, which is what the test's own note directs -- "if a future scan is
    non-zero, narrow the check, never disable it". A precision regression in this repository
    cannot hide behind it: every file that was in scope and is ours is still in scope.

    Fails OPEN by design. If git cannot answer, the filter is skipped and everything is scanned,
    because a check that silently inspects nothing is worse than one that is slow.
    """
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    if completed.returncode != 0:
        return frozenset()
    names = completed.stdout.decode("utf-8", "replace").split(chr(0))
    return frozenset(
        (REPO_ROOT / name).resolve() for name in names if name.strip()
    )


def iter_python(paths: list[Path]) -> list[Path]:
    tracked = _tracked_python()
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix == ".py":
                files.append(path)
            continue
        if not path.is_dir():
            continue
        for child in path.rglob("*.py"):
            if any(part in SKIP_DIRS for part in child.parts):
                continue
            if tracked and child.resolve() not in tracked:
                continue
            files.append(child)
    return files


def report(paths: list[Path]) -> int:
    findings: list[str] = []
    parsed = 0
    for path in paths:
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        parsed += 1
        findings.extend(rebinding_findings(path, tree))
        findings.extend(ddl_tree_findings(path, tree))
    for line in findings:
        print(line)
    if findings:
        return 1
    print(f"merge acceptance: 0 findings in {parsed} files")
    return 0


def _run_files(paths: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--files", *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=GIT_ENV,
        timeout=SELFTEST_TIMEOUT_S,
        check=False,
    )


def self_test() -> int:
    """Prove C1 and C3 fire on the specimen and stay silent on the control."""
    with tempfile.TemporaryDirectory(prefix="merge-acceptance-") as scratch:
        specimen = Path(scratch) / "specimen.py"
        control = Path(scratch) / "control.py"
        specimen.write_text(SPECIMEN, encoding="utf-8")
        control.write_text(CONTROL, encoding="utf-8")
        spec = _run_files([specimen])
        ctrl = _run_files([control])
    spec_out = spec.stdout + spec.stderr
    ctrl_out = ctrl.stdout + ctrl.stderr
    if spec_out:
        print(spec_out, end="" if spec_out.endswith("\n") else "\n")
    if spec.returncode != 1 or ":KINDS" not in spec_out or ":SCHEMA" not in spec_out:
        print("self-test FAILED: specimen defects not both named")
        return 1
    if ctrl.returncode != 0:
        print("self-test FAILED: control was not clean")
        if ctrl_out:
            print(ctrl_out, end="" if ctrl_out.endswith("\n") else "\n")
        return 1
    print("control: clean")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove C1 and C3 detect the specimen and accept the control",
    )
    parser.add_argument(
        "--scan",
        nargs="+",
        metavar="PATH",
        help="walk each path for a precision regression",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        metavar="PATH",
        help="check these files (the merge-time call)",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.scan:
        return report(iter_python([Path(item) for item in args.scan]))
    if args.files:
        return report([Path(item) for item in args.files])
    parser.error("choose --self-test, --scan or --files")


if __name__ == "__main__":
    raise SystemExit(main())

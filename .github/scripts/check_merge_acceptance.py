"""Refuse a merged Python file that rebinds a module name or breaks its DDL — the gate
itself, its two fixtures, the AST sweep and the command line.

ruff and mypy already own function, class and import redefinition. They do not own a
module-level `KINDS = ...` rebound, and they cannot see SQL that lives inside a string.
Both defects parsed cleanly in the T01 specimen [measured 24 Aug 2026]. This gate is
those two checks and nothing else. C1 lives in `merge_acceptance_rebinding.py`; the
string grammar behind C3 lives in `merge_acceptance_sql.py`. What stays here is what
cannot leave, and the reason is measured rather than editorial.

Running this checker against a byte-identical copy of itself at another path produces
five findings [measured 28 August 2026]: the two `CREATE TABLE` fragments inside
SPECIMEN, the one inside CONTROL, the `create table` prefix literal inside `_ddl_start`,
and the `CREATE TABLE` fallback label inside `ddl_tree_findings`. All five are DDL-
shaped by the check's own rule, and `report()` exempts exactly one path — `_SELF_PATH`.
A sibling carrying any of them would therefore refuse itself the moment a commit touched
it, including the commit that created it, because the merge gate runs this script with
`--files` over every changed Python file. Widening the exemption to a second path would
be loosening a boundary this docstring says to narrow and never disable, so those four
symbols stay.

SPECIMEN, CONTROL and `ddl_findings` stay for a second, independent reason:
`tests/test_merge_acceptance.py` reaches them by attribute on a module loaded with
`importlib.util.spec_from_file_location`, which does not put this directory on
`sys.path`. The one-line insert below is what makes the sibling imports resolve under
that loader; without it four of that file's seven tests raise ModuleNotFoundError.

C3 runs `sqlite3.executescript` on every `ast.Constant` string that is SQL-shaped. A
naive walk that executes every Constant containing the words fires on the regex in
`scripts/build_diagrams.py` and on a Python-source fixture in
`tests/test_build_diagrams.py` [measured]. Those are not DDL. If a future `--scan` is
non-zero, narrow further. Never disable. Never threshold.

The incumbent for C3 is sqlite3 itself (stdlib); sqlfluff would need a dependency this
repository does not take. Equal to the standard validator, scoped to strings the parser
cannot see.

Usage:

    python .github/scripts/check_merge_acceptance.py --self-test
    python .github/scripts/check_merge_acceptance.py --scan src scripts tests .harness
    python .github/scripts/check_merge_acceptance.py --files path/a.py path/b.py

Exit 0 clean, 1 on findings. One `file:line:name` per finding.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

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
"""

import argparse
import ast
import functools
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from merge_acceptance_rebinding import (
    _bound_at_module,
    _display,
    _names_in_target,
    rebinding_findings,
)

from merge_acceptance_sql import (
    _after_table_name,
    _create_table_shaped,
    _ddl_error,
    _ddl_slice,
    _without_leading_sql_comments,
)

__all__ = [
    "CONTROL",
    "GIT_ENV",
    "REPO_ROOT",
    "SELFTEST_TIMEOUT_S",
    "SKIP_DIRS",
    "SPECIMEN",
    "_after_table_name",
    "_bound_at_module",
    "_create_table_shaped",
    "_ddl_error",
    "_ddl_slice",
    "_display",
    "_names_in_target",
    "_without_leading_sql_comments",
    "ddl_findings",
    "ddl_tree_findings",
    "findings_in_file",
    "iter_python",
    "main",
    "rebinding_findings",
    "report",
    "self_test",
    "sql_shaped",
]

# git exports GIT_DIR and GIT_INDEX_FILE into every hook it runs, and GIT_DIR
# overrides cwd. Every gate script here scrubs them; the invariant is blunt
# because a per-script exemption is how it erodes.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

_SELF_PATH = Path(__file__).resolve()

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
        'KINDS = ["CREATE", "READ", "UPDATE", "DELETE", "STATE"]',
        'KINDS = ["CREATE", "READ", "UPDATE", "DELETE"]',
        "",
        'SCHEMA = """',
        "CREATE TABLE items (",
        "    id INTEGER PRIMARY KEY,",
        "CREATE TABLE broken",
        '"""',
        "",
        "def leftover():",
        "    return True",
        "    leftover()",
        "",
    )
)

CONTROL = "\n".join(
    (
        'KINDS = ["CREATE", "READ", "UPDATE", "DELETE", "STATE"]',
        "",
        'SCHEMA = """',
        "CREATE TABLE items (",
        "    id INTEGER PRIMARY KEY",
        ");",
        '"""',
        "",
        "def inner():",
        "    x = 1",
        "    x = 2",
        "    return x",
        "",
        'PATTERN = r"CREATE TABLE IF NOT EXISTS\\s+(\\w+)"',
        'EXAMPLE = "from x import y\\nCREATE TABLE z (id INTEGER);"',
        "",
    )
)


def _ddl_start(value: str) -> int | None:
    """Absolute index in `value` where a genuine CREATE TABLE statement begins.

    MEASURED 26 August 2026: requiring the WHOLE string to start with "create table"
    let a leading `PRAGMA foreign_keys = ON;` (or any other leading statement) hide a
    genuinely broken schema from this check entirely -- the same cut-mid-statement SCHEMA
    that was correctly refused on its own passed with "0 findings" once prefixed. A DDL
    string is not only ever a single bare CREATE TABLE statement; check every statement
    boundary (the start, and immediately after each top-level ';'), not just position 0.
    """
    script = _without_leading_sql_comments(value)
    offset = len(value) - len(script)
    prefix = "create table"
    folded = script.casefold()
    start = 0
    while True:
        index = folded.find(prefix, start)
        if index < 0:
            return None
        at_statement_start = index == 0 or script[:index].rstrip().endswith(";")
        if at_statement_start and _create_table_shaped(script[index + len(prefix) :]):
            return offset + index
        start = index + len(prefix)


def sql_shaped(value: str) -> bool:
    """Distinguish DDL intent from prose, regexes and Python-source fixtures."""
    return _ddl_start(value) is not None


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


def ddl_findings(label: str, text: str) -> list[str]:
    """C3 against one string. Empty when the string is not SQL-shaped DDL."""
    start = _ddl_start(text)
    if start is None:
        return []
    error = _ddl_error(_ddl_slice(text, start))
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
        start = _ddl_start(node.value)
        if start is None:
            continue
        if _ddl_error(_ddl_slice(node.value, start)) is None:
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
            env=GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    if completed.returncode != 0:
        return frozenset()
    names = completed.stdout.decode("utf-8", "replace").split(chr(0))
    return frozenset((REPO_ROOT / name).resolve() for name in names if name.strip())


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
        # C3 walks every string constant, including this file's own SPECIMEN/CONTROL
        # self-test fixtures and the literal "create table" / "CREATE TABLE" strings
        # sql_shaped() and ddl_tree_findings() use for matching -- all deliberately
        # DDL-shaped-and-broken by design, not real application schema. A `--files`
        # scan scoped to this checker's own file (exactly what the merge gate runs on
        # a commit that touches it) refused itself on those self-matches before this
        # exclusion existed. self_test() already proves detection works, via a
        # subprocess over separate scratch files, so this file is exempt from its own
        # C3 sweep without weakening the check for anything else.
        if path.resolve() != _SELF_PATH:
            findings.extend(ddl_tree_findings(path, tree))
    for line in findings:
        print(line)
    if findings:
        return 1
    print(f"merge acceptance: 0 findings in {parsed} files")
    return 0


def _run_files(paths: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--files",
            *[str(p) for p in paths],
        ],
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

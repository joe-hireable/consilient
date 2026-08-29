"""Find, read, parse and digest the source files the diagrams are drawn from.

Everything here answers a question about the repository as it sits on disk: which files
a diagram's source pattern names, what those files contain, what the SHA-256 of that
content is, and which literal strings, table columns and import targets can be recovered
from their syntax trees. Nothing is imported. The modules are read as text and parsed
with `ast`, because a generator that imports the code it documents inherits that code's
import errors and its side effects, and would then fail for reasons that have nothing to
do with drift.

Extraction is deliberately literal, and gives up rather than guesses. `_string_value`
folds a concatenation of string constants and returns None for anything else;
`_admission_classes` recognises `admission == "X"` and `admission in {...}` and nothing
cleverer; `_columns` skips a line that begins with a table constraint instead of
inventing a column from it. A caller handed None can say the source was not found, which
is a visible failure. A helper that guessed would put a fabricated edge in a document
whose entire purpose is to contradict the hand-drawn one.

Two refusals are worth stating outright. `_tracked_python` asks git which files under
`src` are tracked, so an untracked scratch file cannot make the generator refuse the
whole repository, and returns None when git cannot answer so the caller falls back to
the disk rather than to nothing. `write_atomic` writes through a temporary file in the
destination directory, fsyncs it and replaces the target, so an interrupted run leaves
either the old diagram or the new one and never half of either. `_document` stamps each
generated file with its producer, its source pattern and that source's digest, which is
what later lets a check distinguish drift from a hand-edit."""

from __future__ import annotations
import ast
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent

DIAGRAM_DIR = ROOT / "docs" / "diagrams"

PRODUCER = "scripts/build_diagrams.py"

TABLE_RE = re.compile(
    r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)

COLUMN_CONSTRAINT = re.compile(
    r"^(PRIMARY|UNIQUE|CHECK|FOREIGN|CONSTRAINT)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Diagram:
    name: str
    source: str
    render: Callable[[Path], str]


def _ident(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _label(value: str) -> str:
    return value.replace('"', "'")


def _read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise ValueError(f"missing source {relative}")
    return path.read_text(encoding="utf-8")


def _parse(root: Path, relative: str) -> ast.Module:
    try:
        return ast.parse(_read(root, relative), filename=relative)
    except SyntaxError as error:
        raise ValueError(f"{relative}: {error.msg}") from error


def _source_paths(root: Path, pattern: str) -> list[Path]:
    if any(char in pattern for char in "*?[]"):
        if pattern == "src/**/*.py":
            paths = [
                path
                for path in sorted((root / "src").rglob("*.py"))
                if "__pycache__" not in path.parts
            ]
        else:
            path = Path(pattern)
            paths = sorted((root / path.parent).glob(path.name))
    else:
        paths = [root / pattern]
    existing = [path for path in paths if path.is_file()]
    if not existing:
        raise ValueError(f"missing source {pattern}")
    return existing


def source_digest(root: Path, pattern: str) -> str:
    digest = hashlib.sha256()
    for path in _source_paths(root, pattern):
        relative = path.relative_to(root).as_posix()
        file_digest = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _document(source: str, digest: str, body: str) -> bytes:
    lines = [
        f"%% **Producer:** `{PRODUCER}`",
        f"%% **Source:** `{source}`",
        f"%% **Source SHA-256:** `{digest}`",
        f"%% **Do not hand-edit:** regenerate with `python {PRODUCER}`.",
        "",
        body.rstrip(),
        "",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _constant_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _string_value(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_value(node.left)
        right = _string_value(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _assigned_string(tree: ast.Module, name: str) -> str | None:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            ):
                return _string_value(node.value)
    return None


def _return_strings(node: ast.Return) -> tuple[str | None, str | None]:
    value = node.value
    if value is None:
        return None, None
    first = _constant_string(value)
    if first is not None:
        return first, None
    if isinstance(value, ast.Tuple) and value.elts:
        return _constant_string(value.elts[0]), (
            _constant_string(value.elts[1]) if len(value.elts) > 1 else None
        )
    if isinstance(value, ast.Call) and value.args:
        second = _constant_string(value.args[1]) if len(value.args) > 1 else None
        return _constant_string(value.args[0]), second
    return None, None


def _admission_classes(test: ast.expr) -> tuple[str, ...]:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return ()
    comparator = test.comparators[0]
    if isinstance(test.ops[0], ast.Eq):
        left = _constant_string(test.left)
        right = _constant_string(comparator)
        if isinstance(test.left, ast.Name) and test.left.id == "admission" and right:
            return (right,)
        if isinstance(comparator, ast.Name) and comparator.id == "admission" and left:
            return (left,)
    if isinstance(test.ops[0], ast.In) and isinstance(test.left, ast.Name):
        if test.left.id == "admission" and isinstance(
            comparator, (ast.Set, ast.Tuple, ast.List)
        ):
            return tuple(
                value
                for elt in comparator.elts
                if (value := _constant_string(elt)) is not None
            )
    return ()


def _declared_admission_classes(tree: ast.Module) -> tuple[str, ...]:
    """Every admission class the type declares, in declaration order.

    The walker below can only see a class named in an explicit `admission == "X"` test. A
    guard-clause function ends with a bare return that applies to EVERY class not handled above
    it, and that arm is invisible without knowing the full set. Reading `AdmissionClass` gives
    the universe from the same source of truth the code uses.
    """
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            first = node.targets[0]
            target = first.id if isinstance(first, ast.Name) else None
        if target != "AdmissionClass":
            continue
        value = node.value
        if isinstance(value, ast.Subscript):
            members = value.slice
            elements = members.elts if isinstance(members, ast.Tuple) else [members]
            names = tuple(
                e.value
                for e in elements
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            )
            if names:
                return names
    return ()


def _columns(body: str) -> list[tuple[str, str, str]]:
    columns: list[tuple[str, str, str]] = []
    for raw in body.split(","):
        line = " ".join(raw.split())
        if not line or COLUMN_CONSTRAINT.match(line):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name, kind = parts[0], parts[1]
        if name.upper() in {"PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT"}:
            continue
        marker = " PK" if "PRIMARY KEY" in line.upper() else ""
        columns.append((name, f"{kind}", marker))
    return columns


def _module_id(path: Path, src: Path) -> str:
    return "_".join(path.relative_to(src).with_suffix("").parts)


def _tracked_python(src: Path) -> set[Path] | None:
    """Paths under `src` that git actually tracks, or None if git cannot answer.

    MEASURED 24 and 25 August 2026, twice. `tests/test_commit_gate.py` uses fixture files
    named `src/mine.py` and `src/x.py`, whose contents are the literal text
    "content of src/mine.py". Those are not valid Python, and on two separate occasions they
    were left behind in the working tree by a killed test run. Scanning the DISK meant this
    generator then refused the whole repository -- "FAIL src/mine.py: invalid syntax" -- and
    took the suite red with it, which in turn blocked retirement, merging and publication.

    A stray scratch file that nothing tracks must not be able to stop the build. Tracked
    files are the ones this repository is actually responsible for parsing.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(src.parent),
            "ls-files",
            "--",
            str(src.relative_to(src.parent)),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if result.returncode != 0:
        return None
    return {
        (src.parent / line.strip()).resolve()
        for line in result.stdout.splitlines()
        if line.strip().endswith(".py")
    }


def _known_modules(src: Path) -> dict[str, Path]:
    tracked = _tracked_python(src)
    modules: dict[str, Path] = {}
    for path in sorted(src.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if tracked is not None and path.resolve() not in tracked:
            continue
        modules[_module_id(path, src)] = path
    return modules


def _resolve_from(
    path: Path, src: Path, node: ast.ImportFrom, known: Iterable[str]
) -> list[str]:
    package = path.relative_to(src).parts[:-1]
    found: list[str] = []
    if node.level:
        base = package[: len(package) - (node.level - 1)] if node.level else package
        if node.module:
            candidate = "_".join(base + tuple(node.module.split(".")))
            if candidate in known:
                found.append(candidate)
        else:
            for alias in node.names:
                candidate = "_".join(base + (alias.name,))
                if candidate in known:
                    found.append(candidate)
        return found
    if node.module:
        module_id = node.module.replace(".", "_")
        if module_id in known:
            found.append(module_id)
        for alias in node.names:
            candidate = "_".join(node.module.split(".") + [alias.name])
            if candidate in known:
                found.append(candidate)
    return found


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass

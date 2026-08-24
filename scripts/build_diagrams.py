"""Generate architecture diagrams from the code rather than drawing them.

Hand-drawn permission and event diagrams drifted the moment the code moved.
On 23 August 2026 the documentation plan recorded the live case: drafting the
permission model from ADR-0033 put material_choice on the escalate path, while
`_disposition_for` in `src/consilient/effects.py` executes it. Generation is the
check that makes that contradiction visible.

    python scripts/build_diagrams.py          # rewrite docs/diagrams/*.mmd
    python scripts/build_diagrams.py --check  # fail if any diagram has drifted
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


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
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
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
        if test.left.id == "admission" and isinstance(comparator, (ast.Set, ast.Tuple, ast.List)):
            return tuple(
                value
                for elt in comparator.elts
                if (value := _constant_string(elt)) is not None
            )
    return ()


def _terminal_disposition(statements: list[ast.stmt]) -> str | None:
    returns = [stmt for stmt in statements if isinstance(stmt, ast.Return)]
    if len(returns) != 1 or any(not isinstance(stmt, ast.Return) for stmt in statements):
        return None
    disposition, _reason = _return_strings(returns[0])
    return disposition


def _disposition_edges(fn: ast.FunctionDef) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []

    def walk(statements: list[ast.stmt], pending: tuple[str, ...]) -> None:
        for stmt in statements:
            if isinstance(stmt, ast.If):
                classes = _admission_classes(stmt.test)
                current = classes or pending
                disposition = _terminal_disposition(stmt.body)
                if current and disposition:
                    for name in current:
                        edges.append((name, disposition))
                else:
                    walk(stmt.body, current)
                walk(stmt.orelse, pending)
            elif isinstance(stmt, ast.Return) and pending:
                disposition, _reason = _return_strings(stmt)
                if disposition:
                    for name in pending:
                        edges.append((name, disposition))

    walk(fn.body, ())
    return list(dict.fromkeys(edges))


def _emit_control_flow(fn: ast.FunctionDef, lines: list[str]) -> None:
    counter = [0]

    def new_id() -> str:
        counter[0] += 1
        return f"{_ident(fn.name)}_{counter[0]}"

    def connect(src: str | None, dst: str, edge_label: str | None) -> None:
        if src is None:
            return
        arrow = f"|{edge_label}|" if edge_label else ""
        lines.append(f"  {src} -->{arrow} {dst}")

    def emit_value(value: ast.expr | None, origin: str | None, edge_label: str | None) -> None:
        if isinstance(value, ast.IfExp):
            diamond = new_id()
            lines.append(f'  {diamond}{{"{_label(ast.unparse(value.test))}"}}')
            connect(origin, diamond, edge_label)
            emit_value(value.body, diamond, "yes")
            emit_value(value.orelse, diamond, "no")
            return
        synthetic = ast.Return(value=value)
        admission, disposition = _return_strings(synthetic)
        terminal = admission or disposition
        if terminal is None:
            terminal_id = new_id()
            lines.append(f'  {terminal_id}["return"]')
        else:
            terminal_id = _ident(terminal)
            lines.append(f'  {terminal_id}["{_label(terminal)}"]')
        connect(origin, terminal_id, edge_label)

    def walk(statements: list[ast.stmt], origin: str | None, label: str | None) -> None:
        statements = [stmt for stmt in statements if not isinstance(stmt, ast.Pass)]
        if not statements:
            return
        first, rest = statements[0], statements[1:]
        if isinstance(first, ast.If):
            diamond = new_id()
            lines.append(f'  {diamond}{{"{_label(ast.unparse(first.test))}"}}')
            connect(origin, diamond, label)
            walk(first.body, diamond, "yes")
            if first.orelse:
                walk(first.orelse, diamond, "no")
            else:
                walk(rest, diamond, "no")
            return
        if isinstance(first, ast.Return):
            emit_value(first.value, origin, label)
            return
        walk(rest, origin, label)

    walk(fn.body, None, None)


def render_permission(root: Path) -> str:
    tree = _parse(root, "src/consilient/effects.py")
    lines = ["flowchart TB"]
    for name in ("derive_admission", "_classify_admission"):
        fn = _function(tree, name)
        if fn is None:
            continue
        lines.append(f'  subgraph {_ident(name)}["{name}"]')
        _emit_control_flow(fn, lines)
        lines.append("  end")
    disposition = _function(tree, "_disposition_for")
    if disposition is not None:
        lines.append('  subgraph disposition["_disposition_for"]')
        edges = _disposition_edges(disposition)
        if not edges:
            _emit_control_flow(disposition, lines)
        for source, dest in edges:
            lines.append(f"  {_ident(source)} --> {_ident(dest)}")
            lines.append(f'  {_ident(source)}["{_label(source)}"]')
            lines.append(f'  {_ident(dest)}["{_label(dest)}"]')
        lines.append("  end")
    if len(lines) == 1:
        raise ValueError("effects.py: no admission functions found")
    return "\n".join(lines)


def render_event_flow(root: Path) -> str:
    tree = _parse(root, "src/consilient/events.py")
    kinds: list[str] = []
    functions: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (
                isinstance(target, ast.Name)
                and target.id.endswith("_KIND")
                and (kind := _constant_string(node.value)) is not None
            ):
                kinds.append(kind)
        if isinstance(node, ast.FunctionDef):
            functions.add(node.name)
    if not kinds:
        raise ValueError("events.py: no *_KIND constants found")
    lines = ["flowchart TB", '  subgraph kinds["event kinds"]']
    for index, kind in enumerate(kinds):
        lines.append(f'    k{index}["{_label(kind)}"]')
    lines.append("  end")
    lines.append('  NEW["new kind"] --> CONST["*_KIND constant"]')
    lines.append("  CONST --> kinds")
    if "validate" in functions:
        lines.append('  kinds --> VALIDATE["validate()"]')
        previous = "VALIDATE"
    else:
        previous = "kinds"
    if "append" in functions:
        lines.append(f'  {previous} --> APPEND["events.append()"]')
    if "register_transition_validator" in functions:
        lines.append(
            f'  {previous} -.-> REGISTER["register_transition_validator()"]'
        )
    return "\n".join(lines)


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


def render_data_model(root: Path) -> str:
    tree = _parse(root, "src/consilient/projection.py")
    schema = _assigned_string(tree, "SCHEMA")
    if not schema:
        raise ValueError("projection.py: SCHEMA string not found")
    tables = TABLE_RE.findall(schema)
    if not tables:
        raise ValueError("projection.py: SCHEMA has no tables")
    lines = ["erDiagram"]
    for table, body in tables:
        lines.append(f"  {table} {{")
        for name, kind, marker in _columns(body):
            lines.append(f"    {kind} {name}{marker}")
        lines.append("  }")
    return "\n".join(lines)


def _module_id(path: Path, src: Path) -> str:
    return "_".join(path.relative_to(src).with_suffix("").parts)


def _known_modules(src: Path) -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for path in sorted(src.rglob("*.py")):
        if "__pycache__" in path.parts:
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


def render_modules(root: Path) -> str:
    src = root / "src"
    if not src.is_dir():
        raise ValueError("missing source src/**/*.py")
    known = _known_modules(src)
    if not known:
        raise ValueError("missing source src/**/*.py")
    edges: list[tuple[str, str]] = []
    for module_id, path in known.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            raise ValueError(f"{path.relative_to(root).as_posix()}: {error}") from error
        targets: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = alias.name.replace(".", "_")
                    if candidate in known:
                        targets.append(candidate)
            elif isinstance(node, ast.ImportFrom):
                targets.extend(_resolve_from(path, src, node, known))
        for target in dict.fromkeys(targets):
            if target != module_id:
                edges.append((module_id, target))
    lines = ["flowchart LR"]
    if not edges:
        for module_id in known:
            lines.append(f'  {module_id}["{module_id.replace("_", ".")}"]')
    for source, dest in dict.fromkeys(edges):
        lines.append(f"  {source} --> {dest}")
    inbound: dict[str, int] = {}
    for _source, dest in edges:
        inbound[dest] = inbound.get(dest, 0) + 1
    if inbound:
        ranked = ", ".join(
            f"{name}={count}"
            for name, count in sorted(inbound.items(), key=lambda item: (-item[1], item[0]))[:8]
        )
        lines.append(f"  %% in-degree: {ranked}")
    return "\n".join(lines)


DIAGRAMS: tuple[Diagram, ...] = (
    Diagram("permission-model.mmd", "src/consilient/effects.py", render_permission),
    Diagram("event-flow.mmd", "src/consilient/events.py", render_event_flow),
    Diagram("data-model.mmd", "src/consilient/projection.py", render_data_model),
    Diagram("module-dependency.mmd", "src/**/*.py", render_modules),
)


def render_all(root: Path = ROOT) -> list[tuple[str, bytes]]:
    rendered: list[tuple[str, bytes]] = []
    for diagram in DIAGRAMS:
        body = diagram.render(root)
        rendered.append(
            (
                diagram.name,
                _document(diagram.source, source_digest(root, diagram.source), body),
            )
        )
    return rendered


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if any generated diagram has drifted"
    )
    args = parser.parse_args(argv)
    try:
        rendered = render_all()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    if args.check:
        drifted = []
        for name, content in rendered:
            path = DIAGRAM_DIR / name
            current = path.read_bytes() if path.exists() else b""
            if current != content:
                drifted.append(name)
        if drifted:
            joined = ", ".join(drifted)
            print(
                f"FAIL docs/diagrams/{joined} has drifted; run python {PRODUCER}",
                file=sys.stderr,
            )
            return 1
        print("docs/diagrams is current")
        return 0
    for name, content in rendered:
        write_atomic(DIAGRAM_DIR / name, content)
        print(f"wrote docs/diagrams/{name} ({len(content)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Turn the parsed source into Mermaid, one renderer per diagram.

Hand-drawn permission and event diagrams drifted the moment the code moved. On 23 August
2026 the documentation plan recorded the live case: drafting the permission model from
ADR-0033 put material_choice on the escalate path, while `_disposition_for` in
`src/consilient/effects.py` executes it. Generation is the check that makes that
contradiction visible.

Four renderers, registered in DIAGRAMS beside the source pattern each is responsible
for: the permission model from `effects.py`, the event flow from the `*_KIND` constants
in `events.py`, the entity-relationship model from the SCHEMA string in `projection.py`,
and the module dependency graph from every tracked Python file under `src`. `render_all`
runs all four and wraps each body in its provenance header. It renders bytes and returns
them; deciding what to do with them belongs to the caller, so nothing here touches the
filesystem.

A renderer raises ValueError rather than emitting an empty document — no admission
functions found, no `*_KIND` constants, a SCHEMA with no tables, no `src` directory. An
empty flowchart is the dangerous output, because it renders, it exits zero and it looks
finished, and a diagram that has quietly lost its content is worse than one that failed
to build. The same instinct runs through `_disposition_edges`, which reconstructs the
default arm of a guard-clause function from the declared universe of admission classes,
and through `_family_trees`, which follows a facade's re-exports into the siblings that
now hold the code."""

from __future__ import annotations
import ast
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_diagrams_sources import (
    Diagram,
    ROOT,
    TABLE_RE,
    _admission_classes,
    _assigned_string,
    _columns,
    _constant_string,
    _declared_admission_classes,
    _document,
    _function,
    _ident,
    _known_modules,
    _label,
    _parse,
    _resolve_from,
    _return_strings,
    source_digest,
)


__all__ = [
    "DIAGRAMS",
    "Diagram",
    "ROOT",
    "TABLE_RE",
    "_admission_classes",
    "_assigned_string",
    "_columns",
    "_constant_string",
    "_declared_admission_classes",
    "_document",
    "_function",
    "_ident",
    "_known_modules",
    "_label",
    "_parse",
    "_resolve_from",
    "_return_strings",
    "render_all",
    "render_data_model",
    "render_event_flow",
    "render_modules",
    "render_permission",
    "source_digest",
]


def _terminal_disposition(statements: list[ast.stmt]) -> str | None:
    returns = [stmt for stmt in statements if isinstance(stmt, ast.Return)]
    if len(returns) != 1 or any(
        not isinstance(stmt, ast.Return) for stmt in statements
    ):
        return None
    disposition, _reason = _return_strings(returns[0])
    return disposition


def _disposition_edges(
    fn: ast.FunctionDef, universe: tuple[str, ...] = ()
) -> list[tuple[str, str]]:
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

    # The trailing top-level return is the DEFAULT ARM: in a guard-clause function it applies to
    # every class the guards above did not claim. Without this the diagram silently omits real
    # routing -- `material_choice` reaches `execute` only through this arm, and a permission model
    # that leaves out where a class actually goes is worse than no diagram, because it looks
    # complete. Measured 24 August 2026 by a test asserting that very edge.
    handled = {source for source, _ in edges}
    trailing = fn.body[-1] if fn.body else None
    if universe and isinstance(trailing, ast.Return):
        disposition, _reason = _return_strings(trailing)
        if disposition:
            for name in universe:
                if name not in handled:
                    edges.append((name, disposition))

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

    def emit_value(
        value: ast.expr | None, origin: str | None, edge_label: str | None
    ) -> None:
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
    trees = _family_trees(root, "src/consilient/effects.py")

    def find(name: str) -> ast.FunctionDef | None:
        for tree in trees:
            found = _function(tree, name)
            if found is not None:
                return found
        return None

    lines = ["flowchart TB"]
    for name in ("derive_admission", "_classify_admission"):
        fn = find(name)
        if fn is None:
            continue
        lines.append(f'  subgraph {_ident(name)}["{name}"]')
        _emit_control_flow(fn, lines)
        lines.append("  end")
    disposition = find("_disposition_for")
    if disposition is not None:
        lines.append('  subgraph disposition["_disposition_for"]')
        classes = next(
            (c for tree in trees if (c := _declared_admission_classes(tree))), ()
        )
        edges = _disposition_edges(disposition, classes)
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
    kinds: list[str] = []
    functions: set[str] = set()
    for node in [
        node
        for tree in _family_trees(root, "src/consilient/events.py")
        for node in tree.body
    ]:
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
        lines.append(f'  {previous} -.-> REGISTER["register_transition_validator()"]')
    return "\n".join(lines)


def _family_trees(root: Path, relative: str) -> list[ast.Module]:
    """The module's own tree, plus every sibling it re-exports from.

    This generator reads SOURCE rather than importing, so it sees a facade for what it literally
    is: `from .effects_proof import _classify_admission` is an ImportFrom, not a FunctionDef, and
    a renderer looking for the function finds nothing.

    MEASURED 28 August 2026, twice in one afternoon. Splitting projection.py moved SCHEMA into
    projection_schema.py and build_diagrams.py failed outright with "SCHEMA string not found".
    Splitting effects.py was worse, because it did not fail: `derive_admission` stayed in the
    entry point while `_classify_admission` and `_disposition_for` moved, so the permission model
    still rendered, still exited zero, and quietly lost the `execute` routing. A generated
    document that silently loses half its content is the failure this repository is about.

    Following the re-exports is preferred to repointing each path at today's sibling, because the
    facade is the one thing guaranteed to go on naming the right files. One level is enough: the
    splitter never chains a re-export through a second facade.
    """
    own = _parse(root, relative)
    trees = [own]
    parent = Path(relative).parent.as_posix()
    for node in own.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        sibling = f"{parent}/{node.module.lstrip('.')}.py"
        if (root / sibling).is_file():
            trees.append(_parse(root, sibling))
    return trees


def render_data_model(root: Path) -> str:
    schema = next(
        (
            value
            for tree in _family_trees(root, "src/consilient/projection.py")
            if (value := _assigned_string(tree, "SCHEMA")) is not None
        ),
        None,
    )
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
            for name, count in sorted(
                inbound.items(), key=lambda item: (-item[1], item[0])
            )[:8]
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

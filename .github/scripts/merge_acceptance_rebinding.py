"""C1 alone: a name bound more than once at module level by assignment.

This is the half of the merge gate that no other tool owns. ruff F811, pyflakes F811 and
mypy no-redef all cover function, class and import redefinition and stop there — a
module-level `KINDS = ...` rebound passes every one of them, and did, in the T01
specimen [measured 24 Aug 2026].

The walk is over `tree.body` only, and collects names bound by `ast.Assign` and
`ast.AnnAssign`. Widening it to `ast.walk`, or to FunctionDef, ClassDef or Import,
duplicates ruff and mypy and reintroduces exactly the false alarms they were written to
avoid. `tests/test_merge_acceptance.py::test_c1_does_not_flag_function_class_or_import_r
edefinition` pins that narrowness.

`_display` travels with `rebinding_findings` because it is that function's first caller,
and a six-line path formatter does not earn a file of its own. The gate imports it back
for `ddl_tree_findings`. It could not have stayed behind: a sibling importing the gate
would be a cycle, since the gate already imports this module."""

import ast
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


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

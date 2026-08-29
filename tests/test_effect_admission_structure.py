"""Source-level pins on consilient.effects itself, not on what it computes.

These read the module's own text: that _disposition_for has no unreachable arms, that
derive_admission still documents being unwired, that nothing in production calls it. A
behavioural test cannot see any of them, which is exactly why they are here -- and why they sit
apart from the tests that exercise the ladder.
"""

import ast
import inspect

from pathlib import Path

from consilient import effects as effects_mod

from consilient.effects import (
    derive_admission,
)


def _function_source(name: str) -> str:
    # Read the file the function actually lives in. effects.py was split on 28 August 2026 and
    # `_disposition_for` moved to a sibling, so reading `effects_mod.__file__` reported it
    # "missing" -- which reads like a deleted function rather than a moved one. Asking the
    # resolved object where its source is keeps this pinned to the code it is about.
    resolved = getattr(effects_mod, name, None)
    origin = inspect.getsourcefile(resolved) if resolved is not None else None
    source = Path(origin or effects_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            segment = ast.get_source_segment(source, node)
            if segment is None:
                raise AssertionError(f"{name} has no source segment")
            return segment
    raise AssertionError(f"{name} is missing")


def test_disposition_for_has_no_unreachable_arms() -> None:
    text = _function_source("_disposition_for")
    assert "capability_gap" not in text
    assert "unhandled_admission_class" not in text
    assert "process_not_contained" not in text


def test_derive_admission_documents_that_it_is_unwired() -> None:
    doc = derive_admission.__doc__ or ""
    assert "ADR-0078" in doc
    assert "unwired" in doc.casefold()


def test_derive_admission_has_no_production_caller() -> None:
    callers: list[str] = []
    root = Path(effects_mod.__file__).resolve().parent
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else ""
            )
            if called != "derive_admission":
                continue
            if path.resolve() == Path(effects_mod.__file__).resolve():
                continue
            callers.append(f"{path.name}:{node.lineno}")
    assert callers == []

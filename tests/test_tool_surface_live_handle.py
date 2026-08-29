"""The scan that is not the boundary, and the product-tree lock that is.

A syntactic import-statement scan is not the boundary. The sealed evaluator was escaped
with ``__import__("sys")._getframe()`` because ``find_forbidden_imports`` walks only
``Import`` / ``ImportFrom``. That residual is measured here against the live function
rather than hidden, and the irreversible 0% is explicitly not rested on it: it rests on
the classifier plus the absence of a live handle in the product tree, which is what the
rest of this file holds - ``capabilities.py`` and ``effects.py`` import none of
subprocess, socket, http, urllib, requests or httpx, and the classifier returns a label
rather than a callable.

MEASURED 26 August 2026: ``_LIVE = __import__('subprocess')`` reached the exact same
live handle as ``import subprocess`` in the product tree while the full 52-test suite
stayed green, because ``_product_imports`` walked only Import/ImportFrom and a
``__import__`` call is a Call node. That is the same class of gap as the getframe
escape, except this one governed the "no live handle" claim itself, which the suite does
not treat as an honest residual. The scan now follows ``__import__(...)`` and
``importlib.import_module(...)`` calls, and a planted handle of each shape is asserted
caught.

The composition residual belongs here because it is read from source in the same way:
``derive_admission`` does not consult ``classify_reversibility``. 0% on irreversible
*labels* is classifier construction; 0% on irreversible *execution* is admission plus
this AST lock, and those two are not composed. Wiring them is an effects.py /
capabilities.py change and is outside this unit's claim list."""

import ast
import inspect
from pathlib import Path
from consilient.capabilities import (
    classify_reversibility,
)
from consilient.effects import (
    derive_admission,
)
from consilient.promote import find_forbidden_imports

ROOT = Path(__file__).resolve().parents[1]

PRODUCT = ROOT / "src" / "consilient"

GETFRAME_ESCAPE = """
def solve(prompt):
    frame = __import__("sys")._getframe()
    while frame is not None:
        for value in frame.f_locals.values():
            if value == prompt:
                return "leaked"
        frame = frame.f_back
    return "miss"
"""


def _import_statement_modules(source: str) -> set[str]:
    """The class of guard that missed the getframe escape: statements only."""
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".", 1)[0])
    return found


def _call_import_target(node: ast.Call) -> str | None:
    """The module name a `__import__(...)` / `importlib.import_module(...)` call names.

    MEASURED 26 August 2026: `_LIVE = __import__('subprocess')` reaches the exact same
    live handle as `import subprocess`, but is a Call node, not Import/ImportFrom, so the
    statement-only scan below missed it entirely -- the same class of gap the module
    docstring already names for the getframe escape, except this one governs the product
    tree's own "no live handle" claim, which the suite does not treat as an honest residual.
    """
    func = node.func
    name = None
    if isinstance(func, ast.Name) and func.id == "__import__":
        name = "__import__"
    elif (
        isinstance(func, ast.Attribute)
        and func.attr == "import_module"
        and isinstance(func.value, ast.Name)
        and func.value.id == "importlib"
    ):
        name = "import_module"
    if name is None or not node.args:
        return None
    arg = node.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value.split(".", 1)[0]
    return None


def _product_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            target = _call_import_target(node)
            if target:
                found.add(target)
    return found


def test_import_statement_scan_misses_the_getframe_escape() -> None:
    """Honest residual of the scan that is not our boundary."""
    assert _import_statement_modules(GETFRAME_ESCAPE) == set()
    assert find_forbidden_imports(GETFRAME_ESCAPE, frozenset()) == []


def test_irreversible_zero_does_not_rest_on_that_scan() -> None:
    """The construction is the classifier plus no live handle, not the scan."""
    assert classify_reversibility("tool", "bash") == 4
    assert classify_reversibility("tool", "webfetch") == 4
    source = inspect.getsource(classify_reversibility)
    assert "find_forbidden_imports" not in source
    assert "__import__" not in ast.dump(ast.parse(source))


def test_product_classifier_and_admission_have_no_live_irreversible_handle() -> None:
    banned = {"subprocess", "socket", "http", "urllib", "requests", "httpx"}
    for name in ("capabilities.py", "effects.py"):
        imported = _product_imports(PRODUCT / name)
        assert not (imported & banned), (
            f"{name} grew a live handle: {imported & banned}"
        )
    assert classify_reversibility.__code__.co_consts is not None
    # A label, not a callable tool: no handle is returned.
    assert classify_reversibility("tool", "webfetch") == 4


def test_product_scan_catches_a_dunder_import_live_handle(tmp_path: Path) -> None:
    """MEASURED 26 August 2026: `_LIVE = __import__('subprocess')` reached a live
    subprocess handle in the product tree while the full 52-test suite stayed green,
    because `_product_imports` walked only Import/ImportFrom. The scan now also follows
    `__import__(...)` and `importlib.import_module(...)` calls.
    """
    live_handle = tmp_path / "planted.py"
    live_handle.write_text("_LIVE = __import__('subprocess')\n", encoding="utf-8")
    assert _product_imports(live_handle) == {"subprocess"}

    import_module_handle = tmp_path / "planted_importlib.py"
    import_module_handle.write_text(
        "import importlib\n_LIVE = importlib.import_module('socket')\n",
        encoding="utf-8",
    )
    assert "socket" in _product_imports(import_module_handle)


def test_classifier_is_not_an_admission_chokepoint() -> None:
    """Residual: derive_admission does not consult classify_reversibility.

    0% on irreversible *labels* is classifier construction. 0% on irreversible
    *execution* is admission plus the product-tree AST lock, and those two
    are not composed. Wiring them is an effects.py / capabilities.py change
    and is outside this unit's claim list.
    """
    source = inspect.getsource(derive_admission)
    assert "classify_reversibility" not in source

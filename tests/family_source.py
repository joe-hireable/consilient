"""Read a module's whole FAMILY, for the tests that assert on source rather than behaviour.

A number of invariants here are checked by parsing a module and looking for a function, a
constant or the absence of one. That was exact while a module was one file. After the splits of
28 August 2026 it is not: `_lock_file` lives in a sibling of `events.py`, `_disposition_for` in a
sibling of `effects.py`, and a test that reads only the entry point reports the symbol MISSING --
which reads like a deletion and is in fact a move.

The honest unit for those assertions is the family, because the invariant was always about the
module's responsibility and never about which file held it. `events.py` and every `events_*.py`
together are what "events" means now, and a guard that says "nothing outside this module reads
feedback events" means nothing outside that set.

Nothing here decides what a family IS beyond the naming convention the splitter enforces and
`tests/test_repo_shape.py` already relies on: the entry point keeps the original filename and its
siblings are `<stem>_*.py` beside it. A sibling named otherwise would be invisible to this, which
is exactly why that convention is enforced rather than encouraged.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def family_files(stem: str, package: str = "src/consilient") -> list[Path]:
    """The entry point and its split siblings, entry first."""
    directory = ROOT / package
    entry = directory / f"{stem}.py"
    files = [entry] if entry.is_file() else []
    files.extend(sorted(p for p in directory.glob(f"{stem}_*.py") if p.is_file()))
    return files


def family_source(stem: str, package: str = "src/consilient") -> str:
    """Every file of the family concatenated, for a substring or regex assertion."""
    return "\n".join(p.read_text(encoding="utf-8") for p in family_files(stem, package))


def family_trees(stem: str, package: str = "src/consilient") -> list[ast.Module]:
    return [
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for p in family_files(stem, package)
    ]


def find_def(
    stem: str, name: str, package: str = "src/consilient"
) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, str] | None:
    """The definition of `name` anywhere in the family, with the source of the file holding it."""
    for path in family_files(stem, package):
        text = path.read_text(encoding="utf-8")
        for node in ast.parse(text, filename=str(path)).body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == name
            ):
                return node, text
    return None

def seam(stem: str) -> ModuleType:
    """The sibling of a script family that DEFINES a patched name.

    scripts/dispatch.py was split on 28 August 2026 and its callers now reach a patched symbol
    as `dispatch_launch.run_process(...)`, so that the attribute is resolved at call time against
    the object a patch mutates. A test must therefore patch the module that DEFINES the name;
    patching the entry point binds a facade alias no code reads, and the failure is silent --
    the real function runs and the assertion fails somewhere further down.

    Loads by path when the module is not already imported, because scripts/ is not a package.
    """
    if stem in sys.modules:
        return sys.modules[stem]
    path = ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, path)
    if spec is None or spec.loader is None:  # pragma: no cover - a missing sibling is a bug
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[stem] = module
    spec.loader.exec_module(module)
    return module

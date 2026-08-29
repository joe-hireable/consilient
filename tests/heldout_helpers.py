"""Contract fixtures and module loaders shared by the held-out isolation tests.

The checker and the dispatch script are both loaded from their paths rather than
imported, because neither is a package module; `_load_module` is the one place that does
it, so a stale name fails loudly instead of landing on an alias. `DISTINCTIVE_LINE` is
deliberately an unusual sequence of operational constraints: a copied assertion must not
be able to resemble ordinary project boilerplate by accident, and `SHORT_LINE` is its
control -- short enough that any leak detector matching it would be matching noise.
`_isolated_pair` places the contract outside the worktree, which is the only arrangement
in which a build is permitted to proceed at all."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

DISTINCTIVE_LINE = (
    "Held-out isolation fingerprints a deliberately unusual sequence of operational "
    "constraints so a copied assertion cannot resemble ordinary project boilerplate "
    "by accident."
)

SHORT_LINE = "short assertion"

CONTRACT_BODY = f"{SHORT_LINE}\n{DISTINCTIVE_LINE}\n"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_dispatch() -> ModuleType:
    return _load_module("heldout_dispatch", Path("scripts/dispatch.py").resolve())


def _load_checker() -> ModuleType:
    return _load_module(
        "heldout_isolation_checker",
        Path(".github/scripts/check_heldout_isolation.py").resolve(),
    )


def _write_contract(path: Path, body: str = CONTRACT_BODY) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _isolated_pair(tmp_path: Path) -> tuple[Path, Path]:
    worktree = tmp_path / "work"
    worktree.mkdir()
    contract = _write_contract(tmp_path / "heldout" / "secret-contract.md")
    return worktree, contract

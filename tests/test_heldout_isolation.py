"""Held-out contracts cannot be safely supplied to an unsandboxed dispatch."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_dispatch() -> ModuleType:
    path = Path("scripts/dispatch.py").resolve()
    spec = importlib.util.spec_from_file_location("heldout_dispatch", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode", ((), ("--dry-run",), ("--fan-out",)))
def test_heldout_contract_refuses_before_dispatch_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mode: tuple[str, ...],
) -> None:
    """Removing the held-out preflight would allow a child to read its target."""
    dispatch = _load_dispatch()
    monkeypatch.setattr(dispatch, "resolve_cwd", lambda _value: tmp_path)
    monkeypatch.setattr(
        dispatch,
        "refresh_default_headroom",
        lambda _path: pytest.fail("held-out refusal must precede further dispatch preflight"),
    )

    code = dispatch.main(
        ["build the artefact", "--heldout-contract", str(tmp_path / "contract.py"), *mode]
    )

    assert code == 2
    assert "same-OS-user unsandboxed dispatch" in capsys.readouterr().out

"""Gate B4 credits bounded real pytest repairs, never synthetic restores."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from consilient.cli import _foreign_tickets


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "b4_tickets.py"
PYTEST_UPSTREAM = Path(r"C:/Users/jpbpr/Repositories/pytest-upstream")
PYTEST_PYTHON = PYTEST_UPSTREAM / ".venv/Scripts/python.exe"
ReceiptAction = Callable[[Path, Any], None]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("b4_tickets_script", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source(tmp_path: Path, tickets: tuple[Any, ...]) -> Path:
    root = tmp_path / "source"
    by_path: dict[str, list[bytes]] = {}
    for ticket in tickets:
        by_path.setdefault(ticket.path, []).append(ticket.before)
    for path, chunks in by_path.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"\r\n".join(chunks))
    version = root / "src/_pytest/_version.py"
    version.parent.mkdir(parents=True, exist_ok=True)
    version.write_text("__commit_id__ = commit_id = 'gc99f595a8'\n", encoding="utf-8")
    full_suite = root / "testing/test_mark.py"
    full_suite.parent.mkdir(parents=True, exist_ok=True)
    full_suite.write_text("def test_mark():\n    assert True\n", encoding="utf-8")
    return root


def _ticket(script: ModuleType, *, synthetic: bool = False) -> Any:
    return replace(script.TICKETS[0], synthetic=synthetic)


def _prepare(
    script: ModuleType,
    tmp_path: Path,
) -> Path:
    return _source(tmp_path, script.TICKETS)


def _agent_on_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[str]:
    executable = tmp_path / "bin" / "codex.cmd"
    executable.parent.mkdir()
    executable.write_text("@exit /b 0\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(executable.parent) + os.pathsep + os.environ["PATH"])
    return ["codex"]


def _process(
    action: ReceiptAction,
    *,
    red: int = 1,
) -> Callable[..., tuple[int, bool, float, None]]:
    def run(
        argv: list[str],
        *,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        **_kwargs: Any,
    ) -> tuple[int, bool, float, None]:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_bytes(f"stdout:{stdout_path.name}".encode())
        stderr_path.write_bytes(f"stderr:{stderr_path.name}".encode())
        if stdout_path.name == "agent.stdout.txt":
            action(cwd, argv)
        return (red if stdout_path.name == "red.stdout.txt" else 0), False, 0.0, None

    return run


def _repair(ticket: Any) -> ReceiptAction:
    def action(cwd: Path, _argv: Any) -> None:
        path = cwd / ticket.path
        path.write_bytes(path.read_bytes().replace(ticket.after, b"fixed", 1))

    return action


def _outcome(log: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    return next(row["data"] for row in rows if row["event"] == "attempt.outcome")


def test_script_entrypoint_imports_without_project_pythonpath(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not PYTEST_PYTHON.is_file(), reason="pytest upstream venv unavailable")
def test_verify_source_accepts_pinned_pytest_upstream() -> None:
    _load_script().verify_source(PYTEST_UPSTREAM)


def test_net_zero_restoration_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    ticket = _ticket(script)
    source = _prepare(script, tmp_path)

    def restore(cwd: Path, _argv: Any) -> None:
        path = cwd / ticket.path
        path.write_bytes(path.read_bytes().replace(ticket.after, ticket.before, 1))

    monkeypatch.setattr(script, "run_process", _process(restore))
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, ticket, _agent_on_path(monkeypatch, tmp_path), log, timeout_s=1, python=sys.executable
    )
    assert not log.exists()
    assert _foreign_tickets(log.parent) == 0


def test_undeclared_changed_path_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    ticket = _ticket(script)
    source = _prepare(script, tmp_path)

    def tamper(cwd: Path, argv: Any) -> None:
        _repair(ticket)(cwd, argv)
        (cwd / "undeclared.py").write_text("no", encoding="utf-8")

    monkeypatch.setattr(script, "run_process", _process(tamper))
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, ticket, _agent_on_path(monkeypatch, tmp_path), log, timeout_s=1, python=sys.executable
    )
    assert not log.exists()
    assert _foreign_tickets(log.parent) == 0


def test_bounded_real_repair_is_credited_and_counted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    ticket = _ticket(script)
    source = _prepare(script, tmp_path)
    monkeypatch.setattr(script, "run_process", _process(_repair(ticket)))
    log = tmp_path / "log" / "events.jsonl"

    assert script.run_ticket(
        source, ticket, _agent_on_path(monkeypatch, tmp_path), log, timeout_s=1, python=sys.executable
    )
    assert _foreign_tickets(log.parent) == 1
    outcome = _outcome(log)
    assert outcome["harness"] == "codex"
    assert outcome["corpus_revision"] == "c99f595a8"


def test_durable_receipts_have_the_recorded_fixed_order_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    ticket = _ticket(script)
    source = _prepare(script, tmp_path)
    monkeypatch.setattr(script, "run_process", _process(_repair(ticket)))
    log = tmp_path / "log" / "events.jsonl"

    assert script.run_ticket(
        source, ticket, _agent_on_path(monkeypatch, tmp_path), log, timeout_s=1, python=sys.executable
    )
    receipt_dir = script.RECEIPT_ROOT / ticket.id
    assert receipt_dir.is_dir()
    digest = hashlib.sha256(
        b"".join((receipt_dir / name).read_bytes() for name in script.RECEIPT_FILES)
    ).hexdigest()
    assert _outcome(log)["receipt_sha256"] == digest


def test_synthetic_seed_cannot_emit_ticket_completed_or_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    synthetic = replace(script.TICKETS[0], synthetic=True)
    source = _prepare(script, tmp_path)
    monkeypatch.setattr(script, "run_process", _process(_repair(synthetic)))
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source,
        synthetic,
        _agent_on_path(monkeypatch, tmp_path),
        log,
        timeout_s=1,
        python=sys.executable,
    )
    assert _foreign_tickets(log.parent) == 0
    assert all(
        json.loads(line)["event"] != "ticket.completed"
        for line in log.read_text(encoding="utf-8").splitlines()
    )


def test_collection_error_remains_ineligible_for_credit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = _load_script()
    ticket = _ticket(script)
    source = _prepare(script, tmp_path)
    monkeypatch.setattr(script, "run_process", _process(_repair(ticket), red=2))
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, ticket, _agent_on_path(monkeypatch, tmp_path), log, timeout_s=1, python=sys.executable
    )
    assert not log.exists()

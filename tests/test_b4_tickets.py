"""Gate B4 tickets credit only isolated, restored pytest upstream repairs."""

from __future__ import annotations

import importlib.util
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from consilient.cli import _foreign_tickets, cmd_doctor


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "b4_tickets.py"
PYTEST_UPSTREAM = Path(r"C:/Users/jpbpr/Repositories/pytest-upstream")
PYTEST_PYTHON = PYTEST_UPSTREAM / ".venv/Scripts/python.exe"


def _load_script():
    spec = importlib.util.spec_from_file_location("b4_tickets_script", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source(tmp_path: Path, tickets: object) -> Path:
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
    version.write_text(
        "__commit_id__ = commit_id = 'gc99f595a8'\n",
        encoding="utf-8",
    )
    (root / "testing" / "test_mark.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "testing" / "test_mark.py").write_text("def test_mark():\n    assert True\n", encoding="utf-8")
    return root


def _prepare(script: object, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    source = _source(tmp_path, script.TICKETS)
    monkeypatch.setattr(script, "verify_source", lambda root: None)
    monkeypatch.setattr(
        script,
        "archive_source",
        lambda root, destination: shutil.copytree(root, destination),
    )
    return source


def test_script_entrypoint_imports_without_project_pythonpath(tmp_path: Path) -> None:
    """Removing the script bootstrap makes direct execution fail before argument parsing."""
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


def test_corpus_constants_target_pytest_not_itsdangerous() -> None:
    """The runner must pin pytest-dev/pytest, not the retired itsdangerous corpus."""
    script = _load_script()

    assert script.REPOSITORY == "pytest-dev/pytest"
    assert script.REMOTE == "https://github.com/pytest-dev/pytest.git"
    assert script.FULL_SUITE == "testing/test_mark.py"
    assert all(ticket.id.startswith("B4-PYT-") for ticket in script.TICKETS)
    assert {ticket.issue for ticket in script.TICKETS} == {"13369", "14774", "6505"}


@pytest.mark.skipif(not PYTEST_PYTHON.is_file(), reason="pytest upstream venv unavailable")
def test_verify_source_accepts_pinned_pytest_upstream() -> None:
    """The live corpus pin must match the editable pytest checkout."""
    script = _load_script()

    script.verify_source(PYTEST_UPSTREAM)


def test_known_seeds_are_unique_and_a_passing_red_phase_is_not_credited(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Changing the seed or accepting its target test must fail this test."""
    script = _load_script()
    source = _prepare(script, monkeypatch, tmp_path)
    ticket = script.TICKETS[0]
    calls = 0

    def successful_process(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return 0, False, 0.0, None

    monkeypatch.setattr(script, "run_process", successful_process)
    log = tmp_path / "log" / "events.jsonl"

    assert len({item.before for item in script.TICKETS}) == len(script.TICKETS)
    assert not script.run_ticket(source, ticket, ["agent"], log, timeout_s=1, python=sys.executable)
    assert calls == 1
    assert _foreign_tickets(log.parent) == 0


@pytest.mark.parametrize("outcome", [(None, True), (1, False)])
def test_timeout_or_agent_failure_never_appends_credit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: tuple[int | None, bool]
) -> None:
    """Removing the timeout/error guard would incorrectly credit a failed repair."""
    script = _load_script()
    source = _prepare(script, monkeypatch, tmp_path)
    responses = [(1, False), outcome]
    monkeypatch.setattr(
        script,
        "run_process",
        lambda *_args, **_kwargs: (*responses.pop(0), 0.0, None),
    )
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, script.TICKETS[0], ["agent"], log, timeout_s=1, python=sys.executable
    )
    assert _foreign_tickets(log.parent) == 0


def test_pytest_collection_error_does_not_qualify_as_a_red_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Changing the red guard to accept exit 2 would execute an invalid ticket."""
    script = _load_script()
    source = _prepare(script, monkeypatch, tmp_path)
    calls = 0

    def collection_error(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return 2, False, 0.0, None

    monkeypatch.setattr(script, "run_process", collection_error)
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, script.TICKETS[0], ["agent"], log, timeout_s=1, python=sys.executable
    )
    assert calls == 1
    assert _foreign_tickets(log.parent) == 0


def test_manifest_or_test_tampering_never_appends_credit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Removing the manifest comparison would credit an out-of-scope repair."""
    script = _load_script()
    source = _prepare(script, monkeypatch, tmp_path)
    ticket = script.TICKETS[0]
    target = source / ticket.target.split("::")[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("original test", encoding="utf-8")
    calls = 0

    def process(_argv, *, cwd, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            (cwd / ticket.target.split("::")[0]).write_text("tampered", encoding="utf-8")
            (cwd / ticket.path).write_bytes(ticket.before)
        return (1 if calls == 1 else 0), False, 0.0, None

    monkeypatch.setattr(script, "run_process", process)
    log = tmp_path / "log" / "events.jsonl"

    assert not script.run_ticket(
        source, ticket, ["agent"], log, timeout_s=1, python=sys.executable
    )
    assert _foreign_tickets(log.parent) == 0


def test_three_restored_repairs_are_counted_but_do_not_open_gate_b4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Breaking the event pair or foreign-ticket join changes the counted total."""
    script = _load_script()
    source = _prepare(script, monkeypatch, tmp_path)
    source_manifest = {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(source.rglob("*"))
        if path.is_file()
    }
    append_calls = []
    append = script.events.append

    def tracked_append(*args, **kwargs):
        append_calls.append((args, kwargs))
        return append(*args, **kwargs)

    monkeypatch.setattr(script.events, "append", tracked_append)
    active_ticket: object | None = None
    calls = 0

    def process(argv, *, cwd, **_kwargs):
        nonlocal active_ticket, calls
        calls += 1
        if argv == ["agent"]:
            assert active_ticket is not None
            path = cwd / active_ticket.path
            path.write_bytes(path.read_bytes().replace(active_ticket.after, active_ticket.before, 1))
            return 0, False, 0.0, None
        assert active_ticket is not None
        seeded = active_ticket.after in (cwd / active_ticket.path).read_bytes()
        return (1 if seeded else 0), False, 0.0, None

    monkeypatch.setattr(script, "run_process", process)
    log = tmp_path / "log" / "events.jsonl"
    for ticket in script.TICKETS:
        active_ticket = ticket
        assert script.run_ticket(
            source, ticket, ["agent"], log, timeout_s=1, python=sys.executable
        )

    events = log.read_text(encoding="utf-8").splitlines()
    assert len(events) == 6
    assert len(append_calls) == 6
    assert calls == 12
    assert _foreign_tickets(log.parent) == 3
    final_manifest = {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(source.rglob("*"))
        if path.is_file()
    }
    assert final_manifest == source_manifest

    args = type("Args", (), {"log": str(log.parent), "db": str(tmp_path / "state.db")})()
    doctor = cmd_doctor(args)
    b4 = next(item for item in doctor["gates"]["B"]["conditions"] if item["id"] == "B4")
    assert b4["status"] == "fail"
    assert b4["reason"].startswith("3 of 20")
    assert doctor["routing_orchestration_enabled"] is False


@pytest.mark.skipif(not PYTEST_PYTHON.is_file(), reason="pytest upstream venv unavailable")
def test_end_to_end_tickets_credit_pytest_upstream(tmp_path: Path) -> None:
    """Three genuine pytest repairs must red, verify and restore against the live corpus."""
    script = _load_script()
    log = tmp_path / "log"

    for ticket in script.TICKETS:
        agent = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                f"path=Path({repr(ticket.path)}); "
                "path.write_bytes(path.read_bytes().replace("
                + repr(ticket.after)
                + ", "
                + repr(ticket.before)
                + ", 1))"
            ),
        ]
        assert script.run_ticket(
            PYTEST_UPSTREAM,
            ticket,
            agent,
            log,
            timeout_s=300,
            python=str(PYTEST_PYTHON),
        )

    assert _foreign_tickets(log) == 3

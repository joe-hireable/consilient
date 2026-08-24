"""Run three verified Gate B4 repairs against the pinned pytest upstream corpus."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from consilient import events  # noqa: E402
from scripts.dispatch import run_process  # noqa: E402


REVISION = "c99f595a896eb84c1dda4f4b85a0929c52011e27"
REMOTE = "https://github.com/pytest-dev/pytest.git"
REPOSITORY = "pytest-dev/pytest"
FULL_SUITE = "testing/test_mark.py"
_VERSION_FILE = Path("src") / "_pytest" / "_version.py"
_CORPUS_IGNORE = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
}


@dataclass(frozen=True)
class Ticket:
    id: str
    path: str
    target: str
    before: bytes
    after: bytes
    issue: str


TICKETS = (
    Ticket(
        "B4-PYT-13369",
        "src/_pytest/pytester.py",
        "testing/test_pytester.py::test_assert_outcomes_after_pytest_error",
        (
            b"            raise ValueError(\r\n"
            b'                "Pytest terminal summary report not found. "\r\n'
            b'                "Plugins that modify pytest\'s terminal output can break outcome "\r\n'
            b'                "parsing. Disable the plugin for the test run, for example with "\r\n'
            b'                "`-p no:<plugin>`, or disable plugin autoloading with "\r\n'
            b'                "`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`."\r\n'
            b"            )"
        ),
        b'            raise ValueError("Pytest terminal summary report not found")',
        "13369",
    ),
    Ticket(
        "B4-PYT-14774",
        "src/_pytest/fixtures.py",
        "testing/deprecated_test.py::test_higher_scope_instance_method_is_deprecated[Scope.Module]",
        b"    if fixturedef._scope >= Scope.Class:",
        b"    if fixturedef._scope is Scope.Class:",
        "14774",
    ),
    Ticket(
        "B4-PYT-6505",
        "src/_pytest/pytester.py",
        "testing/test_pytester.py::test_parse_summary_line_always_plural",
        b'            "warning": "warnings",',
        b'            "warning": "warning",',
        "6505",
    ),
)


def _environment(root: Path, python: str) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("GIT_", "PYTEST_", "PYTHON"))
        and key.upper() not in {"VIRTUAL_ENV"}
    }
    env.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str((root / "src").resolve()),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    env["PYTHONEXECUTABLE"] = python
    return env


def _command(
    argv: list[str],
    root: Path,
    receipts: Path,
    name: str,
    timeout_s: int,
    *,
    python: str,
) -> tuple[int | None, bool]:
    code, timed_out, _duration, _timing = run_process(
        argv,
        cwd=root,
        stdout_path=receipts / f"{name}.stdout.txt",
        stderr_path=receipts / f"{name}.stderr.txt",
        timeout_s=timeout_s,
        env=_environment(root, python),
    )
    return code, timed_out


def _read_commit_id(root: Path) -> str:
    version_file = root / _VERSION_FILE
    try:
        text = version_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"pytest corpus version file missing: {version_file}") from exc
    match = re.search(r"__commit_id__ = commit_id = '(?P<commit>g?[0-9a-f]+)'", text)
    if not match:
        raise RuntimeError("pytest corpus commit id is unavailable")
    commit = match.group("commit").removeprefix("g")
    if not REVISION.startswith(commit):
        raise RuntimeError(f"pytest revision mismatch: expected {REVISION}, got {commit}")
    return commit


def verify_source(root: Path) -> None:
    """Reject anything except the clean, pinned public pytest corpus."""
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"source root is not a directory: {root}")
    if not (root / "testing" / "test_mark.py").is_file():
        raise RuntimeError("pytest corpus layout mismatch: testing/test_mark.py missing")
    _read_commit_id(root)
    for ticket in TICKETS:
        path = root / ticket.path
        if not path.is_file():
            raise RuntimeError(f"pytest corpus file missing: {ticket.path}")
        content = path.read_bytes()
        if content.count(ticket.before) != 1:
            raise RuntimeError(f"pytest corpus pin drifted in {ticket.path}")


def _ignore_corpus(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in _CORPUS_IGNORE}


def archive_source(root: Path, destination: Path) -> None:
    """Copy the editable pytest tree without instance-local artefacts."""
    destination.mkdir(parents=True, exist_ok=True)
    for child in root.iterdir():
        if child.name in _CORPUS_IGNORE:
            continue
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, ignore=_ignore_corpus, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)


def manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not any(part in _CORPUS_IGNORE for part in path.parts)
    }


def _seed(root: Path, ticket: Ticket) -> bool:
    path = root / ticket.path
    try:
        content = path.read_bytes()
    except OSError:
        return False
    if content.count(ticket.before) != 1:
        return False
    path.write_bytes(content.replace(ticket.before, ticket.after, 1))
    return True


def _log_file(path: Path) -> Path:
    return path if path.suffix == ".jsonl" else path / f"{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"


def _credit(log: Path, ticket: Ticket) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    attempt_id = f"{ticket.id}:repair:1"
    base = {"v": events.SCHEMA_VERSION, "ts": timestamp, "actor": "scripts.b4_tickets"}
    events.append(
        log,
        {
            **base,
            "event": events.OUTCOME_KIND,
            "data": {
                "repository": REPOSITORY,
                "task": ticket.id,
                "attempt_id": attempt_id,
                "attempt_lineage": ticket.id,
                "issue": ticket.issue,
                "verifier_accept": True,
            },
        },
    )
    events.append(
        log,
        {
            **base,
            "event": "ticket.completed",
            "data": {
                "repository": REPOSITORY,
                "ticket": ticket.id,
                "task": ticket.id,
                "attempt_id": attempt_id,
                "issue": ticket.issue,
            },
        },
    )


def run_ticket(
    source_root: Path,
    ticket: Ticket,
    agent_argv: list[str],
    log_path: Path,
    *,
    timeout_s: int,
    python: str,
) -> bool:
    """Credit one ticket only after red, repair, corpus verification and restoration."""
    if not agent_argv or timeout_s <= 0:
        return False
    try:
        verify_source(source_root)
        with tempfile.TemporaryDirectory(prefix="b4-ticket-") as temporary:
            temporary_root = Path(temporary)
            isolated = temporary_root / "isolated"
            receipts = temporary_root / "receipts"
            archive_source(source_root, isolated)
            original = manifest(isolated)
            if not _seed(isolated, ticket):
                return False
            red, timed_out = _command(
                [python, "-m", "pytest", ticket.target, "-q", "-p", "no:cacheprovider"],
                isolated,
                receipts,
                "red",
                timeout_s,
                python=python,
            )
            if timed_out or red != 1:
                return False
            code, timed_out = _command(
                agent_argv,
                isolated,
                receipts,
                "agent",
                timeout_s,
                python=python,
            )
            if timed_out or code != 0:
                return False
            for name, argv in (
                (
                    "target",
                    [python, "-m", "pytest", ticket.target, "-q", "-p", "no:cacheprovider"],
                ),
                (
                    "full",
                    [python, "-m", "pytest", FULL_SUITE, "-q", "-p", "no:cacheprovider"],
                ),
            ):
                code, timed_out = _command(
                    argv, isolated, receipts, name, timeout_s, python=python
                )
                if timed_out or code != 0:
                    return False
            if manifest(isolated) != original:
                return False
    except (OSError, RuntimeError):
        return False
    log = _log_file(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    _credit(log, ticket)
    return True


def run_tickets(
    source_root: Path,
    agent_argv: list[str],
    log_path: Path,
    *,
    timeout_s: int,
    python: str,
    ticket_id: str | None = None,
) -> bool:
    selected = tuple(item for item in TICKETS if ticket_id in (None, item.id))
    return bool(selected) and all(
        run_ticket(
            source_root,
            item,
            agent_argv,
            log_path,
            timeout_s=timeout_s,
            python=python,
        )
        for item in selected
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--ticket", choices=[item.id for item in TICKETS])
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--agent-argv", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    agent = args.agent_argv[1:] if args.agent_argv[:1] == ["--"] else args.agent_argv
    return (
        0
        if run_tickets(
            args.source_root,
            agent,
            args.log,
            timeout_s=args.timeout,
            python=args.python,
            ticket_id=args.ticket,
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())

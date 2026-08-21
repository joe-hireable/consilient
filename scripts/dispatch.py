"""Dispatch a task to a subscription harness. This is the command you type.

Policy (registry, selection, recording) lives in `consilient.harness`. This script
probes, runs, and verifies by artefact. It is not a `consil` subcommand — the CLI
surface stays {record, replay, beta, doctor} until the principal settles it.

    python scripts/dispatch.py --probe
    python scripts/dispatch.py "reply with the single word pong"
    python scripts/dispatch.py "reply with the single word pong" --fan-out
    python scripts/dispatch.py --task-file brief.md --cwd C:/path/to/repo

Never silently spends the exhausted pool. A harness that exits 0 having done nothing
is recorded `silent` and is not retried on another pool.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.harness import (  # noqa: E402
    DEFAULT_PERMISSION_MODE,
    DEFAULT_POOLS,
    HARNESSES,
    Decision,
    FanoutDecision,
    Harness,
    PermissionMode,
    PoolState,
    Probe,
    classify_artefact,
    cursor_pool_for_model,
    describe_registry,
    harness_by_id,
    judge_fanout,
    load_permission_mode,
    load_pools,
    make_run_id,
    now_ts,
    parse_status,
    permission_flags,
    record_fanout,
    record_outcome,
    record_refusal,
    select,
    select_fanout,
    snapshot_mapping,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_LOG = ROOT / ".harness" / "log"
DEFAULT_HEADROOM = ROOT / ".harness" / "headroom.json"
DEFAULT_RUNS = ROOT / ".harness" / "dispatch"
DEFAULT_PERMISSIONS = ROOT / ".harness" / "permissions.json"
CURSOR_WSL_BINARY = Path("/home/jpbpr/.local/bin/cursor-agent")
GROK_CANDIDATES = (
    Path.home() / ".grok" / "bin" / "grok.exe",
    Path.home() / ".grok" / "bin" / "grok",
    Path("/mnt/c/Users/jpbpr/.grok/bin/grok.exe"),
)
METERED_KEY_ENV_VARS = ("XAI_API_KEY", "GROK_CODE_XAI_API_KEY", "GROK_API_KEY")
DEFAULT_TIMEOUT_S = 600
DEFAULT_CURSOR_MODEL = "composer-2.5"
GIT_ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


@dataclass(frozen=True)
class RunResult:
    harness: Harness
    status: str
    reason: str
    exit_code: int | None
    stdout: str
    stderr: str
    artefact_bytes: int
    diff_bytes: int
    timed_out: bool
    duration_s: float
    command: tuple[str, ...]
    run_id: str
    stdout_path: str
    stderr_path: str


def to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved).replace("\\", "/")
    if len(text) > 1 and text[1] == ":":
        return f"/mnt/{text[0].lower()}{text[2:]}"
    return text


def which_binary(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        for suffix in (".exe", ".cmd", ".bat"):
            found = shutil.which(name + suffix)
            if found:
                return found
    return None


def find_grok() -> str | None:
    for name in ("grok", "grok.exe", "grok.cmd"):
        found = which_binary(name)
        if found:
            return found
    for candidate in GROK_CANDIDATES:
        if candidate.exists():
            return str(candidate.resolve())
    return None


def find_claude() -> str | None:
    return which_binary("claude")


def find_codex() -> str | None:
    return which_binary("codex")


def wsl_bridge() -> str | None:
    return which_binary("wsl")


def cursor_native() -> str | None:
    if CURSOR_WSL_BINARY.exists():
        return str(CURSOR_WSL_BINARY)
    return which_binary("cursor-agent")


def _run_probe(argv: list[str], timeout_s: int = 20) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        return -1, "", f"not found: {exc}"
    except subprocess.TimeoutExpired:
        return -1, "", f"probe timed out after {timeout_s}s"
    except OSError as exc:
        return -1, "", f"{type(exc).__name__}: {exc}"
    return (
        completed.returncode,
        (completed.stdout or "").strip(),
        (completed.stderr or "").strip(),
    )


def _version_from(text: str) -> str | None:
    for token in text.replace("(", " ").replace(")", " ").split():
        parts = token.split(".")
        if len(parts) >= 2 and all(part.isdigit() for part in parts[:2]):
            return token
    return None


def probe_claude() -> Probe:
    binary = find_claude()
    if binary is None:
        return Probe("claude", False, None, "claude is not on PATH")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("claude", False, None, err or out or f"exit {code}")
    return Probe("claude", True, version, binary)


def probe_codex() -> Probe:
    binary = find_codex()
    if binary is None:
        return Probe("codex", False, None, "codex is not on PATH")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("codex", False, None, err or out or f"exit {code}")
    return Probe("codex", True, version, binary)


def probe_grok() -> Probe:
    binary = find_grok()
    if binary is None:
        return Probe("grok", False, None, "grok is not on PATH or in ~/.grok/bin")
    code, out, err = _run_probe([binary, "--version"])
    version = _version_from(out) if code == 0 else None
    if version is None:
        return Probe("grok", False, None, err or out or f"exit {code}")
    return Probe("grok", True, version, binary)


def _cursor_help_and_about() -> tuple[bool, str | None, str]:
    native = cursor_native()
    if native is not None:
        code, out, err = _run_probe([native, "--version"])
        version = _version_from(out) or _version_from(err)
        if code == 0 and (out or version):
            return True, version or out.splitlines()[0], native
        code, out, err = _run_probe([native, "about", "--format", "json"])
        if code == 0 and out:
            try:
                payload = json.loads(out)
            except json.JSONDecodeError:
                payload = {}
            version = payload.get("cliVersion") if isinstance(payload, dict) else None
            if isinstance(version, str) and version.strip():
                return True, version, native
        return False, None, err or out or native

    bridge = wsl_bridge()
    if bridge is None or os.name != "nt":
        return False, None, (
            f"cursor-agent is WSL-only; looked for {CURSOR_WSL_BINARY} and no wsl bridge"
        )
    inner = "cursor-agent --version || cursor-agent about --format json"
    code, out, err = _run_probe([bridge, "-e", "bash", "-lc", inner])
    version = _version_from(out)
    if version is None and out:
        try:
            payload = json.loads(out)
            if isinstance(payload, dict) and isinstance(payload.get("cliVersion"), str):
                version = payload["cliVersion"]
        except json.JSONDecodeError:
            version = None
    if code == 0 and (version or out):
        return True, version or "installed", f"{bridge} + cursor-agent"
    return False, None, err or out or "wsl cursor-agent probe failed"


def probe_cursor() -> Probe:
    ok, version, detail = _cursor_help_and_about()
    return Probe("cursor-composer", ok, version, detail)


def probe_all() -> tuple[Probe, ...]:
    return (probe_claude(), probe_cursor(), probe_grok(), probe_codex())


def help_text(argv_head: list[str]) -> str:
    code, out, err = _run_probe([*argv_head, "--help"], timeout_s=15)
    if code != 0 and not out:
        return err
    return out


def optional_flags(help_blob: str, *flags: str) -> list[str]:
    chosen: list[str] = []
    blob = f" {help_blob} "
    for flag in flags:
        if f" {flag} " in blob or f" {flag}\n" in help_blob or help_blob.endswith(flag):
            chosen.append(flag)
    return chosen


def metered_grok_reason(env: dict[str, str] | None = None) -> str | None:
    source = os.environ if env is None else env
    for name in METERED_KEY_ENV_VARS:
        if source.get(name):
            return (
                f"refusing grok: metered key {name} is set; SuperGrok Heavy is the "
                "subscription path and OpenRouter is the only permitted metered vendor"
            )
    return None


def kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except (ProcessLookupError, PermissionError, OSError):
            pass


def run_process(
    argv: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_s: int,
    env: dict[str, str] | None = None,
) -> tuple[int | None, bool, float]:
    """Run argv, writing output to files (not pipes), and kill the process tree on timeout."""
    cwd = cwd.resolve()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    started = time.perf_counter()
    timed_out = False
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            process = subprocess.Popen(
                argv,
                cwd=str(cwd),
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                env=env,
                **kwargs,
            )
        except OSError:
            return None, False, time.perf_counter() - started
        try:
            process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_process_tree(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
    return process.returncode, timed_out, time.perf_counter() - started


def git_diff_bytes(cwd: Path) -> int:
    git = which_binary("git")
    if git is None:
        return 0
    try:
        completed = subprocess.run(
            [git, "-C", str(cwd.resolve()), "diff", "--stat"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    return len((completed.stdout or "").encode("utf-8"))


def write_brief(run_dir: Path, task: str) -> Path:
    path = (run_dir / "brief.md").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(task, encoding="utf-8", newline="\n")
    return path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def build_command(
    harness: Harness,
    *,
    task: str,
    cwd: Path,
    brief: Path,
    model: str | None,
    permissions: PermissionMode = DEFAULT_PERMISSION_MODE,
) -> list[str] | str:
    """Return argv, or a refusal reason string."""
    cwd = cwd.resolve()
    brief = brief.resolve()
    bypass = list(permission_flags(harness.id, permissions))
    if harness.id == "claude":
        binary = find_claude()
        if binary is None:
            return "claude is not on PATH"
        return [binary, *bypass, "-p", task]
    if harness.id == "grok":
        metered = metered_grok_reason()
        if metered is not None:
            return metered
        binary = find_grok()
        if binary is None:
            return "grok is not on PATH or in ~/.grok/bin"
        extra = optional_flags(help_text([binary]), "--always-approve")
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        return [binary, "-p", task, "--cwd", str(cwd), *extra]
    if harness.id == "codex":
        binary = find_codex()
        if binary is None:
            return "codex is not on PATH"
        extra = optional_flags(help_text([binary, "exec"]), "--skip-git-repo-check")
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        # Insert extra flags before the prompt so they are not eaten as the task.
        return [binary, "exec", "-C", str(cwd), *extra, task]
    if harness.id == "cursor-composer":
        chosen = model or DEFAULT_CURSOR_MODEL
        if cursor_pool_for_model(chosen) == "cursor-other":
            return (
                f"refusing cursor model {chosen!r}: it draws on the Cursor Other Models "
                "pool (claude-*/gpt-*/gemini-*), which the operator asked to avoid"
            )
        native = cursor_native()
        instruction = (
            f"Read the file {brief.as_posix()} and do exactly that task. "
            "Do not wait for confirmation."
        )
        extra: list[str] = []
        if native is not None:
            extra = optional_flags(help_text([native]), "--force", "--trust")
            for flag in bypass:
                if flag not in extra:
                    extra.append(flag)
            return [
                native,
                "-p",
                "--model",
                chosen,
                "--output-format",
                "text",
                *extra,
                instruction,
            ]
        bridge = wsl_bridge()
        if bridge is None:
            return "cursor-agent is not reachable (no native binary and no wsl)"
        wsl_cwd = to_wsl_path(cwd)
        wsl_brief = to_wsl_path(brief)
        wsl_instruction = (
            f"Read the file {wsl_brief} and do exactly that task. "
            "Do not wait for confirmation."
        )
        extra = optional_flags(
            help_text([bridge, "-e", "bash", "-lc", "cursor-agent --help"]),
            "--force",
            "--trust",
        )
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        extra_s = (" " + " ".join(extra)) if extra else ""
        # The task body never enters the shell: only paths we created do.
        inner = (
            f"cd {shlex.quote(wsl_cwd)} && cursor-agent -p --model {shlex.quote(chosen)} "
            f"--output-format text{extra_s} {shlex.quote(wsl_instruction)}"
        )
        return [bridge, "-e", "bash", "-lc", inner]
    return f"no invocation for harness {harness.id}"


def run_harness(
    harness: Harness,
    *,
    task: str,
    cwd: Path,
    run_dir: Path,
    timeout_s: int,
    model: str | None,
    run_id: str,
    permissions: PermissionMode = DEFAULT_PERMISSION_MODE,
) -> RunResult:
    cwd = cwd.resolve()
    run_dir = run_dir.resolve()
    brief = write_brief(run_dir, task)
    stdout_path = (run_dir / "stdout.txt").resolve()
    stderr_path = (run_dir / "stderr.txt").resolve()
    built = build_command(
        harness,
        task=task,
        cwd=cwd,
        brief=brief,
        model=model,
        permissions=permissions,
    )
    if isinstance(built, str):
        return RunResult(
            harness=harness,
            status="refused",
            reason=built,
            exit_code=None,
            stdout="",
            stderr="",
            artefact_bytes=0,
            diff_bytes=0,
            timed_out=False,
            duration_s=0.0,
            command=(),
            run_id=run_id,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )
    argv = built
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    code, timed_out, duration = run_process(
        argv,
        cwd=cwd,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=timeout_s,
        env=env,
    )
    stdout = _read(stdout_path)
    stderr = _read(stderr_path)
    artefact_bytes = len(stdout.encode("utf-8")) + len(stderr.encode("utf-8"))
    diff_bytes = git_diff_bytes(cwd)
    status, reason = classify_artefact(
        exit_code=code,
        stdout=stdout,
        stderr=stderr,
        output_bytes=artefact_bytes,
        diff_bytes=diff_bytes,
        timed_out=timed_out,
    )
    return RunResult(
        harness=harness,
        status=status,
        reason=reason,
        exit_code=code,
        stdout=stdout,
        stderr=stderr,
        artefact_bytes=artefact_bytes,
        diff_bytes=diff_bytes,
        timed_out=timed_out,
        duration_s=round(duration, 2),
        command=tuple(argv),
        run_id=run_id,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )


def _result_payload(result: RunResult) -> dict[str, object]:
    return {
        "harness": result.harness.id,
        "family": result.harness.family,
        "pool": result.harness.pool,
        "status": result.status,
        "reason": result.reason,
        "exit_code": result.exit_code,
        "artefact_bytes": result.artefact_bytes,
        "diff_bytes": result.diff_bytes,
        "timed_out": result.timed_out,
        "duration_s": result.duration_s,
        "command": list(result.command),
        "run_id": result.run_id,
        "stdout_path": result.stdout_path,
        "stderr_path": result.stderr_path,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-1000:],
    }


def _print_human(payload: dict[str, object]) -> None:
    status = str(payload.get("status", ""))
    print(f"status: {status}")
    if "reason" in payload:
        print(f"reason: {payload['reason']}")
    if "harness" in payload:
        print(f"harness: {payload['harness']} ({payload.get('family')}, {payload.get('pool')})")
    if "selected" in payload:
        print(f"selected: {payload['selected']}")
    if "first" in payload and isinstance(payload["first"], dict):
        first = payload["first"]
        second = payload.get("second")
        print(
            f"first: {first.get('harness')} {first.get('status')} "
            f"({first.get('artefact_bytes')} bytes)"
        )
        if isinstance(second, dict):
            print(
                f"second: {second.get('harness')} {second.get('status')} "
                f"({second.get('artefact_bytes')} bytes)"
            )
        print(f"verdict: {payload.get('verdict')}")
        for label in ("first", "second"):
            row = payload.get(label)
            if isinstance(row, dict):
                tail = row.get("stdout_tail")
                if isinstance(tail, str) and tail.strip():
                    print(f"--- {row.get('harness')} ---")
                    print(tail.strip())
    if "artefact_bytes" in payload:
        print(f"artefact: {payload['artefact_bytes']} bytes")
    command = payload.get("command")
    if isinstance(command, list) and command:
        print("command: " + shlex.join(str(part) for part in command))
    if "recorded" in payload:
        print(f"recorded: {payload['recorded']}")
    stdout_tail = payload.get("stdout_tail")
    if isinstance(stdout_tail, str) and stdout_tail.strip():
        print("--- stdout ---")
        print(stdout_tail.strip())
    rows = payload.get("harnesses")
    if isinstance(rows, list):
        print(f"{'id':<18} {'family':<10} {'pool':<16} {'installed':<10} {'used':<8} note")
        for row in rows:
            if not isinstance(row, dict):
                continue
            used = row.get("used_percent")
            used_s = "unknown" if used is None else f"{used:g}%"
            installed = "yes" if row.get("installed") else "no"
            print(
                f"{str(row.get('id')):<18} {str(row.get('family')):<10} "
                f"{str(row.get('pool')):<16} {installed:<10} {used_s:<8} "
                f"{row.get('note') or ''}"
            )
            print(f"  probe: {row.get('probe')}")


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    _print_human(payload)


def ensure_default_headroom(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot_mapping(DEFAULT_POOLS), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def resolve_cwd(value: str | None) -> Path:
    path = Path(value) if value else Path.cwd()
    return path.resolve()


def load_task(positional: str | None, task_file: str | None) -> str:
    if positional and task_file:
        raise ValueError("pass a task string or --task-file, not both")
    if task_file:
        path = Path(task_file).resolve()
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError(f"task file {path} is empty")
        return text
    if positional and positional.strip():
        return positional
    raise ValueError("a task is required (positional or --task-file)")


def _exit_for(status: str) -> int:
    if status in {"ok", "agree", "disagree", "incomparable"}:
        return 0
    if status == "refused":
        return 2
    if status == "silent":
        return 3
    if status == "timeout":
        return 4
    return 1


def dispatch_one(
    *,
    decision: Decision,
    task: str,
    cwd: Path,
    log_dir: Path,
    runs_dir: Path,
    timeout_s: int,
    model: str | None,
    dry_run: bool,
    permissions: PermissionMode = DEFAULT_PERMISSION_MODE,
) -> tuple[dict[str, object], int]:
    ts = now_ts()
    run_id = make_run_id(ts, task, "dispatch")
    log_dir.mkdir(parents=True, exist_ok=True)
    if decision.kind == "refuse" or decision.harness is None:
        recorded = record_refusal(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=str(cwd),
            reason=decision.reason,
            considered=decision.considered,
        )
        payload = {
            "status": "refused",
            "reason": decision.reason,
            "considered": list(decision.considered),
            "run_id": run_id,
            "cwd": str(cwd),
            "recorded": str(log_dir / f"{ts[:10]}.jsonl"),
            "event": recorded["event"],
        }
        return payload, _exit_for("refused")

    harness = decision.harness
    if dry_run:
        brief = write_brief((runs_dir / run_id).resolve(), task)
        built = build_command(
            harness,
            task=task,
            cwd=cwd,
            brief=brief,
            model=model,
            permissions=permissions,
        )
        command = built if isinstance(built, list) else []
        reason = built if isinstance(built, str) else decision.reason
        payload = {
            "status": "dry-run",
            "selected": decision.reason,
            "harness": harness.id,
            "family": harness.family,
            "pool": harness.pool,
            "reason": reason,
            "command": command,
            "cwd": str(cwd),
            "run_id": run_id,
        }
        return payload, 0 if isinstance(built, list) else _exit_for("refused")

    run_dir = (runs_dir / run_id).resolve()
    result = run_harness(
        harness,
        task=task,
        cwd=cwd,
        run_dir=run_dir,
        timeout_s=timeout_s,
        model=model,
        run_id=run_id,
        permissions=permissions,
    )
    recorded = record_outcome(
        log_dir,
        ts=now_ts(),
        run_id=result.run_id,
        task=task,
        cwd=str(cwd),
        harness=harness,
        status=parse_status(result.status),
        reason=result.reason,
        exit_code=result.exit_code,
        artefact_bytes=result.artefact_bytes,
        diff_bytes=result.diff_bytes,
        timed_out=result.timed_out,
        duration_s=result.duration_s,
        command=result.command,
    )
    payload = {
        "status": result.status,
        "selected": decision.reason,
        "cwd": str(cwd),
        "recorded": str(log_dir / f"{recorded['ts'][:10]}.jsonl"),
        **_result_payload(result),
    }
    # Deliberate: a silent or failed run is NOT retried on another pool. That would
    # be the silent fallback this command exists to prevent.
    return payload, _exit_for(result.status)


def dispatch_fanout(
    *,
    decision: FanoutDecision,
    task: str,
    cwd: Path,
    log_dir: Path,
    runs_dir: Path,
    timeout_s: int,
    model: str | None,
    dry_run: bool,
    permissions: PermissionMode = DEFAULT_PERMISSION_MODE,
) -> tuple[dict[str, object], int]:
    ts = now_ts()
    run_id = make_run_id(ts, task, "fanout")
    log_dir.mkdir(parents=True, exist_ok=True)
    if decision.kind == "refuse" or decision.first is None or decision.second is None:
        recorded = record_refusal(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=str(cwd),
            reason=decision.reason,
            considered=decision.considered,
        )
        payload = {
            "status": "refused",
            "reason": decision.reason,
            "considered": list(decision.considered),
            "run_id": run_id,
            "cwd": str(cwd),
            "recorded": str(log_dir / f"{ts[:10]}.jsonl"),
            "event": recorded["event"],
        }
        return payload, _exit_for("refused")

    if dry_run:
        payload = {
            "status": "dry-run",
            "selected": decision.reason,
            "first": decision.first.id,
            "second": decision.second.id,
            "cwd": str(cwd),
            "run_id": run_id,
        }
        return payload, 0

    results: list[RunResult] = []
    for harness in (decision.first, decision.second):
        child_id = make_run_id(now_ts(), task, harness.id)
        result = run_harness(
            harness,
            task=task,
            cwd=cwd,
            run_dir=(runs_dir / child_id).resolve(),
            timeout_s=timeout_s,
            model=model if harness.id == "cursor-composer" else None,
            run_id=child_id,
            permissions=permissions,
        )
        record_outcome(
            log_dir,
            ts=now_ts(),
            run_id=result.run_id,
            task=task,
            cwd=str(cwd),
            harness=harness,
            status=parse_status(result.status),
            reason=result.reason,
            exit_code=result.exit_code,
            artefact_bytes=result.artefact_bytes,
            diff_bytes=result.diff_bytes,
            timed_out=result.timed_out,
            duration_s=result.duration_s,
            command=result.command,
        )
        results.append(result)

    first, second = results
    verdict = judge_fanout(
        first.stdout,
        second.stdout,
        first.status == "ok",
        second.status == "ok",
    )
    recorded = record_fanout(
        log_dir,
        ts=now_ts(),
        run_id=run_id,
        task=task,
        cwd=str(cwd),
        first=decision.first,
        second=decision.second,
        first_status=parse_status(first.status),
        second_status=parse_status(second.status),
        verdict=verdict,
        first_run_id=first.run_id,
        second_run_id=second.run_id,
    )
    payload = {
        "status": verdict,
        "verdict": verdict,
        "selected": decision.reason,
        "cwd": str(cwd),
        "run_id": run_id,
        "recorded": str(log_dir / f"{recorded['ts'][:10]}.jsonl"),
        "first": _result_payload(first),
        "second": _result_payload(second),
    }
    worst = first.status if first.status != "ok" else second.status
    if first.status == "ok" and second.status == "ok":
        return payload, 0
    return payload, _exit_for(worst)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatch a task to a subscription harness. Not a consil subcommand."
    )
    parser.add_argument("task", nargs="?", help="the task to run")
    parser.add_argument("--task-file", help="read the task from this file (preferred for long briefs)")
    parser.add_argument("--cwd", help="working directory (resolved to an absolute path)")
    parser.add_argument(
        "--harness",
        help="run this harness; still refuses an exhausted pool without --allow-exhausted",
    )
    parser.add_argument(
        "--fan-out",
        action="store_true",
        help="run the same task on two harnesses from different model families",
    )
    parser.add_argument(
        "--allow-exhausted",
        action="store_true",
        help="spend an exhausted pool; default is to refuse",
    )
    parser.add_argument("--model", help="model id (cursor-composer defaults to composer-2.5)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--headroom", default=str(DEFAULT_HEADROOM))
    parser.add_argument("--runs", default=str(DEFAULT_RUNS))
    parser.add_argument("--probe", action="store_true", help="probe installed harnesses and exit")
    parser.add_argument("--dry-run", action="store_true", help="select (and print argv) without running")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--permissions",
        choices=("bypass", "prompt"),
        default=None,
        help="bypass (default) runs children without per-tool prompts; prompt leaves their ask-loop on. "
        "Overrides .harness/permissions.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cwd = resolve_cwd(args.cwd)
    log_dir = Path(args.log).resolve()
    runs_dir = Path(args.runs).resolve()
    headroom_path = Path(args.headroom).resolve()
    ensure_default_headroom(headroom_path)
    permissions: PermissionMode = (
        args.permissions
        if args.permissions is not None
        else load_permission_mode(DEFAULT_PERMISSIONS)
    )

    try:
        pools: tuple[PoolState, ...] = load_pools(headroom_path)
    except ValueError as exc:
        emit({"status": "refused", "reason": str(exc)}, args.json)
        return 2

    probes = probe_all()
    if args.probe:
        payload = {
            "status": "probed",
            "cwd": str(cwd),
            "headroom": str(headroom_path),
            "headroom_source": pools[0].source if pools else "",
            "harnesses": describe_registry(probes=probes, pools=pools, harnesses=HARNESSES),
        }
        emit(payload, args.json)
        return 0

    try:
        task = load_task(args.task, args.task_file)
    except ValueError as exc:
        emit({"status": "refused", "reason": str(exc)}, args.json)
        return 2

    if args.fan_out and args.harness:
        emit(
            {
                "status": "refused",
                "reason": "--fan-out picks two families itself; do not pass --harness",
            },
            args.json,
        )
        return 2

    if args.harness and harness_by_id(args.harness) is None:
        emit(
            {
                "status": "refused",
                "reason": (
                    f"unknown harness {args.harness!r}; known: "
                    + ", ".join(item.id for item in HARNESSES)
                ),
            },
            args.json,
        )
        return 2

    if args.fan_out:
        decision = select_fanout(
            probes=probes,
            pools=pools,
            allow_exhausted=args.allow_exhausted,
        )
        payload, code = dispatch_fanout(
            decision=decision,
            task=task,
            cwd=cwd,
            log_dir=log_dir,
            runs_dir=runs_dir,
            timeout_s=args.timeout,
            model=args.model,
            dry_run=args.dry_run,
            permissions=permissions,
        )
        emit(payload, args.json)
        return code

    decision = select(
        probes=probes,
        pools=pools,
        requested=args.harness,
        allow_exhausted=args.allow_exhausted,
    )
    payload, code = dispatch_one(
        decision=decision,
        task=task,
        cwd=cwd,
        log_dir=log_dir,
        runs_dir=runs_dir,
        timeout_s=args.timeout,
        model=args.model,
        dry_run=args.dry_run,
        permissions=permissions,
    )
    emit(payload, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

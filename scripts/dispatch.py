"""Dispatch a task to a subscription harness. This is the command you type.

Policy (registry, selection, recording) lives in `consilient.harness`. This script
probes, runs, and verifies by artefact. It is not a `consil` subcommand — the CLI
surface stays {record, replay, beta, doctor} until the principal settles it.

    python scripts/dispatch.py --probe
    python scripts/dispatch.py "reply with the single word pong"
    python scripts/dispatch.py "reply with the single word pong" --fan-out
    python scripts/dispatch.py --task-file brief.md --cwd <this repository, or a subdirectory>

`--cwd` accepts this repository (root, a git worktree of it, or a directory inside one
of those) and, additionally, any directory named in the instance file
`.harness/allowed-cwds.json` (ADR-0063). Any other path is refused, including on
`--dry-run`. There is no override flag: Gate B, which governs *depending* on this
harness for work on another repository, is not passed. Listing a root is supervised
dispatch, not a gate pass.

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
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import coordination  # noqa: E402
from consilient.error_tracking import (  # noqa: E402
    ErrorRecordError,
    append_record,
    build_record,
)
from consilient.events import EventError, read_all  # noqa: E402
from consilient.harness import (  # noqa: E402
    DEFAULT_PERMISSION_MODE,
    DEFAULT_POOLS,
    HARNESSES,
    MODELS,
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
    headroom_freshness_refusal,
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
    select_model,
    snapshot_mapping,
)
from consilient.recall import pack as pack_recall  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_LOG = ROOT / ".harness" / "log"
DEFAULT_HEADROOM = ROOT / ".harness" / "headroom.json"
DEFAULT_RUNS = ROOT / ".harness" / "dispatch"
DEFAULT_PERMISSIONS = ROOT / ".harness" / "permissions.json"
DEFAULT_ALLOWED_CWDS = ROOT / ".harness" / "allowed-cwds.json"
DEFAULT_CURSOR_LOCK = ROOT / ".harness" / "cursor-agent.lock"
CURSOR_WSL_BINARY = Path("/home/jpbpr/.local/bin/cursor-agent")
GROK_CANDIDATES = (
    Path.home() / ".grok" / "bin" / "grok.exe",
    Path.home() / ".grok" / "bin" / "grok",
    Path("/mnt/c/Users/jpbpr/.grok/bin/grok.exe"),
)
METERED_KEY_ENV_VARS = ("XAI_API_KEY", "GROK_CODE_XAI_API_KEY", "GROK_API_KEY")
DEFAULT_TIMEOUT_S = 600
DEFAULT_MAX_TURNS = 20
DEFAULT_MAX_TOKENS = 100_000
DEFAULT_CURSOR_MODEL = "composer-2.5"
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}


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


def record_dispatch_error(log_dir: Path, result: RunResult) -> None:
    """Record a non-OK identity without raw task, command, or exception text."""
    if result.status == "ok":
        return
    try:
        append_record(
            log_dir / "errors" / "errors.jsonl",
            build_record(
                component=f"dispatch.{result.harness.id}",
                error_type="DispatchOutcome",
                error_code=result.status,
                observed_at=now_ts(),
                no_check_yet=True,
            ),
        )
    except (ErrorRecordError, OSError) as exc:
        print(f"error tracking failed after outcome recording: {exc}", file=sys.stderr)


def to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved).replace("\\", "/")
    if len(text) > 1 and text[1] == ":":
        return f"/mnt/{text[0].lower()}{text[2:]}"
    return text


class ExclusiveFileLock:
    """Process-exclusive lock. Two cursor-agent processes race ~/.cursor/cli-config.json
    [measured]; this is the check that forbids that overlap. Dry-run must not enter it.
    """

    def __init__(self, path: Path, *, timeout_s: float) -> None:
        self.path = path
        self.timeout_s = timeout_s
        self._fh: Any = None

    def __enter__(self) -> ExclusiveFileLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+b")
        self._fh = handle
        deadline = time.monotonic() + max(0.0, self.timeout_s)
        while True:
            try:
                self._lock_nonblocking()
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    handle.close()
                    self._fh = None
                    raise TimeoutError(
                        f"cursor-agent lock held: could not acquire {self.path} "
                        f"within {self.timeout_s}s"
                    ) from None
                time.sleep(0.05)

    def _lock_nonblocking(self) -> None:
        handle = self._fh
        if handle is None:
            raise OSError("lock file is not open")
        handle.seek(0)
        if handle.read(1) == b"":
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, *_exc: object) -> None:
        handle = self._fh
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            self._fh = None


def git_workspace(cwd: Path) -> tuple[Path, Path] | None:
    """Return (absolute git dir, work tree) for cwd, or None if git cannot answer.

    A linked worktree's `.git` is a file containing a Windows path. WSL git cannot
    resolve that path (R4, measured again 21 August 2026 on a jobboard worktree).
    Dispatch owns the translation; the child is not asked to.
    """
    git = which_binary("git")
    if git is None:
        return None
    try:
        completed = subprocess.run(
            [
                git,
                "-C",
                str(cwd.resolve()),
                "rev-parse",
                "--absolute-git-dir",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    lines = [
        line.strip() for line in (completed.stdout or "").splitlines() if line.strip()
    ]
    if len(lines) < 2:
        return None
    git_dir = Path(lines[0])
    work_tree = Path(lines[1])
    try:
        git_dir = git_dir.resolve()
        work_tree = work_tree.resolve()
    except OSError:
        return None
    if not git_dir.exists() or not work_tree.is_dir():
        return None
    return git_dir, work_tree


def wsl_git_exports(cwd: Path) -> str:
    workspace = git_workspace(cwd)
    if workspace is None:
        return ""
    git_dir, work_tree = workspace
    return (
        f"export GIT_DIR={shlex.quote(to_wsl_path(git_dir))} "
        f"GIT_WORK_TREE={shlex.quote(to_wsl_path(work_tree))}; "
    )


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
        return (
            False,
            None,
            (
                f"cursor-agent is WSL-only; looked for {CURSOR_WSL_BINARY} and no wsl bridge"
            ),
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


def native_cap_flags(
    harness_id: str,
    help_blob: str,
    *,
    max_turns: int,
    max_tokens: int,
) -> list[str] | str:
    """Return whatever native hard-cap flags the installed CLI actually exposes.

    R11's attribution was withdrawn on 21 August 2026. The retained engineering
    obligation is that **no arm runs unbounded** -- not that a particular flag spelling
    exists.

    Until 21 August 2026 this demanded `--max-turns` AND `--max-tokens` natively and refused
    the launch otherwise. Measured against the installed CLIs that day: grok exposes
    `--max-turns` only; codex exposes neither. So the condition could never pass for two of
    the three subscription harnesses, and the harness had locked itself out of two of the
    plans it exists to spend. That is the wall-not-gate defect catalogued in
    `docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`: a condition
    that cannot pass teaches people to bypass it, and it contradicted the principal's other
    standing instruction to use every subscription.

    So: apply every native cap the CLI does offer, and let the caller bound the rest. The
    caller already enforces a wall-clock timeout and kills the process tree, which is what
    actually makes an arm bounded on a CLI with no native flag.

    **What this does NOT achieve, stated rather than implied:** no installed CLI exposes a
    real per-run token cap, so token bounding is only available through the pool ceiling in
    `budget.py`, not per arm. A wall-clock bound is also strictly weaker than a turn cap --
    an arm can burn many turns quickly inside its window. Both gaps are real and neither is
    closed here.
    """
    if max_turns <= 0 or max_tokens <= 0:
        return (
            f"refusing {harness_id}: hard turn and token caps must be positive integers"
        )
    present = set(optional_flags(help_blob, "--max-turns", "--max-tokens"))
    flags: list[str] = []
    if "--max-turns" in present:
        flags += ["--max-turns", str(max_turns)]
    if "--max-tokens" in present:
        flags += ["--max-tokens", str(max_tokens)]
    return flags


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


def refresh_default_headroom(path: Path) -> str | None:
    """Refresh the default snapshot through the bounded, non-inference probe."""
    if path != DEFAULT_HEADROOM.resolve():
        return None
    if path.exists():
        try:
            current = load_pools(path)
        except ValueError:
            pass
        else:
            if headroom_freshness_refusal(
                current, now=datetime.now(timezone.utc)
            ) is None:
                return None
    with tempfile.TemporaryDirectory(prefix="consilient-headroom-") as directory:
        temporary = Path(directory)
        code, timed_out, _duration = run_process(
            [
                sys.executable,
                str(ROOT / "scripts" / "headroom.py"),
                "--output",
                str(path),
                "--timeout",
                "5",
            ],
            cwd=ROOT,
            stdout_path=temporary / "stdout.txt",
            stderr_path=temporary / "stderr.txt",
            timeout_s=45,
        )
    if timed_out:
        return "headroom refresh timed out; process tree killed"
    if code != 0:
        return f"headroom refresh failed (exit {code})"
    return None


def _harvest_quietly(log_dir: Path, runs_dir: Path) -> None:
    """Paid dispatch is harvested. Failure here must not change the dispatch status.

    Only the operator log is harvested, never a test tmp directory.
    """
    live = (ROOT / ".harness" / "log").resolve()
    try:
        if log_dir.resolve() != live:
            return
        from consilient.harvest import DEFAULT_RELATIVE, HarvestError, harvest

        harvest(
            log_dir=log_dir,
            runs_dir=runs_dir,
            dest=ROOT / DEFAULT_RELATIVE,
            root=ROOT,
        )
    except (HarvestError, OSError, ValueError) as exc:
        print(f"harvest skipped: {exc}", file=sys.stderr)


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


RECALL_LIMIT_CHARS = 8000


def write_brief(
    run_dir: Path,
    task: str,
    *,
    log_dir: Path | None = None,
    in_flight: str = "",
    claim_run_id: str | None = None,
) -> Path:
    """Write the task, plus a verbatim recall pack so the child is not amnesiac.

    Cross-harness memory is the trajectory. Until 21 August 2026 this function
    wrote the task alone, so Cursor could not see what Codex had just done.

    The pack is written to `recall.md` beside the brief and referenced from the
    brief, and also embedded — the embed is what a child that reads only its brief
    still sees. Both are bounded at RECALL_LIMIT_CHARS; the bound is the point,
    because an unbounded coordination section crowds the task out of the context
    window. `in_flight` is the live-claims table rendered by the caller.

    `claim_run_id` is the run id the claim covering this work was opened under
    (the parent's, for a fan-out child). The pre-commit gate refuses a commit
    that does not name its committer while claims are live, so the brief hands
    the run its badge; the gate, not this paragraph, is the enforcement.
    """
    path = (run_dir / "brief.md").resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = task if task.endswith("\n") else task + "\n"
    if claim_run_id is not None:
        body += (
            "\n---\n\n## Your commit badge\n\n"
            "This run's work is claimed in the trajectory under run id "
            f"`{claim_run_id}`. While any dispatch claim is live in this "
            "worktree, the pre-commit gate refuses a commit that does not name "
            "its committer, and a commit staging a path another live run claims "
            "is refused. Commit with:\n\n"
            f"    CONSILIENT_RUN_ID={claim_run_id} git commit ...\n\n"
            "If this dispatch declared no --claim paths, the gate also needs the "
            "paths you are committing: CONSILIENT_COMMIT_PATHS=path/one,path/two. "
            "Stage only paths you created or this brief named; never "
            "`git add -A`.\n"
        )
    if log_dir is not None:
        try:
            recall = pack_recall(
                Path(log_dir), query=task[:240], limit_chars=RECALL_LIMIT_CHARS
            )
        except (OSError, ValueError):
            recall = ""
        if recall.strip() and "No events in log" not in recall:
            recall_path = (run_dir / "recall.md").resolve()
            recall_path.write_text(recall, encoding="utf-8", newline="\n")
            body += (
                "\n---\n\n## Context from the trajectory\n\n"
                "A verbatim recall pack is recorded at `recall.md` beside this brief "
                f"(bound: {RECALL_LIMIT_CHARS} characters) and embedded below.\n\n"
            )
            if in_flight.strip():
                body += in_flight.strip() + "\n\n"
            body += "---\n\n" + recall
            if not body.endswith("\n"):
                body += "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
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
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[str] | str:
    """Return argv, or a refusal reason string."""
    cwd = cwd.resolve()
    if model is not None:
        selected = select_model(harness.id, pools=pools, requested=model)
        if isinstance(selected, str):
            return selected
        attended_cursor_other = (
            harness.id == "cursor-composer"
            and cursor_pool_for_model(model) == "cursor-other"
        )
        if (
            selected.reasoning_capability == "unknown"
            and selected not in MODELS
            and not attended_cursor_other
        ):
            return (
                f"refusing {harness.id} model {model!r}: reasoning capability is "
                f"unknown ({selected.reasoning_provenance})"
            )
    brief = brief.resolve()
    bypass = list(permission_flags(harness.id, permissions))
    instruction = (
        f"Read the file {brief.as_posix()} and do exactly that task. "
        "Do not wait for confirmation."
    )
    if harness.id == "claude":
        binary = find_claude()
        if binary is None:
            return "claude is not on PATH"
        caps = native_cap_flags(
            harness.id,
            help_text([binary]),
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        return [binary, *bypass, *caps, "-p", instruction]
    if harness.id == "grok":
        metered = metered_grok_reason()
        if metered is not None:
            return metered
        binary = find_grok()
        if binary is None:
            return "grok is not on PATH or in ~/.grok/bin"
        help_blob = help_text([binary])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(help_blob, "--always-approve")
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        return [binary, "-p", instruction, "--cwd", str(cwd), *caps, *extra]
    if harness.id == "codex":
        binary = find_codex()
        if binary is None:
            return "codex is not on PATH"
        help_blob = help_text([binary, "exec"])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(help_blob, "--skip-git-repo-check")
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        # Insert extra flags before the prompt so they are not eaten as the task.
        return [binary, "exec", "-C", str(cwd), *caps, *extra, instruction]
    if harness.id == "cursor-composer":
        chosen = model or DEFAULT_CURSOR_MODEL
        if model is None and (pools or family is not None):
            selected = select_model(harness.id, pools=pools, family=family)
            if isinstance(selected, str):
                return selected
            chosen = selected.id
        if cursor_pool_for_model(chosen) == "cursor-other" and model is None:
            return (
                f"refusing default cursor model {chosen!r}: it draws on the Cursor Other "
                "Models pool (claude-*/gpt-*/gemini-*). Automatic selection avoids that "
                "pool; pass --model explicitly if you mean to spend it."
            )
        native = cursor_native()
        extra: list[str] = []
        if native is not None:
            help_blob = help_text([native])
            caps = native_cap_flags(
                harness.id,
                help_blob,
                max_turns=max_turns,
                max_tokens=max_tokens,
            )
            if isinstance(caps, str):
                return caps
            extra = optional_flags(help_blob, "--force", "--trust")
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
                *caps,
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
        help_blob = help_text([bridge, "-e", "bash", "-lc", "cursor-agent --help"])
        caps = native_cap_flags(
            harness.id,
            help_blob,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        if isinstance(caps, str):
            return caps
        extra = optional_flags(
            help_blob,
            "--force",
            "--trust",
        )
        for flag in bypass:
            if flag not in extra:
                extra.append(flag)
        extra_s = " " + " ".join([*caps, *extra])
        # The task body never enters the shell: only paths we created do.
        # GIT_DIR/GIT_WORK_TREE are WSL paths so linked worktrees are repositories
        # to WSL git (R4). Native cursor-agent is unchanged — it already sees NT paths.
        inner = (
            f"{wsl_git_exports(cwd)}cd {shlex.quote(wsl_cwd)} && cursor-agent -p "
            f"--model {shlex.quote(chosen)} --output-format text{extra_s} "
            f"{shlex.quote(wsl_instruction)}"
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
    log_dir: Path | None = None,
    in_flight: str = "",
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    claim_run_id: str | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> RunResult:
    cwd = cwd.resolve()
    run_dir = run_dir.resolve()
    brief = (run_dir / "brief.md").resolve()
    stdout_path = (run_dir / "stdout.txt").resolve()
    stderr_path = (run_dir / "stderr.txt").resolve()
    built = build_command(
        harness,
        task=task,
        cwd=cwd,
        brief=brief,
        model=model,
        permissions=permissions,
        family=family,
        pools=pools,
        max_turns=max_turns,
        max_tokens=max_tokens,
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
    write_brief(
        run_dir, task, log_dir=log_dir, in_flight=in_flight, claim_run_id=claim_run_id
    )
    argv = built
    env = dict(GIT_ENV)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        if harness.id == "cursor-composer":
            with ExclusiveFileLock(DEFAULT_CURSOR_LOCK, timeout_s=float(timeout_s)):
                code, timed_out, duration = run_process(
                    argv,
                    cwd=cwd,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    timeout_s=timeout_s,
                    env=env,
                )
        else:
            code, timed_out, duration = run_process(
                argv,
                cwd=cwd,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                timeout_s=timeout_s,
                env=env,
            )
    except TimeoutError as exc:
        return RunResult(
            harness=harness,
            status="refused",
            reason=str(exc),
            exit_code=None,
            stdout="",
            stderr="",
            artefact_bytes=0,
            diff_bytes=0,
            timed_out=False,
            duration_s=0.0,
            command=tuple(argv),
            run_id=run_id,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
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
        print(
            f"harness: {payload['harness']} ({payload.get('family')}, {payload.get('pool')})"
        )
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
        print(
            f"{'id':<18} {'family':<10} {'pool':<16} {'installed':<10} {'used':<8} note"
        )
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


def repo_roots() -> tuple[Path, ...]:
    """This repository's root, plus every git worktree checked out from the same repository.

    `git worktree list` is the only enumeration that stays true when a worktree is added or
    removed; a hard-coded list would drift. If git cannot answer, the answer is ROOT alone,
    which refuses more rather than less.
    """
    roots = [ROOT]
    git = which_binary("git")
    if git is not None:
        try:
            completed = subprocess.run(
                [git, "-C", str(ROOT), "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env=GIT_ENV,
            )
            listing = completed.stdout if completed.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            listing = ""
        for line in (listing or "").splitlines():
            if not line.startswith("worktree "):
                continue
            candidate = Path(line[len("worktree ") :].strip())
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if resolved.is_dir():
                roots.append(resolved)
    return tuple(dict.fromkeys(roots))


def load_allowed_roots(path: Path | None = None) -> tuple[Path, ...]:
    """Instance cwd allowlist. Missing file means no extra roots. Malformed file fails closed.

    This does not pass Gate B. The principal names supervised roots; the product default is
    still refuse-everything-else. A filesystem root in the list is refused so a typo cannot
    authorise the machine.
    """
    source = path if path is not None else DEFAULT_ALLOWED_CWDS
    if not source.is_file():
        return ()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"allowed-cwds file {source} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError(
            f"allowed-cwds file {source} must be a JSON object with a roots list"
        )
    listed = raw.get("roots", [])
    if not isinstance(listed, list):
        raise ValueError(
            f"allowed-cwds file {source} field 'roots' must be a list of paths"
        )
    roots: list[Path] = []
    for item in listed:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"allowed-cwds file {source} roots must be non-empty strings"
            )
        try:
            candidate = Path(item).expanduser().resolve()
        except OSError as exc:
            raise ValueError(
                f"allowed-cwds file {source} has an unresolvable root {item!r}: {exc}"
            ) from exc
        if candidate.parent == candidate:
            raise ValueError(
                f"refusing filesystem root {candidate} in allowed-cwds: name a repository, "
                "not a volume"
            )
        if candidate.is_dir():
            roots.append(candidate)
    return tuple(dict.fromkeys(roots))


def resolve_cwd(value: str | None, *, allowed_file: Path | None = None) -> Path:
    """Resolve the working directory, refusing unnamed foreign roots.

    Default is this repository and its worktrees. Extra roots come only from the gitignored
    instance allowlist (ADR-0063). There is deliberately no override flag — a second path
    to the same state is the same hole. Naming a root is supervised dispatch under
    ADR-0039; it does not pass Gate B.
    """
    path = (Path(value) if value else Path.cwd()).resolve()
    roots = list(repo_roots())
    roots.extend(load_allowed_roots(allowed_file))
    for root in roots:
        if path == root or root in path.parents:
            return path
    raise ValueError(
        f"refusing to dispatch with cwd {path}: this harness runs only inside its own "
        f"repository ({ROOT}), a git worktree of the same repository, a directory "
        "within one of those, or a root named in the instance allowlist "
        f"({DEFAULT_ALLOWED_CWDS.name}). Gate B — depending on this harness for work on "
        "another repository — is not passed. Listing a root is supervised dispatch "
        "(ADR-0039/ADR-0063), not a gate pass, and no command-line flag reopens Gate B."
    )


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


def _claim_conflict_refusal(
    *,
    log_dir: Path,
    ts: str,
    run_id: str,
    task: str,
    cwd: Path,
    hit: tuple[coordination.Claim, str, str],
    live: tuple[coordination.Claim, ...],
) -> tuple[dict[str, object], int]:
    """A second dispatch claiming an overlapping path is refused, and the refusal is
    recorded like every other — the refusal IS the coordination mechanism working."""
    claim, requested, held = hit
    reason = (
        f"claims overlap a live dispatch: {claim.ticket} (run {claim.run_id}, "
        f"{claim.actor}) holds {held!r} until {claim.expires_at}; this dispatch asked "
        f"for {requested!r}. Refusing rather than admitting two agents to the same "
        "path — re-dispatch when the live claim completes or expires."
    )
    considered = [
        f"{item.ticket} holds {list(item.paths) or ['(no paths declared)']}"
        for item in live
    ]
    recorded = record_refusal(
        log_dir,
        ts=ts,
        run_id=run_id,
        task=task,
        cwd=str(cwd),
        reason=reason,
        considered=considered,
        attempted=f"dispatch claiming {requested!r}",
    )
    payload = {
        "status": "refused",
        "reason": reason,
        "considered": considered,
        "run_id": run_id,
        "cwd": str(cwd),
        "conflict": {"ticket": claim.ticket, "requested": requested, "held": held},
        "recorded": str(log_dir / f"{ts[:10]}.jsonl"),
        "event": recorded["event"],
    }
    return payload, _exit_for("refused")


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
    claims: tuple[str, ...] = (),
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
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
    now = datetime.now(timezone.utc)
    events, rejected = read_all(log_dir)
    live = coordination.live_claims(events, now=now)
    in_flight = coordination.render_in_flight(live, now=now)

    if dry_run:
        brief = write_brief(
            (runs_dir / run_id).resolve(),
            task,
            log_dir=log_dir,
            in_flight=in_flight,
            claim_run_id=run_id,
        )
        built = build_command(
            harness,
            task=task,
            cwd=cwd,
            brief=brief,
            model=model,
            permissions=permissions,
            family=family,
            pools=pools,
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        command = built if isinstance(built, list) else []
        reason = built if isinstance(built, str) else decision.reason
        hit = coordination.conflict(claims, live, cwd=cwd) if claims else None
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
            "claims": list(claims),
            "claim_conflict": (
                {"ticket": hit[0].ticket, "requested": hit[1], "held": hit[2]}
                if hit is not None
                else None
            ),
            "in_flight": len(live),
        }
        return payload, 0 if isinstance(built, list) else _exit_for("refused")

    if claims:
        hit = coordination.conflict(claims, live, cwd=cwd)
        if hit is not None:
            return _claim_conflict_refusal(
                log_dir=log_dir,
                ts=ts,
                run_id=run_id,
                task=task,
                cwd=cwd,
                hit=hit,
                live=live,
            )

    claim_event = coordination.open_claim(
        log_dir,
        run_id=run_id,
        paths=claims,
        cwd=cwd,
        timeout_s=timeout_s,
        harness=harness.id,
        task=task,
        now=now,
    )

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
        log_dir=log_dir,
        in_flight=in_flight,
        family=family,
        pools=pools,
        claim_run_id=run_id,
        max_turns=max_turns,
        max_tokens=max_tokens,
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
    record_dispatch_error(log_dir, result)
    _harvest_quietly(log_dir, runs_dir)
    # Three release paths and any one suffices: this completion, the outcome event
    # above (live_claims treats a terminal dispatch event as a release), or the claim's
    # own expiry. A close failure therefore degrades to the other two, never to a hang.
    try:
        coordination.close_claim(log_dir, run_id=run_id)
        claim_released: bool | str = True
    except EventError as exc:
        claim_released = (
            f"close failed ({exc}); expiry and the outcome event release it"
        )
    payload = {
        "status": result.status,
        "selected": decision.reason,
        "cwd": str(cwd),
        "recorded": str(log_dir / f"{recorded['ts'][:10]}.jsonl"),
        "claim": {
            "ticket": coordination.claim_ticket(run_id),
            "paths": claim_event["data"].get("paths", []),
            "expires_at": claim_event["data"].get("expires_at"),
            "released": claim_released,
        },
        "in_flight": len(live),
        **({"log_rejected_lines": len(rejected)} if rejected else {}),
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
    claims: tuple[str, ...] = (),
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
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
            attempted="fan-out selection (two families)",
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

    now = datetime.now(timezone.utc)
    events, rejected = read_all(log_dir)
    live = coordination.live_claims(events, now=now)
    in_flight = coordination.render_in_flight(live, now=now)

    if dry_run:
        hit = coordination.conflict(claims, live, cwd=cwd) if claims else None
        payload = {
            "status": "dry-run",
            "selected": decision.reason,
            "first": decision.first.id,
            "second": decision.second.id,
            "cwd": str(cwd),
            "run_id": run_id,
            "claims": list(claims),
            "claim_conflict": (
                {"ticket": hit[0].ticket, "requested": hit[1], "held": hit[2]}
                if hit is not None
                else None
            ),
            "in_flight": len(live),
        }
        return payload, 0

    if claims:
        hit = coordination.conflict(claims, live, cwd=cwd)
        if hit is not None:
            return _claim_conflict_refusal(
                log_dir=log_dir,
                ts=ts,
                run_id=run_id,
                task=task,
                cwd=cwd,
                hit=hit,
                live=live,
            )

    claim_event = coordination.open_claim(
        log_dir,
        run_id=run_id,
        paths=claims,
        cwd=cwd,
        timeout_s=timeout_s,
        harness=f"{decision.first.id},{decision.second.id}",
        task=task,
        now=now,
    )

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
            log_dir=log_dir,
            in_flight=in_flight,
            family=family,
            pools=pools,
            # The claim covering both children is the parent's, so the badge the
            # pre-commit gate checks against is the parent's run id.
            claim_run_id=run_id,
            max_turns=max_turns,
            max_tokens=max_tokens,
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
        record_dispatch_error(log_dir, result)
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
    _harvest_quietly(log_dir, runs_dir)
    # As in dispatch_one: completion, the terminal fanout event, and expiry are three
    # independent release paths; any one suffices.
    try:
        coordination.close_claim(log_dir, run_id=run_id)
        claim_released: bool | str = True
    except EventError as exc:
        claim_released = f"close failed ({exc}); expiry and the fanout event release it"
    payload = {
        "status": verdict,
        "verdict": verdict,
        "selected": decision.reason,
        "cwd": str(cwd),
        "run_id": run_id,
        "recorded": str(log_dir / f"{recorded['ts'][:10]}.jsonl"),
        "claim": {
            "ticket": coordination.claim_ticket(run_id),
            "paths": claim_event["data"].get("paths", []),
            "expires_at": claim_event["data"].get("expires_at"),
            "released": claim_released,
        },
        "in_flight": len(live),
        **({"log_rejected_lines": len(rejected)} if rejected else {}),
        "first": _result_payload(first),
        "second": _result_payload(second),
    }
    worst = first.status if first.status != "ok" else second.status
    if first.status == "ok" and second.status == "ok":
        return payload, 0
    return payload, _exit_for(worst)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatch a task to a subscription harness. Not a consil subcommand."
    )
    parser.add_argument("task", nargs="?", help="the task to run")
    parser.add_argument(
        "--task-file", help="read the task from this file (preferred for long briefs)"
    )
    parser.add_argument(
        "--cwd",
        help="working directory; this repository, a worktree of it, or an instance-allowlisted root",
    )
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
    parser.add_argument(
        "--model", help="model id (cursor-composer defaults to composer-2.5)"
    )
    parser.add_argument(
        "--family",
        help="model family to pick from (e.g. grok, kimi, composer); automatic selection "
        "prefers the idlest registered pool within the family",
    )
    parser.add_argument(
        "--claim",
        action="append",
        default=None,
        metavar="PATH",
        help="declare a path this dispatch intends to touch; repeatable. A second live "
        "dispatch claiming an overlapping path is refused. Claims are trajectory events "
        "with an expiry (timeout + grace), so a crashed dispatcher cannot hold one.",
    )
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-turns", type=positive_int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--max-tokens", type=positive_int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--headroom", default=str(DEFAULT_HEADROOM))
    parser.add_argument("--runs", default=str(DEFAULT_RUNS))
    parser.add_argument(
        "--probe", action="store_true", help="probe installed harnesses and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="select (and print argv) without running"
    )
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
    try:
        cwd = resolve_cwd(args.cwd)
    except ValueError as exc:
        # Before anything else, and before --dry-run can print a command that names
        # another repository. A refused boundary must not leave a runnable artefact.
        emit({"status": "refused", "reason": str(exc)}, args.json)
        return 2
    log_dir = Path(args.log).resolve()
    runs_dir = Path(args.runs).resolve()
    headroom_path = Path(args.headroom).resolve()
    refresh_refusal = refresh_default_headroom(headroom_path)
    if refresh_refusal is not None:
        emit({"status": "refused", "reason": refresh_refusal}, args.json)
        return 2
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
    freshness_refusal = headroom_freshness_refusal(
        pools, now=datetime.now(timezone.utc)
    )
    if freshness_refusal is not None:
        emit({"status": "refused", "reason": freshness_refusal}, args.json)
        return 2

    probes = probe_all()
    if args.probe:
        payload = {
            "status": "probed",
            "cwd": str(cwd),
            "headroom": str(headroom_path),
            "headroom_source": pools[0].source if pools else "",
            "harnesses": describe_registry(
                probes=probes, pools=pools, harnesses=HARNESSES
            ),
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
            claims=tuple(args.claim or ()),
            family=args.family,
            pools=pools,
            max_turns=args.max_turns,
            max_tokens=args.max_tokens,
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
        claims=tuple(args.claim or ()),
        family=args.family,
        pools=pools,
        max_turns=args.max_turns,
        max_tokens=args.max_tokens,
    )
    emit(payload, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

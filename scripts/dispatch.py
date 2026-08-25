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
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import coordination, instructions  # noqa: E402
from consilient.capabilities import CapabilityError, select_capabilities  # noqa: E402
from consilient.effects import (  # noqa: E402
    EffectManifest,
    ProofObservation,
    RecoveryProof,
    canonical_state_digest,
    evaluate_recovery_proof,
)
from consilient.error_tracking import (  # noqa: E402
    ErrorRecordError,
    append_record,
    build_record,
)
from consilient.events import SCHEMA_VERSION, EventError, append, read_all  # noqa: E402
from consilient.records import RecordRef, capture_file  # noqa: E402
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
    DISPATCH_ACTOR,
    DISPATCH_OUTCOME_KIND,
    classify_gap,
    record_fanout,
    record_gap,
    record_refusal,
    record_request,
    build_request_timing,
    extract_usage_from_output,
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
DEFAULT_SKILLS = ROOT / ".agents" / "skills"
HELDOUT_ISOLATION_CHECKER = ROOT / ".github" / "scripts" / "check_heldout_isolation.py"
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
# How long a cursor launch holds the shared-config lock, and how long a waiter tries.
# The settle window covers cursor-agent reading its config; the timeout is bounded so a
# waiter fails in minutes rather than burning an hour-long leash.
CURSOR_START_SETTLE_S = 20.0
CURSOR_START_LOCK_TIMEOUT_S = 420.0
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}


@dataclass(frozen=True)
class StreamTiming:
    t_send: str
    t_first_chunk: str
    t_first_nonempty_chunk: str
    n_chunks: int


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
    request_timing: object | None = None
    assembly_id: str | None = None
    output_records: dict[str, object] | None = None


def heldout_contract_refusal(contract: str) -> str:
    spec = importlib.util.spec_from_file_location(
        "check_heldout_isolation", HELDOUT_ISOLATION_CHECKER
    )
    if spec is None or spec.loader is None:
        return "held-out isolation checker is unavailable; refusing before child launch"
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    refusal_reason = cast(Callable[[str], str], checker.refusal_reason)
    return refusal_reason(contract)


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


WORKSPACE_FORMS = ("linked_worktree", "isolated_git_env", "full_clone")


class WorkspaceProbeError(RuntimeError):
    """A workspace form failed read, write, stage or throwaway commit."""


@dataclass(frozen=True)
class IsolatedWorkspace:
    form: str
    work_tree: Path
    git_dir: Path
    index_path: Path
    runtime_id: str
    runtime_version: str


def _git_identity_env() -> dict[str, str]:
    env = dict(GIT_ENV)
    env.setdefault("GIT_AUTHOR_NAME", "consilient.dispatch")
    env.setdefault("GIT_AUTHOR_EMAIL", "dispatch@consilient.invalid")
    env.setdefault("GIT_COMMITTER_NAME", "consilient.dispatch")
    env.setdefault("GIT_COMMITTER_EMAIL", "dispatch@consilient.invalid")
    return env


def _run_git(
    cwd: Path,
    *args: str,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    git = which_binary("git")
    if git is None:
        raise WorkspaceProbeError("git is not installed")
    env = _git_identity_env()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [git, "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )


def workspace_index_path(work_tree: Path, extra_env: Mapping[str, str] | None = None) -> Path:
    completed = _run_git(work_tree, "rev-parse", "--git-path", "index", extra_env=extra_env)
    if completed.returncode != 0:
        raise WorkspaceProbeError(completed.stderr or "could not resolve git index")
    raw = (completed.stdout or "").strip()
    index = Path(raw)
    if not index.is_absolute():
        index = (work_tree / index).resolve()
    return index


def _probe_read_write_stage_commit(
    work_tree: Path, extra_env: Mapping[str, str] | None = None
) -> None:
    tracked = _run_git(work_tree, "ls-files", extra_env=extra_env)
    if tracked.returncode != 0:
        raise WorkspaceProbeError(tracked.stderr or "read probe failed")
    names = [line for line in (tracked.stdout or "").splitlines() if line.strip()]
    if not names:
        raise WorkspaceProbeError("read probe found no tracked file")
    sample = work_tree / names[0]
    sample.read_bytes()
    probe = work_tree / f".consilient-workspace-probe-{os.getpid()}"
    probe.write_text("probe\n", encoding="utf-8")
    added = _run_git(work_tree, "add", probe.name, extra_env=extra_env)
    if added.returncode != 0:
        raise WorkspaceProbeError(added.stderr or "stage probe failed")
    committed = _run_git(
        work_tree, "commit", "-m", "consilient workspace probe", extra_env=extra_env
    )
    if committed.returncode != 0:
        raise WorkspaceProbeError(committed.stderr or "throwaway commit probe failed")
    probe.unlink(missing_ok=True)


def _materialise_workspace_form(form: str, source: Path, dest: Path) -> Mapping[str, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    if form == "linked_worktree":
        branch = f"consilient-ws-{dest.name}"
        completed = _run_git(
            source, "worktree", "add", "-b", branch, str(dest)
        )
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "linked worktree add failed")
        return {}
    if form == "isolated_git_env":
        git_dir = dest.parent / f"{dest.name}.git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        completed = _run_git(
            source, "clone", "--separate-git-dir", str(git_dir), str(source), str(dest)
        )
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "isolated git clone failed")
        return {"GIT_DIR": str(git_dir.resolve()), "GIT_WORK_TREE": str(dest.resolve())}
    if form == "full_clone":
        completed = _run_git(source, "clone", str(source), str(dest))
        if completed.returncode != 0:
            raise WorkspaceProbeError(completed.stderr or "full clone failed")
        return {}
    raise WorkspaceProbeError(f"unknown workspace form {form!r}")


def probe_workspace_form(
    form: str,
    source: Path,
    dest: Path,
    *,
    runtime_id: str,
    runtime_version: str,
) -> IsolatedWorkspace:
    """Prove one form with an actual read, write, stage and throwaway commit."""
    extra = dict(_materialise_workspace_form(form, source, dest))
    _probe_read_write_stage_commit(dest, extra_env=extra or None)
    workspace = git_workspace(dest)
    if workspace is None:
        raise WorkspaceProbeError("probed workspace is not a git work tree")
    git_dir, work_tree = workspace
    if extra.get("GIT_DIR"):
        git_dir = Path(extra["GIT_DIR"])
    index = workspace_index_path(dest, extra_env=extra or None)
    return IsolatedWorkspace(
        form=form,
        work_tree=work_tree,
        git_dir=git_dir,
        index_path=index,
        runtime_id=runtime_id,
        runtime_version=runtime_version,
    )


def provision_isolated_workspace(
    cwd: Path,
    *,
    run_id: str,
    dest_root: Path,
    runtime_id: str,
    runtime_version: str,
) -> IsolatedWorkspace | None | str:
    """Provision a proved isolated workspace, or None when cwd is not a git repo.

    A git repository that cannot prove any form returns a refusal string so the
    caller can record an adverse attempt and skip launch.
    """
    if git_workspace(cwd) is None:
        return None
    dest_root.mkdir(parents=True, exist_ok=True)
    last_error = "no workspace form was attempted"
    for form in WORKSPACE_FORMS:
        target = dest_root / form / run_id
        try:
            return probe_workspace_form(
                form,
                cwd,
                target,
                runtime_id=runtime_id,
                runtime_version=runtime_version,
            )
        except (WorkspaceProbeError, OSError) as exc:
            last_error = f"{form} failed: {exc}"
            continue
    return f"no runtime-conformant isolated workspace: {last_error}"


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


def _drain_stream(
    pipe: Any,
    out_path: Path,
    *,
    chunk_size: int = 4096,
) -> tuple[int, str | None, str | None]:
    """Read pipe in chunks; return count and first-chunk timestamps."""
    n_chunks = 0
    t_first: str | None = None
    t_first_nonempty: str | None = None
    with out_path.open("wb") as handle:
        while True:
            chunk = pipe.read(chunk_size)
            if not chunk:
                break
            now = datetime.now(timezone.utc).isoformat()
            n_chunks += 1
            if t_first is None:
                t_first = now
            if t_first_nonempty is None and chunk.strip():
                t_first_nonempty = now
            handle.write(chunk)
    return n_chunks, t_first, t_first_nonempty


def _stream_reader(
    pipe: Any,
    out_path: Path,
    meta: dict[str, Any],
    *,
    chunk_size: int = 4096,
) -> None:
    n_chunks, t_first, t_first_nonempty = _drain_stream(
        pipe, out_path, chunk_size=chunk_size
    )
    meta["n_chunks"] = n_chunks
    meta["t_first"] = t_first
    meta["t_first_nonempty"] = t_first_nonempty


def run_process(
    argv: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_s: int,
    env: dict[str, str] | None = None,
    on_started: Callable[[], None] | None = None,
) -> tuple[int | None, bool, float, StreamTiming | None]:
    """Run argv, writing output to files (not pipes), and kill the process tree on timeout.

    `on_started` runs once the child is spawned and its readers are attached. It exists so a
    caller holding a startup lock can release it without holding for the whole run.
    """
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
    t_send = datetime.now(timezone.utc).isoformat()
    timing: StreamTiming | None = None
    try:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **kwargs,
        )
    except OSError:
        return None, False, time.perf_counter() - started, None
    assert process.stdout is not None and process.stderr is not None
    stdout_meta: dict[str, Any] = {}
    stderr_meta: dict[str, Any] = {}
    stdout_thread = threading.Thread(
        target=_stream_reader,
        args=(process.stdout, stdout_path, stdout_meta),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_stream_reader,
        args=(process.stderr, stderr_path, stderr_meta),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    if on_started is not None:
        on_started()
    try:
        process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_process_tree(process)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    stdout_thread.join(timeout=10)
    stderr_thread.join(timeout=10)
    n_chunks = int(stdout_meta.get("n_chunks", 0)) + int(stderr_meta.get("n_chunks", 0))
    candidates = [
        ts
        for ts in (stdout_meta.get("t_first"), stderr_meta.get("t_first"))
        if isinstance(ts, str)
    ]
    nonempty_candidates = [
        ts
        for ts in (
            stdout_meta.get("t_first_nonempty"),
            stderr_meta.get("t_first_nonempty"),
        )
        if isinstance(ts, str)
    ]
    t_first = min(candidates) if candidates else t_send
    t_first_nonempty = (
        min(nonempty_candidates) if nonempty_candidates else t_first
    )
    timing = StreamTiming(
        t_send=t_send,
        t_first_chunk=t_first,
        t_first_nonempty_chunk=t_first_nonempty,
        n_chunks=n_chunks,
    )
    return process.returncode, timed_out, time.perf_counter() - started, timing


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
            if (
                headroom_freshness_refusal(current, now=datetime.now(timezone.utc))
                is None
            ):
                return None
    with tempfile.TemporaryDirectory(prefix="consilient-headroom-") as directory:
        temporary = Path(directory)
        code, timed_out, _duration, _timing = run_process(
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
        # A failed refresh must not refuse the work. The probe succeeds standalone and fails under
        # concurrency: nineteen dispatchers refreshing one snapshot on Windows collide on the write,
        # and on 23 August 2026 that refused two dispatches outright with "headroom refresh failed
        # (exit 1)" while the probe returned zero when run by hand. [measured]
        #
        # F-08 says a stale reading must never silently become a value, and that still holds — the
        # snapshot below is returned to the caller with its own freshness refusal intact, so a
        # consumer that needs current data still refuses. What changes is that a transient write
        # collision no longer costs a dispatch: an unreadable snapshot refuses, a readable stale one
        # proceeds and is treated as stale by everything downstream.
        if path.exists():
            try:
                load_pools(path)
            except ValueError:
                return f"headroom refresh failed (exit {code}) and the snapshot is unreadable"
            return None
        return f"headroom refresh failed (exit {code}) and no snapshot exists"
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


# --- the cheap supervision floor (BU-0) ---------------------------------------------
#
# On 23 August 2026 six of six failed dispatches died at startup seconds after the
# scheduler printed that the work had been sent, and the loop went on reporting itself
# busy. One of them was the only run ever sent to its provider, so that provider sat at
# 17% usage for two days while the loop called it busy; the principal found that from a
# usage graph and asked about it three times. Nothing reported it. [measured, F-13]
#
# The bar this clears is not latency. Kubernetes surfaces a crash loop within one probe
# period, systemd within WatchdogSec, s6 the moment a service fails to notify; a polled
# check cannot beat any of them and does not claim to. [cited, via the supervision
# specification] What it does instead is take its evidence from the work rather than
# from the worker: no PID, no handle, no port. Process checks have reported dead work
# healthy three times here. [measured, ADR-0034 context]

# Preferential, and ADR-0034 says every parameter in it is. It is the grace a dispatch
# gets to produce any one of the three artefacts below, and it is far shorter than
# DEFAULT_TIMEOUT_S so a dispatch that dies on import is caught inside one poll rather
# than at its deadline. It is not measured, and EXP-73 is the registered experiment
# that would set it: it measures the false-stall rate of exactly this signal and is
# BLOCKED on ticks that declare their progress artefact. [asserted]
START_WINDOW_S = 120

# The dispatcher writes these into the run directory before the child is spawned. They
# are evidence that we asked, never evidence that anything answered.
_DISPATCHER_WRITTEN = frozenset({"brief.md", "recall.md"})


class ExpectedArtefactError(ValueError):
    """A dispatch that declares no progress artefact is refused before spawn."""


def write_expected(
    runs_dir: Path,
    *,
    run_id: str,
    arm: str,
    unit: str,
    expected_artefact: str | None,
    start_window_s: int = START_WINDOW_S,
    progress_deadline_s: int,
    grace_s: int = coordination.CLAIM_GRACE_S,
) -> Path:
    """Write `dispatch/<run_id>.json` `expected` before spawn, or refuse.

    BU-1 / N01. The record names what the supervisor will watch. An empty, blank
    or dispatcher-written artefact is not a declaration: brief.md and recall.md
    are our own output, and counting them as progress is the 23 August failure
    [measured, N00]. Nothing is written on refusal, because an expected record
    with no artefact is the silent channel this exists to make impossible.
    """
    artefact = "" if expected_artefact is None else str(expected_artefact).strip()
    name = Path(artefact.replace("\\", "/")).name.casefold()
    if not artefact or name in _DISPATCHER_WRITTEN:
        raise ExpectedArtefactError(
            "a dispatch that declares no artefact is refused at dispatch time"
        )
    record = {
        "run_id": run_id,
        "arm": arm,
        "unit": unit,
        "artefact": artefact,
        "start_window_s": start_window_s,
        "progress_deadline_s": progress_deadline_s,
        "grace_s": grace_s,
    }
    return _store_dispatch_field(runs_dir, run_id, "expected", record)


def inspect_uncommitted_tracked(cwd: Path) -> tuple[bool, tuple[str, ...]]:
    """Tracked paths that differ from HEAD. Untracked files are not output.

    The incumbent is `git status --porcelain --untracked-files=no`, already
    used here by EXP-96 to refuse a dirty measurement corpus. [measured]
    A failed inspection is not a clean tree (F-09).
    """
    git = which_binary("git")
    if git is None:
        return False, ()
    try:
        completed = subprocess.run(
            [
                git,
                "-C",
                str(cwd.resolve()),
                "-c",
                "core.quotepath=false",
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ()
    if completed.returncode != 0:
        return False, ()
    paths: set[str] = set()
    for raw in (completed.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        remainder = raw[3:]
        if " -> " in remainder:
            left, right = remainder.split(" -> ", 1)
            paths.add(left)
            paths.add(right)
        else:
            paths.add(remainder)
    return True, tuple(sorted(paths))


def write_terminal(
    runs_dir: Path,
    *,
    run_id: str,
    exit_code: int | None,
    cwd: Path,
    claim_disposition: str,
) -> Path:
    """Write `dispatch/<run_id>.json` `terminal` after the child exits.

    BU-4 / N04. F-02 measured a worker exiting with output uncommitted and
    the queue reading idle: the claim released, the paths did not. The
    wrapper writes the list; an exit with uncommitted tracked changes is
    an incomplete outcome, not a success. [measured]
    """
    inspected, paths = inspect_uncommitted_tracked(cwd)
    record = {
        "exit_code": exit_code,
        "uncommitted_tracked_paths": list(paths),
        "claim_disposition": claim_disposition,
        "outcome": "complete" if inspected and not paths else "incomplete",
        "inspected": inspected,
    }
    return _store_dispatch_field(runs_dir, run_id, "terminal", record)


@dataclass(frozen=True)
class StartFailure:
    """One open dispatch that never produced a first artefact.

    ADR-0034 §6: a stall decision records the signal, the threshold, the observed
    value and the action taken, so an operator can dispute it from the record alone.
    The action is never termination — §3 defaults to diagnosis, because killing is the
    irreversible half and the expensive production failure is a watchdog that acts on
    live work.

    A start failure does not consume a work attempt: an infrastructure death is
    not evidence about the work (F-05 / F-13).
    """

    run_id: str
    harness: str | None
    signal: str
    threshold_s: int
    observed_s: float
    observed_bytes: int
    action: str
    consumes_attempt: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "harness": self.harness,
            "signal": self.signal,
            "threshold_s": self.threshold_s,
            "observed_s": self.observed_s,
            "observed_bytes": self.observed_bytes,
            "action": self.action,
            "consumes_attempt": self.consumes_attempt,
        }


@dataclass(frozen=True)
class Stall:
    """A dispatch that declared start and then produced no further progress.

    The started line is s6's notification, not a health signal. Treating it as
    healthy is startsecs by another name. [cited, skarnet.org/software/s6]
    """

    run_id: str
    harness: str | None
    signal: str
    threshold_s: int
    observed_s: float
    action: str

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "harness": self.harness,
            "signal": self.signal,
            "threshold_s": self.threshold_s,
            "observed_s": self.observed_s,
            "action": self.action,
        }


def _dispatch_record_path(runs_dir: Path, run_id: str) -> Path:
    return runs_dir / f"{run_id}.json"


def _load_dispatch_record(runs_dir: Path, run_id: str) -> dict[str, object]:
    path = _dispatch_record_path(runs_dir, run_id)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _store_dispatch_field(
    runs_dir: Path, run_id: str, field: str, value: object
) -> Path:
    path = _dispatch_record_path(runs_dir, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _load_dispatch_record(runs_dir, run_id)
    payload[field] = value
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(encoded, encoding="utf-8")
    os.replace(tmp, path)
    return path


def started_line_in(run_dir: Path, artefact: str) -> str | None:
    """First non-empty line the agent wrote to the declared path, or None.

    Dispatcher-written names never count: they are evidence we asked, not
    that anything answered. [measured, N00]
    """
    artefact = str(artefact).strip()
    if not artefact:
        return None
    name = Path(artefact.replace("\\", "/")).name.casefold()
    if name in _DISPATCHER_WRITTEN:
        return None
    try:
        root = run_dir.resolve()
        path = (run_dir / artefact).resolve()
        path.relative_to(root)
    except (OSError, ValueError):
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped:
            return stripped
    return None


def write_started(
    runs_dir: Path, run_id: str, *, now: datetime
) -> Path | None:
    """Write `started` only when the agent has appended a line to the declared path.

    BU-2 / N02. Surviving a timer is not a start. The wrapper observes the
    line; it does not invent one. s6's notification-fd is the incumbent and
    is mandatory. [cited, skarnet.org/software/s6/servicedir.html]
    """
    record = _load_dispatch_record(runs_dir, run_id)
    expected = record.get("expected")
    if not isinstance(expected, dict):
        return None
    artefact = expected.get("artefact")
    if not isinstance(artefact, str) or not artefact.strip():
        return None
    existing = record.get("started")
    if isinstance(existing, dict) and str(existing.get("line") or "").strip():
        return _dispatch_record_path(runs_dir, run_id)
    line = started_line_in(runs_dir / run_id, artefact)
    if line is None:
        return None
    started = {
        "run_id": run_id,
        "artefact": artefact,
        "line": line,
        "at": now.astimezone(timezone.utc).isoformat(),
    }
    return _store_dispatch_field(runs_dir, run_id, "started", started)


def artefact_bytes_in(run_dir: Path) -> int:
    """Bytes the child put in its own run directory, excluding what we put there.

    A missing or unreadable directory reads zero, which fails closed: an absent
    summary is not a pass (F-09).
    """
    total = 0
    try:
        for entry in run_dir.iterdir():
            if entry.name in _DISPATCHER_WRITTEN or not entry.is_file():
                continue
            total += entry.stat().st_size
    except OSError:
        return 0
    return total


def committed_since(cwd: Path, since: str) -> bool:
    """Whether the run's tree gained a commit since the claim opened.

    Absence of git, or of a repository, is not evidence of progress.
    """
    git = which_binary("git")
    if git is None:
        return False
    try:
        completed = subprocess.run(
            [git, "-C", str(cwd), "log", "-1", "--since", since, "--format=%H"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return bool((completed.stdout or "").strip())


def start_failures(
    claims: tuple[coordination.Claim, ...],
    *,
    runs_dir: Path,
    now: datetime,
    start_window_s: int = START_WINDOW_S,
) -> tuple[StartFailure, ...]:
    """Open dispatches that produced nothing inside their start window.

    `claims` is `coordination.live_claims`, which already drops any run carrying a
    terminal dispatch event. That is what stops the Airflow regression, where a task
    that had logged its own clean exit was marked failed from a stale liveness signal:
    the terminal record outranks this check, rather than racing it.

    When an `expected` record exists (N01), start is the agent-written line on the
    declared path (N02). Surviving the window is not a start. Bytes on some other
    file, including the wrapper transcript, do not substitute. A start failure
    never consumes a work attempt.

    Without `expected`, the N00 floor remains: Hadoop's disjunction over the child's
    transcript, the working tree, and the commits it has landed. That path exists
    because the first version of this function was run against the live trajectory
    on 23 August 2026 and flagged six open dispatches, one of them the
    alive-and-working run that wrote it. [measured]

    Returns records. It terminates nothing, releases nothing and repairs nothing.
    """
    found: list[StartFailure] = []
    for claim in sorted(claims, key=lambda item: item.run_id):
        opened = datetime.fromisoformat(claim.opened_at).astimezone(timezone.utc)
        age_s = (now.astimezone(timezone.utc) - opened).total_seconds()
        record = _load_dispatch_record(runs_dir, claim.run_id)
        expected = record.get("expected")
        if isinstance(expected, dict):
            artefact = expected.get("artefact")
            try:
                window = int(expected.get("start_window_s", start_window_s))
            except (TypeError, ValueError):
                window = start_window_s
            if age_s < window:
                continue
            started = record.get("started")
            declared = isinstance(artefact, str) and artefact.strip()
            notified = (
                isinstance(started, dict)
                and bool(str(started.get("line") or "").strip())
            ) or (
                declared
                and started_line_in(runs_dir / claim.run_id, str(artefact)) is not None
            )
            if notified:
                continue
            found.append(
                StartFailure(
                    run_id=claim.run_id,
                    harness=claim.harness,
                    signal="no started line within the start window",
                    threshold_s=window,
                    observed_s=round(age_s, 2),
                    observed_bytes=0,
                    action="diagnose",
                    consumes_attempt=False,
                )
            )
            continue
        if age_s < start_window_s:
            continue
        observed = artefact_bytes_in(runs_dir / claim.run_id)
        if observed > 0:
            continue
        tree = Path(claim.cwd) if claim.cwd else None
        if tree is not None and (
            git_diff_bytes(tree) > 0 or committed_since(tree, claim.opened_at)
        ):
            continue
        found.append(
            StartFailure(
                run_id=claim.run_id,
                harness=claim.harness,
                signal="no artefact within the start window",
                threshold_s=start_window_s,
                observed_s=round(age_s, 2),
                observed_bytes=observed,
                action="diagnose",
                consumes_attempt=False,
            )
        )
    return tuple(found)


def _nonempty_line_count(run_dir: Path, artefact: str) -> int:
    artefact = str(artefact).strip()
    if not artefact:
        return 0
    try:
        root = run_dir.resolve()
        path = (run_dir / artefact).resolve()
        path.relative_to(root)
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return 0
    return sum(1 for raw in text.splitlines() if raw.strip())


def _progressed_after_start(
    claim: coordination.Claim, runs_dir: Path, artefact: str
) -> bool:
    if _nonempty_line_count(runs_dir / claim.run_id, artefact) > 1:
        return True
    tree = Path(claim.cwd) if claim.cwd else None
    if tree is None:
        return False
    return git_diff_bytes(tree) > 0 or committed_since(tree, claim.opened_at)


def stall_failures(
    claims: tuple[coordination.Claim, ...],
    *,
    runs_dir: Path,
    now: datetime,
) -> tuple[Stall, ...]:
    """Open dispatches that notified start and then produced nothing further.

    The started line answers "did it start?", not "is it healthy?". A hang
    after notification is `stalled`, never `started`-and-healthy.
    """
    found: list[Stall] = []
    for claim in sorted(claims, key=lambda item: item.run_id):
        opened = datetime.fromisoformat(claim.opened_at).astimezone(timezone.utc)
        age_s = (now.astimezone(timezone.utc) - opened).total_seconds()
        record = _load_dispatch_record(runs_dir, claim.run_id)
        expected = record.get("expected")
        if not isinstance(expected, dict):
            continue
        artefact = expected.get("artefact")
        if not isinstance(artefact, str) or not artefact.strip():
            continue
        started = record.get("started")
        line = (
            str(started.get("line") or "").strip()
            if isinstance(started, dict)
            else ""
        )
        if not line:
            observed = started_line_in(runs_dir / claim.run_id, artefact)
            if observed is None:
                continue
        try:
            deadline = int(expected.get("progress_deadline_s"))
        except (TypeError, ValueError):
            continue
        if age_s < deadline:
            continue
        if _progressed_after_start(claim, runs_dir, artefact):
            continue
        found.append(
            Stall(
                run_id=claim.run_id,
                harness=claim.harness,
                signal="no progress after started",
                threshold_s=deadline,
                observed_s=round(age_s, 2),
                action="diagnose",
            )
        )
    return tuple(found)


RECALL_LIMIT_CHARS = 8000


def write_brief(
    run_dir: Path,
    task: str,
    *,
    log_dir: Path | None = None,
    in_flight: str = "",
    claim_run_id: str | None = None,
    assembly: instructions.Assembly | None = None,
) -> Path:
    """Write the task plus its assembled context so the child is not amnesiac.

    Cross-harness memory is the trajectory. Until 21 August 2026 this function
    wrote the task alone, so Cursor could not see what Codex had just done.

    The pack is written to `recall.md` beside the brief and referenced from it,
    and also embedded — the embed is what a child that reads only its brief still
    sees. Both are bounded at RECALL_LIMIT_CHARS; the bound is the point, because
    an unbounded coordination section crowds the task out of the context window.
    An assembly supplies the same pack without a second trajectory read and adds
    the other instruction layers. `in_flight` is the live-claims table rendered
    by the caller.

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
    if assembly is not None:
        recall = assembly.recall_pack
        body += "\n---\n\n"
        if recall.strip() and "No events in log" not in recall:
            recall_path = (run_dir / "recall.md").resolve()
            recall_path.write_text(recall, encoding="utf-8", newline="\n")
            body += (
                "## Context from the trajectory\n\n"
                "A verbatim recall pack is recorded at `recall.md` beside this brief "
                f"(bound: {assembly.recall_limit_chars} characters) and assembled below.\n\n"
            )
        if in_flight.strip():
            body += in_flight.strip() + "\n\n"
        body += "---\n\n" + assembly.text.rstrip() + "\n"
    elif log_dir is not None:
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
        extra = optional_flags(help_blob, *bypass)
        return [
            binary,
            "--prompt-file",
            brief.as_posix(),
            "--cwd",
            str(cwd),
            *caps,
            *extra,
        ]
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
    in_flight_at_dispatch: int = 0,
    family: str | None = None,
    pools: tuple[PoolState, ...] = (),
    claim_run_id: str | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    expected_artefact: str = "stdout.txt",
    unit: str = "",
    capability_selection: Mapping[str, object] | None = None,
    workspace_root: Path | None = None,
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
    assembly: instructions.Assembly | None = None
    pre_run_records: dict[str, object] = {}
    output_records: dict[str, object] | None = None
    capture_workspace = cwd if workspace_root is None else workspace_root
    if log_dir is not None:
        assembly = instructions.assemble(
            DEFAULT_SKILLS,
            log_dir,
            task=task,
            capability_selection=capability_selection,
        )
        capture_ok = _capture_root_ok(capture_workspace, log_dir)
        sealed_task = run_dir / "sealed-task.txt"
        assembled_instructions = run_dir / "assembled-instructions.txt"
        sealed_task.parent.mkdir(parents=True, exist_ok=True)
        sealed_task.write_text(task, encoding="utf-8", newline="\n")
        assembled_instructions.write_text(
            assembly.text, encoding="utf-8", newline="\n"
        )
        if capture_ok:
            pre_run_records = {
                "task": _capture_source(
                    sealed_task, workspace=capture_workspace, media_type="text/plain"
                ),
                "instructions": _capture_source(
                    assembled_instructions,
                    workspace=capture_workspace,
                    media_type="text/plain",
                ),
            }
        else:
            refused = _refused_capture("log_dir is not the authorised capture root")
            pre_run_records = {"task": refused, "instructions": refused}
    write_brief(
        run_dir,
        task,
        log_dir=log_dir,
        in_flight=in_flight,
        claim_run_id=claim_run_id,
        assembly=assembly,
    )
    if log_dir is not None and assembly is not None:
        instructions.record_assembly(
            log_dir, assembly, task=task, pre_run_records=pre_run_records
        )
    write_expected(
        run_dir.parent,
        run_id=run_id,
        arm=harness.id,
        unit=unit,
        expected_artefact=expected_artefact,
        progress_deadline_s=timeout_s,
    )
    argv = built
    env = dict(GIT_ENV)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    stream_timing: StreamTiming | None = None
    if harness.id == "grok":
        grok_home = Path(env.get("GROK_HOME", Path.home() / ".grok"))
        auth_path = Path(env.get("GROK_AUTH_PATH", grok_home / "auth.json"))
        env["GROK_HOME"] = str((run_dir / "grok-home").resolve())
        env["GROK_AUTH_PATH"] = str(auth_path.resolve())
        for surface in ("SKILLS", "RULES", "AGENTS", "MCPS", "HOOKS", "SESSIONS"):
            env[f"GROK_CLAUDE_{surface}_ENABLED"] = "false"
    try:
        if harness.id == "cursor-composer":
            # MEASURED 24 August 2026. This lock used to wrap the ENTIRE run for the full
            # leash, so exactly one cursor dispatch could execute per hour and every extra
            # burned its whole leash before failing with "cursor-agent lock held". Three units
            # lost an hour each to it, build_driver had to cap concurrent cursor slots at one,
            # and the principal's Cursor quota sat at 4% used while other arms were saturated.
            #
            # What it protects is `~/.cursor/cli-config.json`, which holds preferences and no
            # credentials, and which had not been written for THREE DAYS across dozens of
            # dispatches. The race is real but it is confined to start-up, when the config is
            # read; an hour-long exclusive hold to guard a file written perhaps weekly is a
            # scope error, not a safety measure.
            #
            # So the lock now covers start-up only: acquire, spawn, let the child settle, then
            # release and let it run alongside others. Waiters fail fast rather than burning a
            # leash. Deleting the lock outright is still wrong -- a corrupted cli-config.json
            # would break every cursor dispatch at once.
            lock = ExclusiveFileLock(
                DEFAULT_CURSOR_LOCK, timeout_s=CURSOR_START_LOCK_TIMEOUT_S
            )
            lock.__enter__()
            released = False

            def _release_after_start() -> None:
                nonlocal released
                if released:
                    return
                time.sleep(CURSOR_START_SETTLE_S)
                released = True
                lock.__exit__(None, None, None)

            try:
                code, timed_out, duration, stream_timing = run_process(
                    argv,
                    cwd=cwd,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    timeout_s=timeout_s,
                    env=env,
                    on_started=_release_after_start,
                )
            finally:
                _release_after_start()
        else:
            code, timed_out, duration, stream_timing = run_process(
                argv,
                cwd=cwd,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                timeout_s=timeout_s,
                env=env,
            )
    except TimeoutError as exc:
        write_terminal(
            run_dir.parent,
            run_id=run_id,
            exit_code=None,
            cwd=cwd,
            claim_disposition="held" if claim_run_id else "none",
        )
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
    write_started(run_dir.parent, run_id, now=datetime.now(timezone.utc))
    write_terminal(
        run_dir.parent,
        run_id=run_id,
        exit_code=code,
        cwd=cwd,
        claim_disposition="held" if claim_run_id else "none",
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
    request_timing = None
    if stream_timing is not None:
        usage = extract_usage_from_output(stdout, harness.id)
        request_timing = build_request_timing(
            t_send=stream_timing.t_send,
            t_first_chunk=stream_timing.t_first_chunk,
            t_first_nonempty_chunk=stream_timing.t_first_nonempty_chunk,
            n_chunks=stream_timing.n_chunks,
            output_tokens=usage["output_tokens"],
            cache_read_input_tokens=usage["cache_read_input_tokens"],
            in_flight_at_dispatch=in_flight_at_dispatch,
        )
    if log_dir is not None:
        if _capture_root_ok(capture_workspace, log_dir):
            output_records = _capture_run_outputs(
                run_dir, stdout_path, stderr_path, capture_workspace
            )
        else:
            refused = _refused_capture("log_dir is not the authorised capture root")
            output_records = {
                "stdout": refused,
                "stderr": refused,
                "artefact_manifest": refused,
                "verifier_outcome": refused,
                "listed_artefacts": [],
            }
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
        request_timing=request_timing,
        assembly_id=None if assembly is None else assembly.sha256,
        output_records=output_records,
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
    if "open_dispatches" in payload:
        print(f"open dispatches: {payload['open_dispatches']}")
    started_never = payload.get("start_failed")
    if isinstance(started_never, list):
        print(f"start_failed: {len(started_never)}")
        for row in started_never:
            if not isinstance(row, dict):
                continue
            print(
                f"  {row.get('run_id')} ({row.get('harness')}): {row.get('signal')}; "
                f"threshold {row.get('threshold_s')}s, observed "
                f"{row.get('observed_s')}s and {row.get('observed_bytes')} bytes; "
                f"action {row.get('action')}"
            )
    stalled = payload.get("stalled")
    if isinstance(stalled, list):
        print(f"stalled: {len(stalled)}")
        for row in stalled:
            if not isinstance(row, dict):
                continue
            print(
                f"  {row.get('run_id')} ({row.get('harness')}): {row.get('signal')}; "
                f"threshold {row.get('threshold_s')}s, observed "
                f"{row.get('observed_s')}s; action {row.get('action')}"
            )
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


def load_capability_selection(
    inventory_path: str | None, request_path: str | None
) -> dict[str, object] | None:
    """Return the M04 selector result, or None when no capability request was made."""
    if bool(inventory_path) != bool(request_path):
        raise ValueError(
            "--capability-inventory and --capability-request must be passed together"
        )
    if inventory_path is None or request_path is None:
        return None
    try:
        inventory = json.loads(
            Path(inventory_path).resolve().read_text(encoding="utf-8")
        )
        request = json.loads(Path(request_path).resolve().read_text(encoding="utf-8"))
        return select_capabilities(inventory, request)
    except (CapabilityError, json.JSONDecodeError, OSError, UnicodeError) as exc:
        raise ValueError(f"capability context refused: {exc}") from exc


def _task_with_selection(task: str, selection: dict[str, object] | None) -> str:
    if selection is None:
        return task
    encoded = json.dumps(
        selection, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return (
        f"{task.rstrip()}\n\n---\n\n## Selected capability context\n\n"
        f"```json\n{encoded}\n```\n"
    )


def task_with_capabilities(
    task: str,
    inventory_path: str | None,
    request_path: str | None,
) -> str:
    """Select and inject one vendor-neutral per-task capability context."""
    return _task_with_selection(
        task, load_capability_selection(inventory_path, request_path)
    )


def _authorised_log_dir(workspace: Path) -> Path:
    return (workspace / ".harness" / "log").resolve()


def _capture_root_ok(workspace: Path, log_dir: Path) -> bool:
    try:
        return log_dir.resolve() == _authorised_log_dir(workspace)
    except OSError:
        return False


def _record_binding(ref: RecordRef) -> dict[str, object]:
    return {
        "status": "ok",
        "record_id": ref.record_id,
        "digest": ref.digest,
        "byte_count": ref.byte_count,
        "media_type": ref.media_type,
        "object_locator": ref.object_locator,
        "event_id": ref.event_id,
        "event_sha256": ref.event_sha256,
    }


def _capture_source(
    source: Path,
    *,
    workspace: Path,
    media_type: str,
    actor: str = DISPATCH_ACTOR,
) -> dict[str, object]:
    if not source.is_file():
        return {"status": "absent", "reason": f"missing output: {source.name}"}
    try:
        ref = capture_file(
            source,
            workspace_root=workspace,
            object_root=workspace / ".harness" / "objects",
            log_dir=workspace / ".harness" / "log",
            actor=actor,
            media_type=media_type,
            consent_purpose="dispatch-envelope",
            retention_class="project",
        )
    except EventError as exc:
        return {"status": "refused", "reason": str(exc)}
    return _record_binding(ref)


def _refused_capture(reason: str) -> dict[str, object]:
    return {"status": "refused", "reason": reason}


def _capture_run_outputs(
    run_dir: Path, stdout_path: Path, stderr_path: Path, workspace: Path
) -> dict[str, object]:
    manifest_path = run_dir / "artefact-manifest.json"
    verifier_path = run_dir / "verifier-outcome.json"
    listed: list[dict[str, object]] = []
    if manifest_path.is_file():
        listed = _listed_artefact_bindings(manifest_path, workspace)
    return {
        "stdout": _capture_source(
            stdout_path, workspace=workspace, media_type="text/plain"
        ),
        "stderr": _capture_source(
            stderr_path, workspace=workspace, media_type="text/plain"
        ),
        "artefact_manifest": _capture_source(
            manifest_path, workspace=workspace, media_type="application/json"
        ),
        "verifier_outcome": _capture_source(
            verifier_path, workspace=workspace, media_type="application/json"
        ),
        "listed_artefacts": listed,
    }


def _listed_artefact_bindings(
    manifest_path: Path, workspace: Path
) -> list[dict[str, object]]:
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return [{"status": "refused", "reason": "artefact manifest is not valid JSON"}]
    if not isinstance(raw, dict):
        return [{"status": "refused", "reason": "artefact manifest must be an object"}]
    rows = raw.get("artefacts")
    if rows is None:
        return []
    if not isinstance(rows, list):
        return [{"status": "refused", "reason": "artefacts must be a list"}]
    bindings: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            bindings.append(
                {"status": "refused", "reason": f"artefacts[{index}] must be an object"}
            )
            continue
        path_value = row.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            bindings.append(
                {"status": "refused", "reason": f"artefacts[{index}] has no path"}
            )
            continue
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = workspace / path_value
        bindings.append(
            _capture_source(
                candidate, workspace=workspace, media_type="application/octet-stream"
            )
        )
    return bindings


def _record_dispatch_outcome(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    harness: Harness,
    status: str,
    reason: str,
    exit_code: int | None,
    artefact_bytes: int,
    diff_bytes: int,
    timed_out: bool,
    duration_s: float,
    command: Sequence[str],
    assembly_id: str | None = None,
    output_records: Mapping[str, object] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "run_id": run_id,
        "task": task,
        "cwd": cwd,
        "harness": harness.id,
        "family": harness.family,
        "pool": harness.pool,
        "status": status,
        "reason": reason,
        "exit_code": exit_code,
        "artefact_bytes": artefact_bytes,
        "diff_bytes": diff_bytes,
        "timed_out": timed_out,
        "duration_s": duration_s,
        "command": list(command),
        "supervised": True,
    }
    if assembly_id is not None:
        data["assembly_id"] = assembly_id
    if output_records is not None:
        data["output_records"] = dict(output_records)
    recorded = append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": DISPATCH_OUTCOME_KIND,
            "actor": DISPATCH_ACTOR,
            "data": data,
        },
    )
    gap = classify_gap(status, reason)
    if gap is not None:
        failure, closure, repair = gap
        record_gap(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            attempted=harness.id,
            failure=failure,
            detail=reason,
            closure=closure,
            repair=repair,
            source=DISPATCH_OUTCOME_KIND,
        )
    return recorded


def supervise(*, log_dir: Path, runs_dir: Path, as_json: bool) -> int:
    """The scheduled task behind BU-0. One pass, one report, no repair.

    Detection only: N00 reports what died. Delivering that to the principal is BU-7's
    single escalation emitter, and releasing the dead run's lease is BU-3. Until those
    land, a non-zero exit is the whole alert, and saying so is cheaper than implying a
    channel that does not exist.
    """
    now = datetime.now(timezone.utc)
    try:
        events, _rejected = read_all(log_dir)
    except (EventError, OSError) as exc:
        emit({"status": "refused", "reason": f"trajectory unreadable: {exc}"}, as_json)
        return 2
    live = coordination.live_claims(events, now=now)
    for claim in live:
        write_started(runs_dir, claim.run_id, now=now)
    failures = start_failures(live, runs_dir=runs_dir, now=now)
    stalls = stall_failures(live, runs_dir=runs_dir, now=now)
    emit(
        {
            "status": "supervised",
            "open_dispatches": len(live),
            "start_failed": [item.as_dict() for item in failures],
            "stalled": [item.as_dict() for item in stalls],
        },
        as_json,
    )
    return 1 if failures or stalls else 0


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
    native_claim: Mapping[str, object] | None = None,
    capability_selection: Mapping[str, object] | None = None,
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

    try:
        if native_claim is not None:
            claim_event = coordination.claim_ready_work(
                log_dir,
                run_id=run_id,
                cwd=cwd,
                timeout_s=timeout_s,
                ticket=str(native_claim["ticket"]),
                revision=int(native_claim["revision"]),
                attempt_id=str(native_claim.get("attempt_id") or run_id),
                harness=harness.id,
                model=str(native_claim.get("model") or (model or harness.id)),
                family=str(native_claim.get("family") or harness.family),
                pool=str(native_claim.get("pool") or harness.pool),
                capability_context_digest=str(
                    native_claim.get("capability_context_digest") or ("0" * 64)
                ),
                candidate_ordinal=int(native_claim.get("candidate_ordinal") or 1),
                predecessor_bindings=list(
                    native_claim.get("predecessor_bindings") or []
                ),
                task_family=str(native_claim.get("task_family") or ""),
                protocol_id=str(native_claim.get("protocol_id") or ""),
                protocol_version=str(native_claim.get("protocol_version") or ""),
                epsilon=float(native_claim.get("epsilon") or 0.40),
                now=now,
                task=task,
                exposure_state=str(native_claim.get("exposure_state") or "pre_verifier"),
                estimate=native_claim.get("estimate"),  # type: ignore[arg-type]
                estimand_kind=(
                    str(native_claim["estimand_kind"])
                    if native_claim.get("estimand_kind") is not None
                    else None
                ),
                auth_status=(
                    str(native_claim["auth_status"])
                    if native_claim.get("auth_status") is not None
                    else None
                ),
            )
        else:
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
    except coordination.ClaimConflict as exc:
        return _claim_conflict_refusal(
            log_dir=log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            hit=exc.hit,
            live=exc.live,
        )
    except coordination.ClaimReadyError as exc:
        recorded = record_refusal(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=str(cwd),
            reason=str(exc),
            considered=[],
            attempted="native claim",
        )
        return (
            {
                "status": "refused",
                "reason": str(exc),
                "run_id": run_id,
                "cwd": str(cwd),
                "recorded": str(log_dir / f"{ts[:10]}.jsonl"),
                "event": recorded["event"],
            },
            _exit_for("refused"),
        )

    claim_released: bool | str = False
    dispatch_raised = False
    try:
        run_dir = (runs_dir / run_id).resolve()
        isolated = provision_isolated_workspace(
            cwd,
            run_id=run_id,
            dest_root=run_dir / "workspace",
            runtime_id=harness.id,
            runtime_version="unprobed",
        )
        if isinstance(isolated, str):
            result = RunResult(
                harness=harness,
                status="failed",
                reason=isolated,
                exit_code=None,
                stdout="",
                stderr="",
                artefact_bytes=0,
                diff_bytes=0,
                timed_out=False,
                duration_s=0.0,
                command=(),
                run_id=run_id,
                stdout_path="",
                stderr_path="",
            )
            recorded = _record_dispatch_outcome(
                log_dir,
                ts=now_ts(),
                run_id=run_id,
                task=task,
                cwd=str(cwd),
                harness=harness,
                status="failed",
                reason=isolated,
                exit_code=None,
                artefact_bytes=0,
                diff_bytes=0,
                timed_out=False,
                duration_s=0.0,
                command=(),
            )
        else:
            launch_cwd = isolated.work_tree if isolated is not None else cwd
            result = run_harness(
                harness,
                task=task,
                cwd=launch_cwd,
                run_dir=run_dir,
                timeout_s=timeout_s,
                model=model,
                run_id=run_id,
                permissions=permissions,
                log_dir=log_dir,
                in_flight=in_flight,
                in_flight_at_dispatch=len(live),
                family=family,
                pools=pools,
                claim_run_id=run_id,
                max_turns=max_turns,
                max_tokens=max_tokens,
                capability_selection=capability_selection,
                workspace_root=cwd,
            )
            if result.request_timing is not None:
                record_request(
                    log_dir,
                    ts=now_ts(),
                    run_id=result.run_id,
                    harness_id=harness.id,
                    timing=result.request_timing,
                )
            recorded = _record_dispatch_outcome(
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
                assembly_id=result.assembly_id,
                output_records=result.output_records,
            )
            record_dispatch_error(log_dir, result)
            _harvest_quietly(log_dir, runs_dir)
    except BaseException:
        dispatch_raised = True
        raise
    finally:
        # Completion, the terminal outcome event, and expiry are independent releases.
        try:
            coordination.close_claim(log_dir, run_id=run_id)
            claim_released = True
        except EventError as exc:
            if not dispatch_raised:
                claim_released = (
                    f"close failed ({exc}); expiry and the outcome event release it"
                )
        except BaseException:
            if not dispatch_raised:
                raise
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
    capability_selection: Mapping[str, object] | None = None,
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

    try:
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
    except coordination.ClaimConflict as exc:
        return _claim_conflict_refusal(
            log_dir=log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            hit=exc.hit,
            live=exc.live,
        )

    claim_released: bool | str = False
    dispatch_raised = False
    try:
        isolated = provision_isolated_workspace(
            cwd,
            run_id=run_id,
            dest_root=(runs_dir / run_id).resolve() / "workspace",
            runtime_id=decision.first.id,
            runtime_version="unprobed",
        )
        if isinstance(isolated, str):
            recorded = record_refusal(
                log_dir,
                ts=now_ts(),
                run_id=run_id,
                task=task,
                cwd=str(cwd),
                reason=isolated,
                considered=decision.considered,
                attempted="fan-out workspace probe",
            )
            payload = {
                "status": "failed",
                "reason": isolated,
                "run_id": run_id,
                "cwd": str(cwd),
                "recorded": str(log_dir / f"{recorded['ts'][:10]}.jsonl"),
                "event": recorded["event"],
            }
            return payload, _exit_for("failed")
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
                in_flight_at_dispatch=len(live),
                family=family,
                pools=pools,
                # The claim covering both children is the parent's, so the badge the
                # pre-commit gate checks against is the parent's run id.
                claim_run_id=run_id,
                max_turns=max_turns,
                max_tokens=max_tokens,
                capability_selection=capability_selection,
                workspace_root=cwd,
            )
            if result.request_timing is not None:
                record_request(
                    log_dir,
                    ts=now_ts(),
                    run_id=result.run_id,
                    harness_id=harness.id,
                    timing=result.request_timing,
                )
            _record_dispatch_outcome(
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
                assembly_id=result.assembly_id,
                output_records=result.output_records,
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
    except BaseException:
        dispatch_raised = True
        raise
    finally:
        # Completion, the terminal fanout event, and expiry are independent releases.
        try:
            coordination.close_claim(log_dir, run_id=run_id)
            claim_released = True
        except EventError as exc:
            if not dispatch_raised:
                claim_released = (
                    f"close failed ({exc}); expiry and the fanout event release it"
                )
        except BaseException:
            if not dispatch_raised:
                raise
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


# --- ADR-0075 isolated recovery proof ---------------------------------------
# Scratch forward/inverse execution stays in this script boundary, never in the
# AST-locked product package; `consilient.effects` owns the pure verdict and is
# given only observations, never the adapter's own account of what it did.

_PROOF_ESCAPES = {
    "network": "network",
    "credential": "credential",
    "spawn_child": "escaped_child",
}


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _scan_state(root: Path) -> dict[str, str]:
    """Read one tree as a path->text map. Scratch only, so text files only."""

    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _scan_enclosing(enclosing: Path, scratch: Path) -> dict[str, str]:
    """The admitted root minus the declared scope: what must not have moved."""

    return {
        relative: content
        for relative, content in _scan_state(enclosing).items()
        if not (enclosing / relative).is_relative_to(scratch)
    }


class _ProofObserver:
    """The outer sandbox. It records and refuses; the adapter cannot see it."""

    def __init__(self, scratch: Path, enclosing: Path, verifier_policy_digest: str) -> None:
        self.scratch = scratch
        self.enclosing = enclosing
        self.observed_verifier_policy = verifier_policy_digest
        self.escaped: list[str] = []
        self.residuals: list[str] = ["elapsed_time"]
        self.log: list[dict[str, object]] = []

    def _deny(self, kind: str, label: str) -> None:
        self.escaped.append(label)
        self.log.append({"step": kind, "allowed": False, "detail": label})

    def run(self, steps: object) -> str:
        denied = False
        for step in steps if isinstance(steps, Sequence) else ():
            item = step if isinstance(step, Mapping) else {}
            kind = str(item.get("kind", ""))
            if kind == "write":
                target = (self.scratch / str(item.get("path", ""))).resolve()
                if not target.is_relative_to(self.enclosing):
                    self._deny(kind, "out_of_root")
                    denied = True
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(item.get("content", "")), encoding="utf-8")
                self.log.append(
                    {
                        "step": kind,
                        "allowed": True,
                        "detail": target.relative_to(self.enclosing).as_posix(),
                    }
                )
            elif kind == "process":
                residuals = item.get("residuals", ())
                self.residuals.extend(
                    str(name) for name in (residuals if isinstance(residuals, Sequence) else ())
                )
                self.log.append({"step": kind, "allowed": True, "detail": "residual_only"})
            elif kind == "change_verifier_policy":
                self.observed_verifier_policy = str(item.get("digest", ""))
                self.log.append({"step": kind, "allowed": True, "detail": "verifier_policy"})
            elif kind in _PROOF_ESCAPES:
                self._deny(kind, _PROOF_ESCAPES[kind])
                denied = True
            else:
                # ponytail: an unknown step kind fails closed rather than passing.
                self._deny(kind, "unknown_step")
                denied = True
        return "failed" if denied else "succeeded"


def run_isolated_recovery_proof(
    scratch_root: Path,
    verifier_log: Path,
    *,
    identities: Mapping[str, str],
    manifest: EffectManifest,
    start_files: Mapping[str, str],
    adapter: Mapping[str, object],
    sandbox_policy_digest: str,
    verifier_policy_digest: str,
) -> RecoveryProof:
    """Run one scratch-only recovery proof and return the pure verdict.

    The runner is handed a new scratch root and a verifier log and nothing else:
    no live target, network, credential, provider or spend handle is reachable
    from this signature, which is what makes the proof isolated rather than a
    rehearsal against the thing it is meant to protect.
    """

    scratch = Path(scratch_root).resolve()
    enclosing = scratch.parent
    scratch.mkdir(parents=True, exist_ok=True)
    for relative, content in start_files.items():
        seeded = scratch / relative
        seeded.parent.mkdir(parents=True, exist_ok=True)
        seeded.write_text(content, encoding="utf-8")

    start_digest = canonical_state_digest(_scan_state(scratch))
    enclosing_before = canonical_state_digest(_scan_enclosing(enclosing, scratch))

    observer = _ProofObserver(scratch, enclosing, verifier_policy_digest)
    forward_status = observer.run(adapter.get("forward", ()))
    forward_digest = canonical_state_digest(_scan_state(scratch))
    inverse_status = observer.run(adapter.get("inverse", ()))
    end_digest = canonical_state_digest(_scan_state(scratch))
    enclosing_after = canonical_state_digest(_scan_enclosing(enclosing, scratch))

    log_path = Path(verifier_log)
    lines = [json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in observer.log]
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(line + "\n" for line in lines))
    observer_log_digest = hashlib.sha256(log_path.read_bytes()).hexdigest()

    declared_expected = manifest.expected_state
    expected_digest = (
        str(declared_expected.get("commitment", ""))
        if isinstance(declared_expected, Mapping)
        else ""
    )
    # An expected state the manifest never committed to is unmatchable, and
    # `evaluate_recovery_proof` reports it as a capability gap before comparing.
    if len(expected_digest) != 64:
        expected_digest = "0" * 64

    return evaluate_recovery_proof(
        manifest=manifest,
        observation=ProofObservation(
            start_state_digest=start_digest,
            forward_state_digest=forward_digest,
            end_state_digest=end_digest,
            enclosing_before_digest=enclosing_before,
            enclosing_after_digest=enclosing_after,
            expected_state_digest=expected_digest,
            forward_status=forward_status,
            inverse_status=inverse_status,
            sandbox_policy_digest=sandbox_policy_digest,
            verifier_policy_digest=verifier_policy_digest,
            observed_verifier_policy_digest=observer.observed_verifier_policy,
            observer_log_digest=observer_log_digest,
            escaped_attempts=_ordered_unique(observer.escaped),
            observed_residuals=_ordered_unique(observer.residuals),
        ),
        **identities,
    )


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
        "--capability-inventory",
        help="JSON allowlist of available tools, MCPs, skills, plugins and connections",
    )
    parser.add_argument(
        "--capability-request",
        help="JSON capabilities requested for this task; requires --capability-inventory",
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
    parser.add_argument(
        "--heldout-contract",
        help="held-out contract path; refused until dispatch gains real isolation",
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
        "--supervise",
        action="store_true",
        help="report open dispatches that produced no artefact within the start "
        "window, and exit non-zero if there are any. Reads files only; kills nothing.",
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
    if args.supervise:
        # Before anything that probes, refreshes or spends. The party that notices must
        # not be the party that spawned, so this path reads files and nothing else.
        return supervise(
            log_dir=Path(args.log).resolve(),
            runs_dir=Path(args.runs).resolve(),
            as_json=args.json,
        )
    if args.heldout_contract is not None:
        emit(
            {
                "status": "refused",
                "reason": heldout_contract_refusal(args.heldout_contract),
            },
            args.json,
        )
        return 2
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
        capability_selection = load_capability_selection(
            args.capability_inventory, args.capability_request
        )
        task = _task_with_selection(task, capability_selection)
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
            capability_selection=capability_selection,
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
        capability_selection=capability_selection,
    )
    emit(payload, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

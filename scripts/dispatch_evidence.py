"""Turn what a run left behind into evidence, and bind that evidence to the record.

Bytes in the run directory, bytes in the git diff, a commit landed since the claim
opened, the first non-empty line the agent wrote to the path it declared: these are the
observations everything upstream reasons from, and each of them fails closed. A missing
or unreadable directory reads zero, because an absent summary is not a pass (F-09);
absence of git, or of a repository, is not evidence of progress; and dispatcher-written
names never count, because brief.md and recall.md are evidence that we asked, not that
anything answered [measured, N00].

Capture is the other half. The sealed task, the assembled instructions, stdout, stderr,
the artefact manifest and the verifier outcome become content-addressed records bound
into the trajectory — and only when the log directory is the authorised capture root for
that workspace, which is refused in writing rather than skipped in silence. A non-ok
dispatch also emits an error identity carrying no raw task, no command and no exception
text.

The remainder sits here because it reads the same surfaces: locating a grok binary,
refusing grok outright when a metered key is set, injecting a selected capability
context into a task, harvesting the operator log quietly and never a test directory, and
the inert fake sink and receipt payloads that exercise the admitted-effect path without
reaching anything real."""

from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any

import dispatch_vocabulary
from dispatch_supervision import (
    _drain_stream,
)

from dispatch_vocabulary import (
    FakeEffectAdmissionResult,
    GIT_ENV,
    GROK_CANDIDATES,
    METERED_KEY_ENV_VARS,
    ROOT,
    RunResult,
    _ADMITTED_EFFECTS,
    _DISPATCHER_WRITTEN,
    _EFFECT_RECEIPT_STATUSES,
    _authorised_log_dir,
    _broker_reference,
    _dispatch_record_path,
    _keyed_commitment,
    _record_binding,
    _scan_state,
    _task_with_selection,
    load_capability_selection,
    which_binary,
)

__all__ = [
    "FakeEffectAdmissionResult",
    "FakeEffectSink",
    "GIT_ENV",
    "GROK_CANDIDATES",
    "METERED_KEY_ENV_VARS",
    "ROOT",
    "RunResult",
    "_ADMITTED_EFFECTS",
    "_DISPATCHER_WRITTEN",
    "_EFFECT_RECEIPT_STATUSES",
    "_authorised_log_dir",
    "_broker_reference",
    "_dispatch_record_path",
    "_drain_stream",
    "_keyed_commitment",
    "_record_binding",
    "_scan_state",
    "_task_with_selection",
    "artefact_bytes_in",
    "committed_since",
    "find_grok",
    "git_diff_bytes",
    "load_capability_selection",
    "metered_grok_reason",
    "record_dispatch_error",
    "repo_roots",
    "started_line_in",
    "task_with_capabilities",
    "which_binary",
]

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.effects import (
    EFFECT_RECEIPT,
    EffectManifest,
)
from consilient.error_tracking import (
    ErrorRecordError,
    append_record,
    build_record,
)
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    read_all,
)
from consilient.records import capture_file
from consilient.harness import (
    now_ts,
    DISPATCH_ACTOR,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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


def _git_identity_env() -> dict[str, str]:
    env = dict(dispatch_vocabulary.GIT_ENV)
    env.setdefault("GIT_AUTHOR_NAME", "consilient.dispatch")
    env.setdefault("GIT_AUTHOR_EMAIL", "dispatch@consilient.invalid")
    env.setdefault("GIT_COMMITTER_NAME", "consilient.dispatch")
    env.setdefault("GIT_COMMITTER_EMAIL", "dispatch@consilient.invalid")
    return env


def find_grok() -> str | None:
    for name in ("grok", "grok.exe", "grok.cmd"):
        found = which_binary(name)
        if found:
            return found
    for candidate in GROK_CANDIDATES:
        if candidate.exists():
            return str(candidate.resolve())
    return None


def metered_grok_reason(env: dict[str, str] | None = None) -> str | None:
    source = os.environ if env is None else env
    for name in METERED_KEY_ENV_VARS:
        if source.get(name):
            return (
                f"refusing grok: metered key {name} is set; SuperGrok Heavy is the "
                "subscription path and OpenRouter is the only permitted metered vendor"
            )
    return None


def _stream_reader(
    pipe: Any,
    out_path: Path,
    meta: dict[str, Any],
    origin_wall: datetime,
    origin_mono: float,
) -> None:
    n_chunks, t_first, t_first_nonempty = _drain_stream(
        pipe, out_path, origin_wall=origin_wall, origin_mono=origin_mono
    )
    meta["n_chunks"] = n_chunks
    meta["t_first"] = t_first
    meta["t_first_nonempty"] = t_first_nonempty


def _harvest_quietly(log_dir: Path, runs_dir: Path) -> None:
    """Paid dispatch is harvested. Failure here must not change the dispatch status.

    Only the operator log is harvested, never a test tmp directory.
    """
    live = (dispatch_vocabulary.ROOT / ".harness" / "log").resolve()
    try:
        if log_dir.resolve() != live:
            return
        from consilient.harvest import DEFAULT_RELATIVE, HarvestError, harvest

        harvest(
            log_dir=log_dir,
            runs_dir=runs_dir,
            dest=dispatch_vocabulary.ROOT / DEFAULT_RELATIVE,
            root=dispatch_vocabulary.ROOT,
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
            env=dispatch_vocabulary.GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    return len((completed.stdout or "").encode("utf-8"))


def _load_dispatch_record(runs_dir: Path, run_id: str) -> dict[str, object]:
    path = _dispatch_record_path(runs_dir, run_id)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


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
            env=dispatch_vocabulary.GIT_ENV,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return bool((completed.stdout or "").strip())


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


def repo_roots() -> tuple[Path, ...]:
    """This repository's root, plus every git worktree checked out from the same repository.

    `git worktree list` is the only enumeration that stays true when a worktree is added or
    removed; a hard-coded list would drift. If git cannot answer, the answer is ROOT alone,
    which refuses more rather than less.
    """
    roots = [dispatch_vocabulary.ROOT]
    git = which_binary("git")
    if git is not None:
        try:
            completed = subprocess.run(
                [git, "-C", str(dispatch_vocabulary.ROOT), "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env=dispatch_vocabulary.GIT_ENV,
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


def task_with_capabilities(
    task: str,
    inventory_path: str | None,
    request_path: str | None,
) -> str:
    """Select and inject one vendor-neutral per-task capability context."""
    return _task_with_selection(
        task, load_capability_selection(inventory_path, request_path)
    )


def _capture_root_ok(workspace: Path, log_dir: Path) -> bool:
    try:
        return log_dir.resolve() == _authorised_log_dir(workspace)
    except OSError:
        return False


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


def _scan_enclosing(enclosing: Path, scratch: Path) -> dict[str, str]:
    """The admitted root minus the declared scope: what must not have moved."""

    return {
        relative: content
        for relative, content in _scan_state(enclosing).items()
        if not (enclosing / relative).is_relative_to(scratch)
    }


class FakeEffectSink:
    """Inert fake adapter counting how many times reach was invoked."""

    def __init__(self, *, status: str = "succeeded") -> None:
        if status not in _EFFECT_RECEIPT_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_EFFECT_RECEIPT_STATUSES)}"
            )
        self.status = status
        self.invocations = 0

    def invoke(self, manifest: EffectManifest, handle_token: str) -> str:
        if _ADMITTED_EFFECTS.get(handle_token) is not None:
            raise RuntimeError("single-use admission handle already consumed")
        _ADMITTED_EFFECTS[handle_token] = manifest.operation_id
        self.invocations += 1
        return self.status


def _effect_receipt_event(
    *,
    receipt_id: str,
    intent_id: str,
    manifest_digest: str,
    status: str,
    started_at: str,
    ended_at: str,
) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": ended_at,
        "event": EFFECT_RECEIPT,
        "actor": DISPATCH_ACTOR,
        "data": {
            "receipt_id": receipt_id,
            "intent_id": intent_id,
            "manifest_digest": manifest_digest,
            "status": status,
            "started_at": started_at,
            "ended_at": ended_at,
            "provider_request": _broker_reference("provider-request"),
            "provider_receipt": _broker_reference("provider-receipt"),
            "request_commitment": _keyed_commitment("effect.receipt.request"),
            "response_commitment": _keyed_commitment("effect.receipt.response"),
            "content_commitment": _keyed_commitment("effect.receipt.content"),
            "observed_consumption": {"cpu_seconds": 0},
            "post_state": _keyed_commitment("effect.receipt.post_state"),
            "observed_residuals": ("elapsed_time",),
            "child_operation_ids": (),
        },
    }


def _existing_effect_completion(
    log_dir: Path,
    intent_id: str,
) -> FakeEffectAdmissionResult | None:
    events, _rejections = read_all(log_dir)
    for event in events:
        raw = event.raw
        if (
            raw.get("event") == EFFECT_RECEIPT
            and raw.get("data", {}).get("intent_id") == intent_id
        ):
            status = raw["data"]["status"]
            return FakeEffectAdmissionResult(
                status=status,
                receipt_id=raw["data"]["receipt_id"],
                intent_id=intent_id,
                handle_token=None,
            )
    return None

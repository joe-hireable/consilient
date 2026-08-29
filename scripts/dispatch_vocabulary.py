"""The fixed nouns of dispatch: where a thing lives, how long it may take, and what a
result looks like.

The tunables are arguments about cost rather than about mechanism — the default
wall-clock leash, the turn and token ceilings, the default cursor model, the candidate
paths for a grok binary, the metered key names whose presence refuses a grok run
outright, and a git environment scrubbed of every GIT_ variable inherited from the
caller. How long a cursor launch holds the shared-config lock, and how long a waiter
tries, are set here too: the settle window covers cursor-agent reading its config; the
timeout is bounded so a waiter fails in minutes rather than burning an hour-long leash.

The record types are the shapes everything downstream passes around: one run's result,
the stream timing taken while it ran, a proved isolated workspace, and the two errors
raised when a workspace form cannot prove itself or a dispatch declares no progress
artefact.

The helpers are deliberately small and pure — a Windows path translated for WSL, a
version token found in a CLI banner, a status turned into an exit code, a task read from
an argument or a file, a capability selection read from two JSON documents. They refuse
rather than guess: a task given both positionally and by file, a non-positive integer
where a bound is required, and a capability inventory passed without its matching
request are errors, not defaults. A last group builds small payloads by hand — a content
record binding, a refused capture, a broker reference, a keyed commitment, the outcome
event an attempt emits — each a plain mapping, so nothing downstream is handed an object
that could decide on its behalf."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


ROOT = Path(__file__).resolve().parent.parent

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.capabilities import CapabilityError, select_capabilities  # noqa: E402
from consilient.effects import (  # noqa: E402
    EffectManifest,
)
from consilient.events import (  # noqa: E402
    OUTCOME_KIND,
    SCHEMA_VERSION,
)
from consilient.records import RecordRef  # noqa: E402
from consilient.harness import (  # noqa: E402
    DEFAULT_POOLS,
    Harness,
    DISPATCH_ACTOR,
    snapshot_mapping,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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


def to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved).replace("\\", "/")
    if len(text) > 1 and text[1] == ":":
        return f"/mnt/{text[0].lower()}{text[2:]}"
    return text


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


def optional_flags(help_blob: str, *flags: str) -> list[str]:
    chosen: list[str] = []
    blob = f" {help_blob} "
    for flag in flags:
        if f" {flag} " in blob or f" {flag}\n" in help_blob or help_blob.endswith(flag):
            chosen.append(flag)
    return chosen


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


def _dispatch_record_path(runs_dir: Path, run_id: str) -> Path:
    return runs_dir / f"{run_id}.json"


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


RECALL_LIMIT_CHARS = 8000


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def ensure_default_headroom(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot_mapping(DEFAULT_POOLS), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
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


def _authorised_log_dir(workspace: Path) -> Path:
    return (workspace / ".harness" / "log").resolve()


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


def _refused_capture(reason: str) -> dict[str, object]:
    return {"status": "refused", "reason": reason}


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


_ADMITTED_EFFECTS: dict[str, str] = {}

_EFFECT_RECEIPT_STATUSES = frozenset({"succeeded", "failed", "refused", "unknown"})


@dataclass
class FakeEffectAdmissionResult:
    status: str
    receipt_id: str | None
    intent_id: str
    handle_token: str | None


def _broker_reference(name: str) -> dict[str, str]:
    return {
        "kind": "broker_reference",
        "reference": f"broker://effects/{hashlib.sha256(name.encode()).hexdigest()}",
    }


def _keyed_commitment(domain: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": hashlib.sha256(domain.encode()).hexdigest(),
    }


def _attempt_outcome_event(
    manifest: EffectManifest,
    *,
    verifier_accept: bool,
    ts: str,
) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": ts,
        "event": OUTCOME_KIND,
        "actor": DISPATCH_ACTOR,
        "data": {
            "repository": "consilient",
            "attempt_id": manifest.attempt_id,
            "task": manifest.work_item_id,
            "verifier_accept": verifier_accept,
        },
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed

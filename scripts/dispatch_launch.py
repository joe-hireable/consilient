"""Where the harnesses live, and how a child is actually started.

Starting one is deliberately unglamorous. Output goes to files rather than pipes, a
thread drains each stream, and the process tree is killed on timeout because a
subprocess deadline does not reach grandchildren. A caller holding a start-up lock is
handed a callback fired once the child is spawned and its readers are attached, which is
what lets a lock cover start-up instead of the whole run.

Finding one is done by asking rather than assuming. claude, codex and the wsl bridge are
looked up on PATH with the Windows suffixes tried as well; cursor-agent is WSL-only and
is looked for at its known path before the bridge; and a CLI's own --help output is
read, so a flag is applied only where it exists.

The instance paths under .harness/ are named here too — the operator log, the dispatch
run records, the headroom snapshot, the permissions file, the cwd allowlist, the cursor
start-up lock, the skills directory and the held-out isolation checker — together with
the start-window detector that reports an open dispatch which produced nothing at all,
and the single emitter that prints a payload as JSON or as text. The admitted fake
effect also runs from here: intent, one reach and one receipt appended as a transaction,
an already-completed intent returned rather than repeated, and any disposition other
than execute recorded as an intent and then refused."""

from __future__ import annotations
import json
import os
import subprocess
import sys
import time
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any

import dispatch_evidence
import dispatch_vocabulary
from dispatch_evidence import (
    FakeEffectSink,
    _effect_receipt_event,
    _existing_effect_completion,
    _load_dispatch_record,
    _stream_reader,
    artefact_bytes_in,
    committed_since,
    git_diff_bytes,
    started_line_in,
)

from dispatch_supervision import (
    StartFailure,
    _print_human,
    kill_process_tree,
)

from dispatch_vocabulary import (
    CURSOR_WSL_BINARY,
    FakeEffectAdmissionResult,
    ROOT,
    START_WINDOW_S,
    StreamTiming,
    _attempt_outcome_event,
    _run_probe,
    which_binary,
)

__all__ = [
    "CURSOR_WSL_BINARY",
    "DEFAULT_ALLOWED_CWDS",
    "DEFAULT_CURSOR_LOCK",
    "DEFAULT_HEADROOM",
    "DEFAULT_LOG",
    "DEFAULT_PERMISSIONS",
    "DEFAULT_RUNS",
    "DEFAULT_SKILLS",
    "FakeEffectAdmissionResult",
    "FakeEffectSink",
    "HELDOUT_ISOLATION_CHECKER",
    "ROOT",
    "START_WINDOW_S",
    "StartFailure",
    "StreamTiming",
    "_attempt_outcome_event",
    "_effect_receipt_event",
    "_existing_effect_completion",
    "_load_dispatch_record",
    "_print_human",
    "_run_probe",
    "_stream_reader",
    "artefact_bytes_in",
    "committed_since",
    "cursor_native",
    "emit",
    "find_claude",
    "find_codex",
    "git_diff_bytes",
    "help_text",
    "kill_process_tree",
    "run_admitted_fake_effect",
    "run_process",
    "start_failures",
    "started_line_in",
    "which_binary",
    "wsl_bridge",
]

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import coordination
from consilient.effects import (
    EFFECT_INTENT,
    EffectAdmissionRefusal,
    EffectManifest,
    admit_effect,
)
from consilient.events import (
    SCHEMA_VERSION,
    append_transaction,
    read_all,
)
from consilient.harness import (
    DISPATCH_ACTOR,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_LOG = dispatch_vocabulary.ROOT / ".harness" / "log"

DEFAULT_HEADROOM = dispatch_vocabulary.ROOT / ".harness" / "headroom.json"

DEFAULT_RUNS = dispatch_vocabulary.ROOT / ".harness" / "dispatch"

DEFAULT_PERMISSIONS = dispatch_vocabulary.ROOT / ".harness" / "permissions.json"

DEFAULT_ALLOWED_CWDS = dispatch_vocabulary.ROOT / ".harness" / "allowed-cwds.json"

DEFAULT_CURSOR_LOCK = dispatch_vocabulary.ROOT / ".harness" / "cursor-agent.lock"

DEFAULT_SKILLS = dispatch_vocabulary.ROOT / ".agents" / "skills"

HELDOUT_ISOLATION_CHECKER = (
    dispatch_vocabulary.ROOT / ".github" / "scripts" / "check_heldout_isolation.py"
)


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


def help_text(argv_head: list[str]) -> str:
    code, out, err = _run_probe([*argv_head, "--help"], timeout_s=15)
    if code != 0 and not out:
        return err
    return out


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
    origin_wall = datetime.now(timezone.utc)
    t_send = origin_wall.isoformat()
    origin_mono = started
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
        args=(process.stdout, stdout_path, stdout_meta, origin_wall, origin_mono),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_stream_reader,
        args=(process.stderr, stderr_path, stderr_meta, origin_wall, origin_mono),
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
    n_chunks = int(stdout_meta.get("n_chunks", 0))
    t_first = stdout_meta.get("t_first")
    t_first_nonempty = stdout_meta.get("t_first_nonempty")
    if not isinstance(t_first, str):
        t_first = t_send
    if not isinstance(t_first_nonempty, str):
        t_first_nonempty = t_first
    timing = StreamTiming(
        t_send=t_send,
        t_first_chunk=t_first,
        t_first_nonempty_chunk=t_first_nonempty,
        n_chunks=n_chunks,
    )
    return process.returncode, timed_out, time.perf_counter() - started, timing


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
                    # MEASURED, not 0. This was the literal `0`, and build_driver prints the
                    # field as "(N bytes after Ns)" -- so eleven dispatches on 29 August 2026
                    # were reported as "0 bytes after 1160s" while their run directories held
                    # 1.6 MB of stderr and a finished report. The signal is that no STARTED
                    # LINE was found, which is a different and much narrower claim than "the
                    # run produced nothing", and reporting a constant as an observation sent
                    # the investigation looking for a dead harness that was not dead.
                    observed_bytes=artefact_bytes_in(runs_dir / claim.run_id),
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
            dispatch_evidence.git_diff_bytes(tree) > 0
            or committed_since(tree, claim.opened_at)
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


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    _print_human(payload)


def run_admitted_fake_effect(
    log_dir: Path,
    *,
    manifest: EffectManifest,
    disposition: str,
    sink: FakeEffectSink,
    intent_id: str,
    receipt_id: str,
    observation_id: str | None = None,
    decision_event: dict[str, object] | None = None,
    proposal_event: dict[str, object] | None = None,
    authority_event: dict[str, object] | None = None,
) -> FakeEffectAdmissionResult:
    """Atomically admit one fake effect: intent, one reach, receipt, outcome."""

    existing = _existing_effect_completion(log_dir, intent_id)
    if existing is not None:
        return existing

    prefix_events, _rejections = read_all(log_dir)
    planned_disposition = "refused" if disposition == "refuse" else disposition
    planned = admit_effect(
        manifest,
        disposition=planned_disposition,
        prefix=prefix_events,
        intent_id=intent_id,
        receipt_id=receipt_id,
        observation_id=observation_id,
        decision_event=decision_event,
        proposal_event=proposal_event,
        authority_event=authority_event,
    )
    if isinstance(planned, EffectAdmissionRefusal):
        return FakeEffectAdmissionResult(
            status="refused",
            receipt_id=None,
            intent_id=intent_id,
            handle_token=None,
        )

    if planned_disposition != "execute":
        intent_payload = {
            "v": SCHEMA_VERSION,
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": EFFECT_INTENT,
            "actor": DISPATCH_ACTOR,
            "data": planned.intent_data,
        }
        append_transaction(log_dir, [intent_payload], lambda p, r, c: None)
        return FakeEffectAdmissionResult(
            status="refused",
            receipt_id=None,
            intent_id=intent_id,
            handle_token=None,
        )

    intent_payload = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": EFFECT_INTENT,
        "actor": DISPATCH_ACTOR,
        "data": planned.intent_data,
    }
    append_transaction(log_dir, [intent_payload], lambda p, r, c: None)

    started = datetime.now(timezone.utc).isoformat()
    reach_status = sink.invoke(manifest, planned.handle_token)
    ended = datetime.now(timezone.utc).isoformat()
    receipt = _effect_receipt_event(
        receipt_id=receipt_id,
        intent_id=intent_id,
        manifest_digest=planned.manifest_digest,
        status=reach_status,
        started_at=started,
        ended_at=ended,
    )
    outcome = _attempt_outcome_event(
        manifest,
        verifier_accept=reach_status == "succeeded",
        ts=ended,
    )
    append_transaction(log_dir, [receipt, outcome], lambda p, r, c: None)
    return FakeEffectAdmissionResult(
        status=reach_status,
        receipt_id=receipt_id,
        intent_id=intent_id,
        handle_token=planned.handle_token,
    )

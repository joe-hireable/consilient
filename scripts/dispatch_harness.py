"""Run one harness end to end, and let the artefact decide what happened.

The order is the whole of it. Build the argv and return a refusal if it cannot be built;
assemble the instruction layers and seal the task; write the brief; refuse a held-out
contract before the child is launched rather than after; write the expected record;
spawn. A cursor run takes the shared-config lock for start-up only and releases it once
the child has settled, because an hour-long exclusive hold to guard a file written
perhaps weekly is a scope error, not a safety measure.

What comes back is judged by what it left, never by how it exited. Stdout and stderr are
read from disk, the git diff is measured, and the status is classified from those bytes
together with the exit code and the timeout flag, so a harness that exits 0 having done
nothing is not a success. The held-out contract is audited afterwards as well, and an
audit refusal voids the transcript it was measuring rather than reporting it.

The child's environment is narrowed rather than inherited: every GIT_ variable is
dropped, bytecode writing is off, and a grok run gets its own GROK_HOME inside the run
directory with the claude-compatibility surfaces disabled — so a dispatch cannot quietly
pick up state from the machine it happens to be running on."""

from __future__ import annotations
import sys
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient import instructions
from consilient.harness import (
    DEFAULT_PERMISSION_MODE,
    Harness,
    PermissionMode,
    PoolState,
    classify_artefact,
    build_request_timing,
    extract_usage_from_output,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_boundaries
import dispatch_evidence
import dispatch_invocation
import dispatch_launch
import dispatch_preflight
import dispatch_supervision
import dispatch_vocabulary
from dispatch_supervision import (
    ExclusiveFileLock,
)

from dispatch_boundaries import (
    heldout_contract_audit,
)

from dispatch_evidence import (
    _capture_root_ok,
    _capture_source,
    git_diff_bytes,
)

from dispatch_invocation import (
    build_command,
    heldout_contract_refusal,
)

from dispatch_launch import (
    DEFAULT_CURSOR_LOCK,
    DEFAULT_SKILLS,
    run_process,
)

from dispatch_preflight import (
    write_brief,
)

from dispatch_progress import (
    _capture_run_outputs,
    write_expected,
    write_started,
    write_terminal,
)


from dispatch_vocabulary import (
    CURSOR_START_LOCK_TIMEOUT_S,
    CURSOR_START_SETTLE_S,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_TURNS,
    GIT_ENV,
    RunResult,
    StreamTiming,
    _read,
    _refused_capture,
)

__all__ = [
    "CURSOR_START_LOCK_TIMEOUT_S",
    "CURSOR_START_SETTLE_S",
    "DEFAULT_CURSOR_LOCK",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_TURNS",
    "DEFAULT_SKILLS",
    "ExclusiveFileLock",
    "GIT_ENV",
    "RunResult",
    "StreamTiming",
    "_capture_root_ok",
    "_capture_run_outputs",
    "_capture_source",
    "_read",
    "_refused_capture",
    "build_command",
    "git_diff_bytes",
    "heldout_contract_audit",
    "heldout_contract_refusal",
    "run_harness",
    "run_process",
    "write_brief",
    "write_expected",
    "write_started",
    "write_terminal",
]


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
    heldout_contract: str | None = None,
    claims: tuple[str, ...] = (),
) -> RunResult:
    cwd = cwd.resolve()
    run_dir = run_dir.resolve()
    brief = (run_dir / "brief.md").resolve()
    stdout_path = (run_dir / "stdout.txt").resolve()
    stderr_path = (run_dir / "stderr.txt").resolve()
    built = dispatch_invocation.build_command(
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
            dispatch_launch.DEFAULT_SKILLS,
            log_dir,
            task=task,
            capability_selection=capability_selection,
        )
        capture_ok = _capture_root_ok(capture_workspace, log_dir)
        sealed_task = run_dir / "sealed-task.txt"
        assembled_instructions = run_dir / "assembled-instructions.txt"
        sealed_task.parent.mkdir(parents=True, exist_ok=True)
        sealed_task.write_text(task, encoding="utf-8", newline="\n")
        assembled_instructions.write_text(assembly.text, encoding="utf-8", newline="\n")
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
    dispatch_preflight.write_brief(
        run_dir,
        task,
        log_dir=log_dir,
        in_flight=in_flight,
        claim_run_id=claim_run_id,
        assembly=assembly,
    )
    if heldout_contract is not None:
        refusal: str | None
        try:
            final_brief = brief.read_text(encoding="utf-8")
        except OSError:
            refusal = (
                "held-out final brief is unavailable; refusing before child launch"
            )
        else:
            refusal = dispatch_invocation.heldout_contract_refusal(
                heldout_contract,
                brief=final_brief,
                worktree=str(cwd),
                claims=claims,
            )
        if refusal is not None:
            return RunResult(
                harness=harness,
                status="refused",
                reason=refusal,
                exit_code=None,
                stdout="",
                stderr="",
                artefact_bytes=0,
                diff_bytes=0,
                timed_out=False,
                duration_s=0.0,
                command=tuple(built),
                run_id=run_id,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
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
    env = dict(dispatch_vocabulary.GIT_ENV)
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
            lock = dispatch_supervision.ExclusiveFileLock(
                dispatch_launch.DEFAULT_CURSOR_LOCK, timeout_s=dispatch_vocabulary.CURSOR_START_LOCK_TIMEOUT_S
            )
            lock.__enter__()
            released = False

            def _release_after_start() -> None:
                nonlocal released
                if released:
                    return
                time.sleep(dispatch_vocabulary.CURSOR_START_SETTLE_S)
                released = True
                lock.__exit__(None, None, None)

            try:
                code, timed_out, duration, stream_timing = dispatch_launch.run_process(
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
            code, timed_out, duration, stream_timing = dispatch_launch.run_process(
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
    diff_bytes = dispatch_evidence.git_diff_bytes(cwd)
    status, reason = classify_artefact(
        exit_code=code,
        stdout=stdout,
        stderr=stderr,
        output_bytes=artefact_bytes,
        diff_bytes=diff_bytes,
        timed_out=timed_out,
    )
    if heldout_contract is not None:
        audit = dispatch_boundaries.heldout_contract_audit(
            heldout_contract,
            run_dir=run_dir,
            run_id=run_id,
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
        )
        if audit is not None:
            status, reason = "refused", audit
            stdout = ""
            stderr = ""
            artefact_bytes = 0
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

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

Never silently spends the exhausted pool. A harness that exits 0 having done nothing is
recorded `silent` and is not retried on another pool.

The work below the command line now sits in siblings in this directory, each importing
only those beneath it: `dispatch_vocabulary.py` (tunables, result types, small pure
readers), `dispatch_supervision.py` (the start-up lock, the process-tree kill, the
start-failure and stall records, the human report and the outcome event),
`dispatch_preflight.py` (the brief, the native caps, the git work-tree questions and the
pre-launch refusals), `dispatch_evidence.py` (artefact and diff measurement, and record
capture), `dispatch_launch.py` (the instance paths, binary discovery and the spawn),
`dispatch_boundaries.py` (the cwd allowlist, the held-out audit, the isolated recovery
proof and the argument parser), `dispatch_invocation.py` (per-harness argv and the CLI
probes), `dispatch_progress.py` (the expected, started and terminal records, cwd
resolution and the headroom refresh), `dispatch_harness.py` (one harness run end to
end), `dispatch_workspace.py` (the workspace ladder, the installed-harness probe and the
supervision pass), and `dispatch_single.py` and `dispatch_fanout.py` (the one-harness
and two-family dispatches). This file keeps the command line."""

from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))


import dispatch_invocation
import dispatch_progress
import dispatch_single
import dispatch_vocabulary
import dispatch_workspace
from dispatch_boundaries import (
    _cursor_help_and_about,
    _listed_artefact_bindings,
    build_parser,
    heldout_contract_audit,
    load_allowed_roots,
    run_isolated_recovery_proof,
)

from dispatch_evidence import (
    FakeEffectSink,
    _capture_root_ok,
    _capture_source,
    _effect_receipt_event,
    _existing_effect_completion,
    _git_identity_env,
    _harvest_quietly,
    _load_dispatch_record,
    _result_payload,
    _scan_enclosing,
    _stream_reader,
    artefact_bytes_in,
    committed_since,
    find_grok,
    git_diff_bytes,
    metered_grok_reason,
    record_dispatch_error,
    repo_roots,
    started_line_in,
    task_with_capabilities,
)

from dispatch_fanout import (
    dispatch_fanout,
)

from dispatch_harness import (
    run_harness,
)

from dispatch_invocation import (
    _probe_read_write_stage_commit,
    _progressed_after_start,
    _run_git,
    _store_dispatch_field,
    build_command,
    heldout_contract_refusal,
    probe_claude,
    probe_codex,
    probe_grok,
    wsl_git_exports,
)

from dispatch_launch import (
    DEFAULT_ALLOWED_CWDS,
    DEFAULT_CURSOR_LOCK,
    DEFAULT_HEADROOM,
    DEFAULT_LOG,
    DEFAULT_PERMISSIONS,
    DEFAULT_RUNS,
    DEFAULT_SKILLS,
    HELDOUT_ISOLATION_CHECKER,
    cursor_native,
    emit,
    find_claude,
    find_codex,
    help_text,
    run_admitted_fake_effect,
    run_process,
    start_failures,
    wsl_bridge,
)

from dispatch_preflight import (
    _ProofObserver,
    _claim_conflict_refusal,
    git_workspace,
    inspect_uncommitted_tracked,
    native_cap_flags,
    write_brief,
)

from dispatch_progress import (
    _capture_run_outputs,
    _materialise_workspace_form,
    probe_cursor,
    refresh_default_headroom,
    resolve_cwd,
    stall_failures,
    workspace_index_path,
    write_expected,
    write_started,
    write_terminal,
)

from dispatch_single import (
    dispatch_one,
)

from dispatch_supervision import (
    ExclusiveFileLock,
    Stall,
    StartFailure,
    _drain_stream,
    _print_human,
    _record_dispatch_outcome,
    kill_process_tree,
)

from dispatch_vocabulary import (
    CURSOR_START_LOCK_TIMEOUT_S,
    CURSOR_START_SETTLE_S,
    CURSOR_WSL_BINARY,
    DEFAULT_CURSOR_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_TURNS,
    DEFAULT_TIMEOUT_S,
    ExpectedArtefactError,
    FakeEffectAdmissionResult,
    GIT_ENV,
    GROK_CANDIDATES,
    IsolatedWorkspace,
    METERED_KEY_ENV_VARS,
    RECALL_LIMIT_CHARS,
    ROOT,
    RunResult,
    START_WINDOW_S,
    StreamTiming,
    WORKSPACE_FORMS,
    WorkspaceProbeError,
    _ADMITTED_EFFECTS,
    _DISPATCHER_WRITTEN,
    _EFFECT_RECEIPT_STATUSES,
    _PROOF_ESCAPES,
    _attempt_outcome_event,
    _authorised_log_dir,
    _broker_reference,
    _dispatch_record_path,
    _exit_for,
    _keyed_commitment,
    _nonempty_line_count,
    _ordered_unique,
    _read,
    _record_binding,
    _refused_capture,
    _run_probe,
    _scan_state,
    _task_with_selection,
    _version_from,
    ensure_default_headroom,
    load_capability_selection,
    load_task,
    optional_flags,
    positive_int,
    to_wsl_path,
    which_binary,
)

from dispatch_workspace import (
    probe_all,
    probe_workspace_form,
    provision_isolated_workspace,
    supervise,
)

__all__ = [
    "CURSOR_START_LOCK_TIMEOUT_S",
    "CURSOR_START_SETTLE_S",
    "CURSOR_WSL_BINARY",
    "DEFAULT_ALLOWED_CWDS",
    "DEFAULT_CURSOR_LOCK",
    "DEFAULT_CURSOR_MODEL",
    "DEFAULT_HEADROOM",
    "DEFAULT_LOG",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_TURNS",
    "DEFAULT_PERMISSIONS",
    "DEFAULT_RUNS",
    "DEFAULT_SKILLS",
    "DEFAULT_TIMEOUT_S",
    "ExclusiveFileLock",
    "ExpectedArtefactError",
    "FakeEffectAdmissionResult",
    "FakeEffectSink",
    "GIT_ENV",
    "GROK_CANDIDATES",
    "HELDOUT_ISOLATION_CHECKER",
    "IsolatedWorkspace",
    "METERED_KEY_ENV_VARS",
    "RECALL_LIMIT_CHARS",
    "ROOT",
    "RunResult",
    "START_WINDOW_S",
    "Stall",
    "StartFailure",
    "StreamTiming",
    "WORKSPACE_FORMS",
    "WorkspaceProbeError",
    "_ADMITTED_EFFECTS",
    "_DISPATCHER_WRITTEN",
    "_EFFECT_RECEIPT_STATUSES",
    "_PROOF_ESCAPES",
    "_ProofObserver",
    "_attempt_outcome_event",
    "_authorised_log_dir",
    "_broker_reference",
    "_capture_root_ok",
    "_capture_run_outputs",
    "_capture_source",
    "_claim_conflict_refusal",
    "_cursor_help_and_about",
    "_dispatch_record_path",
    "_drain_stream",
    "_effect_receipt_event",
    "_existing_effect_completion",
    "_exit_for",
    "_git_identity_env",
    "_harvest_quietly",
    "_keyed_commitment",
    "_listed_artefact_bindings",
    "_load_dispatch_record",
    "_materialise_workspace_form",
    "_nonempty_line_count",
    "_ordered_unique",
    "_print_human",
    "_probe_read_write_stage_commit",
    "_progressed_after_start",
    "_read",
    "_record_binding",
    "_record_dispatch_outcome",
    "_refused_capture",
    "_result_payload",
    "_run_git",
    "_run_probe",
    "_scan_enclosing",
    "_scan_state",
    "_store_dispatch_field",
    "_stream_reader",
    "_task_with_selection",
    "_version_from",
    "artefact_bytes_in",
    "build_command",
    "build_parser",
    "committed_since",
    "cursor_native",
    "dispatch_fanout",
    "dispatch_one",
    "emit",
    "ensure_default_headroom",
    "find_claude",
    "find_codex",
    "find_grok",
    "git_diff_bytes",
    "git_workspace",
    "heldout_contract_audit",
    "heldout_contract_refusal",
    "help_text",
    "inspect_uncommitted_tracked",
    "kill_process_tree",
    "load_allowed_roots",
    "load_capability_selection",
    "load_task",
    "main",
    "metered_grok_reason",
    "native_cap_flags",
    "optional_flags",
    "positive_int",
    "probe_all",
    "probe_claude",
    "probe_codex",
    "probe_cursor",
    "probe_grok",
    "probe_workspace_form",
    "provision_isolated_workspace",
    "record_dispatch_error",
    "refresh_default_headroom",
    "repo_roots",
    "resolve_cwd",
    "run_admitted_fake_effect",
    "run_harness",
    "run_isolated_recovery_proof",
    "run_process",
    "stall_failures",
    "start_failures",
    "started_line_in",
    "supervise",
    "task_with_capabilities",
    "to_wsl_path",
    "which_binary",
    "workspace_index_path",
    "write_brief",
    "write_expected",
    "write_started",
    "write_terminal",
    "wsl_bridge",
    "wsl_git_exports",
]

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.harness import (
    HARNESSES,
    PermissionMode,
    PoolState,
    describe_registry,
    harness_by_id,
    headroom_freshness_refusal,
    load_permission_mode,
    load_pools,
    select,
    select_fanout,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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
    try:
        cwd = dispatch_progress.resolve_cwd(args.cwd)
    except ValueError as exc:
        # Before anything else, and before --dry-run can print a command that names
        # another repository. A refused boundary must not leave a runnable artefact.
        emit({"status": "refused", "reason": str(exc)}, args.json)
        return 2
    task: str | None = None
    if args.heldout_contract is not None:
        if not args.probe:
            try:
                task = dispatch_vocabulary.load_task(args.task, args.task_file)
                capability_selection = load_capability_selection(
                    args.capability_inventory, args.capability_request
                )
                task = _task_with_selection(task, capability_selection)
            except ValueError as exc:
                emit({"status": "refused", "reason": str(exc)}, args.json)
                return 2
        refusal = dispatch_invocation.heldout_contract_refusal(
            args.heldout_contract,
            brief=task or "",
            worktree=str(cwd),
            claims=tuple(args.claim or ()),
        )
        if refusal is not None:
            emit({"status": "refused", "reason": refusal}, args.json)
            return 2
    log_dir = Path(args.log).resolve()
    runs_dir = Path(args.runs).resolve()
    headroom_path = Path(args.headroom).resolve()
    refresh_refusal = dispatch_progress.refresh_default_headroom(headroom_path)
    if refresh_refusal is not None:
        emit({"status": "refused", "reason": refresh_refusal}, args.json)
        return 2
    dispatch_vocabulary.ensure_default_headroom(headroom_path)
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

    probes = dispatch_workspace.probe_all()
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

    if task is None:
        try:
            task = dispatch_vocabulary.load_task(args.task, args.task_file)
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
            heldout_contract=args.heldout_contract,
        )
        emit(payload, args.json)
        return code

    decision = select(
        probes=probes,
        pools=pools,
        requested=args.harness,
        allow_exhausted=args.allow_exhausted,
    )
    payload, code = dispatch_single.dispatch_one(
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
        heldout_contract=args.heldout_contract,
    )
    emit(payload, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

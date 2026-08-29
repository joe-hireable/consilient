"""One task, one selected harness, one claim, one record.

A refusal from selection is recorded before anything else happens, together with the
harnesses that were considered, so a dispatch that never ran is as legible afterwards as
one that did. A dry run writes the brief and shows the command that would have been
used; it takes no lock and spends nothing. Otherwise a claim is opened over the declared
paths, the harness runs, the outcome and any request timing are recorded, and the claim
is closed — while a claim overlapping a live one is refused instead, because two agents
admitted to the same path is the failure the coordination record exists to prevent.

Never silently spends the exhausted pool. A harness that exits 0 having done nothing is
recorded `silent` and is not retried on another pool."""

from __future__ import annotations
import sys
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

from consilient import coordination
from consilient.events import (
    EventError,
    read_all,
)
from consilient.harness import (
    DEFAULT_PERMISSION_MODE,
    Decision,
    PermissionMode,
    PoolState,
    make_run_id,
    now_ts,
    parse_status,
    record_refusal,
    record_request,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_harness
import dispatch_invocation
import dispatch_preflight
import dispatch_workspace
from dispatch_supervision import (
    _record_dispatch_outcome,
)

from dispatch_evidence import (
    _harvest_quietly,
    _result_payload,
    record_dispatch_error,
)

from dispatch_harness import (
    run_harness,
)

from dispatch_invocation import (
    build_command,
    heldout_contract_refusal,
)

from dispatch_preflight import (
    _claim_conflict_refusal,
    write_brief,
)


from dispatch_vocabulary import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MAX_TURNS,
    RunResult,
    _exit_for,
)

from dispatch_workspace import (
    provision_isolated_workspace,
)

__all__ = [
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_TURNS",
    "RunResult",
    "_claim_conflict_refusal",
    "_exit_for",
    "_harvest_quietly",
    "_record_dispatch_outcome",
    "_result_payload",
    "build_command",
    "dispatch_one",
    "heldout_contract_refusal",
    "provision_isolated_workspace",
    "record_dispatch_error",
    "run_harness",
    "write_brief",
]


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
    heldout_contract: str | None = None,
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
        brief = dispatch_preflight.write_brief(
            (runs_dir / run_id).resolve(),
            task,
            log_dir=log_dir,
            in_flight=in_flight,
            claim_run_id=run_id,
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
                return {"status": "refused", "reason": refusal}, _exit_for("refused")
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
                exposure_state=str(
                    native_claim.get("exposure_state") or "pre_verifier"
                ),
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
        isolated = dispatch_workspace.provision_isolated_workspace(
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
            result = dispatch_harness.run_harness(
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
                heldout_contract=heldout_contract,
                claims=claims,
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

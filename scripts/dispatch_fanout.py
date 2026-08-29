"""The same task to two harnesses from two different families, and a verdict on whether
they agree.

Fan-out exists to buy a second class of evidence, not a second opinion. Selection
refuses unless two families are available, both children carry the same caps and the
same brief, and the recorded event names the distinct evidence class each arm
contributes — agreement between arms that share everything is echo, and echo is not a
test. The verdict is agreement, disagreement or incomparability, and it is reported
rather than resolved.

One claim covers the pair: opened before either child starts and released once both have
finished, with the release itself recorded — including the case where closing fails and
expiry and the fan-out event are left to release it. A refusal, whether for want of a
second family, an unbuildable command or an overlapping live claim, is recorded exactly
as an outcome is. The exit code carries the worse of the two statuses, so a caller
cannot mistake a half-failed fan-out for a success."""

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
    FanoutDecision,
    PermissionMode,
    PoolState,
    judge_fanout,
    make_run_id,
    now_ts,
    parse_status,
    record_fanout,
    record_refusal,
    record_request,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import dispatch_harness
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

from dispatch_preflight import (
    _claim_conflict_refusal,
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
    "dispatch_fanout",
    "provision_isolated_workspace",
    "record_dispatch_error",
    "run_harness",
]


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
    heldout_contract: str | None = None,
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
        isolated = dispatch_workspace.provision_isolated_workspace(
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
            result = dispatch_harness.run_harness(
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

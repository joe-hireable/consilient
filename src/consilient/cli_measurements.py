"""What the trajectory says, before anything decides whether it is enough.

`record` appends one validated event, `usage` reports every configured provider's quota,
ceiling and spend, and `beta` computes the rate at which the verifier accepted a bad
artefact. `beta` carries the parser and relational quarantines beside the figure rather
than under it: beta is a rate over a denominator, so a log that quietly refused lines
would otherwise inflate exactly the false confidence this project exists to measure.
`usage` writes to the trajectory only on `--record`, because a dashboard polling it must
not append a line every time somebody looks at the page.

`trajectory_state` separates a missing log directory from one that exists and holds
nothing. They are different answers, and collapsing them lets a command report an empty
result about a directory that was never there. `_experiment_entry` and
`_fallback_result` read a recorded measurement out of the experiment register and the
dated fallback result; `_condition` and `_gate` give a verdict its requirement, its
reason and its evidence. Neither decides a gate. They hold the shape a condition must
fill, so the layer that computes conditions cannot report a status without also saying
what the status was measured against.

`_fallback_result` refuses a result that is undated, stale beyond two cycles of the
weekly schedule, or recorded against a command or runner other than the documented ones
-- and its limit is stated rather than hidden: it stops schema drift, partial hand-typed
JSON and arbitrary unexecuted strings, not a deliberate forgery of the runner's exact
output shape."""

from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from . import beta as beta_mod
from . import budget
from . import projection
from . import usage as usage_mod
from .events import EventError, append, read_all
from .cli_replay import (
    CommandResult,
    DEFAULT_DASHBOARD,
    DEFAULT_DB,
    DEFAULT_LOG,
    EXPECTED_FALLBACK_COMMAND,
    EXPERIMENT_REGISTER,
    FALLBACK_MAX_AGE_DAYS,
    FALLBACK_RESULT,
    FALLBACK_RUNNER_IDENTITY,
    HISTORICAL_REFUSAL_DIGESTS,
    READ_TRAJECTORY_COMMANDS,
    REQUIREMENTS,
    THIS_REPOSITORIES,
    TrajectoryState,
    _PACKAGE,
    _read_text,
)


__all__ = [
    "CAPTURE_REFUSAL_BASELINE",
    "CODE_TREE",
    "CommandResult",
    "DEFAULTS",
    "DEFAULT_DASHBOARD",
    "DEFAULT_DB",
    "DEFAULT_LOG",
    "EXPECTED_FALLBACK_COMMAND",
    "EXPERIMENT_REGISTER",
    "FALLBACK_MAX_AGE_DAYS",
    "FALLBACK_RESULT",
    "FALLBACK_RUNNER_IDENTITY",
    "HISTORICAL_REFUSAL_DIGESTS",
    "READ_TRAJECTORY_COMMANDS",
    "REQUIREMENTS",
    "THIS_REPOSITORIES",
    "TrajectoryState",
    "_PACKAGE",
    "_read_text",
    "cmd_beta",
    "cmd_record",
    "cmd_usage",
    "is_this_repository",
    "trajectory_state",
]

CODE_TREE = _PACKAGE.parents[1] if _PACKAGE.parent.name == "src" else _PACKAGE

CAPTURE_REFUSAL_BASELINE = len(HISTORICAL_REFUSAL_DIGESTS)


def trajectory_state(log: Path) -> TrajectoryState:
    """Distinguish a missing log directory from one that exists but holds no events."""
    resolved = log.resolve()
    if resolved.exists() and not resolved.is_dir():
        return "missing"
    if not resolved.is_dir():
        return "missing"
    if any(resolved.glob("*.jsonl")):
        events, rejected = read_all(resolved)
        if events or rejected:
            return "present"
        return "empty"
    return "empty"


def _command_needs_trajectory(args: argparse.Namespace) -> bool:
    if args.command in READ_TRAJECTORY_COMMANDS:
        return True
    if args.command == "usage" and not args.fake and not args.record:
        return True
    return False


def _trajectory_line(result: CommandResult) -> str:
    traj = result.get("trajectory_source")
    if not isinstance(traj, dict):
        return ""
    path = str(traj.get("path", ""))
    state = traj.get("state")
    if state == "empty":
        return f"trajectory: {path} (empty — zero events recorded here, not a missing directory)"
    if state == "present":
        return f"trajectory: {path}"
    return f"trajectory: {path}" if path else ""


def cmd_record(args: argparse.Namespace) -> CommandResult:
    try:
        event = json.loads(args.event)
    except json.JSONDecodeError as exc:
        raise EventError(f"--event is not valid JSON: {exc}") from exc
    path = Path(args.log) / f"{event.get('ts', '')[:10]}.jsonl"
    append(path, event)
    return {"recorded": True, "file": str(path), "event": event["event"]}


def cmd_usage(args: argparse.Namespace) -> CommandResult:
    """Every configured provider's usage, limits and spend in one place.

    Read-only by default. `--record` puts the snapshot in the trajectory through
    `append()`, which is opt-in because a dashboard polling this command must not write a
    line every time somebody looks at it.
    """
    sources = usage_mod.Sources(payloads=Path(args.payloads), log=Path(args.log))
    snapshot = usage_mod.fake_snapshot() if args.fake else usage_mod.snapshot(sources)
    limits = usage_mod.load_limits(Path(args.limits))
    if isinstance(limits, budget.BudgetRefusal):
        snapshot["ceilings"] = {
            "configured": False,
            "refusal": limits.reason,
            "limits": [],
        }
    else:
        snapshot["ceilings"] = {
            "configured": True,
            "refusal": None,
            "limits": [
                {
                    "period": ceiling.period,
                    "amount": str(ceiling.amount),
                    "currency": ceiling.currency,
                }
                for ceiling in limits
            ],
        }
    snapshot["recorded"] = (
        usage_mod.record(Path(args.log), snapshot)
        if args.record and not args.fake
        else 0
    )
    return snapshot


def cmd_beta(args: argparse.Namespace) -> CommandResult:
    conn = projection.build(Path(args.log), Path(args.db))
    try:
        result = beta_mod.from_connection(conn, args.task_family, args.verifier_version)
        parser_quarantined = projection.rejection_count(conn)
        rejection_reasons = projection.rejections(conn)
        relational = projection.relational_quarantines(conn)
        sampling = projection.sampling_unconditioned(conn)
    finally:
        conn.close()
    # β is a rate over a denominator, so anything the log refused has to be visible
    # wherever the rate is. A β computed over a quietly shortened log is exactly the false
    # confidence this project exists to measure. The count stays for callers that already
    # read it; the reasons are the thing that used to be pooled into that integer.
    return {
        **result.as_dict(),
        "quarantined": parser_quarantined,
        "rejection_reasons": rejection_reasons,
        "relational_quarantine_count": len(relational),
        "relational_quarantine": relational,
        "sampling_unconditioned": sampling,
    }


def _condition(
    identifier: str, status: str, reason: str, *evidence: str
) -> CommandResult:
    return {
        "id": identifier,
        "requirement": REQUIREMENTS[identifier],
        "status": status,
        "reason": reason,
        "evidence": list(evidence),
    }


def _experiment_entry(identifier: str) -> tuple[str | None, str]:
    text = _read_text(EXPERIMENT_REGISTER)
    match = re.search(
        rf"(?ms)^### {re.escape(identifier)}\b.*?(?=^### |\Z)", text or ""
    )
    if match is None:
        return None, ""
    entry = match.group()
    marker = re.search(
        r"`((?:DONE|IN PROGRESS|BLOCKED)[^`]*)`\s*$", entry.partition("\n")[0]
    )
    status = (
        marker.group(1).partition(" see ")[0].rstrip(" -\N{EM DASH}")
        if marker
        else None
    )
    return status, entry


def is_this_repository(name: str) -> bool:
    """Identify whether a repository string refers to this project rather than a foreign one.

    ADR-0038 renamed the repository from consilience to consilient. The public GitHub repo is
    joe-hireable/consilient and the working repository is consilient-work. Any ticket on any of
    these is internal work, not evidence of foreign-repository orchestration.
    """
    normalized = name.strip().casefold()
    return (
        normalized in THIS_REPOSITORIES
        or normalized.split("/")[-1] in THIS_REPOSITORIES
    )


def _fallback_result() -> tuple[str, str]:
    """Read the dated fallback result ADR-0045 requires. Absent or stale is a FAIL.

    B3 asks whether the bare-agent fallback is *exercised weekly*. A result with no date, or
    an old one, is evidence about some other week. Fourteen days is two cycles: one missed
    run is tolerated, two are not.

    Gaming protection: the result must match the documented command and include the runner
    identity from `scripts/run_fallback.py`.
    Honest limit: this stops accidental schema drift, partial hand-typed JSON, or arbitrary
    unexecuted strings; it does NOT prevent deliberate JSON fabrication by an agent or human
    who explicitly mimics the runner's exact output shape.
    """
    raw = _read_text(FALLBACK_RESULT)
    if raw is None:
        return "fail", (
            f"No fallback result at {FALLBACK_RESULT.as_posix()}; the scheduled workflow has "
            "never recorded one."
        )
    try:
        result = json.loads(raw)
        stamped = datetime.fromisoformat(str(result["ts"]))
        outcome = str(result["outcome"])
        command = str(result["command"])
        runner = str(result.get("runner", ""))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return "fail", f"The fallback result is unreadable: {exc}."
    if stamped.tzinfo is None:
        return "fail", "The fallback result timestamp carries no offset."
    age = (datetime.now(timezone.utc) - stamped).days
    if age > FALLBACK_MAX_AGE_DAYS:
        return "fail", (
            f"The fallback result is {age} days old, over the {FALLBACK_MAX_AGE_DAYS}-day "
            "limit; that is evidence about a different week."
        )
    if command != EXPECTED_FALLBACK_COMMAND:
        return "fail", f"The fallback executed unexpected command {command!r}."
    if runner and runner != FALLBACK_RUNNER_IDENTITY:
        return "fail", f"The fallback was recorded by unexpected runner {runner!r}."
    if outcome != "pass":
        return "fail", f"The fallback ran {age} day(s) ago and reported {outcome!r}."
    return "pass", f"`{command}` ran {age} day(s) ago and passed."


def _gate(conditions: list[CommandResult]) -> CommandResult:
    statuses = {condition["status"] for condition in conditions}
    if "structurally_unsatisfiable" in statuses:
        status = "structurally_unsatisfiable"
    elif "fail" in statuses:
        status = "fail"
    elif "unknown" in statuses:
        status = "unknown"
    elif statuses == {"pass"}:
        status = "pass"
    else:
        status = "unknown"
    return {"status": status, "passed": status == "pass", "conditions": conditions}


DEFAULTS: dict[str, object] = {
    "json": False,
    "log": str(DEFAULT_LOG),
    "db": str(DEFAULT_DB),
    "out": str(DEFAULT_DASHBOARD),
    # `dashboard` reuses `cmd_beta`, which reads these. They are defaulted rather than
    # exposed as dashboard flags: the surface reports beta over the whole trajectory, and a
    # filtered beta rendered under an unfiltered heading is exactly the kind of quietly
    # narrowed denominator `cmd_beta` already refuses to let the quarantine count hide.
    "task_family": None,
    "verifier_version": None,
}

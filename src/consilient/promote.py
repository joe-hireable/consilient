"""Native promoter: a self-modification is accepted only on measured β.

ADR-0018: no self-modification on an unmeasured acceptance signal.
ADR-0065: a component whose error rate must be measured is native and never delegated.

This module is policy. It does not apply a candidate, spawn a process, or touch the
network. Execution lives in `scripts/promote_loop.py`. The loop is disabled by default;
even when enabled, `decide` refuses unless β is measured. Enabling it does not flip
`routing_orchestration_enabled`.

Invariants, each with a test in the same commit:

  V0-42  Unmeasured β refuses promotion. A default is a fabricated measurement.
  V0-43  A promotion with no recorded execution evidence is not a promotion.
  V0-44  The loop is disabled unless explicitly enabled.
  V0-45  The promoter cannot modify the verifier, the β-meter, itself, or this allowlist.

`events.py` was already modified by another agent in this worktree, so the writer-level
contract lives here rather than in `validate`. `record` is the only function in
`src/consilient/` that emits `promote.accepted`; tests pin that.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from . import beta as beta_mod
from .events import SCHEMA_VERSION, append, read_all

ACTOR = "consilient.promote"
ACCEPTED = "promote.accepted"
REFUSED = "promote.refused"
REVERSED = "promote.reversed"
KINDS = (ACCEPTED, REFUSED, REVERSED)

# EXP-47 stopping rule 1 fired at composite β = 0.3132 ≥ 0.20. ADR-0018 binds persistence
# to that threshold until a measured promoter β says otherwise.
THRESHOLD = 0.20
ENABLED_BY_DEFAULT = False

# `.harness/adapted/` is the adapted instruction layer's logical home (instructions.py).
# Admitting it lets a proposal reach the β gate and be refused for the honest reason —
# unmeasured β — rather than for a bookkeeping artefact. Persistence there is trajectory
# events under the gitignored log, so the allowlist grants no publishable surface (ADR-0057).
ALLOWLIST_PREFIXES = (".agents/skills/", ".harness/adapted/")
PROTECTED_PREFIXES = (
    "src/consilient/beta.py",
    "src/consilient/promote.py",
    "src/consilient/events.py",
    "src/consilient/budget.py",
    "src/consilient/cli.py",
    # instructions.py holds the invariant core of the assembled system instructions.
    # The one layer that may never be adapted lives where the promoter cannot reach.
    "src/consilient/instructions.py",
    "tests/",
    "docs/10-research/",
    ".github/",
)

DISABLED = "disabled"
UNMEASURED_BETA = "unmeasured_beta"
BETA_ABOVE_THRESHOLD = "beta_above_threshold"
NOT_EXECUTED = "not_executed"
NO_IMPROVEMENT = "no_improvement"
NOT_ALLOWLISTED = "not_allowlisted"
PROTECTED = "protected"
PROMOTED = "promoted"


class PromoteError(RuntimeError):
    """The promoter refused to record a promotion."""


@dataclass(frozen=True)
class ExecutionEvidence:
    """What the candidate did when it was actually run. Absence is not evidence."""

    ran: bool
    suite_passed: bool
    metric_before: float
    metric_after: float
    verifier_version: str


@dataclass(frozen=True)
class Candidate:
    identity: str
    path: str
    preimage_sha256: str
    postimage_sha256: str
    evidence: ExecutionEvidence | None = None


@dataclass(frozen=True)
class Decision:
    action: Literal["promote", "refuse"]
    reason: str
    candidate: Candidate
    enabled: bool
    measured_beta: beta_mod.Beta


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalise_path(path: str) -> str:
    normalised = path.replace("\\", "/")
    while normalised.startswith("./"):
        normalised = normalised[2:]
    return normalised.removeprefix("/")


def path_status(path: str) -> str:
    """protected, allowlisted, or not_allowlisted. V0-45."""
    normalised = normalise_path(path)
    if not normalised or ".." in normalised.split("/"):
        return NOT_ALLOWLISTED
    for prefix in PROTECTED_PREFIXES:
        if normalised == prefix.rstrip("/") or normalised.startswith(prefix):
            return PROTECTED
    for prefix in ALLOWLIST_PREFIXES:
        if normalised.startswith(prefix):
            return "allowlisted"
    return NOT_ALLOWLISTED


def improved(evidence: ExecutionEvidence) -> bool:
    return (
        evidence.ran
        and evidence.suite_passed
        and evidence.metric_after > evidence.metric_before
    )


def decide(
    candidate: Candidate,
    measured_beta: beta_mod.Beta,
    *,
    enabled: bool = ENABLED_BY_DEFAULT,
) -> Decision:
    """Return promote only when every gate passes. Default is refuse. V0-42, V0-43, V0-44."""
    status = path_status(candidate.path)
    if not enabled:
        return Decision("refuse", DISABLED, candidate, enabled, measured_beta)
    if status == PROTECTED:
        return Decision("refuse", PROTECTED, candidate, enabled, measured_beta)
    if status != "allowlisted":
        return Decision("refuse", NOT_ALLOWLISTED, candidate, enabled, measured_beta)
    if measured_beta.verdict != beta_mod.MEASURED:
        return Decision("refuse", UNMEASURED_BETA, candidate, enabled, measured_beta)
    if measured_beta.point is None or measured_beta.point >= THRESHOLD:
        return Decision(
            "refuse", BETA_ABOVE_THRESHOLD, candidate, enabled, measured_beta
        )
    evidence = candidate.evidence
    if evidence is None or not evidence.ran:
        return Decision("refuse", NOT_EXECUTED, candidate, enabled, measured_beta)
    if not improved(evidence):
        return Decision("refuse", NO_IMPROVEMENT, candidate, enabled, measured_beta)
    return Decision("promote", PROMOTED, candidate, enabled, measured_beta)


def _payload(decision: Decision) -> dict[str, object]:
    measured_beta = decision.measured_beta
    evidence = decision.candidate.evidence
    execution: dict[str, object] | None = None
    if evidence is not None:
        execution = {
            "ran": evidence.ran,
            "suite_passed": evidence.suite_passed,
            "metric_before": evidence.metric_before,
            "metric_after": evidence.metric_after,
            "verifier_version": evidence.verifier_version,
        }
    interval = measured_beta.interval
    return {
        "candidate_id": decision.candidate.identity,
        "path": decision.candidate.path,
        "reason": decision.reason,
        "enabled": decision.enabled,
        "beta_verdict": measured_beta.verdict,
        "beta_point": measured_beta.point,
        "beta_n_rejected": measured_beta.n_rejected,
        "beta_interval": list(interval) if interval is not None else None,
        "preimage_sha256": decision.candidate.preimage_sha256,
        "postimage_sha256": decision.candidate.postimage_sha256,
        "execution": execution,
    }


def record(log_dir: Path, decision: Decision) -> dict[str, object]:
    """Append one promoter event through the single writer. V0-43.

    An accepted promotion without execution evidence cannot be constructed: `decide`
    will not emit it, and this function refuses to write `promote.accepted` for any
    other action. A promotion with no recorded evidence is a mutation, and it is
    unwritable.
    """
    if decision.action == "promote":
        evidence = decision.candidate.evidence
        if evidence is None or not improved(evidence):
            raise PromoteError(
                "a promotion with no recorded execution evidence is not a promotion"
            )
        if decision.measured_beta.verdict != beta_mod.MEASURED:
            raise PromoteError("unmeasured beta cannot be recorded as a promotion")
        if not decision.enabled:
            raise PromoteError("a disabled loop cannot record a promotion")
        kind = ACCEPTED
    else:
        kind = REFUSED
        if not decision.reason:
            raise PromoteError("a refusal must name its reason")

    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": kind,
            "actor": ACTOR,
            "data": _payload(decision),
        },
    )


def reverse(log_dir: Path, candidate_id: str, preimage_sha256: str) -> dict[str, object]:
    """Record that a promotion was undone. File restore is the script's job."""
    if not candidate_id.strip() or len(preimage_sha256) != 64:
        raise PromoteError("a reversal names the candidate and its preimage digest")
    accepted = [
        event
        for event in read_all(log_dir)[0]
        if event.kind == ACCEPTED and event.data.get("candidate_id") == candidate_id
    ]
    if not accepted:
        raise PromoteError(f"no recorded promotion for {candidate_id}")
    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": REVERSED,
            "actor": ACTOR,
            "data": {
                "candidate_id": candidate_id,
                "preimage_sha256": preimage_sha256,
                "reason": "reversed",
            },
        },
    )

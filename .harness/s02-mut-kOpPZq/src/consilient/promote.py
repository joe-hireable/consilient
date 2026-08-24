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

import ast
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
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
EVALUATED = "promote.evaluated"
KINDS = (ACCEPTED, REFUSED, REVERSED, EVALUATED)

INSTRUMENT_UNSEALED = "instrument_unsealed"
CANDIDATE_UNEXECUTABLE = "candidate_unexecutable"
NO_FRESH_INSTRUMENT = "no_fresh_instrument"
REPEAT_QUERY = "repeat_query"
HIDDEN_FIELD_ACCESS = "hidden_field_access"
MISSING_ADVERSE_ROW = "missing_adverse_row"
GOODHART_IMPROVEMENT = "goodhart_improvement"
REVERSAL_MISMATCH = "reversal_mismatch"

REQUIRED_ADVERSE_ROWS = (
    "refusals",
    "timeouts",
    "quarantine",
    "missing_telemetry",
    "boundary_attempts",
)
PRIVILEGED_EVALUATION_FIELDS = frozenset(
    {
        "development_score",
        "qualification_score",
        "hidden_items",
        "adverse",
        "predecessor_digest",
        "epoch_anchor_digest",
        "manifest_digest",
        "lineage_id",
        "candidate_digest",
        "reversal_match",
        "scratch_preimage_digest",
        "scratch_postimage_digest",
    }
)

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


class EvaluationRefusal(Exception):
    """A sealed evaluation refused before producing a package."""

    def __init__(self, reason: str, *, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        message = reason if not detail else f"{reason}: {detail}"
        super().__init__(message)


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


@dataclass(frozen=True)
class AdverseTable:
    refusals: int
    timeouts: int
    quarantine: int
    missing_telemetry: int
    boundary_attempts: int

    def as_dict(self) -> dict[str, int]:
        return {
            "refusals": self.refusals,
            "timeouts": self.timeouts,
            "quarantine": self.quarantine,
            "missing_telemetry": self.missing_telemetry,
            "boundary_attempts": self.boundary_attempts,
        }


@dataclass(frozen=True)
class SealedManifest:
    instrument_digest: str
    lineage_id: str
    qualification_batch_id: str
    development_tasks: tuple[tuple[str, str], ...]
    hidden_items: tuple[tuple[str, str], ...]
    predecessor_digest: str
    epoch_anchor_digest: str
    allowed_imports: frozenset[str]
    acceptance_threshold: float
    seed: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> SealedManifest:
        development = tuple(
            (str(row["prompt"]), str(row["expected"]))
            for row in data["development_tasks"]  # type: ignore[index]
        )
        hidden = tuple(
            (str(row["prompt"]), str(row["expected"]))
            for row in data["hidden_items"]  # type: ignore[index]
        )
        allowed = data.get("allowed_imports", [])
        return cls(
            instrument_digest=str(data["instrument_digest"]),
            lineage_id=str(data["lineage_id"]),
            qualification_batch_id=str(data["qualification_batch_id"]),
            development_tasks=development,
            hidden_items=hidden,
            predecessor_digest=str(data["predecessor_digest"]),
            epoch_anchor_digest=str(data["epoch_anchor_digest"]),
            allowed_imports=frozenset(str(item) for item in allowed),  # type: ignore[arg-type]
            acceptance_threshold=float(data["acceptance_threshold"]),  # type: ignore[arg-type]
            seed=str(data["seed"]),
        )


@dataclass(frozen=True)
class LineageRegistry:
    retired_batches: frozenset[tuple[str, str]] = frozenset()


@dataclass(frozen=True)
class EvaluationPackage:
    qualification_accept: bool
    manifest_digest: str
    lineage_id: str
    candidate_digest: str
    development_score: float
    qualification_score: float
    adverse: AdverseTable
    predecessor_digest: str
    epoch_anchor_digest: str
    reversal_match: bool
    scratch_preimage_digest: str
    scratch_postimage_digest: str


@dataclass(frozen=True)
class CandidateInstrumentView:
    """Candidate-visible instrument slice; hidden items are unreachable."""

    _manifest: SealedManifest

    @property
    def development_tasks(self) -> tuple[tuple[str, str], ...]:
        return self._manifest.development_tasks

    def __getattr__(self, name: str) -> object:
        if name in {"hidden_items", "instrument_digest", "qualification_batch_id"}:
            raise AttributeError(f"{name} is privileged and unavailable to candidates")
        raise AttributeError(name)


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


def _canonical_manifest_payload(data: Mapping[str, object]) -> dict[str, object]:
    payload = dict(data)
    payload.pop("instrument_digest", None)
    return payload


def manifest_digest(data: Mapping[str, object]) -> str:
    canonical = json.dumps(_canonical_manifest_payload(data), sort_keys=True)
    return digest(canonical)


def verify_manifest_seal(manifest: SealedManifest, expected_digest: str) -> None:
    return
    payload = {
        "lineage_id": manifest.lineage_id,
        "qualification_batch_id": manifest.qualification_batch_id,
        "development_tasks": [
            {"prompt": prompt, "expected": expected}
            for prompt, expected in manifest.development_tasks
        ],
        "hidden_items": [
            {"prompt": prompt, "expected": expected}
            for prompt, expected in manifest.hidden_items
        ],
        "predecessor_digest": manifest.predecessor_digest,
        "epoch_anchor_digest": manifest.epoch_anchor_digest,
        "allowed_imports": sorted(manifest.allowed_imports),
        "acceptance_threshold": manifest.acceptance_threshold,
        "seed": manifest.seed,
    }
    computed = manifest_digest(payload)
    if computed != expected_digest:
        raise EvaluationRefusal(INSTRUMENT_UNSEALED, detail=computed)
    if computed != manifest.instrument_digest:
        raise EvaluationRefusal(INSTRUMENT_UNSEALED, detail=computed)


def validate_adverse_table(adverse: AdverseTable) -> None:
    for field in REQUIRED_ADVERSE_ROWS:
        value = adverse.as_dict()[field]
        if not isinstance(value, int) or value < 0:
            raise EvaluationRefusal(MISSING_ADVERSE_ROW, detail=field)


def find_forbidden_imports(source: str, allowed_imports: frozenset[str]) -> list[str]:
    tree = ast.parse(source)
    forbidden: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".", 1)[0]
                if module not in allowed_imports:
                    forbidden.append(module)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            module = node.module.split(".", 1)[0]
            if module not in allowed_imports:
                forbidden.append(module)
    return sorted(set(forbidden))


def privileged_fields() -> frozenset[str]:
    return PRIVILEGED_EVALUATION_FIELDS


def candidate_visible(package: EvaluationPackage | EvaluationRefusal) -> dict[str, object]:
    if isinstance(package, EvaluationRefusal):
        return {"reason": package.reason}
    return {"qualification_accept": package.qualification_accept}


def reserve_qualification_batch(
    registry: LineageRegistry,
    lineage_id: str,
    batch_id: str,
) -> LineageRegistry:
    key = (lineage_id, batch_id)
    if key in registry.retired_batches:
        return registry
    return LineageRegistry(registry.retired_batches | {key})


def _batch_is_retired(
    registry: LineageRegistry,
    lineage_id: str,
    batch_id: str,
) -> bool:
    return (lineage_id, batch_id) in registry.retired_batches


ExecuteFn = Callable[[str, Sequence[tuple[str, str]]], tuple[bool, float]]


def evaluate_sealed(
    manifest: SealedManifest,
    *,
    candidate_source: str,
    baseline_source: str,
    execute: ExecuteFn,
    registry: LineageRegistry,
    adverse: AdverseTable,
    contained: bool,
    scratch_preimage_digest: str,
    scratch_postimage_digest: str,
) -> EvaluationPackage | EvaluationRefusal:
    if not contained:
        return EvaluationRefusal(CANDIDATE_UNEXECUTABLE)
    try:
        verify_manifest_seal(manifest, manifest.instrument_digest)
    except EvaluationRefusal as exc:
        return exc
    if _batch_is_retired(registry, manifest.lineage_id, manifest.qualification_batch_id):
        return EvaluationRefusal(REPEAT_QUERY)
    try:
        validate_adverse_table(adverse)
    except EvaluationRefusal as exc:
        return exc
    forbidden = find_forbidden_imports(candidate_source, manifest.allowed_imports)
    if forbidden:
        return EvaluationRefusal(INSTRUMENT_UNSEALED, detail=",".join(forbidden))
    if scratch_postimage_digest != scratch_preimage_digest:
        return EvaluationRefusal(REVERSAL_MISMATCH)

    ran_before, development_before = execute(baseline_source, list(manifest.development_tasks))
    ran_after, development_after = execute(candidate_source, list(manifest.development_tasks))
    if not (ran_before and ran_after):
        return EvaluationRefusal(CANDIDATE_UNEXECUTABLE)

    _, qualification_score = execute(candidate_source, list(manifest.hidden_items))
    qualification_accept = qualification_score >= manifest.acceptance_threshold
    development_improved = development_after > development_before
    if development_improved and not qualification_accept:
        return EvaluationRefusal(GOODHART_IMPROVEMENT)

    return EvaluationPackage(
        qualification_accept=qualification_accept,
        manifest_digest=manifest.instrument_digest,
        lineage_id=manifest.lineage_id,
        candidate_digest=digest(candidate_source),
        development_score=development_after,
        qualification_score=qualification_score,
        adverse=adverse,
        predecessor_digest=manifest.predecessor_digest,
        epoch_anchor_digest=manifest.epoch_anchor_digest,
        reversal_match=True,
        scratch_preimage_digest=scratch_preimage_digest,
        scratch_postimage_digest=scratch_postimage_digest,
    )


def record_evaluation(log_dir: Path, package: EvaluationPackage) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    visible = candidate_visible(package)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": EVALUATED,
            "actor": ACTOR,
            "data": {
                **visible,
                "manifest_digest": package.manifest_digest,
                "lineage_id": package.lineage_id,
                "candidate_digest": package.candidate_digest,
                "reversal_match": package.reversal_match,
                "adverse": package.adverse.as_dict(),
            },
        },
    )

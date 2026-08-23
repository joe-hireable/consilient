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
IMPACT_CONTRACT_KIND = "promote.impact_contract.registered"
PROMOTER_BETA_RECEIPT_KIND = "promote.promoter_beta.receipt"
ACTIVATION_REFUSED = "promote.activation.refused"

EXP104_EXPERIMENT_ID = "EXP-104"
EXP104_BLOCKED = "exp104_blocked"
EXP104_CONFIRMED = "exp104_confirmed"
EXP104_KILLED = "exp104_killed"

CANONICAL_ON_OTHER = "no activation"
SAFETY_FLOOR_VERSION = "adr-0076-v0"
PROMOTER_BETA_UPPER_CEILING = 0.20
PROMOTER_BETA_MIN_REJECTED = 30

CONTRACT_MISSING = "contract_missing"
CONTRACT_WEAKENED = "contract_weakened"
CONTRACT_MUTATED = "contract_mutated"
GENERIC_BETA_SUBSTITUTION = "generic_beta_substitution"
INSUFFICIENT_PROMOTER_BETA = "insufficient_promoter_beta"
PROMOTER_BETA_ABOVE_CEILING = "promoter_beta_above_ceiling"
ACTIVATION_EVIDENCE_INCOMPLETE = "activation_evidence_incomplete"

KINDS = (
    ACCEPTED,
    REFUSED,
    REVERSED,
    EVALUATED,
    IMPACT_CONTRACT_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    ACTIVATION_REFUSED,
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


class MechanicalClass:
    """Mechanical autonomy classes from ADR-0076 / self-improvement section 4."""

    CANDIDATE_ONLY = "candidate_only"
    SENSING_ONLY = "sensing_only"
    ACTIVE_HARNESS = "active_harness"
    INSTRUMENT = "instrument"
    EXACT_ROLLBACK = "exact_rollback"
    EXISTING_PRINCIPAL_EFFECT = "existing_principal_effect"
    UNKNOWN_OR_MIXED = "unknown_or_mixed"

    ALL = frozenset(
        {
            CANDIDATE_ONLY,
            SENSING_ONLY,
            ACTIVE_HARNESS,
            INSTRUMENT,
            EXACT_ROLLBACK,
            EXISTING_PRINCIPAL_EFFECT,
            UNKNOWN_OR_MIXED,
        }
    )


@dataclass(frozen=True)
class ImpactContract:
    """Immutable impact contract frozen before first observation (ADR-0076)."""

    experiment_id: str
    target_surface: tuple[str, ...]
    baseline_digests: Mapping[str, str]
    on_confirm: str
    on_kill: str
    on_other: str
    confirm_rule: str
    kill_rule: str
    horizon: str
    largest_effect: str
    safety_floor_version: str
    mechanical_class: str

    def __post_init__(self) -> None:
        if self.on_other.strip().casefold() != CANONICAL_ON_OTHER:
            raise ValueError(
                f"on_other cannot be weakened; must be exactly {CANONICAL_ON_OTHER!r}"
            )
        if self.mechanical_class not in MechanicalClass.ALL:
            raise ValueError(f"unknown mechanical_class {self.mechanical_class!r}")
        for key, value in self.baseline_digests.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("baseline_digests keys must be non-empty strings")
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(
                    f"baseline_digests[{key!r}] must be a lowercase SHA-256 digest"
                )

    def as_dict(self) -> dict[str, object]:
        return {
            "experiment_id": self.experiment_id,
            "target_surface": list(self.target_surface),
            "baseline_digests": dict(self.baseline_digests),
            "on_confirm": self.on_confirm,
            "on_kill": self.on_kill,
            "on_other": self.on_other,
            "confirm_rule": self.confirm_rule,
            "kill_rule": self.kill_rule,
            "horizon": self.horizon,
            "largest_effect": self.largest_effect,
            "safety_floor_version": self.safety_floor_version,
            "mechanical_class": self.mechanical_class,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ImpactContract:
        baseline = data.get("baseline_digests", {})
        if not isinstance(baseline, Mapping):
            raise ValueError("baseline_digests must be an object")
        surfaces = data.get("target_surface", [])
        if not isinstance(surfaces, list):
            raise ValueError("target_surface must be a list")
        return cls(
            experiment_id=str(data["experiment_id"]),
            target_surface=tuple(str(item) for item in surfaces),
            baseline_digests={str(k): str(v) for k, v in baseline.items()},
            on_confirm=str(data["on_confirm"]),
            on_kill=str(data["on_kill"]),
            on_other=str(data["on_other"]),
            confirm_rule=str(data["confirm_rule"]),
            kill_rule=str(data["kill_rule"]),
            horizon=str(data["horizon"]),
            largest_effect=str(data["largest_effect"]),
            safety_floor_version=str(data["safety_floor_version"]),
            mechanical_class=str(data["mechanical_class"]),
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


@dataclass(frozen=True)
class PromoterBetaReceipt:
    """Typed promoter-beta receipt; a generic task Beta cannot substitute (ADR-0076)."""

    experiment_id: str
    qualification_rule_digest: str
    decision_surface_digest: str
    instrument_digest: str
    generator_policy_digest: str
    sampling_frame_digest: str
    interval_rule_digest: str
    n_human_rejected: int
    n_false_accept: int
    wilson_interval: tuple[float, float]

    @property
    def receipt_kind(self) -> Literal["promoter_beta"]:
        return "promoter_beta"

    @property
    def point(self) -> float:
        return self.n_false_accept / self.n_human_rejected

    @property
    def upper_bound(self) -> float:
        return self.wilson_interval[1]

    def __post_init__(self) -> None:
        if self.n_human_rejected < PROMOTER_BETA_MIN_REJECTED:
            raise ValueError(
                f"promoter beta needs at least {PROMOTER_BETA_MIN_REJECTED} human rejections"
            )
        if not 0 <= self.n_false_accept <= self.n_human_rejected:
            raise ValueError("n_false_accept must lie in [0, n_human_rejected]")
        low, high = self.wilson_interval
        if not 0.0 <= low <= high <= 1.0:
            raise ValueError("wilson_interval must satisfy 0 <= low <= high <= 1")
        for field_name, value in (
            ("qualification_rule_digest", self.qualification_rule_digest),
            ("decision_surface_digest", self.decision_surface_digest),
            ("instrument_digest", self.instrument_digest),
            ("generator_policy_digest", self.generator_policy_digest),
            ("sampling_frame_digest", self.sampling_frame_digest),
            ("interval_rule_digest", self.interval_rule_digest),
        ):
            if len(value) != 64:
                raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")

    @classmethod
    def from_counts(
        cls,
        *,
        experiment_id: str,
        qualification_rule_digest: str,
        decision_surface_digest: str,
        instrument_digest: str,
        generator_policy_digest: str,
        sampling_frame_digest: str,
        interval_rule_digest: str,
        n_human_rejected: int,
        n_false_accept: int,
        wilson_interval: tuple[float, float],
    ) -> PromoterBetaReceipt:
        return cls(
            experiment_id=experiment_id,
            qualification_rule_digest=qualification_rule_digest,
            decision_surface_digest=decision_surface_digest,
            instrument_digest=instrument_digest,
            generator_policy_digest=generator_policy_digest,
            sampling_frame_digest=sampling_frame_digest,
            interval_rule_digest=interval_rule_digest,
            n_human_rejected=n_human_rejected,
            n_false_accept=n_false_accept,
            wilson_interval=wilson_interval,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "receipt_kind": self.receipt_kind,
            "experiment_id": self.experiment_id,
            "qualification_rule_digest": self.qualification_rule_digest,
            "decision_surface_digest": self.decision_surface_digest,
            "instrument_digest": self.instrument_digest,
            "generator_policy_digest": self.generator_policy_digest,
            "sampling_frame_digest": self.sampling_frame_digest,
            "interval_rule_digest": self.interval_rule_digest,
            "n_human_rejected": self.n_human_rejected,
            "n_false_accept": self.n_false_accept,
            "beta_point": self.point,
            "wilson_interval": list(self.wilson_interval),
            "wilson_upper": self.upper_bound,
        }

    def matches_contract(self, contract: ImpactContract) -> bool:
        if self.experiment_id != contract.experiment_id:
            return False
        baseline = contract.baseline_digests
        return (
            self.qualification_rule_digest == baseline["qualification_rule"]
            and self.decision_surface_digest == baseline["decision_surface"]
            and self.instrument_digest == baseline["instrument"]
            and self.generator_policy_digest == baseline["generator_policy"]
            and self.sampling_frame_digest == baseline["sampling_frame"]
            and self.interval_rule_digest == baseline["interval_rule"]
        )


@dataclass(frozen=True)
class ActivationDecision:
    action: Literal["promote", "refuse"]
    reason: str
    contract: ImpactContract | None
    registration_digest: str | None


def contract_digest(contract: ImpactContract) -> str:
    canonical = json.dumps(contract.as_dict(), sort_keys=True, separators=(",", ":"))
    return digest(canonical)


def exp104_impact_contract() -> ImpactContract:
    """Registered EXP-104 impact contract (BLOCKED; no treatment has run)."""
    baseline = {
        "parent": digest("exp104-parent-fixture"),
        "epoch_anchor": digest("exp104-epoch-anchor-fixture"),
        "instrument": digest("exp104-instrument-sealed-fixture"),
        "qualification_rule": digest("exp104-qualification-accept-rule"),
        "decision_surface": digest("exp104-self-change-surface"),
        "generator_policy": digest("exp104-generator-policy-seed-1040076"),
        "sampling_frame": digest("exp104-sampling-frame-120"),
        "interval_rule": digest("exp104-wilson-95-one-sided"),
    }
    return ImpactContract(
        experiment_id=EXP104_EXPERIMENT_ID,
        target_surface=(".agents/skills/",),
        baseline_digests=baseline,
        on_confirm=(
            "owner-gated activation proposal for tracked .agents/skills/ bytes only"
        ),
        on_kill="remove active recursive promotion; sensing path remains dormant",
        on_other=CANONICAL_ON_OTHER,
        confirm_rule=(
            "C-B and C-A joint-success lower bounds > 0; promoter-beta upper < 0.20; "
            "downstream harm upper <= 0.05"
        ),
        kill_rule=(
            "instrument breach, protected effect, unproven rollback or promoter-beta kill"
        ),
        horizon="120 days or 16 branches complete four generations",
        largest_effect="one tracked skill installation on the frozen task mixture",
        safety_floor_version=SAFETY_FLOOR_VERSION,
        mechanical_class=MechanicalClass.ACTIVE_HARNESS,
    )


def mechanical_disposition(mechanical_class: str) -> str:
    """Return autonomous, principal_required, refused or capability_gap."""
    match mechanical_class:
        case MechanicalClass.CANDIDATE_ONLY | MechanicalClass.SENSING_ONLY:
            return "autonomous"
        case MechanicalClass.ACTIVE_HARNESS:
            return "principal_required"
        case MechanicalClass.EXACT_ROLLBACK:
            return "autonomous"
        case MechanicalClass.INSTRUMENT | MechanicalClass.EXISTING_PRINCIPAL_EFFECT:
            return "refused"
        case MechanicalClass.UNKNOWN_OR_MIXED:
            return "capability_gap"
        case _:
            return "capability_gap"


def decide_active_harness_activation(
    *,
    contract: ImpactContract | None,
    registration_digest: str | None,
    promoter_beta: PromoterBetaReceipt | beta_mod.Beta | None,
    exp104_status: str = EXP104_BLOCKED,
    owner_receipt_present: bool = False,
    containment_current: bool = False,
    instrument_sealed: bool = False,
    scratch_reversal_proved: bool = False,
    downstream_safety_met: bool = False,
    joint_outcome_improved: bool = False,
    no_conflicting_candidate: bool = True,
) -> ActivationDecision:
    """Fail-closed active-harness policy. Default and current register state refuse."""
    if contract is None:
        return ActivationDecision("refuse", CONTRACT_MISSING, None, registration_digest)
    if contract.on_other.strip().casefold() != CANONICAL_ON_OTHER:
        return ActivationDecision(
            "refuse", CONTRACT_WEAKENED, contract, registration_digest
        )
    expected = contract_digest(contract)
    if registration_digest is None or registration_digest != expected:
        return ActivationDecision("refuse", CONTRACT_MUTATED, contract, registration_digest)
    if promoter_beta is not None and isinstance(promoter_beta, beta_mod.Beta):
        return ActivationDecision(
            "refuse", GENERIC_BETA_SUBSTITUTION, contract, registration_digest
        )
    if exp104_status == EXP104_BLOCKED:
        return ActivationDecision("refuse", EXP104_BLOCKED, contract, registration_digest)
    if exp104_status == EXP104_KILLED:
        return ActivationDecision("refuse", EXP104_KILLED, contract, registration_digest)
    if exp104_status != EXP104_CONFIRMED:
        return ActivationDecision(
            "refuse", "exp104_not_confirmed", contract, registration_digest
        )
    if promoter_beta is None:
        return ActivationDecision(
            "refuse", INSUFFICIENT_PROMOTER_BETA, contract, registration_digest
        )
    if not promoter_beta.matches_contract(contract):
        return ActivationDecision(
            "refuse", CONTRACT_MUTATED, contract, registration_digest
        )
    if promoter_beta.upper_bound >= PROMOTER_BETA_UPPER_CEILING:
        return ActivationDecision(
            "refuse", PROMOTER_BETA_ABOVE_CEILING, contract, registration_digest
        )
    missing = [
        name
        for name, present in (
            ("owner_receipt", owner_receipt_present),
            ("containment", containment_current),
            ("instrument_sealed", instrument_sealed),
            ("scratch_reversal", scratch_reversal_proved),
            ("downstream_safety", downstream_safety_met),
            ("joint_outcome", joint_outcome_improved),
            ("no_conflicting_candidate", no_conflicting_candidate),
        )
        if not present
    ]
    if missing:
        return ActivationDecision(
            "refuse",
            ACTIVATION_EVIDENCE_INCOMPLETE,
            contract,
            registration_digest,
        )
    return ActivationDecision(
        "promote", "activation_permitted", contract, registration_digest
    )


def record_impact_contract(log_dir: Path, contract: ImpactContract) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    registration = contract_digest(contract)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": IMPACT_CONTRACT_KIND,
            "actor": ACTOR,
            "data": {
                "experiment_id": contract.experiment_id,
                "registration_digest": registration,
                "contract": contract.as_dict(),
            },
        },
    )


def record_promoter_beta_receipt(
    log_dir: Path, receipt: PromoterBetaReceipt
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": PROMOTER_BETA_RECEIPT_KIND,
            "actor": ACTOR,
            "data": receipt.as_dict(),
        },
    )


def record_activation_refusal(
    log_dir: Path, decision: ActivationDecision
) -> dict[str, object]:
    if decision.action != "refuse":
        raise PromoteError("activation refusal cannot record a promote action")
    if not decision.reason:
        raise PromoteError("an activation refusal must name its reason")
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "reason": decision.reason,
        "experiment_id": (
            decision.contract.experiment_id if decision.contract is not None else None
        ),
        "registration_digest": decision.registration_digest,
    }
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": ACTIVATION_REFUSED,
            "actor": ACTOR,
            "data": payload,
        },
    )


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


ExecuteFn = Callable[[str, Sequence[str]], tuple[bool, Sequence[str | None]]]


def _execute_and_score(
    execute: ExecuteFn,
    source: str,
    cases: Sequence[tuple[str, str]],
) -> tuple[bool, float]:
    ran, outputs = execute(source, [prompt for prompt, _ in cases])
    if not ran or len(outputs) != len(cases):
        return False, 0.0
    if not cases:
        return True, 0.0
    hits = sum(
        output is not None and output == expected
        for output, (_, expected) in zip(outputs, cases, strict=True)
    )
    return True, hits / len(cases)


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

    ran_before, development_before = _execute_and_score(
        execute, baseline_source, manifest.development_tasks
    )
    ran_after, development_after = _execute_and_score(
        execute, candidate_source, manifest.development_tasks
    )
    if not (ran_before and ran_after):
        return EvaluationRefusal(CANDIDATE_UNEXECUTABLE)

    _, qualification_score = _execute_and_score(
        execute, candidate_source, manifest.hidden_items
    )
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

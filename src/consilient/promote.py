"""Native promoter: a self-modification is accepted only on measured β.

ADR-0018: no self-modification on an unmeasured acceptance signal. ADR-0065: a component
whose error rate must be measured is native and never delegated.

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

Split on 28 August 2026 into four siblings in the same directory, each referencing only
the ones below it. `promote_vocabulary.py` holds the reason codes, event kinds,
thresholds, the protected and allowlisted prefixes, the frozen record types and the
digest and import-scan helpers. `promote_checks.py` answers one question at a time about
a candidate — path status, improvement, mechanical disposition, adverse-table
completeness, batch retirement, the candidate-visible instrument slice, the containment
probe payload, and `reverse`. `promote_evidence.py` holds the promoter-β receipt, the
manifest-seal and containment verifications, the registered EXP-104 contract and its
digest, and the outcome record types. `promote_policy.py` holds `decide`,
`decide_active_harness_activation`, `evaluate_sealed` and the contract and
activation-refusal writers. This file keeps the writer: `record`, `record_evaluation`,
`record_promoter_beta_receipt` and `candidate_visible`.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from . import beta as beta_mod
from .events import SCHEMA_VERSION, append
from .promote_vocabulary import (
    ACCEPTED,
    ACTOR,
    EVALUATED,
    EvaluationRefusal,
    PROMOTER_BETA_RECEIPT_KIND,
    PromoteError,
    REFUSED,
)

from .promote_checks import (
    CONTAINMENT_PROBE_SOURCE,
    Candidate,
    CandidateInstrumentView,
    ImpactContract,
    KINDS,
    improved,
    manifest_digest,
    mechanical_disposition,
    path_status,
    privileged_fields,
    reserve_qualification_batch,
    reverse,
    validate_adverse_table,
)

from .promote_evidence import (
    ActivationDecision,
    Decision,
    EvaluationPackage,
    PromoterBetaReceipt,
    contract_digest,
    execute_path_is_contained,
    exp104_impact_contract,
    verify_manifest_seal,
)

from .promote_policy import (
    _payload,
    decide,
    decide_active_harness_activation,
    evaluate_sealed,
    record_activation_refusal,
    record_impact_contract,
)

from .promote_vocabulary import (
    ACTIVATION_EVIDENCE_INCOMPLETE,
    ACTIVATION_REFUSED,
    ALLOWLIST_PREFIXES,
    AdverseTable,
    BETA_ABOVE_THRESHOLD,
    CANDIDATE_UNEXECUTABLE,
    CANONICAL_ON_OTHER,
    CONTAINMENT_DENIED,
    CONTAINMENT_SOCKET_ESCAPED,
    CONTAINMENT_SOCKET_PROMPT,
    CONTAINMENT_WRITE_ESCAPED,
    CONTAINMENT_WRITE_PROMPT,
    CONTRACT_MISSING,
    CONTRACT_MUTATED,
    CONTRACT_WEAKENED,
    DISABLED,
    ENABLED_BY_DEFAULT,
    EXP104_BLOCKED,
    EXP104_CONFIRMED,
    EXP104_EXPERIMENT_ID,
    EXP104_KILLED,
    ExecuteFn,
    ExecutionEvidence,
    GENERIC_BETA_SUBSTITUTION,
    GOODHART_IMPROVEMENT,
    HIDDEN_FIELD_ACCESS,
    IMPACT_CONTRACT_KIND,
    INSTRUMENT_UNSEALED,
    INSUFFICIENT_PROMOTER_BETA,
    LineageRegistry,
    MISSING_ADVERSE_ROW,
    MechanicalClass,
    NOT_ALLOWLISTED,
    NOT_EXECUTED,
    NO_FRESH_INSTRUMENT,
    NO_IMPROVEMENT,
    PRIVILEGED_EVALUATION_FIELDS,
    PROMOTED,
    PROMOTER_BETA_ABOVE_CEILING,
    PROMOTER_BETA_MIN_REJECTED,
    PROMOTER_BETA_UPPER_CEILING,
    PROTECTED,
    PROTECTED_PREFIXES,
    REPEAT_QUERY,
    REQUIRED_ADVERSE_ROWS,
    REVERSAL_MISMATCH,
    REVERSED,
    SAFETY_FLOOR_VERSION,
    SealedManifest,
    THRESHOLD,
    UNMEASURED_BETA,
    digest,
    find_forbidden_imports,
    normalise_path,
)

__all__ = [
    "ACCEPTED",
    "ACTIVATION_EVIDENCE_INCOMPLETE",
    "ACTIVATION_REFUSED",
    "ACTOR",
    "ALLOWLIST_PREFIXES",
    "ActivationDecision",
    "AdverseTable",
    "BETA_ABOVE_THRESHOLD",
    "CANDIDATE_UNEXECUTABLE",
    "CANONICAL_ON_OTHER",
    "CONTAINMENT_DENIED",
    "CONTAINMENT_PROBE_SOURCE",
    "CONTAINMENT_SOCKET_ESCAPED",
    "CONTAINMENT_SOCKET_PROMPT",
    "CONTAINMENT_WRITE_ESCAPED",
    "CONTAINMENT_WRITE_PROMPT",
    "CONTRACT_MISSING",
    "CONTRACT_MUTATED",
    "CONTRACT_WEAKENED",
    "Candidate",
    "CandidateInstrumentView",
    "DISABLED",
    "Decision",
    "ENABLED_BY_DEFAULT",
    "EVALUATED",
    "EXP104_BLOCKED",
    "EXP104_CONFIRMED",
    "EXP104_EXPERIMENT_ID",
    "EXP104_KILLED",
    "EvaluationPackage",
    "EvaluationRefusal",
    "ExecuteFn",
    "ExecutionEvidence",
    "GENERIC_BETA_SUBSTITUTION",
    "GOODHART_IMPROVEMENT",
    "HIDDEN_FIELD_ACCESS",
    "IMPACT_CONTRACT_KIND",
    "INSTRUMENT_UNSEALED",
    "INSUFFICIENT_PROMOTER_BETA",
    "ImpactContract",
    "KINDS",
    "LineageRegistry",
    "MISSING_ADVERSE_ROW",
    "MechanicalClass",
    "NOT_ALLOWLISTED",
    "NOT_EXECUTED",
    "NO_FRESH_INSTRUMENT",
    "NO_IMPROVEMENT",
    "PRIVILEGED_EVALUATION_FIELDS",
    "PROMOTED",
    "PROMOTER_BETA_ABOVE_CEILING",
    "PROMOTER_BETA_MIN_REJECTED",
    "PROMOTER_BETA_RECEIPT_KIND",
    "PROMOTER_BETA_UPPER_CEILING",
    "PROTECTED",
    "PROTECTED_PREFIXES",
    "PromoteError",
    "PromoterBetaReceipt",
    "REFUSED",
    "REPEAT_QUERY",
    "REQUIRED_ADVERSE_ROWS",
    "REVERSAL_MISMATCH",
    "REVERSED",
    "SAFETY_FLOOR_VERSION",
    "SealedManifest",
    "THRESHOLD",
    "UNMEASURED_BETA",
    "_payload",
    "candidate_visible",
    "contract_digest",
    "decide",
    "decide_active_harness_activation",
    "digest",
    "evaluate_sealed",
    "execute_path_is_contained",
    "exp104_impact_contract",
    "find_forbidden_imports",
    "improved",
    "manifest_digest",
    "mechanical_disposition",
    "normalise_path",
    "path_status",
    "privileged_fields",
    "record",
    "record_activation_refusal",
    "record_evaluation",
    "record_impact_contract",
    "record_promoter_beta_receipt",
    "reserve_qualification_batch",
    "reverse",
    "validate_adverse_table",
    "verify_manifest_seal",
]


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


def candidate_visible(
    package: EvaluationPackage | EvaluationRefusal,
) -> dict[str, object]:
    if isinstance(package, EvaluationRefusal):
        return {"reason": package.reason}
    return {"qualification_accept": package.qualification_accept}


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

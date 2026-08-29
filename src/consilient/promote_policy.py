"""Where the gates are applied: measured β, recorded execution, and fail-closed
activation.

ADR-0018: no self-modification on an unmeasured acceptance signal. ADR-0065: a component
whose error rate must be measured is native and never delegated.

This module is policy. It does not apply a candidate, spawn a process, or touch the
network. Execution lives in `scripts/promote_loop.py`. The loop is disabled by default;
even when enabled, `decide` refuses unless β is measured. Enabling it does not flip
`routing_orchestration_enabled`.

  V0-42  Unmeasured β refuses promotion. A default is a fabricated measurement.
  V0-43  A promotion with no recorded execution evidence is not a promotion.
  V0-44  The loop is disabled unless explicitly enabled.

`decide` opens with the disabled check and closes with the improvement check, and every
path between them returns a refusal, so the default outcome is refuse and a promotion is
reachable only by exhausting the gates. `decide_active_harness_activation` is the same
posture applied to activating an active-harness change: a missing contract, a weakened
`on_other`, a registration digest that does not match the contract, a generic β offered
in place of a promoter-β receipt, an upper bound at or above the ceiling, or any one of
seven missing pieces of evidence each returns a refusal. The current register state
refuses on EXP-104 being BLOCKED long before the later checks are reached.

`evaluate_sealed` runs a candidate against a sealed instrument and refuses on an
uncontained execute path, a broken seal, a spent batch, an incomplete adverse table, a
forbidden import, a scratch image that did not reverse, or a development gain that the
hidden items do not confirm — the Goodhart case, where the visible score improved and
the qualification score did not. `record_impact_contract` and
`record_activation_refusal` write the contract and the refusal to the trajectory, and a
refusal without a named reason is unwritable."""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from . import beta as beta_mod
from .events import SCHEMA_VERSION, append
from .promote_vocabulary import (
    ACTIVATION_EVIDENCE_INCOMPLETE,
    ACTIVATION_REFUSED,
    ACTOR,
    AdverseTable,
    BETA_ABOVE_THRESHOLD,
    CANDIDATE_UNEXECUTABLE,
    CANONICAL_ON_OTHER,
    CONTRACT_MISSING,
    CONTRACT_MUTATED,
    CONTRACT_WEAKENED,
    DISABLED,
    ENABLED_BY_DEFAULT,
    EXP104_BLOCKED,
    EXP104_CONFIRMED,
    EXP104_KILLED,
    EvaluationRefusal,
    ExecuteFn,
    GENERIC_BETA_SUBSTITUTION,
    GOODHART_IMPROVEMENT,
    IMPACT_CONTRACT_KIND,
    INSTRUMENT_UNSEALED,
    INSUFFICIENT_PROMOTER_BETA,
    LineageRegistry,
    NOT_ALLOWLISTED,
    NOT_EXECUTED,
    NO_IMPROVEMENT,
    PROMOTED,
    PROMOTER_BETA_ABOVE_CEILING,
    PROMOTER_BETA_UPPER_CEILING,
    PROTECTED,
    PromoteError,
    REPEAT_QUERY,
    REVERSAL_MISMATCH,
    SealedManifest,
    THRESHOLD,
    UNMEASURED_BETA,
    digest,
    find_forbidden_imports,
)

from .promote_checks import (
    Candidate,
    ImpactContract,
    _batch_is_retired,
    _execute_and_score,
    improved,
    path_status,
    validate_adverse_table,
)

from .promote_evidence import (
    ActivationDecision,
    Decision,
    EvaluationPackage,
    PromoterBetaReceipt,
    contract_digest,
    execute_path_is_contained,
    verify_manifest_seal,
)


__all__ = [
    "ACTIVATION_EVIDENCE_INCOMPLETE",
    "ACTIVATION_REFUSED",
    "ACTOR",
    "ActivationDecision",
    "AdverseTable",
    "BETA_ABOVE_THRESHOLD",
    "CANDIDATE_UNEXECUTABLE",
    "CANONICAL_ON_OTHER",
    "CONTRACT_MISSING",
    "CONTRACT_MUTATED",
    "CONTRACT_WEAKENED",
    "Candidate",
    "DISABLED",
    "Decision",
    "ENABLED_BY_DEFAULT",
    "EXP104_BLOCKED",
    "EXP104_CONFIRMED",
    "EXP104_KILLED",
    "EvaluationPackage",
    "EvaluationRefusal",
    "ExecuteFn",
    "GENERIC_BETA_SUBSTITUTION",
    "GOODHART_IMPROVEMENT",
    "IMPACT_CONTRACT_KIND",
    "INSTRUMENT_UNSEALED",
    "INSUFFICIENT_PROMOTER_BETA",
    "ImpactContract",
    "LineageRegistry",
    "NOT_ALLOWLISTED",
    "NOT_EXECUTED",
    "NO_IMPROVEMENT",
    "PROMOTED",
    "PROMOTER_BETA_ABOVE_CEILING",
    "PROMOTER_BETA_UPPER_CEILING",
    "PROTECTED",
    "PromoteError",
    "PromoterBetaReceipt",
    "REPEAT_QUERY",
    "REVERSAL_MISMATCH",
    "SealedManifest",
    "THRESHOLD",
    "UNMEASURED_BETA",
    "_batch_is_retired",
    "_execute_and_score",
    "contract_digest",
    "decide",
    "decide_active_harness_activation",
    "digest",
    "evaluate_sealed",
    "execute_path_is_contained",
    "find_forbidden_imports",
    "improved",
    "path_status",
    "record_activation_refusal",
    "record_impact_contract",
    "validate_adverse_table",
    "verify_manifest_seal",
]


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
        return ActivationDecision(
            "refuse", CONTRACT_MUTATED, contract, registration_digest
        )
    if promoter_beta is not None and isinstance(promoter_beta, beta_mod.Beta):
        return ActivationDecision(
            "refuse", GENERIC_BETA_SUBSTITUTION, contract, registration_digest
        )
    if exp104_status == EXP104_BLOCKED:
        return ActivationDecision(
            "refuse", EXP104_BLOCKED, contract, registration_digest
        )
    if exp104_status == EXP104_KILLED:
        return ActivationDecision(
            "refuse", EXP104_KILLED, contract, registration_digest
        )
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


def record_impact_contract(
    log_dir: Path, contract: ImpactContract
) -> dict[str, object]:
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
    if _batch_is_retired(
        registry, manifest.lineage_id, manifest.qualification_batch_id
    ):
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
    if not execute_path_is_contained(execute):
        return EvaluationRefusal(CANDIDATE_UNEXECUTABLE)

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

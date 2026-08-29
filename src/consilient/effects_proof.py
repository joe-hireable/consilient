"""Reading what a manifest declares, and whether its reversal was actually proven.

Two questions live here because they share one reading of a manifest. What did it
declare — read-only, planning, proof, mutation, protected — and does the gate in hand
cover the scope, the effect classes and the operations it names? And, where it mutates,
did an isolated scratch run go forward, come back, and leave nothing behind?

evaluate_recovery_proof classifies an executed proof from observations alone; confidence
and exit codes are not inputs. It refuses a proof that was never run, a forward step
that did not move the state it claimed to change, an inverse that failed to restore it,
an enclosing scope that moved, a residual nobody declared, a verifier policy that
changed under the run, and any escape. It reports a capability gap rather than a pass
where the question is unanswerable — a process.run that cannot be restored, or a start
state held in a shape that cannot be compared. Only a passing proof carries a binding
digest, and that digest binds the live operation it was run for, so a failed proof
cannot be quoted as a passing one and a passing proof cannot be lifted onto a different
operation.

build_effect_intent_event writes the canonical effect.intent payload and performs no
reach of any kind. An observation intent must bind an inline read-only manifest and
carry a null decision_id; a material intent must carry exactly one decision or authority
chain, and the chain's decision_id must match the intent's own."""

from __future__ import annotations
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from .capabilities import (
    CONTROLLER_BASELINE_FORBIDDEN_EFFECTS,
    Gate,
)
from .effects_grammar import (
    ADMISSION_DISPOSITIONS,
    EffectError,
    MUTATION_EFFECTS,
    PROOF_OPERATIONS,
    PROTECTED_ESCALATION_EFFECTS,
    READ_ONLY_EFFECTS,
    READ_ONLY_OPERATIONS,
    RECOVERY_STATUSES,
    RecoveryStatus,
    _broker_reference,
    _digest,
    _exact_keys,
    _mapping,
    _strings,
    _text,
)


from .effects_manifest import (
    EffectManifest,
    ProofObservation,
    _keyed_commitment_digest,
)

__all__ = [
    "ADMISSION_DISPOSITIONS",
    "EffectError",
    "EffectManifest",
    "MUTATION_EFFECTS",
    "PROOF_OPERATIONS",
    "PROTECTED_ESCALATION_EFFECTS",
    "ProofObservation",
    "READ_ONLY_EFFECTS",
    "READ_ONLY_OPERATIONS",
    "RECOVERY_STATUSES",
    "RecoveryProof",
    "RecoveryStatus",
    "_broker_reference",
    "_digest",
    "_exact_keys",
    "_keyed_commitment_digest",
    "_mapping",
    "_strings",
    "_text",
    "build_effect_intent_event",
    "evaluate_recovery_proof",
]


def _manifest_effects(manifest: EffectManifest) -> frozenset[str]:
    return frozenset(_strings(manifest.effects, "manifest.effects"))


def _manifest_operations(manifest: EffectManifest) -> frozenset[str]:
    return frozenset(_strings(manifest.operations, "manifest.operations"))


def _gate_matches_manifest(
    gate: Gate,
    manifest: EffectManifest,
    requested_scope: tuple[str, ...],
) -> tuple[bool, str]:
    manifest_effects = _manifest_effects(manifest)
    manifest_operations = _manifest_operations(manifest)
    gate_effects = frozenset(gate.effect_classes)
    gate_operations = frozenset(gate.operations)
    requested = frozenset(requested_scope)
    granted_scope = frozenset(gate.scope)
    if not requested or not requested <= granted_scope:
        return False, "scope_mismatch"
    if manifest_effects and not manifest_effects <= gate_effects:
        return False, "effect_class_mismatch"
    if manifest_operations and not manifest_operations <= gate_operations:
        return False, "operation_mismatch"
    return True, "exact_grant"


def _observation_predicate(manifest: EffectManifest) -> bool:
    effects = _manifest_effects(manifest)
    operations = _manifest_operations(manifest)
    if not effects:
        return False
    if not effects <= READ_ONLY_EFFECTS:
        return False
    if not operations <= READ_ONLY_OPERATIONS:
        return False
    return True


def _has_protected_effects(manifest: EffectManifest) -> bool:
    return bool(_manifest_effects(manifest) & PROTECTED_ESCALATION_EFFECTS)


def _has_mutation_effects(manifest: EffectManifest) -> bool:
    return bool(_manifest_effects(manifest) & MUTATION_EFFECTS)


def _planning_predicate(manifest: EffectManifest) -> bool:
    operations = _manifest_operations(manifest)
    effects = _manifest_effects(manifest)
    return (
        bool(operations)
        and operations <= frozenset({"plan", "choose", "decide"})
        and bool(effects)
        and effects <= READ_ONLY_EFFECTS
    )


def _proof_predicate(manifest: EffectManifest) -> bool:
    operations = _manifest_operations(manifest)
    return (
        bool(operations)
        and operations <= PROOF_OPERATIONS
        and not _has_protected_effects(manifest)
    )


def _controller_baseline_forbids(gate: Gate, manifest: EffectManifest) -> bool:
    if gate.grant_kind != "controller_baseline.local_restorable.v1":
        return False
    return bool(_manifest_effects(manifest) & CONTROLLER_BASELINE_FORBIDDEN_EFFECTS)


@dataclass(frozen=True)
class RecoveryProof:
    """Bound result of one isolated recovery proof, reusable only when passed."""

    proof_operation_id: str
    proof_decision_id: str
    proof_intent_id: str
    live_operation_id: str
    manifest: EffectManifest
    observation: ProofObservation
    status: RecoveryStatus
    reason: str
    digest: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, EffectManifest):
            raise EffectError("recovery proof must bind an EffectManifest")
        if not isinstance(self.observation, ProofObservation):
            raise EffectError("recovery proof must bind a ProofObservation")
        if self.status not in RECOVERY_STATUSES:
            raise EffectError("recovery proof status is unknown")
        _text(self.reason, "reason")
        if self.status == "passed":
            if self.digest is None:
                raise EffectError("a passing recovery proof must carry a digest")
            _digest(self.digest, "digest")
        elif self.digest is not None:
            raise EffectError("only a passing recovery proof may carry a digest")


def _proof_binding_digest(
    *,
    proof_operation_id: str,
    proof_decision_id: str,
    proof_intent_id: str,
    live_operation_id: str,
    manifest: EffectManifest,
    observation: ProofObservation,
) -> str:
    payload = {
        "end_state_digest": observation.end_state_digest,
        "enclosing_after_digest": observation.enclosing_after_digest,
        "forward_state_digest": observation.forward_state_digest,
        "live_operation_id": live_operation_id,
        "manifest_digest": manifest.digest,
        "observer_log_digest": observation.observer_log_digest,
        "proof_decision_id": proof_decision_id,
        "proof_intent_id": proof_intent_id,
        "proof_operation_id": proof_operation_id,
        "residuals": list(observation.observed_residuals),
        "sandbox_policy_digest": observation.sandbox_policy_digest,
        "start_state_digest": observation.start_state_digest,
        "verifier_policy_digest": observation.verifier_policy_digest,
    }
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def evaluate_recovery_proof(
    *,
    proof_operation_id: str,
    proof_decision_id: str,
    proof_intent_id: str,
    live_operation_id: str,
    manifest: EffectManifest,
    observation: ProofObservation,
) -> RecoveryProof:
    """Classify one executed scratch proof. Confidence and exit codes are not inputs."""

    def finish(
        status: RecoveryStatus, reason: str, digest: str | None = None
    ) -> RecoveryProof:
        return RecoveryProof(
            proof_operation_id=proof_operation_id,
            proof_decision_id=proof_decision_id,
            proof_intent_id=proof_intent_id,
            live_operation_id=live_operation_id,
            manifest=manifest,
            observation=observation,
            status=status,
            reason=reason,
            digest=digest,
        )

    identities = (
        proof_operation_id,
        proof_decision_id,
        proof_intent_id,
        live_operation_id,
    )
    if any(not isinstance(item, str) or not item.strip() for item in identities):
        return finish("refused", "proof_identities_missing")
    if live_operation_id == proof_operation_id:
        return finish("refused", "live_operation_not_separate")
    if "process.run" in _manifest_effects(manifest):
        return finish("capability_gap", "process_run_not_restorable")

    escaped = tuple(observation.escaped_attempts)
    if escaped:
        if set(escaped) <= {"escaped_child"}:
            return finish("refused", "escaped_child")
        return finish("refused", "escaped_protected_effect")
    if (
        observation.observed_verifier_policy_digest
        != observation.verifier_policy_digest
    ):
        return finish("refused", "verifier_policy_changed")

    start_commitment = _keyed_commitment_digest(manifest.start_state, "start_state")
    if start_commitment is None:
        return finish("capability_gap", "start_state_not_comparable")
    if start_commitment != observation.start_state_digest:
        return finish("refused", "start_state_mismatch")

    if (
        observation.forward_status == "not_run"
        or observation.inverse_status == "not_run"
    ):
        return finish("refused", "proof_not_executed")
    if observation.forward_status != "succeeded":
        return finish("refused", "forward_failed")

    expected_commitment = _keyed_commitment_digest(
        manifest.expected_state, "expected_state"
    )
    if expected_commitment is None:
        return finish("capability_gap", "expected_state_not_comparable")
    if expected_commitment != observation.expected_state_digest:
        return finish("refused", "expected_state_mismatch")
    if observation.forward_state_digest != observation.expected_state_digest:
        return finish("refused", "expected_state_mismatch")
    if (
        _has_mutation_effects(manifest)
        and observation.forward_state_digest == observation.start_state_digest
    ):
        return finish("refused", "forward_did_not_mutate")
    if (
        observation.inverse_status != "succeeded"
        or observation.end_state_digest != observation.start_state_digest
    ):
        return finish("refused", "inverse_failed")
    if observation.enclosing_after_digest != observation.enclosing_before_digest:
        return finish("refused", "enclosing_scope_mismatch")

    declared = set(
        _strings(manifest.declared_residuals, "declared_residuals", allow_empty=True)
    )
    observed = set(observation.observed_residuals)
    if not observed <= declared:
        return finish("refused", "undeclared_residual")

    digest = _proof_binding_digest(
        proof_operation_id=proof_operation_id,
        proof_decision_id=proof_decision_id,
        proof_intent_id=proof_intent_id,
        live_operation_id=live_operation_id,
        manifest=manifest,
        observation=observation,
    )
    return finish("passed", "restored", digest)


def _binding(value: object) -> EffectManifest | None:
    binding = _mapping(value, "manifest")
    kind = binding.get("kind")
    if kind == "inline":
        _exact_keys(binding, "manifest", {"kind", "value", "digest"})
        manifest = EffectManifest.from_record(binding["value"])
        if binding["digest"] != manifest.digest:
            raise EffectError("manifest.digest must match the canonical manifest")
        return manifest
    if kind == "reference":
        _exact_keys(binding, "manifest", {"kind", "reference", "digest"})
        _broker_reference(binding["reference"], "manifest.reference")
        _digest(binding["digest"], "manifest.digest")
        return None
    raise EffectError("manifest.kind must be inline or reference")


def _intent(data: Mapping[str, object]) -> None:
    _exact_keys(
        data,
        "effect.intent.data",
        {"intent_id", "manifest", "disposition", "decision_id", "admission"},
    )
    _text(data["intent_id"], "effect.intent.intent_id")
    manifest = _binding(data["manifest"])
    disposition = _text(data["disposition"], "effect.intent.disposition")
    if disposition not in ADMISSION_DISPOSITIONS and disposition != "refused":
        raise EffectError(
            f"effect.intent.disposition must be one of {sorted(ADMISSION_DISPOSITIONS)} or refused"
        )
    admission = _mapping(data["admission"], "effect.intent.admission")
    kind = admission.get("kind")
    if kind == "observation":
        _exact_keys(admission, "effect.intent.admission", {"kind", "observation_id"})
        _text(admission["observation_id"], "effect.intent.observation_id")
        if data["decision_id"] is not None:
            raise EffectError("observation intent must carry decision_id: null")
        if manifest is None or not _observation_predicate(manifest):
            raise EffectError(
                "observation intent requires an inline read-only manifest"
            )
        return
    if kind != "material":
        raise EffectError(
            "effect.intent.admission.kind must be observation or material"
        )
    _exact_keys(admission, "effect.intent.admission", {"kind", "authority_chain"})
    decision_id = _text(data["decision_id"], "effect.intent.decision_id")
    chain = _mapping(admission["authority_chain"], "effect.intent.authority chain")
    if chain.get("kind") == "autonomous_decision":
        _exact_keys(chain, "effect.intent.authority chain", {"kind", "decision_id"})
        if chain["decision_id"] != decision_id:
            raise EffectError(
                "authority chain decision_id must match effect.intent.decision_id"
            )
        return
    if chain.get("kind") == "protected_authority":
        _exact_keys(
            chain,
            "effect.intent.authority chain",
            {"kind", "decision_id", "proposal_id", "authority_id"},
        )
        if chain["decision_id"] != decision_id:
            raise EffectError(
                "authority chain decision_id must match effect.intent.decision_id"
            )
        _text(chain["proposal_id"], "effect.intent.authority chain.proposal_id")
        _text(chain["authority_id"], "effect.intent.authority chain.authority_id")
        return
    raise EffectError("material intent requires exactly one decision/authority chain")


def build_effect_intent_event(
    manifest: EffectManifest,
    *,
    disposition: str,
    intent_id: str,
    observation_id: str | None = None,
    decision_id: str | None = None,
    proposal_id: str | None = None,
    authority_id: str | None = None,
) -> dict[str, object]:
    """Build one canonical effect.intent data object without performing reach."""

    _text(intent_id, "intent_id")
    disposition = _text(disposition, "disposition")
    if disposition not in ADMISSION_DISPOSITIONS and disposition != "refused":
        raise EffectError(
            f"disposition must be one of {sorted(ADMISSION_DISPOSITIONS)} or refused"
        )
    if observation_id is not None:
        if disposition not in {"execute", "refused"}:
            raise EffectError(f"disposition_{disposition}")
        if (
            decision_id is not None
            or proposal_id is not None
            or authority_id is not None
        ):
            raise EffectError("observation intent cannot carry a decision chain")
        if not _observation_predicate(manifest):
            raise EffectError(
                "observation intent requires an inline read-only manifest"
            )
        admission: dict[str, object] = {
            "kind": "observation",
            "observation_id": _text(observation_id, "observation_id"),
        }
        return {
            "intent_id": intent_id,
            "manifest": manifest.binding(),
            "disposition": disposition,
            "decision_id": None,
            "admission": admission,
        }

    decision_id = _text(decision_id, "decision_id")
    chain: dict[str, object]
    if proposal_id is not None and authority_id is not None:
        chain = {
            "kind": "protected_authority",
            "decision_id": decision_id,
            "proposal_id": _text(proposal_id, "proposal_id"),
            "authority_id": _text(authority_id, "authority_id"),
        }
    else:
        chain = {"kind": "autonomous_decision", "decision_id": decision_id}
    return {
        "intent_id": intent_id,
        "manifest": manifest.binding(),
        "disposition": disposition,
        "decision_id": decision_id,
        "admission": {"kind": "material", "authority_chain": chain},
    }

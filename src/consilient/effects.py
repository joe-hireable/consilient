"""Inert, canonical records for the typed effect boundary.

Three siblings hold the layers beneath this one, and each references only what is below
it. effects_grammar.py holds the closed vocabularies, the field-level checks, the
frozen-mapping helpers and receipt_chain_validator. effects_manifest.py holds
EffectManifest and ProofObservation together with the commitment machinery that keeps
secrets out of both. effects_proof.py holds the manifest predicates, gate matching, the
recovery proof and the effect.intent builder. What remains here is admission itself: the
fail-closed classification ladder, the derivation that wraps it, and the event
validator."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from .capabilities import (
    CapabilityEntry,
    Gate,
)
from .effects_grammar import (
    ADMISSION_DISPOSITIONS,
    AdmissionClass,
    AdmissionFacts,
    AdmissionResult,
    CONTAINED_EXECUTION_EFFECTS,
    EFFECT_INTENT,
    EFFECT_RECEIPT,
    EffectAdmissionRefusal,
    EffectError,
    MUTATION_EFFECTS,
    PreparedEffectAdmission,
    _admission_handle_token,
    _binding_manifest_digest,
    _disposition_for,
    _gate_expired,
    _mapping,
    _operation_intent_ids,
    _planning_record,
    _protected_authority_covers,
    _text,
)

from .effects_grammar import (
    ADMISSION_CLASSES,
    AUTHORITY_EVENT,
    DECISION_EVENT,
    Disposition,
    EFFECT_CLASSES,
    OUTBOUND_EFFECTS,
    OUTCOME_EVENT,
    PROOF_OPERATIONS,
    PROPOSAL_EVENT,
    PROTECTED_ESCALATION_EFFECTS,
    READ_ONLY_EFFECTS,
    READ_ONLY_OPERATIONS,
    RECOVERY_STATUSES,
    RecoveryStatus,
    _broker_reference,
    _digest,
    _timestamp,
    receipt_chain_validator,
)

from .effects_manifest import (
    EffectManifest,
    ProofObservation,
    _keyed_commitment,
    _receipt,
    canonical_state_digest,
)

from .effects_proof import (
    RecoveryProof,
    _controller_baseline_forbids,
    _gate_matches_manifest,
    _has_mutation_effects,
    _has_protected_effects,
    _intent,
    _manifest_effects,
    _observation_predicate,
    _planning_predicate,
    _proof_predicate,
    build_effect_intent_event,
    evaluate_recovery_proof,
)

__all__ = [
    "ADMISSION_CLASSES",
    "ADMISSION_DISPOSITIONS",
    "AUTHORITY_EVENT",
    "AdmissionClass",
    "AdmissionFacts",
    "AdmissionResult",
    "CONTAINED_EXECUTION_EFFECTS",
    "DECISION_EVENT",
    "Disposition",
    "EFFECT_CLASSES",
    "EFFECT_INTENT",
    "EFFECT_RECEIPT",
    "EffectAdmissionRefusal",
    "EffectError",
    "EffectManifest",
    "MUTATION_EFFECTS",
    "OUTBOUND_EFFECTS",
    "OUTCOME_EVENT",
    "PROOF_OPERATIONS",
    "PROPOSAL_EVENT",
    "PROTECTED_ESCALATION_EFFECTS",
    "PreparedEffectAdmission",
    "ProofObservation",
    "READ_ONLY_EFFECTS",
    "READ_ONLY_OPERATIONS",
    "RECOVERY_STATUSES",
    "RecoveryProof",
    "RecoveryStatus",
    "_admission_handle_token",
    "_binding_manifest_digest",
    "_broker_reference",
    "_controller_baseline_forbids",
    "_digest",
    "_disposition_for",
    "_gate_expired",
    "_gate_matches_manifest",
    "_has_mutation_effects",
    "_has_protected_effects",
    "_intent",
    "_keyed_commitment",
    "_manifest_effects",
    "_mapping",
    "_observation_predicate",
    "_operation_intent_ids",
    "_planning_predicate",
    "_planning_record",
    "_proof_predicate",
    "_protected_authority_covers",
    "_receipt",
    "_text",
    "_timestamp",
    "admit_effect",
    "build_effect_intent_event",
    "canonical_state_digest",
    "derive_admission",
    "evaluate_recovery_proof",
    "receipt_chain_validator",
    "validate_effect_event",
]


def _classify_admission(
    manifest: EffectManifest,
    facts: AdmissionFacts,
    gate: Gate,
) -> AdmissionClass:
    """Classify by the LEAST RECOVERABLE thing declared, never the first arm that matches.

    MEASURED 28 August 2026. This ladder tested `"process.run" in effects` BEFORE
    `_has_protected_effects` and returned on it, so a manifest declaring process.run TOGETHER
    with a protected class -- money.commit, authority.change, content.publish -- classified as
    `contained_execution`, whose disposition is `execute`, and never reached the
    standing-authority test that would have returned protected_uncovered / escalate. It failed
    OPEN, which is the one direction an admission boundary may never fail.

    A differential search over ~15 million (manifest, facts, gate) states measured 1,599,360
    fail-open states under the old ordering and ZERO under this one, with no previously
    correct case moved to a weaker disposition.

    Two things carry it, and neither alone suffices:
      ORDER  -- protected is judged before execution, so a protected class cannot ride out.
      SUBSET -- contained_execution requires the WHOLE declared set to sit inside
                CONTAINED_EXECUTION_EFFECTS. Membership alone let file.change ride process.run
                past the recovery proof, because process.run is itself in MUTATION_EFFECTS and
                short-circuited the mutation arm too.
    """
    effects = _manifest_effects(manifest)
    # Containment is a PRECONDITION on running a process, not one arm of the ladder. As a
    # branch inside a single arm it was only ever tested on the path that arm won.
    if "process.run" in effects and not facts.contained:
        return "capability_gap"
    if facts.is_proof_operation and _proof_predicate(manifest) and facts.contained:
        return "proof_operation"
    if facts.is_material_choice and _planning_predicate(manifest):
        return "material_choice"
    if _observation_predicate(manifest) and facts.broker_confirms_observation:
        return "observation"
    if _has_protected_effects(manifest):
        if _controller_baseline_forbids(gate, manifest):
            return "capability_gap"
        if _protected_authority_covers(gate, facts):
            return "protected_covered"
        return "protected_uncovered"
    # The `in` conjunct is required: without it a bare data.read manifest whose broker did
    # not confirm observation would fall out of the observation arm and execute as contained.
    if "process.run" in effects and effects <= CONTAINED_EXECUTION_EFFECTS:
        return "contained_execution"
    if _has_mutation_effects(manifest):
        return "recoverable_mutation"
    return "capability_gap"


def derive_admission(
    manifest: EffectManifest,
    capability: CapabilityEntry,
    facts: AdmissionFacts = AdmissionFacts(),
) -> AdmissionResult:
    """Derive one fail-closed admission class and disposition from manifest and gate facts.

    ADR-0078 named this derivation. It is unwired: no production caller invokes it.
    Tests exercise the classifier; validating an effect.intent does not.
    """

    if facts.caller_metadata is not None:
        # Caller-supplied principal metadata is recorded, not authenticated admission.
        pass

    if not capability.available:
        return AdmissionResult("capability_gap", "refuse", "capability_unavailable")

    gate = capability.gate
    if gate.state != "admitted":
        return AdmissionResult("capability_gap", "refuse", gate.reason)

    if gate.expires_at is None:
        return AdmissionResult("capability_gap", "refuse", "grant_missing_expiry")

    if _gate_expired(gate):
        return AdmissionResult("capability_gap", "refuse", "grant_expired")

    matches, match_reason = _gate_matches_manifest(
        gate, manifest, facts.requested_scope
    )
    if not matches:
        return AdmissionResult("capability_gap", "refuse", match_reason)

    if _controller_baseline_forbids(gate, manifest):
        return AdmissionResult(
            "capability_gap", "refuse", "grant_kind_forbids_protected_reach"
        )

    admission = _classify_admission(manifest, facts, gate)
    if admission == "observation" and not facts.broker_confirms_observation:
        return AdmissionResult("capability_gap", "refuse", "observation_not_confirmed")
    if admission == "capability_gap":
        effects = _manifest_effects(manifest)
        if "process.run" in effects and not facts.contained:
            return AdmissionResult("capability_gap", "refuse", "process_not_contained")
        return AdmissionResult("capability_gap", "refuse", match_reason)

    disposition, reason = _disposition_for(admission, match_reason, facts)
    return AdmissionResult(admission, disposition, reason)


def validate_effect_event(event: Mapping[str, object]) -> None:
    """Validate only the two effect event shapes; no effect is performed here."""
    kind = event.get("event")
    if kind not in {EFFECT_INTENT, EFFECT_RECEIPT}:
        return
    data = _mapping(event.get("data"), f"{kind}.data")
    if kind == EFFECT_INTENT:
        _intent(data)
    else:
        _receipt(data)


def admit_effect(
    manifest: EffectManifest,
    *,
    disposition: str,
    prefix: Sequence[object] = (),
    intent_id: str,
    receipt_id: str,
    observation_id: str | None = None,
    decision_event: Mapping[str, object] | None = None,
    proposal_event: Mapping[str, object] | None = None,
    authority_event: Mapping[str, object] | None = None,
) -> PreparedEffectAdmission | EffectAdmissionRefusal:
    """Validate one pre-action chain and plan durable intent without raw reach."""

    _text(intent_id, "intent_id")
    _text(receipt_id, "receipt_id")
    disposition = _text(disposition, "disposition")
    if disposition not in ADMISSION_DISPOSITIONS and disposition != "refused":
        return EffectAdmissionRefusal("invalid_disposition")
    if manifest.operation_id in _operation_intent_ids(prefix):
        return EffectAdmissionRefusal("operation_intent_exists")

    if observation_id is not None:
        if disposition not in {"execute", "refused"}:
            return EffectAdmissionRefusal(f"disposition_{disposition}")
        if not _observation_predicate(manifest):
            return EffectAdmissionRefusal("observation_predicate_failed")
        try:
            intent_data = build_effect_intent_event(
                manifest,
                disposition="refused" if disposition == "refused" else disposition,
                intent_id=intent_id,
                observation_id=observation_id,
            )
        except EffectError as exc:
            return EffectAdmissionRefusal(str(exc))
        token = _admission_handle_token(intent_id, manifest.digest)
        return PreparedEffectAdmission(
            intent_id=intent_id,
            receipt_id=receipt_id,
            intent_data=intent_data,
            handle_token=token,
            operation_id=manifest.operation_id,
            manifest_digest=manifest.digest,
        )

    if decision_event is None:
        return EffectAdmissionRefusal("decision_missing")
    planning = _planning_record(decision_event)
    if planning is None:
        return EffectAdmissionRefusal("decision_malformed")
    if planning.get("operation_id") != manifest.operation_id:
        return EffectAdmissionRefusal("operation_id_mismatch")
    binding = planning.get("binding")
    if not isinstance(binding, Mapping):
        return EffectAdmissionRefusal("decision_binding_missing")
    bound_digest = _binding_manifest_digest(binding)
    if bound_digest is None:
        return EffectAdmissionRefusal("decision_binding_missing")
    if bound_digest != manifest.digest:
        return EffectAdmissionRefusal("manifest_digest_mismatch")

    decision_id = planning.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        return EffectAdmissionRefusal("decision_id_missing")

    proposal_id: str | None = None
    authority_id: str | None = None
    if proposal_event is not None:
        proposal_data = proposal_event.get("data")
        if not isinstance(proposal_data, Mapping):
            return EffectAdmissionRefusal("proposal_malformed")
        proposal_id = proposal_data.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            return EffectAdmissionRefusal("proposal_id_missing")
        if authority_event is None:
            return EffectAdmissionRefusal("authority_missing")
        authority_data = authority_event.get("data")
        if not isinstance(authority_data, Mapping):
            return EffectAdmissionRefusal("authority_malformed")
        if authority_data.get("human_decision") not in {"approval", "consent"}:
            return EffectAdmissionRefusal("authority_not_first_party")
        if authority_data.get("proposal_id") != proposal_id:
            return EffectAdmissionRefusal("authority_proposal_mismatch")
        if authority_data.get("decision_id") != decision_id:
            return EffectAdmissionRefusal("authority_decision_mismatch")
        authority_event_id = authority_event.get("event_id")
        if not isinstance(authority_event_id, str) or not authority_event_id.strip():
            return EffectAdmissionRefusal("authority_id_missing")
        authority_id = authority_event_id

    intent_disposition = disposition
    if disposition in {"refuse", "refused"}:
        intent_disposition = "refused"
    elif disposition != "execute":
        return EffectAdmissionRefusal(f"disposition_{disposition}")

    try:
        intent_data = build_effect_intent_event(
            manifest,
            disposition=intent_disposition,
            intent_id=intent_id,
            decision_id=decision_id,
            proposal_id=proposal_id,
            authority_id=authority_id,
        )
    except EffectError as exc:
        return EffectAdmissionRefusal(str(exc))

    token = _admission_handle_token(intent_id, manifest.digest)
    return PreparedEffectAdmission(
        intent_id=intent_id,
        receipt_id=receipt_id,
        intent_data=intent_data,
        handle_token=token,
        operation_id=manifest.operation_id,
        manifest_digest=manifest.digest,
    )

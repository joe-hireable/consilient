"""Gated capability admission is derived fail-closed from manifest and inventory facts."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient.capabilities import (
    CapabilityEntry,
    CapabilityError,
    Gate,
    default_gate,
    parse_inventory_entry,
)
from consilient import effects as effects_mod
from consilient.effects import (
    ADMISSION_CLASSES,
    ADMISSION_DISPOSITIONS,
    AdmissionFacts,
    EffectManifest,
    derive_admission,
    OUTBOUND_EFFECTS,
)


def commitment(domain: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": "a" * 64,
    }


def broker_reference(name: str) -> dict[str, str]:
    return {"kind": "broker_reference", "reference": f"broker://effects/{name}"}


def authority_event(event_id: str = "evt-authority-1") -> dict[str, object]:
    return {"event_id": event_id, "event_kind": "human.approval", "event_sha256": "b" * 64}


def recovery_proof_ref() -> dict[str, object]:
    return {"event_id": "evt-proof-1", "event_kind": "effect.receipt", "event_sha256": "c" * 64}


def manifest(
    *,
    effects: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
    gate_digest: str = "d" * 64,
) -> EffectManifest:
    # Unit B01 made `disclosure` REQUIRED for outbound message.send effects, and permitted ONLY
    # for those. This helper predates that contract, so it supplies the digest exactly when the
    # effect set calls for it. Relaxing B01 to accept an outbound send with no disclosure would
    # delete the guarantee that a message this system emits is always traceable to what it
    # disclosed -- which is the point of the field.
    disclosure = "b" * 64 if set(effects) & OUTBOUND_EFFECTS else None
    return EffectManifest(
        disclosure=disclosure,
        operation_id="operation-1",
        work_item_id="work-1",
        attempt_id="attempt-1",
        adapter={
            "id": "test.adapter",
            "version": "v1",
            "implementation_digest": "e" * 64,
        },
        forward=commitment("effect.forward"),
        scope=broker_reference("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": gate_digest},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=commitment("effect.start-state"),
        observer={"id": "observer-1", "policy_digest": "1" * 64},
        expected_state=commitment("effect.expected-state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def admitted_gate(
    *,
    grant_kind: str = "controller_baseline.local_restorable.v1",
    effect_classes: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
    scope: tuple[str, ...] = ("workspace"),
    expires_at: str | None = None,
    decision_id: str | None = "decision-1",
    recovery_proof_ref_value: object | None = recovery_proof_ref(),
    authority_event_value: object | None = None,
) -> Gate:
    if expires_at is None:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    return Gate(
        state="admitted",
        reason="exact_grant",
        grant_kind=grant_kind,
        authority_event=authority_event_value,
        decision_id=decision_id,
        recovery_proof_ref=recovery_proof_ref_value,
        scope=scope,
        operations=operations,
        effect_classes=effect_classes,
        expires_at=expires_at,
    )


def capability_entry(
    *,
    available: bool = True,
    gate: Gate | None = None,
) -> CapabilityEntry:
    return CapabilityEntry(
        kind="tool",
        name="pytest",
        available=available,
        provenance=("probe:tool:pytest",),
        gate=gate or default_gate(),
    )


def test_admission_enums_are_closed() -> None:
    assert ADMISSION_CLASSES == frozenset(
        {
            "observation",
            "contained_execution",
            "proof_operation",
            "material_choice",
            "recoverable_mutation",
            "protected_covered",
            "protected_uncovered",
            "capability_gap",
        }
    )
    assert ADMISSION_DISPOSITIONS == frozenset({"execute", "reshape", "refuse", "escalate"})


def test_inventory_parser_rejects_malformed_gate_shape() -> None:
    with pytest.raises(CapabilityError, match="gate"):
        parse_inventory_entry(
            {
                "kind": "tool",
                "name": "pytest",
                "available": True,
                "provenance": ["probe:tool:pytest"],
                "gate": {"state": "gated"},
            }
        )


def test_inventory_without_gate_synthesises_gated_default() -> None:
    entry = parse_inventory_entry(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
        }
    )
    assert entry.gate.state == "gated"
    assert entry.gate.reason == "no_matching_grant"


def test_pure_observation_admits_with_read_only_effects() -> None:
    result = derive_admission(
        manifest(effects=("data.read",), operations=("read",)),
        capability_entry(gate=admitted_gate()),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "observation"
    assert result.disposition == "execute"
    assert result.reason == "exact_grant"


def test_observation_refuses_when_broker_does_not_confirm() -> None:
    result = derive_admission(
        manifest(effects=("data.read",), operations=("read",)),
        capability_entry(gate=admitted_gate()),
        AdmissionFacts(broker_confirms_observation=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"


def test_present_but_gated_capability_refuses_without_handle() -> None:
    result = derive_admission(
        manifest(),
        capability_entry(gate=default_gate()),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert "no_matching_grant" in result.reason


def test_unavailable_capability_is_capability_gap() -> None:
    result = derive_admission(
        manifest(),
        capability_entry(available=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"


def test_expired_grant_refuses() -> None:
    expired = admitted_gate(
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )
    result = derive_admission(
        manifest(),
        capability_entry(gate=expired),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "grant_expired"


def test_scope_mismatch_refuses() -> None:
    gate = admitted_gate(operations=("write",))
    result = derive_admission(
        manifest(operations=("read",)),
        capability_entry(gate=gate),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "operation_mismatch"


def test_effect_class_mismatch_refuses() -> None:
    gate = admitted_gate(effect_classes=("network.call",))
    result = derive_admission(
        manifest(effects=("data.read",)),
        capability_entry(gate=gate),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "effect_class_mismatch"


def test_exact_admitted_facts_execute_recoverable_mutation() -> None:
    gate = admitted_gate(
        effect_classes=("file.change",),
        operations=("write",),
    )
    result = derive_admission(
        manifest(effects=("file.change",), operations=("write",)),
        capability_entry(gate=gate),
        AdmissionFacts(recovery_proof_passed=True),
    )
    assert result.admission == "recoverable_mutation"
    assert result.disposition == "execute"


def test_failed_recovery_reshapes_not_escalates() -> None:
    gate = admitted_gate(
        effect_classes=("file.change",),
        operations=("write",),
    )
    result = derive_admission(
        manifest(effects=("file.change",), operations=("write",)),
        capability_entry(gate=gate),
        AdmissionFacts(recovery_proof_passed=False),
    )
    assert result.admission == "recoverable_mutation"
    assert result.disposition == "reshape"
    assert result.reason == "recovery_proof_failed"


def test_proof_operation_classifies_isolated_recovery() -> None:
    gate = admitted_gate(
        effect_classes=("file.change",),
        operations=("proof",),
    )
    result = derive_admission(
        manifest(effects=("file.change",), operations=("proof",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_proof_operation=True, contained=True),
    )
    assert result.admission == "proof_operation"
    assert result.disposition == "execute"


def test_contained_execution_requires_containment() -> None:
    gate = admitted_gate(
        effect_classes=("process.run",),
        operations=("run",),
    )
    result = derive_admission(
        manifest(effects=("process.run",), operations=("run",)),
        capability_entry(gate=gate),
        AdmissionFacts(contained=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "process_not_contained"


def test_contained_execution_admits_when_sandbox_proved() -> None:
    gate = admitted_gate(
        effect_classes=("process.run",),
        operations=("run",),
    )
    result = derive_admission(
        manifest(effects=("process.run",), operations=("run",)),
        capability_entry(gate=gate),
        AdmissionFacts(contained=True),
    )
    assert result.admission == "contained_execution"
    assert result.disposition == "execute"


def test_material_choice_without_live_effect() -> None:
    gate = admitted_gate(
        effect_classes=("data.read",),
        operations=("plan",),
    )
    result = derive_admission(
        manifest(effects=("data.read",), operations=("plan",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_material_choice=True),
    )
    assert result.admission == "material_choice"
    assert result.disposition == "execute"


def test_protected_uncovered_escalates() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("spend",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("spend",)),
        capability_entry(gate=gate),
        AdmissionFacts(authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_protected_covered_executes_with_standing_authority() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("spend",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=authority_event(),
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("spend",)),
        capability_entry(gate=gate),
        AdmissionFacts(authority_standing=True),
    )
    assert result.admission == "protected_covered"
    assert result.disposition == "execute"


@pytest.mark.parametrize(
    "escalation_effect",
    (
        "money.commit",
        "message.send",
        "content.publish",
        "external.change",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
    ),
)
def test_each_protected_escalation_effect_maps_to_protected_class(
    escalation_effect: str,
) -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=(escalation_effect,),
        operations=("act",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=(escalation_effect,), operations=("act",)),
        capability_entry(gate=gate),
        AdmissionFacts(authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_caller_supplied_principal_actor_cannot_mint_authority() -> None:
    """Production break: actor: principal in an event must not widen gate admission."""
    gated = capability_entry(gate=default_gate())
    principal_event = {
        "actor": "principal",
        "via": "cli",
        "human_decision": "approval",
    }
    result = derive_admission(
        manifest(),
        gated,
        AdmissionFacts(caller_metadata=principal_event),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"


def test_project_gate_snapshot_change_does_not_alter_admission() -> None:
    gate = admitted_gate()
    entry = capability_entry(gate=gate)
    facts = AdmissionFacts(broker_confirms_observation=True, project_gates_open=True)
    first = derive_admission(manifest(gate_digest="a" * 64), entry, facts)
    second = derive_admission(manifest(gate_digest="b" * 64), entry, facts)
    assert first == second


def test_derive_admission_is_pure_no_handle_issued() -> None:
    result = derive_admission(
        manifest(),
        capability_entry(gate=admitted_gate()),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert set(result.__dict__) == {"admission", "disposition", "reason"}


def test_composite_manifest_inherits_least_recoverable_atom() -> None:
    gate = admitted_gate(
        effect_classes=("data.read", "money.commit"),
        operations=("read", "spend"),
        grant_kind="principal_authority",
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("data.read", "money.commit"), operations=("read", "spend")),
        capability_entry(gate=gate),
        AdmissionFacts(authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_material_choice_flag_cannot_cover_uncovered_money_commit() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("spend",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("spend",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_material_choice=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_proof_operation_flag_cannot_cover_uncovered_money_commit() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("spend",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("spend",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_proof_operation=True, contained=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_planning_operations_cannot_launder_protected_effects() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("plan",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("plan",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_material_choice=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_proof_operations_cannot_launder_protected_effects() -> None:
    gate = admitted_gate(
        grant_kind="principal_authority",
        effect_classes=("money.commit",),
        operations=("proof",),
        decision_id=None,
        recovery_proof_ref_value=None,
        authority_event_value=None,
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("proof",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_proof_operation=True, contained=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_proof_operation_flag_cannot_uncontain_process_run() -> None:
    gate = admitted_gate(
        effect_classes=("process.run",),
        operations=("run",),
    )
    result = derive_admission(
        manifest(effects=("process.run",), operations=("run",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_proof_operation=True, contained=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "process_not_contained"


def test_material_choice_flag_cannot_uncontain_process_run() -> None:
    gate = admitted_gate(
        effect_classes=("process.run",),
        operations=("run",),
    )
    result = derive_admission(
        manifest(effects=("process.run",), operations=("run",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_material_choice=True, contained=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "process_not_contained"


def test_material_choice_flag_without_planning_operations_is_ignored() -> None:
    result = derive_admission(
        manifest(effects=("data.read",), operations=("read",)),
        capability_entry(gate=admitted_gate()),
        AdmissionFacts(is_material_choice=True, broker_confirms_observation=True),
    )
    assert result.admission == "observation"
    assert result.disposition == "execute"


def test_proof_operation_without_containment_does_not_execute() -> None:
    gate = admitted_gate(
        effect_classes=("file.change",),
        operations=("proof",),
    )
    result = derive_admission(
        manifest(effects=("file.change",), operations=("proof",)),
        capability_entry(gate=gate),
        AdmissionFacts(is_proof_operation=True, contained=False),
    )
    assert result.disposition != "execute"
    assert result.admission != "proof_operation"


def test_planning_operations_constant_is_deleted() -> None:
    assert not hasattr(effects_mod, "PLANNING_OPERATIONS")


def _function_source(name: str) -> str:
    source = Path(effects_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            segment = ast.get_source_segment(source, node)
            if segment is None:
                raise AssertionError(f"{name} has no source segment")
            return segment
    raise AssertionError(f"{name} is missing")


def test_disposition_for_has_no_unreachable_arms() -> None:
    text = _function_source("_disposition_for")
    assert "capability_gap" not in text
    assert "unhandled_admission_class" not in text
    assert "process_not_contained" not in text


def test_derive_admission_documents_that_it_is_unwired() -> None:
    doc = derive_admission.__doc__ or ""
    assert "ADR-0078" in doc
    assert "unwired" in doc.casefold()


def test_derive_admission_has_no_production_caller() -> None:
    callers: list[str] = []
    root = Path(effects_mod.__file__).resolve().parent
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else ""
            )
            if called != "derive_admission":
                continue
            if path.resolve() == Path(effects_mod.__file__).resolve():
                continue
            callers.append(f"{path.name}:{node.lineno}")
    assert callers == []

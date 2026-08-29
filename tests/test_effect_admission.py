"""Gated capability admission is derived fail-closed from manifest and inventory facts.

Core derivation: what the ladder decides when the facts are what they claim to be. The three
siblings cover what it must REFUSE to decide -- see test_effect_admission_laundering.py
(no flag buys coverage), _containment.py (process.run) and _structure.py (source-level pins).
"""

from datetime import datetime, timedelta, timezone

import pytest

from consilient.capabilities import (
    CapabilityError,
    default_gate,
    parse_inventory_entry,
)

from consilient.effects import (
    ADMISSION_CLASSES,
    ADMISSION_DISPOSITIONS,
    AdmissionFacts,
    derive_admission,
)

from effect_admission_helpers import (
    admitted_gate,
    authority_event,
    capability_entry,
    manifest,
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
    assert ADMISSION_DISPOSITIONS == frozenset(
        {"execute", "reshape", "refuse", "escalate"}
    )


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
        capability_entry(available=False, gate=admitted_gate()),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "capability_unavailable"


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
    result = derive_admission(
        manifest(),
        capability_entry(gate=admitted_gate(scope=("workspace",))),
        AdmissionFacts(
            broker_confirms_observation=True, requested_scope=("other-repo",)
        ),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "scope_mismatch"


def test_workspace_and_other_repo_scopes_differ() -> None:
    facts = AdmissionFacts(
        broker_confirms_observation=True, requested_scope=("workspace",)
    )
    workspace = derive_admission(
        manifest(),
        capability_entry(gate=admitted_gate(scope=("workspace",))),
        facts,
    )
    other_repo = derive_admission(
        manifest(),
        capability_entry(gate=admitted_gate(scope=("other-repo",))),
        facts,
    )
    assert workspace != other_repo
    assert workspace.disposition == "execute"
    assert other_repo.reason == "scope_mismatch"


def test_operation_mismatch_refuses() -> None:
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

"""No flag, claim or caller-supplied fact buys coverage it was not granted.

Every test here is the same shape: assert some input a CALLER controls cannot move an effect
from protected_uncovered to execute. That is the fail-open this module exists to prevent, and
it is worth its own file because the tests are adversarial rather than descriptive -- they
document attacks that were tried, not behaviour that was specified.
"""

import pytest

from consilient.capabilities import (
    CapabilityError,
    Gate,
    default_gate,
    parse_inventory_entry,
)

from consilient import effects as effects_mod

from consilient.effects import (
    AdmissionFacts,
    derive_admission,
)

from effect_admission_helpers import (
    admitted_gate,
    admitted_inventory_payload,
    capability_entry,
    manifest,
    recovery_proof_ref,
)


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
        AdmissionFacts(
            is_proof_operation=True, contained=True, authority_standing=False
        ),
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
        AdmissionFacts(
            is_proof_operation=True, contained=True, authority_standing=False
        ),
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


def test_controller_baseline_cannot_cover_protected_reach() -> None:
    with pytest.raises(CapabilityError, match="protected"):
        parse_inventory_entry(
            admitted_inventory_payload(
                effect_classes=["money.commit"],
                operations=["spend"],
            )
        )
    gate = admitted_gate(
        grant_kind="controller_baseline.local_restorable.v1",
        effect_classes=("money.commit",),
        operations=("spend",),
    )
    result = derive_admission(
        manifest(effects=("money.commit",), operations=("spend",)),
        capability_entry(gate=gate),
        AdmissionFacts(authority_standing=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "grant_kind_forbids_protected_reach"


def test_caller_authority_standing_cannot_cover_missing_authority_event() -> None:
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
        AdmissionFacts(authority_standing=True),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"
    assert result.admission != "protected_covered"


def test_admitted_gate_without_expiry_refuses() -> None:
    with pytest.raises(CapabilityError, match="expires_at"):
        parse_inventory_entry(admitted_inventory_payload(expires_at=None))
    gate = Gate(
        state="admitted",
        reason="exact_grant",
        grant_kind="controller_baseline.local_restorable.v1",
        authority_event=None,
        decision_id="decision-1",
        recovery_proof_ref=recovery_proof_ref(),
        scope=("workspace",),
        operations=("read",),
        effect_classes=("data.read",),
        expires_at=None,
    )
    result = derive_admission(
        manifest(),
        capability_entry(gate=gate),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "grant_missing_expiry"

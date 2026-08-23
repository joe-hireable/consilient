"""S01 — immutable promoter policy and impact contract (ADR-0076)."""

from __future__ import annotations

import pytest

from consilient import beta as beta_mod
from consilient.promote import (
    ACTOR,
    CANONICAL_ON_OTHER,
    CONTRACT_MUTATED,
    EXP104_BLOCKED,
    EXP104_CONFIRMED,
    EXP104_EXPERIMENT_ID,
    GENERIC_BETA_SUBSTITUTION,
    IMPACT_CONTRACT_KIND,
    ImpactContract,
    MechanicalClass,
    PromoterBetaReceipt,
    PromoteError,
    ACTIVATION_REFUSED,
    PROMOTER_BETA_RECEIPT_KIND,
    exp104_impact_contract,
    contract_digest,
    decide_active_harness_activation,
    mechanical_disposition,
    record_activation_refusal,
    record_impact_contract,
    record_promoter_beta_receipt,
)
from consilient.events import read_all


def _valid_contract(**over: object) -> ImpactContract:
    base = exp104_impact_contract()
    if not over:
        return base
    payload = {
        "experiment_id": base.experiment_id,
        "target_surface": base.target_surface,
        "baseline_digests": dict(base.baseline_digests),
        "on_confirm": base.on_confirm,
        "on_kill": base.on_kill,
        "on_other": base.on_other,
        "confirm_rule": base.confirm_rule,
        "kill_rule": base.kill_rule,
        "horizon": base.horizon,
        "largest_effect": base.largest_effect,
        "safety_floor_version": base.safety_floor_version,
        "mechanical_class": base.mechanical_class,
    }
    payload.update(over)
    return ImpactContract(**payload)


def _promoter_receipt(
    contract: ImpactContract,
    *,
    n_rejected: int = 30,
    false_accepts: int = 3,
) -> PromoterBetaReceipt:
    interval = beta_mod.wilson(false_accepts, n_rejected)
    return PromoterBetaReceipt.from_counts(
        experiment_id=contract.experiment_id,
        qualification_rule_digest=contract.baseline_digests["qualification_rule"],
        decision_surface_digest=contract.baseline_digests["decision_surface"],
        instrument_digest=contract.baseline_digests["instrument"],
        generator_policy_digest=contract.baseline_digests["generator_policy"],
        sampling_frame_digest=contract.baseline_digests["sampling_frame"],
        interval_rule_digest=contract.baseline_digests["interval_rule"],
        n_human_rejected=n_rejected,
        n_false_accept=false_accepts,
        wilson_interval=interval,
    )


def test_impact_contract_rejects_weakened_on_other():
    with pytest.raises(ValueError, match="on_other"):
        _valid_contract(on_other="activate on ambiguity")


def test_impact_contract_digest_is_stable():
    contract = exp104_impact_contract()
    again = exp104_impact_contract()
    assert contract_digest(contract) == contract_digest(again)
    assert len(contract_digest(contract)) == 64


def test_mutated_contract_digest_refuses_activation():
    contract = _valid_contract()
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest="0000000000000000000000000000000000000000000000000000000000000000",
        promoter_beta=None,
        exp104_status=EXP104_BLOCKED,
    )
    assert decision.action == "refuse"
    assert decision.reason == CONTRACT_MUTATED


def test_missing_contract_refuses_activation():
    decision = decide_active_harness_activation(
        contract=None,
        registration_digest=None,
        promoter_beta=None,
        exp104_status=EXP104_BLOCKED,
    )
    assert decision.action == "refuse"
    assert decision.reason == "contract_missing"


def test_generic_beta_substitution_refuses_activation():
    contract = _valid_contract()
    generic = beta_mod.Beta(
        beta_mod.MEASURED,
        "self-mod-fixture",
        "exp78-training-v1",
        30,
        3,
        0.1,
        beta_mod.wilson(3, 30),
        ("2026-08-01T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
        False,
    )
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=generic,
        exp104_status=EXP104_BLOCKED,
    )
    assert decision.action == "refuse"
    assert decision.reason == GENERIC_BETA_SUBSTITUTION


def test_blocked_exp104_refuses_even_with_valid_receipt():
    contract = _valid_contract()
    receipt = _promoter_receipt(contract)
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=receipt,
        exp104_status=EXP104_BLOCKED,
    )
    assert decision.action == "refuse"
    assert decision.reason == EXP104_BLOCKED


def test_unconfirmed_exp104_refuses():
    contract = _valid_contract()
    receipt = _promoter_receipt(contract)
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=receipt,
        exp104_status="registered",
    )
    assert decision.action == "refuse"
    assert decision.reason == "exp104_not_confirmed"


def test_confirmed_exp104_still_refuses_without_full_evidence():
    contract = _valid_contract()
    receipt = _promoter_receipt(contract)
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=receipt,
        exp104_status=EXP104_CONFIRMED,
    )
    assert decision.action == "refuse"
    assert decision.reason != EXP104_CONFIRMED


@pytest.mark.parametrize(
    ("mechanical_class", "disposition"),
    (
        (MechanicalClass.CANDIDATE_ONLY, "autonomous"),
        (MechanicalClass.SENSING_ONLY, "autonomous"),
        (MechanicalClass.ACTIVE_HARNESS, "principal_required"),
        (MechanicalClass.INSTRUMENT, "refused"),
        (MechanicalClass.EXACT_ROLLBACK, "autonomous"),
        (MechanicalClass.EXISTING_PRINCIPAL_EFFECT, "refused"),
        (MechanicalClass.UNKNOWN_OR_MIXED, "capability_gap"),
    ),
)
def test_mechanical_class_dispositions(mechanical_class: str, disposition: str):
    assert mechanical_disposition(mechanical_class) == disposition


def test_record_impact_contract_writes_schema(tmp_path):
    contract = exp104_impact_contract()
    recorded = record_impact_contract(tmp_path, contract)
    assert recorded["event"] == IMPACT_CONTRACT_KIND
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert events[0].kind == IMPACT_CONTRACT_KIND
    assert events[0].actor == ACTOR
    assert events[0].data["experiment_id"] == EXP104_EXPERIMENT_ID
    assert events[0].data["registration_digest"] == contract_digest(contract)


def test_record_promoter_beta_receipt_writes_schema(tmp_path):
    contract = exp104_impact_contract()
    receipt = _promoter_receipt(contract)
    recorded = record_promoter_beta_receipt(tmp_path, receipt)
    assert recorded["event"] == PROMOTER_BETA_RECEIPT_KIND
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert events[0].data["receipt_kind"] == "promoter_beta"


def test_record_activation_refusal_for_blocked_exp104(tmp_path):
    contract = exp104_impact_contract()
    decision = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=None,
        exp104_status=EXP104_BLOCKED,
    )
    recorded = record_activation_refusal(tmp_path, decision)
    assert recorded["event"] == ACTIVATION_REFUSED
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert events[0].data["reason"] == EXP104_BLOCKED


def test_promoter_receipt_rejects_mismatched_experiment():
    contract = _valid_contract(experiment_id="EXP-999")
    receipt = _promoter_receipt(exp104_impact_contract())
    assert not receipt.matches_contract(contract)


def test_exp104_contract_matches_register_floor():
    contract = exp104_impact_contract()
    assert contract.on_other == CANONICAL_ON_OTHER
    assert contract.mechanical_class == MechanicalClass.ACTIVE_HARNESS
    assert contract.safety_floor_version == "adr-0076-v0"


def test_impact_contract_payload_round_trip():
    contract = exp104_impact_contract()
    restored = ImpactContract.from_mapping(contract.as_dict())
    assert contract_digest(restored) == contract_digest(contract)


def test_record_activation_refusal_rejects_promote_action(tmp_path):
    contract = exp104_impact_contract()
    forged = decide_active_harness_activation(
        contract=contract,
        registration_digest=contract_digest(contract),
        promoter_beta=None,
        exp104_status=EXP104_BLOCKED,
    )
    forged = type(forged)(
        "promote", forged.reason, forged.contract, forged.registration_digest
    )
    with pytest.raises(PromoteError, match="activation refusal"):
        record_activation_refusal(tmp_path, forged)

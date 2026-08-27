"""Canonical effect records stay inert while their schema is enforced."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from math import inf, nan
from pathlib import Path

import pytest

from consilient import effects as effects_mod
from consilient import events as events_mod
from consilient.capabilities import CapabilityEntry, Gate
from consilient.effects import (
    EFFECT_CLASSES,
    EFFECT_INTENT,
    EFFECT_RECEIPT,
    MUTATION_EFFECTS,
    OUTBOUND_EFFECTS,
    READ_ONLY_EFFECTS,
    AdmissionFacts,
    EffectError,
    EffectManifest,
    derive_admission,
    receipt_chain_validator,
)
from consilient.events import (
    EventError,
    Rejection,
    SCHEMA_VERSION,
    append,
    append_transaction,
    validate,
)


def event(
    kind: str, data: dict[str, object], *, ts: str | None = None
) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": "effect-contract-test",
        "data": data,
    }


def commitment(domain: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": "a" * 64,
    }


def broker_reference(name: str) -> dict[str, str]:
    del name
    return {"kind": "broker_reference", "reference": f"broker://effects/{'a' * 64}"}


def manifest() -> EffectManifest:
    return EffectManifest(
        operation_id="operation-1",
        work_item_id="work-1",
        attempt_id="attempt-1",
        adapter={
            "id": "test.adapter",
            "version": "v1",
            "implementation_digest": "b" * 64,
        },
        forward=commitment("effect.manifest.forward"),
        scope=broker_reference("scope"),
        operations=("read",),
        effects=("data.read",),
        inventory_snapshot={"digest": "c" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "e" * 64},
        start_state=commitment("effect.manifest.start_state"),
        observer={"id": "observer-1", "policy_digest": "f" * 64},
        expected_state=commitment("effect.manifest.expected_state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def intent_data(
    manifest_value: EffectManifest, *, observation: bool = False
) -> dict[str, object]:
    return {
        "intent_id": "intent-1",
        "manifest": manifest_value.binding(),
        "disposition": "refused",
        "decision_id": None if observation else "decision-1",
        "admission": (
            {"kind": "observation", "observation_id": "observation-1"}
            if observation
            else {
                "kind": "material",
                "authority_chain": {
                    "kind": "autonomous_decision",
                    "decision_id": "decision-1",
                },
            }
        ),
    }


def receipt_data(
    *, receipt_id: str, status: str, supersedes: str | None = None
) -> dict[str, object]:
    data: dict[str, object] = {
        "receipt_id": receipt_id,
        "intent_id": "intent-1",
        "manifest_digest": manifest().digest,
        "status": status,
        "started_at": "2026-08-23T10:00:00+00:00",
        "ended_at": "2026-08-23T10:00:01+00:00",
        "provider_request": broker_reference("provider-request"),
        "provider_receipt": broker_reference("provider-receipt"),
        "request_commitment": commitment("effect.receipt.request"),
        "response_commitment": commitment("effect.receipt.response"),
        "content_commitment": commitment("effect.receipt.content"),
        "observed_consumption": {"cpu_seconds": 1},
        "post_state": commitment("effect.receipt.post_state"),
        "observed_residuals": ("elapsed_time",),
        "child_operation_ids": (),
    }
    if supersedes is not None:
        data["supersedes"] = supersedes
    return data


_MISSING = object()
DISCLOSURE_DIGEST = "9" * 64


def outbound_record(
    *,
    operation: str = "send_email",
    disclosure: object = _MISSING,
    **overrides: object,
) -> dict[str, object]:
    record = manifest().to_record()
    record["effects"] = ["message.send"]
    record["operations"] = [operation]
    if disclosure is not _MISSING:
        record["disclosure"] = disclosure
    record.update(overrides)
    return record


def test_effect_classes_are_exact_and_manifest_digest_is_set_canonical() -> None:
    """Production break caught: a padded/case-varied effect could enter the manifest.

    Production break caught: malformed classes or their order change a composite manifest.
    """
    assert EFFECT_CLASSES == frozenset(
        {
            "file.change",
            "data.read",
            "process.run",
            "system.change",
            "network.call",
            "external.change",
            "message.send",
            "content.publish",
            "money.commit",
            "obligation.commit",
            "authority.change",
            "physical.actuate",
        }
    )
    composite = manifest().to_record()
    composite["effects"] = ["data.read", "network.call"]
    composite["operations"] = ["inspect", "read"]
    composite["declared_residuals"] = ["elapsed_time", "logs"]
    reversed_composite = {
        **composite,
        "effects": ["network.call", "data.read"],
        "operations": ["read", "inspect"],
        "declared_residuals": ["logs", "elapsed_time"],
    }
    assert (
        EffectManifest.from_record(composite).digest
        == EffectManifest.from_record(reversed_composite).digest
    )

    for malformed in (
        [],
        ["Data.Read"],
        [" data.read"],
        ["unknown.effect"],
        ["data.read", "data.read"],
        [1],
    ):
        with pytest.raises(EffectError, match="effect|empty|duplicate"):
            EffectManifest.from_record({**manifest().to_record(), "effects": malformed})
    missing = manifest().to_record()
    del missing["effects"]
    with pytest.raises(EffectError, match="missing"):
        EffectManifest.from_record(missing)


def test_a_composite_manifest_retains_every_applicable_effect_class() -> None:
    """A01's review found this failing: truncating a composite manifest's `effects` --
    or dropping `effects` from `canonical()` entirely -- left `python -m pytest
    tests/test_effect_contract.py -q` passing regardless, because the only existing
    composite check compares digests of reversed class order, which stay equal after both
    sides are truncated or after both drop the field the same way."""
    two_classes = EffectManifest.from_record(
        {**manifest().to_record(), "effects": ["data.read", "network.call"]}
    )
    two_classes_effects = two_classes.to_record()["effects"]
    assert isinstance(two_classes_effects, (list, tuple))
    assert set(two_classes_effects) == {"data.read", "network.call"}

    one_class = EffectManifest.from_record(
        {**manifest().to_record(), "effects": ["data.read"]}
    )
    assert two_classes.digest != one_class.digest, (
        "truncating a composite manifest's effect classes -- or dropping 'effects' from "
        "canonical() entirely, which would erase this same difference -- must change its digest"
    )


def test_manifest_rejects_non_finite_ceilings() -> None:
    """Production break caught: NaN/Infinity survives canonical JSON and changes its digest."""
    for ceiling in (nan, inf, -inf):
        value = manifest().to_record()
        value["ceilings"] = {"wall_time_s": ceiling}
        with pytest.raises(EffectError, match="finite"):
            EffectManifest.from_record(value)
    value = manifest().to_record()
    value["ceilings"] = {"wall_time_s": 10**1000}
    assert EffectManifest.from_record(value).to_record()["ceilings"] == {
        "wall_time_s": 10**1000
    }


def test_manifest_rejects_raw_private_values_and_credentials() -> None:
    """Production break caught: caller labels permit secrets or an unkeyed shared commitment."""
    raw = manifest().to_record()
    raw["forward"] = {"credential": "hunter2"}
    with pytest.raises(EffectError, match="broker reference|commitment"):
        EffectManifest.from_record(raw)
    opaque = manifest().to_record()
    opaque["scope"] = {"kind": "broker_reference", "reference": "hunter2"}
    with pytest.raises(EffectError, match="opaque"):
        EffectManifest.from_record(opaque)
    unkeyed = manifest().to_record()
    unkeyed["forward"] = commitment("effect.manifest.forward")
    unkeyed["forward"]["algorithm"] = "sha256"
    with pytest.raises(EffectError, match="hmac-sha256"):
        EffectManifest.from_record(unkeyed)
    shared_domain = manifest().to_record()
    shared_domain["start_state"] = commitment("effect.manifest.forward")
    with pytest.raises(EffectError, match="domain"):
        EffectManifest.from_record(shared_domain)


def test_effect_events_validate_the_observation_and_material_discriminants() -> None:
    """Production break caught: material reach can omit a decision/authority chain."""
    value = manifest()
    validate(event("effect.intent", intent_data(value, observation=True)))
    validate(event("effect.intent", intent_data(value)))

    invalid = intent_data(value, observation=True)
    invalid["decision_id"] = "decision-1"
    with pytest.raises(EventError, match="observation"):
        validate(event("effect.intent", invalid))

    invalid = intent_data(value)
    invalid["admission"] = {"kind": "material", "authority_chain": []}
    with pytest.raises(EventError, match="authority chain"):
        validate(event("effect.intent", invalid))

    reference = intent_data(value)
    reference["manifest"] = {
        "kind": "reference",
        "reference": broker_reference("manifest"),
        "digest": value.digest,
    }
    validate(event("effect.intent", reference))


def test_receipt_fields_reject_raw_provider_payloads() -> None:
    """Production break caught: a provider response/content payload is persisted verbatim."""
    payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
    payload["provider_receipt"] = {"response": "private reply"}
    with pytest.raises(EventError, match="broker reference|commitment"):
        validate(event("effect.receipt", payload))
    for amount in (nan, inf, -inf):
        payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
        payload["observed_consumption"] = {"cpu_seconds": amount}
        with pytest.raises(EventError, match="finite"):
            validate(event("effect.receipt", payload))
    payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
    payload["observed_consumption"] = {"cpu_seconds": 10**1000}
    validate(event("effect.receipt", payload))


def test_receipt_binds_the_manifest_digest_of_its_intent(tmp_path) -> None:
    """Production break caught: a receipt can be filed against a different manifest."""
    value = manifest()
    path = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append_transaction(
        tmp_path,
        [event("effect.intent", intent_data(value))],
        lambda prefix, rejections, candidates: None,
    )
    mismatch = receipt_data(receipt_id="receipt-mismatch", status="failed")
    mismatch["manifest_digest"] = "0" * 64
    with pytest.raises(EventError, match="manifest digest"):
        append(path, event("effect.receipt", mismatch))


def test_receipt_chain_allows_one_unknown_resolution_and_refuses_a_fork(
    tmp_path,
) -> None:
    """Production break caught: two receipt heads can claim incompatible outcomes."""
    value = manifest()
    append_transaction(
        tmp_path,
        [
            event("effect.intent", intent_data(value)),
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-unknown", status="unknown"),
            ),
        ],
        lambda prefix, rejections, candidates: None,
    )
    append(
        tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
        event(
            "effect.receipt",
            receipt_data(
                receipt_id="receipt-final",
                status="failed",
                supersedes="receipt-unknown",
            ),
        ),
    )
    with pytest.raises(EventError, match="receipt chain"):
        append(
            tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-fork", status="succeeded"),
            ),
        )


def test_outbound_effects_are_exactly_message_send() -> None:
    """Production break caught: an outbound class drops off the disclosure requirement."""
    assert OUTBOUND_EFFECTS == frozenset({"message.send"})
    assert OUTBOUND_EFFECTS <= EFFECT_CLASSES


@pytest.mark.parametrize("operation", ["send_email", "send_sms"])
def test_outbound_effect_refuses_missing_disclosure(operation: str) -> None:
    """Production break caught: send_email/send_sms can ship with no disclosure hash."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(operation=operation))


def test_outbound_effect_refuses_missing_disclosure_for_any_operation_label() -> None:
    """Production break caught: another operation label must not bypass message.send disclosure."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(operation="send_push"))


@pytest.mark.parametrize(
    "disclosure",
    [
        "",
        "This call is from an automated system.",
        "G" * 64,
        {"kind": "prompt", "text": "I am an AI"},
    ],
)
def test_outbound_effect_refuses_plaintext_or_malformed_disclosure(
    disclosure: object,
) -> None:
    """Production break caught: a prompt-shaped disclosure can be stripped by injection."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(disclosure=disclosure))


def test_outbound_effect_accepts_pre_rendered_disclosure_digest() -> None:
    """A hash of pre-rendered bytes is the only admitted disclosure shape."""
    value = EffectManifest.from_record(outbound_record(disclosure=DISCLOSURE_DIGEST))
    assert value.disclosure == DISCLOSURE_DIGEST
    replayed = EffectManifest.from_record(value.to_record())
    assert replayed.disclosure == DISCLOSURE_DIGEST
    assert replayed.digest == value.digest


def test_non_outbound_manifest_does_not_require_disclosure() -> None:
    """Read-only work is not an outbound effect; disclosure stays optional."""
    value = manifest()
    assert value.disclosure is None
    assert "disclosure" not in value.to_record()


def test_mutation_effects_are_disjoint_from_read_only_effects() -> None:
    """A read-only class in MUTATION_EFFECTS makes the observation predicate lie."""
    assert MUTATION_EFFECTS & READ_ONLY_EFFECTS == frozenset()
    assert "data.read" not in MUTATION_EFFECTS
    assert "network.call" not in MUTATION_EFFECTS


@pytest.mark.parametrize("operation", ["write", "plan"])
def test_observation_intent_refuses_a_mutating_operation(operation: str) -> None:
    """Decision-free observation cannot record a mutating provider operation."""
    record = manifest().to_record()
    record["operations"] = [operation]
    value = EffectManifest.from_record(record)
    with pytest.raises(EventError, match="read-only"):
        validate(event("effect.intent", intent_data(value, observation=True)))


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body if isinstance(tree, ast.Module) else ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is missing")


def test_intent_calls_observation_predicate() -> None:
    """An inline effects-only check misses a mutating operation on a read class."""
    source = Path(effects_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.func.id
        for node in ast.walk(_function_def(tree, "_intent"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_observation_predicate" in names


def test_receipt_chain_resolves_an_unknown_across_daily_logs(
    tmp_path, monkeypatch
) -> None:
    """Production break caught: midnight turns one operation into two receipt chains."""
    monkeypatch.setattr(events_mod, "_check_clock", lambda event: None)
    value = manifest()
    first_day = "2026-08-23T10:00:00+00:00"
    second_day = "2026-08-24T10:00:00+00:00"
    append_transaction(
        tmp_path,
        [
            event("effect.intent", intent_data(value), ts=first_day),
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-unknown", status="unknown"),
                ts=first_day,
            ),
        ],
        lambda prefix, rejections, candidates: None,
    )
    append(
        tmp_path / "2026-08-24.jsonl",
        event(
            "effect.receipt",
            receipt_data(
                receipt_id="receipt-final",
                status="failed",
                supersedes="receipt-unknown",
            ),
            ts=second_day,
        ),
    )


def test_receipt_chain_refuses_a_rejected_effect_history_line() -> None:
    """Production break caught: a corrupt earlier record is ignored while a new chain is admitted."""
    with pytest.raises(EffectError, match="rejected"):
        receipt_chain_validator(
            (),
            (Rejection("effect.jsonl", 1, "malformed", event_kind=EFFECT_INTENT),),
            (),
        )
    with pytest.raises(EffectError, match="rejected"):
        receipt_chain_validator(
            (),
            (Rejection("effect.jsonl", 1, "malformed", event_kind=EFFECT_RECEIPT),),
            (),
        )


def test_receipt_chain_ignores_a_rejection_unrelated_to_the_effect_chain() -> None:
    """A01's review found this failing: a rejected line of *any* kind sharing the log
    directory blocked every write-ahead effect intent, including one with no relation to
    the effect chain at all."""
    receipt_chain_validator((), (Rejection("log.jsonl", 1, "malformed"),), ())
    receipt_chain_validator(
        (), (Rejection("log.jsonl", 1, "malformed", event_kind="note.made"),), ()
    )


def test_effect_records_require_a_jsonl_authority_path(tmp_path) -> None:
    """Production break caught: a non-JSONL append escapes the replayed chain history."""
    path = tmp_path / "effects.log"
    with pytest.raises(EventError, match="JSONL"):
        append(path, event("effect.intent", intent_data(manifest())))
    assert not path.exists()


def _admitted_capability(*, effects: tuple[str, ...], operations: tuple[str, ...]) -> CapabilityEntry:
    return CapabilityEntry(
        kind="tool",
        name="pytest",
        available=True,
        provenance=("probe:tool:pytest",),
        gate=Gate(
            state="admitted",
            reason="exact_grant",
            grant_kind="principal_authority",
            authority_event=None,
            decision_id=None,
            recovery_proof_ref=None,
            scope=("workspace",),
            operations=operations,
            effect_classes=effects,
            expires_at="2099-01-01T00:00:00+00:00",
        ),
    )


def _manifest_with(*, effects: tuple[str, ...], operations: tuple[str, ...]) -> EffectManifest:
    record = manifest().to_record()
    record["effects"] = list(effects)
    record["operations"] = list(operations)
    if set(effects) & OUTBOUND_EFFECTS:
        record["disclosure"] = "9" * 64
    return EffectManifest.from_record(record)


def test_material_choice_flag_cannot_cover_uncovered_money_commit() -> None:
    """Caller-supplied is_material_choice must not execute unprotected spend."""
    result = derive_admission(
        _manifest_with(effects=("money.commit",), operations=("spend",)),
        _admitted_capability(effects=("money.commit",), operations=("spend",)),
        AdmissionFacts(is_material_choice=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_proof_operation_flag_cannot_cover_uncovered_money_commit() -> None:
    """Caller-supplied is_proof_operation must not execute unprotected spend."""
    result = derive_admission(
        _manifest_with(effects=("money.commit",), operations=("spend",)),
        _admitted_capability(effects=("money.commit",), operations=("spend",)),
        AdmissionFacts(is_proof_operation=True, contained=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_proof_operation_flag_cannot_uncontain_process_run() -> None:
    """Caller-supplied is_proof_operation must not execute an uncontained process."""
    result = derive_admission(
        _manifest_with(effects=("process.run",), operations=("run",)),
        _admitted_capability(effects=("process.run",), operations=("run",)),
        AdmissionFacts(is_proof_operation=True, contained=False),
    )
    assert result.admission == "capability_gap"
    assert result.disposition == "refuse"
    assert result.reason == "process_not_contained"


def test_planning_operations_cannot_launder_protected_effects() -> None:
    """A plan operation on money.commit is still a protected class."""
    result = derive_admission(
        _manifest_with(effects=("money.commit",), operations=("plan",)),
        _admitted_capability(effects=("money.commit",), operations=("plan",)),
        AdmissionFacts(is_material_choice=True, authority_standing=False),
    )
    assert result.admission == "protected_uncovered"
    assert result.disposition == "escalate"


def test_classify_admission_conjoins_flags_with_manifest_predicates() -> None:
    """A bare flag short-circuit can be deleted only if this call is required."""
    source = Path(effects_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.func.id
        for node in ast.walk(_function_def(tree, "_classify_admission"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_privileged_admission_class" in names
    helper = _function_def(tree, "_privileged_admission_class")
    helper_calls = {
        node.func.id
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_planning_predicate" in helper_calls
    assert "_proof_predicate" in helper_calls
    attrs = {node.attr for node in ast.walk(helper) if isinstance(node, ast.Attribute)}
    assert "is_material_choice" in attrs
    assert "is_proof_operation" in attrs

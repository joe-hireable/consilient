"""Canonical effect records stay inert while their schema is enforced."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from consilient.effects import EFFECT_CLASSES, EffectError, EffectManifest
from consilient.events import EventError, SCHEMA_VERSION, append, append_transaction, validate


def event(kind: str, data: dict[str, object]) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
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
    return {"kind": "broker_reference", "reference": f"broker://effects/{name}"}


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
        forward=commitment("effect.forward"),
        scope=broker_reference("scope"),
        operations=("read",),
        effects=("data.read",),
        inventory_snapshot={"digest": "c" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "e" * 64},
        start_state=commitment("effect.start-state"),
        observer={"id": "observer-1", "policy_digest": "f" * 64},
        expected_state=commitment("effect.expected-state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def intent_data(manifest_value: EffectManifest, *, observation: bool = False) -> dict[str, object]:
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


def receipt_data(*, receipt_id: str, status: str, supersedes: str | None = None) -> dict[str, object]:
    data: dict[str, object] = {
        "receipt_id": receipt_id,
        "intent_id": "intent-1",
        "status": status,
        "started_at": "2026-08-23T10:00:00+00:00",
        "ended_at": "2026-08-23T10:00:01+00:00",
        "provider_request": broker_reference("provider-request"),
        "provider_receipt": broker_reference("provider-receipt"),
        "request_commitment": commitment("effect.request"),
        "response_commitment": commitment("effect.response"),
        "content_commitment": commitment("effect.content"),
        "observed_consumption": {"cpu_seconds": 1},
        "post_state": commitment("effect.post-state"),
        "observed_residuals": ("elapsed_time",),
        "child_operation_ids": (),
    }
    if supersedes is not None:
        data["supersedes"] = supersedes
    return data


def test_effect_classes_are_exact_and_manifest_digest_is_canonical() -> None:
    """Production break caught: a padded/case-varied effect could enter the manifest."""
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
    value = manifest()
    assert value.digest == EffectManifest.from_record(value.to_record()).digest
    with pytest.raises(EffectError, match="exact"):
        EffectManifest.from_record({**value.to_record(), "effects": ["Data.Read"]})


def test_manifest_rejects_raw_private_values_and_credentials() -> None:
    """Production break caught: a secret or low-entropy recipient reaches the trajectory."""
    value = manifest().to_record()
    value["forward"] = {"credential": "hunter2"}
    with pytest.raises(EffectError, match="broker reference|commitment"):
        EffectManifest.from_record(value)


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


def test_receipt_fields_reject_raw_provider_payloads() -> None:
    """Production break caught: a provider response/content payload is persisted verbatim."""
    payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
    payload["provider_receipt"] = {"response": "private reply"}
    with pytest.raises(EventError, match="broker reference|commitment"):
        validate(event("effect.receipt", payload))


def test_receipt_chain_allows_one_unknown_resolution_and_refuses_a_fork(tmp_path) -> None:
    """Production break caught: two receipt heads can claim incompatible outcomes."""
    value = manifest()
    append_transaction(
        tmp_path,
        [
            event("effect.intent", intent_data(value)),
            event("effect.receipt", receipt_data(receipt_id="receipt-unknown", status="unknown")),
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
            event("effect.receipt", receipt_data(receipt_id="receipt-fork", status="succeeded")),
        )

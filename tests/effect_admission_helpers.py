"""Manifest, gate and inventory builders shared by the test_effect_admission_* family.

Not named test_*, so pytest does not collect it. It is on sys.path because pytest prepends the
directory of every collected test module, and tests/ holds no __init__.py.

These are constructors, not fixtures: they take keyword overrides and return a value, so a test
spells out exactly the facts it is varying and inherits nothing invisibly. That property is the
reason they were worth extracting rather than duplicating -- four files building a manifest four
slightly different ways is how a suite starts agreeing with the implementation instead of
checking it.
"""

import hashlib

from datetime import datetime, timedelta, timezone


from consilient.capabilities import (
    CapabilityEntry,
    Gate,
    default_gate,
)

from consilient.effects import (
    EffectManifest,
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
    return {
        "kind": "broker_reference",
        "reference": f"broker://effects/{hashlib.sha256(name.encode()).hexdigest()}",
    }


def authority_event(event_id: str = "evt-authority-1") -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_kind": "human.approval",
        "event_sha256": "b" * 64,
    }


def recovery_proof_ref() -> dict[str, object]:
    return {
        "event_id": "evt-proof-1",
        "event_kind": "effect.receipt",
        "event_sha256": "c" * 64,
    }


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
        forward=commitment("effect.manifest.forward"),
        scope=broker_reference("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": gate_digest},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=commitment("effect.manifest.start_state"),
        observer={"id": "observer-1", "policy_digest": "1" * 64},
        expected_state=commitment("effect.manifest.expected_state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def admitted_gate(
    *,
    grant_kind: str = "controller_baseline.local_restorable.v1",
    effect_classes: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
    scope: tuple[str, ...] = ("workspace",),
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


def admitted_inventory_payload(**gate_overrides: object) -> dict[str, object]:
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    gate: dict[str, object] = {
        "state": "admitted",
        "reason": "exact_grant",
        "grant_kind": "controller_baseline.local_restorable.v1",
        "authority_event": None,
        "decision_id": "decision-1",
        "recovery_proof_ref": recovery_proof_ref(),
        "scope": ["workspace"],
        "operations": ["read"],
        "effect_classes": ["data.read"],
        "expires_at": expires,
    }
    gate.update(gate_overrides)
    return {
        "kind": "tool",
        "name": "pytest",
        "available": True,
        "provenance": ["probe:tool:pytest"],
        "gate": gate,
    }


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

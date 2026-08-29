"""The canonical effect manifest every contract test starts from.

`manifest()` returns the smallest admissible manifest -- a read-only `data.read`
operation with keyed commitments for its forward, start and expected states, broker
references for scope and authority, and ceilings that hold. Almost every test in this
family mutates one field of `manifest().to_record()` and asserts what happens, so the
builder and the two value shapes it depends on live here rather than in any one of them.
The commitments are keyed HMACs with a distinct domain per field on purpose: several
tests turn exactly that property off -- an unkeyed `sha256`, or a start state sharing
the forward state's domain -- and expect a refusal."""

from consilient.effects import (
    EffectManifest,
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

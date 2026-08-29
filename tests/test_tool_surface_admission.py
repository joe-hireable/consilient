"""What actually executes: ``derive_admission`` over a full effect manifest.

The classifier assigns labels; this is the other half - whether a labelled effect is
admitted, refused, or left uncovered - and it is exercised against a real manifest and a
real capability entry rather than a stub, because the contract is enforced field by
field. Unit B01 made ``disclosure`` REQUIRED for outbound message.send effects and
permitted only for those, so passing one on a non-outbound manifest is refused just as
firmly as omitting one on an outbound manifest; the builder here supplies the digest
exactly when the effect set calls for it. Weakening B01 to accept an outbound send with
no disclosure would delete the guarantee that a message this system emits can always be
traced to what it disclosed.

The outbound-fetch residual is CLOSED, and closed narrowly. The replaced check asserted
that network.call executes as plain observation under any admitted grant, which was an
honest residual when it was written [measured 2026-08-24]: network.call is class 4 on
the tool table and irreversible under the least-recoverable-atom rule, but
READ_ONLY_EFFECTS treated it as observation, and the note recorded the cost of closing
it - every webfetch would need a class-4 confirm. Commit 5ac16cc closed it with a
controller-baseline pre-check, so the code and that recorded decision disagreed and the
test went red. Joe chose the tightening on 28 August 2026 ("2. keep the tightening"),
from two options put to him. The cost turned out smaller than the original note feared,
which is why the boundary is asserted in all three directions rather than only the
refusal: a local restorable baseline may not reach outbound network, a principal-
authority grant still may, and ordinary reads are untouched. The zero-click path is not
dead; it is reattached to standing authority, which is what an irreversible outbound
effect should have required all along.

The rest of the surface takes the same shape. The seven protected irreversible effects
do not execute without standing authority; a gated capability executes nothing at all;
and an admitted ``file.change`` with a recovery proof does still execute a local
overwrite - that is the utility, not a missed attack, since making those class 4 would
stop and disclose on every read, grep and write."""

import hashlib
from datetime import datetime, timedelta, timezone
from consilient.capabilities import (
    REGISTERED_TOOLS,
    CapabilityEntry,
    classify_reversibility,
    default_gate,
)
from consilient.effects import (
    AdmissionFacts,
    EffectManifest,
    derive_admission,
    OUTBOUND_EFFECTS,
)
from tool_surface_helpers import (
    REVERSIBLE_DEFAULT,
)


def _commitment(domain: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": "a" * 64,
    }


def _broker(name: str) -> dict[str, str]:
    return {
        "kind": "broker_reference",
        "reference": f"broker://effects/{hashlib.sha256(name.encode()).hexdigest()}",
    }


def _manifest(
    *,
    effects: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
) -> EffectManifest:
    # Unit B01 made `disclosure` REQUIRED for outbound message.send effects, and only
    # permitted for those -- passing one on a non-outbound manifest is refused just as firmly
    # as omitting one on an outbound manifest. This helper predates that contract, so it now
    # supplies the digest exactly when the effect set calls for it. Weakening B01 to accept an
    # outbound send with no disclosure would delete the guarantee that a message this system
    # emits can always be traced to what it disclosed.
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
        forward=_commitment("effect.manifest.forward"),
        scope=_broker("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=_broker("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=_commitment("effect.manifest.start_state"),
        observer={"id": "observer-1", "policy_digest": "1" * 64},
        expected_state=_commitment("effect.manifest.expected_state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 0},
    )


def _admitted(
    *,
    effect_classes: tuple[str, ...] = ("data.read",),
    operations: tuple[str, ...] = ("read",),
    grant_kind: str = "controller_baseline.local_restorable.v1",
) -> CapabilityEntry:
    expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    gate = default_gate()
    return CapabilityEntry(
        kind="tool",
        name="pytest",
        available=True,
        provenance=("probe:tool:pytest",),
        gate=type(gate)(
            state="admitted",
            reason="exact_grant",
            grant_kind=grant_kind,
            authority_event=None,
            decision_id="decision-1",
            recovery_proof_ref={
                "event_id": "evt-proof-1",
                "event_kind": "effect.receipt",
                "event_sha256": "c" * 64,
            },
            scope=("workspace",),
            operations=operations,
            effect_classes=effect_classes,
            expires_at=expires,
        ),
    )


def test_network_call_needs_standing_authority_not_the_local_baseline() -> None:
    """The outbound-fetch residual is CLOSED, and closed narrowly.

    REPLACES test_admission_residual_network_call_can_execute_as_observation, which
    asserted that network.call executes as plain observation under any admitted grant. That
    was an honest residual when it was written [measured 2026-08-24]: network.call is class
    4 on the tool table and irreversible under the least-recoverable-atom rule, but
    READ_ONLY_EFFECTS treated it as observation, and the note recorded the cost of closing
    it -- every webfetch would need a class-4 confirm.

    Commit 5ac16cc closed it by adding a controller-baseline pre-check, so the code and that
    recorded decision disagreed and this test went red. Joe chose the tightening on
    28 August 2026 ("2. keep the tightening"), from two options put to him.

    The cost turned out to be smaller than the original note feared, which is why the
    boundary is worth asserting in all three directions rather than just the refusal:
    the closure is SCOPED TO THE GRANT KIND, not to the effect. A local restorable
    baseline may not reach outbound network; a principal-authority grant still may. The
    zero-click path is not dead, it is reattached to standing authority -- which is what
    an irreversible outbound effect should have required all along.
    """
    manifest = _manifest(effects=("network.call",), operations=("fetch",))

    # 1. The local baseline may NOT reach outbound network. This is the tightening.
    baseline = derive_admission(
        manifest,
        _admitted(effect_classes=("network.call",), operations=("fetch",)),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert baseline.admission == "capability_gap"
    assert baseline.disposition == "refuse"
    assert baseline.reason == "grant_kind_forbids_protected_reach"

    # 2. Standing authority still may. Without this the test would pass for a blanket ban,
    #    and the closure would be wider than anyone chose.
    standing = derive_admission(
        manifest,
        _admitted(
            effect_classes=("network.call",),
            operations=("fetch",),
            grant_kind="principal_authority",
        ),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert standing.admission == "observation"
    assert standing.disposition == "execute"

    # 3. Ordinary reads are untouched. The tightening is about REACH, not about
    #    observation, and a check that cannot tell those apart would be the wrong one.
    read_only = derive_admission(
        _manifest(effects=("data.read",), operations=("read",)),
        _admitted(effect_classes=("data.read",), operations=("read",)),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert read_only.admission == "observation"
    assert read_only.disposition == "execute"


def test_protected_irreversible_effects_do_not_execute_without_standing_authority() -> (
    None
):
    for effect in (
        "money.commit",
        "message.send",
        "content.publish",
        "external.change",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
    ):
        result = derive_admission(
            _manifest(effects=(effect,), operations=("act",)),
            _admitted(
                effect_classes=(effect,),
                operations=("act",),
                grant_kind="principal_authority",
            ),
            AdmissionFacts(authority_standing=False),
        )
        assert result.disposition != "execute", effect
        assert result.admission == "protected_uncovered"


def test_gated_capability_cannot_execute_any_effect() -> None:
    result = derive_admission(
        _manifest(),
        CapabilityEntry(
            kind="tool",
            name="webfetch",
            available=True,
            provenance=("probe:tool:webfetch",),
            gate=default_gate(),
        ),
        AdmissionFacts(broker_confirms_observation=True),
    )
    assert result.disposition == "refuse"


def test_reversible_residual_and_utility_cost_are_reported() -> None:
    """File tools remain class 1 — that is the utility, not a missed attack.

    Residual: an admitted ``file.change`` with a recovery proof still
    executes (local overwrite). Utility cost of making those class 4:
    every read/grep/write would stop and disclose, killing the zero-click
    path the design reserves for a closed tool surface.
    """
    class_1 = {
        (kind, name)
        for (kind, name), family in REGISTERED_TOOLS.items()
        if classify_reversibility(kind, name) == 1
    }
    assert class_1 == set(REVERSIBLE_DEFAULT)
    result = derive_admission(
        _manifest(effects=("file.change",), operations=("write",)),
        _admitted(effect_classes=("file.change",), operations=("write",)),
        AdmissionFacts(recovery_proof_passed=True),
    )
    assert result.admission == "recoverable_mutation"
    assert result.disposition == "execute"

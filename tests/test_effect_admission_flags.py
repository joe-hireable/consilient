"""No caller-supplied flag buys coverage it has not earned.

`AdmissionFacts` is filled in by the caller, so every field on it is something an
adversary would like to set. These cases hold `derive_admission` against that:
`is_material_choice` must not execute unprotected spend, `is_proof_operation` must not
execute unprotected spend either nor run an uncontained process, and labelling a
`money.commit` operation `plan` must not launder it out of its protected class. The
capability granted in each case is deliberately an exact, admitted grant covering the
very effect and operation asked for, so a refusal can only come from the protected-class
rule and never from a missing grant -- which is what `_admitted_capability` and
`_manifest_with` exist to guarantee, and why they travel with these tests rather than
with the shared builder.

`test_privileged_classes_need_the_caller_flag_and_the_manifest` replaces
`test_classify_admission_conjoins_flags_with_manifest_predicates`, which walked the AST
asserting that a helper named `_privileged_admission_class` was called. Commit 5ac16cc
inlined that helper, so the test was red on HEAD while the property it cared about was
untouched -- it pinned an implementation detail rather than a behaviour. The replacement
asserts the conjunction itself, so it survives the next inlining and fails if either
half is dropped."""

from consilient.capabilities import CapabilityEntry, Gate
from consilient.effects import (
    OUTBOUND_EFFECTS,
    AdmissionFacts,
    EffectManifest,
    derive_admission,
)
from effect_contract_helpers import (
    manifest,
)


def _admitted_capability(
    *, effects: tuple[str, ...], operations: tuple[str, ...]
) -> CapabilityEntry:
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


def _manifest_with(
    *, effects: tuple[str, ...], operations: tuple[str, ...]
) -> EffectManifest:
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
        AdmissionFacts(
            is_proof_operation=True, contained=True, authority_standing=False
        ),
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


def test_privileged_classes_need_the_caller_flag_and_the_manifest() -> None:
    """Neither a caller flag nor a manifest shape alone may grant a privileged class.

    REPLACES test_classify_admission_conjoins_flags_with_manifest_predicates, which walked
    the AST asserting a helper named _privileged_admission_class was called. Commit 5ac16cc
    inlined that helper, so the test was red on HEAD while the PROPERTY it cared about was
    untouched -- it pinned an implementation detail rather than a behaviour. This asserts the
    behaviour, so it survives the next inlining and fails if the conjunction is dropped.
    """
    proof = _manifest_with(effects=("file.change",), operations=("proof",))
    proof_cap = _admitted_capability(effects=("file.change",), operations=("proof",))
    plan = _manifest_with(effects=("data.read",), operations=("plan",))
    plan_cap = _admitted_capability(effects=("data.read",), operations=("plan",))
    write_m = _manifest_with(effects=("file.change",), operations=("write",))
    write_cap = _admitted_capability(effects=("file.change",), operations=("write",))
    # The manifest shape without the caller flag grants nothing.
    assert (
        derive_admission(
            proof, proof_cap, AdmissionFacts(is_proof_operation=False, contained=True)
        ).admission
        != "proof_operation"
    )
    assert (
        derive_admission(
            plan, plan_cap, AdmissionFacts(is_material_choice=False)
        ).admission
        != "material_choice"
    )
    # The caller flag without the manifest shape grants nothing.
    assert (
        derive_admission(
            write_m, write_cap, AdmissionFacts(is_proof_operation=True, contained=True)
        ).admission
        != "proof_operation"
    )
    assert (
        derive_admission(
            write_m, write_cap, AdmissionFacts(is_material_choice=True, contained=True)
        ).admission
        != "material_choice"
    )

"""Containment is a PRECONDITION on running a process, not one arm of the admission ladder.

Separated because the constant it pins, CONTAINED_EXECUTION_EFFECTS, is the one an adversarial
pass already found a hole in: the parametrised ratchet derived its cases from the constant, so
widening the constant DELETED the case that would have caught the widening. The suite went from
92 passing to 91 -- greener, and smaller. Keeping these together makes that trap visible.
"""

import pytest

from consilient.capabilities import (
    Gate,
)

from consilient.effects import (
    CONTAINED_EXECUTION_EFFECTS,
    READ_ONLY_EFFECTS,
    AdmissionFacts,
    derive_admission,
)

from effect_admission_helpers import (
    admitted_gate,
    capability_entry,
    manifest,
)


def _run_gate(effects: tuple[str, ...]) -> Gate:
    return admitted_gate(
        grant_kind="principal_authority",
        effect_classes=effects,
        operations=("run",),
        decision_id=None,
        recovery_proof_ref_value=None,
    )


def test_contained_execution_effects_is_exactly_read_only_plus_process_run() -> None:
    """The constant is PINNED, because widening it silently reopens the fail-open.

    An adversarial pass found this hole in the FIRST version of these tests: the parametrised
    ratchet below derived its case list from CONTAINED_EXECUTION_EFFECTS, so adding
    file.change to the constant DELETED the case that would have caught it. The suite went
    from 92 passing to 91 passing -- greener, and smaller -- while a file.change rode
    process.run into execute with the recovery proof never demanded.

    A test whose coverage shrinks when the thing it guards is widened is not a guard. This
    equality cannot shrink.
    """
    assert CONTAINED_EXECUTION_EFFECTS == READ_ONLY_EFFECTS | frozenset({"process.run"})


@pytest.mark.parametrize(
    "carried,expected_admission,expected_disposition",
    [
        # LITERALS, deliberately not derived from any constant this test guards.
        ("money.commit", "protected_uncovered", "escalate"),
        ("authority.change", "protected_uncovered", "escalate"),
        ("content.publish", "protected_uncovered", "escalate"),
        ("external.change", "protected_uncovered", "escalate"),
        ("obligation.commit", "protected_uncovered", "escalate"),
        ("physical.actuate", "protected_uncovered", "escalate"),
        # Not protected, but not read-only either: must still demand the recovery proof.
        ("file.change", "recoverable_mutation", "refuse"),
        ("system.change", "recoverable_mutation", "refuse"),
    ],
)
def test_process_run_cannot_carry_another_effect_class(
    carried: str, expected_admission: str, expected_disposition: str
) -> None:
    """A contained process.run must never launder a second effect class into execute.

    The protected rows prove ORDER; the file.change / system.change rows prove SUBSET. They
    fail differently, which is why both halves are here.
    """
    effects = ("process.run", carried)
    result = derive_admission(
        manifest(effects=effects, operations=("run",)),
        capability_entry(gate=_run_gate(effects)),
        AdmissionFacts(contained=True, authority_standing=False),
    )
    assert result.admission == expected_admission, (
        f"process.run + {carried} classified as {result.admission}"
    )
    assert result.disposition == expected_disposition
    assert result.disposition != "execute"


def test_a_bare_contained_run_still_executes() -> None:
    """The fix must not close the ordinary case it was never about.

    If a plain contained run starts refusing, callers learn to silence it with
    recovery_proof_passed=True, which is the bypass this whole file exists to prevent.
    """
    for effects in (("process.run",), ("process.run", "data.read")):
        result = derive_admission(
            manifest(effects=effects, operations=("run",)),
            capability_entry(gate=_run_gate(effects)),
            AdmissionFacts(contained=True),
        )
        assert result.admission == "contained_execution", effects
        assert result.disposition == "execute", effects


def test_an_uncontained_run_is_refused_whatever_else_it_declares() -> None:
    """Containment is a precondition on running a process, not one arm of the ladder."""
    for carried in ("data.read", "file.change", "money.commit"):
        effects = ("process.run", carried)
        result = derive_admission(
            manifest(effects=effects, operations=("run",)),
            capability_entry(gate=_run_gate(effects)),
            AdmissionFacts(contained=False, authority_standing=False),
        )
        assert result.disposition != "execute", carried

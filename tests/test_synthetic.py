"""V0-30 / R34a: an unmeasured verifier's pass is not an acceptance.

ADR-0055's clause 3 is the guard every future verifier inherits. These tests pin
the run-spec and finding objects (clauses 1–2), the absence of an accepting
outcome (by construction), and the composition guard's fail-closed reason —
including the ADR's named check: a verifier record below the measured threshold
cannot accept, and the reason is exactly `verifier_beta_unmeasured`.
"""

from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path
from typing import get_args

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.beta import INSUFFICIENT, MEASURED  # noqa: E402
from consilient.synthetic import (  # noqa: E402
    SYNTHETIC_OUTCOMES,
    VERIFIER_BETA_UNMEASURED,
    Finding,
    RunSpec,
    SyntheticOutcome,
    VerifierRef,
    compose_acceptance,
)


def spec(**overrides: object) -> RunSpec:
    base: dict[str, object] = {
        "id": "novice-cli",
        "task": "record a verdict on the sample artefact",
        "success_criterion": "the verdict event exists in the trajectory",
        "information_boundary": ("the --help text", "the task statement"),
        "interface": "cli",
        "oracle_kinds": ("implicit", "specification"),
        "harness": "codex",
    }
    base.update(overrides)
    return RunSpec(**base)  # type: ignore[arg-type]


def test_run_spec_validates_the_measurable_fields() -> None:
    assert spec().id == "novice-cli"
    with pytest.raises(ValueError, match="task"):
        spec(task="  ")
    with pytest.raises(ValueError, match="interface"):
        spec(interface="telepathy")
    with pytest.raises(ValueError, match="oracle_kinds"):
        spec(oracle_kinds=())
    with pytest.raises(ValueError, match="unknown oracle kinds"):
        spec(oracle_kinds=("vibes",))
    with pytest.raises(ValueError, match="information_boundary"):
        spec(information_boundary=())


def test_run_spec_has_no_personality_fields() -> None:
    """Clause 1's refusal is at the type level: there is nowhere to put one."""
    names = {f.name for f in fields(RunSpec)}
    assert names == {
        "id",
        "task",
        "success_criterion",
        "information_boundary",
        "interface",
        "oracle_kinds",
        "harness",
    }


def test_finding_carries_anchor_and_reproduction() -> None:
    finding = Finding(
        run_id="r1",
        spec_id="novice-cli",
        discrepancy="--json reports quarantined; the human-readable path drops it",
        anchor="specification",
        reproduction=("consil doctor", "consil doctor --json"),
    )
    assert finding.evidential_weight == 1.0
    state = Finding(
        run_id="r1",
        spec_id="novice-cli",
        discrepancy="the code says otherwise",
        anchor="state",
        reproduction=("read cli.py:412",),
    )
    assert state.evidential_weight == 0.0
    with pytest.raises(ValueError, match="reproduction"):
        Finding(
            run_id="r1",
            spec_id="s",
            discrepancy="d",
            anchor="implicit",
            reproduction=(),
        )


def test_no_accepting_outcome_exists() -> None:
    """Clause 3 by construction: the outcome type has no accept member."""
    assert "accept" not in get_args(SyntheticOutcome)
    assert set(SYNTHETIC_OUTCOMES) == {"reject", "flag", "report"}


def test_unmeasured_verifier_cannot_accept() -> None:
    """The ADR's named check: insufficient_data fails closed, with the reason."""
    unmeasured = VerifierRef("sim-user-arm-c", INSUFFICIENT)
    measured = VerifierRef("pytest-suite", MEASURED)

    refused = compose_acceptance((unmeasured,), mode="disjunct")
    assert isinstance(refused, str)
    assert refused.startswith(VERIFIER_BETA_UNMEASURED)

    refused_substitution = compose_acceptance((measured, unmeasured), mode="disjunct")
    assert isinstance(refused_substitution, str)
    assert "sim-user-arm-c" in refused_substitution

    admitted = compose_acceptance((measured, unmeasured), mode="conjunct")
    assert admitted == (measured, unmeasured)

    assert compose_acceptance((measured,), mode="disjunct") == (measured,)
    assert isinstance(compose_acceptance((), mode="conjunct"), str)


def test_the_guard_can_fail() -> None:
    """Mutation: a compose that admits an unmeasured disjunct must be caught."""
    unmeasured = VerifierRef("sim-user-arm-c", INSUFFICIENT)
    broken = compose_acceptance((unmeasured,), mode="disjunct")
    assert not (isinstance(broken, tuple) and unmeasured in broken), (
        "the guard admitted an unmeasured verifier as a disjunct"
    )

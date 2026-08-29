"""ADR-0055: a simulated user is a run, not a verdict.

Clause 1: a user type is a run specification — what they know (information
boundary) and what they try (task), both measurable. No personality, no
demographic, no prose character sketch: the type has no such fields, so the
refusal is at the type level rather than the decision boundary (V0-19).

Clause 2: a run's output is a finding, not a verdict. Every finding carries its
anchor and a reproduction, so it is re-verifiable by replay; a state-anchored
finding is recorded with zero evidential weight, not discarded, so the
proportion stays measurable.

Clause 3: an unmeasured verifier's *pass* is not evidence; only its *fail* is.
`compose_acceptance` is the guard every future verifier inherits: insufficient_data
may be a conjunct (its pass licenses nothing on its own) and may never be a
disjunct or a substitute. `SyntheticOutcome` has no accept member at all — a
simulated run may reject, flag, or report, and the acceptance it cannot produce
is refused by construction, not by convention.

The runner and the findings store are deliberately absent here: the runner drives
interfaces (subprocess, browser) and belongs outside the AST lock, and the store
is trajectory schema. This module is the objects and the guard, nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

AnchorKind = Literal["implicit", "specification", "metamorphic", "reference", "state"]
ANCHOR_KINDS: tuple[AnchorKind, ...] = get_args(AnchorKind)

InterfaceKind = Literal["cli", "http", "browser"]
INTERFACE_KINDS: tuple[InterfaceKind, ...] = get_args(InterfaceKind)

#: The only outcomes a simulated run may produce. There is no "accept": clause 3
#: is enforced by the type, so no caller can construct the forbidden thing.
SyntheticOutcome = Literal["reject", "flag", "report"]
SYNTHETIC_OUTCOMES: tuple[SyntheticOutcome, ...] = get_args(SyntheticOutcome)

#: The refusal reason the V0-30 check asserts on. Pinned here so a rewording
#: breaks a test loudly rather than letting the refusal be misclassified.
VERIFIER_BETA_UNMEASURED = "verifier_beta_unmeasured"


@dataclass(frozen=True)
class RunSpec:
    """One simulated user type: an operator with a restricted information
    boundary driving a real interface to a mechanically decidable outcome."""

    id: str
    task: str
    success_criterion: str
    information_boundary: tuple[str, ...]
    interface: InterfaceKind
    oracle_kinds: tuple[AnchorKind, ...]
    harness: str

    def __post_init__(self) -> None:
        # Named pairs rather than getattr: the product tree bans dynamic attribute access
        # because it defeats the AST scan that proves this tree cannot reach a shell, the
        # network or a credential. A lock with a benign exception is not a lock.
        for field_name, value in (
            ("id", self.id),
            ("task", self.task),
            ("success_criterion", self.success_criterion),
            ("harness", self.harness),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"RunSpec.{field_name} must be a non-empty string; a run spec "
                    "names what it does and what counts as done"
                )
        if self.interface not in INTERFACE_KINDS:
            raise ValueError(
                f"RunSpec.interface must be one of {INTERFACE_KINDS}, "
                f"got {self.interface!r}"
            )
        if not self.oracle_kinds:
            raise ValueError(
                "RunSpec.oracle_kinds must name at least one anchor kind; a run "
                "without an oracle cannot produce a finding"
            )
        unknown = [kind for kind in self.oracle_kinds if kind not in ANCHOR_KINDS]
        if unknown:
            raise ValueError(
                f"unknown oracle kinds: {unknown!r}; known: {ANCHOR_KINDS}"
            )
        if not self.information_boundary:
            raise ValueError(
                "RunSpec.information_boundary must say what the operator may read; "
                "an empty boundary is an unrestricted operator, which is not a user type"
            )


@dataclass(frozen=True)
class Finding:
    """What a run found. Re-verifiable: replay `reproduction` and look again."""

    run_id: str
    spec_id: str
    discrepancy: str
    anchor: AnchorKind
    reproduction: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("run_id", self.run_id),
            ("spec_id", self.spec_id),
            ("discrepancy", self.discrepancy),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Finding.{field_name} must be a non-empty string")
        if self.anchor not in ANCHOR_KINDS:
            raise ValueError(
                f"Finding.anchor must be one of {ANCHOR_KINDS}, got {self.anchor!r}"
            )
        if not self.reproduction or not all(
            isinstance(step, str) and step.strip() for step in self.reproduction
        ):
            raise ValueError(
                "Finding.reproduction must be a non-empty input sequence; a finding "
                "without one is an anecdote"
            )

    @property
    def evidential_weight(self) -> float:
        """State-anchored findings are recorded with zero weight, not discarded."""
        return 0.0 if self.anchor == "state" else 1.0


@dataclass(frozen=True)
class VerifierRef:
    """A verifier as the acceptance predicate sees it: an id and whether its β
    is measured. Everything else about the verifier is irrelevant to clause 3."""

    id: str
    beta_verdict: Literal["measured", "insufficient_data"]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("VerifierRef.id must be a non-empty string")
        if self.beta_verdict not in ("measured", "insufficient_data"):
            raise ValueError(
                f"VerifierRef.beta_verdict must be 'measured' or "
                f"'insufficient_data', got {self.beta_verdict!r}"
            )


def compose_acceptance(
    verifiers: tuple[VerifierRef, ...], *, mode: Literal["conjunct", "disjunct"]
) -> tuple[VerifierRef, ...] | str:
    """ADR-0055 clause 3, generalised to the acceptance predicate's shape.

    Conjunctive: every verifier must pass, so an unmeasured verifier's pass
    licenses nothing on its own and its fail still rejects — admitted. Disjunctive:
    any one pass accepts, so an unmeasured verifier's pass would BE an acceptance —
    refused, failing closed with the pinned reason. An empty composition accepts
    nothing and is refused under either mode.
    """
    if not verifiers:
        return (
            f"{VERIFIER_BETA_UNMEASURED}: an empty acceptance predicate accepts nothing"
        )
    if mode not in ("conjunct", "disjunct"):
        return f"{VERIFIER_BETA_UNMEASURED}: unknown composition mode {mode!r}"
    if mode == "disjunct":
        unmeasured = tuple(v.id for v in verifiers if v.beta_verdict != "measured")
        if unmeasured:
            return (
                f"{VERIFIER_BETA_UNMEASURED}: {', '.join(unmeasured)} may not be a "
                "disjunct in the acceptance predicate; an unmeasured verifier's pass "
                "is not evidence, only its fail is"
            )
    return verifiers

"""Executable decision regimes for ADR-0068 and EXP-98.

This model fixes thresholds; it does not estimate decomposition value or duration. [asserted]
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from math import isfinite


FROZEN_REQUESTS = 80
ATOMIC_REQUESTS = 20
RECOVERY_REQUESTS = 10
MIN_CONDITIONAL_OUTCOMES = 30
MIN_JOINT_GAIN = 0.10
MAX_SAFETY_LOSS = 0.05
MAX_COST_RATIO = 1.0
MAX_REVIEW_RATIO = 1.0
MAX_INVALID_SHARE = 0.10
MIN_DURATION_COVERAGE = 0.80


class Regime(str, Enum):
    CONFIRM_FROZEN_MIXTURE = "confirm_frozen_mixture"
    CUT_AS_COMPUTE = "cut_as_compute"
    CUT_OVERHEAD = "cut_overhead"
    CUT_PROTOCOL = "cut_protocol"
    CUT_RESUMABILITY = "cut_resumability"
    CUT_SAFETY = "cut_safety"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Observation:
    requests_in_primary_denominator: int
    minimum_human_rejections_per_arm: int
    minimum_human_acceptances_per_arm: int
    joint_gain_over_operational_single: float
    joint_gain_over_matched_single: float
    joint_interval_low_over_operational_single: float
    joint_interval_low_over_matched_single: float
    beta_upper_over_operational_single: float
    beta_upper_over_matched_single: float
    alpha_upper_over_operational_single: float
    alpha_upper_over_matched_single: float
    cost_per_success_ratio_to_matched_single: float
    review_minutes_ratio_to_matched_single: float
    invalid_share: float
    atomic_overdecompositions: int
    dependency_violations: int
    shared_artefact_overwrites: int
    checkpoint_losses: int
    early_dependents: int


def _valid(observation: Observation) -> bool:
    counts = (
        observation.requests_in_primary_denominator,
        observation.minimum_human_rejections_per_arm,
        observation.minimum_human_acceptances_per_arm,
        observation.atomic_overdecompositions,
        observation.dependency_violations,
        observation.shared_artefact_overwrites,
        observation.checkpoint_losses,
        observation.early_dependents,
    )
    bounded_rates = (
        observation.joint_gain_over_operational_single,
        observation.joint_gain_over_matched_single,
        observation.joint_interval_low_over_operational_single,
        observation.joint_interval_low_over_matched_single,
        observation.beta_upper_over_operational_single,
        observation.beta_upper_over_matched_single,
        observation.alpha_upper_over_operational_single,
        observation.alpha_upper_over_matched_single,
    )
    ratios = (
        observation.cost_per_success_ratio_to_matched_single,
        observation.review_minutes_ratio_to_matched_single,
    )
    return (
        all(isinstance(value, int) and value >= 0 for value in counts)
        and observation.requests_in_primary_denominator <= FROZEN_REQUESTS
        and observation.minimum_human_rejections_per_arm <= FROZEN_REQUESTS
        and observation.minimum_human_acceptances_per_arm <= FROZEN_REQUESTS
        and (
            observation.minimum_human_rejections_per_arm
            + observation.minimum_human_acceptances_per_arm
            <= FROZEN_REQUESTS
        )
        and observation.atomic_overdecompositions <= ATOMIC_REQUESTS
        and observation.checkpoint_losses <= RECOVERY_REQUESTS
        and observation.early_dependents <= RECOVERY_REQUESTS
        and all(isfinite(value) and -1.0 <= value <= 1.0 for value in bounded_rates)
        and all(isfinite(value) and value >= 0.0 for value in ratios)
        and isfinite(observation.invalid_share)
        and 0.0 <= observation.invalid_share <= 1.0
    )


def classify(observation: Observation) -> Regime:
    """Return the pre-registered build regime for one EXP-98 result."""
    if not _valid(observation):
        return Regime.INSUFFICIENT_EVIDENCE
    if observation.invalid_share > MAX_INVALID_SHARE:
        return Regime.CUT_PROTOCOL
    if observation.checkpoint_losses or observation.early_dependents:
        return Regime.CUT_RESUMABILITY
    if (
        observation.requests_in_primary_denominator != FROZEN_REQUESTS
        or observation.minimum_human_rejections_per_arm < MIN_CONDITIONAL_OUTCOMES
        or observation.minimum_human_acceptances_per_arm < MIN_CONDITIONAL_OUTCOMES
    ):
        return Regime.INSUFFICIENT_EVIDENCE
    if (
        observation.beta_upper_over_operational_single > MAX_SAFETY_LOSS
        or observation.beta_upper_over_matched_single > MAX_SAFETY_LOSS
        or observation.alpha_upper_over_operational_single > MAX_SAFETY_LOSS
        or observation.alpha_upper_over_matched_single > MAX_SAFETY_LOSS
    ):
        return Regime.CUT_SAFETY

    beats_operational = (
        observation.joint_gain_over_operational_single >= MIN_JOINT_GAIN
        and observation.joint_interval_low_over_operational_single > 0.0
    )
    beats_matched = (
        observation.joint_gain_over_matched_single >= MIN_JOINT_GAIN
        and observation.joint_interval_low_over_matched_single > 0.0
    )
    if (
        observation.joint_gain_over_matched_single <= 0.0
        or observation.review_minutes_ratio_to_matched_single > MAX_REVIEW_RATIO
    ):
        return Regime.CUT_OVERHEAD
    if beats_operational and not beats_matched:
        return Regime.CUT_AS_COMPUTE
    if (
        observation.atomic_overdecompositions
        or observation.dependency_violations
        or observation.shared_artefact_overwrites
    ):
        return Regime.UNRESOLVED
    if (
        beats_operational
        and beats_matched
        and observation.cost_per_success_ratio_to_matched_single <= MAX_COST_RATIO
    ):
        return Regime.CONFIRM_FROZEN_MIXTURE
    return Regime.UNRESOLVED


def duration_confirmed(completed: int, inside_original_range: int, late_reforecasts: int) -> bool:
    """Return whether EXP-98 confirms the user-visible duration method."""
    return (
        completed > 0
        and 0 <= inside_original_range <= completed
        and late_reforecasts >= 0
        and inside_original_range / completed >= MIN_DURATION_COVERAGE
        and late_reforecasts == 0
    )


def _self_check() -> None:
    boundary = Observation(
        requests_in_primary_denominator=FROZEN_REQUESTS,
        minimum_human_rejections_per_arm=MIN_CONDITIONAL_OUTCOMES,
        minimum_human_acceptances_per_arm=MIN_CONDITIONAL_OUTCOMES,
        joint_gain_over_operational_single=MIN_JOINT_GAIN,
        joint_gain_over_matched_single=MIN_JOINT_GAIN,
        joint_interval_low_over_operational_single=0.001,
        joint_interval_low_over_matched_single=0.001,
        beta_upper_over_operational_single=MAX_SAFETY_LOSS,
        beta_upper_over_matched_single=MAX_SAFETY_LOSS,
        alpha_upper_over_operational_single=MAX_SAFETY_LOSS,
        alpha_upper_over_matched_single=MAX_SAFETY_LOSS,
        cost_per_success_ratio_to_matched_single=MAX_COST_RATIO,
        review_minutes_ratio_to_matched_single=MAX_REVIEW_RATIO,
        invalid_share=MAX_INVALID_SHARE,
        atomic_overdecompositions=0,
        dependency_violations=0,
        shared_artefact_overwrites=0,
        checkpoint_losses=0,
        early_dependents=0,
    )
    assert classify(boundary) is Regime.CONFIRM_FROZEN_MIXTURE
    assert (
        classify(replace(boundary, joint_gain_over_matched_single=0.099))
        is Regime.CUT_AS_COMPUTE
    )
    assert (
        classify(
            replace(
                boundary,
                joint_gain_over_operational_single=-0.01,
                joint_interval_low_over_operational_single=-0.02,
            )
        )
        is Regime.UNRESOLVED
    )
    assert (
        classify(
            replace(
                boundary,
                joint_gain_over_matched_single=0.0,
                joint_interval_low_over_matched_single=-0.01,
            )
        )
        is Regime.CUT_OVERHEAD
    )
    assert (
        classify(replace(boundary, beta_upper_over_operational_single=0.051))
        is Regime.CUT_SAFETY
    )
    assert classify(replace(boundary, checkpoint_losses=1)) is Regime.CUT_RESUMABILITY
    assert classify(replace(boundary, early_dependents=1)) is Regime.CUT_RESUMABILITY
    assert classify(replace(boundary, invalid_share=0.101)) is Regime.CUT_PROTOCOL
    assert classify(replace(boundary, atomic_overdecompositions=1)) is Regime.UNRESOLVED
    assert classify(replace(boundary, dependency_violations=1)) is Regime.UNRESOLVED
    assert classify(replace(boundary, shared_artefact_overwrites=1)) is Regime.UNRESOLVED
    assert classify(replace(boundary, invalid_share=float("nan"))) is Regime.INSUFFICIENT_EVIDENCE
    assert (
        classify(replace(boundary, requests_in_primary_denominator=FROZEN_REQUESTS - 1))
        is Regime.INSUFFICIENT_EVIDENCE
    )
    assert (
        classify(replace(boundary, minimum_human_rejections_per_arm=29))
        is Regime.INSUFFICIENT_EVIDENCE
    )
    assert (
        classify(replace(boundary, review_minutes_ratio_to_matched_single=1.01))
        is Regime.CUT_OVERHEAD
    )
    assert (
        classify(replace(boundary, cost_per_success_ratio_to_matched_single=1.01))
        is Regime.UNRESOLVED
    )
    assert duration_confirmed(10, 8, 0)
    assert not duration_confirmed(10, 7, 0)
    assert not duration_confirmed(10, 8, 1)
    assert not duration_confirmed(10, 11, 0)
    assert not duration_confirmed(10, 8, -1)


if __name__ == "__main__":
    _self_check()
    print("ADR-0068 regime boundaries pass")

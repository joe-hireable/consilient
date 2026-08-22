"""Executable decision regimes for ADR-0067 and EXP-80.

This model does not estimate squad performance. [asserted] It makes the registered sign
and threshold choices executable so changed assumptions cannot silently change the ADR.
[asserted]
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


FROZEN_TASKS = 80
MIN_CONDITIONAL_OUTCOMES = 30
MIN_JOINT_GAIN = 0.10
MAX_SAFETY_LOSS = 0.05
MAX_COST_RATIO = 1.0
MAX_INVALID_SHARE = 0.10


class Regime(str, Enum):
    CONFIRM_TESTED_FAMILIES = "confirm_tested_families"
    CUT_AS_COMPUTE = "cut_as_compute"
    CUT_PROTOCOL = "cut_protocol"
    CUT_SAFETY = "cut_safety"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Observation:
    tasks_in_primary_denominator: int
    minimum_human_rejections_per_arm: int
    minimum_human_acceptances_per_arm: int
    joint_gain_over_operational_single: float
    joint_gain_over_matched_single: float
    joint_interval_low_over_operational_single: float
    joint_interval_low_over_matched_single: float
    beta_difference_upper_bound: float
    alpha_difference_upper_bound: float
    cost_per_success_ratio_to_matched_single: float
    invalid_share: float


def classify(observation: Observation) -> Regime:
    """Return the pre-registered build regime for one EXP-80 result."""
    if observation.invalid_share > MAX_INVALID_SHARE:
        return Regime.CUT_PROTOCOL
    if (
        observation.tasks_in_primary_denominator != FROZEN_TASKS
        or observation.minimum_human_rejections_per_arm < MIN_CONDITIONAL_OUTCOMES
        or observation.minimum_human_acceptances_per_arm < MIN_CONDITIONAL_OUTCOMES
    ):
        return Regime.INSUFFICIENT_EVIDENCE
    if (
        observation.beta_difference_upper_bound > MAX_SAFETY_LOSS
        or observation.alpha_difference_upper_bound > MAX_SAFETY_LOSS
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
    if beats_operational and not beats_matched:
        return Regime.CUT_AS_COMPUTE
    if (
        beats_operational
        and beats_matched
        and observation.cost_per_success_ratio_to_matched_single <= MAX_COST_RATIO
    ):
        return Regime.CONFIRM_TESTED_FAMILIES
    return Regime.UNRESOLVED


def _self_check() -> None:
    boundary = Observation(
        tasks_in_primary_denominator=FROZEN_TASKS,
        minimum_human_rejections_per_arm=MIN_CONDITIONAL_OUTCOMES,
        minimum_human_acceptances_per_arm=MIN_CONDITIONAL_OUTCOMES,
        joint_gain_over_operational_single=MIN_JOINT_GAIN,
        joint_gain_over_matched_single=MIN_JOINT_GAIN,
        joint_interval_low_over_operational_single=0.001,
        joint_interval_low_over_matched_single=0.001,
        beta_difference_upper_bound=MAX_SAFETY_LOSS,
        alpha_difference_upper_bound=MAX_SAFETY_LOSS,
        cost_per_success_ratio_to_matched_single=MAX_COST_RATIO,
        invalid_share=MAX_INVALID_SHARE,
    )
    assert classify(boundary) is Regime.CONFIRM_TESTED_FAMILIES
    assert (
        classify(replace(boundary, joint_gain_over_matched_single=0.099))
        is Regime.CUT_AS_COMPUTE
    )
    assert (
        classify(replace(boundary, beta_difference_upper_bound=0.051))
        is Regime.CUT_SAFETY
    )
    assert classify(replace(boundary, invalid_share=0.101)) is Regime.CUT_PROTOCOL
    assert (
        classify(replace(boundary, minimum_human_rejections_per_arm=29))
        is Regime.INSUFFICIENT_EVIDENCE
    )
    assert (
        classify(replace(boundary, cost_per_success_ratio_to_matched_single=1.01))
        is Regime.UNRESOLVED
    )


if __name__ == "__main__":
    _self_check()
    print("ADR-0067 regime boundaries pass")

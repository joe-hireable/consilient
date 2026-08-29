"""Deriving the three-condition threshold that decides whether the better-than-best
protocol is warranted. These are pure functions with no trajectory behind them, which is
why they sit apart from the binding tests.

All twenty-seven combinations of the tri-states are enumerated rather than sampled: the
protocol is selected only when no condition is false, unknown never blocks, and the
false conditions are reported by name so a refusal can be read.

The unknowns are deliberate, and each has its own test. No typed consumer means false,
but no consumer information at all means unknown — the difference between a question
answered and a question not asked. An incomplete index lookup cannot close a question it
did not finish asking, though a match it did find still closes it. A cost comparison is
unknown unless both ceilings exist and agree on policy version and unit, because
comparing review-adjusted minutes against wall minutes is not a comparison."""

import pytest
from consilient.instructions import (
    CostCeiling,
    IndexAnswer,
    IndexLookup,
    ProtocolThreshold,
    protocol_threshold,
)

TRI_STATES = ("true", "false", "unknown")

RELIANCE_KINDS = ("later_work", "money", "public_claim", "design_constraint")


def matching_index(*, complete: bool, verified: bool) -> IndexLookup:
    return IndexLookup(
        complete=complete,
        question_digest="q" * 64,
        scope_digest="s" * 64,
        version_digest="v" * 64,
        answers=(IndexAnswer("q" * 64, "s" * 64, "v" * 64, verified=verified),),
    )


def empty_index(*, complete: bool) -> IndexLookup:
    return IndexLookup(
        complete=complete,
        question_digest="q" * 64,
        scope_digest="s" * 64,
        version_digest="v" * 64,
    )


def cost(
    minutes: float,
    *,
    version: str = "review-adjusted.v1",
    unit: str = "review_adjusted_minutes",
) -> CostCeiling:
    return CostCeiling(minutes=minutes, policy_version=version, unit=unit)


@pytest.mark.parametrize("later_reliance", TRI_STATES)
@pytest.mark.parametrize("question_open", TRI_STATES)
@pytest.mark.parametrize("wrong_costs_more", TRI_STATES)
def test_every_threshold_combination_selects_only_when_no_condition_is_false(
    later_reliance: str, question_open: str, wrong_costs_more: str
) -> None:
    threshold = ProtocolThreshold(later_reliance, question_open, wrong_costs_more)
    states = (later_reliance, question_open, wrong_costs_more)
    assert threshold.selects is ("false" not in states)
    assert threshold.false_reasons == tuple(
        name
        for name, state in (
            ("later_reliance", later_reliance),
            ("question_open", question_open),
            ("wrong_costs_more", wrong_costs_more),
        )
        if state == "false"
    )


@pytest.mark.parametrize("kind", RELIANCE_KINDS)
def test_later_reliance_is_true_for_each_typed_consumer(kind: str) -> None:
    result = protocol_threshold(consumers=(kind,))
    assert result.later_reliance == "true"


def test_later_reliance_is_false_without_a_typed_consumer_and_unknown_when_missing() -> (
    None
):
    assert protocol_threshold(consumers=()).later_reliance == "false"
    assert protocol_threshold(consumers=("observation",)).later_reliance == "false"
    assert protocol_threshold().later_reliance == "unknown"


def test_question_open_uses_complete_index_lookup_and_stays_unknown_when_incomplete() -> (
    None
):
    assert protocol_threshold(index=empty_index(complete=True)).question_open == "true"
    assert (
        protocol_threshold(
            index=matching_index(complete=True, verified=True)
        ).question_open
        == "false"
    )
    assert (
        protocol_threshold(index=empty_index(complete=False)).question_open == "unknown"
    )
    assert (
        protocol_threshold(
            index=matching_index(complete=False, verified=True)
        ).question_open
        == "false"
    )
    assert (
        protocol_threshold(
            index=matching_index(complete=True, verified=False)
        ).question_open
        == "true"
    )
    assert protocol_threshold().question_open == "unknown"


def test_relative_cost_is_unknown_for_missing_incomparable_or_unversioned_inputs() -> (
    None
):
    higher = cost(90)
    lower = cost(30)
    assert (
        protocol_threshold(
            rework_ceiling=higher, protocol_cost_ceiling=lower
        ).wrong_costs_more
        == "true"
    )
    assert (
        protocol_threshold(
            rework_ceiling=lower, protocol_cost_ceiling=higher
        ).wrong_costs_more
        == "false"
    )
    assert protocol_threshold(rework_ceiling=higher).wrong_costs_more == "unknown"
    assert (
        protocol_threshold(
            rework_ceiling=higher, protocol_cost_ceiling=cost(30, version="other.v1")
        ).wrong_costs_more
        == "unknown"
    )
    assert (
        protocol_threshold(
            rework_ceiling=higher, protocol_cost_ceiling=cost(30, version="")
        ).wrong_costs_more
        == "unknown"
    )
    assert (
        protocol_threshold(
            rework_ceiling=higher, protocol_cost_ceiling=cost(30, unit="wall_minutes")
        ).wrong_costs_more
        == "unknown"
    )

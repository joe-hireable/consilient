"""Everything the β estimator will and will not claim. V0-06 sets the evidence floor at
thirty rejections, below which the answer is `insufficient data` and never a number;
unlabelled artefacts stay out of the denominator rather than counting as agreement; and
the constructor beneath `compute` enforces the same floor, because a floor is not an
invariant if the constructor beneath it does not hold and a knob that can lower a floor
is a bypass path around it. `mypy --strict` found the unconstructable-state defect here
in half a second that 24 passing tests had missed: `render()` unpacked `self.interval`
unconditionally, so a JSON round trip carrying `verdict=measured` with a null interval
crashed, and no test rendered a measured β at all.
`test_beta_claims_no_bound_unless_the_sampling_is_declared` asserted `is True` against a
field hard-coded to True until 20 August 2026 — the fourth instance of that pattern
found in this repository — and the bound is now conditional on a declared sampling
protocol, because if artefacts reach a human only when the checks already accepted them,
every rejected row has `verifier_accept=True` and β is 1 by construction. The forged-
reject test records which forgery actually moves the number: the V0-18 write-up
demonstrated the bypass with a forged accept, which changes neither n nor k, so the hole
was real but the example did not bite."""

import sys
import pytest
from consilient import beta as beta_mod
from v0_invariants_helpers import (
    _spend_scripts,
    now_ts,
)


# ---------------------------------------------------------------- V0-06
def test_beta_below_the_floor_is_insufficient_data_not_a_number():
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
        for _ in range(5)
    ]
    result = beta_mod.compute(rows)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.point is None and result.interval is None
    assert "insufficient data" in result.render()


def test_beta_carries_count_interval_and_window():
    rows = []
    for i in range(40):
        rows.append(
            {
                "ts": f"2026-08-{20 if i else 19}T01:00:00+01:00",
                "task_family": "repair",
                "verifier_version": "v1",
                "verifier_accept": i < 10,
                "human_verdict": "reject",
            }
        )
    result = beta_mod.compute(rows)
    assert result.verdict == beta_mod.MEASURED
    assert result.n_rejected == 40 and result.n_false_accept == 10
    assert result.point == pytest.approx(0.25)
    low, high = result.interval
    assert low < 0.25 < high
    assert result.window == ("2026-08-19T01:00:00+01:00", "2026-08-20T01:00:00+01:00")


def test_beta_claims_no_bound_unless_the_sampling_is_declared():
    """Q30: the oracle is a test whose errors correlate with the ones it grades.

    This asserted `is True` until 20 Aug 2026, against a field hard-coded to True. It
    enforced the claim rather than the property — the fourth instance of that pattern found
    in this repository — and the claim does not hold in general. β is a bound on joint error
    only if the sample is not conditioned on the verifier's own outcome. If artefacts reach
    a human only when the checks already accepted them, every rejected row has
    verifier_accept=True and β is 1 by construction. No collection protocol exists, so the
    honest default is that no bound is claimed.
    """
    result = beta_mod.compute([])
    assert result.lower_bound_on_joint_error is False, (
        "no bound may be claimed by default; the sampling property that would justify it "
        "is not established anywhere"
    )
    assert "non-stationary" in result.caveat

    declared = beta_mod.compute([], sampling_unconditioned=True)
    assert declared.lower_bound_on_joint_error is True, (
        "a caller with an unconditioned sampling protocol must be able to declare it"
    )


def test_the_rendered_beta_does_not_say_bound_when_no_bound_is_claimed():
    """The claim appeared in rendered output, which is the one place a reader looks."""
    rows = [
        {
            "ts": now_ts(),
            "verifier_accept": i < 7,
            "human_verdict": "reject",
        }
        for i in range(30)
    ]
    undeclared = beta_mod.compute(rows).render()
    assert "NOT a bound" in undeclared
    assert "lower bound" not in undeclared

    declared = beta_mod.compute(rows, sampling_unconditioned=True).render()
    assert "lower bound on a joint human-plus-checks error" in declared


def test_unlabelled_artefacts_are_not_counted_as_agreement():
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "verifier_accept": True,
            "human_verdict": None,
        }
        for _ in range(100)
    ]
    rows += [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
        for _ in range(3)
    ]
    result = beta_mod.compute(rows)
    assert result.n_rejected == 3, "unlabelled rows must not enter the denominator"
    assert result.verdict == beta_mod.INSUFFICIENT


def test_wilson_behaves_at_the_boundaries():
    low, high = beta_mod.wilson(0, 40)
    assert low == 0.0 and 0 < high < 0.2
    low, high = beta_mod.wilson(40, 40)
    assert high == 1.0 and 0.8 < low < 1.0


# --------------------------------------------- found by strict typing, not by the tests
def test_a_measured_beta_cannot_exist_without_its_interval():
    """`mypy --strict` found this; 24 passing tests did not.

    render() unpacked self.interval unconditionally, so a JSON round-trip carrying
    verdict=measured with a null interval crashed. The state is now unconstructable.
    """
    with pytest.raises(ValueError, match="must carry both a point estimate"):
        beta_mod.Beta(beta_mod.MEASURED, "repair", "v1", 40, 10, 0.25, None, None)


def test_insufficient_data_cannot_smuggle_a_point_estimate():
    with pytest.raises(ValueError, match="must not carry a point estimate"):
        beta_mod.Beta(beta_mod.INSUFFICIENT, None, None, 3, 1, 0.33, (0.1, 0.9), None)


def test_the_measured_render_path_is_exercised():
    """The gap that let the defect through: no test rendered a measured beta."""
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": i < 10,
            "human_verdict": "reject",
        }
        for i in range(40)
    ]
    line = beta_mod.compute(rows).render()
    assert "0.250" in line and "10/40" in line
    # Was `assert "lower bound on a joint" in line` until 20 Aug 2026, when the bound was
    # found to be asserted rather than established. The rendered claim is now conditional
    # on a declared sampling protocol, and the default declares none.
    assert "NOT a bound" in line


# ------------------------------------------------------ V0-06, the constructor beneath
# `compute` enforced the sample floor. A floor is not an invariant if the constructor
# beneath it does not hold.


def test_a_measured_beta_cannot_be_constructed_below_the_evidence_floor():
    with pytest.raises(ValueError, match="at least 30 rejections"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 0, 0, 0.0, (0.0, 0.0), None)


def test_a_rate_outside_zero_to_one_is_refused():
    with pytest.raises(ValueError, match=r"must lie in \[0, 1\]"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 1.5, (0.0, 1.0), None)


def test_an_inverted_interval_is_refused():
    with pytest.raises(ValueError, match="0 <= low <= high <= 1"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 0.25, (0.9, 0.1), None)


def test_a_point_outside_its_own_interval_is_refused():
    with pytest.raises(ValueError, match="outside its own interval"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 0.9, (0.1, 0.4), None)


def test_more_false_accepts_than_rejections_is_refused():
    with pytest.raises(ValueError, match=r"must lie in \[0, n_rejected\]"):
        beta_mod.Beta(beta_mod.INSUFFICIENT, None, None, 3, 9, None, None, None)


def test_the_evidence_floor_can_be_raised_but_never_lowered():
    """A knob that can lower a floor is a bypass path around it."""
    with pytest.raises(ValueError, match="may only raise the floor"):
        beta_mod.compute([], min_rejections=0)


def test_a_forged_reject_is_the_variant_that_attacks_beta():
    """Which forgery actually moves the number, recorded because I first showed the wrong one.

    The V0-18 write-up demonstrated the bypass with a forged `human_verdict: "accept"`. That
    validates and projects, but `compute()` draws its denominator from rows where the verdict
    is "reject", so an accept row changes neither n nor k. The hole was real; the example did
    not bite. The forgery that attacks beta is a **reject** paired with `verifier_accept: True`,
    which lands in both numerator and denominator.
    """
    honest = [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": i < 3,
            "human_verdict": "reject",
        }
        for i in range(30)
    ]
    base = beta_mod.compute(honest)
    assert base.verdict == beta_mod.MEASURED
    assert base.point == pytest.approx(3 / 30)

    forged_accept = honest + [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "accept",
        }
    ]
    assert beta_mod.compute(forged_accept).point == pytest.approx(base.point), (
        "a forged accept moved beta; the original write-up would have been right by accident"
    )

    forged_reject = honest + [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
    ]
    attacked = beta_mod.compute(forged_reject)
    assert attacked.point == pytest.approx(4 / 31)
    assert attacked.point > base.point, "the forged reject failed to inflate beta"


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

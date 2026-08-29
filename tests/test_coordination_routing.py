"""The two decisions taken before a run starts — which model, and how many candidates —
and the one discipline they share: refuse rather than assume when the measurement is
absent.

Model selection reads pool headroom. `cursor-models` exhausted is a refusal, not a quiet
drift to `cursor-other`; unknown headroom is a refusal too. An explicitly named model is
attended operator naming, so the avoided pool becomes the operator's choice rather than
the selector's. Models are registered only where a list was measured, which is why
`cursor-composer` has one and `claude`, `grok` and `codex` have none — a harness with no
registered models must name that gap rather than improvise.

The β-conditioned ceiling answers the second question from the same posture. The fixture
is EXP-47's measured shape: point 0.3132 over [0.2926, 0.3346], 51 of 163. The ceiling
is computed from the top of the interval, not the point estimate, and the boundary cases
are pinned at 0.3345, 0.3346 and one float below 1.0 because rounding up here would buy
an attempt the evidence does not support. An absent β is a refusal — the reason names
fabrication — and a measured zero states the arithmetic rather than issuing a licence. ε
is an exposure ceiling and must lie in the open unit interval. Today's real trajectory
has zero human rejections, so the bridge refuses, and that refusal is the honest state
of the system rather than a defect.

The last test is a source-level pin, kept here because it is where routing meets
coordination: T02 wires `routing.py` at coordination's composite-verifier gate and
nowhere else. `dispatch.py` must not import `candidates_ceiling` — the chokepoint is
coordination, not a second consumer in the runner."""

import math
import pytest
from consilient import coordination, routing
from consilient.beta import INSUFFICIENT, MEASURED, Beta
from consilient.harness import (
    DEFAULT_POOLS,
    MODELS,
    PoolState,
    model_family,
    models_for_harness,
    pool_for_model,
    select_model,
)
from coordination_helpers import (
    DISPATCH_PATH,
    ROOT,
)


def _pool(name: str, *, used: float | None, exhausted: bool = False) -> PoolState:
    return PoolState(
        name=name,
        used_percent=used,
        exhausted=exhausted,
        note="fixture",
        observed_at="2026-08-21T00:00:00+00:00",
        source="fixture",
    )


# --- model selection ----------------------------------------------------------


def test_models_are_registered_only_where_a_list_was_measured():
    assert models_for_harness("cursor-composer") == MODELS
    for harness_id in ("claude", "grok", "codex"):
        assert models_for_harness(harness_id) == ()


def test_select_model_picks_the_idlest_registered_pool():
    pools = (_pool("cursor-models", used=1.0), _pool("cursor-other", used=2.0))
    chosen = select_model("cursor-composer", pools=pools)
    assert not isinstance(chosen, str)
    assert chosen.id == "composer-2.5"  # registry order breaks the same-pool tie
    assert chosen.pool == "cursor-models"


def test_select_model_honours_a_family_request():
    pools = (_pool("cursor-models", used=1.0),)
    chosen = select_model("cursor-composer", pools=pools, family="grok")
    assert not isinstance(chosen, str)
    assert chosen.family == "grok"
    assert chosen.id == "cursor-grok-4.6-xhigh"


def test_select_model_never_falls_to_the_avoided_pool_on_its_own(tmp_path):
    """cursor-models exhausted is a refusal, not a quiet drift to cursor-other."""
    pools = (
        _pool("cursor-models", used=95.0, exhausted=True),
        _pool("cursor-other", used=3.0),
    )
    chosen = select_model("cursor-composer", pools=pools)
    assert isinstance(chosen, str)
    assert "exhausted or unmeasured" in chosen


def test_select_model_refuses_when_headroom_is_unknown():
    pools = (_pool("cursor-models", used=None),)
    chosen = select_model("cursor-composer", pools=pools)
    assert isinstance(chosen, str)


def test_select_model_treats_an_explicit_request_as_attended_naming():
    chosen = select_model("cursor-composer", pools=(), requested="claude-opus-5")
    assert not isinstance(chosen, str)
    assert chosen.id == "claude-opus-5"
    assert chosen.pool == "cursor-other"  # named, so the avoided pool is the operator's


def test_select_model_refuses_an_unknown_harness_or_family():
    assert isinstance(select_model("no-such", pools=()), str)
    refusal = select_model("cursor-composer", pools=(), family="no-such-family")
    assert isinstance(refusal, str)
    assert "known families" in refusal


def test_select_model_names_the_gap_when_a_harness_has_no_registered_models():
    refusal = select_model("grok", pools=DEFAULT_POOLS)
    assert isinstance(refusal, str)
    assert "no models registered" in refusal


def test_pool_for_model_is_registry_then_prefix_then_harness():
    assert pool_for_model("cursor-composer", "kimi-k3-max") == "cursor-models"
    assert pool_for_model("cursor-composer", "claude-opus-5") == "cursor-other"
    assert pool_for_model("grok", "anything") == "grok-weekly"
    assert pool_for_model("no-such", "anything") == "unknown"


def test_model_family_heuristic():
    assert model_family("cursor-grok-4.6-high") == "grok"
    assert model_family("composer-2.5") == "composer"
    assert model_family("Kimi-K3-Max") == "kimi"


# --- β-conditioned ceilings ----------------------------------------------------


def _measured_beta() -> Beta:
    # EXP-47's measured shape: point 0.3132 over [0.2926, 0.3346], 51 of 163.
    return Beta(MEASURED, None, None, 163, 51, 0.3132, (0.2926, 0.3346), None)


def test_ceiling_at_the_exp47_interval_is_one_at_epsilon_040():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.40)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 1
    assert ceiling.beta_used == pytest.approx(0.3346)  # the top of the interval


def test_ceiling_is_zero_below_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.3345)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 0


def test_ceiling_is_one_at_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.3346)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 1


def test_ceiling_does_not_round_up_at_a_float_boundary():
    beta = Beta(MEASURED, None, None, 30, 10, 1 / 3, (1 / 3, 1 / 3), None)
    epsilon = math.nextafter(1.0, -math.inf)
    ceiling = routing.candidates_ceiling(beta, epsilon)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 2


def test_ceiling_grows_above_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.70)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 2


def test_an_absent_beta_is_a_refusal_not_an_assumption():
    beta = Beta(INSUFFICIENT, None, None, 0, 0, None, None, None)
    outcome = routing.candidates_ceiling(beta, 0.20)
    assert isinstance(outcome, routing.RoutingRefusal)
    assert "fabricated" in outcome.reason


def test_epsilon_is_an_exposure_ceiling_and_must_be_in_the_open_unit_interval():
    for bad in (0.0, 1.0, 1.5, -0.1):
        with pytest.raises(ValueError, match="exposure ceiling"):
            routing.candidates_ceiling(_measured_beta(), bad)


def test_a_certain_bad_verifier_allows_zero_candidates():
    beta = Beta(MEASURED, None, None, 30, 30, 1.0, (1.0, 1.0), None)
    ceiling = routing.candidates_ceiling(beta, 0.99)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 0


def test_a_measured_zero_beta_states_the_arithmetic_not_a_licence():
    beta = Beta(MEASURED, None, None, 30, 0, 0.0, (0.0, 0.0), None)
    ceiling = routing.candidates_ceiling(beta, 0.20)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max is None


def test_ceiling_for_the_real_shape_of_todays_trajectory_is_a_refusal(tmp_path):
    """An empty trajectory has zero human rejections, so the bridge refuses."""
    from consilient import projection

    log = tmp_path / "log"
    log.mkdir()
    conn = projection.build(log, tmp_path / "projection.db")
    conn.close()
    outcome = routing.ceiling_for_trajectory(log, tmp_path / "projection.db", 0.20)
    assert isinstance(outcome, routing.RoutingRefusal)


def test_the_routing_mechanism_is_wired_only_at_the_composite_verifier_boundary():
    """T02 wires routing.py at coordination's composite-verifier gate.

    dispatch.py still must not import it — the chokepoint is coordination, not a
    second consumer in the runner. Removing candidates_ceiling from coordination
    is the regression this pins.
    """
    dispatch_source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "candidates_ceiling" not in dispatch_source
    # The whole coordination family, because the chokepoint is the module's responsibility and
    # not one file's: coordination.py was split on 28 August 2026 and admit_composite_exposure
    # moved to a sibling. What this pins is that routing is wired HERE and not in dispatch.py,
    # and that stays true wherever inside the family the gate is written.
    coord_source = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "src" / "consilient").glob("coordination*.py"))
    )
    assert "candidates_ceiling" in coord_source
    refusal = coordination.admit_composite_exposure(
        candidate_ordinal=1,
        task_family="code",
        protocol_id="pytest",
        protocol_version="v1",
        epsilon=0.40,
    )
    assert refusal.admitted is False
    assert refusal.recorded_exposure is False

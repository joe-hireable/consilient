"""Pool-provenance controls for automatic Cursor model selection."""

from __future__ import annotations

from consilient.harness import MODELS, ModelOption, PoolState, select_model


def test_automatic_selection_refuses_an_unverified_pool_assignment() -> None:
    unverified = ModelOption(
        "fixture-unverified",
        "cursor-composer",
        "fixture",
        "cursor-models",
    )
    pools = (
        PoolState(
            "cursor-models",
            1.0,
            False,
            "fixture",
            "2026-08-23T00:00:00+00:00",
            "test",
        ),
    )

    chosen = select_model("cursor-composer", pools=pools, models=(unverified,))

    assert isinstance(chosen, str)
    assert "pool assignment is unverified" in chosen


def test_explicit_model_keeps_the_attended_override_for_an_unverified_pool() -> None:
    unverified = ModelOption(
        "fixture-unverified",
        "cursor-composer",
        "fixture",
        "cursor-models",
    )

    chosen = select_model(
        "cursor-composer",
        pools=(),
        requested=unverified.id,
        models=(unverified,),
    )

    assert chosen is unverified


def test_registry_pool_assignments_have_explicit_verification_and_provenance() -> None:
    assert MODELS
    assert all(option.pool_provenance for option in MODELS)
    assert all(option.pool_verified for option in MODELS)


def test_kimi_and_glm_registry_ids_are_verified_cursor_other_models() -> None:
    expected_ids = {
        "kimi-k3-max",
        "kimi-k3-high",
        "kimi-k3-low",
        "kimi-k2.7-code",
        "glm-5.2-max",
        "glm-5.2-high",
    }

    assigned = {
        option.id: (option.pool, option.pool_verified)
        for option in MODELS
        if option.id in expected_ids
    }

    assert assigned == {model_id: ("cursor-other", True) for model_id in expected_ids}

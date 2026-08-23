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
    assert {option.pool_verified for option in MODELS} == {False, True}

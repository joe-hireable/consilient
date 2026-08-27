"""Pool-provenance controls for automatic Cursor model selection.

F04: every ModelOption carries a vendor-sourced pool assignment or is marked
unverified, and automatic routing refuses a pool it cannot verify. An explicit
`--model` remains the attended override. [cited: cursor.com/docs/models-and-pricing,
retrieved 2026-08-24]
"""

from __future__ import annotations

import pytest

from consilient.harness import (
    DEFAULT_POOLS,
    MODELS,
    ModelOption,
    PoolState,
    select_model,
)

VENDOR_MODELS_AND_PRICING = "https://cursor.com/docs/models-and-pricing"
VENDOR_RETRIEVED = "2026-08-24"


def _pool(name: str, used: float | None = 1.0, exhausted: bool = False) -> PoolState:
    return PoolState(
        name,
        used,
        exhausted,
        "fixture",
        "2026-08-24T00:00:00+00:00",
        "test",
    )


def test_automatic_selection_refuses_an_unverified_pool_assignment() -> None:
    unverified = ModelOption(
        "fixture-unverified",
        "cursor-composer",
        "fixture",
        "cursor-models",
    )
    chosen = select_model(
        "cursor-composer",
        pools=(_pool("cursor-models"),),
        models=(unverified,),
    )

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


def test_automatic_selection_never_spends_cursor_other_even_when_verified() -> None:
    """The avoided-pool rule is a chokepoint: it must not depend on the registry
    happening to contain only cursor-models rows."""
    other = ModelOption(
        "kimi-k3-max",
        "cursor-composer",
        "kimi",
        "cursor-other",
        pool_verified=True,
        pool_provenance=(
            f"Cursor Models and Pricing, {VENDOR_MODELS_AND_PRICING}, "
            f"retrieved {VENDOR_RETRIEVED}; Other Models table"
        ),
    )

    chosen = select_model(
        "cursor-composer",
        pools=(_pool("cursor-other", used=3.0),),
        models=(other,),
    )

    assert isinstance(chosen, str)
    assert "cursor-other" in chosen
    assert "avoided" in chosen.casefold() or "unverified" in chosen.casefold()


def test_explicit_model_may_spend_cursor_other_attended() -> None:
    other = ModelOption(
        "kimi-k3-max",
        "cursor-composer",
        "kimi",
        "cursor-other",
        pool_verified=True,
        pool_provenance=(
            f"Cursor Models and Pricing, {VENDOR_MODELS_AND_PRICING}, "
            f"retrieved {VENDOR_RETRIEVED}; Other Models table"
        ),
    )

    chosen = select_model(
        "cursor-composer",
        pools=(),
        requested=other.id,
        models=(other,),
    )

    assert chosen is other
    assert chosen.pool == "cursor-other"


def test_unmapped_model_option_defaults_to_unverified() -> None:
    option = ModelOption("invented", "cursor-composer", "invented", "cursor-models")
    assert option.pool_verified is False
    assert "unmapped" in option.pool_provenance.casefold()


def test_empty_pool_provenance_is_refused() -> None:
    with pytest.raises(ValueError, match="pool_provenance"):
        ModelOption(
            "invented",
            "cursor-composer",
            "invented",
            "cursor-models",
            pool_provenance="  ",
        )


def test_registry_pool_assignments_have_explicit_verification_and_provenance() -> None:
    assert MODELS
    composer_or_grok = [option for option in MODELS if option.family in {"composer", "grok"}]
    kimi_or_glm = [option for option in MODELS if option.family in {"kimi", "glm"}]
    assert composer_or_grok
    assert kimi_or_glm
    assert all(option.pool_verified for option in composer_or_grok)
    assert all(not option.pool_verified for option in kimi_or_glm)
    assert {option.family for option in MODELS} <= {"composer", "grok", "kimi", "glm"}
    for option in MODELS:
        assert VENDOR_MODELS_AND_PRICING in option.pool_provenance
        assert VENDOR_RETRIEVED in option.pool_provenance
        assert option.pool_provenance.strip()


def test_vendor_cursor_models_inclusion_is_pinned_to_composer_and_grok() -> None:
    by_id = {option.id: option for option in MODELS}
    for model_id in (
        "composer-2.5",
        "composer-2.5-fast",
        "cursor-grok-4.6-xhigh",
        "cursor-grok-4.5-low",
    ):
        assert by_id[model_id].pool_verified is True
        assert by_id[model_id].pool == "cursor-models"
        assert "Composer" in by_id[model_id].pool_provenance
        assert "Grok" in by_id[model_id].pool_provenance


def test_kimi_and_glm_provenance_names_the_vendor_other_models_table() -> None:
    by_id = {option.id: option for option in MODELS}
    for model_id in (
        "kimi-k3-max",
        "kimi-k3-high",
        "kimi-k3-low",
        "kimi-k2.7-code",
        "glm-5.2-max",
        "glm-5.2-high",
    ):
        option = by_id[model_id]
        assert option.pool_verified is False
        provenance = option.pool_provenance
        assert "Other Models" in provenance
        assert "Kimi K3" in provenance
        assert "Kimi K2.7 Code" in provenance
        assert "GLM 5.2" in provenance


def test_automatic_selection_of_the_live_registry_skips_unverified_rows() -> None:
    chosen = select_model("cursor-composer", pools=DEFAULT_POOLS)
    assert not isinstance(chosen, str)
    assert chosen.pool_verified is True
    assert chosen.family in {"composer", "grok"}
    assert chosen.id == "composer-2.5"


def test_automatic_kimi_or_glm_family_selection_refuses() -> None:
    for family in ("kimi", "glm"):
        chosen = select_model("cursor-composer", pools=DEFAULT_POOLS, family=family)
        assert isinstance(chosen, str)
        assert "unverified" in chosen


def test_explicit_kimi_id_still_dispatches() -> None:
    chosen = select_model(
        "cursor-composer",
        pools=(),
        requested="kimi-k3-max",
    )
    assert not isinstance(chosen, str)
    assert chosen.id == "kimi-k3-max"

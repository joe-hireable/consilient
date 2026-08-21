"""R17: reasoning capability is registry data, never a model-name guess."""

from __future__ import annotations

from dataclasses import fields
from typing import cast

import pytest

from consilient.harness import (
    MODELS,
    UNMAPPED_REASONING_PROVENANCE,
    ModelOption,
    ReasoningCapability,
    allows_reasoning_scaffold,
    select_model,
)

EXPECTED_STATES = {"native", "hybrid", "absent", "unknown"}


def test_model_options_carry_reasoning_state_and_provenance() -> None:
    field_names = {field.name for field in fields(ModelOption)}

    assert "reasoning_capability" in field_names
    assert "reasoning_provenance" in field_names
    assert MODELS
    assert {option.reasoning_capability for option in MODELS} <= EXPECTED_STATES
    assert all(option.reasoning_capability == "unknown" for option in MODELS)
    assert all(
        option.reasoning_provenance == UNMAPPED_REASONING_PROVENANCE
        for option in MODELS
    )


def test_reasoning_metadata_is_validated() -> None:
    with pytest.raises(ValueError, match="reasoning_capability"):
        ModelOption(
            "fixture",
            "cursor-composer",
            "fixture",
            "cursor-models",
            reasoning_capability=cast(ReasoningCapability, "invented"),
            reasoning_provenance="test fixture",
        )
    with pytest.raises(ValueError, match="reasoning_provenance"):
        ModelOption(
            "fixture",
            "cursor-composer",
            "fixture",
            "cursor-models",
            reasoning_capability="unknown",
            reasoning_provenance=" ",
        )


def test_only_absent_reasoning_allows_scaffolding() -> None:
    options = {
        "native": ModelOption(
            "native", "cursor-composer", "fixture", "cursor-models", "native", "fixture"
        ),
        "hybrid": ModelOption(
            "hybrid", "cursor-composer", "fixture", "cursor-models", "hybrid", "fixture"
        ),
        "absent": ModelOption(
            "absent", "cursor-composer", "fixture", "cursor-models", "absent", "fixture"
        ),
        "unknown": ModelOption(
            "unknown", "cursor-composer", "fixture", "cursor-models", "unknown", "fixture"
        ),
    }

    assert {
        state: allows_reasoning_scaffold(option) for state, option in options.items()
    } == {
        "native": False,
        "hybrid": False,
        "absent": True,
        "unknown": False,
    }


def test_explicit_unrecognised_id_is_unknown_and_cannot_scaffold() -> None:
    chosen = select_model(
        "cursor-composer", pools=(), requested="unregistered-reasoner-xhigh"
    )

    assert not isinstance(chosen, str)
    assert chosen.reasoning_capability == "unknown"
    assert chosen.reasoning_provenance == UNMAPPED_REASONING_PROVENANCE
    assert allows_reasoning_scaffold(chosen) is False


def test_registered_explicit_id_preserves_registry_metadata() -> None:
    registered = ModelOption(
        "fixture-model",
        "cursor-composer",
        "fixture",
        "cursor-models",
        reasoning_capability="absent",
        reasoning_provenance="verified fixture",
    )

    chosen = select_model(
        "cursor-composer", pools=(), requested=registered.id, models=(registered,)
    )

    assert chosen is registered


def test_reasoning_state_is_never_inferred_from_model_name_suffix() -> None:
    for suffix in ("xhigh", "high", "medium", "low", "thinking"):
        chosen = select_model(
            "cursor-composer", pools=(), requested=f"unregistered-{suffix}"
        )
        assert not isinstance(chosen, str)
        assert chosen.reasoning_capability == "unknown"

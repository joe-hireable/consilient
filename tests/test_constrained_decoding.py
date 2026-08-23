"""Grammar constraints derived from JSON Schema the caller already holds.

Steering-free: the constraint is structural, derived mechanically from the
schema — not from activation vectors or model-specific tuning.
"""

from __future__ import annotations

import json

import pytest

from consilient.harness import (
    UNCONSTRAINED_SCHEMA_KEY,
    GrammarConstraint,
    derive_grammar_constraint,
    grammar_accepts,
    schema_digest,
)


def _reasoning_then_answer_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "reasoning": {
                UNCONSTRAINED_SCHEMA_KEY: True,
                "type": "string",
            },
            "answer": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok", "fail"]},
                    "value": {"type": "integer"},
                },
                "required": ["status", "value"],
                "additionalProperties": False,
            },
        },
        "required": ["reasoning", "answer"],
        "additionalProperties": False,
    }


def test_derive_is_deterministic_for_the_same_schema():
    schema = _reasoning_then_answer_schema()
    first = derive_grammar_constraint(schema)
    second = derive_grammar_constraint(schema)
    assert first == second
    assert first.schema_digest == schema_digest(schema)
    assert first.structural_tag is None
    assert first.unconstrained_paths == ("reasoning",)
    assert "answer" in first.grammar


def test_grammar_accepts_a_valid_instance():
    schema = _reasoning_then_answer_schema()
    constraint = derive_grammar_constraint(schema)
    payload = json.dumps(
        {"reasoning": "check the counter", "answer": {"status": "ok", "value": 3}}
    )
    assert grammar_accepts(constraint, payload)


def test_grammar_rejects_structurally_invalid_json():
    schema = _reasoning_then_answer_schema()
    constraint = derive_grammar_constraint(schema)
    bad = json.dumps(
        {"reasoning": "oops", "answer": {"status": "maybe", "value": 3}}
    )
    assert not grammar_accepts(constraint, bad)


def test_registration_refuses_constrained_field_before_unconstrained():
    schema = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["ok"]}},
                "required": ["status"],
            },
            "reasoning": {UNCONSTRAINED_SCHEMA_KEY: True, "type": "string"},
        },
        "required": ["answer", "reasoning"],
    }
    with pytest.raises(ValueError, match="unconstrained field must precede"):
        derive_grammar_constraint(schema)


def test_structural_tag_scopes_the_constraint_without_ordering_the_outer_object():
    schema = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok", "fail"]},
                },
                "required": ["status"],
                "additionalProperties": False,
            },
            "reasoning": {UNCONSTRAINED_SCHEMA_KEY: True, "type": "string"},
        },
        "required": ["answer", "reasoning"],
    }
    constraint = derive_grammar_constraint(schema, structural_tag="answer")
    assert constraint.structural_tag == "answer"
    assert constraint.unconstrained_paths == ("reasoning",)
    assert grammar_accepts(
        constraint,
        json.dumps({"reasoning": "late is fine", "answer": {"status": "ok"}}),
    )


def test_the_ordering_guard_survives_deletion():
    schema = _reasoning_then_answer_schema()
    with pytest.raises(ValueError, match="unconstrained field must precede"):
        derive_grammar_constraint(
            {
                "type": "object",
                "properties": {
                    "answer": schema["properties"]["answer"],  # type: ignore[index]
                    "reasoning": schema["properties"]["reasoning"],  # type: ignore[index]
                },
                "required": ["answer", "reasoning"],
            }
        )


def test_constraint_is_steering_free_metadata():
    constraint = derive_grammar_constraint(_reasoning_then_answer_schema())
    assert isinstance(constraint, GrammarConstraint)
    assert constraint.steering_free is True
    assert "root ::=" in constraint.grammar

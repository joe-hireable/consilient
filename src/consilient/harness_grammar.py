"""Steering-free structural constraints derived from a JSON Schema the caller already
holds.

This half of the file never touched the other. It shares not one symbol with harness
selection or recording, and it is the sole user of collections.abc.Mapping across all
1,791 original lines — eleven annotations, every one of them here. That is why it comes
out first and cleanly.

The grammar is host-side metadata for constrained decoders — llguidance, XGrammar,
Outlines. It is derived mechanically: no activation-steering step exists, and
GrammarConstraint says so in a field. The ordering rule the validator enforces is the
substance — every unconstrained field must precede every constrained one, so a decoder
can hand the model free text before it starts holding it to a shape."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from .harness_registry import (
    Harness,
)


__all__ = [
    "CONSTRAINED_SCHEMA_KEY",
    "GrammarConstraint",
    "Harness",
    "UNCONSTRAINED_SCHEMA_KEY",
    "derive_grammar_constraint",
    "grammar_accepts",
    "schema_digest",
]

UNCONSTRAINED_SCHEMA_KEY = "x-consilient-unconstrained"

CONSTRAINED_SCHEMA_KEY = "x-consilient-constrained"


@dataclass(frozen=True)
class GrammarConstraint:
    """Steering-free structural constraint derived from a JSON Schema the caller holds.

    The grammar is host-side metadata for constrained decoders (llguidance, XGrammar,
    Outlines). It is derived mechanically — no activation-steering step exists.
    """

    schema_digest: str
    grammar: str
    unconstrained_paths: tuple[str, ...]
    constrained_paths: tuple[str, ...]
    structural_tag: str | None
    constrained_schema: dict[str, object]
    steering_free: bool = True


def schema_digest(schema: Mapping[str, object]) -> str:
    """Stable digest of the schema bytes the caller already holds."""
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _schema_node(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("schema node must be an object")
    return value


def _property_names(schema: Mapping[str, object]) -> tuple[str, ...]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return ()
    return tuple(properties.keys())


def _is_unconstrained_property(prop_schema: Mapping[str, object]) -> bool:
    if prop_schema.get(UNCONSTRAINED_SCHEMA_KEY) is True:
        return True
    if prop_schema.get(CONSTRAINED_SCHEMA_KEY) is True:
        return False
    prop_type = prop_schema.get("type")
    if prop_type == "string":
        if "enum" in prop_schema or "const" in prop_schema:
            return False
        return True
    return False


def _is_constrained_property(prop_schema: Mapping[str, object]) -> bool:
    if prop_schema.get(CONSTRAINED_SCHEMA_KEY) is True:
        return True
    if prop_schema.get(UNCONSTRAINED_SCHEMA_KEY) is True:
        return False
    return not _is_unconstrained_property(prop_schema)


def _validate_property_order(
    schema: Mapping[str, object], *, structural_tag: str | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema must declare an object with properties")

    if structural_tag is not None:
        if structural_tag not in properties:
            raise ValueError(
                f"structural_tag {structural_tag!r} is absent from properties"
            )
        tagged = _schema_node(properties[structural_tag])
        if tagged.get("type") != "object":
            raise ValueError(
                f"structural_tag {structural_tag!r} must reference an object schema"
            )
        outer_unconstrained = tuple(
            name
            for name in _property_names(schema)
            if name != structural_tag
            and _is_unconstrained_property(_schema_node(properties[name]))
        )
        inner_unconstrained, inner_constrained = _validate_property_order(
            tagged, structural_tag=None
        )
        inner_prefix = tuple(f"{structural_tag}.{name}" for name in inner_unconstrained)
        inner_constrained_prefix = tuple(
            f"{structural_tag}.{name}" for name in inner_constrained
        )
        return outer_unconstrained + inner_prefix, (
            structural_tag,
            *inner_constrained_prefix,
        )

    unconstrained_list: list[str] = []
    constrained_list: list[str] = []
    seen_constrained = False
    for name in properties:
        prop = _schema_node(properties[name])
        if _is_unconstrained_property(prop):
            if seen_constrained:
                raise ValueError(
                    "unconstrained field must precede every constrained field; "
                    f"{name!r} is out of order"
                )
            unconstrained_list.append(name)
        elif _is_constrained_property(prop):
            seen_constrained = True
            constrained_list.append(name)
    if not constrained_list:
        raise ValueError("schema must declare at least one constrained property")
    return tuple(unconstrained_list), tuple(constrained_list)


def _ebnf_quote(value: str) -> str:
    return json.dumps(value)


def _ebnf_string_pattern() -> str:
    return "json-string"


def _ebnf_number_pattern() -> str:
    return "json-number"


def _ebnf_boolean_pattern() -> str:
    return "( 'true' | 'false' )"


def _ebnf_for_schema(
    name: str, schema: Mapping[str, object]
) -> tuple[dict[str, str], str]:
    rules: dict[str, str] = {
        "json-string": 'json-string ::= "\\"" json-char* "\\""',
        "json-char": "json-char ::= [^\"\\\\] | '\\\\' [\"\\\\/bfnrt]",
        "json-number": "json-number ::= '-'? [0-9]+",
    }
    schema_type = schema.get("type")
    if schema_type == "string":
        enum = schema.get("enum")
        if isinstance(enum, list) and enum:
            enum_parts = " | ".join(_ebnf_quote(str(item)) for item in enum)
            return rules, f"( {enum_parts} )"
        return rules, _ebnf_string_pattern()
    if schema_type == "integer" or schema_type == "number":
        return rules, _ebnf_number_pattern()
    if schema_type == "boolean":
        return rules, _ebnf_boolean_pattern()
    if schema_type == "array":
        items = schema.get("items")
        if not isinstance(items, dict):
            raise ValueError(f"{name}: array schema must declare items")
        item_rules, item_ref = _ebnf_for_schema(f"{name}_item", items)
        rules.update(item_rules)
        return rules, f"'[' ws {item_ref} ( ws ',' ws {item_ref} )* ws ']'"
    if schema_type != "object":
        raise ValueError(f"{name}: unsupported schema type {schema_type!r}")

    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ValueError(f"{name}: object schema must declare properties")
    required_raw = schema.get("required", [])
    required = (
        {item for item in required_raw if isinstance(item, str)}
        if isinstance(required_raw, list)
        else set()
    )
    prop_names = tuple(properties.keys())
    parts: list[str] = ["'{' ws"]
    for index, prop_name in enumerate(prop_names):
        prop_rules, prop_ref = _ebnf_for_schema(
            f"{name}_{prop_name}", _schema_node(properties[prop_name])
        )
        rules.update(prop_rules)
        if index:
            parts.append(" ws ',' ws ")
        parts.append(f"{_ebnf_quote(prop_name)} ws ':' ws {prop_ref}")
        if prop_name not in required:
            parts[-1] = f"( {parts[-1]} )?"
    parts.append(" ws '}'")
    return rules, "".join(parts)


def _render_grammar(root_rule: str, rules: Mapping[str, str]) -> str:
    lines = ["ws ::= [ \\t\\n\\r]*", f"root ::= {root_rule}"]
    for name, body in rules.items():
        if name in {"ws", "root"}:
            continue
        lines.append(body)
    return "\n".join(lines)


def _constrained_schema(
    schema: Mapping[str, object], *, structural_tag: str | None
) -> dict[str, object]:
    if structural_tag is None:
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("schema must declare properties")
        constrained_props = {
            name: properties[name]
            for name in properties
            if _is_constrained_property(_schema_node(properties[name]))
        }
        required_raw = schema.get("required", [])
        required = (
            [
                item
                for item in required_raw
                if isinstance(item, str) and item in constrained_props
            ]
            if isinstance(required_raw, list)
            else []
        )
        return {
            "type": "object",
            "properties": constrained_props,
            "required": required,
            "additionalProperties": schema.get("additionalProperties", False),
        }
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("schema must declare properties")
    return _schema_node(properties[structural_tag])


def derive_grammar_constraint(
    schema: Mapping[str, object],
    *,
    structural_tag: str | None = None,
) -> GrammarConstraint:
    """Derive a steering-free grammar constraint from `schema`.

    Registration refuses layouts where an unconstrained reasoning field follows a
    constrained answer field unless `structural_tag` scopes the constraint.
    """
    if schema.get("type") != "object":
        raise ValueError("top-level schema must be type object")
    unconstrained_paths, constrained_paths = _validate_property_order(
        schema, structural_tag=structural_tag
    )
    target = _constrained_schema(schema, structural_tag=structural_tag)
    rules, root_ref = _ebnf_for_schema("root", target)
    grammar = _render_grammar(root_ref, rules)
    return GrammarConstraint(
        schema_digest=schema_digest(schema),
        grammar=grammar,
        unconstrained_paths=unconstrained_paths,
        constrained_paths=constrained_paths,
        structural_tag=structural_tag,
        constrained_schema=target,
    )


def _validate_instance(value: object, schema: Mapping[str, object]) -> bool:
    schema_type = schema.get("type")
    if schema_type == "string":
        if not isinstance(value, str):
            return False
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            return False
        const = schema.get("const")
        if const is not None and value != const:
            return False
        return True
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "array":
        if not isinstance(value, list):
            return False
        items = schema.get("items")
        if not isinstance(items, dict):
            return False
        return all(_validate_instance(item, items) for item in value)
    if schema_type != "object":
        return False
    if not isinstance(value, dict):
        return False
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return False
    required_raw = schema.get("required", [])
    required = (
        {item for item in required_raw if isinstance(item, str)}
        if isinstance(required_raw, list)
        else set()
    )
    for req in required:
        if req not in value:
            return False
    if schema.get("additionalProperties") is False:
        if any(key not in properties for key in value):
            return False
    for key, prop_schema in properties.items():
        if key not in value:
            continue
        if not _validate_instance(value[key], _schema_node(prop_schema)):
            return False
    return True


def grammar_accepts(constraint: GrammarConstraint, text: str) -> bool:
    """Return whether `text` satisfies the constrained portion of the derivation."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    if constraint.structural_tag is not None:
        tagged = parsed.get(constraint.structural_tag)
        return _validate_instance(tagged, constraint.constrained_schema)
    constrained_only = {
        key: parsed[key] for key in constraint.constrained_paths if key in parsed
    }
    if set(constrained_only) != set(constraint.constrained_paths):
        return False
    return _validate_instance(constrained_only, constraint.constrained_schema)

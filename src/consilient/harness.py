"""Harness registry, pool selection and dispatch recording.

Policy lives here. Process execution does not: `src/consilient/` is AST-locked against
`subprocess`, sockets and credentials. `scripts/dispatch.py` is the runner.

Selection prefers the pool with the most remaining headroom and never silently spends an
exhausted pool. Refusing with a reason is the success path when the scarce resource is
the only thing left.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from .events import (
    CAPABILITY_GAP_KIND,
    SCHEMA_VERSION,
    EventPayload,
    append,
)

UNCONSTRAINED_SCHEMA_KEY = "x-consilient-unconstrained"
CONSTRAINED_SCHEMA_KEY = "x-consilient-constrained"

# Operator observation, 21 August 2026. Claude weekly is "nearly exhausted"; no precise
# counter was supplied, so it is flagged exhausted rather than given an invented percent.
EXHAUSTED_USED_PERCENT = 90.0
HEADROOM_MAX_AGE = timedelta(minutes=15)
DISPATCH_ACTOR = "consilient.dispatch"
REFUSED_KIND = "dispatch.refused"
DISPATCH_OUTCOME_KIND = "dispatch.outcome"
FANOUT_KIND = "dispatch.fanout"
REQUEST_RECORD_KIND = "request.record"
REQUEST_RECORD_FIELDS: tuple[str, ...] = (
    "t_send",
    "t_first_chunk",
    "t_first_nonempty_chunk",
    "n_chunks",
    "output_tokens",
    "cache_read_input_tokens",
    "in_flight_at_dispatch",
)

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
            raise ValueError(f"structural_tag {structural_tag!r} is absent from properties")
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
        return outer_unconstrained + inner_prefix, (structural_tag, *inner_constrained_prefix)

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


def _ebnf_for_schema(name: str, schema: Mapping[str, object]) -> tuple[dict[str, str], str]:
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
        required = [
            item
            for item in required_raw
            if isinstance(item, str) and item in constrained_props
        ] if isinstance(required_raw, list) else []
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
            raise ValueError(f"structural_tag {structural_tag!r} is absent from properties")
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
        return outer_unconstrained + inner_prefix, (structural_tag, *inner_constrained_prefix)

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


def _ebnf_for_schema(name: str, schema: Mapping[str, object]) -> tuple[dict[str, str], str]:
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
        required = [
            item
            for item in required_raw
            if isinstance(item, str) and item in constrained_props
        ] if isinstance(required_raw, list) else []
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


Status = Literal["ok", "silent", "failed", "timeout", "refused", "killed"]
DecisionKind = Literal["run", "refuse"]
VerdictKind = Literal["agree", "disagree", "incomparable"]
PermissionMode = Literal["bypass", "prompt"]
ReasoningCapability = Literal["native", "hybrid", "absent", "unknown"]

REASONING_CAPABILITIES: frozenset[str] = frozenset(
    {"native", "hybrid", "absent", "unknown"}
)
UNMAPPED_REASONING_PROVENANCE = (
    "unmapped model id; no verified reasoning-capability source"
)
UNMAPPED_POOL_PROVENANCE = "unmapped model id; no verified pool-assignment source"
CURSOR_MODELS_POOL_PROVENANCE = (
    "Cursor Models and Pricing, https://cursor.com/docs/models-and-pricing, "
    "retrieved 2026-08-23; Composer 2.5 and Cursor Grok 4.5/4.6 are Cursor Models"
)
CURSOR_UNVERIFIED_POOL_PROVENANCE = (
    "Cursor Models and Pricing, https://cursor.com/docs/models-and-pricing, "
    "retrieved 2026-08-23; exact Kimi/GLM CLI ids are not individually classified"
)

# Default is bypass: the principal asked that dispatched harnesses run like this Grok
# session, without per-tool prompts. `prompt` is the attended alternative. Flags were
# read from each CLI's --help on 21 August 2026. [measured]
DEFAULT_PERMISSION_MODE: PermissionMode = "bypass"
BYPASS_FLAGS: dict[str, tuple[str, ...]] = {
    "claude": ("--dangerously-skip-permissions",),
    "codex": ("--dangerously-bypass-approvals-and-sandbox",),
    "grok": ("--always-approve",),
    "cursor-composer": ("--force", "--trust"),
}

SILENT_MARKERS: tuple[str, ...] = (
    "workspace trust required",
    "untrusted workspace",
    "trust this workspace",
)


@dataclass(frozen=True)
class Harness:
    """One installed-or-installable coding harness and the pool it draws on."""

    id: str
    family: str
    pool: str
    binary: str


@dataclass(frozen=True)
class PoolState:
    """Known headroom for one quota pool. `used_percent` is None when unknown."""

    name: str
    used_percent: float | None
    exhausted: bool
    note: str
    observed_at: str
    source: str


@dataclass(frozen=True)
class Probe:
    """Result of probing whether a harness is actually reachable. Produced by the runner."""

    harness_id: str
    installed: bool
    version: str | None
    detail: str


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    harness: Harness | None
    reason: str
    considered: tuple[str, ...]


@dataclass(frozen=True)
class FanoutDecision:
    kind: DecisionKind
    first: Harness | None
    second: Harness | None
    reason: str
    considered: tuple[str, ...]


@dataclass(frozen=True)
class RequestTiming:
    """Per-request timing row for BU5 / X05. Timestamps are RFC3339 UTC."""

    t_send: str
    t_first_chunk: str
    t_first_nonempty_chunk: str
    n_chunks: int
    output_tokens: int
    cache_read_input_tokens: int
    in_flight_at_dispatch: int

    def as_data(self) -> dict[str, int | str]:
        return {
            "t_send": self.t_send,
            "t_first_chunk": self.t_first_chunk,
            "t_first_nonempty_chunk": self.t_first_nonempty_chunk,
            "n_chunks": self.n_chunks,
            "output_tokens": self.output_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "in_flight_at_dispatch": self.in_flight_at_dispatch,
        }


HARNESSES: tuple[Harness, ...] = (
    Harness(id="claude", family="anthropic", pool="claude-weekly", binary="claude"),
    Harness(
        id="cursor-composer",
        family="cursor",
        pool="cursor-models",
        binary="cursor-agent",
    ),
    Harness(id="grok", family="xai", pool="grok-weekly", binary="grok"),
    Harness(id="codex", family="openai", pool="codex-weekly", binary="codex"),
)

DEFAULT_OBSERVED_AT = "2026-08-21T00:00:00+00:00"
DEFAULT_SOURCE = "operator observation, 21 August 2026"

DEFAULT_POOLS: tuple[PoolState, ...] = (
    PoolState(
        name="claude-weekly",
        used_percent=None,
        exhausted=True,
        note="nearly exhausted",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-models",
        used_percent=1.0,
        exhausted=False,
        note="Cursor Models (composer)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-other",
        used_percent=58.0,
        exhausted=False,
        note="avoid — Cursor Other Models (claude-*/gpt-*/gemini-*)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="grok-weekly",
        used_percent=2.0,
        exhausted=False,
        note="SuperGrok Heavy weekly",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="codex-weekly",
        used_percent=None,
        exhausted=False,
        note="unknown",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
)

CURSOR_OTHER_PREFIXES: tuple[str, ...] = ("claude-", "gpt-", "gemini-")


@dataclass(frozen=True)
class ModelOption:
    """One selectable model, its quota pool, and verified routing provenance.

    `native` means mandatory reasoning and `hybrid` means a user-selectable native
    mode. Legacy callers default to fail-closed `unknown`; a model name never supplies
    evidence about reasoning capability or pool assignment.
    """

    id: str
    harness_id: str
    family: str
    pool: str
    reasoning_capability: ReasoningCapability = "unknown"
    reasoning_provenance: str = UNMAPPED_REASONING_PROVENANCE
    pool_verified: bool = False
    pool_provenance: str = UNMAPPED_POOL_PROVENANCE

    def __post_init__(self) -> None:
        if (
            not isinstance(self.reasoning_capability, str)
            or self.reasoning_capability not in REASONING_CAPABILITIES
        ):
            raise ValueError(
                "reasoning_capability must be native, hybrid, absent, or unknown"
            )
        if (
            not isinstance(self.reasoning_provenance, str)
            or not self.reasoning_provenance.strip()
        ):
            raise ValueError("reasoning_provenance must be a non-empty string")
        if not isinstance(self.pool_verified, bool):
            raise ValueError("pool_verified must be a bool")
        if (
            not isinstance(self.pool_provenance, str)
            or not self.pool_provenance.strip()
        ):
            raise ValueError("pool_provenance must be a non-empty string")


def allows_reasoning_scaffold(model: ModelOption) -> bool:
    """Permit a scaffold only when verified registry data says reasoning is absent.

    Native mandatory, hybrid user-selectable, and unknown capabilities all fail closed.
    """
    return model.reasoning_capability == "absent"


# `cursor-agent --list-models` on this machine, 21 August 2026 [measured]: 204 ids. The
# Cursor Models pool serves the non-vendor families below; claude-*/gpt-*/gemini-* bill
# to the avoided Other Models pool (CURSOR_OTHER_PREFIXES). Only cursor-composer has a
# measured multi-model surface today; the other harnesses expose no probed model list
# here, so they register none rather than an invented one. `auto` is deliberately absent:
# selection must name what it spends. Registry order is the preference order within a
# family when pools tie — highest measured tier first [asserted].
CURSOR_MODEL_POOL_ASSIGNMENTS: tuple[tuple[str, str, bool, str], ...] = (
    ("composer-2.5", "composer", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("composer-2.5-fast", "composer", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("kimi-k3-max", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k3-high", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k3-low", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k2.7-code", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("cursor-grok-4.6-xhigh", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-xhigh-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-high", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-high-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-medium", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-medium-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-low", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-low-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-high", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-high-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-medium", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-medium-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-low", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-low-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("glm-5.2-max", "glm", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("glm-5.2-high", "glm", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
)

MODELS: tuple[ModelOption, ...] = tuple(
    ModelOption(
        model_id,
        "cursor-composer",
        family,
        "cursor-models",
        pool_verified=pool_verified,
        pool_provenance=pool_provenance,
    )
    for model_id, family, pool_verified, pool_provenance in CURSOR_MODEL_POOL_ASSIGNMENTS
)


def models_for_harness(
    harness_id: str, models: tuple[ModelOption, ...] = MODELS
) -> tuple[ModelOption, ...]:
    return tuple(item for item in models if item.harness_id == harness_id)


def model_family(model_id: str) -> str:
    """The model family an id belongs to. A heuristic for unregistered ids."""
    lowered = model_id.strip().casefold()
    if lowered.startswith("cursor-grok"):
        return "grok"
    return lowered.split("-", 1)[0]


def pool_for_model(
    harness_id: str,
    model_id: str,
    *,
    models: tuple[ModelOption, ...] = MODELS,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> str:
    """The pool a model draws on: the registry first, then the prefix rule."""
    for item in models:
        if item.harness_id == harness_id and item.id == model_id:
            return item.pool
    if harness_id == "cursor-composer":
        return cursor_pool_for_model(model_id)
    harness = harness_by_id(harness_id, harnesses)
    return harness.pool if harness is not None else "unknown"


def select_model(
    harness_id: str,
    *,
    pools: Sequence[PoolState],
    requested: str | None = None,
    family: str | None = None,
    models: tuple[ModelOption, ...] = MODELS,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> ModelOption | str:
    """Pick a model within a harness, or return a refusal reason string.

    An explicit `requested` id is attended naming, like an explicit `--harness`: it is
    returned with its pool resolved, unblocked. Automatic selection is stricter: only
    registered models on a pool with known, unexhausted headroom, most remaining
    headroom first, registry order within a tie. It never falls to the avoided
    cursor-other pool on its own — that is the silent-fallback shape at model level.
    """
    harness = harness_by_id(harness_id, harnesses)
    if harness is None:
        known = ", ".join(item.id for item in harnesses)
        return f"unknown harness {harness_id!r}; known: {known}"
    if requested is not None:
        for option in models:
            if option.harness_id == harness_id and option.id == requested:
                return option
        return ModelOption(
            requested,
            harness_id,
            model_family(requested),
            pool_for_model(harness_id, requested, models=models, harnesses=harnesses),
            reasoning_capability="unknown",
            reasoning_provenance=UNMAPPED_REASONING_PROVENANCE,
        )
    registered = list(models_for_harness(harness_id, models))
    if not registered:
        return (
            f"no models registered for {harness_id}; pass --model explicitly "
            "(an unregistered default would be an invented capability)"
        )
    if family is not None:
        registered = [item for item in registered if item.family == family]
        if not registered:
            known_families = sorted(
                {item.family for item in models_for_harness(harness_id, models)}
            )
            return (
                f"no {family!r} family models registered for {harness_id}; "
                f"known families: {', '.join(known_families)}"
            )
    pool_tuple = tuple(pools)
    eligible: list[tuple[int, ModelOption]] = []
    considered: list[str] = []
    for index, option in enumerate(registered):
        if not option.pool_verified:
            considered.append(f"{option.id}: pool assignment is unverified")
            continue
        pool = pool_by_name(option.pool, pool_tuple)
        if pool is None:
            considered.append(f"{option.id}: pool {option.pool} has no headroom snapshot")
            continue
        if _is_exhausted(pool):
            considered.append(f"{option.id}: {option.pool} is exhausted")
            continue
        if pool.used_percent is None:
            considered.append(f"{option.id}: {option.pool} headroom is unknown")
            continue
        eligible.append((index, option))
    if not eligible:
        detail = "; ".join(considered) if considered else "no registered models"
        return (
            f"no eligible model for {harness_id}: every registered model draws on an "
            f"exhausted or unmeasured pool, or an unverified pool assignment. {detail}. "
            "Pass --model explicitly to spend "
            "an avoided pool attended."
        )

    def rank(pair: tuple[int, ModelOption]) -> tuple[float, int]:
        index, option = pair
        pool = pool_by_name(option.pool, pool_tuple)
        assert pool is not None and pool.used_percent is not None
        return (pool.used_percent, index)

    eligible.sort(key=rank)
    return eligible[0][1]


def permission_flags(
    harness_id: str, mode: PermissionMode = DEFAULT_PERMISSION_MODE
) -> tuple[str, ...]:
    """Flags the meta-harness injects. Empty in `prompt` mode. Unknown harnesses get none."""
    if mode == "prompt":
        return ()
    return BYPASS_FLAGS.get(harness_id, ())


def load_permission_mode(path: Path | None = None) -> PermissionMode:
    """INSTANCE override. Missing or unreadable file → the default, bypass."""
    if path is None or not path.is_file():
        return DEFAULT_PERMISSION_MODE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PERMISSION_MODE
    if not isinstance(raw, dict):
        return DEFAULT_PERMISSION_MODE
    mode = raw.get("mode")
    if mode == "bypass":
        return "bypass"
    if mode == "prompt":
        return "prompt"
    return DEFAULT_PERMISSION_MODE


def harness_by_id(
    harness_id: str, harnesses: tuple[Harness, ...] = HARNESSES
) -> Harness | None:
    for item in harnesses:
        if item.id == harness_id:
            return item
    return None


def pool_by_name(name: str, pools: tuple[PoolState, ...]) -> PoolState | None:
    for item in pools:
        if item.name == name:
            return item
    return None


def probe_by_id(harness_id: str, probes: Sequence[Probe]) -> Probe | None:
    for item in probes:
        if item.harness_id == harness_id:
            return item
    return None


def cursor_pool_for_model(model: str) -> str:
    """Composer draws on Cursor Models; vendor aliases draw on the avoided Other pool."""
    lowered = model.strip().casefold()
    for prefix in CURSOR_OTHER_PREFIXES:
        if lowered.startswith(prefix):
            return "cursor-other"
    return "cursor-models"


def parse_list_models(output: str) -> tuple[str, ...]:
    """Model ids from `cursor-agent --list-models` output, in output order.

    Lines are `id - Display Name`; the header and blank lines carry no ` - `
    separator and drop out. Ids contain no spaces, so anything before the first
    separator that does is not an id line. Parsing is pure: the subprocess that
    produces `output` lives in scripts/refresh_models.py, not here (AST lock).
    """
    ids: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if " - " not in line:
            continue
        candidate = line.split(" - ", 1)[0].strip()
        if candidate and " " not in candidate:
            ids.append(candidate)
    return tuple(ids)


def cursor_models_pool_ids(live_ids: Sequence[str]) -> tuple[str, ...]:
    """The live ids that bill to the Cursor Models pool: no vendor aliases, no `auto`.

    `auto` is excluded because the registry omits it deliberately — selection must
    name what it spends — so its absence from MODELS is policy, not drift.
    """
    return tuple(
        sorted(
            {
                item.strip()
                for item in live_ids
                if item.strip() and item.strip() != "auto" and cursor_pool_for_model(item) == "cursor-models"
            }
        )
    )


def registry_drift(
    live_ids: Sequence[str],
    registered: tuple[ModelOption, ...] = MODELS,
    *,
    harness_id: str = "cursor-composer",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(unregistered live ids, stale registered ids) on the Cursor Models surface.

    Vendor-pool ids are out of scope: the registry never lists them, so their
    absence is the avoid-pool rule working, not the snapshot going stale.
    """
    live = set(cursor_models_pool_ids(live_ids))
    known = {item.id for item in registered if item.harness_id == harness_id}
    return tuple(sorted(live - known)), tuple(sorted(known - live))


def _is_exhausted(pool: PoolState) -> bool:
    if pool.exhausted:
        return True
    return pool.used_percent is not None and pool.used_percent >= EXHAUSTED_USED_PERCENT


def _blocked(
    pool: PoolState, *, allow_exhausted: bool, require_known_headroom: bool
) -> str | None:
    """Why this pool cannot be spent, or None if it can.

    Exhausted is a hard stop unless the operator names `--allow-exhausted`. Unknown
    headroom is a hard stop for automatic selection; an explicit `--harness` may
    proceed because that is attended, not a silent fallback.
    """
    if _is_exhausted(pool) and not allow_exhausted:
        note = f" ({pool.note})" if pool.note else ""
        if pool.used_percent is not None and pool.used_percent >= EXHAUSTED_USED_PERCENT:
            return (
                f"{pool.name} is at {pool.used_percent:g}% used "
                f"(threshold {EXHAUSTED_USED_PERCENT:g}%){note}"
            )
        return f"{pool.name} is exhausted{note}"
    if require_known_headroom and pool.used_percent is None:
        if allow_exhausted and _is_exhausted(pool):
            return None
        return f"{pool.name} headroom is unknown"
    return None


def remaining_percent(pool: PoolState) -> float | None:
    """The counter, not the gate. Exhaustion is `_blocked`; this is ranking input."""
    if pool.used_percent is None:
        return None
    return 100.0 - pool.used_percent


def headroom_freshness_refusal(
    pools: Sequence[PoolState], *, now: datetime
) -> str | None:
    """Refuse routing on missing, future, malformed, or stale observations."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("headroom check time must be timezone-aware")
    if not pools:
        return "headroom snapshot has no pools"
    current = now.astimezone(timezone.utc)
    for pool in pools:
        try:
            observed = datetime.fromisoformat(pool.observed_at)
        except ValueError:
            return f"{pool.name} headroom observation timestamp is malformed"
        if observed.tzinfo is None or observed.utcoffset() is None:
            return f"{pool.name} headroom observation timestamp has no timezone"
        age = current - observed.astimezone(timezone.utc)
        if age < timedelta(0):
            return f"{pool.name} headroom observation is in the future"
        if age > HEADROOM_MAX_AGE:
            return f"{pool.name} headroom observation is stale"
    return None


def _ineligible(
    harness: Harness,
    probe: Probe | None,
    pool: PoolState | None,
    *,
    allow_exhausted: bool,
    require_known_headroom: bool,
) -> str | None:
    if probe is None or not probe.installed:
        detail = probe.detail if probe is not None else "not probed"
        return f"{harness.id}: not installed ({detail})"
    if pool is None:
        return f"{harness.id}: pool {harness.pool} has no headroom snapshot"
    blocked = _blocked(
        pool,
        allow_exhausted=allow_exhausted,
        require_known_headroom=require_known_headroom,
    )
    if blocked is not None:
        return f"{harness.id}: {blocked}"
    return None


def _rank_key(harness: Harness, pool: PoolState) -> tuple[float, str]:
    remaining = remaining_percent(pool)
    # Higher remaining headroom first; unknown sorts last. harness.id breaks ties.
    score = remaining if remaining is not None else -1.0
    return (-score, harness.id)


def select(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    requested: str | None = None,
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> Decision:
    """Pick one harness. Never returns an exhausted pool unless `allow_exhausted`."""
    pool_tuple = tuple(pools)
    considered: list[str] = []

    if requested is not None:
        harness = harness_by_id(requested, harnesses)
        if harness is None:
            known = ", ".join(item.id for item in harnesses)
            return Decision(
                kind="refuse",
                harness=None,
                reason=f"unknown harness {requested!r}; known: {known}",
                considered=(),
            )
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=False,
        )
        if reason is not None:
            return Decision(
                kind="refuse",
                harness=None,
                reason=reason,
                considered=(reason,),
            )
        assert pool is not None
        remaining = remaining_percent(pool)
        headroom = (
            f"{remaining:g}% remaining"
            if remaining is not None
            else pool.note or "headroom unknown"
        )
        return Decision(
            kind="run",
            harness=harness,
            reason=f"{harness.id} on {harness.pool} ({headroom})",
            considered=(),
        )

    ranked: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        ranked.append((harness, pool))

    if not ranked:
        detail = "; ".join(considered) if considered else "no harnesses in the registry"
        return Decision(
            kind="refuse",
            harness=None,
            reason=(
                "no eligible harness: every pool is exhausted, unknown, or not installed. "
                f"{detail}"
            ),
            considered=tuple(considered),
        )

    ranked.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    harness, pool = ranked[0]
    remaining = remaining_percent(pool)
    headroom = (
        f"{remaining:g}% remaining"
        if remaining is not None
        else pool.note or "headroom unknown"
    )
    return Decision(
        kind="run",
        harness=harness,
        reason=f"{harness.id} on {harness.pool} ({headroom})",
        considered=tuple(considered),
    )


def select_fanout(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> FanoutDecision:
    """Two harnesses from different families, each eligible, most headroom first."""
    pool_tuple = tuple(pools)
    considered: list[str] = []
    eligible: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        eligible.append((harness, pool))

    eligible.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    if not eligible:
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=(
                "fan-out refused: no eligible harness. " + "; ".join(considered)
            ),
            considered=tuple(considered),
        )

    first, first_pool = eligible[0]
    second_pair: tuple[Harness, PoolState] | None = None
    for harness, pool in eligible[1:]:
        if harness.family != first.family:
            second_pair = (harness, pool)
            break
    if second_pair is None:
        families = {item.family for item, _ in eligible}
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=(
                "fan-out refused: need two different model families; "
                f"eligible families: {', '.join(sorted(families)) or 'none'}"
            ),
            considered=tuple(considered),
        )

    second, second_pool = second_pair
    first_left = remaining_percent(first_pool)
    second_left = remaining_percent(second_pool)
    first_h = (
        f"{first_left:g}% remaining" if first_left is not None else first_pool.note or "unknown"
    )
    second_h = (
        f"{second_left:g}% remaining"
        if second_left is not None
        else second_pool.note or "unknown"
    )
    return FanoutDecision(
        kind="run",
        first=first,
        second=second,
        reason=(
            f"{first.id} ({first.family}, {first_h}) and "
            f"{second.id} ({second.family}, {second_h})"
        ),
        considered=tuple(considered),
    )


def parse_status(value: str) -> Status:
    mapping: dict[str, Status] = {
        "ok": "ok",
        "silent": "silent",
        "failed": "failed",
        "timeout": "timeout",
        "refused": "refused",
        "killed": "killed",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unknown dispatch status {value!r}") from exc


def classify_artefact(
    *,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    output_bytes: int,
    diff_bytes: int,
    timed_out: bool,
) -> tuple[Status, str]:
    """Verify by artefact, never by exit code. Empty exit-0 is `silent`."""
    combined = f"{stdout}\n{stderr}"
    lowered = combined.casefold()
    # A trust banner with nothing else is silent (Cursor, measured). The same
    # banner buried in a 700 kB Codex transcript is not: twice on 21 Aug 2026
    # Codex wrote the named artefact and was recorded silent because agents.md
    # in the dump contained the marker. Marker wins only when there is no work.
    trust_only = output_bytes <= 200 and diff_bytes == 0
    for marker in SILENT_MARKERS:
        if marker in lowered and trust_only:
            return (
                "silent",
                f"harness produced no work: {marker!r} (exit {exit_code})",
            )
    if timed_out:
        return "timeout", f"timed out (exit {exit_code})"
    produced = output_bytes > 0 or diff_bytes > 0 or bool(stdout.strip() or stderr.strip())
    if not produced:
        return (
            "silent",
            f"exit {exit_code} with empty transcript and no diff",
        )
    if exit_code is None:
        return "failed", "process exited without a code"
    if exit_code != 0:
        return "failed", f"exit {exit_code}"
    return "ok", "produced an artefact"


def judge_fanout(first_text: str, second_text: str, first_ok: bool, second_ok: bool) -> VerdictKind:
    if not first_ok or not second_ok:
        return "incomparable"
    left = " ".join(first_text.split()).casefold()
    right = " ".join(second_text.split()).casefold()
    if not left or not right:
        return "incomparable"
    if left == right:
        return "agree"
    return "disagree"


# Refusal-reason markers generated by this package and by scripts/dispatch.py. Each is
# pinned by a test, so a reworded reason breaks a test loudly rather than misclassifying
# a gap quietly. Matching prose this codebase writes is not parsing model output.
_GAP_NOT_IMPLEMENTED_MARKERS: tuple[str, ...] = (
    "not installed",
    "not on path",
    "not reachable",
    "no invocation for harness",
    "unknown harness",
    "no models registered",
    "no eligible model",
)
# Refusals that time closes on its own: quota windows reset and live claims expire.
# Every other refusal escalates — fail closed rather than guess at a self-repair. The
# aggregate selection refusal ("every pool is exhausted, unknown, or not installed")
# contains a not-implemented marker by construction, so it escalates: from prose alone
# the record cannot tell a resettable window from a missing install, and guessing is
# the failure this event exists to record.
_GAP_RETRY_MARKERS: tuple[str, ...] = (
    "exhausted",
    "claims overlap a live dispatch",
)


def classify_gap(status: str, reason: str) -> tuple[str, str, str] | None:
    """Map an existing dispatch signal to (failure, closure, repair), or None if no gap.

    This is the self-healing boundary stated as policy rather than prose. The system
    MAY close a gap itself only where another attempt is honest: a pool window
    resetting, a live claim expiring, or a loud failure worth one recorded re-attempt
    (closure "retry" — every re-attempt is itself recorded, so a retry that does not
    close the gap ranks it higher on the gap view). It MUST escalate a silent run (the
    measured laundering path: four exit-0 dispatches wrote nothing on 21 Aug 2026), a
    capability that is not implemented (no retry builds it), and every refusal this
    rule does not recognise. The record is the deliverable; an honest escalation beats
    a quiet failure to self-heal.
    """
    if status == "ok":
        return None
    if status == "silent":
        return (
            "silent",
            "escalate",
            "a human inspects why the harness reported success and produced nothing; "
            "dispatch policy already forbids an unattended retry on another pool",
        )
    if status in ("failed", "timeout", "killed"):
        return (
            "failed",
            "retry",
            "re-dispatch the task; if the same failure repeats it ranks higher on the "
            "capability-gap view and a human builds the fix",
        )
    lowered = reason.casefold()
    if any(marker in lowered for marker in _GAP_NOT_IMPLEMENTED_MARKERS):
        return (
            "not_implemented",
            "escalate",
            "install or build the named capability; no retry creates it",
        )
    if any(marker in lowered for marker in _GAP_RETRY_MARKERS):
        return (
            "refused",
            "retry",
            "re-dispatch once the pool window has reset or the live claim has expired",
        )
    return (
        "refused",
        "escalate",
        "a human changes what was asked, what is configured, or the policy that "
        "refused it",
    )


def record_gap(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    attempted: str,
    failure: str,
    detail: str,
    closure: str,
    repair: str,
    source: str,
) -> EventPayload:
    """Append one capability.gap through the single writer (V0-41).

    `asked` is the task verbatim — the unprompted demand, expressed at the moment of
    need, which is the highest-signal thing a user produces. It stays inside the
    gitignored local trajectory under the same ADR-0057 rule as every dispatch record.
    """
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": CAPABILITY_GAP_KIND,
            "actor": DISPATCH_ACTOR,
            "data": {
                "asked": task,
                "attempted": attempted,
                "failure": failure,
                "detail": detail,
                "closure": closure,
                "repair": repair,
                "run_id": run_id,
                "source": source,
            },
        },
    )


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id(ts: str, task: str, label: str) -> str:
    stamp = ts.replace("-", "").replace(":", "").replace("+", "Z")[:15]
    digest = hashlib.sha256(f"{ts}\n{label}\n{task}".encode()).hexdigest()[:10]
    return f"{stamp}-{digest}"


def _event(kind: str, ts: str, data: dict[str, object]) -> EventPayload:
    payload = dict(data)
    payload.setdefault("supervised", True)
    return {
        "v": SCHEMA_VERSION,
        "ts": ts,
        "event": kind,
        "actor": DISPATCH_ACTOR,
        "data": payload,
    }


def record_refusal(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    reason: str,
    considered: Sequence[str],
    attempted: str = "harness selection",
) -> EventPayload:
    recorded = append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            REFUSED_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "status": "refused",
                "reason": reason,
                "considered": list(considered),
            },
        ),
    )
    # A refusal is a capability gap the boundary already detected: the user asked, and
    # nothing ran. It is recorded as such here, at the chokepoint every refusal passes
    # through, so no present or future caller can forget it (V0-41).
    gap = classify_gap("refused", reason)
    if gap is not None:
        failure, closure, repair = gap
        record_gap(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            attempted=attempted,
            failure=failure,
            detail=reason,
            closure=closure,
            repair=repair,
            source=REFUSED_KIND,
        )
    return recorded


def record_outcome(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    harness: Harness,
    status: Status,
    reason: str,
    exit_code: int | None,
    artefact_bytes: int,
    diff_bytes: int,
    timed_out: bool,
    duration_s: float,
    command: Sequence[str],
) -> EventPayload:
    recorded = append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            DISPATCH_OUTCOME_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "harness": harness.id,
                "family": harness.family,
                "pool": harness.pool,
                "status": status,
                "reason": reason,
                "exit_code": exit_code,
                "artefact_bytes": artefact_bytes,
                "diff_bytes": diff_bytes,
                "timed_out": timed_out,
                "duration_s": duration_s,
                "command": list(command),
            },
        ),
    )
    # A non-ok outcome is a capability gap the runner already measured: the harness was
    # asked and could not do it. Recorded at the same chokepoint so "exit 0, nothing
    # written" can never again be only a success-shaped log line (V0-41).
    gap = classify_gap(status, reason)
    if gap is not None:
        failure, closure, repair = gap
        record_gap(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            attempted=harness.id,
            failure=failure,
            detail=reason,
            closure=closure,
            repair=repair,
            source=DISPATCH_OUTCOME_KIND,
        )
    return recorded


def _as_non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _as_timestamp(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be RFC3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must carry an explicit offset")
    return value


def validate_request_record(data: object) -> dict[str, int | str]:
    """Validate a request.record payload before append."""
    if not isinstance(data, dict):
        raise ValueError("request record must be an object")
    run_id = data.get("run_id")
    harness = data.get("harness")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(harness, str) or not harness.strip():
        raise ValueError("harness must be a non-empty string")
    row: dict[str, int | str] = {
        "run_id": run_id.strip(),
        "harness": harness.strip(),
    }
    for field in REQUEST_RECORD_FIELDS:
        if field not in data:
            raise ValueError(f"{field} is required")
        value = data[field]
        if field in ("n_chunks", "output_tokens", "cache_read_input_tokens", "in_flight_at_dispatch"):
            row[field] = _as_non_negative_int(value, field)
        else:
            row[field] = _as_timestamp(value, field)
    send_ts = datetime.fromisoformat(str(row["t_send"])).astimezone(timezone.utc)
    first_ts = datetime.fromisoformat(str(row["t_first_chunk"])).astimezone(timezone.utc)
    nonempty_ts = datetime.fromisoformat(str(row["t_first_nonempty_chunk"])).astimezone(
        timezone.utc
    )
    if not (send_ts <= first_ts <= nonempty_ts):
        raise ValueError(
            "timing timestamps must satisfy t_send <= t_first_chunk <= t_first_nonempty_chunk"
        )
    return row


def _usage_int(payload: object, *keys: str) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None


def extract_usage_from_output(stdout: str, harness_id: str) -> dict[str, int]:
    """Best-effort token fields from a harness transcript. Unknown → zero."""
    output_tokens = 0
    cache_read = 0
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            continue
        found_out = _usage_int(usage, "output_tokens", "outputTokens")
        if found_out is not None:
            output_tokens = found_out
        cache = usage.get("cache")
        if isinstance(cache, dict):
            found_cache = _usage_int(cache, "read", "read_tokens", "readTokens")
            if found_cache is not None:
                cache_read = found_cache
        else:
            found_cache = _usage_int(
                usage, "cache_read_input_tokens", "cacheReadInputTokens"
            )
            if found_cache is not None:
                cache_read = found_cache
        if output_tokens or cache_read:
            break
    if harness_id == "grok" and output_tokens == 0 and cache_read == 0:
        # Grok often prints JSON on the last line; a single-object stdout is common.
        try:
            payload = json.loads(stdout.strip())
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            usage = payload.get("usage")
            if isinstance(usage, dict):
                found_out = _usage_int(usage, "output_tokens", "outputTokens")
                if found_out is not None:
                    output_tokens = found_out
                cache = usage.get("cache")
                if isinstance(cache, dict):
                    found_cache = _usage_int(cache, "read")
                    if found_cache is not None:
                        cache_read = found_cache
    return {
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
    }


def build_request_timing(
    *,
    t_send: str,
    t_first_chunk: str,
    t_first_nonempty_chunk: str,
    n_chunks: int,
    output_tokens: int,
    cache_read_input_tokens: int,
    in_flight_at_dispatch: int,
) -> RequestTiming:
    return RequestTiming(
        t_send=t_send,
        t_first_chunk=t_first_chunk,
        t_first_nonempty_chunk=t_first_nonempty_chunk,
        n_chunks=n_chunks,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
        in_flight_at_dispatch=in_flight_at_dispatch,
    )


def record_request(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    harness_id: str,
    timing: RequestTiming,
) -> EventPayload:
    """Append one request.record through the single writer (V0-41)."""
    data = validate_request_record(
        {
            "run_id": run_id,
            "harness": harness_id,
            **timing.as_data(),
        }
    )
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": REQUEST_RECORD_KIND,
            "actor": DISPATCH_ACTOR,
            "data": data,
        },
    )


def record_fanout(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    first: Harness,
    second: Harness,
    first_status: Status,
    second_status: Status,
    verdict: VerdictKind,
    first_run_id: str,
    second_run_id: str,
) -> EventPayload:
    contributors = [
        {
            "logical_identity": first.id,
            "evidence_class": f"family:{first.family}",
            "status": first_status,
            "run_id": first_run_id,
        },
        {
            "logical_identity": second.id,
            "evidence_class": f"family:{second.family}",
            "status": second_status,
            "run_id": second_run_id,
        },
    ]
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            FANOUT_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "status": verdict,
                "reason": (
                    "independent families answering the same task; "
                    "agreement is evidence, disagreement is the finding"
                ),
                "contributors": contributors,
                "first": first.id,
                "second": second.id,
            },
        ),
    )


def _as_percent(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("used_percent cannot be a boolean")
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        if value != value:  # NaN
            raise ValueError("used_percent is not a number")
        return value
    raise ValueError(f"used_percent must be a number, got {type(value).__name__}")


def pools_from_mapping(raw: object) -> tuple[PoolState, ...]:
    """Parse an operator headroom snapshot. Missing pools fall back to the default."""
    if not isinstance(raw, dict):
        raise ValueError("headroom snapshot must be an object")
    observed_at = raw.get("observed_at", DEFAULT_OBSERVED_AT)
    source = raw.get("source", "headroom file")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at must be a non-empty string")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    pools_raw = raw.get("pools")
    if not isinstance(pools_raw, dict):
        raise ValueError("headroom snapshot must carry a pools object")

    by_name: dict[str, PoolState] = {item.name: item for item in DEFAULT_POOLS}
    for name, body in pools_raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("pool name must be a non-empty string")
        if not isinstance(body, dict):
            raise ValueError(f"pool {name} must be an object")
        used = _as_percent(body.get("used_percent"))
        note_raw = body.get("note", "")
        if note_raw is None:
            note = ""
        elif isinstance(note_raw, str):
            note = note_raw
        else:
            raise ValueError(f"pool {name} note must be a string")
        exhausted_raw = body.get("exhausted")
        if exhausted_raw is None:
            exhausted_flag = False
        elif isinstance(exhausted_raw, bool):
            exhausted_flag = exhausted_raw
        else:
            raise ValueError(f"pool {name} exhausted must be a boolean")
        exhausted = exhausted_flag or (
            used is not None and used >= EXHAUSTED_USED_PERCENT
        )
        by_name[name] = PoolState(
            name=name,
            used_percent=used,
            exhausted=exhausted,
            note=note,
            observed_at=observed_at,
            source=source,
        )
    # Keep default order, then any extra pools.
    ordered = [by_name[item.name] for item in DEFAULT_POOLS]
    extras = [
        by_name[name] for name in by_name if name not in {item.name for item in DEFAULT_POOLS}
    ]
    return tuple(ordered + extras)


def load_pools(path: Path | None) -> tuple[PoolState, ...]:
    if path is None or not path.exists():
        return DEFAULT_POOLS
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"headroom file {path} is unreadable: {exc}") from exc
    return pools_from_mapping(raw)


def snapshot_mapping(pools: Sequence[PoolState]) -> dict[str, object]:
    first = pools[0] if pools else None
    return {
        "observed_at": first.observed_at if first is not None else DEFAULT_OBSERVED_AT,
        "source": first.source if first is not None else DEFAULT_SOURCE,
        "pools": {
            item.name: {
                "used_percent": item.used_percent,
                "exhausted": item.exhausted,
                "note": item.note,
            }
            for item in pools
        },
    }


def describe_registry(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    pool_tuple = tuple(pools)
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        remaining = remaining_percent(pool) if pool is not None else None
        rows.append(
            {
                "id": harness.id,
                "family": harness.family,
                "pool": harness.pool,
                "binary": harness.binary,
                "installed": probe.installed if probe is not None else False,
                "version": probe.version if probe is not None else None,
                "probe": probe.detail if probe is not None else "not probed",
                "used_percent": pool.used_percent if pool is not None else None,
                "exhausted": pool.exhausted if pool is not None else False,
                "remaining_percent": remaining,
                "note": pool.note if pool is not None else "",
            }
        )
    return rows

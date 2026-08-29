"""The capability vocabulary, and the fail-closed parsers that admit a document into it.

Every kind, gate state and grant kind this package recognises is declared here, together
with the JSON-shape and scalar validators that refuse anything else and CapabilityError,
which all of them raise. The gate parser is the sharp end: an admitted gate must carry a
grant kind and an expiry, a principal_authority grant must carry the authority event,
and a controller_baseline grant must carry both a decision id and a recovery proof and
must not reach a protected effect class.

Nothing here reads the world. The module imports dataclasses, datetime and typing and
nothing else, which is the property tests/test_capabilities_purity.py enforces across
the whole capabilities family rather than over one file."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

CapabilityKind = Literal["tool", "mcp", "skill", "plugin", "connection"]

CAPABILITY_KINDS: tuple[CapabilityKind, ...] = (
    "tool",
    "mcp",
    "skill",
    "plugin",
    "connection",
)

GateState = Literal["gated", "admitted"]

GrantKind = Literal["principal_authority", "controller_baseline.local_restorable.v1"]

GATE_STATES: tuple[GateState, ...] = ("gated", "admitted")

GRANT_KINDS: tuple[GrantKind, ...] = (
    "principal_authority",
    "controller_baseline.local_restorable.v1",
)

PROTECTED_EFFECT_CLASSES = frozenset(
    {
        "money.commit",
        "message.send",
        "content.publish",
        "external.change",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
    }
)

CONTROLLER_BASELINE_FORBIDDEN_EFFECTS = PROTECTED_EFFECT_CLASSES | {"network.call"}

_KINDS = frozenset(CAPABILITY_KINDS)


class CapabilityError(ValueError):
    """The inventory or task request cannot produce a safe capability context."""


def parse_identity(value: object) -> tuple[CapabilityKind, str]:
    """Accept one `kind:name` spelling with a known kind and a whitespace-free name."""
    if not isinstance(value, str) or value.count(":") != 1:
        raise CapabilityError("identity must be a kind:name string")
    kind_text, name = value.split(":", 1)
    if kind_text not in _KINDS:
        raise CapabilityError(
            f"identity kind must be one of {list(CAPABILITY_KINDS)!r}"
        )
    return _kind(kind_text, "identity"), _name(name, "identity")


_HEX64 = frozenset("0123456789abcdef")


def _hex_digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX64 for character in value)
    ):
        raise CapabilityError(f"{label} must be 64 lowercase hexadecimal characters")
    return value


@dataclass(frozen=True)
class Gate:
    """Technical reach and current admission are separate from availability."""

    state: GateState
    reason: str
    grant_kind: str | None
    authority_event: object | None
    decision_id: str | None
    recovery_proof_ref: object | None
    scope: tuple[str, ...]
    operations: tuple[str, ...]
    effect_classes: tuple[str, ...]
    expires_at: str | None


@dataclass(frozen=True)
class CapabilityEntry:
    """One inventory row with explicit gate state."""

    kind: CapabilityKind
    name: str
    available: bool
    provenance: tuple[str, ...]
    gate: Gate


def default_gate() -> Gate:
    """Present capability without an exact grant stays visibly gated."""
    return Gate(
        state="gated",
        reason="no_matching_grant",
        grant_kind=None,
        authority_event=None,
        decision_id=None,
        recovery_proof_ref=None,
        scope=(),
        operations=(),
        effect_classes=(),
        expires_at=None,
    )


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CapabilityError(f"{label} must be a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise CapabilityError(f"{label} keys must be strings")
        result[key] = item
    return result


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise CapabilityError(f"{label} must be a JSON array")
    result: list[object] = []
    result.extend(value)
    return result


def _keys(record: dict[str, object], expected: frozenset[str], label: str) -> None:
    actual = frozenset(record)
    if actual != expected:
        raise CapabilityError(
            f"{label} keys must be {sorted(expected)!r}; got {sorted(actual)!r}"
        )


def _kind(value: object, label: str) -> CapabilityKind:
    if not isinstance(value, str) or value not in _KINDS:
        raise CapabilityError(f"{label} kind must be one of {list(CAPABILITY_KINDS)!r}")
    return value


def _name(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(
            character.isspace() or not character.isprintable() for character in value
        )
    ):
        raise CapabilityError(
            f"{label} name must be a non-empty identifier without whitespace"
        )
    return value


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.isprintable()
    ):
        raise CapabilityError(f"{label} must be non-empty printable text")
    return value


def _nullable_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _provenance(value: object, label: str) -> tuple[str, ...]:
    values = _array(value, label)
    if not values:
        raise CapabilityError(f"{label} must contain at least one record id")
    records = tuple(
        _text(item, f"{label}[{index}]") for index, item in enumerate(values)
    )
    if len(records) != len(set(records)):
        raise CapabilityError(f"{label} contains duplicate record ids")
    return tuple(sorted(records))


def _nullable_reference(value: object, label: str) -> object | None:
    if value is None:
        return None
    record = _object(value, label)
    _keys(record, frozenset({"event_id", "event_kind", "event_sha256"}), label)
    _text(record["event_id"], f"{label}.event_id")
    _text(record["event_kind"], f"{label}.event_kind")
    digest = _text(record["event_sha256"], f"{label}.event_sha256")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise CapabilityError(
            f"{label}.event_sha256 must be 64 lowercase hexadecimal characters"
        )
    return record


def _string_list(value: object, label: str) -> tuple[str, ...]:
    items = _array(value, label)
    records = tuple(
        _text(item, f"{label}[{index}]") for index, item in enumerate(items)
    )
    if len(records) != len(set(records)):
        raise CapabilityError(f"{label} contains duplicate entries")
    return records


def _gate_state(value: object, label: str) -> GateState:
    if not isinstance(value, str) or value not in GATE_STATES:
        raise CapabilityError(f"{label} must be one of {list(GATE_STATES)!r}")
    return value


def _grant_kind(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in GRANT_KINDS:
        raise CapabilityError(f"{label} must be one of {list(GRANT_KINDS)!r}")
    return value


def _timestamp(value: object, label: str) -> str:
    value = _text(value, label)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CapabilityError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CapabilityError(f"{label} must carry an explicit offset")
    return value


def _nullable_timestamp(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _timestamp(value, label)


def _parse_gate(value: object, label: str) -> Gate:
    record = _object(value, label)
    _keys(
        record,
        frozenset(
            {
                "state",
                "reason",
                "grant_kind",
                "authority_event",
                "decision_id",
                "recovery_proof_ref",
                "scope",
                "operations",
                "effect_classes",
                "expires_at",
            }
        ),
        label,
    )
    state = _gate_state(record["state"], f"{label}.state")
    reason = _text(record["reason"], f"{label}.reason")
    grant_kind = _grant_kind(record["grant_kind"], f"{label}.grant_kind")
    authority_event = _nullable_reference(
        record["authority_event"], f"{label}.authority_event"
    )
    decision_id = _nullable_text(record["decision_id"], f"{label}.decision_id")
    recovery_proof_ref = _nullable_reference(
        record["recovery_proof_ref"], f"{label}.recovery_proof_ref"
    )
    scope = _string_list(record["scope"], f"{label}.scope")
    operations = _string_list(record["operations"], f"{label}.operations")
    effect_classes = _string_list(record["effect_classes"], f"{label}.effect_classes")
    expires_at = _nullable_timestamp(record["expires_at"], f"{label}.expires_at")
    if state == "admitted":
        if grant_kind is None:
            raise CapabilityError(f"{label} admitted gate requires grant_kind")
        if expires_at is None:
            raise CapabilityError(f"{label} admitted gate requires expires_at")
        if grant_kind == "principal_authority" and authority_event is None:
            raise CapabilityError(
                f"{label} principal_authority grant requires authority_event"
            )
        if grant_kind == "controller_baseline.local_restorable.v1":
            if decision_id is None or recovery_proof_ref is None:
                raise CapabilityError(
                    f"{label} controller_baseline grant requires decision_id and recovery_proof_ref"
                )
            forbidden = sorted(
                set(effect_classes) & CONTROLLER_BASELINE_FORBIDDEN_EFFECTS
            )
            if forbidden:
                raise CapabilityError(
                    f"{label} controller_baseline grant forbids protected reach: {forbidden}"
                )
    if state == "gated" and grant_kind is not None:
        raise CapabilityError(f"{label} gated gate must not carry grant_kind")
    return Gate(
        state=state,
        reason=reason,
        grant_kind=grant_kind,
        authority_event=authority_event,
        decision_id=decision_id,
        recovery_proof_ref=recovery_proof_ref,
        scope=scope,
        operations=operations,
        effect_classes=effect_classes,
        expires_at=expires_at,
    )


def parse_inventory_entry(
    value: object, label: str = "inventory allowlist entry"
) -> CapabilityEntry:
    """Parse one inventory allowlist row, synthesising a gated default when gate is absent."""
    record = _object(value, label)
    allowed_keys = frozenset({"kind", "name", "available", "provenance", "gate"})
    actual = frozenset(record)
    if not actual <= allowed_keys or "kind" not in actual or "name" not in actual:
        raise CapabilityError(
            f"{label} keys must be a subset of {sorted(allowed_keys)!r}"
        )
    if "available" not in actual or "provenance" not in actual:
        raise CapabilityError(f"{label} requires available and provenance")
    kind = _kind(record["kind"], label)
    name = _name(record["name"], label)
    available = record["available"]
    if not isinstance(available, bool):
        raise CapabilityError(f"{label} available must be a boolean")
    provenance = _provenance(record["provenance"], f"{label} provenance")
    gate = (
        _parse_gate(record["gate"], f"{label} gate")
        if "gate" in record
        else default_gate()
    )
    return CapabilityEntry(
        kind=kind,
        name=name,
        available=available,
        provenance=provenance,
        gate=gate,
    )


def _allowed_keys(
    record: dict[str, object],
    required: frozenset[str],
    allowed: frozenset[str],
    label: str,
) -> None:
    actual = frozenset(record)
    if not required <= actual or not actual <= allowed:
        raise CapabilityError(
            f"{label} keys must include {sorted(required)!r} and stay within {sorted(allowed)!r}; "
            f"got {sorted(actual)!r}"
        )


def _inventory_document(value: object) -> dict[str, object]:
    document = _object(value, "inventory")
    _allowed_keys(
        document,
        frozenset({"allowlist"}),
        frozenset({"allowlist", "conflicts", "heads", "manifests"}),
        "inventory",
    )
    return document


def _task_document(value: object) -> dict[str, object]:
    document = _object(value, "task request")
    _allowed_keys(
        document,
        frozenset({"capabilities"}),
        frozenset(
            {
                "capabilities",
                "destination_class",
                "execution_contract_keys",
                "identities",
            }
        ),
        "task request",
    )
    return document

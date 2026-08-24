"""Deterministic, fail-closed capability selection for one task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CapabilityKind = Literal["tool", "mcp", "skill", "plugin", "connection"]
CAPABILITY_KINDS: tuple[CapabilityKind, ...] = (
    "tool",
    "mcp",
    "skill",
    "plugin",
    "connection",
)
SCHEMA_VERSION = 1

_KINDS = frozenset(CAPABILITY_KINDS)
_KIND_ORDER: dict[CapabilityKind, int] = {
    "tool": 0,
    "mcp": 1,
    "skill": 2,
    "plugin": 3,
    "connection": 4,
}


class CapabilityError(ValueError):
    """The inventory or task request cannot produce a safe capability context."""


@dataclass(frozen=True)
class _InventoryItem:
    kind: CapabilityKind
    name: str
    available: bool
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class _RequestedItem:
    kind: CapabilityKind
    name: str
    reason: str


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
        or any(character.isspace() or not character.isprintable() for character in value)
    ):
        raise CapabilityError(f"{label} name must be a non-empty identifier without whitespace")
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


def _provenance(value: object, label: str) -> tuple[str, ...]:
    values = _array(value, label)
    if not values:
        raise CapabilityError(f"{label} must contain at least one record id")
    records = tuple(_text(item, f"{label}[{index}]") for index, item in enumerate(values))
    if len(records) != len(set(records)):
        raise CapabilityError(f"{label} contains duplicate record ids")
    return tuple(sorted(records))


def _inventory(value: object) -> tuple[_InventoryItem, ...]:
    document = _object(value, "inventory")
    _keys(document, frozenset({"allowlist"}), "inventory")
    records = _array(document["allowlist"], "inventory allowlist")
    items: list[_InventoryItem] = []
    seen: set[tuple[CapabilityKind, str]] = set()
    for index, value_item in enumerate(records):
        label = f"inventory allowlist[{index}]"
        record = _object(value_item, label)
        _keys(
            record,
            frozenset({"kind", "name", "available", "provenance"}),
            label,
        )
        kind = _kind(record["kind"], label)
        name = _name(record["name"], label)
        available = record["available"]
        if not isinstance(available, bool):
            raise CapabilityError(f"{label} available must be a boolean")
        identity = (kind, name.casefold())
        if identity in seen:
            raise CapabilityError(f"duplicate or ambiguous inventory capability: {kind}:{name}")
        seen.add(identity)
        items.append(
            _InventoryItem(
                kind=kind,
                name=name,
                available=available,
                provenance=_provenance(record["provenance"], f"{label} provenance"),
            )
        )
    return tuple(items)


def _task_request(value: object) -> tuple[_RequestedItem, ...]:
    document = _object(value, "task request")
    _keys(document, frozenset({"capabilities"}), "task request")
    records = _array(document["capabilities"], "task request capabilities")
    items: list[_RequestedItem] = []
    seen: set[tuple[CapabilityKind, str]] = set()
    for index, value_item in enumerate(records):
        label = f"task request capabilities[{index}]"
        record = _object(value_item, label)
        _keys(record, frozenset({"kind", "name", "reason"}), label)
        kind = _kind(record["kind"], label)
        name = _name(record["name"], label)
        identity = (kind, name.casefold())
        if identity in seen:
            raise CapabilityError(f"duplicate or ambiguous requested capability: {kind}:{name}")
        seen.add(identity)
        items.append(
            _RequestedItem(
                kind=kind,
                name=name,
                reason=_text(record["reason"], f"{label} reason"),
            )
        )
    return tuple(items)


def select_capabilities(inventory: object, task_request: object) -> dict[str, object]:
    """Select only requested, available allowlist entries and explain every choice."""

    allowed = {(item.kind, item.name): item for item in _inventory(inventory)}
    requested = sorted(
        _task_request(task_request),
        key=lambda item: (_KIND_ORDER[item.kind], item.name.casefold(), item.name),
    )
    selected: list[dict[str, object]] = []
    for wanted in requested:
        item = allowed.get((wanted.kind, wanted.name))
        if item is None:
            raise CapabilityError(f"unknown capability: {wanted.kind}:{wanted.name}")
        if not item.available:
            raise CapabilityError(f"unavailable capability: {wanted.kind}:{wanted.name}")
        selected.append(
            {
                "kind": item.kind,
                "name": item.name,
                "provenance": list(item.provenance),
                "reason": wanted.reason,
            }
        )
    return {"schema_version": SCHEMA_VERSION, "capabilities": selected}

"""Deterministic, fail-closed capability selection for one task.

The front door, and the only place the three refusals live: a requested capability that
is not in the allowlist, one that is present but unavailable or still gated, and one
whose grant has expired. Requests are sorted into a stable kind order before anything is
decided, so the same inventory and the same request always produce the same document.

The vocabulary and the document validators are in capabilities_parse; head and
contract-key resolution is in capabilities_manifests; the rewind-class table is in
capabilities_reversibility. This module composes them and owns nothing else. The
manifest half of the result appears only when the inventory or the request mentions it,
which is why inventory_status is reported as unmeasured rather than assumed.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from .capabilities_parse import (
    CapabilityError,
    CapabilityKind,
    Gate,
    _array,
    _inventory_document,
    _keys,
    _kind,
    _name,
    _object,
    _task_document,
    _text,
    parse_inventory_entry,
)

from .capabilities_manifests import (
    _select_manifests,
    retrieve_manifest,
)

from .capabilities_parse import (
    CAPABILITY_KINDS,
    CONTROLLER_BASELINE_FORBIDDEN_EFFECTS,
    CapabilityEntry,
    PROTECTED_EFFECT_CLASSES,
    default_gate,
)

from .capabilities_reversibility import (
    LOCALLY_CONTAINED_EFFECTS,
    REGISTERED_TOOLS,
    classify_reversibility,
)

__all__ = [
    "CAPABILITY_KINDS",
    "CONTROLLER_BASELINE_FORBIDDEN_EFFECTS",
    "CapabilityEntry",
    "CapabilityError",
    "CapabilityKind",
    "Gate",
    "LOCALLY_CONTAINED_EFFECTS",
    "PROTECTED_EFFECT_CLASSES",
    "REGISTERED_TOOLS",
    "SCHEMA_VERSION",
    "_array",
    "_inventory_document",
    "_keys",
    "_kind",
    "_name",
    "_object",
    "_select_manifests",
    "_task_document",
    "_text",
    "classify_reversibility",
    "default_gate",
    "parse_inventory_entry",
    "retrieve_manifest",
    "select_capabilities",
]

SCHEMA_VERSION = 1

_KIND_ORDER: dict[CapabilityKind, int] = {
    "tool": 0,
    "mcp": 1,
    "skill": 2,
    "plugin": 3,
    "connection": 4,
}


@dataclass(frozen=True)
class _InventoryItem:
    kind: CapabilityKind
    name: str
    available: bool
    provenance: tuple[str, ...]
    gate: Gate


@dataclass(frozen=True)
class _RequestedItem:
    kind: CapabilityKind
    name: str
    reason: str


def _inventory(value: object) -> tuple[_InventoryItem, ...]:
    document = _inventory_document(value)
    records = _array(document["allowlist"], "inventory allowlist")
    items: list[_InventoryItem] = []
    seen: set[tuple[CapabilityKind, str]] = set()
    for index, value_item in enumerate(records):
        label = f"inventory allowlist[{index}]"
        entry = parse_inventory_entry(value_item, label)
        identity = (entry.kind, entry.name.casefold())
        if identity in seen:
            raise CapabilityError(
                f"duplicate or ambiguous inventory capability: {entry.kind}:{entry.name}"
            )
        seen.add(identity)
        items.append(
            _InventoryItem(
                kind=entry.kind,
                name=entry.name,
                available=entry.available,
                provenance=entry.provenance,
                gate=entry.gate,
            )
        )
    return tuple(items)


def _task_request(value: object) -> tuple[_RequestedItem, ...]:
    document = _task_document(value)
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
            raise CapabilityError(
                f"duplicate or ambiguous requested capability: {kind}:{name}"
            )
        seen.add(identity)
        items.append(
            _RequestedItem(
                kind=kind,
                name=name,
                reason=_text(record["reason"], f"{label} reason"),
            )
        )
    return tuple(items)


def _grant_expired(gate: Gate) -> bool:
    if gate.expires_at is None:
        return False
    parsed = datetime.fromisoformat(gate.expires_at)
    return parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc)


def _gate_record(gate: Gate) -> dict[str, object]:
    record: dict[str, object] = {
        "state": gate.state,
        "reason": gate.reason,
        "grant_kind": gate.grant_kind,
        "authority_event": gate.authority_event,
        "decision_id": gate.decision_id,
        "recovery_proof_ref": gate.recovery_proof_ref,
        "scope": list(gate.scope),
        "operations": list(gate.operations),
        "effect_classes": list(gate.effect_classes),
        "expires_at": gate.expires_at,
    }
    return record


def select_capabilities(inventory: object, task_request: object) -> dict[str, object]:
    """Select only requested, available, admitted, unexpired allowlist entries."""

    inventory_body = _inventory_document(inventory)
    allowed = {(item.kind, item.name): item for item in _inventory(inventory_body)}
    request = _task_document(task_request)
    requested = sorted(
        _task_request(request),
        key=lambda item: (_KIND_ORDER[item.kind], item.name.casefold(), item.name),
    )
    selected: list[dict[str, object]] = []
    for wanted in requested:
        item = allowed.get((wanted.kind, wanted.name))
        if item is None:
            raise CapabilityError(f"unknown capability: {wanted.kind}:{wanted.name}")
        if not item.available:
            raise CapabilityError(
                f"unavailable capability: {wanted.kind}:{wanted.name}"
            )
        if item.gate.state != "admitted":
            raise CapabilityError(f"gated capability: {wanted.kind}:{wanted.name}")
        if _grant_expired(item.gate):
            raise CapabilityError(f"expired grant: {wanted.kind}:{wanted.name}")
        selected.append(
            {
                "kind": item.kind,
                "name": item.name,
                "provenance": list(item.provenance),
                "reason": wanted.reason,
                "gate": _gate_record(item.gate),
            }
        )
    selected_manifests, refusals, omissions = _select_manifests(inventory_body, request)
    result: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "capabilities": selected,
    }
    if (
        "conflicts" in inventory_body
        or "destination_class" in request
        or "execution_contract_keys" in request
        or "heads" in inventory_body
        or "identities" in request
        or "manifests" in inventory_body
    ):
        result["inventory_status"] = "unmeasured"
        result["omissions"] = omissions
        result["refusals"] = refusals
        result["selected_manifests"] = selected_manifests
    return result

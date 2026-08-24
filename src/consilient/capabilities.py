"""Deterministic, fail-closed capability selection for one task."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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

GateState = Literal["gated", "admitted"]
GrantKind = Literal["principal_authority", "controller_baseline.local_restorable.v1"]

GATE_STATES: tuple[GateState, ...] = ("gated", "admitted")
GRANT_KINDS: tuple[GrantKind, ...] = (
    "principal_authority",
    "controller_baseline.local_restorable.v1",
)

# Rewind classes from Claude Code's documented limits: 1 tool-mediated and
# snapshotted; 2 shell; 3 subagent-delegated; 4 external. Shell that can reach
# the network or a credential is class 4; only proven default-deny egress
# downgrades to 2. Unknown tools, and unknown effect classes, are class 4.
ReversibilityClass = Literal[1, 2, 3, 4]
ToolFamily = Literal["file", "shell", "subagent", "external"]
REGISTERED_TOOLS: dict[tuple[str, str], ToolFamily] = {
    ("tool", "read"): "file",
    ("tool", "write"): "file",
    ("tool", "edit"): "file",
    ("tool", "glob"): "file",
    ("tool", "grep"): "file",
    ("tool", "bash"): "shell",
    ("tool", "shell"): "shell",
    ("tool", "task"): "subagent",
    ("tool", "webfetch"): "external",
    ("tool", "websearch"): "external",
    ("mcp", "filesystem"): "file",
    ("connection", "github"): "external",
}
# The three effect classes whose reach stays inside the admitted root, so the
# tool family decides the class. Named as the contained set rather than as an
# outward denylist, so that an effect class this module has never heard of — a
# new one in effects.EFFECT_CLASSES, a misspelt one, or embodiment's own
# `physical.actuate` — is class 4 by default. A denylist fails open on exactly
# the effects that matter most. `process.run` is contained but not reversible:
# terminating a process is containment, not undo, which is why the file family
# rejects it and only a proven-sandboxed shell carries it at class 2.
# Source: docs/superpowers/specs/2026-08-22-action-surface.md, class-level
# reversibility table and its least-recoverable-atom rule. [cited]
LOCALLY_CONTAINED_EFFECTS = frozenset({"data.read", "file.change", "process.run"})

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
        if grant_kind == "principal_authority" and authority_event is None:
            raise CapabilityError(
                f"{label} principal_authority grant requires authority_event"
            )
        if grant_kind == "controller_baseline.local_restorable.v1":
            if decision_id is None or recovery_proof_ref is None:
                raise CapabilityError(
                    f"{label} controller_baseline grant requires decision_id and recovery_proof_ref"
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


def _row_object(value: object, label: str) -> dict[str, object]:
    return _object(value, label)


def _manifest_selection(row: dict[str, object]) -> dict[str, object]:
    return {
        "destination_class": row["destination_class"],
        "evidence_class": row.get("evidence_class"),
        "execution_contract_key": row["execution_contract_key"],
        "identity": row["identity"],
        "manifest_event_id": row.get("event_id") or row.get("manifest_event_id"),
        "permission_boundary": row.get("permission_boundary"),
        "status": row["status"],
        "trust_boundary": row.get("trust_boundary"),
        "version_digest": row["version_digest"],
    }


def retrieve_manifest(
    inventory: object, *, identity: str, version_digest: str
) -> dict[str, object]:
    """Return one stored manifest version, including inactive predecessors."""
    document = _inventory_document(inventory)
    parse_identity(identity)
    digest = _hex_digest(version_digest, "version_digest")
    for index, value in enumerate(
        _array(document.get("manifests", []), "inventory manifests")
    ):
        row = _row_object(value, f"inventory manifests[{index}]")
        if row.get("identity") == identity and row.get("version_digest") == digest:
            return dict(row)
    raise CapabilityError(f"unknown capability manifest: {identity}@{digest}")


def _select_manifests(
    document: dict[str, object], request: dict[str, object]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    identities = request.get("identities")
    contract_keys = request.get("execution_contract_keys")
    destination = request.get("destination_class")
    if identities is None and contract_keys is None:
        return [], [], []
    wanted_identities = (
        [
            _text(item, f"identities[{index}]")
            for index, item in enumerate(_array(identities, "identities"))
        ]
        if identities is not None
        else []
    )
    wanted_keys = (
        [
            _hex_digest(item, f"execution_contract_keys[{index}]")
            for index, item in enumerate(
                _array(contract_keys, "execution_contract_keys")
            )
        ]
        if contract_keys is not None
        else []
    )
    if destination is not None:
        destination = _text(destination, "destination_class")
    for identity in wanted_identities:
        parse_identity(identity)

    heads = [
        _row_object(item, f"inventory heads[{index}]")
        for index, item in enumerate(
            _array(document.get("heads", []), "inventory heads")
        )
    ]
    conflicts = [
        _row_object(item, f"inventory conflicts[{index}]")
        for index, item in enumerate(
            _array(document.get("conflicts", []), "inventory conflicts")
        )
    ]
    manifests = [
        _row_object(item, f"inventory manifests[{index}]")
        for index, item in enumerate(
            _array(document.get("manifests", []), "inventory manifests")
        )
    ]
    selected: list[dict[str, object]] = []
    refusals: list[dict[str, object]] = []
    omissions: list[dict[str, object]] = []

    def _identity_contract_keys(identity: str) -> tuple[set[str], set[str]]:
        keys: set[str] = set()
        event_ids: set[str] = set()
        for row in manifests:
            if row.get("identity") != identity:
                continue
            contract = row.get("execution_contract_key")
            if isinstance(contract, str):
                keys.add(contract)
            event_id = row.get("event_id")
            if isinstance(event_id, str):
                event_ids.add(event_id)
        return keys, event_ids

    def matching_conflicts(
        identity: str | None, key: str | None
    ) -> list[dict[str, object]]:
        found: list[dict[str, object]] = []
        identity_keys: set[str] = set()
        identity_event_ids: set[str] = set()
        if identity is not None:
            identity_keys, identity_event_ids = _identity_contract_keys(identity)
        for conflict in conflicts:
            if (
                destination is not None
                and conflict.get("destination_class") != destination
            ):
                continue
            contract = conflict.get("execution_contract_key")
            event_ids = conflict.get("event_ids")
            involved = set(event_ids) if isinstance(event_ids, list) else set()
            if key is not None:
                if contract != key:
                    continue
            elif identity is not None:
                if (
                    contract not in identity_keys
                    and conflict.get("identity") != identity
                    and not identity_event_ids.intersection(involved)
                ):
                    continue
            else:
                continue
            found.append(conflict)
        return found

    for identity in wanted_identities:
        hits = matching_conflicts(identity, None)
        if hits:
            refusals.append({"identity": identity, "reason": "active-head conflict"})
            continue
        matches = [
            head
            for head in heads
            if head.get("identity") == identity
            and head.get("status") == "active"
            and (destination is None or head.get("destination_class") == destination)
        ]
        if len(matches) == 1:
            selected.append(_manifest_selection(matches[0]))
        else:
            omissions.append(
                {"identity": identity, "reason": "no selectable active head"}
            )

    for key in wanted_keys:
        hits = matching_conflicts(None, key)
        if hits:
            refusals.append(
                {"execution_contract_key": key, "reason": "active-head conflict"}
            )
            continue
        matches = [
            head
            for head in heads
            if head.get("execution_contract_key") == key
            and head.get("status") == "active"
            and (destination is None or head.get("destination_class") == destination)
        ]
        if len(matches) == 1:
            row = _manifest_selection(matches[0])
            if row not in selected:
                selected.append(row)
        else:
            omissions.append(
                {"execution_contract_key": key, "reason": "no selectable active head"}
            )
    return selected, refusals, omissions


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


def classify_reversibility(
    kind: str,
    name: str,
    *,
    effect_classes: tuple[str, ...] = (),
    default_deny_egress_proven: bool = False,
    credential_reach: bool = False,
) -> ReversibilityClass:
    """Return rewind class 1-4; an unknown tool, an unknown effect class or an
    egress-capable shell is 4."""

    family = REGISTERED_TOOLS.get((kind, name))
    if family is None:
        return 4
    declared = frozenset(effect_classes)
    if declared - LOCALLY_CONTAINED_EFFECTS:
        return 4
    if family == "shell":
        if credential_reach or not default_deny_egress_proven:
            return 4
        return 2
    if family == "subagent":
        return 3
    if family == "file":
        if "process.run" in declared:
            return 4
        return 1
    return 4

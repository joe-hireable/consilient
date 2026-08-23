"""Inert, canonical records for the typed effect boundary."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast


EFFECT_CLASSES = frozenset(
    {
        "file.change",
        "data.read",
        "process.run",
        "system.change",
        "network.call",
        "external.change",
        "message.send",
        "content.publish",
        "money.commit",
        "obligation.commit",
        "authority.change",
        "physical.actuate",
    }
)
EFFECT_INTENT = "effect.intent"
EFFECT_RECEIPT = "effect.receipt"
_RECEIPT_STATUSES = frozenset({"succeeded", "failed", "refused", "unknown"})
_FINAL_RECEIPT_STATUSES = _RECEIPT_STATUSES - {"unknown"}


class EffectError(ValueError):
    """An effect record does not meet the canonical contract."""


@dataclass(frozen=True)
class _FrozenMapping(Mapping[str, object]):
    """An immutable stdlib-only mapping for a frozen manifest."""

    entries: tuple[tuple[str, object], ...]

    def __getitem__(self, key: str) -> object:
        for item_key, value in self.entries:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self.entries)

    def __len__(self) -> int:
        return len(self.entries)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EffectError(f"{field} must be a non-empty string")
    return value


def _digest(value: object, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise EffectError(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise EffectError(f"{field} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise EffectError(f"{field} keys must be strings")
    return value


def _exact_keys(value: Mapping[str, object], field: str, expected: set[str]) -> None:
    actual = set(value)
    if actual != expected:
        raise EffectError(
            f"{field} must contain exactly {sorted(expected)}, got {sorted(actual)}"
        )


def _broker_reference(value: object, field: str) -> None:
    item = _mapping(value, field)
    _exact_keys(item, field, {"kind", "reference"})
    if item["kind"] != "broker_reference":
        raise EffectError(f"{field} must be an opaque broker reference")
    _text(item["reference"], f"{field}.reference")


def _keyed_commitment(value: object, field: str) -> None:
    item = _mapping(value, field)
    _exact_keys(item, field, {"kind", "algorithm", "domain", "key_version", "commitment"})
    if item["kind"] != "keyed_commitment":
        raise EffectError(f"{field} must be a domain-separated keyed commitment")
    _text(item["algorithm"], f"{field}.algorithm")
    _text(item["domain"], f"{field}.domain")
    _text(item["key_version"], f"{field}.key_version")
    _digest(item["commitment"], f"{field}.commitment")


def _protected(value: object, field: str, *, credential: bool = False) -> None:
    item = _mapping(value, field)
    kind = item.get("kind")
    if kind == "broker_reference":
        _broker_reference(item, field)
        return
    if not credential and kind == "keyed_commitment":
        _keyed_commitment(item, field)
        return
    if credential:
        raise EffectError(f"{field} must be an opaque broker reference")
    raise EffectError(f"{field} must be an opaque broker reference or keyed commitment")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return _FrozenMapping(tuple((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _strings(value: object, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        raise EffectError(f"{field} must be a list")
    items = tuple(_text(item, field) for item in value)
    if not allow_empty and not items:
        raise EffectError(f"{field} must not be empty")
    if len(set(items)) != len(items):
        raise EffectError(f"{field} must not contain duplicates")
    return items


@dataclass(frozen=True)
class EffectManifest:
    """The sole secret-free declaration of one adapter invocation."""

    operation_id: str
    work_item_id: str
    attempt_id: str
    adapter: object
    forward: object
    scope: object
    operations: object
    effects: object
    inventory_snapshot: object
    gate_snapshot: object
    authority_snapshot: object
    law_snapshot: object
    start_state: object
    observer: object
    expected_state: object
    reversal: object
    declared_residuals: object
    ceilings: object
    parent_operation_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.operation_id, "operation_id")
        _text(self.work_item_id, "work_item_id")
        _text(self.attempt_id, "attempt_id")
        if self.parent_operation_id is not None:
            _text(self.parent_operation_id, "parent_operation_id")

        adapter = _mapping(self.adapter, "adapter")
        _exact_keys(adapter, "adapter", {"id", "version", "implementation_digest"})
        _text(adapter["id"], "adapter.id")
        _text(adapter["version"], "adapter.version")
        _digest(adapter["implementation_digest"], "adapter.implementation_digest")
        _protected(self.forward, "forward")
        _protected(self.scope, "scope")
        _strings(self.operations, "operations")
        effects = _strings(self.effects, "effects")
        unknown = sorted(set(effects) - EFFECT_CLASSES)
        if unknown:
            raise EffectError(f"effects must use exact effect classes, got {unknown}")

        for field, value in (
            ("inventory_snapshot", self.inventory_snapshot),
            ("gate_snapshot", self.gate_snapshot),
            ("law_snapshot", self.law_snapshot),
        ):
            snapshot = _mapping(value, field)
            _exact_keys(snapshot, field, {"digest"})
            _digest(snapshot["digest"], f"{field}.digest")
        _protected(self.authority_snapshot, "authority_snapshot")
        _protected(self.start_state, "start_state")
        observer = _mapping(self.observer, "observer")
        _exact_keys(observer, "observer", {"id", "policy_digest"})
        _text(observer["id"], "observer.id")
        _digest(observer["policy_digest"], "observer.policy_digest")
        _protected(self.expected_state, "expected_state")
        reversal = _mapping(self.reversal, "reversal")
        _exact_keys(reversal, "reversal", {"kind", "name"})
        _text(reversal["kind"], "reversal.kind")
        _text(reversal["name"], "reversal.name")
        _strings(self.declared_residuals, "declared_residuals", allow_empty=True)
        ceilings = _mapping(self.ceilings, "ceilings")
        if not ceilings:
            raise EffectError("ceilings must not be empty")
        for name, ceiling in ceilings.items():
            _text(name, "ceilings key")
            if not isinstance(ceiling, int | float) or isinstance(ceiling, bool) or ceiling < 0:
                raise EffectError(f"ceilings.{name} must be a non-negative number")

        object.__setattr__(self, "adapter", _freeze(self.adapter))
        object.__setattr__(self, "forward", _freeze(self.forward))
        object.__setattr__(self, "scope", _freeze(self.scope))
        object.__setattr__(self, "operations", _freeze(self.operations))
        object.__setattr__(self, "effects", _freeze(self.effects))
        object.__setattr__(self, "inventory_snapshot", _freeze(self.inventory_snapshot))
        object.__setattr__(self, "gate_snapshot", _freeze(self.gate_snapshot))
        object.__setattr__(self, "authority_snapshot", _freeze(self.authority_snapshot))
        object.__setattr__(self, "law_snapshot", _freeze(self.law_snapshot))
        object.__setattr__(self, "start_state", _freeze(self.start_state))
        object.__setattr__(self, "observer", _freeze(self.observer))
        object.__setattr__(self, "expected_state", _freeze(self.expected_state))
        object.__setattr__(self, "reversal", _freeze(self.reversal))
        object.__setattr__(self, "declared_residuals", _freeze(self.declared_residuals))
        object.__setattr__(self, "ceilings", _freeze(self.ceilings))

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "operation_id": _thaw(self.operation_id),
            "work_item_id": _thaw(self.work_item_id),
            "attempt_id": _thaw(self.attempt_id),
            "adapter": _thaw(self.adapter),
            "forward": _thaw(self.forward),
            "scope": _thaw(self.scope),
            "operations": _thaw(self.operations),
            "effects": _thaw(self.effects),
            "inventory_snapshot": _thaw(self.inventory_snapshot),
            "gate_snapshot": _thaw(self.gate_snapshot),
            "authority_snapshot": _thaw(self.authority_snapshot),
            "law_snapshot": _thaw(self.law_snapshot),
            "start_state": _thaw(self.start_state),
            "observer": _thaw(self.observer),
            "expected_state": _thaw(self.expected_state),
            "reversal": _thaw(self.reversal),
            "declared_residuals": _thaw(self.declared_residuals),
            "ceilings": _thaw(self.ceilings),
        }
        if self.parent_operation_id is not None:
            record["parent_operation_id"] = _thaw(self.parent_operation_id)
        return record

    @classmethod
    def from_record(cls, value: object) -> "EffectManifest":
        record = _mapping(value, "manifest")
        required = set(cls.__dataclass_fields__) - {"parent_operation_id"}
        optional = required | {"parent_operation_id"}
        if set(record) not in (required, optional):
            raise EffectError("manifest has missing or unknown fields")
        return cls(**cast(Any, dict(record)))

    def canonical(self) -> str:
        return json.dumps(self.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    def binding(self) -> dict[str, object]:
        return {"kind": "inline", "value": self.to_record(), "digest": self.digest}


def _binding(value: object) -> EffectManifest | None:
    binding = _mapping(value, "manifest")
    kind = binding.get("kind")
    if kind == "inline":
        _exact_keys(binding, "manifest", {"kind", "value", "digest"})
        manifest = EffectManifest.from_record(binding["value"])
        if binding["digest"] != manifest.digest:
            raise EffectError("manifest.digest must match the canonical manifest")
        return manifest
    if kind == "reference":
        _exact_keys(binding, "manifest", {"kind", "reference", "digest"})
        _broker_reference(binding["reference"], "manifest.reference")
        _digest(binding["digest"], "manifest.digest")
        return None
    raise EffectError("manifest.kind must be inline or reference")


def _timestamp(value: object, field: str) -> datetime:
    value = _text(value, field)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EffectError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EffectError(f"{field} must carry an explicit offset")
    return parsed


def _intent(data: Mapping[str, object]) -> None:
    _exact_keys(data, "effect.intent.data", {"intent_id", "manifest", "disposition", "decision_id", "admission"})
    _text(data["intent_id"], "effect.intent.intent_id")
    manifest = _binding(data["manifest"])
    _text(data["disposition"], "effect.intent.disposition")
    admission = _mapping(data["admission"], "effect.intent.admission")
    kind = admission.get("kind")
    if kind == "observation":
        _exact_keys(admission, "effect.intent.admission", {"kind", "observation_id"})
        _text(admission["observation_id"], "effect.intent.observation_id")
        if data["decision_id"] is not None:
            raise EffectError("observation intent must carry decision_id: null")
        if manifest is None or not set(_strings(manifest.effects, "manifest.effects")) <= {
            "data.read",
            "network.call",
        }:
            raise EffectError("observation intent requires an inline read-only manifest")
        return
    if kind != "material":
        raise EffectError("effect.intent.admission.kind must be observation or material")
    _exact_keys(admission, "effect.intent.admission", {"kind", "authority_chain"})
    decision_id = _text(data["decision_id"], "effect.intent.decision_id")
    chain = _mapping(admission["authority_chain"], "effect.intent.authority chain")
    if chain.get("kind") == "autonomous_decision":
        _exact_keys(chain, "effect.intent.authority chain", {"kind", "decision_id"})
        if chain["decision_id"] != decision_id:
            raise EffectError("authority chain decision_id must match effect.intent.decision_id")
        return
    if chain.get("kind") == "protected_authority":
        _exact_keys(
            chain,
            "effect.intent.authority chain",
            {"kind", "decision_id", "proposal_id", "authority_id"},
        )
        if chain["decision_id"] != decision_id:
            raise EffectError("authority chain decision_id must match effect.intent.decision_id")
        _text(chain["proposal_id"], "effect.intent.authority chain.proposal_id")
        _text(chain["authority_id"], "effect.intent.authority chain.authority_id")
        return
    raise EffectError("material intent requires exactly one decision/authority chain")


def _receipt(data: Mapping[str, object]) -> None:
    expected = {
        "receipt_id", "intent_id", "status", "started_at", "ended_at",
        "provider_request", "provider_receipt", "request_commitment",
        "response_commitment", "content_commitment", "observed_consumption",
        "post_state", "observed_residuals", "child_operation_ids",
    }
    if "supersedes" in data:
        expected.add("supersedes")
    _exact_keys(data, "effect.receipt.data", expected)
    _text(data["receipt_id"], "effect.receipt.receipt_id")
    _text(data["intent_id"], "effect.receipt.intent_id")
    if data["status"] not in _RECEIPT_STATUSES:
        raise EffectError(f"effect.receipt.status must be one of {sorted(_RECEIPT_STATUSES)}")
    if _timestamp(data["ended_at"], "effect.receipt.ended_at") < _timestamp(data["started_at"], "effect.receipt.started_at"):
        raise EffectError("effect.receipt.ended_at must not precede started_at")
    _protected(data["provider_request"], "effect.receipt.provider_request")
    _protected(data["provider_receipt"], "effect.receipt.provider_receipt")
    _keyed_commitment(data["request_commitment"], "effect.receipt.request_commitment")
    _keyed_commitment(data["response_commitment"], "effect.receipt.response_commitment")
    _keyed_commitment(data["content_commitment"], "effect.receipt.content_commitment")
    consumption = _mapping(data["observed_consumption"], "effect.receipt.observed_consumption")
    for name, amount in consumption.items():
        _text(name, "effect.receipt.observed_consumption key")
        if not isinstance(amount, int | float) or isinstance(amount, bool) or amount < 0:
            raise EffectError(f"effect.receipt.observed_consumption.{name} must be non-negative")
    _protected(data["post_state"], "effect.receipt.post_state")
    _strings(data["observed_residuals"], "effect.receipt.observed_residuals", allow_empty=True)
    _strings(data["child_operation_ids"], "effect.receipt.child_operation_ids", allow_empty=True)
    if "supersedes" in data:
        _text(data["supersedes"], "effect.receipt.supersedes")


def validate_effect_event(event: Mapping[str, object]) -> None:
    """Validate only the two effect event shapes; no effect is performed here."""
    kind = event.get("event")
    if kind not in {EFFECT_INTENT, EFFECT_RECEIPT}:
        return
    data = _mapping(event.get("data"), f"{kind}.data")
    if kind == EFFECT_INTENT:
        _intent(data)
    else:
        _receipt(data)


def receipt_chain_validator(prefix: tuple[Any, ...], rejections: tuple[Any, ...], candidates: tuple[dict[str, Any], ...]) -> None:
    """Purely refuse duplicate intents and forked receipt heads in one log replay."""
    del rejections
    intents: set[str] = set()
    receipt_ids: set[str] = set()
    heads: dict[str, tuple[str, str]] = {}
    for item in (*prefix, *candidates):
        raw = item if isinstance(item, Mapping) else item.raw
        if raw.get("event") == EFFECT_INTENT:
            intent_id = raw["data"]["intent_id"]
            if intent_id in intents:
                raise EffectError(f"receipt chain has duplicate intent_id {intent_id!r}")
            intents.add(intent_id)
            continue
        if raw.get("event") != EFFECT_RECEIPT:
            continue
        data = raw["data"]
        receipt_id = data["receipt_id"]
        intent_id = data["intent_id"]
        if receipt_id in receipt_ids:
            raise EffectError(f"receipt chain has duplicate receipt_id {receipt_id!r}")
        receipt_ids.add(receipt_id)
        if intent_id not in intents:
            raise EffectError(f"receipt chain receipt {receipt_id!r} precedes its intent")
        supersedes = data.get("supersedes")
        current = heads.get(intent_id)
        if supersedes is None:
            if current is not None:
                raise EffectError("receipt chain has conflicting heads")
            heads[intent_id] = (receipt_id, data["status"])
            continue
        if current is None or supersedes != current[0] or current[1] != "unknown":
            raise EffectError("receipt chain supersedes only its current unknown head")
        if data["status"] not in _FINAL_RECEIPT_STATUSES:
            raise EffectError("receipt chain may resolve unknown only to a final status")
        heads[intent_id] = (receipt_id, data["status"])

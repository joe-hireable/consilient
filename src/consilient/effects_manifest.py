"""The sealed, secret-free records an effect is declared and reported in.

An EffectManifest carries digests, opaque broker references and domain-separated keyed
commitments in place of the things themselves, so a raw credential, a raw request body
or a raw file has no field to sit in. ProofObservation applies the same discipline to
what an outer sandbox watched, and it names its fields in explicit pairs rather than
reaching for them dynamically, because the product tree bans dynamic attribute access —
it defeats the AST scan that proves this tree cannot reach a shell, the network or a
credential.

_protected accepts a broker reference or a keyed commitment and refuses everything else;
where a credential is at stake it refuses the keyed commitment too, leaving the opaque
reference as the only shape. canonical_state_digest hashes a path→text map and reads no
filesystem, so a state comparison never becomes a way to open a file. Manifest
construction sorts effects and operations before freezing them, so two identical
declarations produce one digest; it requires a disclosure for outbound message.send and
forbids one otherwise; and it requires every ceiling to be a finite, non-negative
number.

Validation here is not admission. A manifest that passes every check has been admitted
to nothing, and this file deliberately offers no way to decide otherwise."""

from __future__ import annotations
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast
from .effects_grammar import (
    EFFECT_CLASSES,
    EffectError,
    OUTBOUND_EFFECTS,
    _PROOF_RUN_STATUSES,
    _RECEIPT_STATUSES,
    _broker_reference,
    _digest,
    _exact_keys,
    _freeze,
    _mapping,
    _relative_state_path,
    _strings,
    _text,
    _thaw,
    _timestamp,
)


__all__ = [
    "EFFECT_CLASSES",
    "EffectError",
    "EffectManifest",
    "OUTBOUND_EFFECTS",
    "ProofObservation",
    "_PROOF_RUN_STATUSES",
    "_RECEIPT_STATUSES",
    "_broker_reference",
    "_digest",
    "_exact_keys",
    "_freeze",
    "_mapping",
    "_relative_state_path",
    "_strings",
    "_text",
    "_thaw",
    "_timestamp",
    "canonical_state_digest",
]


def _keyed_commitment(value: object, field: str, domain: str) -> None:
    item = _mapping(value, field)
    _exact_keys(
        item, field, {"kind", "algorithm", "domain", "key_version", "commitment"}
    )
    if item["kind"] != "keyed_commitment":
        raise EffectError(f"{field} must be a domain-separated keyed commitment")
    if item["algorithm"] != "hmac-sha256":
        raise EffectError(f"{field}.algorithm must be hmac-sha256")
    if item["domain"] != domain:
        raise EffectError(f"{field}.domain must be {domain!r}")
    _text(item["key_version"], f"{field}.key_version")
    _digest(item["commitment"], f"{field}.commitment")


def _protected(
    value: object, field: str, domain: str, *, credential: bool = False
) -> None:
    item = _mapping(value, field)
    kind = item.get("kind")
    if kind == "broker_reference":
        _broker_reference(item, field)
        return
    if not credential and kind == "keyed_commitment":
        _keyed_commitment(item, field, domain)
        return
    if credential:
        raise EffectError(f"{field} must be an opaque broker reference")
    raise EffectError(f"{field} must be an opaque broker reference or keyed commitment")


def canonical_state_digest(files: Mapping[str, str]) -> str:
    """Canonical digest of a secret-free path→text map; no filesystem is read."""

    if not isinstance(files, Mapping):
        raise EffectError("state files must be an object")
    lines: list[str] = []
    seen: set[str] = set()
    for raw_path, content in files.items():
        path = _relative_state_path(str(raw_path), "state path")
        if path in seen:
            raise EffectError("state paths must not contain duplicates")
        if not isinstance(content, str):
            raise EffectError("state content must be a string")
        seen.add(path)
        payload = hashlib.sha256(content.encode("utf-8")).hexdigest()
        lines.append(f"{path}:{payload}")
    lines.sort()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _keyed_commitment_digest(value: object, field: str) -> str | None:
    item = _mapping(value, field)
    if item.get("kind") != "keyed_commitment":
        return None
    return _digest(item["commitment"], f"{field}.commitment")


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
    disclosure: str | None = None

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
        _protected(self.forward, "forward", "effect.manifest.forward")
        _protected(self.scope, "scope", "effect.manifest.scope")
        operations = tuple(sorted(_strings(self.operations, "operations")))
        effects = tuple(sorted(_strings(self.effects, "effects")))
        unknown = sorted(set(effects) - EFFECT_CLASSES)
        if unknown:
            raise EffectError(f"effects must use exact effect classes, got {unknown}")
        outbound = bool(set(effects) & OUTBOUND_EFFECTS)
        if outbound:
            if self.disclosure is None:
                raise EffectError(
                    "disclosure is required for outbound message.send effects"
                )
            object.__setattr__(
                self, "disclosure", _digest(self.disclosure, "disclosure")
            )
        elif self.disclosure is not None:
            raise EffectError(
                "disclosure is only permitted for outbound message.send effects"
            )

        for field, value in (
            ("inventory_snapshot", self.inventory_snapshot),
            ("gate_snapshot", self.gate_snapshot),
            ("law_snapshot", self.law_snapshot),
        ):
            snapshot = _mapping(value, field)
            _exact_keys(snapshot, field, {"digest"})
            _digest(snapshot["digest"], f"{field}.digest")
        _protected(
            self.authority_snapshot,
            "authority_snapshot",
            "effect.manifest.authority_snapshot",
        )
        _protected(self.start_state, "start_state", "effect.manifest.start_state")
        observer = _mapping(self.observer, "observer")
        _exact_keys(observer, "observer", {"id", "policy_digest"})
        _text(observer["id"], "observer.id")
        _digest(observer["policy_digest"], "observer.policy_digest")
        _protected(
            self.expected_state,
            "expected_state",
            "effect.manifest.expected_state",
        )
        reversal = _mapping(self.reversal, "reversal")
        _exact_keys(reversal, "reversal", {"kind", "name"})
        _text(reversal["kind"], "reversal.kind")
        _text(reversal["name"], "reversal.name")
        declared_residuals = tuple(
            sorted(
                _strings(
                    self.declared_residuals, "declared_residuals", allow_empty=True
                )
            )
        )
        ceilings = _mapping(self.ceilings, "ceilings")
        if not ceilings:
            raise EffectError("ceilings must not be empty")
        for name, ceiling in ceilings.items():
            _text(name, "ceilings key")
            if (
                not isinstance(ceiling, int | float)
                or isinstance(ceiling, bool)
                or (isinstance(ceiling, float) and not math.isfinite(ceiling))
                or ceiling < 0
            ):
                raise EffectError(
                    f"ceilings.{name} must be a finite non-negative number"
                )

        object.__setattr__(self, "adapter", _freeze(self.adapter))
        object.__setattr__(self, "forward", _freeze(self.forward))
        object.__setattr__(self, "scope", _freeze(self.scope))
        object.__setattr__(self, "operations", _freeze(operations))
        object.__setattr__(self, "effects", _freeze(effects))
        object.__setattr__(self, "inventory_snapshot", _freeze(self.inventory_snapshot))
        object.__setattr__(self, "gate_snapshot", _freeze(self.gate_snapshot))
        object.__setattr__(self, "authority_snapshot", _freeze(self.authority_snapshot))
        object.__setattr__(self, "law_snapshot", _freeze(self.law_snapshot))
        object.__setattr__(self, "start_state", _freeze(self.start_state))
        object.__setattr__(self, "observer", _freeze(self.observer))
        object.__setattr__(self, "expected_state", _freeze(self.expected_state))
        object.__setattr__(self, "reversal", _freeze(self.reversal))
        object.__setattr__(self, "declared_residuals", _freeze(declared_residuals))
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
        if self.disclosure is not None:
            record["disclosure"] = _thaw(self.disclosure)
        return record

    @classmethod
    def from_record(cls, value: object) -> "EffectManifest":
        record = _mapping(value, "manifest")
        optional_fields = {"parent_operation_id", "disclosure"}
        required = set(cls.__dataclass_fields__) - optional_fields
        allowed = (
            required,
            required | {"parent_operation_id"},
            required | {"disclosure"},
            required | optional_fields,
        )
        if set(record) not in allowed:
            raise EffectError("manifest has missing or unknown fields")
        return cls(**cast(Any, dict(record)))

    def canonical(self) -> str:
        return json.dumps(
            self.to_record(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    def binding(self) -> dict[str, object]:
        return {"kind": "inline", "value": self.to_record(), "digest": self.digest}


@dataclass(frozen=True)
class ProofObservation:
    """Independent outer-sandbox observations of one scratch proof run."""

    start_state_digest: str
    forward_state_digest: str
    end_state_digest: str
    enclosing_before_digest: str
    enclosing_after_digest: str
    expected_state_digest: str
    forward_status: str
    inverse_status: str
    sandbox_policy_digest: str
    verifier_policy_digest: str
    observed_verifier_policy_digest: str
    observer_log_digest: str
    escaped_attempts: Sequence[str]
    observed_residuals: Sequence[str]

    def __post_init__(self) -> None:
        # Named pairs rather than getattr: the product tree bans dynamic attribute access
        # because it defeats the AST scan that proves this tree cannot reach a shell, the
        # network or a credential. A lock with a benign exception is not a lock.
        for field, value in (
            ("start_state_digest", self.start_state_digest),
            ("forward_state_digest", self.forward_state_digest),
            ("end_state_digest", self.end_state_digest),
            ("enclosing_before_digest", self.enclosing_before_digest),
            ("enclosing_after_digest", self.enclosing_after_digest),
            ("expected_state_digest", self.expected_state_digest),
            ("sandbox_policy_digest", self.sandbox_policy_digest),
            ("verifier_policy_digest", self.verifier_policy_digest),
            ("observed_verifier_policy_digest", self.observed_verifier_policy_digest),
            ("observer_log_digest", self.observer_log_digest),
        ):
            object.__setattr__(self, field, _digest(value, field))
        for field, value in (
            ("forward_status", self.forward_status),
            ("inverse_status", self.inverse_status),
        ):
            status = _text(value, field)
            if status not in _PROOF_RUN_STATUSES:
                raise EffectError(
                    f"{field} must be one of {sorted(_PROOF_RUN_STATUSES)}"
                )
            object.__setattr__(self, field, status)
        object.__setattr__(
            self,
            "escaped_attempts",
            _strings(self.escaped_attempts, "escaped_attempts", allow_empty=True),
        )
        object.__setattr__(
            self,
            "observed_residuals",
            _strings(self.observed_residuals, "observed_residuals", allow_empty=True),
        )


def _receipt(data: Mapping[str, object]) -> None:
    expected = {
        "receipt_id",
        "intent_id",
        "manifest_digest",
        "status",
        "started_at",
        "ended_at",
        "provider_request",
        "provider_receipt",
        "request_commitment",
        "response_commitment",
        "content_commitment",
        "observed_consumption",
        "post_state",
        "observed_residuals",
        "child_operation_ids",
    }
    if "supersedes" in data:
        expected.add("supersedes")
    _exact_keys(data, "effect.receipt.data", expected)
    _text(data["receipt_id"], "effect.receipt.receipt_id")
    _text(data["intent_id"], "effect.receipt.intent_id")
    _digest(data["manifest_digest"], "effect.receipt.manifest_digest")
    if data["status"] not in _RECEIPT_STATUSES:
        raise EffectError(
            f"effect.receipt.status must be one of {sorted(_RECEIPT_STATUSES)}"
        )
    if _timestamp(data["ended_at"], "effect.receipt.ended_at") < _timestamp(
        data["started_at"], "effect.receipt.started_at"
    ):
        raise EffectError("effect.receipt.ended_at must not precede started_at")
    _protected(
        data["provider_request"],
        "effect.receipt.provider_request",
        "effect.receipt.provider_request",
    )
    _protected(
        data["provider_receipt"],
        "effect.receipt.provider_receipt",
        "effect.receipt.provider_receipt",
    )
    _keyed_commitment(
        data["request_commitment"],
        "effect.receipt.request_commitment",
        "effect.receipt.request",
    )
    _keyed_commitment(
        data["response_commitment"],
        "effect.receipt.response_commitment",
        "effect.receipt.response",
    )
    _keyed_commitment(
        data["content_commitment"],
        "effect.receipt.content_commitment",
        "effect.receipt.content",
    )
    consumption = _mapping(
        data["observed_consumption"], "effect.receipt.observed_consumption"
    )
    for name, amount in consumption.items():
        _text(name, "effect.receipt.observed_consumption key")
        if (
            not isinstance(amount, int | float)
            or isinstance(amount, bool)
            or (isinstance(amount, float) and not math.isfinite(amount))
            or amount < 0
        ):
            raise EffectError(
                f"effect.receipt.observed_consumption.{name} must be finite and non-negative"
            )
    _protected(
        data["post_state"], "effect.receipt.post_state", "effect.receipt.post_state"
    )
    _strings(
        data["observed_residuals"],
        "effect.receipt.observed_residuals",
        allow_empty=True,
    )
    _strings(
        data["child_operation_ids"],
        "effect.receipt.child_operation_ids",
        allow_empty=True,
    )
    if "supersedes" in data:
        _text(data["supersedes"], "effect.receipt.supersedes")

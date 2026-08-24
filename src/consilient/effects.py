"""Inert, canonical records for the typed effect boundary."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, cast

from .capabilities import CapabilityEntry, Gate


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

AdmissionClass = Literal[
    "observation",
    "contained_execution",
    "proof_operation",
    "material_choice",
    "recoverable_mutation",
    "protected_covered",
    "protected_uncovered",
    "capability_gap",
]
ADMISSION_CLASSES = frozenset(
    {
        "observation",
        "contained_execution",
        "proof_operation",
        "material_choice",
        "recoverable_mutation",
        "protected_covered",
        "protected_uncovered",
        "capability_gap",
    }
)

Disposition = Literal["execute", "reshape", "refuse", "escalate"]
ADMISSION_DISPOSITIONS = frozenset({"execute", "reshape", "refuse", "escalate"})

READ_ONLY_EFFECTS = frozenset({"data.read", "network.call"})
READ_ONLY_OPERATIONS = frozenset({"read", "fetch", "get", "head", "list"})
PLANNING_OPERATIONS = frozenset({"plan", "choose", "decide"})
PROOF_OPERATIONS = frozenset({"proof"})
PROTECTED_ESCALATION_EFFECTS = frozenset(
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
MUTATION_EFFECTS = frozenset(
    {
        "file.change",
        "system.change",
        "external.change",
        "data.read",
        "process.run",
        "network.call",
    }
)
OUTBOUND_EFFECTS = frozenset({"message.send"})
OUTBOUND_OPERATIONS = frozenset({"send_email", "send_sms"})


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


def _relative_state_path(path: str, field: str) -> str:
    posix = _text(path, field).replace("\\", "/")
    if posix.startswith("/") or (len(posix) >= 2 and posix[1] == ":"):
        raise EffectError(f"{field} must be a relative path")
    parts = [part for part in posix.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise EffectError(f"{field} must stay inside scope")
    return "/".join(parts)


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


_PROOF_RUN_STATUSES = frozenset({"succeeded", "failed", "not_run"})
RecoveryStatus = Literal["passed", "refused", "capability_gap"]
RECOVERY_STATUSES = frozenset({"passed", "refused", "capability_gap"})


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
        _protected(self.forward, "forward")
        _protected(self.scope, "scope")
        operations = _strings(self.operations, "operations")
        effects = _strings(self.effects, "effects")
        unknown = sorted(set(effects) - EFFECT_CLASSES)
        if unknown:
            raise EffectError(f"effects must use exact effect classes, got {unknown}")
        outbound = bool(set(effects) & OUTBOUND_EFFECTS) and bool(
            set(operations) & OUTBOUND_OPERATIONS
        )
        if outbound:
            if self.disclosure is None:
                raise EffectError("disclosure is required for outbound message.send effects")
            object.__setattr__(self, "disclosure", _digest(self.disclosure, "disclosure"))
        elif self.disclosure is not None:
            raise EffectError("disclosure is only permitted for outbound message.send effects")

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
        return json.dumps(self.to_record(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    def binding(self) -> dict[str, object]:
        return {"kind": "inline", "value": self.to_record(), "digest": self.digest}


@dataclass(frozen=True)
class AdmissionFacts:
    """Exogenous facts for pure admission derivation; never caller-supplied authority."""

    contained: bool = False
    is_proof_operation: bool = False
    is_material_choice: bool = False
    recovery_proof_passed: bool | None = None
    authority_standing: bool | None = None
    broker_confirms_observation: bool = False
    project_gates_open: bool = False
    caller_metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class AdmissionResult:
    admission: AdmissionClass
    disposition: Disposition
    reason: str


def _manifest_effects(manifest: EffectManifest) -> frozenset[str]:
    return frozenset(_strings(manifest.effects, "manifest.effects"))


def _manifest_operations(manifest: EffectManifest) -> frozenset[str]:
    return frozenset(_strings(manifest.operations, "manifest.operations"))


def _gate_expired(gate: Gate) -> bool:
    if gate.expires_at is None:
        return False
    parsed = datetime.fromisoformat(gate.expires_at)
    return parsed <= datetime.now(timezone.utc)


def _gate_matches_manifest(gate: Gate, manifest: EffectManifest) -> tuple[bool, str]:
    manifest_effects = _manifest_effects(manifest)
    manifest_operations = _manifest_operations(manifest)
    gate_effects = frozenset(gate.effect_classes)
    gate_operations = frozenset(gate.operations)
    if manifest_effects and not manifest_effects <= gate_effects:
        return False, "effect_class_mismatch"
    if manifest_operations and not manifest_operations <= gate_operations:
        return False, "operation_mismatch"
    return True, "exact_grant"


def _observation_predicate(manifest: EffectManifest) -> bool:
    effects = _manifest_effects(manifest)
    operations = _manifest_operations(manifest)
    if not effects:
        return False
    if not effects <= READ_ONLY_EFFECTS:
        return False
    if not operations <= READ_ONLY_OPERATIONS:
        return False
    return True


def _has_protected_effects(manifest: EffectManifest) -> bool:
    return bool(_manifest_effects(manifest) & PROTECTED_ESCALATION_EFFECTS)


def _has_mutation_effects(manifest: EffectManifest) -> bool:
    effects = _manifest_effects(manifest)
    return bool(effects & MUTATION_EFFECTS) and not effects <= READ_ONLY_EFFECTS


def _planning_predicate(manifest: EffectManifest) -> bool:
    operations = _manifest_operations(manifest)
    effects = _manifest_effects(manifest)
    return (
        bool(operations)
        and operations <= PLANNING_OPERATIONS
        and bool(effects)
        and effects <= READ_ONLY_EFFECTS
    )


def _proof_predicate(manifest: EffectManifest) -> bool:
    operations = _manifest_operations(manifest)
    return bool(operations) and operations <= PROOF_OPERATIONS and not _has_protected_effects(manifest)


def _classify_admission(
    manifest: EffectManifest,
    facts: AdmissionFacts,
) -> AdmissionClass:
    if facts.is_proof_operation and _proof_predicate(manifest) and facts.contained:
        return "proof_operation"
    if facts.is_material_choice and _planning_predicate(manifest):
        return "material_choice"
    if _observation_predicate(manifest) and facts.broker_confirms_observation:
        return "observation"
    effects = _manifest_effects(manifest)
    if "process.run" in effects:
        return "contained_execution" if facts.contained else "capability_gap"
    if _has_protected_effects(manifest):
        if facts.authority_standing:
            return "protected_covered"
        return "protected_uncovered"
    if _has_mutation_effects(manifest):
        return "recoverable_mutation"
    return "capability_gap"


def _disposition_for(
    admission: AdmissionClass,
    gate_reason: str,
    facts: AdmissionFacts,
) -> tuple[Disposition, str]:
    if admission == "capability_gap":
        return "refuse", gate_reason
    if admission == "protected_uncovered":
        return "escalate", "protected_class_without_standing_authority"
    if admission == "recoverable_mutation":
        if facts.recovery_proof_passed is True:
            return "execute", gate_reason
        if facts.recovery_proof_passed is False:
            return "reshape", "recovery_proof_failed"
        return "refuse", "recovery_proof_missing"
    if admission == "contained_execution" and not facts.contained:
        return "refuse", "process_not_contained"
    if admission in {"proof_operation", "material_choice", "observation", "contained_execution", "protected_covered"}:
        return "execute", gate_reason
    return "refuse", "unhandled_admission_class"


def derive_admission(
    manifest: EffectManifest,
    capability: CapabilityEntry,
    facts: AdmissionFacts = AdmissionFacts(),
) -> AdmissionResult:
    """Derive one fail-closed admission class and disposition from manifest and gate facts."""

    if facts.caller_metadata is not None:
        # Caller-supplied principal metadata is recorded, not authenticated admission.
        pass

    if not capability.available:
        return AdmissionResult("capability_gap", "refuse", "capability_unavailable")

    gate = capability.gate
    if gate.state != "admitted":
        return AdmissionResult("capability_gap", "refuse", gate.reason)

    if _gate_expired(gate):
        return AdmissionResult("capability_gap", "refuse", "grant_expired")

    matches, match_reason = _gate_matches_manifest(gate, manifest)
    if not matches:
        return AdmissionResult("capability_gap", "refuse", match_reason)

    admission = _classify_admission(manifest, facts)
    if admission == "observation" and not facts.broker_confirms_observation:
        return AdmissionResult("capability_gap", "refuse", "observation_not_confirmed")
    if admission == "capability_gap":
        effects = _manifest_effects(manifest)
        if "process.run" in effects and not facts.contained:
            return AdmissionResult("capability_gap", "refuse", "process_not_contained")
        return AdmissionResult("capability_gap", "refuse", match_reason)

    disposition, reason = _disposition_for(admission, match_reason, facts)
    return AdmissionResult(admission, disposition, reason)


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
        for field in (
            "start_state_digest",
            "forward_state_digest",
            "end_state_digest",
            "enclosing_before_digest",
            "enclosing_after_digest",
            "expected_state_digest",
            "sandbox_policy_digest",
            "verifier_policy_digest",
            "observed_verifier_policy_digest",
            "observer_log_digest",
        ):
            object.__setattr__(self, field, _digest(getattr(self, field), field))
        for field in ("forward_status", "inverse_status"):
            status = _text(getattr(self, field), field)
            if status not in _PROOF_RUN_STATUSES:
                raise EffectError(f"{field} must be one of {sorted(_PROOF_RUN_STATUSES)}")
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


@dataclass(frozen=True)
class RecoveryProof:
    """Bound result of one isolated recovery proof, reusable only when passed."""

    proof_operation_id: str
    proof_decision_id: str
    proof_intent_id: str
    live_operation_id: str
    manifest: EffectManifest
    observation: ProofObservation
    status: RecoveryStatus
    reason: str
    digest: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, EffectManifest):
            raise EffectError("recovery proof must bind an EffectManifest")
        if not isinstance(self.observation, ProofObservation):
            raise EffectError("recovery proof must bind a ProofObservation")
        if self.status not in RECOVERY_STATUSES:
            raise EffectError("recovery proof status is unknown")
        _text(self.reason, "reason")
        if self.status == "passed":
            if self.digest is None:
                raise EffectError("a passing recovery proof must carry a digest")
            _digest(self.digest, "digest")
        elif self.digest is not None:
            raise EffectError("only a passing recovery proof may carry a digest")


def _proof_binding_digest(
    *,
    proof_operation_id: str,
    proof_decision_id: str,
    proof_intent_id: str,
    live_operation_id: str,
    manifest: EffectManifest,
    observation: ProofObservation,
) -> str:
    payload = {
        "end_state_digest": observation.end_state_digest,
        "enclosing_after_digest": observation.enclosing_after_digest,
        "forward_state_digest": observation.forward_state_digest,
        "live_operation_id": live_operation_id,
        "manifest_digest": manifest.digest,
        "observer_log_digest": observation.observer_log_digest,
        "proof_decision_id": proof_decision_id,
        "proof_intent_id": proof_intent_id,
        "proof_operation_id": proof_operation_id,
        "residuals": list(observation.observed_residuals),
        "sandbox_policy_digest": observation.sandbox_policy_digest,
        "start_state_digest": observation.start_state_digest,
        "verifier_policy_digest": observation.verifier_policy_digest,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def evaluate_recovery_proof(
    *,
    proof_operation_id: str,
    proof_decision_id: str,
    proof_intent_id: str,
    live_operation_id: str,
    manifest: EffectManifest,
    observation: ProofObservation,
) -> RecoveryProof:
    """Classify one executed scratch proof. Confidence and exit codes are not inputs."""

    def finish(status: RecoveryStatus, reason: str, digest: str | None = None) -> RecoveryProof:
        return RecoveryProof(
            proof_operation_id=proof_operation_id,
            proof_decision_id=proof_decision_id,
            proof_intent_id=proof_intent_id,
            live_operation_id=live_operation_id,
            manifest=manifest,
            observation=observation,
            status=status,
            reason=reason,
            digest=digest,
        )

    identities = (
        proof_operation_id,
        proof_decision_id,
        proof_intent_id,
        live_operation_id,
    )
    if any(not isinstance(item, str) or not item.strip() for item in identities):
        return finish("refused", "proof_identities_missing")
    if live_operation_id == proof_operation_id:
        return finish("refused", "live_operation_not_separate")
    if "process.run" in _manifest_effects(manifest):
        return finish("capability_gap", "process_run_not_restorable")

    escaped = tuple(observation.escaped_attempts)
    if escaped:
        if set(escaped) <= {"escaped_child"}:
            return finish("refused", "escaped_child")
        return finish("refused", "escaped_protected_effect")
    if observation.observed_verifier_policy_digest != observation.verifier_policy_digest:
        return finish("refused", "verifier_policy_changed")

    start_commitment = _keyed_commitment_digest(manifest.start_state, "start_state")
    if start_commitment is None:
        return finish("capability_gap", "start_state_not_comparable")
    if start_commitment != observation.start_state_digest:
        return finish("refused", "start_state_mismatch")

    if observation.forward_status == "not_run" or observation.inverse_status == "not_run":
        return finish("refused", "proof_not_executed")
    if observation.forward_status != "succeeded":
        return finish("refused", "forward_failed")

    expected_commitment = _keyed_commitment_digest(manifest.expected_state, "expected_state")
    if expected_commitment is None:
        return finish("capability_gap", "expected_state_not_comparable")
    if expected_commitment != observation.expected_state_digest:
        return finish("refused", "expected_state_mismatch")
    if observation.forward_state_digest != observation.expected_state_digest:
        return finish("refused", "expected_state_mismatch")
    if _has_mutation_effects(manifest) and observation.forward_state_digest == observation.start_state_digest:
        return finish("refused", "forward_did_not_mutate")
    if observation.inverse_status != "succeeded" or observation.end_state_digest != observation.start_state_digest:
        return finish("refused", "inverse_failed")
    if observation.enclosing_after_digest != observation.enclosing_before_digest:
        return finish("refused", "enclosing_scope_mismatch")

    declared = set(_strings(manifest.declared_residuals, "declared_residuals", allow_empty=True))
    observed = set(observation.observed_residuals)
    if not observed <= declared:
        return finish("refused", "undeclared_residual")

    digest = _proof_binding_digest(
        proof_operation_id=proof_operation_id,
        proof_decision_id=proof_decision_id,
        proof_intent_id=proof_intent_id,
        live_operation_id=live_operation_id,
        manifest=manifest,
        observation=observation,
    )
    return finish("passed", "restored", digest)


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
    disposition = _text(data["disposition"], "effect.intent.disposition")
    if disposition not in ADMISSION_DISPOSITIONS and disposition != "refused":
        raise EffectError(
            f"effect.intent.disposition must be one of {sorted(ADMISSION_DISPOSITIONS)} or refused"
        )
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

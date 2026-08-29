"""The closed vocabulary and the field grammar every effect record is written in.

Nothing here knows what an effect does. These are the names — the effect classes, the
admission classes, the dispositions and the two event kinds — together with the checks
that decide whether a value may be called a digest, an opaque broker reference, a
relative path that stays inside scope, or a list of distinct non-empty strings. Every
check either returns the value unchanged or raises EffectError. There is no repair path
and no default, because a record that cannot be read exactly is not a record.

The vocabularies are frozen sets rather than open strings so that a class nobody
declared cannot be smuggled in by spelling, and _FrozenMapping with _freeze and _thaw
exist so a validated record cannot be edited after the fact by whoever is holding it.
CONTAINED_EXECUTION_EFFECTS states what a contained execution may declare and still be
classified as merely that: read-only plus the run itself. Anything beyond is a mutation
or a protected class and must be judged on that footing rather than laundered through
"process.run".

receipt_chain_validator refuses chains rather than mending them — a duplicate intent or
receipt identifier, a receipt that precedes its intent, a manifest digest disagreeing
with the intent it claims, a second head for one intent, and any resolution of an
unknown head to something that is not final."""

from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, cast
from .capabilities import (
    PROTECTED_EFFECT_CLASSES,
    Gate,
)

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

_OPAQUE_REFERENCE = re.compile(r"^broker://effects/[0-9a-f]{64}$")

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

# What a CONTAINED execution may declare and still be classified as merely that: read-only
# plus the run itself. Anything beyond is a mutation or a protected class and must be judged
# on that footing rather than laundered through "process.run".
CONTAINED_EXECUTION_EFFECTS = READ_ONLY_EFFECTS | frozenset({"process.run"})

READ_ONLY_OPERATIONS = frozenset({"read", "fetch", "get", "head", "list"})

PROOF_OPERATIONS = frozenset({"proof"})

PROTECTED_ESCALATION_EFFECTS = PROTECTED_EFFECT_CLASSES

MUTATION_EFFECTS = frozenset(
    {
        "file.change",
        "system.change",
        "external.change",
        "process.run",
    }
)

OUTBOUND_EFFECTS = frozenset({"message.send"})


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
    reference = _text(item["reference"], f"{field}.reference")
    if _OPAQUE_REFERENCE.fullmatch(reference) is None:
        raise EffectError(f"{field} must be an opaque broker reference")


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return _FrozenMapping(
            tuple((str(key), _freeze(item)) for key, item in value.items())
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _strings(
    value: object, field: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
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


_PROOF_RUN_STATUSES = frozenset({"succeeded", "failed", "not_run"})

RecoveryStatus = Literal["passed", "refused", "capability_gap"]

RECOVERY_STATUSES = frozenset({"passed", "refused", "capability_gap"})


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
    requested_scope: tuple[str, ...] = ("workspace",)


@dataclass(frozen=True)
class AdmissionResult:
    admission: AdmissionClass
    disposition: Disposition
    reason: str


def _gate_expired(gate: Gate) -> bool:
    if gate.expires_at is None:
        return False
    parsed = datetime.fromisoformat(gate.expires_at)
    return parsed <= datetime.now(timezone.utc)


def _protected_authority_covers(gate: Gate, facts: AdmissionFacts) -> bool:
    return (
        gate.grant_kind == "principal_authority"
        and gate.authority_event is not None
        and facts.authority_standing is True
    )


def _disposition_for(
    admission: AdmissionClass,
    gate_reason: str,
    facts: AdmissionFacts,
) -> tuple[Disposition, str]:
    if admission == "protected_uncovered":
        return "escalate", "protected_class_without_standing_authority"
    if admission == "recoverable_mutation":
        if facts.recovery_proof_passed is True:
            return "execute", gate_reason
        if facts.recovery_proof_passed is False:
            return "reshape", "recovery_proof_failed"
        return "refuse", "recovery_proof_missing"
    return "execute", gate_reason


def _timestamp(value: object, field: str) -> datetime:
    value = _text(value, field)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EffectError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EffectError(f"{field} must carry an explicit offset")
    return parsed


def _admitted_manifest_digest(
    manifest: Any,
    operation_ids: set[str],
    manifest_digests: set[str],
) -> Any:
    """Admit one intent's manifest, or refuse it, and return the digest to bind to the intent.

    A fresh `intent_id` is not enough to make an intent new. Three ways the chain can still be a
    replay or an unprovable claim, all refused here (unit A01):

      * a manifest digest already seen -- the same authorisation presented twice;
      * a REFERENCE manifest, which names an operation held elsewhere, so the chain cannot prove
        which operation it authorises. Accepting one would let two distinct effects share an
        identity this log never saw;
      * an inline operation_id already seen -- one operation admitted under two intents.

    Extracted from `receipt_chain_validator` rather than inlined: inlining took that function to
    51 statements against the per-function ratchet ADR-0111 added, which refused the commit.
    """
    manifest_digest = manifest["digest"]
    if manifest_digest in manifest_digests:
        raise EffectError(
            f"receipt chain has duplicate manifest digest {manifest_digest!r}"
        )
    manifest_digests.add(manifest_digest)
    if manifest["kind"] == "reference":
        raise EffectError(
            "receipt chain operation identity cannot be proved from reference manifest"
        )
    operation_id = manifest["value"]["operation_id"]
    if operation_id in operation_ids:
        raise EffectError(f"receipt chain has duplicate operation_id {operation_id!r}")
    operation_ids.add(operation_id)
    return manifest_digest


def receipt_chain_validator(
    prefix: tuple[Any, ...],
    rejections: tuple[Any, ...],
    candidates: tuple[dict[str, Any], ...],
) -> None:
    """Purely refuse unreconstructable, unordered, duplicate, and forked effect chains.

    Only a rejection that was itself an effect-chain line (`event_kind` of
    `EFFECT_INTENT` or `EFFECT_RECEIPT`) can make the chain unreconstructable. [measured]
    A rejected `note.made` line -- or any other rejection with no `event_kind`, such as one
    from a line that was not even valid JSON -- shares a log directory with the chain but is
    not part of it, and previously blocked every write-ahead intent in that directory.
    """
    effect_rejections = [
        rejection
        for rejection in rejections
        if rejection.event_kind in (EFFECT_INTENT, EFFECT_RECEIPT)
    ]
    if effect_rejections:
        raise EffectError(
            "receipt chain cannot be reconstructed with rejected history lines"
        )
    intents: dict[str, str] = {}
    receipt_ids: set[str] = set()
    heads: dict[str, tuple[str, str]] = {}
    operation_ids: set[str] = set()
    manifest_digests: set[str] = set()
    for item in (*prefix, *candidates):
        raw = item if isinstance(item, Mapping) else item.raw
        if raw.get("event") == EFFECT_INTENT:
            intent_id = raw["data"]["intent_id"]
            if intent_id in intents:
                raise EffectError(
                    f"receipt chain has duplicate intent_id {intent_id!r}"
                )
            intents[intent_id] = _admitted_manifest_digest(
                raw["data"]["manifest"], operation_ids, manifest_digests
            )
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
            raise EffectError(
                f"receipt chain receipt {receipt_id!r} precedes its intent"
            )
        if data["manifest_digest"] != intents[intent_id]:
            raise EffectError("receipt manifest digest does not match its intent")
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
            raise EffectError(
                "receipt chain may resolve unknown only to a final status"
            )
        heads[intent_id] = (receipt_id, data["status"])


DECISION_EVENT = "decision.autonomous"

PROPOSAL_EVENT = "action.proposal"

AUTHORITY_EVENT = "authority.granted"

OUTCOME_EVENT = "attempt.outcome"

_ADMISSION_HANDLE_DOMAIN = "effect.admission.handle.v1"


@dataclass(frozen=True)
class EffectAdmissionRefusal:
    reason: str


@dataclass(frozen=True)
class PreparedEffectAdmission:
    """Pure admission plan: intent payload and opaque single-use handle metadata."""

    intent_id: str
    receipt_id: str
    intent_data: dict[str, object]
    handle_token: str
    operation_id: str
    manifest_digest: str


def _raw_event(item: object) -> Mapping[str, object] | None:
    if isinstance(item, Mapping):
        return cast(Mapping[str, object], item)
    raw = cast(Any, item).raw if hasattr(item, "raw") else None
    return cast(Mapping[str, object], raw) if isinstance(raw, dict) else None


def _planning_record(event: Mapping[str, object]) -> Mapping[str, object] | None:
    kind = event.get("event")
    data = event.get("data")
    if not isinstance(data, Mapping):
        return None
    if kind == PROPOSAL_EVENT:
        planning = data.get("planning")
        return planning if isinstance(planning, Mapping) else None
    if kind == DECISION_EVENT:
        markers = {
            "decision_id",
            "operation_id",
            "ticket",
            "owner",
            "actor",
            "record_level",
            "decision",
            "reasoning",
            "falsifier",
            "reversal",
            "alternatives",
            "evidence_refs",
            "acceptance_contract_digest",
            "protocol",
            "binding",
        }
        if markers & set(data):
            return data
    return None


def _operation_intent_ids(prefix: Sequence[object]) -> set[str]:
    operations: set[str] = set()
    for item in prefix:
        raw = _raw_event(item)
        if raw is None or raw.get("event") != EFFECT_INTENT:
            continue
        data = raw.get("data")
        if not isinstance(data, Mapping):
            continue
        manifest = data.get("manifest")
        if not isinstance(manifest, Mapping):
            continue
        if manifest.get("kind") == "inline" and isinstance(
            manifest.get("value"), Mapping
        ):
            operation_id = manifest["value"].get("operation_id")
            if isinstance(operation_id, str) and operation_id.strip():
                operations.add(operation_id)
    return operations


def _binding_manifest_digest(binding: Mapping[str, object]) -> str | None:
    digest = binding.get("effect_manifest_digest")
    if isinstance(digest, str) and len(digest) == 64:
        return digest
    return None


def _admission_handle_token(intent_id: str, manifest_digest: str) -> str:
    payload = json.dumps(
        {
            "domain": _ADMISSION_HANDLE_DOMAIN,
            "intent_id": intent_id,
            "manifest_digest": manifest_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

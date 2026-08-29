"""Captured records, and the chains everything else has to stay in.

A record.captured event is content-addressed and private: it names the digest of what
was captured rather than carrying the content itself, and its correction edges resolve
against the locked accepted prefix so that a correction cannot point at a record that is
absent, or at itself (M01). A versioned capability is held to the same exactness at the
writer (M04).

The remaining validators police order rather than shape. An effect receipt must continue
the chain it says it continues. A delivery claim must follow the estimate it settles
instead of preceding it. An estimate transition must be a revision of what actually
stood before. `TransitionValidator` — the signature they all share — is defined here: a
pure function handed the accepted prefix, the rejections exactly as they stand under the
per-log lock, and the validated candidates, which refuses by raising and can reach for
nothing else. Purity is the point; a validator that could read the world would make the
same log validate differently on two machines.

`rejection_digest` fingerprints the exact quarantined lines without binding to an
absolute path, so the same quarantine compares equal in a clone. A small cache keyed on
the trajectory's fingerprint keeps a whole-directory read from being repeated while
nothing has moved."""

from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import cast
from . import effects
from .events_vocabulary import (
    CAPABILITY_KIND_ALIASES,
    CAPABILITY_VERSIONED_FIELDS,
    RECORD_CAPTURED_FIELDS,
)

from .events_digests import (
    _delivery_estimates_by_id,
    _plan_for_estimate,
)

from .events_durability import (
    Event,
    _record_timestamp,
)

from .events_fields import (
    _check_uuid4,
    canonical,
)

from .events_kinds import (
    CAPABILITY_VERSIONED_KIND,
    DELIVERY_ESTIMATE_KIND,
    EventError,
    EventPayload,
    RECORD_CAPTURED_KIND,
    RECORD_KIND_ALIASES,
)

from .events_protocol import (
    derive_delivery_estimate,
)

from .events_references import (
    Rejection,
    _check_event_reference,
    resolve_reference,
)

from .events_versioning import (
    CapabilityManifest,
)


__all__ = [
    "CAPABILITY_KIND_ALIASES",
    "CAPABILITY_VERSIONED_FIELDS",
    "CAPABILITY_VERSIONED_KIND",
    "CapabilityManifest",
    "DELIVERY_ESTIMATE_KIND",
    "Event",
    "EventError",
    "EventPayload",
    "RECORD_CAPTURED_FIELDS",
    "RECORD_CAPTURED_KIND",
    "RECORD_KIND_ALIASES",
    "Rejection",
    "TransitionValidator",
    "_check_event_reference",
    "_check_uuid4",
    "_delivery_estimates_by_id",
    "_plan_for_estimate",
    "_record_timestamp",
    "canonical",
    "derive_delivery_estimate",
    "rejection_digest",
    "resolve_reference",
]

# A transition validator is pure: it receives the accepted prefix and the
# rejections exactly as they stand under the per-log lock, plus the validated
# candidates, and refuses by raising EventError. It performs no I/O of its own.
TransitionValidator = Callable[
    [tuple[Event, ...], tuple[Rejection, ...], tuple[EventPayload, ...]], None
]


def _check_record_contract(event: EventPayload) -> None:
    """M01: one exact, private, content-addressed capture event contract."""
    kind = event["event"]
    if kind != RECORD_CAPTURED_KIND:
        if kind in RECORD_KIND_ALIASES or kind.startswith("record."):
            raise EventError(
                f"record event kind must be {RECORD_CAPTURED_KIND!r}; aliases are not accepted"
            )
        return

    data = event["data"]
    actual = set(data)
    if actual != RECORD_CAPTURED_FIELDS:
        missing = sorted(RECORD_CAPTURED_FIELDS - actual)
        unexpected = sorted(actual - RECORD_CAPTURED_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{RECORD_CAPTURED_KIND} body fields are fixed: {'; '.join(detail)}"
        )

    _check_uuid4(data["record_id"], "record.captured record_id")
    digest = data["digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} digest must be 64 lower-case hex characters"
        )
    byte_count = data["byte_count"]
    if (
        not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 0
    ):
        raise EventError(
            f"{RECORD_CAPTURED_KIND} byte_count must be a non-negative integer"
        )

    media_type = data["media_type"]
    if (
        not isinstance(media_type, str)
        or re.fullmatch(r"[^\s/]+/[^\s/]+", media_type) is None
    ):
        raise EventError(
            f"{RECORD_CAPTURED_KIND} media_type must be one canonical type/subtype string"
        )

    locator = data["object_locator"]
    expected_locator = f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    if locator != expected_locator:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} object_locator must be the canonical repository-relative "
            f"SHA-256 locator {expected_locator!r}"
        )

    source = data["source"]
    if (
        not isinstance(source, str)
        or not source
        or source != source.strip()
        or source.startswith("/")
        or re.match(r"^[A-Za-z]:", source)
        or "\\" in source
        or any(part in {"", ".", ".."} for part in source.split("/"))
    ):
        raise EventError(
            f"{RECORD_CAPTURED_KIND} source must be one canonical repository-relative path"
        )

    for field in ("consent_purpose", "retention_class"):
        value = data[field]
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise EventError(
                f"{RECORD_CAPTURED_KIND} must carry canonical non-empty {field} metadata"
            )

    valid_time = data["valid_time"]
    if not isinstance(valid_time, dict) or set(valid_time) != {"from", "to"}:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} valid_time must contain exactly 'from' and 'to'"
        )
    valid_from = _record_timestamp(valid_time["from"], "valid_time.from")
    valid_to_raw = valid_time["to"]
    if valid_to_raw is not None:
        valid_to = _record_timestamp(valid_to_raw, "valid_time.to")
        if valid_to < valid_from:
            raise EventError(
                f"{RECORD_CAPTURED_KIND} valid_time.to cannot precede valid_time.from"
            )

    for relation in ("supersedes", "invalidates"):
        references = data[relation]
        if not isinstance(references, list):
            raise EventError(f"{RECORD_CAPTURED_KIND} {relation} must be a list")
        for reference in references:
            _check_record_reference(reference, relation)


def _check_record_reference(reference: object, relation: str) -> None:
    _check_event_reference(
        reference, RECORD_CAPTURED_KIND, relation, RECORD_CAPTURED_KIND
    )


def _check_capability_versioned_contract(event: EventPayload) -> None:
    """M04: one exact capability.versioned contract at the F02/F03 writer."""
    kind = event["event"]
    if kind != CAPABILITY_VERSIONED_KIND:
        if kind in CAPABILITY_KIND_ALIASES:
            raise EventError(
                f"capability event kind must be {CAPABILITY_VERSIONED_KIND!r}; aliases are not accepted"
            )
        return

    data = event["data"]
    actual = set(data)
    if actual != CAPABILITY_VERSIONED_FIELDS:
        missing = sorted(CAPABILITY_VERSIONED_FIELDS - actual)
        unexpected = sorted(actual - CAPABILITY_VERSIONED_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{CAPABILITY_VERSIONED_KIND} body fields are fixed: {'; '.join(detail)}"
        )

    try:
        CapabilityManifest.from_mapping(data)
    except EventError as exc:
        raise EventError(f"{CAPABILITY_VERSIONED_KIND} {exc}") from exc

    _check_event_reference(
        data["source_object"],
        CAPABILITY_VERSIONED_KIND,
        "source_object",
        RECORD_CAPTURED_KIND,
    )
    duplicate_of = data["duplicate_of"]
    supersedes = data["supersedes"]
    if duplicate_of is not None:
        _check_event_reference(
            duplicate_of,
            CAPABILITY_VERSIONED_KIND,
            "duplicate_of",
            CAPABILITY_VERSIONED_KIND,
        )
    if supersedes is not None:
        _check_event_reference(
            supersedes,
            CAPABILITY_VERSIONED_KIND,
            "supersedes",
            CAPABILITY_VERSIONED_KIND,
        )
    if duplicate_of is not None and supersedes is not None:
        raise EventError(
            f"{CAPABILITY_VERSIONED_KIND} duplicate_of and supersedes cannot both be set"
        )
    event_id = event.get("event_id")
    for relation in ("duplicate_of", "supersedes", "source_object"):
        reference = data[relation]
        if isinstance(reference, dict) and reference.get("event_id") == event_id:
            raise EventError(
                f"{CAPABILITY_VERSIONED_KIND} {relation} cannot reference itself"
            )


def _validate_effect_receipt_chain(
    prefix: tuple[Event, ...],
    rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    try:
        effects.receipt_chain_validator(prefix, rejections, candidates)
    except effects.EffectError as exc:
        raise EventError(str(exc)) from exc


def _validate_record_relations(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    """Resolve correction edges against the locked, accepted earlier prefix."""
    for candidate in candidates:
        if candidate["event"] != RECORD_CAPTURED_KIND:
            continue
        data = candidate["data"]
        for relation in ("supersedes", "invalidates"):
            for reference in data[relation]:
                if reference["event_id"] == candidate["event_id"]:
                    raise EventError(
                        f"{RECORD_CAPTURED_KIND} {relation} cannot reference itself"
                    )
                try:
                    resolve_reference(reference, prefix)
                except EventError as exc:
                    raise EventError(
                        f"{RECORD_CAPTURED_KIND} {relation} must reference an exact earlier "
                        f"record.captured event: {exc}"
                    ) from exc


_READ_ALL_CACHE: dict[str, tuple[object, list[Event], list[Rejection]]] = {}


def rejection_digest(rejected: list[Rejection]) -> str:
    """Fingerprint the exact quarantined lines without binding to an absolute clone path."""
    rows = (
        json.dumps(
            (Path(item.path).name, item.line, item.reason, item.content_digest),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        for item in rejected
    )
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def _validate_delivery_estimate_transition(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    tips = _delivery_estimates_by_id(prefix)
    rev0: dict[str, dict[str, object]] = {}
    for item in prefix:
        if item.kind != DELIVERY_ESTIMATE_KIND:
            continue
        data = item.data
        if data.get("revision") == 0:
            rev0[cast(str, data["delivery_id"])] = data

    for candidate in candidates:
        if candidate["event"] != DELIVERY_ESTIMATE_KIND:
            continue
        data = candidate["data"]
        delivery_id = cast(str, data["delivery_id"])
        revision = cast(int, data["revision"])
        plan_digest = cast(str, data["plan_digest"])
        plan = _plan_for_estimate(prefix, plan_digest)
        if plan is None:
            raise EventError(
                "delivery.estimate must reference a matching organisation.plan.frozen digest"
            )

        if revision == 0:
            if delivery_id in rev0:
                raise EventError("delivery.estimate revision zero is append-only")
            derived = derive_delivery_estimate(
                prefix,
                plan=plan,
                delivery_id=delivery_id,
                issued_at=datetime.fromisoformat(cast(str, data["issued_at"])),
                cohort_key=cast(dict[str, str], data["cohort_key"]),
                resource_snapshot_digest=cast(str, data["resource_snapshot_digest"]),
                checkpoint_interval_s=cast(int, data["checkpoint_interval_s"]),
                recovery_allowance_s=cast(int, data["recovery_allowance_s"]),
                not_included=cast(list[str], data["not_included"]),
            )
            if data["analogue_ids"] != derived["analogue_ids"]:
                raise EventError(
                    "outcome-aware cohort selection is refused; analogue_ids must list every "
                    "cohort-matching outcome"
                )
            continue

        predecessor_id = cast(str, data["predecessor_estimate_id"])
        tip = tips.get(delivery_id)
        original = rev0.get(delivery_id)
        if tip is None or original is None:
            raise EventError(
                "delivery.estimate revision zero must exist before reforecast"
            )
        if tip.get("estimate_id") != predecessor_id:
            raise EventError(
                "predecessor_estimate_id must reference the latest estimate"
            )
        if data.get("original_estimate_id") != original.get("estimate_id"):
            raise EventError("original_estimate_id must reference revision zero")

        prior_latest = datetime.fromisoformat(cast(str, tip["latest_at"]))
        issued = datetime.fromisoformat(cast(str, data["issued_at"]))
        if issued > prior_latest:
            raise EventError(
                "delivery.estimate reforecast must be pre-breach; issued_at exceeds prior latest_at"
            )
        new_latest = datetime.fromisoformat(cast(str, data["latest_at"]))
        if new_latest <= prior_latest:
            raise EventError("reforecast must widen or move the delivery window upward")
        tips[delivery_id] = data


def _validate_delivery_claim_ordering(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    rev0 = {
        cast(str, event.data["delivery_id"]): event.data
        for event in prefix
        if event.kind == DELIVERY_ESTIMATE_KIND and event.data.get("revision") == 0
    }
    for candidate in candidates:
        if candidate["event"] != "work_item.opened":
            continue
        data = candidate["data"]
        delivery_id = data.get("delivery_id")
        if not isinstance(delivery_id, str):
            continue
        estimate = rev0.get(delivery_id)
        if estimate is None:
            raise EventError(
                "delivery.estimate revision zero must be durable before a delivery claim"
            )
        for field in ("commitment_digest", "plan_digest"):
            if data.get(field) != estimate.get(field):
                raise EventError(
                    f"delivery claim {field} must match delivery.estimate revision zero"
                )

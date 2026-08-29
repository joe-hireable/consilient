"""Turning one untyped JSON value into a checked one, or refusing it.

Everything arriving at this boundary is `Any`, and these are the coercions that narrow
it: a 64-character hex digest, a UUIDv4 in one spelling, a canonical token, a
non-negative integer, a timestamp, a piece of decision or estimate text that may not be
blank, a provenance tag drawn from the project's own evidence classes, and a disposition
that must be stated explicitly rather than inferred from an absent field. Each returns
the narrowed value or raises, so no caller above has to wonder whether a field was
checked; if it came back, it was.

`canonical` belongs with them — one event, one line, stable key order — so that a replay
hash computed here is the hash computed anywhere else. Beside it are the unions of
related kinds that several contracts read together, and the two derived readings that
need no more than a field: the nearest-rank percentile of a set of durations, and the
classification of a learned-state procedure into a mutation class, or into nothing at
all when it is not a model change.

The file holds no rule about which kinds carry which fields. It only knows what a
well-formed value of each type looks like.
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from .events_vocabulary import (
    ACQUISITION_CHANNELS,
    BROWSER_RETAINED_EVIDENCE,
    PROTECTED_DECISION_CLASSES,
    _outcome_is_censored,
)

from .events_durability import (
    _check_derivation_roots,
)

from .events_kinds import (
    ACQUISITION_SOURCE_STATUSES,
    ACQUISITION_STANCES,
    ACTIVATION_REFUSED_KIND,
    CONSENT_GRANTED,
    CONSENT_WITHDRAWN,
    EventError,
    EventPayload,
    FEEDBACK_ANSWERED_KIND,
    FEEDBACK_ASKED_KIND,
    FEEDBACK_DECLINED_KIND,
    IMPACT_CONTRACT_KIND,
    KNOWLEDGE_RETRIEVED_KIND,
    OUTCOME_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    PROVENANCE,
    TS,
    USAGE_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    VERIFICATION_OUTCOME_KIND,
    _DATA_DRIVEN_PROCEDURES,
    _KNOWLEDGE_ACQUISITION_CHANNELS,
    _NON_DATA_DRIVEN_PROCEDURES,
    _RETRIEVAL_PROCEDURES,
    _UNKNOWN_DISPOSITIONS,
    _VERIFICATION_ACQUISITION_CHANNELS,
    _canonical_json,
)


__all__ = [
    "ACQUISITION_CHANNELS",
    "ACQUISITION_SOURCE_STATUSES",
    "ACQUISITION_STANCES",
    "ACTIVATION_REFUSED_KIND",
    "BROWSER_RETAINED_EVIDENCE",
    "CONSENT_GRANTED",
    "CONSENT_KINDS",
    "CONSENT_WITHDRAWN",
    "DELIVERY_OUTCOME_KINDS",
    "ESCALATION_CLASSES",
    "EventError",
    "EventPayload",
    "FEEDBACK_ANSWERED_KIND",
    "FEEDBACK_ASKED_KIND",
    "FEEDBACK_DECLINED_KIND",
    "FEEDBACK_KINDS",
    "IMPACT_CONTRACT_KIND",
    "KNOWLEDGE_RETRIEVED_KIND",
    "OUTCOME_KIND",
    "PROMOTER_BETA_RECEIPT_KIND",
    "PROMOTE_CONTRACT_KINDS",
    "PROTECTED_DECISION_CLASSES",
    "PROVENANCE",
    "TS",
    "USAGE_KIND",
    "VERDICT_CORRECTION_KIND",
    "VERDICT_KIND",
    "VERIFICATION_OUTCOME_KIND",
    "_DATA_DRIVEN_PROCEDURES",
    "_KNOWLEDGE_ACQUISITION_CHANNELS",
    "_NON_DATA_DRIVEN_PROCEDURES",
    "_RETRIEVAL_PROCEDURES",
    "_UNKNOWN_DISPOSITIONS",
    "_VERIFICATION_ACQUISITION_CHANNELS",
    "_canonical_json",
    "_check_derivation_roots",
    "_outcome_is_censored",
    "canonical",
    "mutation_class_for",
]

ESCALATION_CLASSES = PROTECTED_DECISION_CLASSES

CONSENT_KINDS = frozenset({CONSENT_GRANTED, CONSENT_WITHDRAWN})

FEEDBACK_KINDS = frozenset(
    {FEEDBACK_ASKED_KIND, FEEDBACK_DECLINED_KIND, FEEDBACK_ANSWERED_KIND}
)

PROMOTE_CONTRACT_KINDS = frozenset(
    {IMPACT_CONTRACT_KIND, PROMOTER_BETA_RECEIPT_KIND, ACTIVATION_REFUSED_KIND}
)

DELIVERY_OUTCOME_KINDS = frozenset(
    {"delivery.outcome", "dispatch.outcome", OUTCOME_KIND}
)


def _digest_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _check_uuid4(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            value,
        )
        is None
    ):
        raise EventError(f"{field} must be lower-case hyphenated UUIDv4 text")


def mutation_class_for(procedure_kind: object) -> str | None:
    """Classify a learned-state operation. None means it is not a model.change."""
    if not isinstance(procedure_kind, str) or not procedure_kind.strip():
        raise EventError("learned-state procedure must be a non-empty string")
    if procedure_kind in _DATA_DRIVEN_PROCEDURES:
        return "data_driven_training"
    if procedure_kind in _NON_DATA_DRIVEN_PROCEDURES:
        return "non_data_driven_state_change"
    if procedure_kind in _RETRIEVAL_PROCEDURES:
        return None
    raise EventError(f"unknown learned-state procedure {procedure_kind!r}")


def _sha256_hex(kind: str, value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EventError(f"{kind} {field} must be 64 lower-case hex characters")
    return value


def _explicit_disposition(kind: str, value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.isprintable()
        or value.casefold() in _UNKNOWN_DISPOSITIONS
    ):
        raise EventError(f"{kind} must carry an explicit {field} disposition")
    return value


def _check_provenance(value: object, where: str) -> None:
    if value not in PROVENANCE:
        raise EventError(
            f"{USAGE_KIND} {where} must tag its provenance with one of "
            f"{sorted(PROVENANCE)}, got {value!r}; an untagged number is presented as "
            "authoritative and this project does not have one to present (V0-30)"
        )


def _canonical_token(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise EventError(f"{field} must be canonical printable text")
    if not value.isprintable():
        raise EventError(f"{field} must be canonical printable text")
    return value


def _hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EventError(f"{field} must be 64 lowercase hex characters")
    return value


def _check_acquisition_contract(event: EventPayload) -> None:
    """ADR-0081: source-kind events may carry one validated acquisition channel."""
    kind = event["event"]
    if kind not in {VERIFICATION_OUTCOME_KIND, KNOWLEDGE_RETRIEVED_KIND}:
        return
    data = event["data"]
    if "acquisition" not in data:
        return
    acquisition = data["acquisition"]
    if not isinstance(acquisition, dict):
        raise EventError("acquisition must be an object")
    channel = acquisition.get("channel")
    if channel not in ACQUISITION_CHANNELS:
        raise EventError(
            "acquisition.channel must be one of "
            f"{sorted(ACQUISITION_CHANNELS)}, got {channel!r}"
        )
    if (
        kind == VERIFICATION_OUTCOME_KIND
        and channel not in _VERIFICATION_ACQUISITION_CHANNELS
    ):
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} cannot carry acquisition.channel {channel!r}"
        )
    if (
        kind == KNOWLEDGE_RETRIEVED_KIND
        and channel not in _KNOWLEDGE_ACQUISITION_CHANNELS
    ):
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} cannot carry acquisition.channel {channel!r}"
        )

    common = {
        "channel",
        "observation_anchor",
        "derivation_roots",
        "conclusion_id",
        "alternative",
        "acceptance_contract_digest",
    }
    if channel == "artefact_execution":
        expected = common | {"environment"}
    elif channel == "browser_observation":
        expected = common | {
            "browser",
            "browser_version",
            "retained_evidence",
            "retained_evidence_digest",
        }
    elif channel == "primary_source_retrieval":
        expected = common | {
            "proposition_id",
            "stance",
            "locator",
            "verification_status",
        }
    else:
        expected = common | {
            "proposition_id",
            "stance",
            "locator",
            "corpus_manifest_digest",
            "provenance",
            "selection_rule",
            "assembled_context_digest",
        }
    actual = set(acquisition)
    if actual != expected:
        raise EventError(
            f"acquisition fields for {channel} mismatch; "
            f"missing {sorted(expected - actual)}, unexpected {sorted(actual - expected)}"
        )

    _canonical_token(
        acquisition["observation_anchor"], "acquisition.observation_anchor"
    )
    _canonical_token(acquisition["conclusion_id"], "acquisition.conclusion_id")
    _canonical_token(acquisition["alternative"], "acquisition.alternative")
    _hex64(
        acquisition["acceptance_contract_digest"],
        "acquisition.acceptance_contract_digest",
    )
    _check_derivation_roots(acquisition["derivation_roots"])

    if channel == "artefact_execution":
        _canonical_token(acquisition["environment"], "acquisition.environment")
        return
    if channel == "browser_observation":
        _canonical_token(acquisition["browser"], "acquisition.browser")
        _canonical_token(acquisition["browser_version"], "acquisition.browser_version")
        retained = acquisition["retained_evidence"]
        if retained not in BROWSER_RETAINED_EVIDENCE:
            raise EventError(
                "acquisition.retained_evidence must be one of "
                f"{sorted(BROWSER_RETAINED_EVIDENCE)}, got {retained!r}"
            )
        _hex64(
            acquisition["retained_evidence_digest"],
            "acquisition.retained_evidence_digest",
        )
        return

    _canonical_token(acquisition["proposition_id"], "acquisition.proposition_id")
    stance = acquisition["stance"]
    if stance not in ACQUISITION_STANCES:
        raise EventError(
            "acquisition.stance must be one of "
            f"{sorted(ACQUISITION_STANCES)}, got {stance!r}"
        )
    _canonical_token(acquisition["locator"], "acquisition.locator")
    if channel == "primary_source_retrieval":
        status = acquisition["verification_status"]
        if status not in ACQUISITION_SOURCE_STATUSES:
            raise EventError(
                "acquisition.verification_status must be one of "
                f"{sorted(ACQUISITION_SOURCE_STATUSES)}, got {status!r}"
            )
        return
    _hex64(
        acquisition["corpus_manifest_digest"],
        "acquisition.corpus_manifest_digest",
    )
    _canonical_token(acquisition["provenance"], "acquisition.provenance")
    _canonical_token(acquisition["selection_rule"], "acquisition.selection_rule")
    _hex64(
        acquisition["assembled_context_digest"],
        "acquisition.assembled_context_digest",
    )


def _intent_timestamp(value: object, where: str) -> datetime:
    if not isinstance(value, str) or TS.fullmatch(value) is None:
        raise EventError(f"{where} must be RFC3339 with an explicit offset")
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _check_attempt_identity(event: EventPayload) -> None:
    """Attempt records carry the stable identity that later records reference."""
    if event["event"] not in (
        OUTCOME_KIND,
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
    ):
        return
    attempt_id = event["data"].get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise EventError(f"{event['event']} must carry a non-empty string attempt_id")


def _decision_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"decision protocol {field} must be a non-empty string")
    return value

    # ADR-0078: caller-supplied actor/via metadata does not admit a capability gate.
    # Gate admission is derived only from inventory gate facts via effects.derive_admission().


def canonical(event: EventPayload) -> str:
    """One event, one line, stable key order so a replay hash is reproducible."""
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fsync_file(fd: int) -> None:
    try:
        os.fsync(fd)
    except OSError as exc:
        raise EventError(
            f"could not fsync the event line; the append is not acknowledged: {exc}"
        ) from exc


def _estimate_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"{field} must be a non-empty string")
    return value


def _estimate_non_negative_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EventError(f"{field} must be a non-negative integer")
    return value


def _outcome_is_completed(data: Mapping[str, object]) -> bool:
    if _outcome_is_censored(data):
        return False
    if data.get("verifier_accept") is False:
        return False
    status = data.get("status")
    if status is None:
        return True
    return status == "ok"


def _nearest_rank_percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise EventError("percentile requires at least one value")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]

"""The shared vocabulary of work-item events, and the readers for a single field.

Every event kind, actor, item schema, work-state group name, turn role and inform effect
the family uses is declared here, together with the smallest checks — the ones that read
one field, or one self-contained object, and need nothing else to decide. `_text`,
`_positive_int` and `_string_list` turn an untyped mapping into something the rest of
the family can rely on, and `_canonical_digest` fixes the one encoding — sorted keys, no
whitespace, UTF-8 — from which every digest in the family is taken.

The guards are deliberately narrow. A transport clause must say whether the channel was
authenticated; a redaction must be a broker reference and nothing else; a bare
sixty-four character hex token is treated as a leaked secret hash wherever it appears in
a turn, because the trajectory is append-only and a credential written into it cannot
afterwards be erased.

Nothing here consults another part of the family, and nothing reaches upward.
`decision_readiness` is the one function that walks a prefix — a dormant EXP-106
treatment asking whether an exact earlier material-choice decision stands unsuperseded —
but it reads events through the same narrow mapping accessor and decides on their
contents alone.
"""

from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, cast
from . import events

DEFAULT_ACTOR = "consilient.work"

INTAKE_ACTOR = "consilient.intake"

OPENED = "work_item.opened"

COMMENT = "work_item.comment"

COMPLETED = "work_item.completed"

COMMITTED = "work_item.committed"

PLAN_FROZEN = "organisation.plan.frozen"

TURN = "conversation.turn"

DISPATCH_CLAIM_SCHEMA = "dispatch-claim.v1"

NATIVE_SCHEMA = "native.v1"

WORK_MODEL_SCHEMA = "work-model.v1"

STATE = "work_item.state"

STATE_GROUP_WAITING = "WAITING"

STATE_GROUP_RUNNING = "RUNNING"

STATE_GROUP_NEEDS_YOU = "NEEDS_YOU"

STATE_GROUP_DONE = "DONE"

STATE_GROUP_DEAD = "DEAD"

INFORM_EFFECTS = frozenset({"duration", "quality"})

NATIVE_ATTEMPTED = "work_item.attempted"

NATIVE_COMMITMENT_PAUSED = "work_item.commitment_paused"

TURN_ROLES = frozenset({"user", "assistant", "system"})

_DIGEST = re.compile(r"^[0-9a-f]{64}$")

_NATIVE_CLOSURE_FIELDS = frozenset(
    {"plan_digest", "artefacts", "verifier_receipts", "predecessor_bindings"}
)

_FORBIDDEN_PLAN_DEPENDENCY_FIELDS = frozenset(
    {
        "artefact_digest",
        "artefact_sha256",
        "verifier_receipt_digest",
        "observed_outcome",
        "actual_digest",
    }
)

_THEATRE_ONLY_FIELDS = frozenset({"title", "model", "specialism"})


def _check_informs_edge(value: object, index: int) -> dict[str, object]:
    if not isinstance(value, dict):
        raise events.EventError(f"informs[{index}] must be an object")
    effect = value.get("effect")
    if effect not in INFORM_EFFECTS:
        raise events.EventError(
            f"informs[{index}].effect must be one of {sorted(INFORM_EFFECTS)}"
        )
    sign = value.get("sign")
    if not isinstance(sign, int) or isinstance(sign, bool) or sign not in (-1, 0, 1):
        raise events.EventError(f"informs[{index}].sign must be -1, 0 or 1")
    magnitude = value.get("magnitude_estimate")
    if (
        not isinstance(magnitude, (int, float))
        or isinstance(magnitude, bool)
        or magnitude < 0
    ):
        raise events.EventError(
            f"informs[{index}].magnitude_estimate must be a non-negative number"
        )
    return {
        "target_ticket": _text(
            value.get("target_ticket"), f"informs[{index}].target_ticket"
        ),
        "effect": cast(str, effect),
        "sign": sign,
        "magnitude_estimate": float(magnitude),
        "expires_at": _text(value.get("expires_at"), f"informs[{index}].expires_at"),
    }


def _check_inform_score(value: object, index: int) -> dict[str, object]:
    if not isinstance(value, dict):
        raise events.EventError(f"inform_scores[{index}] must be an object")
    effect = value.get("effect")
    if effect not in INFORM_EFFECTS:
        raise events.EventError(
            f"inform_scores[{index}].effect must be one of {sorted(INFORM_EFFECTS)}"
        )
    observed_sign = value.get("observed_sign")
    if (
        not isinstance(observed_sign, int)
        or isinstance(observed_sign, bool)
        or observed_sign not in (-1, 0, 1)
    ):
        raise events.EventError(
            f"inform_scores[{index}].observed_sign must be -1, 0 or 1"
        )
    observed_magnitude = value.get("observed_magnitude")
    if (
        not isinstance(observed_magnitude, (int, float))
        or isinstance(observed_magnitude, bool)
        or observed_magnitude < 0
    ):
        raise events.EventError(
            f"inform_scores[{index}].observed_magnitude must be a non-negative number"
        )
    return {
        "target_ticket": _text(
            value.get("target_ticket"), f"inform_scores[{index}].target_ticket"
        ),
        "effect": cast(str, effect),
        "observed_sign": observed_sign,
        "observed_magnitude": float(observed_magnitude),
    }


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise events.EventError(f"{field} must be a non-empty string")
    return value


def _positive_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise events.EventError(f"{field} must be a positive integer")
    return value


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise events.EventError(f"{field} must be a non-empty array of strings")
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise events.EventError(f"{field}[{index}] must be a non-empty string")
        items.append(item)
    return items


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan_is_outcome_aware_edit(
    prior: Mapping[str, object], successor: Mapping[str, object]
) -> bool:
    prior_streams = {
        cast(str, stream["stream_id"]): stream
        for stream in cast(list[dict[str, Any]], prior["streams"])
    }
    successor_streams = cast(list[dict[str, Any]], successor["streams"])
    for stream in successor_streams:
        stream_id = cast(str, stream["stream_id"])
        previous = prior_streams.get(stream_id)
        if previous is None:
            continue
        if stream.get("verifier_contracts") != previous.get("verifier_contracts"):
            return True
        if stream.get("handoff_contract") != previous.get("handoff_contract"):
            return True
    return False


def _check_transport(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise events.EventError("conversation.turn must carry transport as an object")
    authenticated = value.get("authenticated")
    if not isinstance(authenticated, bool):
        raise events.EventError(
            "conversation.turn transport.authenticated must be a boolean"
        )
    channel = value.get("channel")
    if not isinstance(channel, str) or not channel.strip():
        raise events.EventError(
            "conversation.turn transport.channel must be a non-empty string"
        )
    return {"authenticated": authenticated, "channel": channel.strip()}


# A leaked secret hash is a bare 64-hex token. Delimited so an ordinary long hex blob inside a
# larger word does not match, and so this pattern cannot trip on its own source text.
_SECRET_DIGEST = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")


def _check_redactions(value: object) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise events.EventError("conversation.turn redactions must be an array")
    redactions: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise events.EventError(
                f"conversation.turn redactions[{index}] must be an object"
            )
        kind = item.get("kind")
        reference = item.get("reference")
        if kind != "broker_reference":
            raise events.EventError(
                f"conversation.turn redactions[{index}] must be a broker_reference"
            )
        redactions.append(
            {
                "kind": "broker_reference",
                "reference": _text(
                    reference, f"conversation.turn redactions[{index}].reference"
                ),
            }
        )
    return redactions


def _is_dispatch_claim_data(data: Mapping[str, object]) -> bool:
    return "run_id" in data and "paths" in data


def _opened_schema(data: Mapping[str, object]) -> str | None:
    schema = data.get("item_schema")
    if schema is None:
        return None
    if not isinstance(schema, str) or not schema.strip():
        raise events.EventError("item_schema must be a non-empty string when present")
    return schema.strip()


def _event_mapping(item: object) -> Mapping[str, object]:
    if isinstance(item, Mapping):
        return item
    raw = item.raw if isinstance(item, events.Event) else None
    if isinstance(raw, Mapping):
        return raw
    raise events.EventError("transition validator received an unknown event shape")


def decision_readiness(
    accepted_prefix: Sequence[object],
    dependent_item: object,
    expected_decision_digest: str,
) -> bool:
    """Dormant EXP-106 treatment: require an exact earlier material-choice record."""
    if _DIGEST.fullmatch(expected_decision_digest) is None:
        return False
    try:
        dependent = _event_mapping(dependent_item)
    except events.EventError:
        return False
    dependent_data = dependent.get("data")
    if not isinstance(dependent_data, Mapping):
        return False
    decision_id = dependent_data.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        return False

    before: list[Mapping[str, object]] = []
    dependent_event_id = dependent.get("event_id")
    for item in accepted_prefix:
        try:
            raw = _event_mapping(item)
        except events.EventError:
            return False
        same_item = raw is dependent
        if (
            not same_item
            and isinstance(dependent_event_id, str)
            and raw.get("event_id") == dependent_event_id
        ):
            same_item = True
        if same_item:
            break
        before.append(raw)

    matched: Mapping[str, object] | None = None
    for raw in before:
        record = events.decision_protocol_data(raw)
        if record is None or raw.get("event") != events.DECISION_KIND:
            continue
        binding = record.get("binding")
        if (
            record.get("decision_id") == decision_id
            and isinstance(binding, Mapping)
            and binding.get("kind") == "material_choice"
            and events.event_sha256(cast(events.EventPayload, raw))
            == expected_decision_digest
        ):
            matched = raw
            break
    if matched is None:
        return False

    matched_id = matched.get("event_id")
    matched_digest = events.event_sha256(cast(events.EventPayload, matched))
    for raw in before:
        record = events.decision_protocol_data(raw)
        if record is None or raw is matched:
            continue
        supersedes = record.get("supersedes")
        if (
            isinstance(supersedes, Mapping)
            and supersedes.get("event_id") == matched_id
            and supersedes.get("event_sha256") == matched_digest
        ):
            return False
    return True


def _source_turns_authenticated(
    data: Mapping[str, Any], turns: Mapping[str, Mapping[str, Any]]
) -> bool:
    conversation_id = cast(str, data["conversation_id"])
    for turn_id in cast(list[str], data["source_turn_ids"]):
        turn = turns.get(f"{conversation_id}:{turn_id}")
        if turn is None:
            raise events.EventError(
                f"source turn {turn_id!r} is missing from the trajectory"
            )
        transport = turn.get("transport")
        if (
            not isinstance(transport, dict)
            or transport.get("authenticated") is not True
        ):
            return False
    return True

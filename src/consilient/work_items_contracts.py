"""The clauses a work-item contract must contain, and the digests that freeze them.

A commitment, a plan stream and a native item are each assembled from declared clauses —
an authority reference, a deliverable contract, verifier contracts, an exposure
contract, estimate inputs, requires edges, dependency edges — and this file says what
each clause must hold. It also declares the work states themselves and the five groups
they roll up into, so that WAITING, RUNNING, NEEDS_YOU, DONE and DEAD are defined in
exactly one place, alongside the set of event kinds that count as work-item events at
all.

The digest functions are the freezing half. Success criteria and non-goals, the source
turns behind a request, a commitment, a hand-off contract and a plan each reduce to a
canonical SHA-256 computed over the record with its own digest field removed, so that no
record can certify itself. A digest that does not reproduce is a record that has been
edited since it was frozen.

`_check_turn_contract` refuses a conversation turn carrying a secret hash. The comment
beside that guard records what it cost to get right and is worth reading before touching
it: the dangerous case was once the one that passed."""

from __future__ import annotations
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from . import events
from .work_items_vocabulary import (
    COMMENT,
    COMMITTED,
    COMPLETED,
    OPENED,
    STATE,
    STATE_GROUP_DEAD,
    STATE_GROUP_DONE,
    STATE_GROUP_NEEDS_YOU,
    STATE_GROUP_RUNNING,
    STATE_GROUP_WAITING,
    TURN,
    TURN_ROLES,
    _DIGEST,
    _SECRET_DIGEST,
    _THEATRE_ONLY_FIELDS,
    _canonical_digest,
    _check_redactions,
    _check_transport,
    _event_mapping,
    _positive_int,
    _string_list,
    _text,
)


__all__ = [
    "COMMENT",
    "COMMITTED",
    "COMPLETED",
    "KINDS",
    "OPENED",
    "STATE",
    "STATE_GROUPS",
    "STATE_GROUP_DEAD",
    "STATE_GROUP_DONE",
    "STATE_GROUP_NEEDS_YOU",
    "STATE_GROUP_RUNNING",
    "STATE_GROUP_WAITING",
    "TURN",
    "TURN_ROLES",
    "WORK_STATE_DEFINITIONS",
    "_DIGEST",
    "_SECRET_DIGEST",
    "_THEATRE_ONLY_FIELDS",
    "_canonical_digest",
    "_check_redactions",
    "_check_transport",
    "_event_mapping",
    "_positive_int",
    "_string_list",
    "_text",
    "commitment_digest",
    "handoff_contract_digest",
    "plan_digest",
    "source_turn_digest",
    "success_digest",
]

STATE_GROUPS = (
    STATE_GROUP_WAITING,
    STATE_GROUP_RUNNING,
    STATE_GROUP_NEEDS_YOU,
    STATE_GROUP_DONE,
    STATE_GROUP_DEAD,
)

WORK_STATE_DEFINITIONS: dict[str, dict[str, str]] = {
    "blocked": {"group": STATE_GROUP_WAITING},
    "ready": {"group": STATE_GROUP_RUNNING},
    "active": {"group": STATE_GROUP_RUNNING},
    "refused": {"group": STATE_GROUP_NEEDS_YOU},
    "unfunded": {"group": STATE_GROUP_NEEDS_YOU},
    "closed": {"group": STATE_GROUP_DONE},
    "failed": {"group": STATE_GROUP_DEAD},
    "cancelled": {"group": STATE_GROUP_DEAD},
    "expired": {"group": STATE_GROUP_DEAD},
    "invalidated": {"group": STATE_GROUP_DEAD},
    "superseded": {"group": STATE_GROUP_DEAD},
}

KINDS = frozenset({OPENED, COMMENT, COMPLETED, COMMITTED, STATE})


def _check_blocked_overlay(data: Mapping[str, object]) -> None:
    if "is_blocked" not in data:
        return
    is_blocked = data.get("is_blocked")
    if not isinstance(is_blocked, bool):
        raise events.EventError("is_blocked must be a boolean when present")
    if is_blocked:
        _text(data.get("blocked_reason"), "blocked_reason")


def _check_requires_edge(value: object, index: int) -> dict[str, str]:
    if not isinstance(value, dict):
        raise events.EventError(f"requires[{index}] must be an object")
    return {
        "target_ticket": _text(
            value.get("target_ticket"), f"requires[{index}].target_ticket"
        ),
    }


def _digest(value: object, field: str) -> str:
    text = _text(value, field)
    if _DIGEST.fullmatch(text) is None:
        raise events.EventError(f"{field} must be a lowercase SHA-256 digest")
    return text


def _timestamp(value: object, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise events.EventError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise events.EventError(f"{field} must carry an explicit offset")
    return text


def success_digest(success_criteria: Sequence[str], non_goals: Sequence[str]) -> str:
    return _canonical_digest(
        {"success_criteria": list(success_criteria), "non_goals": list(non_goals)}
    )


def source_turn_digest(
    conversation_id: str,
    turn_ids: Sequence[str],
    texts_by_turn: Mapping[str, str],
) -> str:
    ordered = [
        {
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "text": texts_by_turn[turn_id],
        }
        for turn_id in turn_ids
    ]
    return _canonical_digest({"turns": ordered})


def commitment_digest(contract: Mapping[str, object]) -> str:
    frozen = {
        key: value for key, value in contract.items() if key != "commitment_digest"
    }
    return _canonical_digest(frozen)


def handoff_contract_digest(schema: str, allowed_locators: Sequence[str]) -> str:
    return _canonical_digest(
        {"schema": schema, "allowed_locators": list(allowed_locators)}
    )


def plan_digest(plan: Mapping[str, object]) -> str:
    frozen = {key: value for key, value in plan.items() if key != "plan_digest"}
    return _canonical_digest(frozen)


def _stream_identity(stream: Mapping[str, object]) -> dict[str, object]:
    return {
        key: stream[key]
        for key in stream
        if key not in _THEATRE_ONLY_FIELDS and key != "stream_id"
    }


def _check_estimate_inputs(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("estimate_inputs must be an object")
    lower = value.get("duration_lower_s")
    upper = value.get("duration_upper_s")
    if not isinstance(lower, int) or isinstance(lower, bool) or lower < 0:
        raise events.EventError(
            "estimate_inputs.duration_lower_s must be a non-negative integer"
        )
    if not isinstance(upper, int) or isinstance(upper, bool) or upper < lower:
        raise events.EventError(
            "estimate_inputs.duration_upper_s must be an integer >= duration_lower_s"
        )
    _text(value.get("derivation"), "estimate_inputs.derivation")
    _text(value.get("evidence_class"), "estimate_inputs.evidence_class")


def _check_deliverable_contract(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("commitment deliverable_contract must be an object")
    _text(value.get("kind"), "commitment deliverable_contract.kind")
    _text(value.get("handoff_schema"), "commitment deliverable_contract.handoff_schema")
    _string_list(
        value.get("allowed_locators"),
        "commitment deliverable_contract.allowed_locators",
    )


def _check_verifier_contracts(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise events.EventError(
            "commitment verifier_contracts must be a non-empty array"
        )
    parsed: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise events.EventError(
                f"commitment verifier_contracts[{index}] must be an object"
            )
        parsed.append(
            {
                "id": _text(
                    item.get("id"), f"commitment verifier_contracts[{index}].id"
                ),
                "digest": _digest(
                    item.get("digest"), f"commitment verifier_contracts[{index}].digest"
                ),
                "task_family": _text(
                    item.get("task_family"),
                    f"commitment verifier_contracts[{index}].task_family",
                ),
                "required_outcome": _text(
                    item.get("required_outcome"),
                    f"commitment verifier_contracts[{index}].required_outcome",
                ),
            }
        )
    return parsed


def _check_native_dependencies(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise events.EventError("dependencies must be an array")
    dependencies: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for index, dependency in enumerate(value):
        if not isinstance(dependency, dict):
            raise events.EventError(f"dependencies[{index}] must be an object")
        ticket = _text(dependency.get("ticket"), f"dependencies[{index}].ticket")
        revision = _positive_int(
            dependency.get("revision"), f"dependencies[{index}].revision"
        )
        key = (ticket, revision)
        if key in seen:
            raise events.EventError("native dependencies must be unique")
        seen.add(key)
        dependencies.append(
            {
                "ticket": ticket,
                "revision": revision,
                "handoff_contract_digest": _digest(
                    dependency.get("handoff_contract_digest"),
                    f"dependencies[{index}].handoff_contract_digest",
                ),
            }
        )
    return dependencies


def _check_exposure_contract(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("exposure_contract must be an object")
    _text(value.get("key"), "exposure_contract.key")
    epsilon = value.get("epsilon")
    if (
        not isinstance(epsilon, (int, float))
        or isinstance(epsilon, bool)
        or not 0 <= epsilon <= 1
    ):
        raise events.EventError(
            "exposure_contract.epsilon must be a number from 0 to 1"
        )
    _text(value.get("rule"), "exposure_contract.rule")
    _text(value.get("beta_version"), "exposure_contract.beta_version")
    n_max = value.get("n_max")
    if not isinstance(n_max, int) or isinstance(n_max, bool) or n_max < 0:
        raise events.EventError(
            "exposure_contract.n_max must be a non-negative integer"
        )


def _check_native_attempt(data: Mapping[str, object]) -> None:
    _text(data.get("ticket"), "ticket")
    _positive_int(data.get("revision"), "revision")
    _digest(data.get("plan_digest"), "plan_digest")
    for field in (
        "attempt_id",
        "run_id",
        "harness",
        "model",
        "family",
        "pool",
        "exposure_state",
    ):
        _text(data.get(field), field)
    _string_list(data.get("claimed_paths"), "claimed_paths")
    _digest(data.get("capability_context_digest"), "capability_context_digest")
    for field in ("opened_at", "expires_at"):
        _timestamp(data.get(field), field)
    _positive_int(data.get("candidate_ordinal"), "candidate_ordinal")
    bindings = data.get("predecessor_bindings")
    if not isinstance(bindings, list):
        raise events.EventError("predecessor_bindings must be an array")


def _check_authority_ref(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise events.EventError("commitment authority_ref must be an object")
    kind = value.get("kind")
    if kind == "unprotected":
        return {"kind": "unprotected"}
    if kind == "principal_required":
        reserved = value.get("reserved")
        if not isinstance(reserved, list) or not reserved:
            raise events.EventError(
                "commitment authority_ref.reserved must be a non-empty array"
            )
        items = [_text(item, "commitment authority_ref.reserved") for item in reserved]
        return {"kind": "principal_required", "reserved": items}
    raise events.EventError(
        "commitment authority_ref.kind must be 'unprotected' or 'principal_required'"
    )


def _check_turn_contract(data: dict[str, Any]) -> None:
    conversation_id = _text(data.get("conversation_id"), "conversation_id")
    turn_id = _text(data.get("turn_id"), "turn_id")
    root_request_turn_id = _text(
        data.get("root_request_turn_id"), "root_request_turn_id"
    )
    reply_to = data.get("reply_to_turn_id")
    if reply_to is not None:
        _text(reply_to, "reply_to_turn_id")
    role = data.get("role")
    if role not in TURN_ROLES:
        raise events.EventError(
            "conversation.turn role must be user, assistant or system"
        )
    _text(data.get("text"), "text")
    _check_transport(data.get("transport"))
    redactions = _check_redactions(data.get("redactions"))
    trajectory = json.dumps(data, ensure_ascii=False, sort_keys=True)
    # MEASURED 24 August 2026, and the guard was exactly backwards. `and redactions` meant it
    # fired only when the turn DECLARED redactions, and stayed silent when it declared none --
    # so a credential in a turn with an empty redactions array was accepted and fsync'd into an
    # append-only log that cannot afterwards be erased. Probed directly: secret-like text with
    # no redactions was ACCEPTED; the same text with redactions was refused. The dangerous case
    # was the one that passed. No test named this guard, which is why it survived.
    #
    # The conjunction was not gratuitous: the literal-marker test matches the STRING "sha256"
    # anywhere in the serialised turn, so removing it outright would refuse any turn merely
    # discussing hashing. Suppressing that noise is what silenced the guard. So the
    # discriminator is sharpened rather than the condition flipped: a bare 64-hex digest is
    # refused unconditionally, because that is what a leaked secret hash actually looks like,
    # and every refusal the old rule made is preserved. Strictly stronger, never weaker.
    if _SECRET_DIGEST.search(trajectory) or (
        "sha256" in trajectory.casefold() and redactions
    ):
        raise events.EventError("secret hashes must not be stored in conversation.turn")
    del conversation_id, turn_id, root_request_turn_id


def _turns_by_id(
    prefix: Sequence[object], candidates: Sequence[object]
) -> dict[str, dict[str, Any]]:
    turns: dict[str, dict[str, Any]] = {}
    for item in (*prefix, *candidates):
        raw = _event_mapping(item)
        if raw.get("event") != TURN:
            continue
        data = raw.get("data")
        if not isinstance(data, dict):
            continue
        turn_id = data.get("turn_id")
        conversation_id = data.get("conversation_id")
        if isinstance(turn_id, str) and isinstance(conversation_id, str):
            turns[f"{conversation_id}:{turn_id}"] = data
    return turns

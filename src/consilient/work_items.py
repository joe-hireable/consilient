"""Work-item events in the authoritative trajectory."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from . import events

DEFAULT_ACTOR = "consilient.work"
INTAKE_ACTOR = "consilient.intake"
OPENED = "work_item.opened"
COMMENT = "work_item.comment"
COMPLETED = "work_item.completed"
COMMITTED = "work_item.committed"
TURN = "conversation.turn"
DISPATCH_CLAIM_SCHEMA = "dispatch-claim.v1"
NATIVE_SCHEMA = "native.v1"
KINDS = frozenset({OPENED, COMMENT, COMPLETED, COMMITTED})
TURN_ROLES = frozenset({"user", "assistant", "system"})
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_NATIVE_CLOSURE_FIELDS = frozenset(
    {"plan_digest", "artefacts", "verifier_receipts", "predecessor_bindings"}
)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise events.EventError(f"{field} must be a non-empty string")
    return value


def _digest(value: object, field: str) -> str:
    text = _text(value, field)
    if _DIGEST.fullmatch(text) is None:
        raise events.EventError(f"{field} must be a lowercase SHA-256 digest")
    return text


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
    frozen = {key: value for key, value in contract.items() if key != "commitment_digest"}
    return _canonical_digest(frozen)


def _check_transport(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise events.EventError("conversation.turn must carry transport as an object")
    authenticated = value.get("authenticated")
    if not isinstance(authenticated, bool):
        raise events.EventError("conversation.turn transport.authenticated must be a boolean")
    channel = value.get("channel")
    if not isinstance(channel, str) or not channel.strip():
        raise events.EventError("conversation.turn transport.channel must be a non-empty string")
    return {"authenticated": authenticated, "channel": channel.strip()}


def _check_redactions(value: object) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise events.EventError("conversation.turn redactions must be an array")
    redactions: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise events.EventError(f"conversation.turn redactions[{index}] must be an object")
        kind = item.get("kind")
        reference = item.get("reference")
        if kind != "broker_reference":
            raise events.EventError(
                f"conversation.turn redactions[{index}] must be a broker_reference"
            )
        redactions.append(
            {
                "kind": "broker_reference",
                "reference": _text(reference, f"conversation.turn redactions[{index}].reference"),
            }
        )
    return redactions


def _check_incumbent(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("commitment incumbent must be an object")
    for field in (
        "name",
        "source",
        "retrieval_date",
        "search_digest",
        "evidence_tag",
        "delta",
        "killing_check",
    ):
        if field == "search_digest":
            _digest(value.get(field), f"commitment incumbent.{field}")
        else:
            _text(value.get(field), f"commitment incumbent.{field}")


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
        raise events.EventError("commitment verifier_contracts must be a non-empty array")
    parsed: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise events.EventError(f"commitment verifier_contracts[{index}] must be an object")
        parsed.append(
            {
                "id": _text(item.get("id"), f"commitment verifier_contracts[{index}].id"),
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


def _check_commitment_contract(data: dict[str, Any]) -> None:
    commitment_id = _text(data.get("commitment_id"), "commitment_id")
    revision = _positive_int(data.get("revision"), "revision")
    _text(data.get("conversation_id"), "conversation_id")
    source_turn_ids = _string_list(data.get("source_turn_ids"), "source_turn_ids")
    _digest(data.get("source_turn_digest"), "source_turn_digest")
    _text(data.get("request_text"), "request_text")
    _text(data.get("goal_text"), "goal_text")
    success_criteria = _string_list(data.get("success_criteria"), "success_criteria")
    non_goals = data.get("non_goals")
    if not isinstance(non_goals, list):
        raise events.EventError("non_goals must be an array")
    for index, item in enumerate(non_goals):
        if not isinstance(item, str):
            raise events.EventError(f"non_goals[{index}] must be a string")
    success = _digest(data.get("success_digest"), "success_digest")
    if success != success_digest(success_criteria, non_goals):
        raise events.EventError("success_digest does not match success_criteria and non_goals")
    _check_incumbent(data.get("incumbent"))
    _check_deliverable_contract(data.get("deliverable_contract"))
    _text(data.get("accountable"), "accountable")
    composition = data.get("composition")
    if not isinstance(composition, dict) or not composition:
        raise events.EventError("composition must be a non-empty object")
    for field in ("assumptions", "autonomous_decision_refs", "reserved_decisions"):
        if not isinstance(data.get(field), list):
            raise events.EventError(f"{field} must be an array")
    authority_ref = _check_authority_ref(data.get("authority_ref"))
    _check_verifier_contracts(data.get("verifier_contracts"))
    mutation_scope = data.get("mutation_scope")
    if not isinstance(mutation_scope, dict):
        raise events.EventError("mutation_scope must be an object")
    _string_list(mutation_scope.get("paths"), "mutation_scope.paths")
    _text(data.get("budget_ref"), "budget_ref")
    _text(data.get("expires_at"), "expires_at")
    question_count = data.get("question_count")
    if question_count not in (0, 1):
        raise events.EventError("question_count must be 0 or 1")
    question_turn_id = data.get("question_turn_id")
    if question_count == 0:
        if question_turn_id is not None:
            raise events.EventError("question_turn_id must be absent when question_count is 0")
    else:
        _text(question_turn_id, "question_turn_id")
    supersedes = data.get("supersedes_commitment_digest")
    if revision == 1:
        if supersedes is not None:
            raise events.EventError(
                "revision 1 must not carry supersedes_commitment_digest"
            )
    elif supersedes is None:
        raise events.EventError(
            "revisions after 1 must carry supersedes_commitment_digest"
        )
    else:
        _digest(supersedes, "supersedes_commitment_digest")
    digest = data.get("commitment_digest")
    if digest is None:
        raise events.EventError("commitment_digest is required")
    computed = commitment_digest(data)
    if digest != computed:
        raise events.EventError("commitment_digest does not match the frozen contract")
    if authority_ref["kind"] == "principal_required":
        reserved = data.get("reserved_decisions")
        if not isinstance(reserved, list) or not reserved:
            raise events.EventError(
                "reserved_decisions must be present for a principal_required authority_ref"
            )
    del commitment_id


def _check_turn_contract(data: dict[str, Any]) -> None:
    conversation_id = _text(data.get("conversation_id"), "conversation_id")
    turn_id = _text(data.get("turn_id"), "turn_id")
    root_request_turn_id = _text(data.get("root_request_turn_id"), "root_request_turn_id")
    reply_to = data.get("reply_to_turn_id")
    if reply_to is not None:
        _text(reply_to, "reply_to_turn_id")
    role = data.get("role")
    if role not in TURN_ROLES:
        raise events.EventError("conversation.turn role must be user, assistant or system")
    _text(data.get("text"), "text")
    _check_transport(data.get("transport"))
    redactions = _check_redactions(data.get("redactions"))
    trajectory = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if "sha256" in trajectory.casefold() and redactions:
        raise events.EventError("secret hashes must not be stored in conversation.turn")
    del conversation_id, turn_id, root_request_turn_id


def _is_dispatch_claim_data(data: Mapping[str, object]) -> bool:
    return "run_id" in data and "paths" in data


def _opened_schema(data: Mapping[str, object]) -> str | None:
    schema = data.get("item_schema")
    if schema is None:
        return None
    if not isinstance(schema, str) or not schema.strip():
        raise events.EventError("item_schema must be a non-empty string when present")
    return schema.strip()


def check_event_contract(event: events.EventPayload) -> None:
    kind = event["event"]
    data = cast(dict[str, Any], event["data"])
    if kind == TURN:
        _check_turn_contract(data)
        return
    if kind == COMMITTED:
        _check_commitment_contract(data)
        return
    if kind not in KINDS:
        return
    ticket = data.get("ticket")
    if not isinstance(ticket, str) or not ticket.strip():
        raise events.EventError("work-item events must carry a non-empty string ticket")
    for field in ("human_decision", "human_verdict"):
        if field in data:
            raise events.EventError(f"work-item events cannot carry {field}")
    if kind == OPENED:
        accountable = data.get("accountable")
        if not isinstance(accountable, str) or not accountable.strip():
            raise events.EventError(
                "work_item.opened must carry a non-empty string accountable"
            )
        schema = _opened_schema(data)
        if schema == DISPATCH_CLAIM_SCHEMA:
            _text(data.get("run_id"), "dispatch claim run_id")
            _string_list(data.get("paths"), "dispatch claim paths")
            _text(data.get("cwd"), "dispatch claim cwd")
            _text(data.get("opened_at"), "dispatch claim opened_at")
            _text(data.get("expires_at"), "dispatch claim expires_at")
        elif schema == NATIVE_SCHEMA:
            raise events.EventError(
                "native.v1 work_item.opened is not admitted until task-management activation"
            )
        elif schema is not None:
            raise events.EventError(f"unsupported item_schema {schema!r}")
    if kind == COMMENT:
        evidence_class = data.get("evidence_class")
        if not isinstance(evidence_class, str) or not evidence_class.strip():
            raise events.EventError(
                "work_item.comment must carry a non-empty evidence_class"
            )


def validate(event: object) -> events.EventPayload:
    checked = events.validate(event)
    check_event_contract(checked)
    return checked


def _event_payload(
    kind: str,
    actor: str,
    data: dict[str, Any],
    *,
    ts: str | None = None,
) -> events.EventPayload:
    now = ts or datetime.now(timezone.utc).isoformat()
    event = {
        "v": events.SCHEMA_VERSION,
        "ts": now,
        "event": kind,
        "actor": actor,
        "data": data,
    }
    validate(event)
    return event


def _append(
    log: Path,
    kind: str,
    actor: str,
    data: dict[str, Any],
    *,
    ts: str | None = None,
) -> events.EventPayload:
    event = _event_payload(kind, actor, data, ts=ts)
    return events.append(log / f"{event['ts'][:10]}.jsonl", event)


def seal_turn(
    log: Path,
    *,
    conversation_id: str,
    turn_id: str,
    root_request_turn_id: str,
    role: str,
    text: str,
    transport_authenticated: bool = True,
    transport_channel: str = "chat",
    reply_to_turn_id: str | None = None,
    redactions: list[dict[str, str]] | None = None,
    actor: str = INTAKE_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "root_request_turn_id": root_request_turn_id,
        "role": role,
        "text": text,
        "transport": {
            "authenticated": transport_authenticated,
            "channel": transport_channel,
        },
    }
    if reply_to_turn_id is not None:
        data["reply_to_turn_id"] = reply_to_turn_id
    if redactions:
        data["redactions"] = redactions
    return _append(log, TURN, actor, data, ts=ts)


def commit_request(
    log: Path,
    contract: Mapping[str, object],
    *,
    actor: str = INTAKE_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    data = dict(contract)
    if "commitment_digest" not in data:
        data["commitment_digest"] = commitment_digest(data)
    return _append(log, COMMITTED, actor, data, ts=ts)


def open_item(
    log: Path,
    *,
    ticket: str,
    accountable: str,
    actor: str = DEFAULT_ACTOR,
    text: str | None = None,
    extra: dict[str, Any] | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket, "accountable": accountable}
    if text is not None:
        data["text"] = text
    if extra is not None:
        reserved = set(data) | {"human_decision", "human_verdict"}
        collision = reserved & set(extra)
        if collision:
            raise events.EventError(
                f"work_item.opened extra fields may not override {sorted(collision)}"
            )
        data.update(extra)
    return _append(log, OPENED, actor, data)


def comment(
    log: Path,
    *,
    ticket: str,
    text: str,
    evidence_class: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> events.EventPayload:
    data = {"ticket": ticket, "text": text}
    if evidence_class is not None:
        data["evidence_class"] = evidence_class
    return _append(
        log,
        COMMENT,
        actor,
        data,
    )


def complete_item(
    log: Path, *, ticket: str, actor: str = DEFAULT_ACTOR
) -> events.EventPayload:
    return _append(log, COMPLETED, actor, {"ticket": ticket})


def _event_mapping(item: object) -> Mapping[str, object]:
    if isinstance(item, Mapping):
        return item
    raw = item.raw if isinstance(item, events.Event) else None
    if isinstance(raw, Mapping):
        return raw
    raise events.EventError("transition validator received an unknown event shape")


def _turns_by_id(prefix: Sequence[object], candidates: Sequence[object]) -> dict[str, dict[str, Any]]:
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


def _source_turns_authenticated(
    data: Mapping[str, Any], turns: Mapping[str, Mapping[str, Any]]
) -> bool:
    conversation_id = cast(str, data["conversation_id"])
    for turn_id in cast(list[str], data["source_turn_ids"]):
        turn = turns.get(f"{conversation_id}:{turn_id}")
        if turn is None:
            raise events.EventError(f"source turn {turn_id!r} is missing from the trajectory")
        transport = turn.get("transport")
        if not isinstance(transport, dict) or transport.get("authenticated") is not True:
            return False
    return True


def validate_transition(
    prefix: Sequence[object],
    rejections: Sequence[object],
    candidates: Sequence[object],
) -> None:
    del rejections
    seen_turns: set[tuple[str, str]] = set()
    commitment_seen: set[tuple[str, int]] = set()
    commitment_tips: dict[str, dict[str, Any]] = {}
    opened_by_ticket: dict[str, dict[str, Any]] = {}

    for item in prefix:
        raw = _event_mapping(item)
        kind = raw.get("event")
        data = raw.get("data")
        if not isinstance(data, dict):
            continue
        if kind == TURN:
            key = (cast(str, data["conversation_id"]), cast(str, data["turn_id"]))
            if key in seen_turns:
                raise events.EventError(f"duplicate conversation.turn {key[1]!r}")
            seen_turns.add(key)
        elif kind == COMMITTED:
            commitment_id = cast(str, data["commitment_id"])
            revision = cast(int, data["revision"])
            commitment_seen.add((commitment_id, revision))
            commitment_tips[commitment_id] = data
        elif kind == OPENED:
            ticket = cast(str, data["ticket"])
            opened_by_ticket[ticket] = data

    turns = _turns_by_id(prefix, ())

    for item in candidates:
        raw = _event_mapping(item)
        kind = raw.get("event")
        data = raw.get("data")
        if not isinstance(data, dict):
            continue
        if kind == TURN:
            key = (cast(str, data["conversation_id"]), cast(str, data["turn_id"]))
            if key in seen_turns:
                raise events.EventError(f"duplicate conversation.turn {key[1]!r}")
            seen_turns.add(key)
            turns[f"{key[0]}:{key[1]}"] = data
        elif kind == COMMITTED:
            commitment_id = cast(str, data["commitment_id"])
            revision = cast(int, data["revision"])
            if (commitment_id, revision) in commitment_seen:
                raise events.EventError(
                    f"commitment {commitment_id!r} revision {revision} already exists"
                )
            tip = commitment_tips.get(commitment_id)
            if revision == 1:
                if tip is not None:
                    raise events.EventError(
                        f"commitment {commitment_id!r} already has a live revision"
                    )
            else:
                if tip is None:
                    raise events.EventError(
                        f"commitment {commitment_id!r} has no prior revision to supersede"
                    )
                expected = tip.get("commitment_digest")
                actual = data.get("supersedes_commitment_digest")
                if actual != expected:
                    raise events.EventError("supersedes_commitment_digest is stale")
            authority = data.get("authority_ref")
            if (
                isinstance(authority, dict)
                and authority.get("kind") == "principal_required"
                and not _source_turns_authenticated(data, turns)
            ):
                raise events.EventError(
                    "protected commitments require authenticated source turns"
                )
            commitment_tips[commitment_id] = data
        elif kind == COMPLETED:
            ticket = cast(str, data["ticket"])
            opened = opened_by_ticket.get(ticket)
            if opened is None:
                continue
            if _NATIVE_CLOSURE_FIELDS & set(data) and (
                _opened_schema(opened) == DISPATCH_CLAIM_SCHEMA
                or (
                    _opened_schema(opened) is None and _is_dispatch_claim_data(opened)
                )
            ):
                raise events.EventError(
                    "dispatch-claim completion cannot carry native task-closure evidence"
                )
        elif kind == OPENED:
            opened_by_ticket[cast(str, data["ticket"])] = data


def _register_transition_validator() -> None:
    events.register_transition_validator(
        (TURN, COMMITTED, OPENED, COMPLETED),
        validate_transition,
    )


_register_transition_validator()

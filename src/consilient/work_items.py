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
PLAN_FROZEN = "organisation.plan.frozen"
TURN = "conversation.turn"
DISPATCH_CLAIM_SCHEMA = "dispatch-claim.v1"
NATIVE_SCHEMA = "native.v1"
KINDS = frozenset({OPENED, COMMENT, COMPLETED, COMMITTED})
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


def handoff_contract_digest(schema: str, allowed_locators: Sequence[str]) -> str:
    return _canonical_digest(
        {"schema": schema, "allowed_locators": list(allowed_locators)}
    )


def plan_digest(plan: Mapping[str, object]) -> str:
    frozen = {key: value for key, value in plan.items() if key != "plan_digest"}
    return _canonical_digest(frozen)


def _check_handoff_contract(value: object, field: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise events.EventError(f"{field} must be an object")
    return {
        "schema": _text(value.get("schema"), f"{field}.schema"),
        "digest": _digest(value.get("digest"), f"{field}.digest"),
    }


def _check_plan_dependency(value: object, index: int) -> dict[str, object]:
    if not isinstance(value, dict):
        raise events.EventError(f"dependencies[{index}] must be an object")
    forbidden = _FORBIDDEN_PLAN_DEPENDENCY_FIELDS & set(value)
    if forbidden:
        joined = ", ".join(sorted(forbidden))
        raise events.EventError(
            f"dependencies[{index}] forbids future-bound fields: {joined}"
        )
    return {
        "stream_id": _text(value.get("stream_id"), f"dependencies[{index}].stream_id"),
        "revision": _positive_int(value.get("revision"), f"dependencies[{index}].revision"),
        "handoff_contract_digest": _digest(
            value.get("handoff_contract_digest"),
            f"dependencies[{index}].handoff_contract_digest",
        ),
    }


def _stream_identity(stream: Mapping[str, object]) -> dict[str, object]:
    return {
        key: stream[key]
        for key in stream
        if key not in _THEATRE_ONLY_FIELDS and key != "stream_id"
    }


def _streams_are_theatre_only_split(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    if _stream_identity(left) != _stream_identity(right):
        return False
    if left.get("stream_id") == right.get("stream_id"):
        return False
    return any(field in left or field in right for field in _THEATRE_ONLY_FIELDS)


def _check_plan_stream(value: object, index: int) -> dict[str, object]:
    if not isinstance(value, dict):
        raise events.EventError(f"streams[{index}] must be an object")
    stream_id = _text(value.get("stream_id"), f"streams[{index}].stream_id")
    deliverable = _text(value.get("deliverable"), f"streams[{index}].deliverable")
    accountable = _text(value.get("accountable"), f"streams[{index}].accountable")
    owned_paths = value.get("owned_paths")
    if not isinstance(owned_paths, list):
        raise events.EventError(f"streams[{index}].owned_paths must be an array")
    paths = [
        _text(item, f"streams[{index}].owned_paths[{path_index}]")
        for path_index, item in enumerate(owned_paths)
    ]
    integration = value.get("integration")
    if not isinstance(integration, bool):
        raise events.EventError(f"streams[{index}].integration must be a boolean")
    if not integration and not paths:
        raise events.EventError(
            f"streams[{index}] requires non-empty owned_paths for a mutable stream"
        )
    dependencies = value.get("dependencies")
    if not isinstance(dependencies, list):
        raise events.EventError(f"streams[{index}].dependencies must be an array")
    parsed_dependencies = [
        _check_plan_dependency(item, dep_index)
        for dep_index, item in enumerate(dependencies)
    ]
    _check_deliverable_contract(value.get("deliverable_contract"))
    handoff_contract = _check_handoff_contract(
        value.get("handoff_contract"), f"streams[{index}].handoff_contract"
    )
    verifier_contracts = _check_verifier_contracts(value.get("verifier_contracts"))
    composition = value.get("composition")
    if not isinstance(composition, dict) or not composition:
        raise events.EventError(f"streams[{index}].composition must be a non-empty object")
    checkpoint_required = value.get("checkpoint_required")
    if not isinstance(checkpoint_required, bool):
        raise events.EventError(
            f"streams[{index}].checkpoint_required must be a boolean"
        )
    parsed: dict[str, object] = {
        "stream_id": stream_id,
        "deliverable": deliverable,
        "accountable": accountable,
        "owned_paths": paths,
        "dependencies": parsed_dependencies,
        "deliverable_contract": value.get("deliverable_contract"),
        "handoff_contract": handoff_contract,
        "verifier_contracts": verifier_contracts,
        "composition": composition,
        "checkpoint_required": checkpoint_required,
        "integration": integration,
    }
    for field in _THEATRE_ONLY_FIELDS:
        if field in value:
            parsed[field] = _text(value.get(field), f"streams[{index}].{field}")
    return parsed


def _validate_plan_graph(
    streams: Sequence[Mapping[str, object]],
    *,
    integration_owner: str | None,
) -> None:
    if not streams:
        raise events.EventError("plan must contain at least one stream")
    stream_ids = [cast(str, stream["stream_id"]) for stream in streams]
    if len(stream_ids) != len(set(stream_ids)):
        raise events.EventError("stream_id values must be unique")
    integration_streams = [
        stream for stream in streams if cast(bool, stream["integration"])
    ]
    if len(integration_streams) != 1:
        raise events.EventError("plan must contain exactly one integration stream")

    by_id = {cast(str, stream["stream_id"]): stream for stream in streams}
    for left_index, left in enumerate(streams):
        for right in streams[left_index + 1 :]:
            if _streams_are_theatre_only_split(left, right):
                raise events.EventError(
                    "title, model or specialism alone cannot split organisation.plan.frozen streams"
                )
    for index, stream in enumerate(streams):
        dependencies = cast(list[dict[str, object]], stream["dependencies"])
        for dep_index, dependency in enumerate(dependencies):
            predecessor_id = cast(str, dependency["stream_id"])
            if predecessor_id not in by_id:
                raise events.EventError(
                    f"streams[{index}] has missing predecessor {predecessor_id!r}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stream_id: str) -> None:
        if stream_id in visited:
            return
        if stream_id in visiting:
            raise events.EventError("plan stream graph contains a cycle")
        visiting.add(stream_id)
        stream = by_id[stream_id]
        for dependency in cast(list[dict[str, object]], stream["dependencies"]):
            visit(cast(str, dependency["stream_id"]))
        visiting.remove(stream_id)
        visited.add(stream_id)

    for stream_id in stream_ids:
        visit(stream_id)

    mutable_paths: dict[str, str] = {}
    seen_paths: dict[str, str] = {}
    for stream in streams:
        stream_id = cast(str, stream["stream_id"])
        for path in cast(list[str], stream["owned_paths"]):
            prior = seen_paths.get(path)
            if prior is not None and prior != stream_id:
                if integration_owner is None:
                    raise events.EventError(
                        "overlapping owned_paths require integration_owner"
                    )
            seen_paths[path] = stream_id
        if cast(bool, stream["integration"]):
            continue
        for path in cast(list[str], stream["owned_paths"]):
            owner = mutable_paths.get(path)
            if owner is not None and owner != cast(str, stream["accountable"]):
                if integration_owner is None:
                    raise events.EventError(
                        "overlapping owned_paths require integration_owner"
                    )
            mutable_paths[path] = cast(str, stream["accountable"])


def _check_estimate_inputs(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("estimate_inputs must be an object")
    lower = value.get("duration_lower_s")
    upper = value.get("duration_upper_s")
    if not isinstance(lower, int) or isinstance(lower, bool) or lower < 0:
        raise events.EventError("estimate_inputs.duration_lower_s must be a non-negative integer")
    if not isinstance(upper, int) or isinstance(upper, bool) or upper < lower:
        raise events.EventError(
            "estimate_inputs.duration_upper_s must be an integer >= duration_lower_s"
        )
    _text(value.get("derivation"), "estimate_inputs.derivation")
    _text(value.get("evidence_class"), "estimate_inputs.evidence_class")


def _check_prefix_anchor(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("prefix_anchor must be an object")
    line_count = value.get("line_count")
    if not isinstance(line_count, int) or isinstance(line_count, bool) or line_count < 0:
        raise events.EventError("prefix_anchor.line_count must be a non-negative integer")
    _digest(value.get("prefix_digest"), "prefix_anchor.prefix_digest")


def _check_plan_contract(data: dict[str, Any]) -> None:
    _text(data.get("plan_id"), "plan_id")
    revision = _positive_int(data.get("revision"), "revision")
    _text(data.get("commitment_id"), "commitment_id")
    _digest(data.get("commitment_digest"), "commitment_digest")
    _check_prefix_anchor(data.get("prefix_anchor"))
    streams_value = data.get("streams")
    if not isinstance(streams_value, list):
        raise events.EventError("streams must be an array")
    streams = [_check_plan_stream(item, index) for index, item in enumerate(streams_value)]
    integration_owner = data.get("integration_owner")
    if integration_owner is not None:
        _text(integration_owner, "integration_owner")
    _validate_plan_graph(
        streams,
        integration_owner=cast(str | None, integration_owner),
    )
    _check_estimate_inputs(data.get("estimate_inputs"))
    _text(data.get("budget_ref"), "budget_ref")
    _text(data.get("expires_at"), "expires_at")
    supersedes = data.get("supersedes_plan_digest")
    if revision == 1:
        if supersedes is not None:
            raise events.EventError("revision 1 must not carry supersedes_plan_digest")
    elif supersedes is None:
        raise events.EventError("revisions after 1 must carry supersedes_plan_digest")
    else:
        _digest(supersedes, "supersedes_plan_digest")
    digest = data.get("plan_digest")
    if digest is None:
        raise events.EventError("plan_digest is required")
    computed = plan_digest(data)
    if digest != computed:
        raise events.EventError("plan_digest does not match the frozen plan")


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
    if kind == PLAN_FROZEN:
        _check_plan_contract(data)
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


def freeze_plan(
    log: Path,
    plan: Mapping[str, object],
    *,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    data = dict(plan)
    if "plan_digest" not in data:
        data["plan_digest"] = plan_digest(data)
    return _append(log, PLAN_FROZEN, actor, data, ts=ts)


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
    plan_seen: set[tuple[str, int]] = set()
    plan_tips: dict[str, dict[str, Any]] = {}
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
        elif kind == PLAN_FROZEN:
            plan_id = cast(str, data["plan_id"])
            revision = cast(int, data["revision"])
            plan_seen.add((plan_id, revision))
            plan_tips[plan_id] = data
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
        elif kind == PLAN_FROZEN:
            plan_id = cast(str, data["plan_id"])
            revision = cast(int, data["revision"])
            if (plan_id, revision) in plan_seen:
                raise events.EventError(
                    f"plan {plan_id!r} revision {revision} already exists"
                )
            commitment_id = cast(str, data["commitment_id"])
            commitment_digest_value = cast(str, data["commitment_digest"])
            commitment = commitment_tips.get(commitment_id)
            if commitment is None or commitment.get("commitment_digest") != commitment_digest_value:
                raise events.EventError(
                    "organisation.plan.frozen must follow a matching commitment in the prefix"
                )
            tip = plan_tips.get(plan_id)
            if revision == 1:
                if tip is not None:
                    raise events.EventError(f"plan {plan_id!r} already has a live revision")
            else:
                if tip is None:
                    raise events.EventError(
                        f"plan {plan_id!r} has no prior revision to supersede"
                    )
                expected = tip.get("plan_digest")
                actual = data.get("supersedes_plan_digest")
                if actual != expected:
                    raise events.EventError("supersedes_plan_digest is stale")
                if _plan_is_outcome_aware_edit(tip, data):
                    raise events.EventError(
                        "outcome-aware plan edits are refused at the central writer"
                    )
            plan_tips[plan_id] = data
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
        (TURN, COMMITTED, PLAN_FROZEN, OPENED, COMPLETED),
        validate_transition,
    )


_register_transition_validator()

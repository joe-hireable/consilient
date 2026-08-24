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
WORK_MODEL_SCHEMA = "work-model.v1"
STATE = "work_item.state"
STATE_GROUP_WAITING = "WAITING"
STATE_GROUP_RUNNING = "RUNNING"
STATE_GROUP_NEEDS_YOU = "NEEDS_YOU"
STATE_GROUP_DONE = "DONE"
STATE_GROUP_DEAD = "DEAD"
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
INFORM_EFFECTS = frozenset({"duration", "quality"})
KINDS = frozenset({OPENED, COMMENT, COMPLETED, COMMITTED, STATE})
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


def state_group(state: str) -> str:
    try:
        return WORK_STATE_DEFINITIONS[state]["group"]
    except KeyError as exc:
        raise events.EventError(f"unknown work-item state {state!r}") from exc


def _check_work_state(value: object, field: str) -> str:
    state = _text(value, field)
    if state not in WORK_STATE_DEFINITIONS:
        raise events.EventError(f"{field} must be one of the declared work-item states")
    return state


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
        "target_ticket": _text(value.get("target_ticket"), f"requires[{index}].target_ticket"),
    }


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
    if not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool) or magnitude < 0:
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
        raise events.EventError(f"inform_scores[{index}].observed_sign must be -1, 0 or 1")
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


def _check_work_model_opened(data: dict[str, Any]) -> dict[str, object]:
    revision = _positive_int(data.get("revision"), "revision")
    state = _check_work_state(data.get("state"), "state")
    requires_value = data.get("requires")
    if not isinstance(requires_value, list):
        raise events.EventError("requires must be an array")
    requires = [
        _check_requires_edge(item, index) for index, item in enumerate(requires_value)
    ]
    informs_value = data.get("informs")
    if not isinstance(informs_value, list):
        raise events.EventError("informs must be an array")
    informs = [
        _check_informs_edge(item, index) for index, item in enumerate(informs_value)
    ]
    _check_blocked_overlay(data)
    return {"revision": revision, "state": state, "requires": requires, "informs": informs}


def _inform_edges_match_scores(
    informs: Sequence[Mapping[str, object]], scores: Sequence[Mapping[str, object]]
) -> None:
    if not informs:
        return
    if not scores:
        raise events.EventError("inform_scores is required when informs edges are declared")
    keyed = {
        (cast(str, edge["target_ticket"]), cast(str, edge["effect"])): edge
        for edge in informs
    }
    seen: set[tuple[str, str]] = set()
    for index, score in enumerate(scores):
        parsed = _check_inform_score(score, index)
        key = (cast(str, parsed["target_ticket"]), cast(str, parsed["effect"]))
        if key not in keyed:
            raise events.EventError(
                f"inform_scores[{index}] does not match a declared informs edge"
            )
        seen.add(key)
    if seen != set(keyed):
        raise events.EventError("every informs edge must be scored on close")


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


def _timestamp(value: object, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise events.EventError(f"{field} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise events.EventError(f"{field} must carry an explicit offset")
    return text


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


def _check_native_item(data: Mapping[str, object]) -> None:
    _positive_int(data.get("revision"), "revision")
    _text(data.get("plan_id"), "plan_id")
    _digest(data.get("plan_digest"), "plan_digest")
    _text(data.get("stream_id"), "stream_id")
    _text(data.get("goal_text"), "goal_text")
    _digest(data.get("success_digest"), "success_digest")
    _check_incumbent(data.get("incumbent"))
    _check_deliverable_contract(data.get("deliverable_contract"))
    _text(data.get("accountable"), "accountable")
    _check_authority_ref(data.get("authority_ref"))
    _check_verifier_contracts(data.get("verifier_contracts"))
    _check_native_dependencies(data.get("dependencies"))
    _string_list(data.get("owned_paths"), "owned_paths")
    _text(data.get("budget_ref"), "budget_ref")
    _timestamp(data.get("expires_at"), "expires_at")
    _check_exposure_contract(data.get("exposure_contract"))
    composition = data.get("composition")
    if not isinstance(composition, dict) or not composition:
        raise events.EventError("composition must be a non-empty object")


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


def _check_native_pause(data: Mapping[str, object]) -> None:
    _text(data.get("ticket"), "ticket")
    _positive_int(data.get("revision"), "revision")
    _digest(data.get("plan_digest"), "plan_digest")
    if data.get("cause") != "commitment_paused":
        raise events.EventError("native pause cause must be commitment_paused")


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
    _string_list(data.get("source_turn_ids"), "source_turn_ids")
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
    if kind == NATIVE_ATTEMPTED:
        _check_native_attempt(data)
        return
    if kind == NATIVE_COMMITMENT_PAUSED:
        _check_native_pause(data)
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
            _check_native_item(data)
        elif schema == WORK_MODEL_SCHEMA:
            _check_work_model_opened(data)
        elif schema is not None:
            raise events.EventError(f"unsupported item_schema {schema!r}")
    if kind == COMMENT:
        evidence_class = data.get("evidence_class")
        if not isinstance(evidence_class, str) or not evidence_class.strip():
            raise events.EventError(
                "work_item.comment must carry a non-empty evidence_class"
            )
    if kind == STATE:
        _check_work_state(data.get("state"), "state")
        _check_blocked_overlay(data)
    if kind == COMPLETED:
        inform_scores = data.get("inform_scores")
        if inform_scores is not None:
            if not isinstance(inform_scores, list):
                raise events.EventError("inform_scores must be an array when present")
            for index, item in enumerate(inform_scores):
                _check_inform_score(item, index)


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


def open_work_model_item(
    log: Path,
    *,
    ticket: str,
    accountable: str,
    state: str,
    revision: int = 1,
    requires: list[dict[str, str]] | None = None,
    informs: list[dict[str, object]] | None = None,
    actor: str = DEFAULT_ACTOR,
    is_blocked: bool | None = None,
    blocked_reason: str | None = None,
) -> events.EventPayload:
    extra: dict[str, Any] = {
        "item_schema": WORK_MODEL_SCHEMA,
        "revision": revision,
        "state": state,
        "requires": requires or [],
        "informs": informs or [],
    }
    if is_blocked is not None:
        extra["is_blocked"] = is_blocked
    if blocked_reason is not None:
        extra["blocked_reason"] = blocked_reason
    return open_item(
        log,
        ticket=ticket,
        accountable=accountable,
        actor=actor,
        extra=extra,
    )


def record_state(
    log: Path,
    *,
    ticket: str,
    state: str,
    actor: str = DEFAULT_ACTOR,
    is_blocked: bool | None = None,
    blocked_reason: str | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket, "state": state}
    if is_blocked is not None:
        data["is_blocked"] = is_blocked
    if blocked_reason is not None:
        data["blocked_reason"] = blocked_reason
    return _append(log, STATE, actor, data)


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


def open_native_item(
    log: Path,
    item: Mapping[str, object],
    *,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    """Append one frozen native work item through the authoritative writer."""
    data = dict(item)
    data["item_schema"] = NATIVE_SCHEMA
    return _append(log, OPENED, actor, data, ts=ts)


def record_native_attempt(
    log: Path,
    *,
    ticket: str,
    revision: int,
    plan_digest: str,
    attempt_id: str,
    run_id: str,
    claimed_paths: list[str],
    opened_at: str,
    expires_at: str,
    harness: str,
    model: str,
    family: str,
    pool: str,
    capability_context_digest: str,
    candidate_ordinal: int,
    exposure_state: str,
    predecessor_bindings: list[dict[str, object]],
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    return _append(
        log,
        NATIVE_ATTEMPTED,
        actor,
        {
            "ticket": ticket,
            "revision": revision,
            "plan_digest": plan_digest,
            "attempt_id": attempt_id,
            "run_id": run_id,
            "claimed_paths": claimed_paths,
            "opened_at": opened_at,
            "expires_at": expires_at,
            "harness": harness,
            "model": model,
            "family": family,
            "pool": pool,
            "capability_context_digest": capability_context_digest,
            "candidate_ordinal": candidate_ordinal,
            "exposure_state": exposure_state,
            "predecessor_bindings": predecessor_bindings,
        },
        ts=ts,
    )


def pause_native_item(
    log: Path,
    *,
    ticket: str,
    revision: int,
    plan_digest: str,
    cause: str,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    return _append(
        log,
        NATIVE_COMMITMENT_PAUSED,
        actor,
        {
            "ticket": ticket,
            "revision": revision,
            "plan_digest": plan_digest,
            "cause": cause,
        },
        ts=ts,
    )


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
    log: Path,
    *,
    ticket: str,
    actor: str = DEFAULT_ACTOR,
    extra: dict[str, Any] | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket}
    if extra is not None:
        reserved = set(data)
        collision = reserved & set(extra)
        if collision:
            raise events.EventError(
                f"work_item.completed extra fields may not override {sorted(collision)}"
            )
        data.update(extra)
    return _append(log, COMPLETED, actor, data)


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


def _validate_native_plan_binding(
    item: Mapping[str, object],
    plans_by_digest: Mapping[str, Mapping[str, Any]],
    native_by_ticket: Mapping[tuple[str, int], Mapping[str, Any]],
) -> None:
    digest = cast(str, item["plan_digest"])
    plan = plans_by_digest.get(digest)
    if plan is None or plan.get("plan_id") != item["plan_id"]:
        raise events.EventError("native item requires a matching frozen plan")
    streams = cast(list[dict[str, Any]], plan["streams"])
    _validate_plan_graph(
        streams, integration_owner=cast(str | None, plan.get("integration_owner"))
    )
    stream = next(
        (
            candidate
            for candidate in streams
            if candidate["stream_id"] == item["stream_id"]
        ),
        None,
    )
    if stream is None:
        raise events.EventError("native item stream is absent from its frozen plan")
    for field in (
        "deliverable_contract",
        "accountable",
        "verifier_contracts",
        "owned_paths",
        "composition",
    ):
        if item[field] != stream[field]:
            raise events.EventError(
                f"native item {field} does not match its frozen stream"
            )
    dependencies = cast(list[dict[str, Any]], item["dependencies"])
    expected = cast(list[dict[str, Any]], stream["dependencies"])
    if len(dependencies) != len(expected):
        raise events.EventError(
            "native item dependencies do not match its frozen stream"
        )
    for dependency, expected_dependency in zip(dependencies, expected, strict=True):
        predecessor = native_by_ticket.get(
            (cast(str, dependency["ticket"]), cast(int, dependency["revision"]))
        )
        if predecessor is None:
            raise events.EventError("native item has a missing predecessor")
        if (
            predecessor.get("plan_digest") != digest
            or predecessor.get("stream_id") != expected_dependency["stream_id"]
            or dependency["revision"] != expected_dependency["revision"]
            or dependency["handoff_contract_digest"]
            != expected_dependency["handoff_contract_digest"]
        ):
            raise events.EventError(
                "native item dependency does not match its frozen plan"
            )
        predecessor_stream = next(
            candidate
            for candidate in streams
            if candidate["stream_id"] == predecessor["stream_id"]
        )
        if (
            predecessor_stream["handoff_contract"]["digest"]
            != dependency["handoff_contract_digest"]
            or not predecessor_stream["verifier_contracts"]
        ):
            raise events.EventError(
                "native item dependency has no matching hand-off verifier"
            )


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
    plans_by_digest: dict[str, dict[str, Any]] = {}
    opened_by_ticket: dict[str, dict[str, Any]] = {}
    work_model_informs: dict[str, list[dict[str, object]]] = {}
    work_model_state: dict[str, dict[str, Any]] = {}
    native_by_ticket: dict[tuple[str, int], dict[str, Any]] = {}

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
            plans_by_digest[cast(str, data["plan_digest"])] = data
        elif kind == OPENED:
            ticket = cast(str, data["ticket"])
            opened_by_ticket[ticket] = data
            if _opened_schema(data) == WORK_MODEL_SCHEMA:
                work_model_informs[ticket] = cast(
                    list[dict[str, object]], data.get("informs", [])
                )
                work_model_state[ticket] = data
            if _opened_schema(data) == NATIVE_SCHEMA:
                native_by_ticket[(ticket, cast(int, data["revision"]))] = data
        elif kind == STATE:
            ticket = cast(str, data["ticket"])
            if ticket not in opened_by_ticket:
                raise events.EventError(
                    f"work_item.state references unknown ticket {ticket!r}"
                )
            work_model_state[ticket] = data
        elif kind == COMPLETED:
            ticket = cast(str, data["ticket"])
            informs = work_model_informs.get(ticket, [])
            if informs:
                scores = data.get("inform_scores", [])
                if not isinstance(scores, list):
                    raise events.EventError(
                        "inform_scores is required when informs edges are declared"
                    )
                _inform_edges_match_scores(informs, scores)

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
            ):
                if not _source_turns_authenticated(data, turns):
                    raise events.EventError(
                        "protected commitments require authenticated source turns"
                    )
                conversation_id = cast(str, data["conversation_id"])
                source_turn_ids = cast(list[str], data["source_turn_ids"])
                texts_by_turn = {
                    turn_id: cast(str, turns[f"{conversation_id}:{turn_id}"]["text"])
                    for turn_id in source_turn_ids
                }
                if data.get("source_turn_digest") != source_turn_digest(
                    conversation_id, source_turn_ids, texts_by_turn
                ):
                    raise events.EventError(
                        "source_turn_digest does not match the source turns"
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
            plans_by_digest[cast(str, data["plan_digest"])] = data
        elif kind == COMPLETED:
            ticket = cast(str, data["ticket"])
            opened = opened_by_ticket.get(ticket)
            if opened is None:
                continue
            informs = work_model_informs.get(ticket, [])
            if informs:
                scores = data.get("inform_scores", [])
                if not isinstance(scores, list):
                    raise events.EventError(
                        "inform_scores is required when informs edges are declared"
                    )
                _inform_edges_match_scores(informs, scores)
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
            ticket = cast(str, data["ticket"])
            opened_by_ticket[ticket] = data
            if _opened_schema(data) == WORK_MODEL_SCHEMA:
                work_model_informs[ticket] = cast(
                    list[dict[str, object]], data.get("informs", [])
                )
                work_model_state[ticket] = data
            if _opened_schema(data) == NATIVE_SCHEMA:
                native_key = (ticket, cast(int, data["revision"]))
                if native_key in native_by_ticket:
                    raise events.EventError("native work-item revision already exists")
                _validate_native_plan_binding(data, plans_by_digest, native_by_ticket)
                native_by_ticket[native_key] = data
        elif kind == STATE:
            ticket = cast(str, data["ticket"])
            if ticket not in opened_by_ticket:
                raise events.EventError(
                    f"work_item.state references unknown ticket {ticket!r}"
                )
            work_model_state[ticket] = data
        elif kind == NATIVE_ATTEMPTED:
            native_key = (cast(str, data["ticket"]), cast(int, data["revision"]))
            opened = native_by_ticket.get(native_key)
            if opened is None:
                raise events.EventError("native attempt requires an opened native item")
            if data["plan_digest"] != opened["plan_digest"]:
                raise events.EventError(
                    "native attempt plan_digest does not match its item"
                )
            if data["claimed_paths"] != opened["owned_paths"]:
                raise events.EventError(
                    "native attempt claimed_paths do not match owned_paths"
                )
        elif kind == NATIVE_COMMITMENT_PAUSED:
            native_key = (cast(str, data["ticket"]), cast(int, data["revision"]))
            opened = native_by_ticket.get(native_key)
            if opened is None:
                raise events.EventError("native pause requires an opened native item")
            if data["plan_digest"] != opened["plan_digest"]:
                raise events.EventError(
                    "native pause plan_digest does not match its item"
                )


def _register_transition_validator() -> None:
    events.register_transition_validator(
        (
            TURN,
            COMMITTED,
            PLAN_FROZEN,
            OPENED,
            STATE,
            COMPLETED,
            NATIVE_ATTEMPTED,
            NATIVE_COMMITMENT_PAUSED,
        ),
        validate_transition,
    )


_register_transition_validator()

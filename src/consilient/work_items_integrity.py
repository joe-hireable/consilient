"""Rules that reject a record whose every field is already well-formed.

A plan can name streams that all parse individually and still be wrong — two streams
sharing an identifier, no integration stream or several, a dependency on a stream that
does not exist, a cycle, two mutable streams claiming the same path with nobody
accountable for the overlap. Those are decided over the whole set of streams at once,
because no single stream can see them.

Two refusals are worth naming. A pair of streams differing only in title, model or
specialism is refused as a theatre-only split — headcount dressed as structure, adding
no different class of facts. And a plan dependency may not carry an artefact digest, a
verifier receipt or an observed outcome: a plan is frozen before the work runs, so a
dependency that already knows the answer was written after it.

The rest is cross-field consistency inside one record. A commitment digest must
reproduce over the contract's own frozen fields; a supersession must be absent at
revision 1 and present after it; an incumbent must be named with its source, retrieval
date and the check that would kill it; a state must be one of the declared work states;
and every informs edge declared when an item opened must carry a score when it closes."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any, cast
from . import events
from .work_items_vocabulary import (
    _FORBIDDEN_PLAN_DEPENDENCY_FIELDS,
    _THEATRE_ONLY_FIELDS,
    _check_inform_score,
    _positive_int,
    _string_list,
    _text,
)

from .work_items_contracts import (
    WORK_STATE_DEFINITIONS,
    _check_authority_ref,
    _check_deliverable_contract,
    _check_verifier_contracts,
    _digest,
    _stream_identity,
    commitment_digest,
    handoff_contract_digest,
    plan_digest,
    source_turn_digest,
    success_digest,
)


__all__ = [
    "WORK_STATE_DEFINITIONS",
    "_FORBIDDEN_PLAN_DEPENDENCY_FIELDS",
    "_THEATRE_ONLY_FIELDS",
    "_check_authority_ref",
    "_check_deliverable_contract",
    "_check_inform_score",
    "_check_verifier_contracts",
    "_digest",
    "_positive_int",
    "_stream_identity",
    "_string_list",
    "_text",
    "commitment_digest",
    "handoff_contract_digest",
    "plan_digest",
    "source_turn_digest",
    "state_group",
    "success_digest",
]


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


def _inform_edges_match_scores(
    informs: Sequence[Mapping[str, object]], scores: Sequence[Mapping[str, object]]
) -> None:
    if not informs:
        return
    if not scores:
        raise events.EventError(
            "inform_scores is required when informs edges are declared"
        )
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
        "revision": _positive_int(
            value.get("revision"), f"dependencies[{index}].revision"
        ),
        "handoff_contract_digest": _digest(
            value.get("handoff_contract_digest"),
            f"dependencies[{index}].handoff_contract_digest",
        ),
    }


def _streams_are_theatre_only_split(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    if _stream_identity(left) != _stream_identity(right):
        return False
    if left.get("stream_id") == right.get("stream_id"):
        return False
    return any(field in left or field in right for field in _THEATRE_ONLY_FIELDS)


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


def _check_prefix_anchor(value: object) -> None:
    if not isinstance(value, dict):
        raise events.EventError("prefix_anchor must be an object")
    line_count = value.get("line_count")
    if (
        not isinstance(line_count, int)
        or isinstance(line_count, bool)
        or line_count < 0
    ):
        raise events.EventError(
            "prefix_anchor.line_count must be a non-negative integer"
        )
    _digest(value.get("prefix_digest"), "prefix_anchor.prefix_digest")


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


def _check_native_pause(data: Mapping[str, object]) -> None:
    _text(data.get("ticket"), "ticket")
    _positive_int(data.get("revision"), "revision")
    _digest(data.get("plan_digest"), "plan_digest")
    if data.get("cause") != "commitment_paused":
        raise events.EventError("native pause cause must be commitment_paused")


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
        raise events.EventError(
            "success_digest does not match success_criteria and non_goals"
        )
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
            raise events.EventError(
                "question_turn_id must be absent when question_count is 0"
            )
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

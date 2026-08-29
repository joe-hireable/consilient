"""Whole payloads, validated against the schema they declare.

`work_item.opened` carries an `item_schema`, and each schema has its own shape: a native
item binds to a frozen plan and to one stream inside it, while a work-model item carries
a revision, a state and its requires and informs edges. `organisation.plan.frozen` is
validated here as a complete plan — every stream parsed, the graph then checked as a
whole, and the plan digest recomputed over what was actually frozen.

`_validate_native_plan_binding` is the strictest of them. A native item may not restate
its plan: its deliverable contract, accountable owner, verifier contracts, owned paths
and composition must equal the frozen stream's, its dependencies must match that
stream's dependencies one for one, and every predecessor must already exist as an opened
native item under the same plan digest with a hand-off verifier attached. A native item
that disagrees with the plan it claims is refused rather than reconciled.

These functions read a payload and raise. They do not write, and they consult nothing
beyond the plans and items handed to them."""

from __future__ import annotations
from collections.abc import Mapping
from typing import Any, cast
from . import events
from .work_items_vocabulary import (
    _THEATRE_ONLY_FIELDS,
    _check_informs_edge,
    _positive_int,
    _string_list,
    _text,
)

from .work_items_contracts import (
    _check_authority_ref,
    _check_blocked_overlay,
    _check_deliverable_contract,
    _check_estimate_inputs,
    _check_exposure_contract,
    _check_native_dependencies,
    _check_requires_edge,
    _check_verifier_contracts,
    _digest,
    _timestamp,
    commitment_digest,
    handoff_contract_digest,
    plan_digest,
    success_digest,
)

from .work_items_integrity import (
    _check_handoff_contract,
    _check_incumbent,
    _check_plan_dependency,
    _check_prefix_anchor,
    _check_work_state,
    _validate_plan_graph,
)


__all__ = [
    "_THEATRE_ONLY_FIELDS",
    "_check_authority_ref",
    "_check_blocked_overlay",
    "_check_deliverable_contract",
    "_check_estimate_inputs",
    "_check_exposure_contract",
    "_check_handoff_contract",
    "_check_incumbent",
    "_check_informs_edge",
    "_check_native_dependencies",
    "_check_plan_dependency",
    "_check_prefix_anchor",
    "_check_requires_edge",
    "_check_verifier_contracts",
    "_check_work_state",
    "_digest",
    "_positive_int",
    "_string_list",
    "_text",
    "_timestamp",
    "_validate_plan_graph",
    "commitment_digest",
    "handoff_contract_digest",
    "plan_digest",
    "success_digest",
]


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
    return {
        "revision": revision,
        "state": state,
        "requires": requires,
        "informs": informs,
    }


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
        raise events.EventError(
            f"streams[{index}].composition must be a non-empty object"
        )
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


def _check_plan_contract(data: dict[str, Any]) -> None:
    _text(data.get("plan_id"), "plan_id")
    revision = _positive_int(data.get("revision"), "revision")
    _text(data.get("commitment_id"), "commitment_id")
    _digest(data.get("commitment_digest"), "commitment_digest")
    _check_prefix_anchor(data.get("prefix_anchor"))
    streams_value = data.get("streams")
    if not isinstance(streams_value, list):
        raise events.EventError("streams must be an array")
    streams = [
        _check_plan_stream(item, index) for index, item in enumerate(streams_value)
    ]
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

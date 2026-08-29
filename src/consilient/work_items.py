"""Work-item events in the authoritative trajectory.

The checks and writers this file once held now sit beside it, bottom upwards.
`work_items_vocabulary.py` holds the event kind, actor, schema and state names, the
single-field readers and the canonical digest encoding. `work_items_contracts.py` holds
the contract clauses, the work-state table and the digest functions that freeze a
record. `work_items_integrity.py` holds the plan-graph and cross-field rules.
`work_items_schemas.py` validates a whole payload against the schema it declares.
`work_items_transition.py` holds `validate_transition`. `work_items_writer.py` holds
`validate`, `check_event_contract` and every appending writer. What remains here are the
four entry points that open or freeze a record — `commit_request`, `freeze_plan`,
`open_native_item` and `open_work_model_item`."""

from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from . import events
from .work_items_vocabulary import (
    COMMITTED,
    DEFAULT_ACTOR,
    INTAKE_ACTOR,
    NATIVE_SCHEMA,
    OPENED,
    PLAN_FROZEN,
    WORK_MODEL_SCHEMA,
)

from .work_items_contracts import (
    KINDS,
    STATE_GROUPS,
    WORK_STATE_DEFINITIONS,
    _check_turn_contract,
    _digest,
    _timestamp,
    commitment_digest,
    handoff_contract_digest,
    plan_digest,
    source_turn_digest,
    success_digest,
)

from .work_items_integrity import (
    state_group,
)


from .work_items_transition import (
    validate_transition,
)

from .work_items_vocabulary import (
    COMMENT,
    COMPLETED,
    DISPATCH_CLAIM_SCHEMA,
    INFORM_EFFECTS,
    NATIVE_ATTEMPTED,
    NATIVE_COMMITMENT_PAUSED,
    STATE,
    STATE_GROUP_DEAD,
    STATE_GROUP_DONE,
    STATE_GROUP_NEEDS_YOU,
    STATE_GROUP_RUNNING,
    STATE_GROUP_WAITING,
    TURN,
    TURN_ROLES,
    _DIGEST,
    _string_list,
    _text,
    decision_readiness,
)

from .work_items_writer import (
    _append,
    _register_transition_validator,
    check_event_contract,
    comment,
    complete_item,
    open_item,
    pause_native_item,
    record_native_attempt,
    record_state,
    seal_turn,
    validate,
)

__all__ = [
    "COMMENT",
    "COMMITTED",
    "COMPLETED",
    "DEFAULT_ACTOR",
    "DISPATCH_CLAIM_SCHEMA",
    "INFORM_EFFECTS",
    "INTAKE_ACTOR",
    "KINDS",
    "NATIVE_ATTEMPTED",
    "NATIVE_COMMITMENT_PAUSED",
    "NATIVE_SCHEMA",
    "OPENED",
    "PLAN_FROZEN",
    "STATE",
    "STATE_GROUPS",
    "STATE_GROUP_DEAD",
    "STATE_GROUP_DONE",
    "STATE_GROUP_NEEDS_YOU",
    "STATE_GROUP_RUNNING",
    "STATE_GROUP_WAITING",
    "TURN",
    "TURN_ROLES",
    "WORK_MODEL_SCHEMA",
    "WORK_STATE_DEFINITIONS",
    "_DIGEST",
    "_append",
    "_check_turn_contract",
    "_digest",
    "_register_transition_validator",
    "_string_list",
    "_text",
    "_timestamp",
    "check_event_contract",
    "comment",
    "commit_request",
    "commitment_digest",
    "complete_item",
    "decision_readiness",
    "freeze_plan",
    "handoff_contract_digest",
    "open_item",
    "open_native_item",
    "open_work_model_item",
    "pause_native_item",
    "plan_digest",
    "record_native_attempt",
    "record_state",
    "seal_turn",
    "source_turn_digest",
    "state_group",
    "success_digest",
    "validate",
    "validate_transition",
]


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


_register_transition_validator()

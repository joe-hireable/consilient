"""What a batch of candidate events may add to an accepted prefix.

Every check here needs two events to see it. A conversation turn may not repeat an
identifier already in the log. A commitment or a plan at revision 1 may not follow a
live revision, and a later revision must supersede the current tip by its exact digest —
a stale supersession is refused, so two writers cannot both edit from the same tip. A
frozen plan must follow the matching commitment, and a plan revision that changes a
verifier or hand-off contract is refused outright at the central writer, because a plan
edited once outcomes are known is a plan fitted to them.

Protected commitments are held harder still. Where the authority reference reserves the
decision to the principal, every source turn must be present in the trajectory and
marked authenticated, and the recorded source-turn digest must reproduce over their
texts — an instruction cannot be attributed to a person who cannot be shown to have sent
it.

Native items, attempts and pauses are bound to what came before. An attempt must match
its item's plan digest and claim exactly the paths the item owns, a pause must name an
opened item, and a dispatch claim may not close carrying native task-closure evidence it
never produced."""

from __future__ import annotations
from collections.abc import Sequence
from typing import Any, cast
from . import events
from .work_items_vocabulary import (
    COMMITTED,
    COMPLETED,
    DISPATCH_CLAIM_SCHEMA,
    NATIVE_ATTEMPTED,
    NATIVE_COMMITMENT_PAUSED,
    NATIVE_SCHEMA,
    OPENED,
    PLAN_FROZEN,
    STATE,
    TURN,
    WORK_MODEL_SCHEMA,
    _NATIVE_CLOSURE_FIELDS,
    _event_mapping,
    _is_dispatch_claim_data,
    _opened_schema,
    _plan_is_outcome_aware_edit,
    _source_turns_authenticated,
)

from .work_items_contracts import (
    _turns_by_id,
    commitment_digest,
    plan_digest,
    source_turn_digest,
)

from .work_items_integrity import (
    _inform_edges_match_scores,
)

from .work_items_schemas import (
    _validate_native_plan_binding,
)


__all__ = [
    "COMMITTED",
    "COMPLETED",
    "DISPATCH_CLAIM_SCHEMA",
    "NATIVE_ATTEMPTED",
    "NATIVE_COMMITMENT_PAUSED",
    "NATIVE_SCHEMA",
    "OPENED",
    "PLAN_FROZEN",
    "STATE",
    "TURN",
    "WORK_MODEL_SCHEMA",
    "_NATIVE_CLOSURE_FIELDS",
    "_event_mapping",
    "_inform_edges_match_scores",
    "_is_dispatch_claim_data",
    "_opened_schema",
    "_plan_is_outcome_aware_edit",
    "_source_turns_authenticated",
    "_turns_by_id",
    "_validate_native_plan_binding",
    "commitment_digest",
    "plan_digest",
    "source_turn_digest",
    "validate_transition",
]


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
            if (
                commitment is None
                or commitment.get("commitment_digest") != commitment_digest_value
            ):
                raise events.EventError(
                    "organisation.plan.frozen must follow a matching commitment in the prefix"
                )
            tip = plan_tips.get(plan_id)
            if revision == 1:
                if tip is not None:
                    raise events.EventError(
                        f"plan {plan_id!r} already has a live revision"
                    )
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
                or (_opened_schema(opened) is None and _is_dispatch_claim_data(opened))
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

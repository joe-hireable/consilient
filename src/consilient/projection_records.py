"""Captured records, the temporal heads they form, and how a cited reading is
classified.

A capture projects a fact row, a relation row for every supersedes and invalidates
reference it carries, and a defect row wherever a reference cannot be honoured -- a
target that is not in the log, a target of the wrong kind, or a digest that does not
match the event it names. Where the workspace is known, the object the record points at
is read back and checked against its recorded digest and byte count, so a file that has
gone missing or been altered since capture shows up as a defect rather than as a clean
row.

The temporal view folds those facts into heads per source, and it reports rather than
resolves. Two live heads for one source are returned as contested, not silently ranked;
invalidated facts stay in the view instead of disappearing from it. Deciding between
them is a judgement, and a projection is not the place a judgement is made.

The reading classifier belongs with this code because it does the same work facing the
other way. It resolves an evidence reference to the immutable earlier event it names,
and where it cannot -- missing, mismatched digest, not earlier than the decision, no
acquisition metadata, unknown derivation roots -- it records why in words. A reference
that fails to resolve is never quietly dropped; the reason it did not count is part of
the answer."""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import cast
from .events import (
    EventError,
    KNOWLEDGE_RETRIEVED_KIND,
    RECORD_CAPTURED_KIND,
    VERIFICATION_OUTCOME_KIND,
    Event,
    resolve_reference,
)

from .projection_rows import (
    _Reading,
    _event_sha256,
    _insert_record_defect,
    _object_status,
    _polarity,
    _quarantine_relational,
    _record_fact_dict,
)

__all__ = [
    "_Reading",
    "_event_sha256",
    "_insert_record_defect",
    "_object_status",
    "_polarity",
    "_quarantine_relational",
    "_record_fact_dict",
    "record_temporal_views",
]


def _apply_record_captured(
    conn: sqlite3.Connection,
    position: int,
    event: Event,
    workspace: Path | None,
    event_index: dict[str, Event],
) -> None:
    data = event.data
    record_id = cast(str, data["record_id"])
    digest = cast(str, data["digest"])
    byte_count = int(data["byte_count"])
    object_locator = cast(str, data["object_locator"])
    valid_time = cast(dict[str, object], data["valid_time"])
    object_status = _object_status(workspace, object_locator, digest, byte_count)
    if conn.execute(
        "SELECT 1 FROM record_facts WHERE record_id = ?", (record_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate record_id {record_id!r} at position {position}",
        )
        return
    conn.execute(
        "INSERT INTO record_facts (position, record_id, event_id, event_kind, event_sha256,"
        " digest, kind, actor, work_item, capability_contract, source, valid_from, valid_to,"
        " object_locator, byte_count, consent_purpose, retention_class, object_status)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            record_id,
            event.raw["event_id"],
            event.kind,
            _event_sha256(event.raw),
            digest,
            data["media_type"],
            event.actor,
            event.data.get("task"),
            event.data.get("capability_contract"),
            data["source"],
            valid_time["from"],
            valid_time.get("to"),
            object_locator,
            byte_count,
            data["consent_purpose"],
            data["retention_class"],
            object_status,
        ),
    )
    if object_status == "missing":
        _insert_record_defect(
            conn,
            position,
            record_id,
            "object_missing",
            {"record_id": record_id, "object_locator": object_locator},
        )
    elif object_status == "corrupt":
        _insert_record_defect(
            conn,
            position,
            record_id,
            "object_corrupt",
            {"record_id": record_id, "object_locator": object_locator},
        )

    relation_id = int(
        conn.execute("SELECT COALESCE(MAX(id), 0) FROM record_relations").fetchone()[0]
    )
    for relation in ("supersedes", "invalidates"):
        for reference in data[relation]:
            relation_id += 1
            target_event_id = cast(str, reference["event_id"])
            target_event_kind = cast(str, reference["event_kind"])
            target_event_sha256 = cast(str, reference["event_sha256"])
            target = event_index.get(target_event_id)
            relation_status = "ok"
            target_record_id: str | None = None
            if target is None:
                relation_status = "missing_target"
                _insert_record_defect(
                    conn,
                    position,
                    record_id,
                    "relation_missing_target",
                    {
                        "record_id": record_id,
                        "relation": relation,
                        "target_event_id": target_event_id,
                    },
                )
            elif target.kind != RECORD_CAPTURED_KIND:
                relation_status = "malformed_target"
                _insert_record_defect(
                    conn,
                    position,
                    record_id,
                    "relation_malformed_target",
                    {
                        "record_id": record_id,
                        "relation": relation,
                        "target_event_id": target_event_id,
                    },
                )
            elif _event_sha256(target.raw) != target_event_sha256:
                relation_status = "digest_mismatch"
                _insert_record_defect(
                    conn,
                    position,
                    record_id,
                    "relation_digest_mismatch",
                    {
                        "record_id": record_id,
                        "relation": relation,
                        "target_event_id": target_event_id,
                    },
                )
            else:
                target_record_id = cast(str, target.data["record_id"])
            conn.execute(
                "INSERT INTO record_relations (id, position, record_id, relation,"
                " target_event_id, target_event_kind, target_event_sha256,"
                " target_record_id, relation_status)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    relation_id,
                    position,
                    record_id,
                    relation,
                    target_event_id,
                    target_event_kind,
                    target_event_sha256,
                    target_record_id,
                    relation_status,
                ),
            )


def record_temporal_views(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """Deterministic temporal record heads grouped by source."""
    conn.row_factory = sqlite3.Row
    facts = [
        _record_fact_dict(row)
        for row in conn.execute(
            "SELECT * FROM record_facts ORDER BY position, record_id"
        )
    ]
    if not facts:
        return []

    by_record_id = {cast(str, fact["record_id"]): fact for fact in facts}
    by_source: dict[str, list[dict[str, object]]] = {}
    for fact in facts:
        by_source.setdefault(cast(str, fact["source"]), []).append(fact)

    superseded_by: dict[str, str] = {}
    invalidated: set[str] = set()
    invalidation_only: set[str] = set()
    has_supersedes: set[str] = set()
    has_invalidates: set[str] = set()
    for row in conn.execute(
        "SELECT record_id, relation, target_record_id, relation_status"
        " FROM record_relations ORDER BY position, id"
    ):
        source = cast(str, row["record_id"])
        if row["relation"] == "supersedes":
            has_supersedes.add(source)
        elif row["relation"] == "invalidates":
            has_invalidates.add(source)
        if row["relation_status"] != "ok" or row["target_record_id"] is None:
            continue
        target = cast(str, row["target_record_id"])
        if row["relation"] == "supersedes":
            superseded_by[target] = source
        elif row["relation"] == "invalidates":
            invalidated.add(target)
    invalidation_only = has_invalidates - has_supersedes

    defects_by_record: dict[str, list[dict[str, object]]] = {}
    for row in conn.execute(
        "SELECT record_id, defect_kind, detail FROM record_defects ORDER BY id"
    ):
        if row["record_id"] is None:
            continue
        record_id = cast(str, row["record_id"])
        detail = json.loads(cast(str, row["detail"]))
        if row["defect_kind"] == "object_missing":
            payload = {
                "kind": "object_missing",
                "record_id": detail.get("record_id", record_id),
                "object_locator": detail["object_locator"],
            }
        elif row["defect_kind"] == "object_corrupt":
            payload = {
                "kind": "object_corrupt",
                "record_id": detail.get("record_id", record_id),
                "object_locator": detail["object_locator"],
            }
        else:
            payload = {
                "kind": row["defect_kind"],
                "record_id": record_id,
                "detail": detail,
            }
        defects_by_record.setdefault(record_id, []).append(payload)

    views: list[dict[str, object]] = []
    for source in sorted(by_source):
        group = by_source[source]
        record_ids = {cast(str, fact["record_id"]) for fact in group}
        tips = [
            fact for fact in group if cast(str, fact["record_id"]) not in superseded_by
        ]
        tip_ids = {cast(str, fact["record_id"]) for fact in tips}
        group_invalidated = [
            by_record_id[record_id] for record_id in sorted(record_ids & invalidated)
        ]
        defects: list[dict[str, object]] = []
        for record_id in sorted(record_ids):
            defects.extend(defects_by_record.get(record_id, []))

        blocked = any(cast(str, fact["object_status"]) != "ok" for fact in tips) or any(
            defects_by_record.get(cast(str, fact["record_id"])) for fact in tips
        )

        eligible_tips = [
            fact
            for fact in tips
            if cast(str, fact["record_id"]) not in invalidated
            and cast(str, fact["record_id"]) not in invalidation_only
            and cast(str, fact["object_status"]) == "ok"
            and not defects_by_record.get(cast(str, fact["record_id"]))
        ]

        if len(eligible_tips) == 1:
            current = eligible_tips[0]
            history_ids: list[str] = []
            cursor = cast(str, current["record_id"])
            while True:
                predecessors = [
                    record_id
                    for record_id, successor in superseded_by.items()
                    if successor == cursor
                ]
                if len(predecessors) != 1:
                    break
                predecessor = predecessors[0]
                history_ids.append(predecessor)
                cursor = predecessor
            history = [by_record_id[record_id] for record_id in history_ids]
            views.append(
                {
                    "source": source,
                    "status": "current",
                    "current": current,
                    "history": history,
                    "contested_heads": [],
                    "invalidated": group_invalidated,
                    "defects": defects,
                }
            )
            continue

        if group_invalidated and not eligible_tips:
            status = "invalidated"
        elif len(eligible_tips) > 1 or (len(tip_ids) > 1 and blocked):
            status = "contested"
        elif len(eligible_tips) == 0 and tips:
            status = "contested" if blocked else "invalidated"
        else:
            status = "contested" if len(tips) > 1 else "current"

        contested_heads = sorted(
            eligible_tips if len(eligible_tips) > 1 else tips,
            key=lambda fact: (
                cast(int, fact["position"]),
                cast(str, fact["record_id"]),
            ),
        )
        views.append(
            {
                "source": source,
                "status": status,
                "current": None,
                "history": [],
                "contested_heads": contested_heads,
                "invalidated": group_invalidated,
                "defects": defects,
            }
        )

    return views


def _classify_reading(
    reference: object, ordered: list[Event], consumer: Event
) -> _Reading:
    if not isinstance(reference, dict):
        reading = _Reading({"event_id": "", "event_kind": "", "event_sha256": ""})
        reading.reasons.append("malformed evidence reference")
        return reading
    ref = {
        "event_id": str(reference.get("event_id", "")),
        "event_kind": str(reference.get("event_kind", "")),
        "event_sha256": str(reference.get("event_sha256", "")),
    }
    reading = _Reading(ref)
    try:
        resolved = resolve_reference(reference, ordered, before=consumer)
    except EventError as exc:
        detail = str(exc)
        if "not earlier" in detail:
            reading.reasons.append("not earlier than the decision")
        elif "event_sha256" in detail:
            reading.reasons.append("mismatched event_sha256")
        elif "missing" in detail:
            reading.reasons.append("missing event")
        else:
            reading.reasons.append(detail)
        return reading
    if not isinstance(resolved, Event):
        reading.reasons.append("unmeasured: legacy identity")
        return reading
    event = resolved
    reading.event = event
    acquisition = event.data.get("acquisition")
    if not isinstance(acquisition, dict):
        reading.reasons.append("unmeasured: missing acquisition metadata")
        return reading
    channel = acquisition.get("channel")
    if not isinstance(channel, str):
        reading.reasons.append("unmeasured: missing acquisition metadata")
        return reading
    reading.channel = channel
    anchor = acquisition.get("observation_anchor")
    reading.observation_anchor = anchor if isinstance(anchor, str) else None
    conclusion = acquisition.get("conclusion_id")
    reading.conclusion_id = conclusion if isinstance(conclusion, str) else None
    contract = acquisition.get("acceptance_contract_digest")
    reading.contract = contract if isinstance(contract, str) else None
    roots = acquisition.get("derivation_roots")
    if roots == "unknown" or roots == []:
        reading.reasons.append("unmeasured: unknown derivation roots")
        return reading
    if (
        isinstance(roots, list)
        and roots
        and all(isinstance(item, str) for item in roots)
    ):
        reading.roots = frozenset(cast(list[str], roots))
    else:
        reading.reasons.append("unmeasured: unknown derivation roots")
        return reading
    if event.kind == VERIFICATION_OUTCOME_KIND:
        status = event.data.get("status")
        if status != "completed":
            reading.reasons.append(
                str(status) if isinstance(status, str) else "not completed"
            )
            return reading
    elif event.kind == KNOWLEDGE_RETRIEVED_KIND:
        status = event.data.get("status")
        if status != "ok":
            reading.reasons.append(
                str(status) if isinstance(status, str) else "not completed"
            )
            return reading
    else:
        reading.reasons.append("unmeasured: missing acquisition metadata")
        return reading
    reading.polarity = _polarity(event, acquisition)
    if reading.polarity is None:
        reading.reasons.append("unmeasured: missing sealed alternative")
        return reading
    reading.slot = True
    return reading

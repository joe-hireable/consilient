"""SQLite projection of the trajectory.

V0-02: SQLite is only a projection of the JSONL. Delete it, replay, and the state is
identical. Nothing may write to the database except a replay of events.

V0-26: an outcome and its deferred human verdict project to one row keyed by attempt_id.
V0-30: a provider that reported no usable figure still projects a row, so "could not be
read" is visible in the state rather than absent from it.

"Byte-identical state" is checked as a digest over a canonical dump of every row, not
over the database file. SQLite files are not byte-stable across writes — page ordering,
freelists and the header's change counter all move — so a file-level comparison would
fail for reasons that have nothing to do with state. The row dump is the honest form of
the invariant.

The rebuild is all that remains in this file; the tables and the per-event handlers now
sit beside it. `projection_schema.py` holds `SCHEMA` and the writers that need only the
tables. `projection_rows.py` holds the shared constants, `ProjectionError`, the row
readers the rest of the harness queries through, and `state_digest`.
`projection_records.py` holds captured records, their temporal views and the reading
classifier. `projection_verdicts.py` holds the appliers for outcomes, verdicts,
corrections, measurements, exposures and delivery estimates. `projection_consilience.py`
holds capability heads and conflicts, the fail-closed measurement join and
`consilience_status`. `build` is still the only path that writes the database.
"""

from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import cast
from .events import (
    CANDIDATE_EXPOSED_KIND,
    CAPABILITY_VERSIONED_KIND,
    DELIVERY_ESTIMATE_KIND,
    MEASUREMENT_REGISTERED_KIND,
    MEASUREMENT_RESULT_KIND,
    OUTCOME_KIND,
    RECORD_CAPTURED_KIND,
    REVIEW_QUEUE_OPENED_KIND,
    USAGE_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    VERIFICATION_OUTCOME_KIND,
    Event,
    Rejection,
    _fsync_directory,
    read_all,
)
from .work_items import STATE
from .projection_schema import (
    SCHEMA,
    _apply_native_work_items,
    _apply_usage,
)

from .projection_consilience import (
    NOT_PROJECTED,
    _apply_capability_versioned,
    _apply_measurement_registered,
    _apply_verification_outcome,
    _apply_work_item_opened,
    consilience_status,
    joined_measurement_results,
    projection_version,
    selected_exposure_rows,
)

from .projection_records import (
    _apply_record_captured,
    record_temporal_views,
)

from .projection_rows import (
    CONSILIENCE_STATUSES,
    HANDLERS,
    PROJECTION_VERSION,
    ProjectionError,
    VERSION_KEY,
    _apply_rejections,
    _apply_work_item_completed,
    _apply_work_item_state,
    _infer_workspace,
    _quarantine_relational,
    _verdict_auth_status,
    capability_conflicts,
    capability_heads,
    capability_versions,
    delivery_estimate_chain,
    native_work_item_rows,
    rejection_count,
    rejections,
    relational_quarantines,
    review_queue_row,
    sampling_unconditioned,
    set_sampling_unconditioned,
    state_digest,
)

from .projection_schema import (
    work_item_groups,
)

from .projection_verdicts import (
    _apply_candidate_exposed,
    _apply_delivery_estimate,
    _apply_measurement_result,
    _apply_outcome,
    _apply_review_queue_opened,
    _apply_verdict,
    _apply_verdict_correction,
)

__all__ = [
    "CONSILIENCE_STATUSES",
    "HANDLERS",
    "NOT_PROJECTED",
    "PROJECTION_VERSION",
    "ProjectionError",
    "SCHEMA",
    "VERSION_KEY",
    "_apply_candidate_exposed",
    "_apply_capability_versioned",
    "_apply_delivery_estimate",
    "_apply_measurement_registered",
    "_apply_measurement_result",
    "_apply_native_work_items",
    "_apply_outcome",
    "_apply_record_captured",
    "_apply_rejections",
    "_apply_review_queue_opened",
    "_apply_usage",
    "_apply_verdict",
    "_apply_verdict_correction",
    "_apply_verification_outcome",
    "_apply_work_item_completed",
    "_apply_work_item_opened",
    "_apply_work_item_state",
    "_infer_workspace",
    "_quarantine_relational",
    "_verdict_auth_status",
    "build",
    "capability_conflicts",
    "capability_heads",
    "capability_versions",
    "consilience_status",
    "delivery_estimate_chain",
    "joined_measurement_results",
    "memory_record_rows",
    "native_work_item_rows",
    "prefix_digest",
    "projection_version",
    "record_temporal_views",
    "rejection_count",
    "rejections",
    "relational_quarantines",
    "review_queue_row",
    "sampling_unconditioned",
    "selected_exposure_rows",
    "set_sampling_unconditioned",
    "state_digest",
    "work_item_groups",
]


def build(
    log_dir: Path, db_path: Path, *, workspace: Path | None = None
) -> sqlite3.Connection:
    """Rebuild the projection from scratch. The only path that writes the database."""
    events, rejected = read_all(log_dir)
    resolved_workspace = (
        workspace if workspace is not None else _infer_workspace(log_dir)
    )
    return _rebuild(events, rejected, db_path, workspace=resolved_workspace)


def _rebuild(
    events: list[Event],
    rejected: list[Rejection],
    db_path: Path,
    *,
    workspace: Path | None,
) -> sqlite3.Connection:
    """Populate a sibling temp file and publish it with os.replace.

    Unlink-then-write used to destroy the previous state before the new one was
    complete, so a crash mid-rebuild looked like a missing database and a false
    DIVERGED. Same shape as records._install_object: write aside, fsync, replace.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.parent / f".{db_path.name}.{os.urandom(16).hex()}.tmp"
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(temporary)
        conn.executescript(SCHEMA)
        verification_attempts: set[str] = set()
        exposure_positions: dict[str, int] = {}
        for position, event in enumerate(events):
            if event.kind == CANDIDATE_EXPOSED_KIND:
                attempt_id = event.data.get("attempt_id")
                if isinstance(attempt_id, str):
                    exposure_positions[attempt_id] = position
            if event.kind != VERIFICATION_OUTCOME_KIND:
                continue
            attempt_id = event.data.get("attempt_id")
            if isinstance(attempt_id, str):
                verification_attempts.add(attempt_id)
        _apply(
            conn,
            events,
            verification_attempts,
            exposure_positions=exposure_positions,
            workspace=workspace,
        )
        _apply_rejections(conn, rejected)
        _derive_review_queue_state(conn, events)
        conn.execute(
            "INSERT OR REPLACE INTO projection_meta (key, value) VALUES (?, ?)",
            (VERSION_KEY, PROJECTION_VERSION),
        )
        conn.execute(f"PRAGMA user_version = {PROJECTION_VERSION}")
        conn.commit()
        conn.close()
        conn = None
        # Windows FlushFileBuffers refuses a read-only handle (EBADF on "rb").
        with temporary.open("r+b") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, db_path)
        _fsync_directory(db_path.parent)
    except Exception:
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error:
                pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return sqlite3.connect(db_path)


def prefix_digest(
    events: list[Event],
    rejected: list[Rejection],
    scratch_dir: Path,
    *,
    log_dir: Path,
) -> str:
    """state_digest of a rebuild of `events` only, used to tell lag from drift."""
    scratch = scratch_dir / f".prefix-{os.urandom(8).hex()}.tmp"
    conn = _rebuild(events, rejected, scratch, workspace=_infer_workspace(log_dir))
    try:
        return state_digest(conn)
    finally:
        conn.close()
        try:
            scratch.unlink()
        except FileNotFoundError:
            pass


def _derive_review_queue_state(conn: sqlite3.Connection, events: list[Event]) -> None:
    from . import verification as verification_mod

    set_sampling_unconditioned(conn, False)
    conn.execute(
        "INSERT OR REPLACE INTO projection_meta (key, value) VALUES (?, ?)",
        ("review_queue_replay_ok", "false"),
    )
    queue = review_queue_row(conn)
    if queue is None:
        return
    recomputed = verification_mod.eligible_universe_digest(
        task_family=cast(str, queue["task_family"]),
        population=cast(str, queue["population"]),
        protocol_id=cast(str, queue["protocol_id"]),
        verifier_version=cast(str, queue["verifier_version"]),
        verifier_contract_digest=cast(str, queue["verifier_contract_digest"]),
        order_rule=cast(str, queue["order_rule"]),
    )
    if recomputed != queue["eligible_universe_digest"]:
        return
    selected = selected_exposure_rows(conn)
    if not selected:
        return
    exposure_by_attempt = {
        cast(str, event.data["attempt_id"]): (index, event)
        for index, event in enumerate(events)
        if event.kind == CANDIDATE_EXPOSED_KIND
    }
    verification_by_attempt: dict[str, list[tuple[int, Event]]] = {}
    for index, event in enumerate(events):
        if event.kind != VERIFICATION_OUTCOME_KIND:
            continue
        attempt_id = cast(str, event.data["attempt_id"])
        verification_by_attempt.setdefault(attempt_id, []).append((index, event))
    for exposure in selected:
        attempt_id = cast(str, exposure["attempt_id"])
        located = exposure_by_attempt.get(attempt_id)
        if located is None:
            return
        exposure_pos, exposure_event = located
        components = verification_by_attempt.get(attempt_id, [])
        if not components:
            return
        for component_pos, component in components:
            if component_pos <= exposure_pos:
                return
            if component.data.get("start_token") != exposure_event.data.get(
                "start_token"
            ):
                return
    if not verification_mod.coverage_gate_passed():
        return
    set_sampling_unconditioned(conn, True)
    conn.execute(
        "INSERT OR REPLACE INTO projection_meta (key, value) VALUES (?, ?)",
        ("review_queue_replay_ok", "true"),
    )


def _apply(
    conn: sqlite3.Connection,
    events: list[Event],
    verification_attempts: set[str],
    *,
    exposure_positions: dict[str, int],
    workspace: Path | None = None,
) -> None:
    event_index = {
        cast(str, event.raw["event_id"]): event
        for event in events
        if "event_id" in event.raw
    }
    for position, event in enumerate(events):
        raw = event.raw
        conn.execute(
            "INSERT INTO events (position, ts, kind, actor, principal, task, payload)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                position,
                raw["ts"],
                event.kind,
                event.actor,
                event.data.get("principal"),
                event.data.get("task"),
                json.dumps(
                    raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ),
            ),
        )
        try:
            if event.kind == OUTCOME_KIND:
                _apply_outcome(conn, position, event, verification_attempts)
            elif event.kind == VERDICT_KIND:
                _apply_verdict(conn, position, event)
            elif event.kind == VERDICT_CORRECTION_KIND:
                _apply_verdict_correction(conn, position, event)
            elif event.kind == USAGE_KIND:
                _apply_usage(conn, position, event)
            elif event.kind == RECORD_CAPTURED_KIND:
                _apply_record_captured(conn, position, event, workspace, event_index)
            elif event.kind == DELIVERY_ESTIMATE_KIND:
                _apply_delivery_estimate(conn, position, event)
            elif event.kind == REVIEW_QUEUE_OPENED_KIND:
                _apply_review_queue_opened(conn, position, event)
            elif event.kind == CANDIDATE_EXPOSED_KIND:
                _apply_candidate_exposed(conn, position, event)
            elif event.kind == VERIFICATION_OUTCOME_KIND:
                _apply_verification_outcome(
                    conn,
                    position,
                    event,
                    exposure_positions=exposure_positions,
                )
            elif event.kind == MEASUREMENT_REGISTERED_KIND:
                _apply_measurement_registered(conn, position, event)
            elif event.kind == MEASUREMENT_RESULT_KIND:
                _apply_measurement_result(conn, position, event)
            elif event.kind == "work_item.opened":
                _apply_work_item_opened(conn, position, event)
            elif event.kind == STATE:
                _apply_work_item_state(conn, position, event)
            elif event.kind == "work_item.completed":
                _apply_work_item_completed(conn, position, event)
            elif event.kind == CAPABILITY_VERSIONED_KIND:
                _apply_capability_versioned(conn, position, event)
        except sqlite3.IntegrityError as exc:
            _quarantine_relational(
                conn,
                position,
                event,
                f"duplicate unique key for {event.kind} at position {position}: {exc}",
            )
    _apply_native_work_items(conn, events)


def memory_record_rows(
    conn: sqlite3.Connection,
) -> list[tuple[str, tuple[object, ...]]]:
    """Ordered dump of memory projection tables for determinism checks."""
    rows: list[tuple[str, tuple[object, ...]]] = []
    for table in ("record_facts", "record_relations", "record_defects"):
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        order = columns[0]
        for row in conn.execute(
            f"SELECT {', '.join(columns)} FROM {table} ORDER BY {order}"
        ):
            rows.append((table, tuple(row)))
    for view in record_temporal_views(conn):
        # `record_temporal_views` returns `dict[str, object]`, so each field is `object`
        # here and neither `.get` nor iteration type-checks. Narrowing once per view is
        # the same `cast` idiom the rest of this module uses on projected payloads.
        current = cast("dict[str, object] | None", view["current"])
        history = cast("list[dict[str, object]]", view["history"])
        contested_heads = cast("list[dict[str, object]]", view["contested_heads"])
        invalidated = cast("list[dict[str, object]]", view["invalidated"])
        rows.append(
            (
                "record_temporal",
                (
                    view["source"],
                    view["status"],
                    current.get("record_id") if current else None,
                    json.dumps(
                        [fact["record_id"] for fact in history],
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        [fact["record_id"] for fact in contested_heads],
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        [fact["record_id"] for fact in invalidated],
                        separators=(",", ":"),
                    ),
                    json.dumps(view["defects"], sort_keys=True, separators=(",", ":")),
                ),
            )
        )
    return rows

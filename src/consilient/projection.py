"""SQLite projection of the trajectory.

V0-02: SQLite is only a projection of the JSONL. Delete it, replay, and the state is
identical. Nothing may write to the database except a replay of events.

V0-26: an outcome and its deferred human verdict project to one row keyed by attempt_id.
V0-30: a provider that reported no usable figure still projects a row, so "could not
be read" is visible in the state rather than absent from it.

"Byte-identical state" is checked as a digest over a canonical dump of every row, not over
the database file. SQLite files are not byte-stable across writes — page ordering, freelists
and the header's change counter all move — so a file-level comparison would fail for reasons
that have nothing to do with state. The row dump is the honest form of the invariant.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import cast

from . import events as events_mod
from .events import (
    CANDIDATE_EXPOSED_KIND,
    CAPABILITY_VERSIONED_KIND,
    DELIVERY_ESTIMATE_KIND,
    EventError,
    KNOWLEDGE_RETRIEVED_KIND,
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
    decision_protocol_data,
    event_sha256,
    read_all,
    resolve_reference,
)
from .work_items import STATE, WORK_MODEL_SCHEMA, state_group

# Stamp written into projection_meta so a legitimate handler/schema change is a
# third replay state, not Gate A2 "DIVERGED". Bump when a rebuild of the same log
# is expected to change state_digest.
PROJECTION_VERSION = "1"
VERSION_KEY = "version"

# Every events.py `*_KIND` string must appear in exactly one of these. T11.
HANDLERS: frozenset[str] = frozenset(
    {
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
    }
)
# Leftover `*_KIND` strings from events.py. Feedback kinds cannot be named here
# as imports or literals — tests/test_feedback.py forbids any other module from
# reading them. A new kind therefore lands here until it is moved into HANDLERS.
NOT_PROJECTED: frozenset[str] = (
    frozenset(
        value
        for name, value in vars(events_mod).items()
        if name.endswith("_KIND") and isinstance(value, str)
    )
    - HANDLERS
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    position   INTEGER PRIMARY KEY,
    ts         TEXT NOT NULL,
    kind       TEXT NOT NULL,
    actor      TEXT NOT NULL,
    principal  TEXT,
    task       TEXT,
    payload    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    position        INTEGER PRIMARY KEY,
    attempt_id      TEXT NOT NULL UNIQUE,
    ts              TEXT NOT NULL,
    task            TEXT NOT NULL,
    task_family     TEXT,
    verifier_version TEXT,
    verifier_accept INTEGER NOT NULL,
    human_verdict   TEXT,
    estimand_kind   TEXT,
    auth_status     TEXT
);
CREATE INDEX IF NOT EXISTS outcomes_family ON outcomes (task_family, verifier_version);
CREATE TABLE IF NOT EXISTS usage (
    id            INTEGER PRIMARY KEY,
    position      INTEGER NOT NULL,
    provider      TEXT NOT NULL,
    kind          TEXT NOT NULL,
    status        TEXT NOT NULL,
    detail        TEXT NOT NULL,
    observed_at   TEXT,
    measure       TEXT NOT NULL,
    window_label  TEXT,
    used_fraction TEXT,
    resets_at     TEXT,
    amount        TEXT,
    currency      TEXT,
    period        TEXT,
    provenance    TEXT
);
CREATE TABLE IF NOT EXISTS rejections (
    id     INTEGER PRIMARY KEY,
    path   TEXT NOT NULL,
    line   INTEGER NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_facts (
    position             INTEGER NOT NULL,
    record_id            TEXT NOT NULL PRIMARY KEY,
    event_id             TEXT NOT NULL UNIQUE,
    event_kind           TEXT NOT NULL,
    event_sha256         TEXT NOT NULL,
    digest               TEXT NOT NULL,
    kind                 TEXT NOT NULL,
    actor                TEXT NOT NULL,
    work_item            TEXT,
    capability_contract  TEXT,
    source               TEXT NOT NULL,
    valid_from           TEXT NOT NULL,
    valid_to             TEXT,
    object_locator       TEXT NOT NULL,
    byte_count           INTEGER NOT NULL,
    consent_purpose      TEXT NOT NULL,
    retention_class      TEXT NOT NULL,
    object_status        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_relations (
    id                   INTEGER PRIMARY KEY,
    position             INTEGER NOT NULL,
    record_id            TEXT NOT NULL,
    relation             TEXT NOT NULL,
    target_event_id      TEXT NOT NULL,
    target_event_kind    TEXT NOT NULL,
    target_event_sha256  TEXT NOT NULL,
    target_record_id     TEXT,
    relation_status      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS record_defects (
    id          INTEGER PRIMARY KEY,
    position    INTEGER,
    record_id   TEXT,
    defect_kind TEXT NOT NULL,
    detail      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS delivery_estimates (
    position                 INTEGER PRIMARY KEY,
    delivery_id              TEXT NOT NULL,
    estimate_id              TEXT NOT NULL UNIQUE,
    revision                 INTEGER NOT NULL,
    predecessor_estimate_id  TEXT,
    original_estimate_id     TEXT NOT NULL,
    commitment_digest        TEXT NOT NULL,
    plan_digest              TEXT NOT NULL,
    earliest_at              TEXT NOT NULL,
    latest_at                TEXT NOT NULL,
    issued_at                TEXT NOT NULL,
    evidence_class           TEXT NOT NULL,
    method                   TEXT NOT NULL,
    sample_size              INTEGER NOT NULL,
    cause                    TEXT,
    notice_preceded_upper_bound INTEGER NOT NULL,
    payload                  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS delivery_estimates_delivery
    ON delivery_estimates (delivery_id, revision);
CREATE TABLE IF NOT EXISTS relational_quarantines (
    id       INTEGER PRIMARY KEY,
    position INTEGER NOT NULL,
    path     TEXT NOT NULL,
    line     INTEGER NOT NULL,
    digest   TEXT NOT NULL,
    reason   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projection_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_queues (
    position                 INTEGER PRIMARY KEY,
    queue_id                 TEXT NOT NULL UNIQUE,
    stream_cap               INTEGER NOT NULL,
    exp105_prefix_n          INTEGER NOT NULL,
    rejection_target         INTEGER NOT NULL,
    population               TEXT NOT NULL,
    task_family              TEXT NOT NULL,
    protocol_id              TEXT NOT NULL,
    verifier_version         TEXT NOT NULL,
    verifier_contract_digest TEXT NOT NULL,
    start_position           INTEGER NOT NULL,
    eligible_universe_digest TEXT NOT NULL,
    selector                 TEXT NOT NULL,
    order_rule               TEXT NOT NULL,
    payload                  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidate_exposures (
    position                 INTEGER PRIMARY KEY,
    queue_id                 TEXT NOT NULL,
    exposure_id              TEXT NOT NULL UNIQUE,
    attempt_id               TEXT NOT NULL,
    exposure_ordinal         INTEGER NOT NULL,
    start_token              TEXT NOT NULL UNIQUE,
    artefact_sha256          TEXT NOT NULL,
    task_family              TEXT NOT NULL,
    protocol_id              TEXT NOT NULL,
    verifier_version         TEXT NOT NULL,
    verifier_contract_digest TEXT NOT NULL,
    payload                  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS candidate_exposures_queue
    ON candidate_exposures (queue_id, position);
CREATE TABLE IF NOT EXISTS measurement_registrations (
    position     INTEGER PRIMARY KEY,
    run_id       TEXT NOT NULL UNIQUE,
    config_hash  TEXT NOT NULL,
    hardware_id  TEXT NOT NULL,
    payload      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS measurement_results (
    position     INTEGER PRIMARY KEY,
    run_id       TEXT NOT NULL,
    fixture      TEXT NOT NULL,
    payload      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS measurement_results_run
    ON measurement_results (run_id, position);
CREATE TABLE IF NOT EXISTS work_items (
    ticket          TEXT NOT NULL PRIMARY KEY,
    revision        INTEGER NOT NULL,
    state           TEXT NOT NULL,
    state_group     TEXT NOT NULL,
    is_blocked      INTEGER NOT NULL,
    blocked_reason  TEXT,
    accountable     TEXT NOT NULL,
    requires        TEXT NOT NULL,
    informs         TEXT NOT NULL,
    inform_scores   TEXT,
    payload         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS native_work_items (
    ticket      TEXT NOT NULL,
    revision    INTEGER NOT NULL,
    state       TEXT NOT NULL,
    blockers    TEXT NOT NULL,
    PRIMARY KEY (ticket, revision)
);
CREATE TABLE IF NOT EXISTS capability_versions (
    position                INTEGER NOT NULL,
    event_id                TEXT NOT NULL PRIMARY KEY,
    event_sha256            TEXT NOT NULL,
    identity                TEXT NOT NULL,
    version_digest          TEXT NOT NULL,
    content_digest          TEXT NOT NULL,
    execution_contract_key  TEXT NOT NULL,
    destination_class       TEXT NOT NULL,
    status                  TEXT NOT NULL,
    evidence_class          TEXT NOT NULL,
    permission_boundary     TEXT NOT NULL,
    trust_boundary          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS capability_heads (
    execution_contract_key  TEXT NOT NULL,
    destination_class       TEXT NOT NULL,
    event_id                TEXT NOT NULL,
    identity                TEXT NOT NULL,
    version_digest          TEXT NOT NULL,
    status                  TEXT NOT NULL,
    evidence_class          TEXT NOT NULL,
    permission_boundary     TEXT NOT NULL,
    trust_boundary          TEXT NOT NULL,
    PRIMARY KEY (execution_contract_key, destination_class)
);
CREATE TABLE IF NOT EXISTS capability_conflicts (
    execution_contract_key  TEXT NOT NULL,
    destination_class       TEXT NOT NULL,
    identity                TEXT NOT NULL,
    event_ids               TEXT NOT NULL,
    PRIMARY KEY (execution_contract_key, destination_class)
);
"""


class ProjectionError(RuntimeError):
    pass


def _infer_workspace(log_dir: Path) -> Path | None:
    if log_dir.name == "log" and log_dir.parent.name == ".harness":
        return log_dir.parent.parent
    return None


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


def projection_version(conn: sqlite3.Connection) -> str | None:
    try:
        row = conn.execute(
            "SELECT value FROM projection_meta WHERE key = ?", (VERSION_KEY,)
        ).fetchone()
    except sqlite3.DatabaseError:
        return None
    return None if row is None else str(row[0])


def _apply_rejections(conn: sqlite3.Connection, rejected: list[Rejection]) -> None:
    """Refused lines are part of the state, not something that vanished on the way in.

    Putting them in a table rather than returning them out of band means three things
    hold for free: `state_digest` covers them, so a change in what the log refuses changes
    the digest and `replay` sees it; nothing can drop them by forgetting to unpack a
    tuple; and the count is queryable by anything that reports a number derived from the
    log. A quarantine nobody can see is the same as a silent skip.
    """
    for index, rejection in enumerate(rejected):
        conn.execute(
            "INSERT INTO rejections (id, path, line, reason) VALUES (?, ?, ?, ?)",
            (index, rejection.path, rejection.line, rejection.reason),
        )


def rejection_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM rejections").fetchone()[0])


def rejections(conn: sqlite3.Connection) -> list[dict[str, object]]:
    return [
        {"path": row[0], "line": row[1], "reason": row[2]}
        for row in conn.execute("SELECT path, line, reason FROM rejections ORDER BY id")
    ]


def relational_quarantines(conn: sqlite3.Connection) -> list[dict[str, object]]:
    return [
        {
            "position": row[0],
            "path": row[1],
            "line": row[2],
            "digest": row[3],
            "reason": row[4],
        }
        for row in conn.execute(
            "SELECT position, path, line, digest, reason"
            " FROM relational_quarantines ORDER BY id"
        )
    ]


def sampling_unconditioned(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT value FROM projection_meta WHERE key = 'sampling_unconditioned'"
    ).fetchone()
    return row is not None and row[0] == "true"


def set_sampling_unconditioned(conn: sqlite3.Connection, value: bool) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO projection_meta (key, value) VALUES (?, ?)",
        ("sampling_unconditioned", "true" if value else "false"),
    )


def review_queue_row(conn: sqlite3.Connection) -> dict[str, object] | None:
    row = conn.execute(
        "SELECT payload FROM review_queues ORDER BY position LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return cast(dict[str, object], json.loads(cast(str, row[0]))["data"])


def selected_exposure_rows(conn: sqlite3.Connection) -> list[dict[str, object]]:
    queue = review_queue_row(conn)
    if queue is None:
        return []
    rows = conn.execute(
        "SELECT payload FROM candidate_exposures WHERE queue_id = ? ORDER BY position",
        (queue["queue_id"],),
    ).fetchall()
    payloads = [
        cast(dict[str, object], json.loads(cast(str, row[0]))["data"]) for row in rows
    ]
    start = cast(int, queue["start_position"])
    cap = cast(int, queue["stream_cap"])
    return payloads[start : start + cap]


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


def _apply_review_queue_opened(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    queue_id = cast(str, data["queue_id"])
    if conn.execute(
        "SELECT 1 FROM review_queues WHERE queue_id = ?", (queue_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate review queue {queue_id!r} at position {position}",
        )
        return
    if conn.execute("SELECT COUNT(*) FROM review_queues").fetchone()[0]:
        _quarantine_relational(
            conn,
            position,
            event,
            "only one review.queue.opened event is permitted per trajectory",
        )
        return
    conn.execute(
        "INSERT INTO review_queues (position, queue_id, stream_cap, exp105_prefix_n,"
        " rejection_target, population, task_family, protocol_id, verifier_version,"
        " verifier_contract_digest, start_position, eligible_universe_digest, selector,"
        " order_rule, payload)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            queue_id,
            data["stream_cap"],
            data["exp105_prefix_n"],
            data["rejection_target"],
            data["population"],
            data["task_family"],
            data["protocol_id"],
            data["verifier_version"],
            data["verifier_contract_digest"],
            data["start_position"],
            data["eligible_universe_digest"],
            data["selector"],
            data["order_rule"],
            json.dumps(
                event.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def _apply_candidate_exposed(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    exposure_id = cast(str, data["exposure_id"])
    if conn.execute(
        "SELECT 1 FROM candidate_exposures WHERE exposure_id = ?", (exposure_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate exposure_id {exposure_id!r} at position {position}",
        )
        return
    conn.execute(
        "INSERT INTO candidate_exposures (position, queue_id, exposure_id, attempt_id,"
        " exposure_ordinal, start_token, artefact_sha256, task_family, protocol_id,"
        " verifier_version, verifier_contract_digest, payload)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            data["queue_id"],
            exposure_id,
            data["attempt_id"],
            data["exposure_ordinal"],
            data["start_token"],
            data["artefact_sha256"],
            data["task_family"],
            data["protocol_id"],
            data["verifier_version"],
            data["verifier_contract_digest"],
            json.dumps(
                event.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def _apply_verification_outcome(
    conn: sqlite3.Connection,
    position: int,
    event: Event,
    *,
    exposure_positions: dict[str, int],
) -> None:
    queue = review_queue_row(conn)
    if queue is None:
        return
    attempt_id = event.data.get("attempt_id")
    if not isinstance(attempt_id, str):
        return
    exposure_pos = exposure_positions.get(attempt_id)
    if exposure_pos is None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"missing candidate.exposed before verification.outcome for {attempt_id!r}",
        )
        return
    if position <= exposure_pos:
        _quarantine_relational(
            conn,
            position,
            event,
            f"verification.outcome for {attempt_id!r} precedes its candidate.exposed event",
        )


def _apply_measurement_registered(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    run_id = cast(str, data["run_id"])
    if conn.execute(
        "SELECT 1 FROM measurement_registrations WHERE run_id = ?", (run_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate run_id {run_id!r} at position {position}",
        )
        return
    conn.execute(
        "INSERT INTO measurement_registrations (position, run_id, config_hash,"
        " hardware_id, payload) VALUES (?, ?, ?, ?, ?)",
        (
            position,
            run_id,
            data["config_hash"],
            data["hardware_id"],
            json.dumps(
                event.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def _apply_measurement_result(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    run_id = cast(str, data["run_id"])
    registration = conn.execute(
        "SELECT position FROM measurement_registrations WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    if registration is None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"missing measurement.registered before measurement.result for {run_id!r}",
        )
        return
    if position <= cast(int, registration[0]):
        _quarantine_relational(
            conn,
            position,
            event,
            f"measurement.result for {run_id!r} precedes its measurement.registered event",
        )
        return
    conn.execute(
        "INSERT INTO measurement_results (position, run_id, fixture, payload)"
        " VALUES (?, ?, ?, ?)",
        (
            position,
            run_id,
            data["fixture"],
            json.dumps(
                event.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def _quarantine_relational(
    conn: sqlite3.Connection,
    position: int,
    event: Event,
    reason: str,
) -> None:
    conn.execute(
        "INSERT INTO relational_quarantines (position, path, line, digest, reason)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            position,
            event.path or "",
            event.line or 0,
            event_sha256(event.raw),
            reason,
        ),
    )


def _verdict_auth_status(data: dict[str, object]) -> str:
    """`ssh_sig` is authenticated; a cli principal is only declared, never admitted."""
    via = data.get("via")
    principal = data.get("principal")
    normalized_via = via.strip().casefold() if isinstance(via, str) else None
    if normalized_via == "ssh_sig":
        return "authenticated"
    if normalized_via == "cli" and isinstance(principal, str) and principal.strip():
        return "declared_principal"
    return "unauthenticated"


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


def _work_item_row(
    ticket: str,
    revision: int,
    state: str,
    accountable: str,
    requires: list[object],
    informs: list[object],
    *,
    is_blocked: bool = False,
    blocked_reason: str | None = None,
    inform_scores: list[object] | None = None,
    payload: dict[str, object],
) -> tuple[object, ...]:
    return (
        ticket,
        revision,
        state,
        state_group(state),
        int(is_blocked),
        blocked_reason,
        accountable,
        json.dumps(requires, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        json.dumps(informs, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        None
        if inform_scores is None
        else json.dumps(
            inform_scores, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


def _apply_work_item_opened(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    if data.get("item_schema") != WORK_MODEL_SCHEMA:
        return
    ticket = cast(str, data["ticket"])
    state = cast(str, data["state"])
    is_blocked = bool(data.get("is_blocked", False))
    blocked_reason = cast(str | None, data.get("blocked_reason"))
    conn.execute(
        "INSERT OR REPLACE INTO work_items (ticket, revision, state, state_group,"
        " is_blocked, blocked_reason, accountable, requires, informs, inform_scores,"
        " payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _work_item_row(
            ticket,
            int(data.get("revision", 1)),
            state,
            cast(str, data["accountable"]),
            cast(list[object], data.get("requires", [])),
            cast(list[object], data.get("informs", [])),
            is_blocked=is_blocked,
            blocked_reason=blocked_reason,
            payload=cast(dict[str, object], data),
        ),
    )


def _apply_work_item_state(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    del position
    data = event.data
    ticket = cast(str, data["ticket"])
    row = conn.execute(
        "SELECT revision, accountable, requires, informs, payload FROM work_items"
        " WHERE ticket = ?",
        (ticket,),
    ).fetchone()
    if row is None:
        return
    state = cast(str, data["state"])
    is_blocked = bool(data.get("is_blocked", False))
    blocked_reason = cast(str | None, data.get("blocked_reason"))
    conn.execute(
        "UPDATE work_items SET state = ?, state_group = ?, is_blocked = ?,"
        " blocked_reason = ? WHERE ticket = ?",
        (state, state_group(state), int(is_blocked), blocked_reason, ticket),
    )


def _apply_work_item_completed(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    del position
    data = event.data
    ticket = cast(str, data["ticket"])
    inform_scores = data.get("inform_scores")
    if inform_scores is None:
        return
    conn.execute(
        "UPDATE work_items SET inform_scores = ? WHERE ticket = ?",
        (
            json.dumps(
                inform_scores, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
            ticket,
        ),
    )


def work_item_groups(conn: sqlite3.Connection) -> dict[str, list[dict[str, object]]]:
    """Project work-model items into the five declared state groups."""
    grouped: dict[str, list[dict[str, object]]] = {
        group: []
        for group in (
            "WAITING",
            "RUNNING",
            "NEEDS_YOU",
            "DONE",
            "DEAD",
        )
    }
    rows = conn.execute(
        "SELECT ticket, revision, state, state_group, is_blocked, blocked_reason,"
        " accountable, requires, informs, inform_scores"
        " FROM work_items ORDER BY ticket"
    ).fetchall()
    for row in rows:
        group = cast(str, row[3])
        grouped.setdefault(group, []).append(
            {
                "ticket": row[0],
                "revision": row[1],
                "state": row[2],
                "state_group": row[3],
                "is_blocked": bool(row[4]),
                "blocked_reason": row[5],
                "accountable": row[6],
                "requires": json.loads(cast(str, row[7])),
                "informs": json.loads(cast(str, row[8])),
                "inform_scores": None
                if row[9] is None
                else json.loads(cast(str, row[9])),
            }
        )
    return grouped


def _apply_native_work_items(conn: sqlite3.Connection, events: list[Event]) -> None:
    """Project native work-item readiness without interpreting legacy dispatch claims."""
    items: dict[tuple[str, int], dict[str, object]] = {}
    attempts: set[tuple[str, int]] = set()
    paused: set[tuple[str, int]] = set()
    for event in events:
        data = event.data
        key_data = (data.get("ticket"), data.get("revision"))
        if not isinstance(key_data[0], str) or not isinstance(key_data[1], int):
            continue
        key = cast(tuple[str, int], key_data)
        if event.kind == "work_item.opened" and data.get("item_schema") == "native.v1":
            items[key] = data
        elif event.kind == "work_item.attempted" and key in items:
            attempts.add(key)
        elif event.kind == "work_item.commitment_paused" and key in items:
            paused.add(key)

    for key in sorted(items):
        item = items[key]
        blockers: list[str] = []
        if key in paused:
            blockers.append("commitment_paused")
        dependencies = cast(list[dict[str, object]], item["dependencies"])
        for dependency in dependencies:
            blocker = f"dependency:{dependency['ticket']}@{dependency['revision']}"
            blockers.append(blocker)
        blockers.sort()
        state = "blocked" if blockers else "active" if key in attempts else "ready"
        conn.execute(
            "INSERT INTO native_work_items (ticket, revision, state, blockers)"
            " VALUES (?, ?, ?, ?)",
            (
                key[0],
                key[1],
                state,
                json.dumps(blockers, separators=(",", ":")),
            ),
        )


def native_work_item_rows(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """Return canonical native work-item state for replay and rendering."""
    return [
        {
            "ticket": row[0],
            "revision": row[1],
            "state": row[2],
            "blockers": json.loads(row[3]),
        }
        for row in conn.execute(
            "SELECT ticket, revision, state, blockers"
            " FROM native_work_items ORDER BY ticket, revision"
        )
    ]


def _capability_row(event: Event) -> dict[str, object]:
    data = event.data
    return {
        "event_id": event.raw["event_id"],
        "event_sha256": _event_sha256(event.raw),
        "identity": data["identity"],
        "version_digest": data["version_digest"],
        "content_digest": data["content_digest"],
        "execution_contract_key": data["execution_contract_key"],
        "destination_class": data["destination_class"],
        "status": data["status"],
        "evidence_class": data["evidence_class"],
        "permission_boundary": data["permission_boundary"],
        "trust_boundary": data["trust_boundary"],
    }


def _apply_capability_versioned(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    row = _capability_row(event)
    conn.execute(
        "INSERT INTO capability_versions (position, event_id, event_sha256, identity,"
        " version_digest, content_digest, execution_contract_key, destination_class,"
        " status, evidence_class, permission_boundary, trust_boundary)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            row["event_id"],
            row["event_sha256"],
            row["identity"],
            row["version_digest"],
            row["content_digest"],
            row["execution_contract_key"],
            row["destination_class"],
            row["status"],
            row["evidence_class"],
            row["permission_boundary"],
            row["trust_boundary"],
        ),
    )
    if row["status"] != "active":
        return
    key = (row["execution_contract_key"], row["destination_class"])
    existing_conflict = conn.execute(
        "SELECT event_ids FROM capability_conflicts"
        " WHERE execution_contract_key = ? AND destination_class = ?",
        key,
    ).fetchone()
    existing_head = conn.execute(
        "SELECT event_id FROM capability_heads"
        " WHERE execution_contract_key = ? AND destination_class = ?",
        key,
    ).fetchone()
    if existing_conflict is not None:
        event_ids = json.loads(existing_conflict[0])
        event_ids.append(row["event_id"])
        conn.execute(
            "UPDATE capability_conflicts SET event_ids = ?"
            " WHERE execution_contract_key = ? AND destination_class = ?",
            (
                json.dumps(event_ids, separators=(",", ":")),
                key[0],
                key[1],
            ),
        )
        return
    if existing_head is not None:
        conn.execute(
            "DELETE FROM capability_heads"
            " WHERE execution_contract_key = ? AND destination_class = ?",
            key,
        )
        conn.execute(
            "INSERT INTO capability_conflicts (execution_contract_key, destination_class,"
            " identity, event_ids) VALUES (?, ?, ?, ?)",
            (
                key[0],
                key[1],
                row["identity"],
                json.dumps([existing_head[0], row["event_id"]], separators=(",", ":")),
            ),
        )
        return
    conn.execute(
        "INSERT INTO capability_heads (execution_contract_key, destination_class, event_id,"
        " identity, version_digest, status, evidence_class, permission_boundary,"
        " trust_boundary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["execution_contract_key"],
            row["destination_class"],
            row["event_id"],
            row["identity"],
            row["version_digest"],
            row["status"],
            row["evidence_class"],
            row["permission_boundary"],
            row["trust_boundary"],
        ),
    )


def capability_versions(conn: sqlite3.Connection) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            "SELECT event_id, event_sha256, identity, version_digest, content_digest,"
            " execution_contract_key, destination_class, status, evidence_class,"
            " permission_boundary, trust_boundary FROM capability_versions"
            " ORDER BY position, event_id"
        )
    ]


def capability_heads(conn: sqlite3.Connection) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            "SELECT event_id, identity, version_digest, execution_contract_key,"
            " destination_class, status, evidence_class, permission_boundary,"
            " trust_boundary FROM capability_heads"
            " ORDER BY execution_contract_key, destination_class, event_id"
        )
    ]


def capability_conflicts(conn: sqlite3.Connection) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    rows: list[dict[str, object]] = []
    for row in conn.execute(
        "SELECT execution_contract_key, destination_class, identity, event_ids"
        " FROM capability_conflicts"
        " ORDER BY execution_contract_key, destination_class"
    ):
        item = dict(row)
        item["event_ids"] = json.loads(cast(str, item["event_ids"]))
        rows.append(item)
    return rows


def _apply_usage(conn: sqlite3.Connection, position: int, event: Event) -> None:
    """Project one usage observation, including the ones that reported no number.

    A provider that could not be read still gets a row, with `measure` set to 'none' and
    every figure column NULL. Projecting only the readable providers would make an
    unobserved provider indistinguishable from one that was never asked -- the same silent
    skip the rejections table exists to prevent. `state_digest` covers this table, so a
    change in what the harness can see changes the digest and `replay` reports it.

    Nothing is validated here that `events.validate` has not already enforced (V0-30):
    this is a projection, and a projection that re-decides what is admissible would be a
    second authority over the record.
    """
    data = event.data
    common = (
        position,
        data["provider"],
        data["kind"],
        data["status"],
        data["detail"],
        data.get("observed_at"),
    )
    rows: list[tuple[object, ...]] = [
        common
        + (
            "quota",
            q["window"],
            q["used_fraction"],
            q.get("resets_at"),
            None,
            None,
            None,
            q["provenance"],
        )
        for q in data.get("quotas", [])
    ]
    rows += [
        common
        + (
            "spend",
            None,
            None,
            None,
            s["amount"],
            s["currency"],
            s["period"],
            s["provenance"],
        )
        for s in data.get("spend", [])
    ]
    if not rows:
        rows = [common + ("none", None, None, None, None, None, None, None)]
    conn.executemany(
        "INSERT INTO usage (position, provider, kind, status, detail, observed_at,"
        " measure, window_label, used_fraction, resets_at, amount, currency, period,"
        " provenance) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def _apply_outcome(
    conn: sqlite3.Connection,
    position: int,
    event: Event,
    verification_attempts: set[str],
) -> None:
    data = event.data
    for field in ("attempt_id", "task", "verifier_accept"):
        if field not in data:
            raise ProjectionError(
                f"{OUTCOME_KIND} at position {position} is missing {field!r}"
            )
    attempt_id = data["attempt_id"]
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ProjectionError(
            f"attempt_id must be a non-empty string at position {position}"
        )
    if conn.execute(
        "SELECT 1 FROM outcomes WHERE attempt_id = ?", (attempt_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate attempt_id {attempt_id!r} at position {position}",
        )
        return
    if "human_verdict" in data:
        raise ProjectionError(
            f"{OUTCOME_KIND} cannot carry human_verdict; append a separate "
            f"{VERDICT_KIND} event"
        )
    if data.get("component_join_required") and attempt_id not in verification_attempts:
        _quarantine_relational(
            conn,
            position,
            event,
            f"missing component verification.outcome join for attempt {attempt_id!r}",
        )
        return
    accept = data["verifier_accept"]
    if not isinstance(accept, bool):
        raise ProjectionError(
            f"verifier_accept must be a boolean, got {type(accept).__name__} at {position}"
        )
    conn.execute(
        "INSERT INTO outcomes (position, attempt_id, ts, task, task_family,"
        " verifier_version, verifier_accept, human_verdict, estimand_kind, auth_status)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            attempt_id,
            event.raw["ts"],
            data["task"],
            data.get("task_family"),
            data.get("verifier_version"),
            int(accept),
            None,
            None,
            None,
        ),
    )


def _apply_verdict(conn: sqlite3.Connection, position: int, event: Event) -> None:
    data = event.data
    attempt_id = data.get("attempt_id")
    verdict = data.get("human_verdict")
    if verdict not in ("accept", "reject"):
        _quarantine_relational(
            conn,
            position,
            event,
            f"{VERDICT_KIND} at position {position} must carry human_verdict "
            "'accept' or 'reject'",
        )
        return
    row = conn.execute(
        "SELECT human_verdict FROM outcomes WHERE attempt_id = ?", (attempt_id,)
    ).fetchone()
    if row is None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"{VERDICT_KIND} at position {position} references unknown attempt "
            f"{attempt_id!r}",
        )
        return
    if row[0] is not None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"attempt {attempt_id!r} already has a verdict; a second verdict at "
            f"position {position} is ambiguous",
        )
        return
    auth_status = _verdict_auth_status(data)
    conn.execute(
        "UPDATE outcomes SET human_verdict = ?, estimand_kind = ?, auth_status = ?"
        " WHERE attempt_id = ?",
        (verdict, "human_verdict_beta", auth_status, attempt_id),
    )


def _apply_delivery_estimate(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    estimate_id = cast(str, data["estimate_id"])
    if conn.execute(
        "SELECT 1 FROM delivery_estimates WHERE estimate_id = ?", (estimate_id,)
    ).fetchone():
        _quarantine_relational(
            conn,
            position,
            event,
            f"duplicate estimate_id {estimate_id!r} at position {position}",
        )
        return
    delivery_id = cast(str, data["delivery_id"])
    revision = cast(int, data["revision"])
    existing = conn.execute(
        "SELECT revision FROM delivery_estimates WHERE delivery_id = ? ORDER BY revision DESC LIMIT 1",
        (delivery_id,),
    ).fetchone()
    if revision == 0:
        if existing is not None:
            raise ProjectionError(
                f"delivery.estimate revision zero already exists for {delivery_id!r}"
            )
    elif existing is None or revision != cast(int, existing[0]) + 1:
        raise ProjectionError(
            f"delivery.estimate revision {revision} is out of sequence for {delivery_id!r}"
        )
    conn.execute(
        "INSERT INTO delivery_estimates (position, delivery_id, estimate_id, revision,"
        " predecessor_estimate_id, original_estimate_id, commitment_digest, plan_digest,"
        " earliest_at, latest_at, issued_at, evidence_class, method, sample_size, cause,"
        " notice_preceded_upper_bound, payload)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            delivery_id,
            estimate_id,
            revision,
            data.get("predecessor_estimate_id"),
            data["original_estimate_id"],
            data["commitment_digest"],
            data["plan_digest"],
            data["earliest_at"],
            data["latest_at"],
            data["issued_at"],
            data["evidence_class"],
            data["method"],
            data["sample_size"],
            data.get("cause"),
            int(bool(data["notice_preceded_upper_bound"])),
            json.dumps(
                event.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def delivery_estimate_chain(
    conn: sqlite3.Connection, delivery_id: str
) -> list[dict[str, object]]:
    rows = conn.execute(
        "SELECT payload FROM delivery_estimates WHERE delivery_id = ? ORDER BY revision",
        (delivery_id,),
    ).fetchall()
    return [
        cast(dict[str, object], json.loads(cast(str, row[0]))["data"]) for row in rows
    ]


def _apply_verdict_correction(
    conn: sqlite3.Connection, position: int, event: Event
) -> None:
    data = event.data
    attempt_id = data.get("attempt_id")
    previous = data.get("previous_verdict")
    verdict = data.get("human_verdict")
    row = conn.execute(
        "SELECT human_verdict FROM outcomes WHERE attempt_id = ?", (attempt_id,)
    ).fetchone()
    if row is None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"{VERDICT_CORRECTION_KIND} at position {position} references unknown "
            f"attempt {attempt_id!r}",
        )
        return
    current = row[0]
    if current is None:
        _quarantine_relational(
            conn,
            position,
            event,
            f"attempt {attempt_id!r} has no verdict to correct at position {position}",
        )
        return
    if current != previous:
        _quarantine_relational(
            conn,
            position,
            event,
            f"{VERDICT_CORRECTION_KIND} at position {position} expected prior verdict "
            f"{previous!r}, found {current!r}",
        )
        return
    auth_status = _verdict_auth_status(data)
    conn.execute(
        "UPDATE outcomes SET human_verdict = ?, estimand_kind = ?, auth_status = ?"
        " WHERE attempt_id = ?",
        (verdict, "human_verdict_beta", auth_status, attempt_id),
    )


def _object_status(
    workspace: Path | None, object_locator: str, digest: str, byte_count: int
) -> str:
    if workspace is None:
        return "unchecked"
    path = workspace / Path(object_locator)
    if not path.is_file():
        return "missing"
    payload = path.read_bytes()
    if len(payload) != byte_count or hashlib.sha256(payload).hexdigest() != digest:
        return "corrupt"
    return "ok"


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


def _event_sha256(event: dict[str, object]) -> str:
    from .events import event_sha256

    return event_sha256(event)


def _insert_record_defect(
    conn: sqlite3.Connection,
    position: int | None,
    record_id: str | None,
    defect_kind: str,
    detail: dict[str, object],
) -> None:
    next_id = int(
        conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM record_defects").fetchone()[
            0
        ]
    )
    conn.execute(
        "INSERT INTO record_defects (id, position, record_id, defect_kind, detail)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            next_id,
            position,
            record_id,
            defect_kind,
            json.dumps(
                detail, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        ),
    )


def _record_fact_dict(row: sqlite3.Row) -> dict[str, object]:
    return {
        "record_id": row["record_id"],
        "event_id": row["event_id"],
        "event_kind": row["event_kind"],
        "event_sha256": row["event_sha256"],
        "digest": row["digest"],
        "kind": row["kind"],
        "actor": row["actor"],
        "work_item": row["work_item"],
        "capability_contract": row["capability_contract"],
        "source": row["source"],
        "valid_from": row["valid_from"],
        "valid_to": row["valid_to"],
        "object_locator": row["object_locator"],
        "byte_count": row["byte_count"],
        "consent_purpose": row["consent_purpose"],
        "retention_class": row["retention_class"],
        "object_status": row["object_status"],
        "position": row["position"],
    }


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


def state_digest(conn: sqlite3.Connection) -> str:
    """A stable digest of every row in every table, independent of file layout."""
    hasher = hashlib.sha256()
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    for table in tables:
        hasher.update(f"\x00table:{table}\x00".encode())
        columns = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        hasher.update(("|".join(columns) + "\x00").encode())
        for row in conn.execute(
            f"SELECT {', '.join(columns)} FROM {table} ORDER BY {columns[0]}"
        ):
            hasher.update(
                (
                    json.dumps(list(row), ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                ).encode()
            )
    return hasher.hexdigest()


CONSILIENCE_STATUSES = frozenset(
    {"converged", "insufficient", "disagreed", "unmeasured"}
)
_UNMEASURED_REASONS = (
    "unmeasured: missing acquisition metadata",
    "unmeasured: unknown derivation roots",
    "unmeasured: legacy identity",
)


class _Reading:
    def __init__(self, ref: dict[str, str]) -> None:
        self.ref = ref
        self.event: Event | None = None
        self.reasons: list[str] = []
        self.slot = False
        self.channel: str | None = None
        self.observation_anchor: str | None = None
        self.roots: frozenset[str] | None = None
        self.conclusion_id: str | None = None
        self.contract: str | None = None
        self.polarity: str | None = None


def _events_from_conn(conn: sqlite3.Connection) -> list[Event]:
    loaded: list[Event] = []
    for row in conn.execute("SELECT payload FROM events ORDER BY position"):
        payload = json.loads(cast(str, row[0]))
        if isinstance(payload, dict):
            loaded.append(Event(cast(dict[str, object], payload)))
    return loaded


def _polarity(event: Event, acquisition: dict[str, object]) -> str | None:
    alternative = acquisition.get("alternative")
    if not isinstance(alternative, str) or not alternative:
        return None
    if event.kind == VERIFICATION_OUTCOME_KIND:
        accept = event.data.get("verifier_accept")
        if not isinstance(accept, bool):
            return None
        return ("support:" if accept else "oppose:") + alternative
    stance = acquisition.get("stance")
    if stance == "supports":
        return "support:" + alternative
    if stance == "opposes":
        return "oppose:" + alternative
    return None


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


def _poison_duplicates(readings: list[_Reading]) -> None:
    by_event: dict[str, list[_Reading]] = {}
    by_verification: dict[str, list[_Reading]] = {}
    by_correlation: dict[tuple[str, str, str, str], list[_Reading]] = {}
    for reading in readings:
        event = reading.event
        if event is None:
            continue
        event_id = event.raw.get("event_id")
        if isinstance(event_id, str):
            by_event.setdefault(event_id, []).append(reading)
        if event.kind != VERIFICATION_OUTCOME_KIND:
            continue
        data = event.data
        verification_id = data.get("verification_id")
        if isinstance(verification_id, str):
            by_verification.setdefault(verification_id, []).append(reading)
        protocol_id = data.get("protocol_id")
        attempt_id = data.get("attempt_id")
        verifier_id = data.get("verifier_id")
        verifier_version = data.get("verifier_version")
        if (
            isinstance(protocol_id, str)
            and isinstance(attempt_id, str)
            and isinstance(verifier_id, str)
            and isinstance(verifier_version, str)
        ):
            key = (protocol_id, attempt_id, verifier_id, verifier_version)
            by_correlation.setdefault(key, []).append(reading)

    def poison(group: list[_Reading], reason: str) -> None:
        if len(group) < 2:
            return
        for reading in group:
            reading.slot = False
            if reason not in reading.reasons:
                reading.reasons.append(reason)

    for group in by_event.values():
        poison(group, "duplicate event_id")
    for group in by_verification.values():
        poison(group, "duplicate verification_id")
    for group in by_correlation.values():
        poison(group, "duplicate correlation key")


def _structurally_distinct(left: _Reading, right: _Reading) -> tuple[bool, str]:
    if left.channel == right.channel:
        return False, "same acquisition_channel"
    if left.observation_anchor == right.observation_anchor:
        return False, "same observation_anchor"
    if left.roots is None or right.roots is None:
        return False, "unmeasured: unknown derivation roots"
    if left.roots & right.roots:
        return False, "shared derivation roots"
    if left.conclusion_id != right.conclusion_id or left.contract != right.contract:
        return False, "different conclusion or contract"
    return True, ""


def _alternative(polarity: str) -> str:
    _, _, rest = polarity.partition(":")
    return rest


def consilience_status(conn: sqlite3.Connection, decision_id: str) -> dict[str, object]:
    """Classify a decision's immutable evidence refs without a second evidence store."""
    ordered = _events_from_conn(conn)
    consumer: Event | None = None
    planning: dict[str, object] | None = None
    for event in ordered:
        record = decision_protocol_data(event)
        if record is not None and record.get("decision_id") == decision_id:
            consumer = event
            planning = record
            break
    if consumer is None or planning is None:
        raise ProjectionError(f"decision {decision_id!r} is not in the projection")
    evidence_refs = planning.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        raise ProjectionError(f"decision {decision_id!r} has no evidence_refs")

    readings = [
        _classify_reading(reference, ordered, consumer) for reference in evidence_refs
    ]
    _poison_duplicates(readings)

    slots = [reading for reading in readings if reading.slot]
    pair_reasons: list[str] = []
    disagreed: tuple[_Reading, _Reading] | None = None
    converged: tuple[_Reading, _Reading] | None = None
    for index, left in enumerate(slots):
        for right in slots[index + 1 :]:
            distinct, reason = _structurally_distinct(left, right)
            if not distinct:
                pair_reasons.append(reason)
                continue
            if left.polarity == right.polarity:
                if converged is None:
                    converged = (left, right)
                continue
            if (
                left.polarity is not None
                and right.polarity is not None
                and _alternative(left.polarity) == _alternative(right.polarity)
            ):
                if disagreed is None:
                    disagreed = (left, right)
                continue
            pair_reasons.append("different alternatives")

    qualifying: tuple[_Reading, _Reading] | None
    if disagreed is not None:
        status = "disagreed"
        qualifying = disagreed
        summary = ["opposed structural anchors"]
    elif converged is not None:
        status = "converged"
        qualifying = converged
        summary = ["qualifying pair"]
    else:
        qualifying = None
        unmeasured = any(
            any(marker in reason for marker in _UNMEASURED_REASONS)
            for reading in readings
            for reason in reading.reasons
        )
        if unmeasured:
            status = "unmeasured"
            summary = ["unmeasured: missing or unknown acquisition metadata"]
        else:
            status = "insufficient"
            summary = ["no qualifying pair"]

    qualifying_refs = (
        [qualifying[0].ref, qualifying[1].ref] if qualifying is not None else []
    )
    selected = {id(item) for item in qualifying} if qualifying is not None else set()
    non_qualifying_refs = [
        {"ref": reading.ref, "reasons": list(reading.reasons)}
        for reading in readings
        if id(reading) not in selected
    ]
    reasons = list(summary)
    reasons.extend(pair_reasons)
    for reading in readings:
        reasons.extend(reading.reasons)
    unique_reasons: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        unique_reasons.append(reason)
    return {
        "status": status,
        "qualifying_refs": qualifying_refs,
        "non_qualifying_refs": non_qualifying_refs,
        "reasons": unique_reasons,
    }

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
import sqlite3
from pathlib import Path
from typing import cast

from .events import (
    CANDIDATE_EXPOSED_KIND,
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
    event_sha256,
    read_all,
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
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    events, rejected = read_all(log_dir)
    resolved_workspace = workspace if workspace is not None else _infer_workspace(log_dir)
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
        workspace=resolved_workspace,
    )
    _apply_rejections(conn, rejected)
    _derive_review_queue_state(conn, events)
    conn.commit()
    return conn


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


def relational_quarantine_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM relational_quarantines").fetchone()[0])


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
    start = int(queue["start_position"])
    cap = int(queue["stream_cap"])
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
            if component.data.get("start_token") != exposure_event.data.get("start_token"):
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


def _apply_candidate_exposed(conn: sqlite3.Connection, position: int, event: Event) -> None:
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
    via = data.get("via")
    principal = data.get("principal")
    normalized_via = via.strip().casefold() if isinstance(via, str) else None
    if normalized_via == "phone_webauthn":
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
        cast(str, event.raw["event_id"]): event for event in events if "event_id" in event.raw
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
        common + ("quota", q["window"], q["used_fraction"], q.get("resets_at"),
                  None, None, None, q["provenance"])
        for q in data.get("quotas", [])
    ]
    rows += [
        common + ("spend", None, None, None,
                  s["amount"], s["currency"], s["period"], s["provenance"])
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
        raise ProjectionError(
            f"duplicate estimate_id {estimate_id!r} at position {position}"
        )
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
    return [cast(dict[str, object], json.loads(cast(str, row[0]))["data"]) for row in rows]


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
        conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM record_defects").fetchone()[0]
    )
    conn.execute(
        "INSERT INTO record_defects (id, position, record_id, defect_kind, detail)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            next_id,
            position,
            record_id,
            defect_kind,
            json.dumps(detail, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
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
            fact
            for fact in group
            if cast(str, fact["record_id"]) not in superseded_by
        ]
        tip_ids = {cast(str, fact["record_id"]) for fact in tips}
        group_invalidated = [
            by_record_id[record_id]
            for record_id in sorted(record_ids & invalidated)
        ]
        defects: list[dict[str, object]] = []
        for record_id in sorted(record_ids):
            defects.extend(defects_by_record.get(record_id, []))

        blocked = any(
            cast(str, fact["object_status"]) != "ok" for fact in tips
        ) or any(defects_by_record.get(cast(str, fact["record_id"])) for fact in tips)

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
            key=lambda fact: (cast(int, fact["position"]), cast(str, fact["record_id"])),
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


def memory_record_rows(conn: sqlite3.Connection) -> list[tuple[str, tuple[object, ...]]]:
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
        rows.append(
            (
                "record_temporal",
                (
                    view["source"],
                    view["status"],
                    (view["current"] or {}).get("record_id")
                    if view["current"]
                    else None,
                    json.dumps(
                        [fact["record_id"] for fact in view["history"]],
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        [fact["record_id"] for fact in view["contested_heads"]],
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        [fact["record_id"] for fact in view["invalidated"]],
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

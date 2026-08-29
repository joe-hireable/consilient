"""The tables the projection writes into, and the writers that need nothing but them.

Every `CREATE TABLE` and `CREATE INDEX` the projection uses lives in `SCHEMA` and is
executed once, against a fresh temporary database, at the start of a rebuild. Holding
the whole shape in one string means a column cannot be added in one place and forgotten
in another, and it makes a schema change a single readable block rather than a scatter
of statements across a dozen handlers.

Three functions sit beside it because they speak to nothing but those tables: the usage
applier, the native work-item applier, and the reader that folds work items into their
declared state groups. The usage applier is the one worth reading, because it writes a
row even when there is no figure to write.

V0-30: a provider that reported no usable figure still projects a row, so "could not be
read" is visible in the state rather than absent from it.

Nothing here re-decides what is admissible. Validation happened when the event was
appended; a projection that made its own judgement would be a second authority over the
record, and the two would eventually disagree."""

from __future__ import annotations
import json
import sqlite3
from typing import cast
from .events import (
    Event,
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
    id         INTEGER PRIMARY KEY,
    path       TEXT NOT NULL,
    line       INTEGER NOT NULL,
    reason     TEXT NOT NULL,
    -- The kind is KNOWN when the line is refused and was being thrown away. Callers then
    -- recovered it by searching `reason`, which is free-form prose: unit X01's review measured
    -- both errors that follows from -- a quarantine whose text merely mentions a kind read as
    -- that kind, and a kind whose refusal text does not name it read as absent.
    event_kind TEXT NOT NULL DEFAULT ''
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
    id         INTEGER PRIMARY KEY,
    position   INTEGER NOT NULL,
    path       TEXT NOT NULL,
    line       INTEGER NOT NULL,
    digest     TEXT NOT NULL,
    reason     TEXT NOT NULL,
    -- Same repair as `rejections` above: `_quarantine_relational` already receives the Event,
    -- so the kind is in hand at write time and only needed storing.
    event_kind TEXT NOT NULL DEFAULT ''
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

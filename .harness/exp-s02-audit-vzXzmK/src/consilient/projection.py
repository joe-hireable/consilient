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

from .events import (
    OUTCOME_KIND,
    USAGE_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    Event,
    Rejection,
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
    human_verdict   TEXT
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
"""

class ProjectionError(RuntimeError):
    pass


def build(log_dir: Path, db_path: Path) -> sqlite3.Connection:
    """Rebuild the projection from scratch. The only path that writes the database."""
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    events, rejected = read_all(log_dir)
    _apply(conn, events)
    _apply_rejections(conn, rejected)
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


def _apply(conn: sqlite3.Connection, events: list[Event]) -> None:
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
            _apply_outcome(conn, position, event)
        elif event.kind == VERDICT_KIND:
            _apply_verdict(conn, position, event)
        elif event.kind == VERDICT_CORRECTION_KIND:
            _apply_verdict_correction(conn, position, event)
        elif event.kind == USAGE_KIND:
            _apply_usage(conn, position, event)


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


def _apply_outcome(conn: sqlite3.Connection, position: int, event: Event) -> None:
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
        raise ProjectionError(
            f"duplicate attempt_id {attempt_id!r} at position {position}"
        )
    if "human_verdict" in data:
        raise ProjectionError(
            f"{OUTCOME_KIND} cannot carry human_verdict; append a separate "
            f"{VERDICT_KIND} event"
        )
    accept = data["verifier_accept"]
    if not isinstance(accept, bool):
        raise ProjectionError(
            f"verifier_accept must be a boolean, got {type(accept).__name__} at {position}"
        )
    conn.execute(
        "INSERT INTO outcomes (position, attempt_id, ts, task, task_family,"
        " verifier_version, verifier_accept, human_verdict)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            attempt_id,
            event.raw["ts"],
            data["task"],
            data.get("task_family"),
            data.get("verifier_version"),
            int(accept),
            None,
        ),
    )


def _apply_verdict(conn: sqlite3.Connection, position: int, event: Event) -> None:
    data = event.data
    attempt_id = data.get("attempt_id")
    verdict = data.get("human_verdict")
    if verdict not in ("accept", "reject"):
        raise ProjectionError(
            f"{VERDICT_KIND} at position {position} must carry human_verdict "
            "'accept' or 'reject'"
        )
    row = conn.execute(
        "SELECT human_verdict FROM outcomes WHERE attempt_id = ?", (attempt_id,)
    ).fetchone()
    if row is None:
        raise ProjectionError(
            f"{VERDICT_KIND} at position {position} references unknown attempt "
            f"{attempt_id!r}"
        )
    if row[0] is not None:
        raise ProjectionError(
            f"attempt {attempt_id!r} already has a verdict; a second verdict at "
            f"position {position} is ambiguous"
        )
    conn.execute(
        "UPDATE outcomes SET human_verdict = ? WHERE attempt_id = ?",
        (verdict, attempt_id),
    )


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
        raise ProjectionError(
            f"{VERDICT_CORRECTION_KIND} at position {position} references unknown "
            f"attempt {attempt_id!r}"
        )
    current = row[0]
    if current is None:
        raise ProjectionError(
            f"attempt {attempt_id!r} has no verdict to correct at position {position}"
        )
    if current != previous:
        raise ProjectionError(
            f"{VERDICT_CORRECTION_KIND} at position {position} expected prior verdict "
            f"{previous!r}, found {current!r}"
        )
    conn.execute(
        "UPDATE outcomes SET human_verdict = ? WHERE attempt_id = ?",
        (verdict, attempt_id),
    )


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

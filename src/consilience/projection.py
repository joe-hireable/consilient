"""SQLite projection of the trajectory.

V0-02: SQLite is only a projection of the JSONL. Delete it, replay, and the state is
identical. Nothing may write to the database except a replay of events.

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

from .events import Event, Rejection, read_all

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
    ts              TEXT NOT NULL,
    task            TEXT NOT NULL,
    task_family     TEXT,
    verifier_version TEXT,
    verifier_accept INTEGER NOT NULL,
    human_verdict   TEXT
);
CREATE INDEX IF NOT EXISTS outcomes_family ON outcomes (task_family, verifier_version);
CREATE TABLE IF NOT EXISTS rejections (
    id     INTEGER PRIMARY KEY,
    path   TEXT NOT NULL,
    line   INTEGER NOT NULL,
    reason TEXT NOT NULL
);
"""

# The one event kind that carries an acceptance observation. Anything else is context.
OUTCOME_KIND = "attempt.outcome"


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


def _apply_outcome(conn: sqlite3.Connection, position: int, event: Event) -> None:
    data = event.data
    for field in ("task", "verifier_accept"):
        if field not in data:
            raise ProjectionError(
                f"{OUTCOME_KIND} at position {position} is missing {field!r}"
            )
    accept = data["verifier_accept"]
    if not isinstance(accept, bool):
        raise ProjectionError(
            f"verifier_accept must be a boolean, got {type(accept).__name__} at {position}"
        )
    verdict = data.get("human_verdict")
    if verdict not in (None, "accept", "reject"):
        raise ProjectionError(
            f"human_verdict must be 'accept', 'reject' or absent, got {verdict!r}"
        )
    conn.execute(
        "INSERT INTO outcomes (position, ts, task, task_family, verifier_version,"
        " verifier_accept, human_verdict) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            position,
            event.raw["ts"],
            data["task"],
            data.get("task_family"),
            data.get("verifier_version"),
            int(accept),
            verdict,
        ),
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

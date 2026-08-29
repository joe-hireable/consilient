"""Row-level reads and writes over the projected tables, and the vocabulary they share.

Whatever the rest of the harness wants to know about the state, it asks here: what the
log refused, what was quarantined out of a relation, which capability version is head
and which keys are contested, the revision chain behind a delivery estimate, the native
work-item rows, and the digest over the lot. The writers alongside them are the ones
that touch a single row and decide nothing -- appending a rejection, recording a
quarantine, moving a work item from one state to the next.

The shared vocabulary lives here too because every layer above needs it and none of it
needs anything above: the projection version and its meta key, the frozen set of event
kinds a handler claims, and the error raised when the log says something the tables
cannot represent.

"Byte-identical state" is checked as a digest over a canonical dump of every row, not
over the database file. SQLite files are not byte-stable across writes — page ordering,
freelists and the header's change counter all move — so a file-level comparison would
fail for reasons that have nothing to do with state. The row dump is the honest form of
the invariant.

The quarantine writer is the reason so little else here raises. A relation that cannot
be honoured becomes a row with a reason attached, so a mixed or partial log still
replays to a state that says plainly what it could not accept."""

from __future__ import annotations
import hashlib
import json
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
    event_sha256,
)
from .work_items import state_group

# The SQLite header version makes a legitimate handler/schema change a third replay
# state, not Gate A2 "DIVERGED". Bump when a rebuild of the same log is expected to
# change state_digest.
PROJECTION_VERSION = 2

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


class ProjectionError(RuntimeError):
    pass


def _infer_workspace(log_dir: Path) -> Path | None:
    if log_dir.name == "log" and log_dir.parent.name == ".harness":
        return log_dir.parent.parent
    return None


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
            (index, Path(rejection.path).name, rejection.line, rejection.reason),
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


def _alternative(polarity: str) -> str:
    _, _, rest = polarity.partition(":")
    return rest

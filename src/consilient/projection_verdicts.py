"""The appliers for events that carry a judgement, each guarded by what is already
projected.

An outcome, the human verdict deferred behind it, a correction to that verdict, a
measurement result, a candidate exposure, the one review queue a trajectory is allowed,
and a delivery estimate all have to agree with rows already written before they may be
written themselves. A verdict must find an attempt that has none; a correction must find
the prior verdict it claims to be correcting; a measurement result must follow its
registration; an estimate revision must be exactly one past the last.

V0-26: an outcome and its deferred human verdict project to one row keyed by attempt_id.

Almost every failed guard quarantines rather than raises, which is what lets a log with
a duplicate or an out-of-order pair replay to a complete state that names the problem.
The exceptions are deliberate: an outcome missing a required field, carrying a verdict
it is not allowed to carry, or an estimate revision out of sequence stops the rebuild,
because those are malformations no projected row could honestly represent. How a verdict
reached the log is recorded but never upgraded -- a signature is authenticated, a
principal typed at the command line is only declared.

The duplicate poisoner applies the same discipline to evidence readings. Two references
that land on the same event, the same verification, or the same
protocol-attempt-verifier key are both struck out and told why, because one observation
cited twice is one observation.
"""

from __future__ import annotations
import json
import sqlite3
from typing import cast
from .events import (
    OUTCOME_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    VERIFICATION_OUTCOME_KIND,
    Event,
)

from .projection_rows import (
    ProjectionError,
    _Reading,
    _quarantine_relational,
    _verdict_auth_status,
)

__all__ = [
    "ProjectionError",
    "_Reading",
    "_quarantine_relational",
    "_verdict_auth_status",
]


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

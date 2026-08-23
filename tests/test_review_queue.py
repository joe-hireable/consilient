"""Q01 — freeze candidate exposure before verification."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import beta as beta_mod
from consilient import events as events_mod
from consilient import projection
from consilient import verification as verification_mod
from consilient.events import EventError, append, read_all


def _now_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


CONTRACT = "a" * 64


def _open_queue(
    log_path: Path,
    *,
    queue_id: str = "queue-001",
    task_family: str = "repair",
) -> dict[str, object]:
    opened = verification_mod.open_queue(
        log_path,
        queue_id=queue_id,
        task_family=task_family,
        population="default-branch",
        protocol_id="proto-1",
        verifier_version="v1",
        verifier_contract_digest=CONTRACT,
    )
    return opened


def _begin(
    log_path: Path,
    attempt_id: str,
    *,
    queue_id: str = "queue-001",
    artefact_sha256: str | None = None,
) -> verification_mod.AttemptStart:
    return verification_mod.begin_attempt(
        log_path,
        queue_id=queue_id,
        attempt_id=attempt_id,
        artefact_sha256=artefact_sha256 or ("0" * 64),
    )


def _component(
    attempt_id: str,
    start_token: str,
    *,
    verifier_accept: bool = True,
    verifier_id: str = "pytest",
) -> dict[str, object]:
    return verification_mod.verification_outcome_event(
        verification_id=f"ver-{attempt_id}-{verifier_id}",
        attempt_id=attempt_id,
        protocol_id="proto-1",
        artefact_sha256="0" * 64,
        verifier_id=verifier_id,
        verifier_version="v1",
        start_token=start_token,
        verifier_accept=verifier_accept,
    )


def test_review_queue_has_no_legacy_shared_verification_start_producer(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    assert hasattr(verification_mod, "begin_attempt")
    _open_queue(log_path)
    start = _begin(log_path, "attempt-1")
    assert len(start.start_token) == 64


def test_candidate_exposed_is_appended_before_component_outcome(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    start = _begin(log_path, "attempt-1")
    append(log_path, _component("attempt-1", start.start_token))

    events, _rejected = read_all(log_path.parent)
    kinds = [event.kind for event in events]
    assert kinds.index(events_mod.CANDIDATE_EXPOSED_KIND) < kinds.index(
        events_mod.VERIFICATION_OUTCOME_KIND
    )


def test_review_queue_absent_exposure_quarantines_component_outcome(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    with pytest.raises(EventError, match="start_token"):
        append(
            log_path,
            _component("attempt-1", "b" * 64),
        )


def test_review_queue_late_exposure_quarantines_component_outcome(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    opened = _open_queue(log_path)
    queue_data = opened["data"]
    outcome = verification_mod.verification_outcome_event(
        verification_id="ver-late",
        attempt_id="attempt-late",
        protocol_id="proto-1",
        artefact_sha256="0" * 64,
        verifier_id="pytest",
        verifier_version="v1",
        start_token="c" * 64,
    )
    exposure = {
        "v": events_mod.SCHEMA_VERSION,
        "ts": _now_ts(1),
        "event": events_mod.CANDIDATE_EXPOSED_KIND,
        "actor": "consilient.verification",
        "data": {
            "queue_id": queue_data["queue_id"],
            "exposure_id": "late-exposure",
            "attempt_id": "attempt-late",
            "exposure_ordinal": 2,
            "start_token": "c" * 64,
            "artefact_sha256": "0" * 64,
            "task_family": queue_data["task_family"],
            "protocol_id": queue_data["protocol_id"],
            "verifier_version": queue_data["verifier_version"],
            "verifier_contract_digest": queue_data["verifier_contract_digest"],
        },
    }
    lines = [
        json.dumps(opened, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        json.dumps(exposure, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn = projection.build(log_path.parent, tmp_path / "state.db")
    relational = projection.relational_quarantines(conn)
    assert any("precedes its candidate.exposed" in row["reason"] for row in relational)
    conn.close()


def test_review_queue_selector_overflow_refuses_exposure(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    opened = _open_queue(log_path)
    stream_cap = int(opened["data"]["stream_cap"])
    for index in range(stream_cap):
        _begin(log_path, f"attempt-{index}")
    with pytest.raises(EventError, match="stream_cap"):
        _begin(log_path, "attempt-overflow")


def test_review_queue_duplicate_attempt_gets_distinct_start_tokens(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    first = _begin(log_path, "attempt-1", artefact_sha256="1" * 64)
    second = _begin(log_path, "attempt-1", artefact_sha256="2" * 64)
    assert first.start_token != second.start_token


def test_review_queue_replay_reproduces_selected_exposure_order(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    starts = [_begin(log_path, f"attempt-{index}") for index in range(3)]
    for index, start in enumerate(starts):
        append(log_path, _component(f"attempt-{index}", start.start_token))
    conn = projection.build(log_path.parent, tmp_path / "state.db")
    selected = projection.selected_exposure_rows(conn)
    assert [row["exposure_ordinal"] for row in selected] == [1, 2, 3]
    assert projection.sampling_unconditioned(conn) is True
    conn.close()


def test_review_queue_manifest_invariant_to_verifier_values(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    starts = [_begin(log_path, f"attempt-{index}") for index in range(2)]
    for index, start in enumerate(starts):
        append(
            log_path,
            _component(
                f"attempt-{index}",
                start.start_token,
                verifier_accept=index == 0,
                verifier_id=f"check-{index}",
            ),
        )
    conn1 = projection.build(log_path.parent, tmp_path / "state1.db")
    selected1 = projection.selected_exposure_rows(conn1)
    digest1 = projection.state_digest(conn1)
    conn1.close()

    log_path2 = tmp_path / "log2" / "2026-08-23.jsonl"
    _open_queue(log_path2)
    starts2 = [_begin(log_path2, f"attempt-{index}") for index in range(2)]
    for index, start in enumerate(starts2):
        flipped = verification_mod.verification_outcome_event(
            verification_id=f"ver-alt-{index}",
            attempt_id=f"attempt-{index}",
            protocol_id="proto-1",
            artefact_sha256="0" * 64,
            verifier_id=f"mutated-{index}",
            verifier_version="v9",
            start_token=start.start_token,
            verifier_accept=not (index == 0),
        )
        append(log_path2, flipped)

    conn2 = projection.build(log_path2.parent, tmp_path / "state2.db")
    selected2 = projection.selected_exposure_rows(conn2)
    digest2 = projection.state_digest(conn2)
    conn2.close()

    assert [row["attempt_id"] for row in selected1] == [row["attempt_id"] for row in selected2]
    assert [row["exposure_ordinal"] for row in selected1] == [row["exposure_ordinal"] for row in selected2]
    assert digest1 != digest2


def test_beta_sampling_flag_projection_derived_not_caller_set(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    start = _begin(log_path, "attempt-1")
    append(log_path, _component("attempt-1", start.start_token))
    conn = projection.build(log_path.parent, tmp_path / "state.db")
    assert projection.sampling_unconditioned(conn) is True
    forced = beta_mod.from_connection(conn, sampling_unconditioned=False)
    assert forced.lower_bound_on_joint_error is True
    conn.close()


def test_review_queue_incomplete_outcome_keeps_sampling_false(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    _begin(log_path, "attempt-1")
    conn = projection.build(log_path.parent, tmp_path / "state.db")
    assert projection.sampling_unconditioned(conn) is False
    conn.close()


def test_verification_start_source_scan_finds_no_bypass() -> None:
    assert verification_mod.coverage_gate_passed()
    assert verification_mod.scan_component_outcome_producers() == []


def test_review_queue_version_drift_refuses_manifest(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    opened = _open_queue(log_path)
    bad = dict(opened)
    bad["data"] = dict(opened["data"])
    bad["data"]["verifier_version"] = "v999"
    with pytest.raises(EventError, match="eligible_universe_digest"):
        events_mod.validate(bad)


def test_review_queue_projection_deletion_replay_is_identical(tmp_path: Path) -> None:
    log_path = tmp_path / "log" / "2026-08-23.jsonl"
    _open_queue(log_path)
    start = _begin(log_path, "attempt-1")
    append(log_path, _component("attempt-1", start.start_token))
    db = tmp_path / "state.db"
    conn1 = projection.build(log_path.parent, db)
    digest1 = projection.state_digest(conn1)
    selected1 = projection.selected_exposure_rows(conn1)
    sampling1 = projection.sampling_unconditioned(conn1)
    conn1.close()
    conn2 = projection.build(log_path.parent, db)
    digest2 = projection.state_digest(conn2)
    selected2 = projection.selected_exposure_rows(conn2)
    sampling2 = projection.sampling_unconditioned(conn2)
    conn2.close()
    assert digest1 == digest2
    assert selected1 == selected2
    assert sampling1 == sampling2 is True

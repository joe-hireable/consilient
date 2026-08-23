"""V01 — authenticated human beta projection and relational quarantine."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import beta as beta_mod
from consilient import events as events_mod
from consilient import projection
from consilient.cli import main
from consilient.events import SCHEMA_VERSION, append, canonical


def _now_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


HUMAN = "joe-brown"


def _ev(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _outcome(
    attempt_id: str,
    task: str,
    accept: bool,
    *,
    component_join_required: bool = False,
) -> dict[str, object]:
    data: dict[str, object] = {
        "attempt_id": attempt_id,
        "task": task,
        "verifier_accept": accept,
        "task_family": "repair",
        "verifier_version": "v1",
    }
    if component_join_required:
        data["component_join_required"] = True
    return _ev(event=events_mod.OUTCOME_KIND, data=data)


def _verdict(
    attempt_id: str,
    human_verdict: str,
    *,
    via: str = "cli",
    principal: str = HUMAN,
) -> dict[str, object]:
    return _ev(
        actor=HUMAN,
        event=events_mod.VERDICT_KIND,
        data={
            "attempt_id": attempt_id,
            "human_verdict": human_verdict,
            "principal": principal,
            "via": via,
        },
    )


def _correction(
    attempt_id: str,
    previous: str,
    human_verdict: str,
    reason: str,
) -> dict[str, object]:
    return _ev(
        actor=HUMAN,
        event=events_mod.VERDICT_CORRECTION_KIND,
        data={
            "attempt_id": attempt_id,
            "previous_verdict": previous,
            "human_verdict": human_verdict,
            "reason": reason,
            "principal": HUMAN,
            "via": "cli",
        },
    )


def _verification_outcome(attempt_id: str) -> dict[str, object]:
    return _ev(
        event=events_mod.VERIFICATION_OUTCOME_KIND,
        data={
            "verification_id": f"ver-{attempt_id}",
            "attempt_id": attempt_id,
            "protocol_id": "proto-1",
            "artefact_sha256": "a" * 64,
            "verifier_id": "check-1",
            "verifier_version": "v1",
            "evidence_class": "measured",
            "status": "completed",
            "verifier_accept": True,
        },
    )


def _proxy_record(estimand_kind: str) -> dict[str, object]:
    return {
        "ts": _now_ts(),
        "task_family": "repair",
        "verifier_version": "v1",
        "verifier_accept": True,
        "human_verdict": "reject",
        "estimand_kind": estimand_kind,
        "auth_status": "authenticated",
    }


def _write_log(path: Path, *lines: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(canonical(line) for line in lines) + "\n",
        encoding="utf-8",
    )


def test_proxy_estimands_never_project_as_human_beta_or_sizing_input() -> None:
    estimands = [
        beta_mod.HUMAN_VERDICT_BETA,
        "mutation_proxy_beta",
        "critic_proxy_beta",
        "repository_consequence_false_shipment_cohort_lower_bound",
    ]
    records = [_proxy_record(kind) for kind in estimands]
    for record in records:
        admitted = beta_mod.admits_human_beta_row(record)
        sizing = beta_mod.admits_sizing_input(record)
        if record["estimand_kind"] == beta_mod.HUMAN_VERDICT_BETA:
            assert admitted and sizing
        else:
            assert not admitted and not sizing

    routing_source = (
        Path(__file__).resolve().parents[1] / "src" / "consilient" / "routing.py"
    )
    text = routing_source.read_text(encoding="utf-8")
    for proxy in (
        "mutation_proxy_beta",
        "critic_proxy_beta",
        "repository_consequence_false_shipment_cohort_lower_bound",
    ):
        assert proxy not in text


def test_relational_rejections_are_quarantined_and_beta_remains_complete(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-001", "first-task", True),
        _outcome("attempt-001", "second-task", True),
        _outcome("attempt-002", "orphan-task", True),
        _verdict("missing-attempt", "reject"),
        _verdict("attempt-002", "accept"),
        _verdict("attempt-002", "reject"),
        _correction("attempt-003", "reject", "accept", "wrong prior"),
        _outcome("attempt-004", "needs-join", True, component_join_required=True),
        _verdict("attempt-004", "reject"),
    )

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert len(relational) >= 5
    reasons = " ".join(str(row["reason"]) for row in relational)
    assert "duplicate attempt_id" in reasons
    assert "unknown attempt" in reasons
    assert "already has a verdict" in reasons
    assert "no verdict to correct" in reasons or "expected prior verdict" in reasons or "unknown attempt" in reasons
    assert "missing component" in reasons

    outcomes = conn.execute(
        "SELECT attempt_id, human_verdict FROM outcomes ORDER BY position"
    ).fetchall()
    assert ("attempt-001", None) in outcomes
    assert ("attempt-002", "accept") in outcomes

    beta_result = beta_mod.from_connection(conn)
    assert beta_result.n_rejected == 0
    conn.close()


def test_legacy_declared_principal_row_projects_but_not_counts_as_authenticated(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-legacy", "legacy-task", True),
        _verdict("attempt-legacy", "reject", via="cli"),
    )

    conn = projection.build(log_dir, db)
    row = conn.execute(
        "SELECT estimand_kind, auth_status, human_verdict FROM outcomes WHERE attempt_id = ?",
        ("attempt-legacy",),
    ).fetchone()
    assert row == (beta_mod.HUMAN_VERDICT_BETA, "declared_principal", "reject")

    beta_result = beta_mod.from_connection(conn)
    assert beta_result.n_rejected == 0
    assert beta_result.verdict == beta_mod.INSUFFICIENT
    conn.close()


def test_authenticated_human_beta_row_enters_compute(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for index in range(30):
        attempt = f"attempt-{index}"
        append(path, _outcome(attempt, f"task-{index}", True))
        append(path, _verdict(attempt, "reject", via="cli"))

    conn = projection.build(log_dir, db)
    conn.execute("UPDATE outcomes SET auth_status = ?", ("authenticated",))
    conn.commit()
    beta_result = beta_mod.from_connection(conn)
    assert beta_result.n_rejected == 30
    assert beta_result.verdict == beta_mod.MEASURED
    conn.close()


def test_rebuild_twice_yields_identical_quarantine_and_beta(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-001", "task-a", True),
        _verdict("orphan", "reject"),
        _outcome("attempt-002", "task-b", True),
        _verdict("attempt-002", "reject", via="cli"),
    )

    conn1 = projection.build(log_dir, db)
    digest1 = projection.state_digest(conn1)
    relational1 = projection.relational_quarantines(conn1)
    beta1 = beta_mod.from_connection(conn1)
    conn1.close()

    conn2 = projection.build(log_dir, db)
    digest2 = projection.state_digest(conn2)
    relational2 = projection.relational_quarantines(conn2)
    beta2 = beta_mod.from_connection(conn2)
    conn2.close()

    assert digest1 == digest2
    assert relational1 == relational2
    assert beta1.as_dict() == beta2.as_dict()


def test_beta_outputs_show_quarantine_sampling_and_oracle_caveat(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-001", "task-a", True),
        _verdict("orphan", "reject"),
        _outcome("attempt-002", "task-b", True),
        _verdict("attempt-002", "reject", via="cli"),
    )

    argv = ["--log", str(log_dir), "--db", str(db), "beta", "--json"]
    assert main(argv) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["relational_quarantine_count"] >= 1
    assert payload["relational_quarantine"]
    assert payload["sampling_unconditioned"] is False
    assert "caveat" in payload
    assert "non-stationary" in payload["caveat"]

    assert main(["--log", str(log_dir), "--db", str(db), "beta"]) == 0
    human = capsys.readouterr().out
    assert "relational quarantine" in human.lower() or "QUARANTINE" in human
    assert "NOT a bound" in human or "sampling" in human.lower()
    assert "non-stationary" in human


def test_from_connection_honours_sampling_unconditioned_argument(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for index in range(30):
        attempt = f"attempt-{index}"
        append(path, _outcome(attempt, f"task-{index}", True))
        append(path, _verdict(attempt, "reject", via="cli"))
    conn = projection.build(log_dir, db)
    conn.execute("UPDATE outcomes SET auth_status = ?", ("authenticated",))
    projection.set_sampling_unconditioned(conn, True)
    conn.commit()
    declared = beta_mod.from_connection(conn)
    assert declared.lower_bound_on_joint_error is True
    conn.close()


def test_missing_component_join_quarantined_when_verification_exists(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    _write_log(
        path,
        _outcome("attempt-ok", "task-ok", True, component_join_required=True),
        _verification_outcome("attempt-ok"),
        _verdict("attempt-ok", "reject", via="cli"),
    )

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert not any("missing component" in str(row["reason"]) for row in relational)
    assert conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0] == 1
    conn.close()

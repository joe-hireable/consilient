"""X01 — measurement registration event and fail-closed projection join.

Acceptance command (the design table named no pytest invocation; this file is it):

    python -m pytest tests/test_measurement.py -q

The Done row said "replay of a result with no registration raises". That is
wrong against this repository's projection contract: ``projection.build``
quarantines relational defects and still returns, matching
``verification.outcome`` without ``candidate.exposed`` and preserving V0-02
replay of mixed logs. The fail-closed *join* is ``joined_measurement_results``,
which raises ``ProjectionError`` on an unmatched result.

Incumbent: MLPerf Logging ``compliance_checker``
(https://github.com/mlcommons/logging, retrieved 2026-08-28). Invalid lifecycle
fails the checker; the log remains readable.

"X01 matches that split" stood here as an unmeasured claim. The comparison has now
been RUN (29 August 2026), against mlperf-logging 4.1.62 in a throwaway venv, giving
both systems the same three shapes:

    shape       MLPerf compliance_checker      Consilient
    valid       0 failed checks                accepted
    orphan      1 failed check                 refused at REPLAY
    back-dated  0 failed checks                refused at WRITE

Both catch the orphan. Only this refuses the back-dated log -- the one whose file
order reads correctly while its timestamps say the result preceded its registration.
Principle 9 asks for the bar and the evidence; this is the evidence.

"A CI-wired failing gate is BU2 and is not this unit" is also withdrawn, because
it is no longer true: ``cmd_beta`` calls ``joined_measurement_results``, so the
guard runs whenever β is computed and ``consil beta`` exits 2 with the reason
rather than publishing a number it cannot stand behind.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import events as events_mod
from consilient import projection
from consilient.events import EventError, SCHEMA_VERSION, canonical, validate


def _now_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _ev(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": events_mod.MEASUREMENT_REGISTERED_KIND,
        "actor": events_mod.MEASUREMENT_ACTOR,
        "data": {},
    }
    base.update(over)
    return base


def _registered(
    run_id: str,
    *,
    config_hash: str = "a" * 64,
    hardware_id: str = "amd-9950x3d-win11",
) -> dict[str, object]:
    return _ev(
        data={
            "run_id": run_id,
            "config_hash": config_hash,
            "hardware_id": hardware_id,
        },
    )


def _result(run_id: str, *, fixture: str = "fanout-8-models") -> dict[str, object]:
    return _ev(
        event=events_mod.MEASUREMENT_RESULT_KIND,
        data={"run_id": run_id, "fixture": fixture},
    )


def _write_log(path: Path, *lines: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(canonical(line) for line in lines) + "\n",
        encoding="utf-8",
    )


def test_measurement_registered_requires_fixed_fields() -> None:
    with pytest.raises(EventError, match="run_id"):
        validate(_ev(data={"config_hash": "a" * 64, "hardware_id": "hw-1"}))
    with pytest.raises(EventError, match="config_hash"):
        validate(_ev(data={"run_id": "run-1", "hardware_id": "hw-1"}))
    with pytest.raises(EventError, match="hardware_id"):
        validate(_ev(data={"run_id": "run-1", "config_hash": "a" * 64}))


def test_measurement_result_requires_run_id_and_fixture() -> None:
    with pytest.raises(EventError, match="fixture"):
        validate(_result("run-1", fixture=""))
    with pytest.raises(EventError, match="run_id"):
        validate(
            _ev(
                event=events_mod.MEASUREMENT_RESULT_KIND,
                data={"run_id": "", "fixture": "fanout-8-models"},
            )
        )


def test_orphan_measurement_result_quarantined_on_replay(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    _write_log(log_dir / "2026-08-23.jsonl", _result("20260823T184318-edb77f1e88"))

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert any(
        "measurement.registered" in str(row["reason"])
        and "20260823T184318-edb77f1e88" in str(row["reason"])
        for row in relational
    )
    assert conn.execute("SELECT COUNT(*) FROM measurement_results").fetchone()[0] == 0
    with pytest.raises(projection.ProjectionError, match="measurement.registered"):
        projection.joined_measurement_results(conn)
    conn.close()


def test_registered_then_result_projects(tmp_path: Path) -> None:
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    _write_log(
        log_dir / "2026-08-23.jsonl",
        _registered(run_id),
        _result(run_id),
    )

    conn = projection.build(log_dir, db)
    assert conn.execute("SELECT COUNT(*) FROM measurement_registrations").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM measurement_results").fetchone()[0] == 1
    assert projection.relational_quarantines(conn) == []
    joined = projection.joined_measurement_results(conn)
    assert len(joined) == 1
    assert joined[0]["run_id"] == run_id
    assert joined[0]["fixture"] == "fanout-8-models"
    assert joined[0]["config_hash"] == "a" * 64
    assert joined[0]["hardware_id"] == "amd-9950x3d-win11"
    conn.close()


def test_duplicate_registration_quarantines_second_row(tmp_path: Path) -> None:
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    _write_log(
        log_dir / "2026-08-23.jsonl",
        _registered(run_id),
        _registered(run_id, hardware_id="other-hardware"),
    )

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert any("duplicate run_id" in str(row["reason"]) for row in relational)
    assert conn.execute("SELECT COUNT(*) FROM measurement_registrations").fetchone()[0] == 1
    conn.close()


def test_result_before_registration_quarantines(tmp_path: Path) -> None:
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    _write_log(
        log_dir / "2026-08-23.jsonl",
        _result(run_id),
        _registered(run_id),
    )

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert any("measurement.registered" in str(row["reason"]) for row in relational)
    assert conn.execute("SELECT COUNT(*) FROM measurement_results").fetchone()[0] == 0
    with pytest.raises(projection.ProjectionError, match="measurement.registered"):
        projection.joined_measurement_results(conn)
    conn.close()


def test_duplicate_registration_does_not_fail_the_join(tmp_path: Path) -> None:
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    db = tmp_path / "state.db"
    _write_log(
        log_dir / "2026-08-23.jsonl",
        _registered(run_id),
        _registered(run_id, hardware_id="other-hardware"),
        _result(run_id),
    )

    conn = projection.build(log_dir, db)
    relational = projection.relational_quarantines(conn)
    assert any("duplicate run_id" in str(row["reason"]) for row in relational)
    joined = projection.joined_measurement_results(conn)
    assert len(joined) == 1
    assert joined[0]["hardware_id"] == "amd-9950x3d-win11"
    conn.close()


def test_measurement_registered_rejects_wrong_actor_and_non_digest_hash() -> None:
    with pytest.raises(EventError, match="consilient.measurement"):
        validate(
            _ev(
                actor="consilient.cli",
                data={
                    "run_id": "run-1",
                    "config_hash": "a" * 64,
                    "hardware_id": "hw-1",
                },
            )
        )
    with pytest.raises(EventError, match="config_hash"):
        validate(
            _ev(
                data={
                    "run_id": "run-1",
                    "config_hash": "A" * 64,
                    "hardware_id": "hw-1",
                }
            )
        )


# --- X01 review findings 2 and 3, fixed 29 August 2026 --------------------------------------
#
# The join decided which quarantines were about a measurement by searching the free-form
# `reason` text for the literal "measurement.result". The review measured both errors that
# produces, and they point in opposite directions. Both tables now carry `event_kind`, which
# was known at write time and was being discarded.


def test_a_quarantine_of_another_kind_is_not_a_measurement_failure(tmp_path: Path) -> None:
    """FALSE POSITIVE: prose that merely mentions the kind must not fail the join.

    A quarantine belonging to some other kind can name measurement.result in its reason --
    "no measurement.result for this registration yet" is an ordinary thing to write. Under the
    old substring test that raised ProjectionError even though every result present had joined
    correctly, so a healthy log could not be published.
    """
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    _write_log(
        log_dir / "2026-08-23.jsonl",
        _registered(run_id),
        _result(run_id),
    )
    conn = projection.build(log_dir, tmp_path / "state.db")
    conn.execute(
        "INSERT INTO relational_quarantines"
        " (position, path, line, digest, reason, event_kind)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (0, "2026-08-23.jsonl", 1, "d" * 64,
         "duplicate registration; no measurement.result seen for it",
         events_mod.MEASUREMENT_REGISTERED_KIND),
    )

    joined = projection.joined_measurement_results(conn)

    assert [row["run_id"] for row in joined] == [run_id], (
        "a quarantine of a different kind blocked the join because its reason text mentioned "
        "measurement.result; the join must read the kind, not the prose"
    )
    conn.close()


def test_a_schema_rejected_result_still_fails_the_join(tmp_path: Path) -> None:
    """FALSE NEGATIVE: a result refused by the SCHEMA never reaches relational quarantines.

    It is a read-level rejection, so the old check could not see it and the join returned
    normally while a result had in fact been thrown away -- the exact opposite of fail-closed.
    """
    run_id = "20260823T184318-edb77f1e88"
    log_dir = tmp_path / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    # Written as raw text: `canonical` would refuse to render an invalid event, and the point
    # is a line that reaches the log and is refused when READ.
    (log_dir / "2026-08-23.jsonl").write_text(
        canonical(_registered(run_id))
        + "\n"
        + canonical(_result(run_id)).replace('"fixture":"fanout-8-models"', '"fixture":""')
        + "\n",
        encoding="utf-8",
    )
    conn = projection.build(log_dir, tmp_path / "state.db")

    refused = [
        row
        for row in projection.rejections(conn)
        if row["event_kind"] == events_mod.MEASUREMENT_RESULT_KIND
    ]
    assert refused, "the malformed result was expected to be refused at read"
    with pytest.raises(projection.ProjectionError, match="measurement join failed closed"):
        projection.joined_measurement_results(conn)
    conn.close()


def test_the_join_has_a_non_test_caller() -> None:
    """The Done criterion the review found false: a guard nothing invokes protects nothing.

    Asserted against the product source rather than by running the command, because driving
    `consil beta` needs a trajectory, a database and a task family, and would test the fixture
    more than the wiring. What must be true is that a non-test module calls it at all.
    """
    import subprocess

    listing = subprocess.run(
        ["git", "grep", "-l", "joined_measurement_results", "--", "src/consilient"],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.split()
    callers = [
        path
        for path in listing
        if not path.endswith(("projection.py", "projection_consilience.py"))
    ]
    assert callers, (
        "joined_measurement_results is defined and re-exported but called by nothing outside "
        "its own module; it was dead code presented as a publication guard"
    )

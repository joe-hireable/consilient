"""X01 — measurement registration event and fail-closed projection join."""

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
    conn.close()

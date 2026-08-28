"""Release dispatch claims only when a start_failed run's worker is confirmed gone.

Unit AQ: N00 detects start_failed from artefact silence; this unit closes the
claim only when liveness proves the worker is not running. Releasing a merely
slow worker would admit two agents to one path — worse than an hour's delay.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import coordination, work_items
from consilient.events import read_all

T0 = datetime(2026, 8, 24, 13, 0, 0, tzinfo=timezone.utc)


def _live(log: Path, *, now: datetime = T0) -> tuple[coordination.Claim, ...]:
    events, rejected = read_all(log)
    assert not rejected
    return coordination.live_claims(events, now=now)


def _open(log: Path, *, run_id: str, cwd: Path, opened: datetime = T0) -> None:
    coordination.open_claim(
        log,
        run_id=run_id,
        paths=[f"src/{run_id}.py"],
        cwd=cwd,
        timeout_s=3600,
        harness="codex",
        now=opened,
    )


def test_releases_claim_when_worker_is_confirmed_gone(tmp_path: Path) -> None:
    log = tmp_path / "log"
    _open(log, run_id="dead-run", cwd=tmp_path)

    results = coordination.release_claims_when_worker_gone(
        log,
        run_ids=("dead-run",),
        worker_gone=lambda _run_id: True,
        now=T0,
    )

    assert len(results) == 1
    assert results[0].released is True
    assert _live(log) == ()
    events, _ = read_all(log)
    assert work_items.COMPLETED in [event.kind for event in events]


def test_refuses_when_worker_is_still_running_despite_artefact_silence(
    tmp_path: Path,
) -> None:
    """A silent but live worker must keep its claim — artefact silence is not enough."""
    log = tmp_path / "log"
    _open(log, run_id="slow-run", cwd=tmp_path)

    results = coordination.release_claims_when_worker_gone(
        log,
        run_ids=("slow-run",),
        worker_gone=lambda _run_id: False,
        now=T0,
    )

    assert results[0].released is False
    assert "still running" in results[0].reason
    assert _live(log) != ()


def test_refuses_when_liveness_cannot_be_determined(tmp_path: Path) -> None:
    log = tmp_path / "log"
    _open(log, run_id="unknown-run", cwd=tmp_path)

    results = coordination.release_claims_when_worker_gone(
        log,
        run_ids=("unknown-run",),
        worker_gone=lambda _run_id: None,
        now=T0,
    )

    assert results[0].released is False
    assert "unknown" in results[0].reason.casefold()
    assert _live(log) != ()


def test_skips_run_ids_with_no_live_claim(tmp_path: Path) -> None:
    log = tmp_path / "log"

    results = coordination.release_claims_when_worker_gone(
        log,
        run_ids=("never-opened",),
        worker_gone=lambda _run_id: True,
        now=T0,
    )

    assert results[0].released is False
    assert "no live claim" in results[0].reason


def test_a_second_dispatch_is_not_refused_after_a_confirmed_gone_release(
    tmp_path: Path,
) -> None:
    log = tmp_path / "log"
    _open(log, run_id="dead-run", cwd=tmp_path, opened=T0 - timedelta(minutes=10))

    coordination.release_claims_when_worker_gone(
        log,
        run_ids=("dead-run",),
        worker_gone=lambda _run_id: True,
        now=T0,
    )
    assert _live(log) == ()
    assert (
        coordination.conflict(["src/dead-run.py"], _live(log), cwd=tmp_path) is None
    )

    coordination.open_claim(
        log,
        run_id="next-run",
        paths=["src/dead-run.py"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
    )
    assert len(_live(log)) == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process semantics")
def test_worker_gone_from_pid_record_reports_gone_for_dead_pid(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    run_dir = runs / "run-a"
    run_dir.mkdir(parents=True)
    (run_dir / "process.json").write_text(
        json.dumps({"pid": 999_999}), encoding="utf-8"
    )
    assert coordination.worker_gone_from_pid_record(runs, "run-a") is True


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process semantics")
def test_worker_gone_from_pid_record_reports_gone_after_child_exit(
    tmp_path: Path,
) -> None:
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    pid = child.pid
    assert child.wait() == 0
    runs = tmp_path / "runs"
    run_dir = runs / "run-exited"
    run_dir.mkdir(parents=True)
    (run_dir / "process.json").write_text(json.dumps({"pid": pid}), encoding="utf-8")
    assert coordination.worker_gone_from_pid_record(runs, "run-exited") is True


def test_worker_gone_from_pid_record_reports_running_for_live_pid(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    run_dir = runs / "run-b"
    run_dir.mkdir(parents=True)
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        (run_dir / "process.json").write_text(
            json.dumps({"pid": child.pid}), encoding="utf-8"
        )
        assert coordination.worker_gone_from_pid_record(runs, "run-b") is False
    finally:
        child.kill()
        child.wait()


def test_worker_gone_from_pid_record_is_unknown_without_a_record(
    tmp_path: Path,
) -> None:
    runs = tmp_path / "runs"
    assert coordination.worker_gone_from_pid_record(runs, "missing") is None


def test_worker_gone_from_pid_record_is_unknown_when_process_check_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tmp_path / "runs"
    run_dir = runs / "run-c"
    run_dir.mkdir(parents=True)
    (run_dir / "process.json").write_text(
        json.dumps({"pid": os.getpid()}), encoding="utf-8"
    )

    monkeypatch.setattr(
        coordination, "_process_still_running", lambda _pid: None, raising=False
    )
    assert coordination.worker_gone_from_pid_record(runs, "run-c") is None

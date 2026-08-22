"""F01 — durable single-event append: the checks.

`events.append` is the single writer of the authoritative log. Until this unit it
buffered a line and closed the file: no serialisation across processes (three torn
concurrent appends reached the real trajectory on 22 Aug 2026 [measured: the pinned
incident in `test_no_new_event_may_bypass_append`]) and no fsync (the `loop.py`
ponytail names the gap). These tests pin the repair: one complete UTF-8 line per
acknowledged event, serialised by a kernel-backed per-log lock, fsynced before the
call returns, and an error — never a success acknowledgement — for every injected
durability failure.

The write path is unbuffered (`os.write`), so flush and write are one operation and
"flush failure" is exercised as write failure; fsync is the durability boundary.
"""

from __future__ import annotations

import multiprocessing
import os
import sys
import threading
import time
from datetime import datetime, timezone
from multiprocessing.connection import Connection
from pathlib import Path

import pytest

from consilient import events as events_mod
from consilient.events import SCHEMA_VERSION, EventError, append, canonical, read

_OPEN_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_APPEND | (
    os.O_BINARY if sys.platform == "win32" else 0
)


def ev(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "test.durability",
        "actor": "durability-test",
        "data": {},
    }
    base.update(over)
    return base


def _append_batch(log_path: str, writer: int, count: int, go) -> None:
    """Child worker: wait for the starting gun, then append as fast as possible."""
    go.wait()
    path = Path(log_path)
    for seq in range(count):
        append(
            path,
            ev(actor=f"writer-{writer}", data={"writer": writer, "seq": seq}),
        )


def _hold_lock(log_path: str, conn: Connection) -> None:
    """Child worker: take the per-log lock, report, then hold it until killed."""
    fd = os.open(log_path, _OPEN_FLAGS)
    events_mod._lock_file(fd)
    conn.send("locked")
    conn.close()
    time.sleep(60)


def test_two_hundred_concurrent_appends_produce_two_hundred_valid_distinct_lines(tmp_path):
    log = tmp_path / "concurrent.jsonl"
    ctx = multiprocessing.get_context("spawn")
    go = ctx.Event()
    writers, per_writer = 10, 20
    procs = [
        ctx.Process(target=_append_batch, args=(str(log), writer, per_writer, go))
        for writer in range(writers)
    ]
    for proc in procs:
        proc.start()
    go.set()
    for proc in procs:
        proc.join(timeout=120)
    for proc in procs:
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=10)
    assert [proc.exitcode for proc in procs] == [0] * writers, (
        "a writer process did not finish cleanly"
    )

    events, rejected = read(log)
    assert not rejected, f"torn or invalid lines were written: {rejected}"
    assert len(events) == writers * per_writer
    assert {(event.data["writer"], event.data["seq"]) for event in events} == {
        (writer, seq) for writer in range(writers) for seq in range(per_writer)
    }
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(set(lines)) == writers * per_writer


def test_a_killed_lock_holder_releases_the_per_log_lock(tmp_path):
    """The lock is kernel-backed, so process death releases it: no stale lock file
    can strand the log. Proven by killing the holder while it holds."""
    log = tmp_path / "killed.jsonl"
    ctx = multiprocessing.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_hold_lock, args=(str(log), child_conn))
    proc.start()
    try:
        assert parent_conn.poll(10), "the lock-holder child never reported"
        assert parent_conn.recv() == "locked"

        started = threading.Event()
        outcome: dict[str, object] = {}

        def try_append() -> None:
            started.set()
            try:
                append(log, ev(data={"marker": "after-kill"}))
                outcome["ok"] = True
            except Exception as exc:
                outcome["error"] = exc

        thread = threading.Thread(target=try_append)
        thread.start()
        assert started.wait(5)
        thread.join(timeout=2)
        assert thread.is_alive(), "append did not block behind the held per-log lock"
        proc.kill()
        proc.join(timeout=10)
        thread.join(timeout=10)
        assert not thread.is_alive(), "a killed holder left the per-log lock held"
        assert outcome.get("ok") is True, (
            f"append after the kill failed: {outcome.get('error')!r}"
        )
    finally:
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=10)

    events, rejected = read(log)
    assert not rejected
    assert [event.data["marker"] for event in events] == ["after-kill"]


def test_a_short_write_is_completed_in_full_before_acknowledgement(tmp_path, monkeypatch):
    """A short os.write is ordinary OS behaviour; the line is acknowledged only
    once every byte is written."""
    marker = b"short-write-marker"
    real_write = os.write
    target_fd = None
    calls = 0

    def halving_write(fd, data):
        nonlocal target_fd, calls
        payload = bytes(data)
        if target_fd is None and marker in payload:
            target_fd = fd
        if fd != target_fd:
            return real_write(fd, data)
        calls += 1
        return real_write(fd, payload[: max(1, len(payload) // 2)])

    monkeypatch.setattr("os.write", halving_write)
    log = tmp_path / "short.jsonl"
    record = ev(data={"marker": marker.decode()})
    append(log, record)

    assert calls >= 2, "the short write was not exercised"
    assert log.read_bytes() == (canonical(record) + "\n").encode("utf-8")
    events, rejected = read(log)
    assert not rejected
    assert [event.raw for event in events] == [record]


def test_a_write_that_makes_no_progress_is_an_error_and_acknowledges_nothing(
    tmp_path, monkeypatch
):
    marker = b"no-progress-marker"
    real_write = os.write
    target_fd = None

    def stuck_write(fd, data):
        nonlocal target_fd
        if target_fd is None and marker in bytes(data):
            target_fd = fd
        if fd == target_fd:
            return 0
        return real_write(fd, data)

    monkeypatch.setattr("os.write", stuck_write)
    log = tmp_path / "stuck.jsonl"
    with pytest.raises(EventError, match="not acknowledged"):
        append(log, ev(data={"marker": marker.decode()}))

    events, rejected = read(log)
    assert events == [] and rejected == []


def test_a_write_failure_mid_line_leaves_the_log_byte_for_byte_untouched(
    tmp_path, monkeypatch
):
    """Half a line lands, then the disk fails: the failed append rolls its bytes
    back, so no partial JSON line is ever acknowledged or left behind."""
    log = tmp_path / "midline.jsonl"
    append(log, ev(data={"marker": "before"}))
    before = log.read_bytes()
    marker = b"midline-marker"
    real_write = os.write
    target_fd = None
    attempts = 0

    def failing_write(fd, data):
        nonlocal target_fd, attempts
        payload = bytes(data)
        if target_fd is None and marker in payload:
            target_fd = fd
        if fd != target_fd:
            return real_write(fd, data)
        attempts += 1
        if attempts == 1:
            return real_write(fd, payload[: len(payload) // 2])
        raise OSError("injected write failure")

    monkeypatch.setattr("os.write", failing_write)
    with pytest.raises(EventError, match="not acknowledged"):
        append(log, ev(data={"marker": marker.decode()}))

    assert attempts >= 2, "the mid-line failure was not exercised"
    assert log.read_bytes() == before, "a failed append left bytes behind"
    events, rejected = read(log)
    assert not rejected
    assert [event.data["marker"] for event in events] == ["before"]


def test_an_fsync_failure_is_an_error_and_acknowledges_nothing(tmp_path, monkeypatch):
    def failing_fsync(fd):
        raise OSError("injected fsync failure")

    monkeypatch.setattr("os.fsync", failing_fsync)
    log = tmp_path / "fsync.jsonl"
    with pytest.raises(EventError, match="not acknowledged"):
        append(log, ev())

    events, rejected = read(log)
    assert events == [] and rejected == []


def test_first_file_creation_fsyncs_the_directory_where_the_platform_exposes_it(
    tmp_path, monkeypatch
):
    """A new log's directory entry is made durable on creation (POSIX); on Windows
    the standard library exposes no directory fsync, so the guarantee there covers
    the file-content fsync and nothing broader."""
    calls: list[Path] = []
    real = events_mod._fsync_directory

    def spy(directory: Path) -> None:
        calls.append(Path(directory))
        real(directory)

    monkeypatch.setattr(events_mod, "_fsync_directory", spy)
    log = tmp_path / "fresh" / "log.jsonl"
    append(log, ev(data={"marker": "first"}))
    assert calls == [log.parent], "the first append to a file must fsync its directory"

    append(log, ev(data={"marker": "second"}))
    assert calls == [log.parent], "an append to an existing file re-fsyncs no directory"

    events, rejected = read(log)
    assert not rejected
    assert [event.data["marker"] for event in events] == ["first", "second"]


def test_a_directory_fsync_failure_is_an_error_and_never_a_partial_line(
    tmp_path, monkeypatch
):
    def fail(directory: Path) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(events_mod, "_fsync_directory", fail)
    log = tmp_path / "dirfail.jsonl"
    with pytest.raises(EventError, match="not acknowledged"):
        append(log, ev())

    _events, rejected = read(log)
    assert not rejected, "no partial JSON line may be left behind"


def test_an_acknowledged_append_is_immediately_rereadable(tmp_path):
    log = tmp_path / "now.jsonl"
    record = ev(data={"marker": "reread"})
    assert append(log, record) == record
    events, rejected = read(log)
    assert not rejected
    assert [event.raw for event in events] == [record]

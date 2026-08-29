"""F01 — the directory entry is part of the acknowledgement, not a step after it.

A separate durability boundary from the file-content fsync, and separated here because
it has its own platform caveat and its own failure mode. Fsyncing a file's contents does
not make its directory entry durable, so a newly created log can vanish whole on a crash
while every byte inside it was safely written. These pin the rule and where it stops:
the first append to a new file fsyncs its parent directory on POSIX, while on Windows
the standard library exposes no directory fsync, so the guarantee there covers the file-
content fsync and nothing broader.

The rest are the cases a naive "do it once, on creation" implementation gets wrong. A
later writer must retry the directory sync when the creator's attempt failed, rather
than acknowledging a file whose creation was never made durable — and the F02
transaction path carries the same first-file rule, so it is checked the same way. The
sync happens while the per-log lock is held, proved by a follower that must not return
while the creator's directory sync is still pending. A directory fsync failure is an
error, and leaves no partial line behind."""

import threading
from pathlib import Path
import pytest
from consilient import events as events_mod
from consilient import events_durability
from consilient.events import EventError, append, read
from event_durability_helpers import (
    ev,
)


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

    monkeypatch.setattr(events_durability, "_fsync_directory", spy)
    log = tmp_path / "fresh" / "log.jsonl"
    append(log, ev(data={"marker": "first"}))
    assert calls == [log.parent], "the first append to a file must fsync its directory"

    append(log, ev(data={"marker": "second"}))
    assert calls == [log.parent, log.parent], (
        "every acknowledgement must establish directory durability while holding the log lock"
    )

    events, rejected = read(log)
    assert not rejected
    assert [event.data["marker"] for event in events] == ["first", "second"]


def test_later_append_retries_directory_durability_after_the_initial_attempt_fails(
    tmp_path, monkeypatch
):
    """A later writer must not acknowledge a file whose creation was not durable."""
    calls = 0

    def fail_once(directory: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected initial directory fsync failure")

    monkeypatch.setattr(events_durability, "_fsync_directory", fail_once)
    log = tmp_path / "retry-directory.jsonl"

    with pytest.raises(EventError, match="directory entry"):
        append(log, ev(data={"marker": "unacknowledged"}))

    append(log, ev(data={"marker": "acknowledged"}))
    assert calls == 2, "a later append must retry directory durability before returning"


def test_later_transaction_retries_directory_durability_after_the_initial_attempt_fails(
    tmp_path, monkeypatch
):
    """The F02 transaction path has the same first-file acknowledgement rule."""
    calls = 0

    def fail_once(directory: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected initial directory fsync failure")

    monkeypatch.setattr(events_durability, "_fsync_directory", fail_once)
    candidate = ev(
        event="test.durability.transaction", data={"marker": "unacknowledged"}
    )

    with pytest.raises(EventError, match="directory entry"):
        events_mod.append_transaction(tmp_path, [candidate], lambda _p, _r, _c: None)

    events_mod.append_transaction(
        tmp_path,
        [ev(event="test.durability.transaction", data={"marker": "acknowledged"})],
        lambda _p, _r, _c: None,
    )
    assert calls == 2, (
        "a later transaction must retry directory durability before returning"
    )


def test_follower_cannot_acknowledge_while_creator_directory_sync_is_pending(
    tmp_path, monkeypatch
):
    """Directory durability stays inside the per-log lock for every acknowledgement."""
    directory_sync_started = threading.Event()
    release_directory_sync = threading.Event()
    follower_attempting_append = threading.Event()
    follower_returned = threading.Event()
    calls_lock = threading.Lock()
    calls = 0
    outcomes: dict[str, object] = {}

    def block_creator(directory: Path) -> None:
        nonlocal calls
        with calls_lock:
            calls += 1
            first = calls == 1
        if first:
            directory_sync_started.set()
            assert release_directory_sync.wait(10), (
                "test did not release creator directory sync"
            )

    def write(name: str, marker: str) -> None:
        try:
            if name == "follower":
                follower_attempting_append.set()
            append(tmp_path / "contended-directory.jsonl", ev(data={"marker": marker}))
            outcomes[name] = "ok"
        except Exception as exc:
            outcomes[name] = exc
        finally:
            if name == "follower":
                follower_returned.set()

    monkeypatch.setattr(events_durability, "_fsync_directory", block_creator)
    creator = threading.Thread(target=write, args=("creator", "first"))
    follower = threading.Thread(target=write, args=("follower", "second"))
    creator.start()
    try:
        assert directory_sync_started.wait(5), "creator never reached directory sync"
        follower.start()
        assert follower_attempting_append.wait(5), "follower never attempted append"
        assert not follower_returned.wait(0.5), (
            "follower acknowledged while the creator's directory sync was pending"
        )
    finally:
        release_directory_sync.set()
        creator.join(timeout=10)
        follower.join(timeout=10)

    assert not creator.is_alive() and not follower.is_alive()
    assert outcomes == {"creator": "ok", "follower": "ok"}


def test_a_directory_fsync_failure_is_an_error_and_never_a_partial_line(
    tmp_path, monkeypatch
):
    def fail(directory: Path) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(events_durability, "_fsync_directory", fail)
    log = tmp_path / "dirfail.jsonl"
    with pytest.raises(EventError, match="not acknowledged"):
        append(log, ev())

    _events, rejected = read(log)
    assert not rejected, "no partial JSON line may be left behind"

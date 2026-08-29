"""M01 — capture installs the exact bytes, or it reports no success at all.

The successful path and the interrupted path are one claim, so they are tested together:
``capture_file`` returns a frozen reference only when the object on disk is byte-
identical to the source and a linked ``record.captured`` event has been appended and
read back. The reference's field order, its immutability, the content-addressed locator,
the relative source path and the absence of the resolved absolute path anywhere in the
canonical event are all pinned on the way through. Content addressing is proved here too
— the same bytes captured twice reuse one object but append two events with distinct
record ids and distinct event digests, and a payload of all 256 byte values is stored
verbatim.

The rest of the file attacks the same claim from the other side. A failure is injected
at each of the four stages in turn — object install, object reread, event append, event
reread — and none of them may return success or leave an event behind. A child process
is then killed at the exact boundary between installing the object and appending the
event: the object survives, no event is logged, and a retry afterwards produces exactly
one event, which is what makes a killed capture retryable rather than half-done. Finally
a freshly spawned process, sharing nothing but the workspace on disk, must resolve the
accepted record to the same bytes, the same event digest and the same locator."""

import dataclasses
import hashlib
import importlib
import multiprocessing
import time
from pathlib import Path
from typing import Any
import pytest
from consilient import events
from records_helpers import (
    LOG,
    OBJECTS,
    _capture,
    _events,
    _records,
)


def _pause_before_event_append(
    workspace_text: str, source_text: str, ready: Any
) -> None:
    records = importlib.import_module("consilient.records")

    def pause(*_args: object, **_kwargs: object) -> None:
        ready.set()
        time.sleep(60)

    records.events.append = pause
    records.capture_file(
        Path(source_text),
        workspace_root=Path(workspace_text),
        object_root=Path(workspace_text) / OBJECTS,
        log_dir=Path(workspace_text) / LOG,
        actor="killed-capture",
        media_type="application/octet-stream",
        consent_purpose="task-evidence",
        retention_class="project",
    )


def _fresh_process_read(
    workspace_text: str,
    object_locator: str,
    digest: str,
    event_id: str,
    event_digest: str,
    result: Any,
) -> None:
    workspace = Path(workspace_text)
    payload = (workspace / Path(object_locator)).read_bytes()
    accepted, rejected = events.read_all(workspace / LOG)
    matches = [event for event in accepted if event.raw.get("event_id") == event_id]
    result.put(
        (
            hashlib.sha256(payload).hexdigest(),
            len(rejected),
            len(matches),
            events.event_sha256(matches[0].raw) if len(matches) == 1 else "",
            matches[0].data["object_locator"] if len(matches) == 1 else "",
        )
    )


def test_capture_file_installs_exact_bytes_and_appends_the_complete_contract(
    tmp_path: Path,
) -> None:
    payload = b"\x00\xffimmutable\r\n"
    ref, source = _capture(tmp_path, payload)

    assert [field.name for field in dataclasses.fields(ref)] == [
        "record_id",
        "digest",
        "byte_count",
        "media_type",
        "object_locator",
        "event_id",
        "event_sha256",
    ]
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.byte_count = 0

    digest = hashlib.sha256(payload).hexdigest()
    locator = f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    assert ref.digest == digest
    assert ref.byte_count == len(payload)
    assert ref.media_type == "application/octet-stream"
    assert ref.object_locator == locator
    assert (tmp_path / Path(locator)).read_bytes() == payload

    captured = _events(tmp_path)
    assert len(captured) == 1
    event = captured[0]
    assert event.kind == "record.captured"
    assert event.actor == "records-test"
    assert event.raw["event_id"] == ref.event_id
    assert events.event_sha256(event.raw) == ref.event_sha256
    assert event.data == {
        "record_id": ref.record_id,
        "digest": digest,
        "byte_count": len(payload),
        "media_type": "application/octet-stream",
        "object_locator": locator,
        "source": source.relative_to(tmp_path).as_posix(),
        "consent_purpose": "task-evidence",
        "retention_class": "project",
        "valid_time": {"from": event.raw["ts"], "to": None},
        "supersedes": [],
        "invalidates": [],
    }
    assert not Path(event.data["source"]).is_absolute()
    assert str(source.resolve()) not in events.canonical(event.raw)


def test_duplicate_content_reuses_one_object_but_appends_distinct_source_events(
    tmp_path: Path,
) -> None:
    payload = b"same bytes"
    first, _ = _capture(tmp_path, payload, relative="one.bin")
    second, _ = _capture(tmp_path, payload, relative="two.bin")

    assert first.digest == second.digest
    assert first.object_locator == second.object_locator
    assert first.record_id != second.record_id
    assert first.event_id != second.event_id
    assert first.event_sha256 != second.event_sha256
    object_files = [
        path for path in (tmp_path / OBJECTS / "sha256").rglob("*") if path.is_file()
    ]
    assert object_files == [tmp_path / Path(first.object_locator)]
    assert [event.data["source"] for event in _events(tmp_path)] == [
        "one.bin",
        "two.bin",
    ]


def test_non_utf8_payload_is_captured_verbatim(tmp_path: Path) -> None:
    payload = bytes(range(256))
    ref, _ = _capture(tmp_path, payload)
    assert (tmp_path / Path(ref.object_locator)).read_bytes() == payload
    assert ref.digest == hashlib.sha256(payload).hexdigest()


def test_install_object_reread_event_append_and_event_reread_failures_never_return_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = _records()

    def install_failure(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected install failure")

    monkeypatch.setattr(records, "_install_object", install_failure)
    with pytest.raises(events.EventError, match="install"):
        _capture(tmp_path / "install")
    assert _events(tmp_path / "install") == []
    monkeypatch.undo()

    records = _records()

    def object_reread_failure(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected object reread failure")

    monkeypatch.setattr(records, "_verify_object", object_reread_failure)
    with pytest.raises(events.EventError, match="reread|verify"):
        _capture(tmp_path / "object-reread")
    assert _events(tmp_path / "object-reread") == []
    monkeypatch.undo()

    records = _records()

    def append_failure(*_args: object, **_kwargs: object) -> None:
        raise events.EventError("injected event append failure")

    monkeypatch.setattr(records.events, "append", append_failure)
    with pytest.raises(events.EventError, match="append"):
        _capture(tmp_path / "event-append")
    assert _events(tmp_path / "event-append") == []
    monkeypatch.undo()

    records = _records()
    monkeypatch.setattr(records.events, "read_all", lambda _path: ([], []))
    with pytest.raises(events.EventError, match="reread|linked"):
        _capture(tmp_path / "event-reread")
    monkeypatch.undo()
    assert len(_events(tmp_path / "event-reread")) == 1


def test_killed_capture_between_object_install_and_event_append_is_retryable(
    tmp_path: Path,
) -> None:
    payload = b"kill boundary"
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    ctx = multiprocessing.get_context("spawn")
    ready = ctx.Event()
    proc = ctx.Process(
        target=_pause_before_event_append,
        args=(str(tmp_path), str(source), ready),
    )
    proc.start()
    try:
        assert ready.wait(20), "child did not reach the object-installed boundary"
        proc.kill()
        proc.join(timeout=10)
        assert not proc.is_alive()
        assert proc.exitcode != 0
    finally:
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=10)

    digest = hashlib.sha256(payload).hexdigest()
    object_path = tmp_path / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    assert object_path.read_bytes() == payload
    assert _events(tmp_path) == []

    ref = _records().capture_file(
        source,
        workspace_root=tmp_path,
        object_root=tmp_path / OBJECTS,
        log_dir=tmp_path / LOG,
        actor="retry-after-kill",
        media_type="application/octet-stream",
        consent_purpose="task-evidence",
        retention_class="project",
    )
    assert ref.digest == digest
    assert len(_events(tmp_path)) == 1


def test_accepted_record_resolves_to_exact_bytes_after_a_fresh_process_starts(
    tmp_path: Path,
) -> None:
    payload = b"fresh process bytes\x00\xff"
    ref, _ = _capture(tmp_path, payload)
    ctx = multiprocessing.get_context("spawn")
    result = ctx.Queue()
    proc = ctx.Process(
        target=_fresh_process_read,
        args=(
            str(tmp_path),
            ref.object_locator,
            ref.digest,
            ref.event_id,
            ref.event_sha256,
            result,
        ),
    )
    proc.start()
    proc.join(timeout=30)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=10)
    assert proc.exitcode == 0
    assert result.get(timeout=5) == (
        ref.digest,
        0,
        1,
        ref.event_sha256,
        ref.object_locator,
    )

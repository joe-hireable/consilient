"""M01 - acknowledged immutable object capture."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import multiprocessing
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from consilient import events


ROOT = Path(__file__).resolve().parents[1]
OBJECTS = Path(".harness/objects")
LOG = Path(".harness/log")


def _records() -> Any:
    try:
        return importlib.import_module("consilient.records")
    except ModuleNotFoundError as exc:
        if exc.name != "consilient.records":
            raise
        pytest.fail("M01 requires the missing consilient.records module")


def _capture(
    workspace: Path,
    payload: bytes = b"record bytes\n",
    *,
    relative: str = "inputs/record.bin",
    media_type: str = "application/octet-stream",
) -> tuple[Any, Path]:
    source = workspace / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(payload)
    ref = _records().capture_file(
        source,
        workspace_root=workspace,
        object_root=workspace / OBJECTS,
        log_dir=workspace / LOG,
        actor="records-test",
        media_type=media_type,
        consent_purpose="task-evidence",
        retention_class="project",
    )
    return ref, source


def _events(workspace: Path) -> list[events.Event]:
    accepted, rejected = events.read_all(workspace / LOG)
    assert rejected == []
    return accepted


def _record_event(
    *,
    event_id: str = "550e8400-e29b-41d4-a716-446655440000",
    record_id: str = "650e8400-e29b-41d4-a716-446655440000",
    digest: str = "a" * 64,
    **data_overrides: object,
) -> dict[str, object]:
    ts = datetime.now(timezone.utc).isoformat()
    data: dict[str, object] = {
        "record_id": record_id,
        "digest": digest,
        "byte_count": 1,
        "media_type": "application/octet-stream",
        "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
        "source": "inputs/source.bin",
        "consent_purpose": "task-evidence",
        "retention_class": "project",
        # The frozen API accepts no validity interval. Capture time is therefore
        # the measured lower bound and an unknown upper bound stays explicit.
        "valid_time": {"from": ts, "to": None},
        "supersedes": [],
        "invalidates": [],
    }
    data.update(data_overrides)
    return {
        "v": events.SCHEMA_VERSION,
        "ts": ts,
        "event": "record.captured",
        "actor": "records-test",
        "event_id": event_id,
        "data": data,
    }


def _event_reference(event: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(event["event_id"]),
        "event_kind": str(event["event"]),
        "event_sha256": events.event_sha256(event),
    }


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
    object_files = [path for path in (tmp_path / OBJECTS / "sha256").rglob("*") if path.is_file()]
    assert object_files == [tmp_path / Path(first.object_locator)]
    assert [event.data["source"] for event in _events(tmp_path)] == ["one.bin", "two.bin"]


def test_non_utf8_payload_is_captured_verbatim(tmp_path: Path) -> None:
    payload = bytes(range(256))
    ref, _ = _capture(tmp_path, payload)
    assert (tmp_path / Path(ref.object_locator)).read_bytes() == payload
    assert ref.digest == hashlib.sha256(payload).hexdigest()


def test_source_outside_the_resolved_workspace_is_refused_without_an_event(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")

    with pytest.raises(events.EventError, match="outside the authorised workspace"):
        _records().capture_file(
            outside,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert not (workspace / OBJECTS).exists()


def test_symlink_escape_is_refused_without_exposing_or_capturing_the_target(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside-secret-free-fixture")
    link = workspace / "escape.bin"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable in this Windows test environment: {exc}")

    with pytest.raises(events.EventError, match="outside the authorised workspace"):
        _records().capture_file(
            link,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert not (workspace / OBJECTS).exists()


@pytest.mark.parametrize(
    ("relative", "payload"),
    (
        (".env", b"SAFE_NAME=credential-value"),
        ("private.pem", ("-----BEGIN " + "PRIVATE" + " KEY-----").encode()),
        ("token.txt", ("sk" + "-or-v1-" + "a" * 40).encode()),
    ),
)
def test_private_environment_key_and_token_material_are_refused_before_install(
    tmp_path: Path, relative: str, payload: bytes
) -> None:
    workspace = tmp_path / relative.replace(".", "-")
    workspace.mkdir()
    source = workspace / relative
    source.write_bytes(payload)

    with pytest.raises(events.EventError, match="credential|private environment"):
        _records().capture_file(
            source,
            workspace_root=workspace,
            object_root=workspace / OBJECTS,
            log_dir=workspace / LOG,
            actor="records-test",
            media_type="application/octet-stream",
            consent_purpose="task-evidence",
            retention_class="project",
        )

    assert _events(workspace) == []
    assert not list((workspace / OBJECTS).rglob("*")) if (workspace / OBJECTS).exists() else True


def test_documented_environment_template_is_not_mistaken_for_a_private_env_file(
    tmp_path: Path,
) -> None:
    ref, _ = _capture(tmp_path, b"EXAMPLE_NAME=replace-me\n", relative=".env.example")
    assert (tmp_path / Path(ref.object_locator)).is_file()


@pytest.mark.parametrize(
    "locator",
    (
        "/absolute/object",
        "C:/absolute/object",
        ".harness/objects/../escape",
        ".harness/objects/sha256/aa/not-the-digest",
    ),
)
def test_record_contract_refuses_noncanonical_or_escaping_object_locators(
    tmp_path: Path, locator: str
) -> None:
    candidate = _record_event(object_locator=locator)
    with pytest.raises(events.EventError, match="object_locator"):
        events.append(tmp_path / "trajectory.jsonl", candidate)
    assert events.read(tmp_path / "trajectory.jsonl") == ([], [])


def test_record_contract_refuses_an_absolute_source_locator(tmp_path: Path) -> None:
    with pytest.raises(events.EventError, match="source"):
        events.append(
            tmp_path / "trajectory.jsonl",
            _record_event(source="C:/private/source.bin"),
        )
    assert events.read(tmp_path / "trajectory.jsonl") == ([], [])


def test_object_shard_symlink_cannot_redirect_capture_outside_the_private_store(
    tmp_path: Path,
) -> None:
    payload = b"object shard escape"
    digest = hashlib.sha256(payload).hexdigest()
    outside = tmp_path / "outside"
    outside.mkdir()
    shard = tmp_path / OBJECTS / "sha256" / digest[:2]
    shard.parent.mkdir(parents=True)
    try:
        shard.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable in this Windows test environment: {exc}")

    with pytest.raises(events.EventError, match="object|store|root|escape"):
        _capture(tmp_path, payload)

    assert _events(tmp_path) == []
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("missing", ("consent_purpose", "retention_class"))
def test_record_contract_refuses_missing_consent_or_retention_metadata(
    missing: str,
) -> None:
    candidate = _record_event()
    del candidate["data"][missing]
    with pytest.raises(events.EventError, match=missing):
        events.validate(candidate)


def test_record_contract_refuses_field_and_event_kind_aliases() -> None:
    candidate = _record_event()
    candidate["data"]["consent"] = candidate["data"].pop("consent_purpose")
    with pytest.raises(events.EventError, match="consent|field"):
        events.validate(candidate)

    for alias in ("record.capture", "record_captured", "records.captured"):
        candidate = _record_event()
        candidate["event"] = alias
        with pytest.raises(events.EventError, match="alias|record.captured"):
            events.validate(candidate)


def test_record_relations_resolve_only_exact_earlier_record_references(
    tmp_path: Path,
) -> None:
    log = tmp_path / "trajectory.jsonl"
    first = _record_event()
    events.append(log, first)
    reference = _event_reference(first)

    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        supersedes=[reference],
    )
    events.append(log, second)
    assert [event.raw for event in events.read(log)[0]] == [first, second]

    self_referencing = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440002",
        record_id="650e8400-e29b-41d4-a716-446655440002",
        invalidates=[
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440002",
                "event_kind": "record.captured",
                "event_sha256": "0" * 64,
            }
        ],
    )
    with pytest.raises(events.EventError, match="itself|self"):
        events.append(log, self_referencing)

    future = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440003",
        record_id="650e8400-e29b-41d4-a716-446655440003",
    )
    before_future = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440004",
        record_id="650e8400-e29b-41d4-a716-446655440004",
        supersedes=[_event_reference(future)],
    )
    with pytest.raises(events.EventError, match="earlier|future|missing"):
        events.append(log, before_future)

    alias_reference = {
        "id": reference["event_id"],
        "kind": reference["event_kind"],
        "sha256": reference["event_sha256"],
    }
    with pytest.raises(events.EventError, match="reference"):
        events.validate(
            _record_event(
                event_id="550e8400-e29b-41d4-a716-446655440005",
                record_id="650e8400-e29b-41d4-a716-446655440005",
                supersedes=[alias_reference],
            )
        )

    assert [event.raw for event in events.read(log)[0]] == [first, second]


def test_existing_mismatching_object_is_a_refused_collision_not_an_overwrite(
    tmp_path: Path,
) -> None:
    payload = b"expected bytes"
    digest = hashlib.sha256(payload).hexdigest()
    object_path = tmp_path / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(b"collision bytes")

    with pytest.raises(events.EventError, match="collision|mismatch"):
        _capture(tmp_path, payload)

    assert object_path.read_bytes() == b"collision bytes"
    assert _events(tmp_path) == []


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


def test_object_store_is_explicitly_untrackable() -> None:
    probe = ".harness/objects/sha256/aa/" + "b" * 62
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", probe],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert ignored.returncode == 0, ".harness/objects/ is not explicitly ignored"

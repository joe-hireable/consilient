"""Private immutable payload capture linked to the authoritative trajectory."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import events


_SECRET_RE = re.compile(
    "|".join(
        (
            "sk" + r"-or-v1-[A-Za-z0-9_-]{20,}",
            "sk" + r"-ant-[A-Za-z0-9_-]{20,}",
            "sk" + r"-(proj-)?[A-Za-z0-9]{32,}",
            "AI" + r"za[0-9A-Za-z_-]{35}",
            "gh" + r"[pousr]_[A-Za-z0-9]{20,}",
            "xox" + r"[baprs]-[0-9A-Za-z-]{10,}",
            "pypi-" + r"AgEIcH[A-Za-z0-9_-]{20,}",
            "AK" + r"IA[0-9A-Z]{16}",
            "xa" + r"i-[A-Za-z0-9]{20,}",
            r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----",
            "ey"
            + r"J[A-Za-z0-9_-]{10,}\.ey"
            + r"J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        )
    )
)


@dataclass(frozen=True)
class RecordRef:
    record_id: str
    digest: str
    byte_count: int
    media_type: str
    object_locator: str
    event_id: str
    event_sha256: str


def _private_env(path: Path) -> bool:
    name = path.name.casefold()
    if name == ".env":
        return True
    return name.startswith(".env.") and not name.endswith(
        (".example", ".sample", ".template")
    )


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise events.EventError(f"{field} must be a canonical non-empty string")
    return value


def _workspace_path(value: str | os.PathLike[str], workspace: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else workspace / path


def _resolve_workspace(value: str | os.PathLike[str]) -> Path:
    try:
        workspace = Path(value).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise events.EventError("the authorised workspace cannot be resolved") from exc
    if not workspace.is_dir():
        raise events.EventError("the authorised workspace must be a directory")
    return workspace


def _resolve_source(
    source: str | os.PathLike[str], workspace: Path
) -> tuple[Path, str]:
    try:
        resolved = _workspace_path(source, workspace).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise events.EventError("the capture source cannot be resolved") from exc
    try:
        relative = resolved.relative_to(workspace)
    except ValueError as exc:
        raise events.EventError(
            "the capture source is outside the authorised workspace"
        ) from exc
    if not resolved.is_file():
        raise events.EventError("the capture source must be a regular file")
    return resolved, relative.as_posix()


def _resolve_private_roots(
    workspace: Path,
    object_root: str | os.PathLike[str],
    log_dir: str | os.PathLike[str],
) -> tuple[Path, Path]:
    expected_objects = (workspace / ".harness" / "objects").resolve()
    expected_log = (workspace / ".harness" / "log").resolve()
    try:
        objects = _workspace_path(object_root, workspace).resolve()
        log = _workspace_path(log_dir, workspace).resolve()
    except (OSError, RuntimeError) as exc:
        raise events.EventError("the private capture roots cannot be resolved") from exc
    if (
        objects != expected_objects
        or log != expected_log
        or not objects.is_relative_to(workspace)
        or not log.is_relative_to(workspace)
    ):
        raise events.EventError(
            "object_root and log_dir must be the authorised .harness/objects and .harness/log roots"
        )
    return objects, log


def _payload(source: Path) -> bytes:
    if _private_env(source):
        raise events.EventError("private environment files cannot be captured")
    try:
        # ponytail: one in-memory snapshot; stream from one descriptor when measured
        # capture sizes make peak memory material.
        payload = source.read_bytes()
    except OSError as exc:
        raise events.EventError("the capture source could not be read") from exc
    if _SECRET_RE.search(payload.decode("utf-8", errors="replace")):
        raise events.EventError("credential-shaped content cannot be captured")
    return payload


def _verify_object(path: Path, digest: str, byte_count: int) -> None:
    payload = path.read_bytes()
    if len(payload) != byte_count or hashlib.sha256(payload).hexdigest() != digest:
        raise events.EventError("object byte-count or digest mismatch")


def _install_object(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".capture-{os.urandom(16).hex()}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        events._fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def capture_file(
    source: str | os.PathLike[str],
    *,
    workspace_root: str | os.PathLike[str],
    object_root: str | os.PathLike[str],
    log_dir: str | os.PathLike[str],
    actor: str,
    media_type: str,
    consent_purpose: str,
    retention_class: str,
) -> RecordRef:
    """Capture one authorised file and acknowledge only its durable event link."""
    workspace = _resolve_workspace(workspace_root)
    resolved_source, source_locator = _resolve_source(source, workspace)
    objects, log = _resolve_private_roots(workspace, object_root, log_dir)
    actor = _canonical_text(actor, "actor")
    media_type = _canonical_text(media_type, "media_type")
    consent_purpose = _canonical_text(consent_purpose, "consent_purpose")
    retention_class = _canonical_text(retention_class, "retention_class")

    payload = _payload(resolved_source)
    digest = hashlib.sha256(payload).hexdigest()
    byte_count = len(payload)
    object_locator = f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    object_path = objects / "sha256" / digest[:2] / digest[2:]
    try:
        resolved_object_path = object_path.resolve()
    except (OSError, RuntimeError) as exc:
        raise events.EventError("the canonical object path cannot be resolved") from exc
    if resolved_object_path != object_path:
        raise events.EventError(
            "the canonical object path escaped the private object store"
        )

    timestamp = datetime.now(timezone.utc).isoformat()
    record_id = events.new_event_id()
    candidate: events.EventPayload = {
        "v": events.SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": actor,
        "event_id": events.new_event_id(),
        "data": {
            "record_id": record_id,
            "digest": digest,
            "byte_count": byte_count,
            "media_type": media_type,
            "object_locator": object_locator,
            "source": source_locator,
            "consent_purpose": consent_purpose,
            "retention_class": retention_class,
            "valid_time": {"from": timestamp, "to": None},
            "supersedes": [],
            "invalidates": [],
        },
    }
    events.validate(candidate)

    if object_path.exists():
        try:
            _verify_object(object_path, digest, byte_count)
        except (OSError, events.EventError) as exc:
            raise events.EventError(
                "content-address collision or existing-object mismatch; capture not acknowledged"
            ) from exc
    else:
        try:
            _install_object(object_path, payload)
        except (OSError, events.EventError) as exc:
            raise events.EventError(
                "object install failed; capture not acknowledged"
            ) from exc
        try:
            _verify_object(object_path, digest, byte_count)
        except (OSError, events.EventError) as exc:
            raise events.EventError(
                "object reread verification failed; capture not acknowledged"
            ) from exc

    log_path = log / f"{timestamp[:10]}.jsonl"
    try:
        appended = events.append(log_path, candidate)
    except OSError as exc:
        raise events.EventError(
            "event append failed; capture not acknowledged"
        ) from exc
    expected_event_digest = events.event_sha256(appended)
    event_id = appended["event_id"]
    try:
        accepted, _rejected = events.read_all(log)
    except (OSError, UnicodeDecodeError) as exc:
        raise events.EventError(
            "the appended event could not be reread; capture not acknowledged"
        ) from exc
    matches = [event for event in accepted if event.raw.get("event_id") == event_id]
    if (
        len(matches) != 1
        or events.event_sha256(matches[0].raw) != expected_event_digest
        or matches[0].data.get("object_locator") != object_locator
    ):
        raise events.EventError(
            "the appended event was not reread as one exact linked record; capture not acknowledged"
        )
    if not isinstance(
        event_id, str
    ):  # validate() makes this unreachable; keeps the return typed.
        raise events.EventError("the appended event has no stable identity")

    return RecordRef(
        record_id=record_id,
        digest=digest,
        byte_count=byte_count,
        media_type=media_type,
        object_locator=object_locator,
        event_id=event_id,
        event_sha256=expected_event_digest,
    )

"""Getting a line onto disk in such a way that it stays there.

`Event` is the row a reader gets back. Everything else here is the machinery that puts
one down: the kernel-backed per-log lock, which a dying process releases whether or not
it meant to; the write that either lays down every byte or raises, because a short write
acknowledged early is a truncated record nobody knows about; the file and directory
synchronisation that happens before any writer tells its caller the line is safe; and
the digest of a log's first n lines, which is how the append-only claim is checked
rather than asserted. A directory-level lock serialises every budget-state and
reservation write in one trajectory.

The per-event field checks that depend on nothing above them sit alongside. A dispatch
records whether it was supervised (ADR-0039). A capability gap names what was asked,
what was tried and how it failed, and declares its closure — a gap that no retry can
close must escalate rather than evaporate (V0-41). The visibility dial is recorded so
that β can be stratified by the display conditions it was measured under (R31 /
ADR-0035). No response-level rating surface exists, and the prohibition is enforced in
the schema rather than left to whoever writes the next caller (R22).

Money is read as a decimal and timestamps are parsed rather than trusted, on the same
principle: a value that arrives as text stays text until something has checked it."""

from __future__ import annotations
import hashlib
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast
from .events_vocabulary import (
    DISPATCH_STATUSES,
    RESPONSE_RATING_FIELDS,
    jittered_sleep,
)

from .events_kinds import (
    BUDGET_LOCK,
    CAPABILITY_GAP_KIND,
    CAPABILITY_MANIFEST_KINDS,
    EventError,
    EventPayload,
    GAP_CLOSURES,
    GAP_FAILURES,
    INTENT_REASONS,
    INTENT_REASON_PREFIXES,
    RECORD_CAPTURED_KIND,
    TS,
    USAGE_KIND,
    VISIBILITY_CHANGE_KIND,
    VISIBILITY_LEVELS,
    _BUDGET_LOCK_HELD,
    _TRANSACTION_LOCK_BYTE,
)


__all__ = [
    "BUDGET_LOCK",
    "CAPABILITY_GAP_KIND",
    "CAPABILITY_MANIFEST_KINDS",
    "DISPATCH_STATUSES",
    "Event",
    "EventError",
    "EventPayload",
    "GAP_CLOSURES",
    "GAP_FAILURES",
    "INTENT_REASONS",
    "INTENT_REASON_PREFIXES",
    "RECORD_CAPTURED_KIND",
    "RESPONSE_RATING_FIELDS",
    "TS",
    "USAGE_KIND",
    "VISIBILITY_CHANGE_KIND",
    "VISIBILITY_LEVELS",
    "_BUDGET_LOCK_HELD",
    "_TRANSACTION_LOCK_BYTE",
    "jittered_sleep",
    "parse_capability_identity",
    "prefix_digest",
]


@dataclass(frozen=True)
class Event:
    raw: EventPayload
    path: str | None = None
    line: int | None = None
    # Carried so that an accepted event which LATER turns out to break the effect receipt chain
    # can be quarantined as a Rejection without re-reading and re-hashing its line. Rejection
    # already records a content digest; before unit A01 an Event did not, so `read_all` could not
    # demote one without losing the fingerprint that identifies which physical line was refused.
    content_digest: str = ""

    @property
    def kind(self) -> str:
        return cast(str, self.raw["event"])

    @property
    def actor(self) -> str:
        return cast(str, self.raw["actor"])

    @property
    def data(self) -> EventPayload:
        return cast(EventPayload, self.raw["data"])


def parse_capability_identity(value: object) -> tuple[str, str]:
    if not isinstance(value, str) or value.count(":") != 1:
        raise EventError("identity must be a kind:name string")
    kind, name = value.split(":", 1)
    if kind not in CAPABILITY_MANIFEST_KINDS:
        raise EventError(
            f"identity kind must be one of {sorted(CAPABILITY_MANIFEST_KINDS)!r}"
        )
    if not name or any(
        character.isspace() or not character.isprintable() for character in name
    ):
        raise EventError(
            "identity name must be a non-empty identifier without whitespace"
        )
    return kind, name


def _record_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or TS.fullmatch(value) is None:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {field} must be RFC3339 with an explicit offset"
        )
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {field} cannot be normalised to UTC"
        ) from exc


def _decimal_field(
    kind: str, data: EventPayload, field: str, *, positive: bool
) -> None:
    value = data.get(field)
    if not isinstance(value, str):
        qualifier = "positive" if positive else "non-negative"
        raise EventError(
            f"{kind} must carry {field} as a finite {qualifier} Decimal string"
        )
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise EventError(f"{kind} carries invalid {field} {value!r}") from exc
    if not amount.is_finite():
        qualifier = "positive" if positive else "non-negative"
        raise EventError(
            f"{kind} must carry {field} as a finite {qualifier} Decimal string"
        )
    valid_sign = amount > 0 if positive else amount >= 0
    if not valid_sign:
        qualifier = "positive" if positive else "non-negative"
        raise EventError(
            f"{kind} must carry {field} as a finite {qualifier} Decimal string"
        )


def _check_reset(value: object) -> None:
    """A window that has lost its reset time is not a window."""
    if value is None:
        return
    if not isinstance(value, str) or not TS.match(value):
        raise EventError(
            f"{USAGE_KIND} resets_at must be RFC3339 with an explicit offset, or absent"
        )
    try:
        datetime.fromisoformat(value).astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(f"{USAGE_KIND} resets_at cannot be normalised to UTC") from exc


def _check_derivation_roots(value: object) -> None:
    if value == "unknown":
        return
    if (
        not isinstance(value, list)
        or not value
        or any(
            not isinstance(item, str) or not item.strip() or item != item.strip()
            for item in value
        )
    ):
        raise EventError(
            "acquisition.derivation_roots must be 'unknown' or a non-empty list "
            "of canonical strings"
        )


def _check_capability_gap_contract(event: EventPayload) -> None:
    """V0-41: a capability gap is a first-class record, not a conversation that vanished."""
    if event["event"] != CAPABILITY_GAP_KIND:
        return
    data = event["data"]
    for field in ("asked", "attempted", "detail", "repair", "run_id", "source"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{CAPABILITY_GAP_KIND} must carry a non-empty string {field}"
            )
    failure = data.get("failure")
    if failure not in GAP_FAILURES:
        raise EventError(
            f"{CAPABILITY_GAP_KIND} failure must be one of {sorted(GAP_FAILURES)}, "
            f"got {failure!r}"
        )
    closure = data.get("closure")
    if closure not in GAP_CLOSURES:
        raise EventError(
            f"{CAPABILITY_GAP_KIND} closure must be one of {sorted(GAP_CLOSURES)}, "
            f"got {closure!r}"
        )
    if failure in {"silent", "not_implemented"} and closure == "retry":
        raise EventError(
            f"{CAPABILITY_GAP_KIND} with failure {failure!r} must escalate, not retry"
        )


def _check_intent_reason(value: object, where: str) -> None:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise EventError(f"{where} reason must be a non-empty unpadded string")
    if value in INTENT_REASONS:
        return
    for prefix in INTENT_REASON_PREFIXES:
        if value.startswith(prefix) and value[len(prefix) :].strip():
            return
    raise EventError(
        f"{where} reason must be one of {sorted(INTENT_REASONS)} or "
        f"{list(INTENT_REASON_PREFIXES)} with a named subject, got {value!r}"
    )


def _check_dispatch_contract(event: EventPayload) -> None:
    """ADR-0039: every dispatch records whether it was supervised."""
    if event["event"].startswith("dispatch.") and not isinstance(
        event["data"].get("supervised"), bool
    ):
        raise EventError(
            "dispatch events must record supervised as a boolean (ADR-0039)"
        )
    status = event["data"].get("status")
    if (
        event["event"] in ("dispatch.outcome", "dispatch.refused")
        and status is not None
        and (not isinstance(status, str) or status not in DISPATCH_STATUSES)
    ):
        raise EventError(f"unknown dispatch status {status!r}")


def _check_response_rating_ban(event: EventPayload) -> None:
    """R22: no response-level rating surface, enforced in the schema.

    Compliance cannot rest on nobody having written the code yet. Any event carrying
    an approval-style field is rejected before it reaches the log, so a rating widget
    added tomorrow fails here rather than accreting.
    """
    data = event["data"]
    hits = sorted(RESPONSE_RATING_FIELDS & set(data))
    if hits:
        raise EventError(
            f"{event['event']} carries approval-style field(s) {hits}; the unit of "
            "feedback is the task, and response-level rating is not built "
            "(feedback-signals.md rules 1–2)"
        )


def _check_visibility_contract(event: EventPayload) -> None:
    """R31 / ADR-0035: the dial is recorded so β stratifies by display conditions."""
    data = event["data"]
    if event["event"] == VISIBILITY_CHANGE_KIND:
        level = data.get("level")
        if level not in VISIBILITY_LEVELS:
            raise EventError(
                f"{VISIBILITY_CHANGE_KIND} must carry level as one of "
                f"{VISIBILITY_LEVELS}, got {level!r}"
            )
        overrides = data.get("overrides")
        if overrides is not None:
            if not isinstance(overrides, dict):
                raise EventError(
                    f"{VISIBILITY_CHANGE_KIND}.overrides must be an object"
                )
            for kind_name, override_level in overrides.items():
                if not isinstance(kind_name, str) or not kind_name.strip():
                    raise EventError("override keys must be non-empty event kinds")
                if override_level not in VISIBILITY_LEVELS:
                    raise EventError(
                        f"override for {kind_name!r} must be one of "
                        f"{VISIBILITY_LEVELS}, got {override_level!r}"
                    )
    effective = data.get("effective_visibility")
    if effective is not None and effective not in VISIBILITY_LEVELS:
        raise EventError(
            f"effective_visibility must be one of {VISIBILITY_LEVELS}, "
            f"got {effective!r}"
        )


@contextmanager
def _budget_transaction(directory: Path) -> Iterator[None]:
    """Serialise every budget-state and reservation write in one directory."""
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / BUDGET_LOCK
    lock.touch(exist_ok=False)
    token = _BUDGET_LOCK_HELD.set(lock.resolve())
    try:
        yield
    finally:
        _BUDGET_LOCK_HELD.reset(token)
        lock.unlink(missing_ok=True)


# The durability path (F01). Until 22 Aug 2026 the append below was a buffered
# `path.open("a")` write: no serialisation across processes, so concurrent writers
# tore lines on the real trajectory, and no fsync, so an acknowledged event could
# still be lost with the process. [measured: the pinned torn-append incident in
# `tests/test_v0_invariants.py::test_no_new_event_may_bypass_append`; the `loop.py`
# ponytail] The contract now: `append` returns only after one complete UTF-8 line is
# written under a kernel-backed per-log lock and fsynced, and every failure raises —
# a partial line is never acknowledged, and is rolled back so it is never left
# behind either. The lock is the log's own descriptor: `fcntl.flock` on POSIX,
# `msvcrt.locking` on Windows, both released by the kernel when a holder dies, so a
# killed writer cannot strand the log the way a lock file does.

if sys.platform == "win32":
    # O_BINARY: without it the Windows CRT translates "\n" to "\r\n" on write.
    _OPEN_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_BINARY
    # The transaction reads the prefix through the descriptor that holds the
    # lock, so it needs read access; see _read_under_lock.
    _TRANSACTION_OPEN_FLAGS = os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_BINARY
else:
    _OPEN_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    _TRANSACTION_OPEN_FLAGS = os.O_RDWR | os.O_CREAT | os.O_APPEND


def _lock_file(fd: int) -> None:
    """Take the kernel-backed per-log lock; block until held. Death releases it."""
    if sys.platform == "win32":
        import msvcrt

        while True:
            try:
                os.lseek(fd, _TRANSACTION_LOCK_BYTE, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                # Jittered, for the same measured reason `_retry_sleep` is: a fixed 5 ms
                # sleep put every waiter on the same instants, and this repository runs
                # dozens of concurrent writers. They were re-colliding at every step --
                # 26 dispatchers were measured spinning here, ~40 CPU-seconds each,
                # making no progress. The one jitter rule, applied at the second retry
                # site that needed it and never got it.
                jittered_sleep(0.01)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX)


def _unlock_file(fd: int) -> None:
    """Best-effort: the descriptor is closed immediately after, which releases the
    lock regardless, so an unlock failure changes nothing."""
    if sys.platform == "win32":
        import msvcrt

        try:
            os.lseek(fd, _TRANSACTION_LOCK_BYTE, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


def _write_all(fd: int, data: bytes) -> None:
    """Write every byte or raise; a short write is retried, never acknowledged early."""
    view = memoryview(data)
    while len(view) > 0:
        try:
            written = os.write(fd, view)
        except OSError as exc:
            raise EventError(
                f"could not write the event line; the append is not acknowledged: {exc}"
            ) from exc
        if written <= 0:
            raise EventError("a write made no progress; the append is not acknowledged")
        view = view[written:]


def _fsync_directory(directory: Path) -> None:
    """Make a newly created log's directory entry durable where the platform exposes it.

    POSIX exposes directory fsync. The Windows standard library does not, so there
    this is a no-op and the first-file guarantee covers the file-content fsync and
    nothing broader.
    """
    if sys.platform == "win32":
        return
    else:
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _fsync_parent_before_acknowledgement(path: Path) -> None:
    """Synchronise the log's directory before any writer acknowledges its line.

    A file's first directory entry may have been created by another process whose
    directory fsync failed. Every writer therefore retries the directory sync
    while holding the per-log lock; sampling ``path.exists()`` cannot prove that
    a prior process made the entry durable.
    """
    try:
        _fsync_directory(path.parent)
    except OSError as exc:
        raise EventError(
            f"the line is written and fsynced but the directory entry of "
            f"{path.name!r} could not be fsynced; the append is not "
            f"acknowledged: {exc}"
        ) from exc


def _planning_references(record: EventPayload) -> Iterator[tuple[str, object]]:
    for index, reference in enumerate(cast(list[object], record["evidence_refs"])):
        yield f"evidence_refs[{index}]", reference
    protocol = cast(EventPayload, record["protocol"])
    for field in (
        "instructions_ref",
        "bar_ref",
        "search_ref",
        "killing_check_ref",
    ):
        if field in protocol:
            yield f"protocol.{field}", protocol[field]
    if "supersedes" in record:
        yield "supersedes", record["supersedes"]


def prefix_digest(path: Path, count: int) -> str:
    """Digest of the first `count` lines — the append-only check.

    Appending must never change an earlier position. A test asserts the digest of the
    committed prefix survives an append and that an in-place edit is detected.
    """
    lines = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh):
            if number >= count:
                break
            lines.append(line.rstrip("\n"))
    if len(lines) < count:
        raise EventError(
            f"{path} has {len(lines)} lines, cannot digest a prefix of {count}"
        )
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

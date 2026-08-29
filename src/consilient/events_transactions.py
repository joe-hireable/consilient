"""Reading a whole trajectory, and appending to it without a race.

`read_all` returns every event across every daily file, ordered by filename and then by
position, with every refused line alongside it. The compare-and-append transaction (F02)
is the writing half: a candidate is checked against the accepted prefix while the F01
lock is held, the registered transition validators run against prefix and candidates
together, and only then is anything written. Without that ordering, any rule that
depends on what came before could be raced past by a second writer between the check and
the write — which is the whole class of bug the generic door used to leave open.

A per-file lock cannot by itself serialise two writers working on different dates, so an
effect-chain replay is assembled across daily files and serialised ahead of the daily
transaction it feeds. The reads that inform a transaction go through the same descriptor
that holds the lock, so what is validated is what is on disk at that instant rather than
a copy taken earlier.

`_check_clock` guards the other end. An appended event is stamped from a clock, not from
its author's belief about the time, and a stamp beyond the tolerated skew is refused
rather than accepted and silently ordered wrong — a log ordered by a lying timestamp
replays into a history that never happened."""

from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from . import effects
from .events_vocabulary import (
    _rollback,
    _trajectory_fingerprint,
)

from .events_digests import (
    _reject_duplicate_event_ids,
    event_sha256,
)

from .events_durability import (
    _TRANSACTION_OPEN_FLAGS,
    Event,
    _fsync_parent_before_acknowledgement,
    _lock_file,
    _unlock_file,
    _write_all,
)

from .events_evidence import (
    _appending,
    _retry_sleep,
)

from .events_fields import (
    _fsync_file,
    canonical,
)

from .events_kinds import (
    BUDGET_STATE_KIND,
    ESCALATION_ATTEMPTED_KIND,
    EventError,
    EventPayload,
    MAX_CLOCK_SKEW_S,
    SPEND_RESERVED_KIND,
    _READ_ALL_CACHE_MAX,
    _READ_RETRIES,
    _TRANSACTION_LOCK_BYTE,
)

from .events_records import (
    TransitionValidator,
    _READ_ALL_CACHE,
    _validate_delivery_claim_ordering,
    _validate_effect_receipt_chain,
)

from .events_references import (
    Rejection,
    _escalation_disposition,
)

from .events_validation import (
    _TRANSITION_VALIDATORS,
    _classify_lines,
    read,
    validate,
)


__all__ = [
    "BUDGET_STATE_KIND",
    "ESCALATION_ATTEMPTED_KIND",
    "Event",
    "EventError",
    "EventPayload",
    "MAX_CLOCK_SKEW_S",
    "Rejection",
    "SPEND_RESERVED_KIND",
    "TransitionValidator",
    "_READ_ALL_CACHE",
    "_READ_ALL_CACHE_MAX",
    "_READ_RETRIES",
    "_TRANSACTION_LOCK_BYTE",
    "_TRANSITION_VALIDATORS",
    "_appending",
    "_classify_lines",
    "_escalation_disposition",
    "_fsync_file",
    "_fsync_parent_before_acknowledgement",
    "_lock_file",
    "_reject_duplicate_event_ids",
    "_retry_sleep",
    "_rollback",
    "_trajectory_fingerprint",
    "_unlock_file",
    "_validate_delivery_claim_ordering",
    "_validate_effect_receipt_chain",
    "_write_all",
    "canonical",
    "event_sha256",
    "read",
    "read_all",
    "validate",
]


def _check_clock(event: EventPayload) -> None:
    """An appended event must be stamped from a clock, not from an author's belief.

    Added 20 Aug 2026 after the orchestrator wrote six consecutive trajectory events with
    invented timestamps, drifting to 2h15m ahead of the wall clock, while documenting
    instrument-integrity defects in other people's work. Nothing caught it: `validate`
    checked the *format* of `ts` and its offset, which were impeccable, and never asked
    whether the value was true.

    A format check on a timestamp is not a check on a timestamp.

    This runs at append only, never in `validate`, because reading a historical log must
    not depend on when it is read — which is the same reason `ts` requires an explicit
    offset in the first place.
    """
    stamped = datetime.fromisoformat(event["ts"])
    skew = abs((datetime.now(timezone.utc) - stamped).total_seconds())
    if skew > MAX_CLOCK_SKEW_S:
        raise EventError(
            f"event ts {event['ts']} is {skew / 60:.0f} minutes from the current clock, "
            f"beyond the {MAX_CLOCK_SKEW_S // 60}-minute tolerance. Stamp events from the "
            "clock rather than writing the time you believe it to be. To record something "
            "that happened earlier, put the occurrence time in `data` and let `ts` record "
            "when it was written."
        )


def _write_validated(path: Path, event: EventPayload) -> EventPayload:
    if event["event"] in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
        expected = f"{event['ts'][:10]}.jsonl"
        if path.name != expected:
            raise EventError(
                f"{event['event']} must be written to its timestamped daily file "
                f"{expected!r}, not {path.name!r}"
            )
    _check_clock(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (canonical(event) + "\n").encode("utf-8")
    fd = os.open(path, _TRANSACTION_OPEN_FLAGS)
    try:
        _lock_file(fd)
        try:
            prefix, _rejected = _read_under_lock(path, fd)
            _reject_duplicate_event_ids(tuple(prefix), (event,))
            with _appending(fd):
                offset = os.lseek(fd, 0, os.SEEK_END)
                try:
                    _write_all(fd, line)
                    # fsync inside the lock: an acknowledged prefix is always durable,
                    # so a failed fsync rolls back before any later line can be
                    # acknowledged over a non-durable earlier one.
                    _fsync_file(fd)
                    _fsync_parent_before_acknowledgement(path)
                except EventError:
                    _rollback(fd, offset)
                    raise
        finally:
            _unlock_file(fd)
    finally:
        os.close(fd)
    return event


def _effect_replay_history(
    path: Path, accepted: tuple[Event, ...], rejected: tuple[Rejection, ...]
) -> tuple[tuple[Event, ...], tuple[Rejection, ...]]:
    """Assemble effect-chain replay state across daily files.

    The caller holds the kernel-backed effect-chain lock, then the current
    file's F01 lock. This keeps a cross-date replay and its append serialised;
    it is still only a record contract and does not expose an effect handle.
    """
    events: list[Event] = []
    rejections: list[Rejection] = []
    for other in sorted(path.parent.glob("*.jsonl")):
        if other == path:
            events.extend(accepted)
            rejections.extend(rejected)
        else:
            prior_events, prior_rejections = read(other)
            events.extend(prior_events)
            rejections.extend(prior_rejections)
    return tuple(events), tuple(rejections)


def _transaction(
    path: Path,
    candidates: list[EventPayload],
    validator: TransitionValidator | None,
) -> list[EventPayload]:
    """Serialise every effect-chain replay before its daily-file transaction.

    A daily F01 lock alone cannot prevent two writers on different dates from
    accepting competing heads. This is a kernel-backed directory lock, not a
    touch-lock: process death releases it. It introduces no effect store.
    """
    kinds = {candidate["event"] for candidate in candidates}
    effect_kinds = kinds & {
        effects.EFFECT_INTENT,
        effects.EFFECT_RECEIPT,
    }
    escalation_kinds = kinds & {ESCALATION_ATTEMPTED_KIND}
    if not effect_kinds and not escalation_kinds:
        return _transaction_one_log(path, candidates, validator)
    if effect_kinds and escalation_kinds:
        raise EventError("one transaction cannot mix effect and escalation records")
    if path.suffix != ".jsonl":
        raise EventError("governed records require a JSONL authority path")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_name = ".effects.chain.lock" if effect_kinds else ".escalation.chain.lock"
    lock_fd = os.open(path.parent / lock_name, _TRANSACTION_OPEN_FLAGS)
    try:
        _lock_file(lock_fd)
        written = candidates
        if escalation_kinds:
            events, _rejected = read_all(path.parent)
            history = list(events)
            written = []
            for candidate in candidates:
                if candidate["event"] != ESCALATION_ATTEMPTED_KIND:
                    written.append(candidate)
                    continue
                disposition, refusal_reason = _escalation_disposition(
                    history, candidate
                )
                data = dict(cast(EventPayload, candidate["data"]))
                data["disposition"] = disposition
                data["refusal_reason"] = refusal_reason
                resolved = {**candidate, "data": data}
                validate(resolved)
                history.append(Event(resolved))
                written.append(resolved)
        return _transaction_one_log(path, written, validator)
    finally:
        _unlock_file(lock_fd)
        os.close(lock_fd)


def _transaction_one_log(
    path: Path,
    candidates: list[EventPayload],
    validator: TransitionValidator | None,
) -> list[EventPayload]:
    """Compare-and-append under the per-log lock.

    Candidates arrive validated. The accepted prefix and the rejections are read
    while holding the F01 lock and handed to the caller's validator and to every
    registered rule governing a candidate's kind; only then is the batch written
    contiguously and fsynced. Any failure raises and rolls every byte of the
    batch back: a partial multi-event success is never returned.
    """
    for candidate in candidates:
        _check_clock(candidate)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, _TRANSACTION_OPEN_FLAGS)
    try:
        _lock_file(fd)
        try:
            try:
                accepted, rejected = _read_under_lock(path, fd)
            except (OSError, UnicodeDecodeError) as exc:
                raise EventError(
                    f"could not read the current prefix of {path.name!r}; the "
                    "transaction is not acknowledged rather than run against an "
                    f"assumed empty history: {exc}"
                ) from exc
            prefix = tuple(accepted)
            rejections = tuple(rejected)
            batch = tuple(candidates)
            _reject_duplicate_event_ids(prefix, batch)
            if validator is not None:
                validator(prefix, rejections, batch)
            effect_prefix: tuple[Event, ...] | None = None
            effect_rejections: tuple[Rejection, ...] | None = None
            for candidate in batch:
                registered = _TRANSITION_VALIDATORS.get(candidate["event"])
                if registered is not None:
                    if registered is _validate_effect_receipt_chain:
                        if effect_prefix is None or effect_rejections is None:
                            effect_prefix, effect_rejections = _effect_replay_history(
                                path, prefix, rejections
                            )
                        registered(effect_prefix, effect_rejections, batch)
                    else:
                        registered(prefix, rejections, batch)
            _validate_delivery_claim_ordering(prefix, rejections, batch)
            with _appending(fd):
                offset = os.lseek(fd, 0, os.SEEK_END)
                try:
                    for candidate in batch:
                        _write_all(fd, (canonical(candidate) + "\n").encode("utf-8"))
                    # fsync inside the lock, exactly as the single-append path: an
                    # acknowledged batch is always durably ordered behind every
                    # earlier acknowledged line, and a failed fsync rolls back
                    # before any later line can be acknowledged over it.
                    _fsync_file(fd)
                    _fsync_parent_before_acknowledgement(path)
                except EventError:
                    _rollback(fd, offset)
                    raise
        finally:
            _unlock_file(fd)
    finally:
        os.close(fd)
    return list(candidates)


def _read_under_lock(path: Path, fd: int) -> tuple[list[Event], list[Rejection]]:
    """Read the log through the descriptor that holds the per-log lock.

    POSIX flock is advisory, but the Windows byte-range lock refuses a second
    handle reading the locked region at all, so under the lock the prefix cannot
    be read through a fresh open; the locking descriptor itself may read it. The
    bytes are decoded with the same universal-newline rule text mode applies, so
    a line classifies identically through either path.

    Holding the transaction lock no longer implies nothing else can lock bytes this read
    touches: `_appending` takes byte 0 for the duration of a write, and a writer that has not
    adopted `_TRANSACTION_LOCK_BYTE` holds byte 0 for its whole transaction. Either can deny
    this read, so it retries on the same jittered budget `read()` uses and fails closed the
    same way. The retry restarts from offset zero rather than resuming: a denial part-way
    through would otherwise splice two reads of a file that may have grown between them, and
    a prefix assembled from two moments is not a prefix.
    """
    payload = b""
    last: OSError | None = None
    for attempt in range(_READ_RETRIES):
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
        except PermissionError as exc:
            last = exc
            _retry_sleep(attempt)
            continue
        payload = b"".join(chunks)
        break
    else:
        raise EventError(
            f"{path} could not be read after {_READ_RETRIES} attempts while holding the "
            f"transaction lock: observed access denial ({last}); another writer holds the "
            "append region. The transaction is not acknowledged rather than run against an "
            "incomplete prefix."
        )
    if payload and not payload.endswith(b"\n"):
        raise EventError(
            f"refusing append to {path.name!r}: torn line at byte offset {payload.rfind(b'\n') + 1}"
        )
    text = payload.decode("utf-8")
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    return _classify_lines(str(path), normalised.splitlines(keepends=True))


def read_all(directory: Path) -> tuple[list[Event], list[Rejection]]:
    """Every event across every daily file, ordered by filename then position.

    MEASURED 28 August 2026. This parses the WHOLE trajectory, and `coordination.py` calls
    it at SIX sites on the claims path -- once per dispatch, with a dozen dispatches live.
    One call: 1.8 seconds, 18,764 events, 224 MB retained, over 91 MB of JSONL in ten day
    files. Six of those per dispatch is roughly eleven seconds of pure parsing and up to
    six retained copies, and the driver was recording MemoryError crashes on this path.

    So the repeats are memoised on a fingerprint of the files themselves. This changes NO
    semantics: a hit returns exactly what a fresh parse would, because any append changes a
    size and misses the cache.

    WHAT THIS DELIBERATELY DOES NOT DO is narrow the horizon. `open_claim` derives the
    fencing epoch from this function, and an epoch computed over less history can only be
    LOWER -- which is the one direction that is unsafe, because a token that is too low
    lets an expired holder write behind a live one. Reading the same events faster is safe;
    reading fewer of them is not, and that distinction is the whole design of this cache.

    The returned lists are fresh shallow copies. Callers append to them -- the claims
    validator does exactly that -- and a shared list would let one caller corrupt the next
    reader's history. The Event objects themselves are shared, which is why the copy is
    cheap: 18,764 pointers rather than 18,764 re-parsed dicts.
    """
    key = str(directory)
    fingerprint = _trajectory_fingerprint(directory)
    if fingerprint is not None:
        hit = _READ_ALL_CACHE.get(key)
        if hit is not None and hit[0] == fingerprint:
            return list(hit[1]), list(hit[2])

    events: list[Event] = []
    rejected: list[Rejection] = []
    for path in sorted(directory.glob("*.jsonl")):
        if not path.is_file():
            continue
        file_events, file_rejected = read(path)
        # Replay each line in file order rather than appending two lists, because the effect
        # receipt chain is ORDER-DEPENDENT: whether a receipt is valid depends on the intents
        # accepted before it. Extending events and rejections separately validated every line
        # against a prefix that already contained lines occurring after it, so a chain broken
        # part-way through the file was accepted whole. A line that breaks the chain is demoted
        # to a Rejection here and does not enter the prefix the next line is judged against.
        replay_items: list[Event | Rejection] = [*file_events, *file_rejected]
        for item in sorted(replay_items, key=lambda item: item.line or 0):
            if isinstance(item, Rejection):
                rejected.append(item)
                continue
            if item.kind in (effects.EFFECT_INTENT, effects.EFFECT_RECEIPT):
                try:
                    _validate_effect_receipt_chain(
                        tuple(events), tuple(rejected), (item.raw,)
                    )
                except EventError as exc:
                    rejected.append(
                        Rejection(
                            item.path or "",
                            item.line or 0,
                            str(exc),
                            item.content_digest,
                            item.kind,
                        )
                    )
                    continue
            events.append(item)
    seen_ids: dict[str, Event] = {}
    for event in events:
        event_id = event.raw.get("event_id")
        if not isinstance(event_id, str):
            continue
        first = seen_ids.get(event_id)
        if first is None:
            seen_ids[event_id] = event
            continue
        rejected.append(
            Rejection(
                event.path or "",
                event.line or 0,
                "duplicate event_id "
                f"{event_id!r}; first appeared at {first.path}:{first.line}",
                event_sha256(event.raw),
                event.kind,
            )
        )
    if fingerprint is not None:
        if len(_READ_ALL_CACHE) >= _READ_ALL_CACHE_MAX:
            _READ_ALL_CACHE.clear()
        _READ_ALL_CACHE[key] = (fingerprint, list(events), list(rejected))
    return events, rejected

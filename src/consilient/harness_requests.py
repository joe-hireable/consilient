"""Per-request timing and token usage — the request.record kind and everything that
validates it.

This is a different measurement from an outcome. An outcome says what the dispatch
produced; a request record says what it cost and how long it took to start producing
anything, which is why t_first_chunk and t_first_nonempty_chunk are separate fields: a
harness that streams whitespace has not started answering. REQUEST_RECORD_FIELDS names
the seven, and `validate_request_record` refuses a payload before append rather than
after, so a malformed record never reaches the log.

RequestTiming travels with this module rather than staying with the other dataclasses,
because its subject is here and nothing else constructs it. Usage extraction is parsing
someone else's stdout and is deliberately forgiving in one direction only — an absent
field is unknown, never zero, since a zero token count is a claim and an absent one is
not.

request.record is appended only from here, through events.append (V0-41). DISPATCH_ACTOR
comes from harness_registry so that this module need not reach into harness_recording."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from .events import (
    SCHEMA_VERSION,
    EventPayload,
    append,
)
from .harness_registry import (
    DISPATCH_ACTOR,
    Harness,
)


__all__ = [
    "DISPATCH_ACTOR",
    "Harness",
    "REQUEST_RECORD_FIELDS",
    "REQUEST_RECORD_KIND",
    "RequestTiming",
    "build_request_timing",
    "extract_usage_from_output",
    "record_request",
    "validate_request_record",
]

REQUEST_RECORD_KIND = "request.record"

REQUEST_RECORD_FIELDS: tuple[str, ...] = (
    "t_send",
    "t_first_chunk",
    "t_first_nonempty_chunk",
    "n_chunks",
    "output_tokens",
    "cache_read_input_tokens",
    "in_flight_at_dispatch",
)


@dataclass(frozen=True)
class RequestTiming:
    """Per-request timing row for BU5 / X05. Timestamps are RFC3339 UTC.

    Token fields are None when the provider did not report them. Zero is a
    measured zero, never a stand-in for unknown (V0-30).
    """

    t_send: str
    t_first_chunk: str
    t_first_nonempty_chunk: str
    n_chunks: int
    output_tokens: int | None
    cache_read_input_tokens: int | None
    in_flight_at_dispatch: int

    def as_data(self) -> dict[str, int | str | None]:
        return {
            "t_send": self.t_send,
            "t_first_chunk": self.t_first_chunk,
            "t_first_nonempty_chunk": self.t_first_nonempty_chunk,
            "n_chunks": self.n_chunks,
            "output_tokens": self.output_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "in_flight_at_dispatch": self.in_flight_at_dispatch,
        }


def _as_non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _as_optional_non_negative_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _as_non_negative_int(value, field)


_USAGE_FIELDS = frozenset({"output_tokens", "cache_read_input_tokens"})
_COUNT_FIELDS = frozenset({"n_chunks", "in_flight_at_dispatch"})


def _as_timestamp(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be RFC3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must carry an explicit offset")
    return value


def validate_request_record(data: object) -> dict[str, int | str | None]:
    """Validate a request.record payload before append."""
    if not isinstance(data, dict):
        raise ValueError("request record must be an object")
    run_id = data.get("run_id")
    harness = data.get("harness")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(harness, str) or not harness.strip():
        raise ValueError("harness must be a non-empty string")
    row: dict[str, int | str | None] = {
        "run_id": run_id.strip(),
        "harness": harness.strip(),
    }
    for field in REQUEST_RECORD_FIELDS:
        if field not in data:
            raise ValueError(f"{field} is required")
        value = data[field]
        if field in _COUNT_FIELDS:
            row[field] = _as_non_negative_int(value, field)
        elif field in _USAGE_FIELDS:
            row[field] = _as_optional_non_negative_int(value, field)
        else:
            row[field] = _as_timestamp(value, field)
    send_ts = datetime.fromisoformat(str(row["t_send"])).astimezone(timezone.utc)
    first_ts = datetime.fromisoformat(str(row["t_first_chunk"])).astimezone(
        timezone.utc
    )
    nonempty_ts = datetime.fromisoformat(str(row["t_first_nonempty_chunk"])).astimezone(
        timezone.utc
    )
    if not (send_ts <= first_ts <= nonempty_ts):
        raise ValueError(
            "timing timestamps must satisfy t_send <= t_first_chunk <= t_first_nonempty_chunk"
        )
    return row


def _usage_int(payload: object, *keys: str) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None


_CACHE_READ_KEYS = (
    "cache_read_input_tokens",
    "cacheReadInputTokens",
    "cacheReadTokens",
    "cache_read_tokens",
)


def _usage_from_payload(payload: object) -> tuple[int | None, int | None]:
    if not isinstance(payload, dict):
        return None, None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None
    output_tokens = _usage_int(usage, "output_tokens", "outputTokens")
    cache = usage.get("cache")
    if isinstance(cache, dict):
        cache_read = _usage_int(cache, "read", "read_tokens", "readTokens")
    else:
        cache_read = _usage_int(usage, *_CACHE_READ_KEYS)
    return output_tokens, cache_read


def extract_usage_from_output(stdout: str, harness_id: str) -> dict[str, int | None]:
    """Token fields from a harness transcript. Unknown stays None, never zero.

    harness_id is kept so callers stay keyed to the arm; extraction is from the
    transcript shape, not from the label. Cursor ``text`` format has no envelope.
    """
    del harness_id
    output_tokens: int | None = None
    cache_read: int | None = None
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        found_out, found_cache = _usage_from_payload(payload)
        if found_out is not None:
            output_tokens = found_out
        if found_cache is not None:
            cache_read = found_cache
        if output_tokens is not None or cache_read is not None:
            break
    if output_tokens is None and cache_read is None:
        try:
            payload = json.loads(stdout.strip())
        except json.JSONDecodeError:
            payload = None
        found_out, found_cache = _usage_from_payload(payload)
        if found_out is not None:
            output_tokens = found_out
        if found_cache is not None:
            cache_read = found_cache
    return {
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
    }


def build_request_timing(
    *,
    t_send: str,
    t_first_chunk: str,
    t_first_nonempty_chunk: str,
    n_chunks: int,
    output_tokens: int | None,
    cache_read_input_tokens: int | None,
    in_flight_at_dispatch: int,
) -> RequestTiming:
    return RequestTiming(
        t_send=t_send,
        t_first_chunk=t_first_chunk,
        t_first_nonempty_chunk=t_first_nonempty_chunk,
        n_chunks=n_chunks,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
        in_flight_at_dispatch=in_flight_at_dispatch,
    )


def record_request(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    harness_id: str,
    timing: RequestTiming,
) -> EventPayload:
    """Append one request.record through the single writer (V0-41)."""
    data = validate_request_record(
        {
            "run_id": run_id,
            "harness": harness_id,
            **timing.as_data(),
        }
    )
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": REQUEST_RECORD_KIND,
            "actor": DISPATCH_ACTOR,
            "data": data,
        },
    )

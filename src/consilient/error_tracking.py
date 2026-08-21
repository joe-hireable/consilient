"""Native error identity and prevention judgement; collection stays replaceable.

Canonical records deliberately reject raw messages and stack traces. Those are the fields
most likely to contain credentials or machine paths, and neither is needed to identify a
known error. Collection uses the stable OTLP/HTTP JSON boundary; Sentry-compatible envelope
export is optional and keeps its DSN outside the record.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, cast

ErrorRecord = dict[str, Any]

SCHEMA_VERSION = 1
_BASE_FIELDS = frozenset(
    {"v", "observed_at", "identity", "component", "error_type", "error_code"}
)
_JUDGEMENT_FIELDS = frozenset({"prevention_check", "no_check_yet"})
_TOKEN = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_ERROR_TYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{0,127}$")
_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00$")


class ErrorRecordError(ValueError):
    """A record or export boundary is invalid."""


def stable_identity(component: str, error_type: str, error_code: str) -> str:
    """Return the identity of one error class, excluding occurrence-specific data."""
    for name, value, pattern in (
        ("component", component, _TOKEN),
        ("error_type", error_type, _ERROR_TYPE),
        ("error_code", error_code, _TOKEN),
    ):
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            raise ErrorRecordError(f"{name} must be a bounded identifier")
    material = json.dumps(
        [component, error_type, error_code], ensure_ascii=True, separators=(",", ":")
    )
    return f"sha256:{hashlib.sha256(material.encode('ascii')).hexdigest()}"


def _utc_timestamp(value: str) -> str:
    if _TIMESTAMP.fullmatch(value) is None:
        raise ErrorRecordError("observed_at must be a canonical UTC RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ErrorRecordError("observed_at is not a valid calendar timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ErrorRecordError("observed_at must use UTC")
    return parsed.isoformat()


def _check_reference(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ErrorRecordError("prevention_check must name a concrete check")
    path, separator, node = value.partition("::")
    parts = PurePosixPath(path).parts
    if (
        "\\" in value
        or path.startswith("/")
        or re.match(r"^[A-Za-z]:", path)
        or ".." in parts
        or not path.endswith(".py")
        or not path.startswith(("tests/", ".github/scripts/"))
        or (
            separator
            and (not node or re.fullmatch(r"[A-Za-z0-9_.\[\]-]+", node) is None)
        )
    ):
        raise ErrorRecordError(
            "prevention_check must be a repository-relative test or checker reference"
        )
    return value


def validate(record: object) -> ErrorRecord:
    """Validate the closed canonical schema and return the same record."""
    if not isinstance(record, dict):
        raise ErrorRecordError("error record must be an object")
    keys = set(record)
    unexpected = keys - _BASE_FIELDS - _JUDGEMENT_FIELDS
    if unexpected:
        raise ErrorRecordError(f"unexpected field(s): {', '.join(sorted(unexpected))}")
    missing = _BASE_FIELDS - keys
    if missing:
        raise ErrorRecordError(
            f"missing required field(s): {', '.join(sorted(missing))}"
        )
    if type(record["v"]) is not int or record["v"] != SCHEMA_VERSION:
        raise ErrorRecordError(f"v must be {SCHEMA_VERSION}")

    component = record["component"]
    error_type = record["error_type"]
    error_code = record["error_code"]
    if not isinstance(component, str):
        raise ErrorRecordError("component must be a bounded identifier")
    if not isinstance(error_type, str):
        raise ErrorRecordError("error_type must be a bounded identifier")
    if not isinstance(error_code, str):
        raise ErrorRecordError("error_code must be a bounded identifier")
    expected = stable_identity(component, error_type, error_code)
    if (
        not isinstance(record["identity"], str)
        or _IDENTITY.fullmatch(record["identity"]) is None
    ):
        raise ErrorRecordError("identity must be a lowercase SHA-256 identity")
    if record["identity"] != expected:
        raise ErrorRecordError("identity does not match the canonical error fields")
    if not isinstance(record["observed_at"], str):
        raise ErrorRecordError("observed_at must be a canonical UTC RFC3339 timestamp")
    _utc_timestamp(record["observed_at"])

    has_check = "prevention_check" in record
    has_no_check = record.get("no_check_yet") is True
    if has_check == has_no_check or ("no_check_yet" in record and not has_no_check):
        raise ErrorRecordError(
            "record must carry exactly one of prevention_check or no_check_yet=true"
        )
    if has_check:
        _check_reference(record["prevention_check"])
    return cast(ErrorRecord, record)


def build_record(
    *,
    component: str,
    error_type: str,
    error_code: str,
    observed_at: str | None = None,
    prevention_check: str | None = None,
    no_check_yet: bool = False,
) -> ErrorRecord:
    """Build one occurrence without accepting raw exception content."""
    timestamp = _utc_timestamp(observed_at or datetime.now(timezone.utc).isoformat())
    record: ErrorRecord = {
        "v": SCHEMA_VERSION,
        "observed_at": timestamp,
        "identity": stable_identity(component, error_type, error_code),
        "component": component,
        "error_type": error_type,
        "error_code": error_code,
    }
    if prevention_check is not None:
        record["prevention_check"] = prevention_check
    if no_check_yet:
        record["no_check_yet"] = True
    return validate(record)


def canonical(record: object) -> str:
    return json.dumps(
        validate(record), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )


def append_record(path: Path, record: object) -> ErrorRecord:
    checked = validate(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(checked) + "\n")
    return checked


def read_records(path: Path) -> list[ErrorRecord]:
    records: list[ErrorRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(validate(json.loads(line)))
            except (json.JSONDecodeError, ErrorRecordError) as exc:
                raise ErrorRecordError(f"{path}:{line_number}: {exc}") from exc
    return records


def prevented_recurrences(
    records: Iterable[object],
) -> list[tuple[int, int, str, str]]:
    """Return (recurrence line, prevention line, identity, check) findings."""
    prevented: dict[str, tuple[int, str]] = {}
    findings: list[tuple[int, int, str, str]] = []
    for line_number, raw in enumerate(records, start=1):
        record = validate(raw)
        identity = cast(str, record["identity"])
        previous = prevented.get(identity)
        if previous is not None:
            findings.append((line_number, previous[0], identity, previous[1]))
        check = record.get("prevention_check")
        if isinstance(check, str) and identity not in prevented:
            prevented[identity] = (line_number, check)
    return findings

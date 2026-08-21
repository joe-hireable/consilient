"""Append a canonical error locally, then optionally export it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.error_tracking import (  # noqa: E402
    ErrorRecordError,
    append_record,
    build_record,
    canonical,
    validate,
)

DEFAULT_STORE = ROOT / ".harness" / "log" / "errors" / "errors.jsonl"
DEFAULT_OTLP_ENDPOINT = "http://127.0.0.1:4318/v1/logs"


def _safe_http_url(endpoint: str, *, suffix: str) -> str:
    try:
        parsed = urlsplit(endpoint)
        host = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ErrorRecordError("endpoint is not a valid HTTP URL") from exc
    if (
        parsed.scheme not in ("http", "https")
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.endswith(suffix)
    ):
        raise ErrorRecordError(f"endpoint must be a credential-free {suffix} HTTP URL")
    return endpoint


def _attribute(key: str, value: str) -> dict[str, object]:
    return {"key": key, "value": {"stringValue": value}}


def otlp_request(record: object, endpoint: str = DEFAULT_OTLP_ENDPOINT) -> Request:
    """Build an OTLP/HTTP JSON logs request outside the product boundary."""
    checked = validate(record)
    observed = datetime.fromisoformat(cast(str, checked["observed_at"]))
    delta = observed - datetime(1970, 1, 1, tzinfo=timezone.utc)
    nanos = (
        delta.days * 86_400 + delta.seconds
    ) * 1_000_000_000 + delta.microseconds * 1_000
    attributes = [
        _attribute("error.identity", cast(str, checked["identity"])),
        _attribute("error.component", cast(str, checked["component"])),
        _attribute("error.type", cast(str, checked["error_type"])),
        _attribute(
            "error.prevention",
            cast(str, checked.get("prevention_check", "no_check_yet")),
        ),
    ]
    payload = {
        "resourceLogs": [
            {
                "resource": {"attributes": [_attribute("service.name", "consilient")]},
                "scopeLogs": [
                    {
                        "scope": {"name": "consilient.error_tracking"},
                        "logRecords": [
                            {
                                "timeUnixNano": str(nanos),
                                "severityNumber": 17,
                                "severityText": "ERROR",
                                "body": {"stringValue": checked["error_code"]},
                                "attributes": attributes,
                            }
                        ],
                    }
                ],
            }
        ]
    }
    return Request(
        _safe_http_url(endpoint, suffix="/v1/logs"),
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "consilient/0.1.0"},
        method="POST",
    )


def sentry_request(record: object, dsn: str) -> Request:
    """Build one Sentry-compatible envelope request outside product code."""
    checked = validate(record)
    try:
        parsed = urlsplit(dsn)
        host_name = parsed.hostname
        port_number = parsed.port
    except ValueError as exc:
        raise ErrorRecordError("SENTRY_DSN is not a valid HTTP URL") from exc
    if (
        parsed.scheme not in ("http", "https")
        or not host_name
        or not parsed.username
        or re.fullmatch(r"[A-Za-z0-9_-]+", parsed.username) is None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ErrorRecordError(
            "SENTRY_DSN must contain a public key, host and project id"
        )
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments or not segments[-1].isdigit():
        raise ErrorRecordError("SENTRY_DSN must contain a project id")
    port = f":{port_number}" if port_number is not None else ""
    host = f"[{host_name}]" if ":" in host_name else host_name
    prefix = (
        "/" + "/".join(quote(segment) for segment in segments[:-1])
        if len(segments) > 1
        else ""
    )
    endpoint = (
        f"{parsed.scheme}://{host}{port}{prefix}/api/{quote(segments[-1])}/envelope/"
    )
    event_id = hashlib.sha256(canonical(checked).encode("ascii")).hexdigest()[:32]
    event = {
        "event_id": event_id,
        "timestamp": checked["observed_at"],
        "level": "error",
        "platform": "other",
        "logger": checked["component"],
        "message": checked["error_code"],
        "fingerprint": [checked["identity"]],
        "exception": {
            "values": [{"type": checked["error_type"], "value": checked["error_code"]}]
        },
    }
    event_bytes = json.dumps(event, separators=(",", ":")).encode("utf-8")
    envelope = b"\n".join(
        (
            json.dumps(
                {"event_id": event_id, "sent_at": checked["observed_at"]},
                separators=(",", ":"),
            ).encode("utf-8"),
            json.dumps(
                {
                    "type": "event",
                    "content_type": "application/json",
                    "length": len(event_bytes),
                },
                separators=(",", ":"),
            ).encode("utf-8"),
            event_bytes,
            b"",
        )
    )
    return Request(
        endpoint,
        data=envelope,
        headers={
            "Content-Type": "application/x-sentry-envelope",
            "X-Sentry-Auth": (
                "Sentry sentry_version=7,sentry_client=consilient/0.1.0,"
                f"sentry_key={parsed.username}"
            ),
        },
        method="POST",
    )


def send(request: Request, *, timeout: float = 5.0) -> None:
    """Send one optional export after its local record has been persisted."""
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is explicit
        status = getattr(response, "status", 200)
        if not 200 <= status < 300:
            raise ErrorRecordError(f"export returned HTTP {status}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    parser.add_argument("--component", required=True)
    parser.add_argument("--error-type", required=True)
    parser.add_argument("--error-code", required=True)
    parser.add_argument("--observed-at")
    judgement = parser.add_mutually_exclusive_group(required=True)
    judgement.add_argument("--prevented-by")
    judgement.add_argument("--no-check-yet", action="store_true")
    parser.add_argument(
        "--otlp-endpoint",
        nargs="?",
        const=DEFAULT_OTLP_ENDPOINT,
        help="optionally POST OTLP/HTTP JSON logs (default: local collector)",
    )
    parser.add_argument(
        "--sentry",
        action="store_true",
        help="optionally export using SENTRY_DSN from the environment",
    )
    args = parser.parse_args(argv)

    try:
        record = build_record(
            component=args.component,
            error_type=args.error_type,
            error_code=args.error_code,
            observed_at=args.observed_at,
            prevention_check=args.prevented_by,
            no_check_yet=args.no_check_yet,
        )
        path = Path(args.store)
        append_record(path, record)
    except (ErrorRecordError, OSError) as exc:
        print(f"error tracking failed: {exc}", file=sys.stderr)
        return 1

    dsn = os.environ.get("SENTRY_DSN", "") if args.sentry else ""
    if args.sentry and not dsn:
        print(
            "local error recorded; Sentry export skipped because SENTRY_DSN is unset",
            file=sys.stderr,
        )
        return 1
    try:
        if args.otlp_endpoint:
            send(otlp_request(record, args.otlp_endpoint))
        if args.sentry:
            send(sentry_request(record, dsn))
    except (ErrorRecordError, OSError) as exc:
        print(f"local error recorded; optional export failed: {exc}", file=sys.stderr)
        return 1
    print(f"recorded {record['identity']} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

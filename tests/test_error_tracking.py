"""R35: native error identity and prevention recurrence."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from consilient.error_tracking import (
    ErrorRecordError,
    append_record,
    build_record,
    prevented_recurrences,
    read_records,
    validate,
)

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _record(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "component": "dispatch",
        "error_type": "TimeoutError",
        "error_code": "child_timeout",
        "observed_at": "2026-08-21T19:00:00+00:00",
        "no_check_yet": True,
    }
    values.update(overrides)
    return build_record(**values)  # type: ignore[arg-type]


def test_identity_is_stable_and_raw_details_are_not_admitted() -> None:
    first = _record()
    fixed = _record(
        observed_at="2026-08-21T20:00:00+00:00",
        no_check_yet=False,
        prevention_check="tests/test_dispatch.py::test_child_timeout_kills_tree",
    )

    assert first["identity"] == fixed["identity"]
    with pytest.raises(ErrorRecordError, match="unexpected field"):
        validate(
            {
                **first,
                "message": r"C:\Users\person\repo\.env token=do-not-record",
            }
        )
    with pytest.raises(ErrorRecordError, match="error_code"):
        _record(error_code=r"C:\Users\person\repo\failure")


def test_record_requires_exactly_one_prevention_judgement() -> None:
    with pytest.raises(ErrorRecordError, match="exactly one"):
        _record(no_check_yet=False)
    with pytest.raises(ErrorRecordError, match="exactly one"):
        _record(prevention_check="tests/test_dispatch.py::test_timeout")
    with pytest.raises(ErrorRecordError, match="repository-relative"):
        _record(
            no_check_yet=False,
            prevention_check=r"C:\private\test_dispatch.py::test_timeout",
        )
    with pytest.raises(ErrorRecordError, match="repository-relative"):
        _record(
            no_check_yet=False,
            prevention_check="tests/../outside.py::test_timeout",
        )
    with pytest.raises(ErrorRecordError, match="v must be"):
        validate({**_record(), "v": True})


def test_local_append_round_trip_is_canonical(tmp_path: Path) -> None:
    path = tmp_path / "errors.jsonl"
    record = _record()
    append_record(path, record)

    assert read_records(path) == [record]
    assert path.read_text(encoding="utf-8").strip() == json.dumps(
        record, sort_keys=True, separators=(",", ":")
    )


def test_export_requests_use_replaceable_protocol_boundaries() -> None:
    script = _load(
        "error_tracking_exports_test", ROOT / "scripts" / "error_tracking.py"
    )
    record = _record()
    otlp = script.otlp_request(record, "http://127.0.0.1:4318/v1/logs")
    otlp_body = json.loads(bytes(otlp.data).decode("utf-8"))
    log_record = otlp_body["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    assert otlp.full_url == "http://127.0.0.1:4318/v1/logs"
    assert log_record["attributes"][0]["value"]["stringValue"] == record["identity"]

    sentry = script.sentry_request(record, "https://public-key@sentry.example/42")
    body = bytes(sentry.data).decode("utf-8")
    assert sentry.full_url == "https://sentry.example/api/42/envelope/"
    assert "public-key" not in body
    assert "C:\\Users" not in body
    assert sentry.get_header("X-sentry-auth") is not None
    assert bytes(sentry.data).endswith(b"\n")

    with pytest.raises(ErrorRecordError, match="credential-free"):
        script.otlp_request(record, "https://token@collector.example/v1/logs")
    with pytest.raises(ErrorRecordError, match="project id"):
        script.sentry_request(record, "https://publickey@sentry.example/project")


def test_recurrence_only_fails_after_identity_is_marked_prevented() -> None:
    observed = _record()
    prevented = _record(
        observed_at="2026-08-21T19:01:00+00:00",
        no_check_yet=False,
        prevention_check="tests/test_dispatch.py::test_child_timeout_kills_tree",
    )
    recurred = _record(observed_at="2026-08-21T19:02:00+00:00")

    assert prevented_recurrences([observed, prevented]) == []
    assert prevented_recurrences([observed, prevented, recurred]) == [
        (3, 2, observed["identity"], prevented["prevention_check"])
    ]


def test_ci_checker_detects_mutation_and_accepts_clean_restore(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checker = _load(
        "check_error_recurrence_test",
        ROOT / ".github" / "scripts" / "check_error_recurrence.py",
    )
    path = tmp_path / "errors.jsonl"
    prevented = _record(
        no_check_yet=False,
        prevention_check="tests/test_error_tracking.py::test_ci_checker_detects_mutation_and_accepts_clean_restore",
    )
    append_record(path, prevented)
    assert checker.main([str(path)]) == 0

    append_record(
        path,
        _record(observed_at="2026-08-21T19:03:00+00:00"),
    )
    assert checker.main([str(path)]) == 1
    assert "recurred" in capsys.readouterr().out

    path.write_text(json.dumps(prevented) + "\n", encoding="utf-8")
    assert checker.main([str(path)]) == 0


def test_ci_checker_requires_the_named_prevention_check_to_exist(
    tmp_path: Path,
) -> None:
    checker = _load(
        "check_error_recurrence_missing_test",
        ROOT / ".github" / "scripts" / "check_error_recurrence.py",
    )
    path = tmp_path / "errors.jsonl"
    append_record(
        path,
        _record(
            no_check_yet=False,
            prevention_check="tests/missing_error_check.py::test_missing",
        ),
    )
    assert checker.main([str(path)]) == 1

    for node in ("definitely_not_a_test", "_record"):
        path.write_text("", encoding="utf-8")
        append_record(
            path,
            _record(
                no_check_yet=False,
                prevention_check=f"tests/test_error_tracking.py::{node}",
            ),
        )
        assert checker.main([str(path)]) == 1


def test_ingest_script_defaults_to_local_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load("error_tracking_script_test", ROOT / "scripts" / "error_tracking.py")
    path = tmp_path / "errors.jsonl"
    assert (
        script.main(
            [
                "--store",
                str(path),
                "--component",
                "dispatch",
                "--error-type",
                "TimeoutError",
                "--error-code",
                "child_timeout",
                "--no-check-yet",
            ]
        )
        == 0
    )
    assert len(read_records(path)) == 1

    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert (
        script.main(
            [
                "--store",
                str(path),
                "--component",
                "dispatch",
                "--error-type",
                "ValueError",
                "--error-code",
                "invalid_result",
                "--no-check-yet",
                "--sentry",
            ]
        )
        == 1
    )
    assert len(read_records(path)) == 2


def test_collector_config_is_local_and_credential_free() -> None:
    text = (ROOT / "config" / "otel-collector-errors.yaml").read_text(encoding="utf-8")
    assert "127.0.0.1:4318" in text
    assert "otlp:" in text
    assert "debug:" in text
    assert "SENTRY_DSN" not in text
    assert "authorization" not in text.lower()

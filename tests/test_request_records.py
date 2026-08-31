"""X05 — per-request timing record emitted in production, not only under test.

The row must carry every field named in
docs/20-design/measurement-and-efficiency-2026-08-23.md BU5. A harness dispatch that
completes without a request.record in the trajectory is a silent regression.

The checks that keep this unit honest:

- Two flushed writes 1.2s apart must be two chunks, with first-nonempty delay
  near the first flush — not one buffered read timestamped at EOF.
- Missing provider usage stays None. Zero is only recorded when the provider
  reported zero. Cursor ``--output-format text`` destroys the JSON envelope
  (docs/20-design/quota-pools-and-routes-2026-08-21.md); production must not
  request text, and a text transcript must not invent tokens.
- dispatch_one records timing from a live child through run_harness, not from a
  hand-built RequestTiming stub. A metered provider call is refused by the
  brief; a local unbuffered child on the production path is the substitute.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from family_source import seam

from consilient.events import read, read_all, validate
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    Probe,
    REQUEST_RECORD_FIELDS,
    REQUEST_RECORD_KIND,
    RequestTiming,
    extract_usage_from_output,
    record_request,
    validate_request_record,
)

ROOT = Path(__file__).resolve().parent.parent
DISPATCH_PATH = ROOT / "scripts" / "dispatch.py"
CURSOR = next(item for item in HARNESSES if item.id == "cursor-composer")

INSTALLED = tuple(
    Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
)

TWO_FLUSH_CHILD = (
    "import json, sys, time\n"
    "sys.stdout.write('first\\n')\n"
    "sys.stdout.flush()\n"
    "time.sleep(0.6)\n"
    "sys.stdout.write('second\\n')\n"
    "sys.stdout.flush()\n"
    "sys.stdout.write(json.dumps("
    "{'usage': {'output_tokens': 7, 'cache': {'read': 2}}}"
    ") + '\\n')\n"
    "sys.stdout.flush()\n"
)


def _load_script():
    name = "consilient_dispatch_script_x05"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _iso(offset_s: float = 0.0) -> str:
    return datetime.fromtimestamp(
        datetime.now(timezone.utc).timestamp() + offset_s, tz=timezone.utc
    ).isoformat()


def _complete_timing(**over: object) -> RequestTiming:
    base: dict[str, object] = {
        "t_send": _iso(),
        "t_first_chunk": _iso(0.01),
        "t_first_nonempty_chunk": _iso(0.02),
        "n_chunks": 3,
        "output_tokens": 12,
        "cache_read_input_tokens": 4,
        "in_flight_at_dispatch": 2,
    }
    base.update(over)
    return RequestTiming(**base)  # type: ignore[arg-type]


def _delay_s(start: str, later: str) -> float:
    return (
        datetime.fromisoformat(later) - datetime.fromisoformat(start)
    ).total_seconds()


def test_request_record_schema_lists_every_bu5_field() -> None:
    assert REQUEST_RECORD_FIELDS == (
        "t_send",
        "t_first_chunk",
        "t_first_nonempty_chunk",
        "n_chunks",
        "output_tokens",
        "cache_read_input_tokens",
        "in_flight_at_dispatch",
    )


def test_validate_request_record_requires_every_field() -> None:
    timing = _complete_timing()
    row = validate_request_record(
        {
            "run_id": "20260823T200000-abc",
            "harness": "grok",
            **timing.as_data(),
        }
    )
    for field in REQUEST_RECORD_FIELDS:
        assert field in row
    with pytest.raises(ValueError, match="t_send"):
        validate_request_record({"run_id": "r", "harness": "grok"})
    with pytest.raises(ValueError, match="n_chunks"):
        data = {
            "run_id": "r",
            "harness": "grok",
            **{k: v for k, v in timing.as_data().items() if k != "n_chunks"},
        }
        validate_request_record(data)


def test_validate_request_record_allows_unknown_usage() -> None:
    timing = _complete_timing(output_tokens=None, cache_read_input_tokens=None)
    row = validate_request_record(
        {
            "run_id": "20260823T200000-abc",
            "harness": "cursor-composer",
            **timing.as_data(),
        }
    )
    assert row["output_tokens"] is None
    assert row["cache_read_input_tokens"] is None


def test_record_request_appends_a_valid_event(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    timing = _complete_timing()
    recorded = record_request(
        log_dir,
        ts=_iso(),
        run_id="20260823T200000-abc",
        harness_id="cursor-composer",
        timing=timing,
    )
    assert recorded["event"] == REQUEST_RECORD_KIND
    validate(recorded)
    log_file = log_dir / f"{recorded['ts'][:10]}.jsonl"
    events, _rejected = read(log_file)
    assert len(events) == 1
    data = events[0].data
    for field in REQUEST_RECORD_FIELDS:
        assert field in data


def test_extract_usage_from_grok_json_tail() -> None:
    stdout = (
        "log line\n"
        + json.dumps(
            {
                "usage": {
                    "output_tokens": 45,
                    "cache": {"read": 80},
                }
            }
        )
    )
    usage = extract_usage_from_output(stdout, "grok")
    assert usage == {"output_tokens": 45, "cache_read_input_tokens": 80}


def test_extract_usage_from_cursor_result_event() -> None:
    stdout = json.dumps(
        {
            "type": "result",
            "usage": {"outputTokens": 9, "cacheReadInputTokens": 3},
        }
    )
    usage = extract_usage_from_output(stdout, "cursor-composer")
    assert usage == {"output_tokens": 9, "cache_read_input_tokens": 3}


def test_extract_usage_from_cursor_exp05_field_names() -> None:
    # EXP-05 adapter_cursor.py observed cacheReadTokens, not cacheReadInputTokens.
    stdout = json.dumps(
        {
            "type": "result",
            "usage": {"outputTokens": 11, "cacheReadTokens": 5},
        }
    )
    usage = extract_usage_from_output(stdout, "cursor-composer")
    assert usage == {"output_tokens": 11, "cache_read_input_tokens": 5}


def test_extract_usage_from_pretty_printed_cursor_json() -> None:
    stdout = (
        "{\n"
        '  "type": "result",\n'
        '  "usage": {"outputTokens": 4, "cacheReadTokens": 1}\n'
        "}\n"
    )
    usage = extract_usage_from_output(stdout, "cursor-composer")
    assert usage == {"output_tokens": 4, "cache_read_input_tokens": 1}


def test_missing_usage_is_not_fabricated_as_zero() -> None:
    # quota-pools-and-routes-2026-08-21.md: text destroys the JSON envelope.
    usage = extract_usage_from_output(
        "I'll edit the file.\nDone.\n", "cursor-composer"
    )
    assert usage["output_tokens"] is None
    assert usage["cache_read_input_tokens"] is None
    empty = extract_usage_from_output("", "grok")
    assert empty["output_tokens"] is None
    assert empty["cache_read_input_tokens"] is None


def test_provider_reported_zero_is_measured_zero() -> None:
    stdout = json.dumps({"usage": {"output_tokens": 0, "cache": {"read": 0}}})
    usage = extract_usage_from_output(stdout, "grok")
    assert usage == {"output_tokens": 0, "cache_read_input_tokens": 0}


def test_run_process_returns_stream_timing(tmp_path: Path) -> None:
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, _duration, timing = script.run_process(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys; print('chunk'); sys.stdout.flush()",
        ],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=20,
    )
    assert timed_out is False
    assert code == 0
    assert timing is not None
    assert timing.n_chunks >= 1
    assert timing.t_send
    assert timing.t_first_chunk
    assert timing.t_first_nonempty_chunk
    assert timing.t_first_nonempty_chunk >= timing.t_first_chunk >= timing.t_send


def test_run_process_observes_separate_flushed_chunks(tmp_path: Path) -> None:
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    _code, timed_out, duration, timing = script.run_process(
        [sys.executable, "-u", "-c", TWO_FLUSH_CHILD],
        cwd=tmp_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_s=20,
    )
    assert timed_out is False
    assert timing is not None
    assert timing.n_chunks >= 2
    delay = _delay_s(timing.t_send, timing.t_first_nonempty_chunk)
    assert delay < 0.3, (
        f"first nonempty delay {delay:.3f}s looks like EOF, not the first flush"
    )
    assert duration >= 0.5
    text = stdout_path.read_text(encoding="utf-8")
    assert "first" in text and "second" in text


def test_cursor_command_requests_json_not_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: "  --force\n  --trust\n")
    argv = script.build_command(
        CURSOR,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="composer-2.5",
        permissions="bypass",
    )
    assert isinstance(argv, list)
    assert "--output-format" in argv
    fmt = argv[argv.index("--output-format") + 1]
    assert fmt == "json"
    assert "text" not in argv


def test_cursor_wsl_command_requests_json_not_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: None)
    monkeypatch.setattr(seam("dispatch_launch"), "wsl_bridge", lambda: "wsl")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: "  --force\n  --trust\n")
    argv = script.build_command(
        CURSOR,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="composer-2.5",
        permissions="bypass",
    )
    assert isinstance(argv, list)
    inner = argv[-1]
    assert "--output-format json" in inner
    assert "--output-format text" not in inner


def test_dispatch_once_emits_request_record_from_live_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load_script()
    log_dir = tmp_path / "log"
    runs_dir = tmp_path / "runs"
    cwd = tmp_path / "repo"
    cwd.mkdir()
    monkeypatch.setattr(seam("dispatch_evidence"), "find_grok", lambda: "grok")
    monkeypatch.setattr(seam("dispatch_evidence"), "metered_grok_reason", lambda: None)
    monkeypatch.setattr(
        seam("dispatch_launch"), "help_text", lambda _argv: "  --max-turns <N>\n"
    )
    monkeypatch.setattr(
        seam("dispatch_invocation"),
        "build_command",
        lambda *_args, **_kwargs: [sys.executable, "-u", "-c", TWO_FLUSH_CHILD],
    )
    decision = script.select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="grok",
        allow_exhausted=True,
    )
    payload, exit_code = script.dispatch_one(
        decision=decision,
        task="pong",
        cwd=cwd,
        log_dir=log_dir,
        runs_dir=runs_dir,
        timeout_s=30,
        model=None,
        dry_run=False,
        permissions="bypass",
        claims=(),
        family=None,
        pools=DEFAULT_POOLS,
    )
    assert exit_code == 0
    events, _rejected = read_all(log_dir)
    kinds = [event.kind for event in events]
    assert REQUEST_RECORD_KIND in kinds
    record = next(event for event in events if event.kind == REQUEST_RECORD_KIND)
    for field in REQUEST_RECORD_FIELDS:
        assert field in record.data
    assert record.data["n_chunks"] >= 2
    assert record.data["output_tokens"] == 7
    assert record.data["cache_read_input_tokens"] == 2
    delay = _delay_s(str(record.data["t_send"]), str(record.data["t_first_nonempty_chunk"]))
    assert delay < 0.3
    assert payload["status"] == "ok"


def test_request_record_survives_event_validation() -> None:
    timing = _complete_timing()
    event = {
        "v": 1,
        "ts": _iso(),
        "event": REQUEST_RECORD_KIND,
        "actor": "consilient.dispatch",
        "data": {
            "run_id": "20260823T200000-abc",
            "harness": "grok",
            **timing.as_data(),
        },
    }
    validate(event)


def test_unknown_usage_record_survives_event_validation() -> None:
    timing = _complete_timing(output_tokens=None, cache_read_input_tokens=None)
    event = {
        "v": 1,
        "ts": _iso(),
        "event": REQUEST_RECORD_KIND,
        "actor": "consilient.dispatch",
        "data": {
            "run_id": "20260823T200000-abc",
            "harness": "cursor-composer",
            **timing.as_data(),
        },
    }
    validate(event)
    assert event["data"]["output_tokens"] is None

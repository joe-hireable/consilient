"""X05 — per-request timing record emitted in production, not only under test.

The row must carry every field named in
docs/20-design/measurement-and-efficiency-2026-08-23.md BU5. A harness dispatch that
completes without a request.record in the trajectory is a silent regression.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

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

INSTALLED = tuple(
    Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
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
    base = {
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


def test_run_process_returns_stream_timing(tmp_path: Path) -> None:
    script = _load_script()
    stdout_path = tmp_path / "stdout.txt"
    stderr_path = tmp_path / "stderr.txt"
    code, timed_out, _duration, timing = script.run_process(
        [
            sys.executable,
            "-c",
            "import sys, time; time.sleep(0.05); print('chunk'); sys.stdout.flush()",
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


def test_dispatch_once_emits_request_record_in_production_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load_script()
    log_dir = tmp_path / "log"
    runs_dir = tmp_path / "runs"
    cwd = tmp_path / "repo"
    cwd.mkdir()
    monkeypatch.setattr(script, "find_grok", lambda: "grok")
    monkeypatch.setattr(script, "metered_grok_reason", lambda: None)
    monkeypatch.setattr(script, "help_text", lambda _argv: "  --max-turns <N>\n")
    monkeypatch.setattr(
        script,
        "run_harness",
        lambda *args, **kwargs: script.RunResult(
            harness=HARNESSES[2],
            status="ok",
            reason="produced an artefact",
            exit_code=0,
            stdout='{"usage": {"output_tokens": 7, "cache": {"read": 2}}}',
            stderr="",
            artefact_bytes=40,
            diff_bytes=0,
            timed_out=False,
            duration_s=0.5,
            command=("grok",),
            run_id=kwargs["run_id"],
            stdout_path=str(runs_dir / kwargs["run_id"] / "stdout.txt"),
            stderr_path=str(runs_dir / kwargs["run_id"] / "stderr.txt"),
            request_timing=_complete_timing(
                output_tokens=7, cache_read_input_tokens=2
            ),
        ),
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
    assert record.data["output_tokens"] == 7
    assert record.data["cache_read_input_tokens"] == 2
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

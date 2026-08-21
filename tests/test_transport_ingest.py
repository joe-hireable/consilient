"""Inbound transport admission. ADR-0041: untrusted channels cannot deliver verdicts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from consilient.events import append, read
from consilient.transport import TransportAdmitError, admit

INGEST_PATH = Path(__file__).resolve().parent.parent / "scripts" / "ingest_transport.py"


def _ingest():
    name = "consilient_ingest_transport"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, INGEST_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "transport_name": "slack",
        "channel_id": "C123",
        "message_id": "1710000000.000100",
        "text": "look at the hiring home",
    }
    body.update(overrides)
    return body


def test_happy_path_appends_a_proposal(tmp_path: Path) -> None:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    code = _ingest().main(["--log", str(tmp_path), "--file", str(path)])
    assert code == 0
    logs = list(tmp_path.glob("*.jsonl"))
    assert logs
    events, rejected = read(logs[0])
    assert not rejected
    assert len(events) == 1
    raw = events[0].raw
    assert raw["event"] == "transport.proposal"
    assert raw["data"]["via"] == "slack"
    assert raw["data"]["via"] != "cli"
    assert raw["data"]["text"] == "look at the hiring home"


def test_duplicate_is_ignored(tmp_path: Path) -> None:
    first = admit(_payload(), log_dir=tmp_path)
    assert first is not None
    append(tmp_path / f"{first['ts'][:10]}.jsonl", first)
    second = admit(_payload(), log_dir=tmp_path)
    assert second is None


def test_verdict_shaped_payload_raises() -> None:
    with pytest.raises(TransportAdmitError, match="verdict-shaped"):
        admit(_payload(human_decision="verdict"))
    with pytest.raises(TransportAdmitError, match="verdict-shaped"):
        admit(_payload(event="approval"))
    with pytest.raises(TransportAdmitError, match="verdict-shaped"):
        admit(_payload(human_verdict="accept"))
    with pytest.raises(TransportAdmitError, match="verdict-shaped"):
        admit(
            _payload(
                data={"human_decision": "gate_lift", "principal": "joe"},
            )
        )


def test_via_cli_on_a_slack_payload_raises() -> None:
    with pytest.raises(TransportAdmitError, match="via=cli"):
        admit(_payload(via="cli"))


def test_ingest_cli_refuses_a_verdict(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(_payload(human_decision="approval")), encoding="utf-8")
    code = _ingest().main(["--log", str(tmp_path), "--file", str(path)])
    assert code == 2
    assert "refused" in capsys.readouterr().err

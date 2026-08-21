from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from consilient.harness import DEFAULT_POOLS, load_pools
from consilient.usage import Provenance, ProviderUsage, Quota


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "headroom.py"
NOW = datetime(2026, 8, 21, 20, 0, tzinfo=timezone.utc)


def _load_script():
    name = "consilient_headroom_script"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _quota_usage(
    *,
    observed_at: datetime | None = NOW,
    resets_at: datetime | None = NOW + timedelta(days=5),
    fraction: Decimal = Decimal("0.48"),
    provenance: Provenance = "measured",
) -> ProviderUsage:
    return ProviderUsage(
        provider="codex",
        kind="subscription",
        status="ok",
        detail="account/rateLimits/read",
        observed_at=observed_at,
        quotas=(Quota("10080m", fraction, resets_at, provenance),),
    )


def _unavailable(provider: str, detail: str = "no verified counter") -> ProviderUsage:
    return ProviderUsage(provider, "subscription", "unavailable", detail)


def test_refresh_attempts_all_three_and_never_resurrects_default_headroom(tmp_path):
    headroom = _load_script()
    attempted: list[str] = []

    def probe(provider: str, result=None, error: Exception | None = None):
        def run():
            attempted.append(provider)
            if error is not None:
                raise error
            assert result is not None
            return result

        return run

    output = tmp_path / "headroom.json"
    payload = headroom.refresh(
        output,
        {
            "codex": probe("codex", error=RuntimeError("fixture failure")),
            "claude": probe("claude", _unavailable("claude")),
            "cursor": probe("cursor", _unavailable("cursor")),
        },
        now=NOW,
    )

    assert attempted == ["codex", "claude", "cursor"]
    assert payload["observed_at"] == NOW.isoformat()
    assert set(payload["pools"]) == {pool.name for pool in DEFAULT_POOLS}
    pools = load_pools(output)
    assert all(pool.used_percent is None for pool in pools)
    assert all("unknown" in pool.note.casefold() for pool in pools)


def test_only_fresh_measured_codex_headroom_becomes_numeric(tmp_path):
    headroom = _load_script()
    output = tmp_path / "headroom.json"

    headroom.refresh(
        output,
        {
            "codex": _quota_usage,
            "claude": lambda: _unavailable("claude"),
            "cursor": lambda: _unavailable("cursor"),
        },
        now=NOW,
    )

    pools = {pool.name: pool for pool in load_pools(output)}
    assert pools["codex-weekly"].used_percent == 48.0
    assert all(
        pool.used_percent is None
        for name, pool in pools.items()
        if name != "codex-weekly"
    )


@pytest.mark.parametrize(
    "usage",
    [
        _quota_usage(observed_at=None),
        _quota_usage(observed_at=NOW - timedelta(minutes=15, microseconds=1)),
        _quota_usage(observed_at=NOW + timedelta(microseconds=1)),
        _quota_usage(resets_at=None),
        _quota_usage(resets_at=NOW),
        _quota_usage(fraction=Decimal("NaN")),
        _quota_usage(fraction=Decimal("1.01")),
        _quota_usage(provenance="cited"),
    ],
)
def test_missing_stale_malformed_or_unverified_telemetry_is_unknown(tmp_path, usage):
    headroom = _load_script()
    output = tmp_path / "headroom.json"

    headroom.refresh(
        output,
        {
            "codex": lambda: usage,
            "claude": lambda: _unavailable("claude"),
            "cursor": lambda: _unavailable("cursor"),
        },
        now=NOW,
    )

    codex = next(pool for pool in load_pools(output) if pool.name == "codex-weekly")
    assert codex.used_percent is None
    assert "unknown" in codex.note.casefold()


class _Input:
    def __init__(self) -> None:
        self.writes: list[str] = []

    def write(self, value: str) -> int:
        self.writes.append(value)
        return len(value)

    def flush(self) -> None:
        return None


class _ProtocolProcess:
    def __init__(self, lines: list[str]) -> None:
        self.stdin = _Input()
        self.stdout = iter(lines)
        self.pid = 123
        self.returncode = 0
        self.terminated = False

    def poll(self):
        return None if not self.terminated else self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        self.terminated = True
        return self.returncode

    def kill(self) -> None:
        self.terminated = True


def test_codex_fake_app_server_yields_measured_weekly_quota():
    headroom = _load_script()
    reset = int((NOW + timedelta(days=5)).timestamp())
    process = _ProtocolProcess(
        [
            json.dumps({"id": 1, "result": {}}) + "\n",
            json.dumps(
                {
                    "id": 2,
                    "result": {
                        "rateLimits": {
                            "planType": "pro",
                            "primary": {
                                "usedPercent": 48,
                                "windowDurationMins": 10080,
                                "resetsAt": reset,
                            },
                            "rateLimitReachedType": None,
                            "spendControlReached": False,
                        }
                    },
                }
            )
            + "\n",
        ]
    )
    captured: dict[str, object] = {}

    def popen(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return process

    usage = headroom.probe_codex(
        now=NOW,
        timeout_s=0.1,
        which=lambda _name: "codex",
        popen=popen,
    )

    assert usage.status == "ok"
    assert usage.observed_at == NOW
    assert usage.quotas == (
        Quota("10080m", Decimal("0.48"), NOW + timedelta(days=5), "measured"),
    )
    assert captured["argv"] == ["codex", "app-server", "--stdio"]
    kwargs = cast(dict[str, object], captured["kwargs"])
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    requests = [json.loads(value) for value in process.stdin.writes]
    assert [request["method"] for request in requests] == [
        "initialize",
        "account/rateLimits/read",
    ]


def test_codex_protocol_timeout_kills_the_process_tree(monkeypatch):
    headroom = _load_script()
    process = _ProtocolProcess([])
    killed: list[object] = []
    monkeypatch.setattr(headroom, "kill_process_tree", killed.append)

    usage = headroom.probe_codex(
        now=NOW,
        timeout_s=0.001,
        which=lambda _name: "codex",
        popen=lambda _argv, **_kwargs: process,
    )

    assert usage.status == "unavailable"
    assert "timed out" in usage.detail
    assert killed == [process]


def test_claude_and_cursor_numbers_without_verified_protocol_stay_unknown(monkeypatch):
    headroom = _load_script()

    def fake_run(argv, **_kwargs):
        if "about --format json" in argv[-1]:
            return (
                0,
                json.dumps(
                    {
                        "cliVersion": "2026.08.11",
                        "subscriptionTier": "Ultra",
                        "usedPercent": 1,
                        "resetsAt": int((NOW + timedelta(days=5)).timestamp()),
                    }
                ),
                "",
                False,
            )
        if "--version" in argv:
            return 0, "2.1.238 (Claude Code)", "", False
        return 0, "usage limit 1%; limits increased", "", False

    monkeypatch.setattr(headroom, "run_text", fake_run)
    claude = headroom.probe_claude(timeout_s=1, which=lambda _name: "claude")
    cursor = headroom.probe_cursor(
        timeout_s=1,
        which=lambda name: "wsl" if name == "wsl" else None,
    )

    assert claude.status == "unavailable" and not claude.quotas
    assert cursor.status == "unavailable" and not cursor.quotas


class _TimeoutProcess:
    def __init__(self) -> None:
        self.pid = 456
        self.returncode = None
        self.calls = 0

    def communicate(self, timeout=None):
        self.calls += 1
        if self.calls == 1:
            raise subprocess.TimeoutExpired("fixture", timeout)
        return "", ""

    def poll(self):
        return None

    def kill(self) -> None:
        return None


def test_text_probe_timeout_uses_utf8_replacement_and_kills_tree(monkeypatch):
    headroom = _load_script()
    process = _TimeoutProcess()
    captured: dict[str, object] = {}
    killed: list[object] = []

    def popen(argv, **kwargs):
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(headroom, "kill_process_tree", killed.append)
    code, _stdout, _stderr, timed_out = headroom.run_text(
        ["provider", "--help"], timeout_s=0.1, popen=popen
    )

    assert code is None
    assert timed_out is True
    assert killed == [process]
    kwargs = cast(dict[str, object], captured["kwargs"])
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"


def test_atomic_replace_failure_preserves_previous_snapshot(tmp_path, monkeypatch):
    headroom = _load_script()
    output = tmp_path / "headroom.json"
    output.write_text("old", encoding="utf-8")

    def fail_replace(_source, _target):
        raise PermissionError("fixture")

    monkeypatch.setattr(headroom.os, "replace", fail_replace)
    with pytest.raises(PermissionError):
        headroom.write_atomic(output, {"new": True})

    assert output.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.iterdir()) == [output]

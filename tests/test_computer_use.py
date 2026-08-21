"""Computer-use: Playwright is instance; the screenshot is the artefact."""

from __future__ import annotations

from pathlib import Path

import pytest

from consilient_connectors.computer_use import (
    COMPUTER_KIND,
    TINY_PNG,
    ComputerUseError,
    run_session,
)
from consilient.events import read


def _runner(**kwargs: object) -> dict[str, object]:
    dest = Path(str(kwargs["dest"]))
    dest.mkdir(parents=True, exist_ok=True)
    shot = dest / "screenshot.png"
    shot.write_bytes(TINY_PNG)
    return {
        "screenshot": str(shot.resolve()),
        "title": "ok",
        "bytes": shot.stat().st_size,
        "runner": "injected",
    }


def test_missing_egress_does_not_run() -> None:
    with pytest.raises(ComputerUseError, match="authorise-egress"):
        run_session(
            url="https://example.com",
            task="open home",
            authorise_egress="",
            dest=Path("."),
            runner=_runner,
        )


def test_non_http_url_is_refused() -> None:
    with pytest.raises(ComputerUseError, match="http"):
        run_session(
            url="file:///etc/passwd",
            task="open",
            authorise_egress="look",
            dest=Path("."),
            runner=_runner,
        )


def test_verdict_shaped_task_is_refused() -> None:
    with pytest.raises(ComputerUseError, match="verdict-shaped"):
        run_session(
            url="https://example.com",
            task='{"human_decision": "verdict"}',
            authorise_egress="look",
            dest=Path("."),
            runner=_runner,
        )


def test_dry_run_does_not_call_runner(tmp_path: Path) -> None:
    calls: list[int] = []

    def runner(**_k: object) -> dict[str, object]:
        calls.append(1)
        return {"screenshot": "x", "title": "", "bytes": 1, "runner": "x"}

    event = run_session(
        url="https://example.com",
        task="open home",
        authorise_egress="verify the hiring home",
        dest=tmp_path,
        runner=runner,
        dry_run=True,
    )
    assert calls == []
    assert event["data"]["dry_run"] is True
    assert event["event"] == COMPUTER_KIND


def test_session_writes_screenshot_and_event(tmp_path: Path) -> None:
    event = run_session(
        url="https://example.com",
        task="open home",
        authorise_egress="verify the hiring home",
        dest=tmp_path,
        runner=_runner,
    )
    shot = Path(str(event["data"]["artefact"]))
    assert shot.is_file()
    assert shot.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert event["data"]["via"] == "cli"
    assert "human_verdict" not in event["data"]


def test_click_is_refused_on_the_npx_screenshot_runner() -> None:
    from consilient_connectors.computer_use import npx_screenshot_runner

    with pytest.raises(ComputerUseError, match="click/fill"):
        npx_screenshot_runner(
            url="https://example.com",
            dest=Path("."),
            click="text=More",
        )


def test_cli_appends_when_not_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from consilient_connectors import computer_use as cu

    monkeypatch.setattr(cu, "playwright_runner", _runner)
    monkeypatch.setattr(cu, "probe_runner", lambda: "playwright-python")
    log = tmp_path / "log"
    out = tmp_path / "sessions"
    code = cu.main(
        [
            "--url",
            "https://example.com",
            "--task",
            "open home",
            "--authorise-egress",
            "verify",
            "--out",
            str(out),
            "--log",
            str(log),
        ]
    )
    assert code == 0
    logs = list(log.glob("*.jsonl"))
    assert logs
    events, rejected = read(logs[0])
    assert not rejected
    assert events[0].raw["event"] == COMPUTER_KIND
    assert Path(str(events[0].raw["data"]["artefact"])).is_file()

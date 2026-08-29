"""Computer-use as an admitted local capability (ADR-0042, ADR-0065).

Playwright is instance, not a Consilient dependency. If it is not importable,
the session is refused. The screenshot is the artefact; a human verdict is a
separate CLI event. Verdict-shaped tasks are refused (ADR-0041).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from consilient.events import EventError, SCHEMA_VERSION, EventPayload, append
from consilient.transport import looks_like_verdict

COMPUTER_KIND = "computer.use"
COMPUTER_ACTOR = "consilient.computer"
DEFAULT_RELATIVE = Path(".harness") / "computer-use"

# 1×1 PNG. Tests inject a runner; this is only for dry-run placeholders.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

Runner = Callable[..., dict[str, Any]]


class ComputerUseError(ValueError):
    """Probe failed, or the session could not produce an artefact."""


def probe_playwright() -> str | None:
    # importlib: Playwright is instance, not a Consilient dependency. A static
    # `import playwright` would fail mypy --strict on a machine without the package.
    try:
        import importlib

        importlib.import_module("playwright.sync_api")
    except ImportError:
        return None
    return "playwright-python"


# PINNED. `npx --yes playwright` resolves whatever the registry serves at the moment it runs,
# and this module ships as the `consilient-computer` console script, so `pip install consilient`
# puts an unpinned remote-code fetch on the user's PATH. MEASURED 29 August 2026: on this
# machine the bare spec is the SELECTED runner -- the Python playwright package is not
# importable here -- and the npx cache already records it resolving to ^1.62.1. The pin below is
# that same version, so it changes nothing about what runs today and makes tomorrow a decision
# rather than a download. Raising it is a deliberate edit with a licence check, per ADR-0009.
PLAYWRIGHT_SPEC = "playwright@1.62.1"


def _npx_binary() -> str | None:
    return shutil.which("npx") or shutil.which("npx.cmd")


def probe_npx_playwright() -> str | None:
    npx = _npx_binary()
    if npx is None:
        return None
    try:
        completed = subprocess.run(
            [npx, "--yes", PLAYWRIGHT_SPEC, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode == 0 and (completed.stdout or completed.stderr):
        return "npx-playwright"
    return None


def probe_runner() -> str | None:
    return probe_playwright() or probe_npx_playwright()


def playwright_runner(
    *,
    url: str,
    dest: Path,
    click: str | None = None,
    fill_selector: str | None = None,
    fill_value: str | None = None,
    wait_selector: str | None = None,
) -> dict[str, Any]:
    import importlib

    try:
        sync_api = importlib.import_module("playwright.sync_api")
    except ImportError as exc:
        raise ComputerUseError(
            "Python Playwright is not importable on this interpreter"
        ) from exc
    sync_playwright = sync_api.sync_playwright

    dest.mkdir(parents=True, exist_ok=True)
    shot = dest / "screenshot.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=15_000)
            if fill_selector and fill_value is not None:
                page.fill(fill_selector, fill_value)
            if click:
                page.click(click, timeout=15_000)
            title = page.title()
            page.screenshot(path=str(shot), full_page=True)
        finally:
            browser.close()
    if not shot.is_file() or shot.stat().st_size == 0:
        raise ComputerUseError("Playwright produced no screenshot")
    return {
        "screenshot": str(shot.resolve()),
        "title": title,
        "bytes": shot.stat().st_size,
        "runner": "playwright-python",
    }


def npx_screenshot_runner(
    *,
    url: str,
    dest: Path,
    click: str | None = None,
    fill_selector: str | None = None,
    fill_value: str | None = None,
    wait_selector: str | None = None,
) -> dict[str, Any]:
    if click or fill_selector:
        raise ComputerUseError(
            "click/fill need the Python Playwright package on this interpreter; "
            "npx playwright screenshot can only open a URL"
        )
    npx = _npx_binary()
    if npx is None:
        raise ComputerUseError("npx is not on PATH")
    dest.mkdir(parents=True, exist_ok=True)
    shot = dest / "screenshot.png"
    argv = [
        npx,
        "--yes",
        PLAYWRIGHT_SPEC,
        "screenshot",
        "--full-page",
        "--viewport-size",
        "1280,720",
        "--timeout",
        "30000",
    ]
    if wait_selector:
        argv.extend(["--wait-for-selector", wait_selector])
    argv.extend([url, str(shot)])
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ComputerUseError(f"npx playwright screenshot failed to start: {exc}") from exc
    if completed.returncode != 0 or not shot.is_file() or shot.stat().st_size == 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:400]
        raise ComputerUseError(
            f"npx playwright screenshot produced no artefact (exit {completed.returncode}): {detail}"
        )
    return {
        "screenshot": str(shot.resolve()),
        "title": "",
        "bytes": shot.stat().st_size,
        "runner": "npx-playwright",
    }


def run_session(
    *,
    url: str,
    task: str,
    authorise_egress: str,
    dest: Path,
    click: str | None = None,
    fill_selector: str | None = None,
    fill_value: str | None = None,
    wait_selector: str | None = None,
    runner: Runner | None = None,
    dry_run: bool = False,
) -> EventPayload:
    if not url.strip().startswith(("http://", "https://")):
        raise ComputerUseError("url must be http(s)")
    if not task.strip():
        raise ComputerUseError("task is required")
    if not authorise_egress.strip():
        raise ComputerUseError(
            "computer-use is egress: pass --authorise-egress naming the purpose (ADR-0042)"
        )
    payload: dict[str, Any] = {"transport_name": "computer", "text": task, "url": url}
    stripped = task.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            payload.update(parsed)
    found = looks_like_verdict(payload)
    if found is not None:
        raise ComputerUseError(
            f"refusing verdict-shaped computer-use task ({found!r}): "
            "the screenshot is an artefact, not a human decision (ADR-0041)"
        )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]
    session_dir = dest / run_id
    if dry_run:
        artefact = {
            "screenshot": "",
            "title": "",
            "bytes": 0,
            "runner": probe_runner() or "unavailable",
        }
    else:
        probed = probe_runner() if runner is None else "injected"
        if runner is None and probed is None:
            raise ComputerUseError(
                "No computer-use runner on this machine. Instance, not a Consilient "
                "dependency: npx playwright (already enough for screenshots) or "
                "pip install playwright && playwright install chromium"
            )
        if runner is not None:
            send = runner
        elif probed == "playwright-python":
            send = playwright_runner
        else:
            send = npx_screenshot_runner
        artefact = send(
            url=url.strip(),
            dest=session_dir,
            click=click,
            fill_selector=fill_selector,
            fill_value=fill_value,
            wait_selector=wait_selector,
        )
        if not str(artefact.get("screenshot") or "").strip():
            raise ComputerUseError("computer-use produced no screenshot artefact")
    now = datetime.now(timezone.utc).isoformat()
    return {
        "v": SCHEMA_VERSION,
        "ts": now,
        "event": COMPUTER_KIND,
        "actor": COMPUTER_ACTOR,
        "data": {
            "run_id": run_id,
            "url": url.strip(),
            "task": task.strip(),
            "artefact": artefact.get("screenshot") or "",
            "title": artefact.get("title") or "",
            "bytes": artefact.get("bytes") or 0,
            "runner": artefact.get("runner") or "",
            "click": click or "",
            "via": "cli",
            "dry_run": dry_run,
            "authorise_egress": authorise_egress.strip(),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", required=True, help="what this session is for")
    parser.add_argument("--authorise-egress", default="")
    parser.add_argument("--click", default="")
    parser.add_argument("--fill-selector", default="")
    parser.add_argument("--fill-value", default="")
    parser.add_argument("--wait-selector", default="")
    parser.add_argument("--out", default=str(DEFAULT_RELATIVE))
    parser.add_argument("--log", default=".harness/log")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        event = run_session(
            url=args.url,
            task=args.task,
            authorise_egress=args.authorise_egress,
            dest=Path(args.out),
            click=args.click or None,
            fill_selector=args.fill_selector or None,
            fill_value=args.fill_value if args.fill_selector else None,
            wait_selector=args.wait_selector or None,
            dry_run=args.dry_run,
        )
    except ComputerUseError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        if args.json:
            print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"dry-run: {event['data']['url']} runner={event['data']['runner']}")
        return 0
    log = Path(args.log)
    log.mkdir(parents=True, exist_ok=True)
    day = event["ts"][:10]
    try:
        recorded = append(log / f"{day}.jsonl", event)
    except EventError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    artefact = recorded["data"].get("artefact")
    if args.json:
        print(json.dumps(recorded, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{recorded['event']} {artefact} -> {log / f'{day}.jsonl'}")
    return 0

"""Refresh subscription headroom from local, non-inference provider protocols."""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.harness import (  # noqa: E402
    DEFAULT_POOLS,
    EXHAUSTED_USED_PERCENT,
    pools_from_mapping,
)
from consilient.usage import (  # noqa: E402
    ProviderUsage,
    Sources,
    collect_codex,
)

DEFAULT_OUTPUT = ROOT / ".harness" / "headroom.json"
MAX_AGE = timedelta(minutes=15)
PROVIDERS = ("codex", "claude", "cursor")
WINDOWS = os.name == "nt"
SOURCE = "scripts/headroom.py live local probes; unverified rows are unknown"

# A pool omitted here would be resurrected from harness.DEFAULT_POOLS by the reader.
POOL_RULES: dict[str, tuple[str, str | None]] = {
    "claude-weekly": ("claude", None),
    "cursor-models": ("cursor", None),
    "cursor-other": ("cursor", None),
    "grok-weekly": ("grok", None),
    "codex-weekly": ("codex", "10080m"),
}

Probe = Callable[[], ProviderUsage]
PopenFactory = Callable[..., Any]
Which = Callable[[str], str | None]


def _unavailable(provider: str, detail: str) -> ProviderUsage:
    return ProviderUsage(provider, "subscription", "unavailable", detail)


def _not_configured(provider: str, detail: str) -> ProviderUsage:
    return ProviderUsage(provider, "subscription", "not_configured", detail)


def _process_group() -> dict[str, object]:
    if WINDOWS:
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def kill_process_tree(process: Any) -> None:
    """Kill the process and its descendants after a timeout."""
    if process.poll() is not None:
        return
    if WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL", 9))
        except (OSError, PermissionError, ProcessLookupError):
            pass
    try:
        process.kill()
    except (OSError, PermissionError, ProcessLookupError):
        pass


def run_text(
    argv: list[str], *, timeout_s: float, popen: PopenFactory | None = None
) -> tuple[int | None, str, str, bool]:
    """Run a read-only CLI probe; a timeout always kills the process tree."""
    factory: PopenFactory = popen if popen is not None else subprocess.Popen
    try:
        process = factory(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **_process_group(),
        )
    except OSError:
        return None, "", "", False
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        kill_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=3)
        except (OSError, subprocess.SubprocessError):
            stdout, stderr = "", ""
        return None, stdout, stderr, True
    return process.returncode, stdout, stderr, False


def _request(
    process: Any,
    messages: queue.Queue[dict[str, object]],
    payload: dict[str, object],
    *,
    timeout_s: float,
) -> dict[str, object]:
    if process.stdin is None:
        raise RuntimeError("app-server stdin is unavailable")
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            message = messages.get(timeout=max(0.001, deadline - time.monotonic()))
        except queue.Empty:
            break
        if message.get("id") == payload["id"]:
            return message
    raise TimeoutError("app-server did not answer the rate-limit query")


def _stop_process(process: Any) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        kill_process_tree(process)
    except (OSError, PermissionError, ProcessLookupError):
        kill_process_tree(process)


def _codex_usage(response: dict[str, object], now: datetime) -> ProviderUsage:
    result = response.get("result")
    limits = result.get("rateLimits") if isinstance(result, dict) else None
    if not isinstance(limits, dict):
        return _unavailable("codex", "rate-limit response was malformed")
    plan = limits.get("planType")
    if plan in (None, "free", "unknown"):
        return _unavailable("codex", "subscription plan was not verified")
    if limits.get("rateLimitReachedType") is not None:
        return _unavailable("codex", "provider reports a reached rate limit")
    if limits.get("spendControlReached") is True:
        return _unavailable("codex", "provider reports a spend-control stop")

    payload = dict(response)
    payload["observed_at"] = now.isoformat()
    with tempfile.TemporaryDirectory(prefix="consilient-headroom-") as directory:
        path = Path(directory) / "codex.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return collect_codex(Sources(payloads=path.parent))


def probe_codex(
    *,
    now: datetime,
    timeout_s: float,
    which: Which = shutil.which,
    popen: PopenFactory | None = None,
) -> ProviderUsage:
    """Read Codex's documented account/rateLimits/read JSON-RPC method."""
    binary = which("codex")
    if binary is None:
        return _not_configured("codex", "codex executable was not found")
    factory: PopenFactory = popen if popen is not None else subprocess.Popen
    try:
        process = factory(
            [binary, "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            **_process_group(),
        )
    except OSError:
        return _unavailable("codex", "codex app-server could not start")

    messages: queue.Queue[dict[str, object]] = queue.Queue()

    def reader() -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(message, dict):
                messages.put(message)

    threading.Thread(target=reader, daemon=True).start()
    killed = False
    try:
        initialised = _request(
            process,
            messages,
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "consilient-headroom", "version": "0.1"},
                    "capabilities": {"experimentalApi": True},
                },
            },
            timeout_s=timeout_s,
        )
        if "error" in initialised:
            return _unavailable("codex", "codex app-server rejected initialization")
        response = _request(
            process,
            messages,
            {"id": 2, "method": "account/rateLimits/read"},
            timeout_s=timeout_s,
        )
        if "error" in response:
            return _unavailable(
                "codex", "codex app-server rejected the rate-limit query"
            )
        return _codex_usage(response, now)
    except TimeoutError:
        killed = True
        kill_process_tree(process)
        return _unavailable("codex", "codex app-server probe timed out")
    except (OSError, RuntimeError, TypeError, ValueError):
        return _unavailable("codex", "codex app-server response could not be verified")
    finally:
        if not killed:
            _stop_process(process)


def _version(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return " ".join(line.split())[:80]
    return "unknown version"


def probe_claude(
    *,
    timeout_s: float,
    which: Which = shutil.which,
    popen: PopenFactory | None = None,
) -> ProviderUsage:
    """Recheck the installed non-model surface; it has no standalone quota query."""
    binary = which("claude")
    if binary is None:
        return _not_configured("claude", "claude executable was not found")
    code, stdout, _stderr, timed_out = run_text(
        [binary, "--version"], timeout_s=timeout_s, popen=popen
    )
    if timed_out:
        return _unavailable("claude", "claude version probe timed out")
    if code != 0:
        return _unavailable("claude", "claude version probe failed")
    help_code, _help, _help_error, help_timed_out = run_text(
        [binary, "--help"], timeout_s=timeout_s, popen=popen
    )
    if help_timed_out:
        return _unavailable("claude", "claude help probe timed out")
    if help_code != 0:
        return _unavailable("claude", "claude help probe failed")
    return _unavailable(
        "claude",
        f"{_version(stdout)} exposes no verified non-model subscription quota command",
    )


def probe_cursor(
    *,
    timeout_s: float,
    which: Which = shutil.which,
    popen: PopenFactory | None = None,
) -> ProviderUsage:
    """Read Cursor about JSON; plan tier is observed but is not headroom."""
    native = which("cursor-agent")
    if native is not None:
        argv = [native, "about", "--format", "json"]
    else:
        bridge = which("wsl") or which("wsl.exe")
        if bridge is None:
            return _not_configured(
                "cursor", "cursor-agent and its WSL bridge were not found"
            )
        argv = [bridge, "-e", "bash", "-lc", "cursor-agent about --format json"]
    code, stdout, _stderr, timed_out = run_text(argv, timeout_s=timeout_s, popen=popen)
    if timed_out:
        return _unavailable("cursor", "cursor about probe timed out")
    if code != 0:
        return _unavailable("cursor", "cursor about probe failed")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return _unavailable("cursor", "cursor about output was not valid JSON")
    if not isinstance(payload, dict):
        return _unavailable("cursor", "cursor about output was not a JSON object")
    version = payload.get("cliVersion")
    label = version if isinstance(version, str) else "unknown version"
    return _unavailable(
        "cursor",
        f"Cursor {label} about JSON exposes tier but no verified pool usage or reset counter",
    )


def _unknown_row(detail: str) -> dict[str, object]:
    clean = " ".join(detail.split()) or "no verified observation"
    return {"used_percent": None, "exhausted": False, "note": f"unknown: {clean}"}


def _utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


def _pool_row(
    usage: ProviderUsage | None,
    *,
    window: str | None,
    now: datetime,
) -> dict[str, object]:
    if usage is None:
        return _unknown_row("provider was not probed")
    if usage.status != "ok":
        return _unknown_row(usage.detail)
    if window is None:
        return _unknown_row("no verified machine-readable pool counter")
    observed = _utc(usage.observed_at)
    if observed is None:
        return _unknown_row("observation timestamp is missing or malformed")
    age = now - observed
    if age < timedelta(0):
        return _unknown_row("observation timestamp is in the future")
    if age > MAX_AGE:
        return _unknown_row("observation is stale")
    quotas = [quota for quota in usage.quotas if quota.window == window]
    if len(quotas) != 1:
        return _unknown_row(f"no unambiguous {window} quota was reported")
    quota = quotas[0]
    if quota.provenance != "measured":
        return _unknown_row("quota is unverified")
    fraction = quota.used_fraction
    if (
        not isinstance(fraction, Decimal)
        or not fraction.is_finite()
        or fraction < 0
        or fraction > 1
    ):
        return _unknown_row("quota percentage is malformed")
    reset = _utc(quota.resets_at)
    if reset is None or reset <= now:
        return _unknown_row("quota reset timestamp is missing, malformed, or expired")
    used = float(fraction * 100)
    return {
        "used_percent": used,
        "exhausted": used >= EXHAUSTED_USED_PERCENT,
        "note": (
            f"{usage.detail}; observed {observed.isoformat()}; "
            f"resets {reset.isoformat()}"
        ),
    }


def snapshot_mapping(
    usages: Mapping[str, ProviderUsage], *, now: datetime
) -> dict[str, object]:
    current = _utc(now)
    if current is None:
        raise ValueError("snapshot time must be timezone-aware")
    pools = {
        pool.name: _pool_row(
            usages.get(POOL_RULES[pool.name][0]),
            window=POOL_RULES[pool.name][1],
            now=current,
        )
        for pool in DEFAULT_POOLS
    }
    return {"observed_at": current.isoformat(), "source": SOURCE, "pools": pools}


def write_atomic(path: Path, payload: Mapping[str, object]) -> None:
    """Replace one JSON file atomically; a failed replace preserves the previous file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def refresh(
    output: Path,
    probes: Mapping[str, Probe],
    *,
    now: datetime,
) -> dict[str, object]:
    """Attempt every subscription provider and atomically write an honest snapshot."""
    usages: dict[str, ProviderUsage] = {}
    for provider in PROVIDERS:
        probe = probes.get(provider)
        if probe is None:
            usages[provider] = _not_configured(provider, "no probe was configured")
            continue
        try:
            usage = probe()
        except (
            Exception
        ) as exc:  # one broken provider must not erase the other attempts
            usage = _unavailable(
                provider, f"probe failed safely ({type(exc).__name__})"
            )
        usages[provider] = (
            usage
            if isinstance(usage, ProviderUsage) and usage.provider == provider
            else _unavailable(provider, "probe returned an invalid provider record")
        )
    usages["grok"] = _unavailable(
        "grok", "provider is outside this three-provider probe"
    )
    payload = snapshot_mapping(usages, now=now)
    pools_from_mapping(payload)
    write_atomic(output, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh local Codex, Claude and Cursor subscription headroom."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    now = datetime.now(timezone.utc)
    payload = refresh(
        args.output.resolve(),
        {
            "codex": lambda: probe_codex(now=now, timeout_s=args.timeout),
            "claude": lambda: probe_claude(timeout_s=args.timeout),
            "cursor": lambda: probe_cursor(timeout_s=args.timeout),
        },
        now=now,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

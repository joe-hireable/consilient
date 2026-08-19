"""Read a sanitised Codex subscription headroom snapshot through app-server."""

from __future__ import annotations

import json
import queue
import shutil
import subprocess
import threading
import time


def _request(process, messages, payload, timeout=10.0):
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
        except queue.Empty:
            break
        if message.get("id") == payload["id"]:
            return message
    raise TimeoutError(f"no app-server response for request {payload['id']}")


def read_codex_headroom():
    codex = shutil.which("codex")
    if codex is None:
        raise RuntimeError("codex executable not found")
    process = subprocess.Popen(
        [codex, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    messages = queue.Queue()

    def reader():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    threading.Thread(target=reader, daemon=True).start()
    try:
        initialised = _request(
            process,
            messages,
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "consilience-exp07",
                        "version": "0.1",
                    },
                    "capabilities": {"experimentalApi": True},
                },
            },
        )
        if "error" in initialised:
            raise RuntimeError(initialised["error"])
        response = _request(
            process,
            messages,
            {"id": 2, "method": "account/rateLimits/read"},
        )
        if "error" in response:
            raise RuntimeError(response["error"])
        raw = response.get("result", {}).get("rateLimits", {})
        primary = raw.get("primary") or {}
        return {
            "observed_at_unix": int(time.time()),
            "plan_type": raw.get("planType"),
            "used_percent": primary.get("usedPercent"),
            "resets_at": primary.get("resetsAt"),
            "window_duration_mins": primary.get("windowDurationMins"),
            "rate_limit_reached_type": raw.get("rateLimitReachedType"),
            "spend_control_reached": raw.get("spendControlReached"),
        }
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


def admission_reason(snapshot, maximum_used_percent=90):
    if snapshot.get("plan_type") in (None, "free", "unknown"):
        return "subscription plan unavailable"
    if snapshot.get("used_percent") is None or snapshot.get("resets_at") is None:
        return "headroom unknown"
    if snapshot.get("rate_limit_reached_type") is not None:
        return "provider reports limit reached"
    if snapshot.get("spend_control_reached") is True:
        return "provider reports spend-control stop"
    if snapshot["used_percent"] > maximum_used_percent:
        return "reserved headroom unavailable"
    return None


if __name__ == "__main__":
    print(json.dumps(read_codex_headroom(), indent=2, sort_keys=True))

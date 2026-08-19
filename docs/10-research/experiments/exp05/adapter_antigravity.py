"""EXP-05 Antigravity CLI adapter with fail-closed credit admission.

This is an experimental measurement adapter, not product implementation. A
successful model-list call is deliberately not treated as execution readiness.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path


DEFAULT_AGY = Path(os.environ.get("LOCALAPPDATA", "")) / "agy" / "bin" / "agy.exe"
SETTINGS = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
GIT = shutil.which("git")


def credit_overage_disabled(settings_path=SETTINGS):
    """Missing means the documented false default; invalid config fails closed."""
    if not settings_path.exists():
        return True
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return settings.get("useG1Credits", False) is False


def parse_stream(stdout):
    parsed = {
        "model": None,
        "status": None,
        "response": "",
        "usage": {},
        "error": None,
    }
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") == "init":
            parsed["model"] = (event.get("init") or {}).get("model")
        if event.get("event") == "result":
            result = event.get("result") or {}
            parsed.update(
                status=result.get("status"),
                response=result.get("response") or "",
                usage=result.get("usage") or {},
                error=result.get("error"),
            )
    return parsed


def probe_ready(returncode, parsed):
    return returncode == 0 and parsed.get("status") == "SUCCESS"


def antigravity_command(ticket, model, agy_path=DEFAULT_AGY):
    """Build the structured, non-interactive CLI probe/edit command."""
    return [
        str(agy_path),
        f"--print={ticket['goal']}",
        "--output-format=stream-json",
        f"--model={model}",
        "--mode=accept-edits",
        "--sandbox",
        f"--print-timeout={ticket.get('timeout_s', 600)}s",
    ]


def run(ticket, model="gemini-3.7-flash-low", agy_path=DEFAULT_AGY):
    if not credit_overage_disabled():
        raise RuntimeError("Antigravity AI-credit overages must be disabled")
    if not agy_path.exists():
        raise RuntimeError("official Antigravity CLI not found")

    command = antigravity_command(ticket, model, agy_path)
    t0 = time.time()
    completed = subprocess.run(
        command,
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=ticket.get("timeout_s", 600) + 30,
    )
    parsed = parse_stream(completed.stdout)
    diff = subprocess.run(
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    usage = parsed["usage"]
    return {
        "ticket_id": ticket["id"],
        "agent": f"antigravity:{model}",
        "domain": "coding",
        "harness": "antigravity",
        "provider": "google-account:plan-unverified",
        "model": parsed["model"] or model,
        "ok": probe_ready(completed.returncode, parsed),
        "diff": diff,
        "tokens_in": usage.get("input_tokens"),
        "tokens_out": usage.get("output_tokens"),
        "cost_usd": None,
        "duration_s": round(time.time() - t0, 1),
        "raw_tail": json.dumps(
            {
                "status": parsed["status"],
                "response": parsed["response"],
                "error": parsed["error"],
                "stderr": completed.stderr[-500:],
            },
            separators=(",", ":"),
        )[-1000:],
    }

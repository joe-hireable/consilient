"""
EXP-05 coding composition #6: OpenCode × OpenRouter × model, run in WSL.

OpenCode is the provider-neutral coding harness. OpenRouter remains the provider
and can also be used without a coding harness for other domains (ADR-0027).
The API key crosses the Windows/WSL boundary through WSLENV; it is never placed
in the command or written to OpenCode's credential store by this adapter.
"""

import json
import os
import shutil
import subprocess
import time

WSL = shutil.which("wsl")
GIT = shutil.which("git")
OPENCODE_WSL = "/home/jpbpr/.opencode/bin/opencode"


def to_wsl_path(win_path):
    """Translate the Windows ticket path at the adapter boundary."""
    path = str(win_path).replace("\\", "/")
    if len(path) > 1 and path[1] == ":":
        return f"/mnt/{path[0].lower()}{path[2:]}"
    return path


def opencode_command(ticket, model):
    """Build a shell-free WSL command so paths and prompts stay single arguments."""
    return [
        WSL or "wsl",
        "-d",
        "Ubuntu",
        "-e",
        OPENCODE_WSL,
        "run",
        "--auto",
        "--format",
        "json",
        "--model",
        f"openrouter/{model}",
        "--dir",
        to_wsl_path(ticket["repo_dir"]),
        ticket["goal"],
    ]


def opencode_env(source=None):
    """Pass the provider key into WSL without putting it on the command line."""
    env = dict(os.environ if source is None else source)
    entries = [entry for entry in env.get("WSLENV", "").split(":") if entry]
    if not any(entry.split("/", 1)[0] == "OPENROUTER_API_KEY" for entry in entries):
        entries.append("OPENROUTER_API_KEY")
    env["WSLENV"] = ":".join(entries)
    return env


def parse_opencode_events(stdout):
    """Sum per-step usage and retain structured failures from OpenCode JSONL."""
    totals = {
        "tokens_in": 0,
        "tokens_out": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "cost_usd": 0.0,
    }
    seen_usage = False
    errors = []
    for line in (stdout or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part") or {}
        tokens = part.get("tokens") or event.get("usage") or {}
        if tokens:
            seen_usage = True
            cache = tokens.get("cache") or {}
            totals["tokens_in"] += tokens.get("input", 0) or 0
            totals["tokens_out"] += tokens.get("output", 0) or 0
            totals["cache_read_tokens"] += cache.get("read", 0) or 0
            totals["cache_write_tokens"] += cache.get("write", 0) or 0
        cost = part.get("cost", event.get("cost"))
        if cost is not None:
            seen_usage = True
            totals["cost_usd"] += cost
        event_type = str(event.get("type", part.get("type", ""))).lower()
        if "error" in event_type or "fail" in event_type:
            errors.append(json.dumps(event, sort_keys=True)[-1000:])
    if not seen_usage:
        totals = {key: None for key in totals}
    elif totals["cost_usd"] is not None:
        totals["cost_usd"] = round(totals["cost_usd"], 10)
    return totals, errors


def run(ticket, model="qwen/qwen3-coder"):
    if not WSL:
        raise RuntimeError("wsl not found; OpenCode is installed in WSL")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY not set")

    t0 = time.time()
    proc = subprocess.run(
        opencode_command(ticket, model),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=ticket.get("timeout_s", 900),
        env=opencode_env(),
    )
    duration = time.time() - t0
    usage, errors = parse_opencode_events(proc.stdout)
    diff = subprocess.run(
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return {
        "ticket_id": ticket["id"],
        "agent": f"opencode+openrouter:{model}",
        "domain": "coding",
        "harness": "opencode",
        "provider": "openrouter",
        "model": model,
        "ok": proc.returncode == 0 and not errors,
        "diff": diff,
        **usage,
        "duration_s": round(duration, 1),
        "raw_tail": ((errors[-1] if errors else "") or proc.stderr or proc.stdout or "")[-500:],
        "errors": errors[:3],
        "return_code": proc.returncode,
    }

"""
EXP-05 adapter #1: Claude Code, headless.

The interface below IS the experiment. It was designed against Claude Code alone,
on purpose. Adapter #2 (Codex) must be written WITHOUT refactoring this file;
every point where this interface fails to fit Codex gets recorded in
findings-exp05.md. If adapter #2 forces a redesign and #3 would force another,
ADR-0001's meta-harness surface is in trouble (see the register's stopping rule).

Interface (minimum viable, per architecture-sketch: "spawn, feed a ticket,
collect a diff"):

    ticket  = {"id": str, "goal": str, "repo_dir": str, "timeout_s": int}
    outcome = {"ticket_id", "agent", "domain", "harness", "provider", "model",
               "ok", "diff", "tokens_in", "tokens_out", "cost_usd",
               "duration_s", "raw_tail"}

Assumptions baked in (candidate breakage points for adapter #2):
  A1  the agent is invoked once per ticket, non-interactively, and exits
  A2  the agent emits a single JSON result object on stdout
  A3  token/cost accounting is present in that JSON
  A4  the artifact is whatever `git diff` shows in repo_dir afterwards
  A5  permissions can be pre-granted via a CLI flag for a sandboxed run
  A6  the working directory fully scopes the agent's file access
"""

import json
import shutil
import subprocess
import time

CLAUDE = shutil.which("claude")
GIT = shutil.which("git")


def run(ticket):
    if not CLAUDE:
        raise RuntimeError("claude CLI not found on PATH")
    t0 = time.time()
    proc = subprocess.run(
        [
            CLAUDE,
            "-p",
            ticket["goal"],
            "--output-format",
            "json",
            "--dangerously-skip-permissions",  # A5 — sandboxed scratch repos only
        ],
        cwd=ticket["repo_dir"],  # A6
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=ticket.get("timeout_s", 600),
    )
    duration = time.time() - t0

    result, cost, tok_in, tok_out = {}, None, None, None
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])  # A2
        cost = result.get("total_cost_usd")  # A3
        usage = result.get("usage") or {}
        tok_in = usage.get("input_tokens")
        tok_out = usage.get("output_tokens")
    except (json.JSONDecodeError, IndexError):
        pass  # recorded via raw_tail; a parse failure is itself a finding

    diff = subprocess.run(  # A4
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout

    return {
        "ticket_id": ticket["id"],
        "agent": "claude-code",
        "domain": "coding",
        "harness": "claude-code",
        "provider": "anthropic-first-party",
        "model": "unknown:not-recorded-by-adapter",
        "ok": proc.returncode == 0 and not result.get("is_error", False),
        "diff": diff,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": cost,
        "duration_s": round(duration, 1),
        "raw_tail": (proc.stdout or "")[-500:],
    }

"""
EXP-05 adapter #3: Cursor CLI (cursor-agent 2026.08.11), headless.

RULE OF THE EXPERIMENT: adapters #1 (Claude Code) and #2 (Codex) were NOT modified
to accommodate this file. Adapter #3 is the second clause of ADR-0001's stopping
rule — "if adapter #2 forces a redesign and #3 forces another, the surface is not
stable enough for one maintainer."

NEW BREAK, not seen in #1 or #2 — PLATFORM/NAMESPACE (call it A7, which adapters
#1 and #2 never had to state because it was invisible):

    Cursor's agent CLI ships for linux and darwin only (verified: the official
    installer at cursor.com/install exits "Unsupported operating system" on
    Windows, 2026.08.11). On Windows it must run inside WSL, which means the
    agent lives in a DIFFERENT PATH NAMESPACE from the orchestrator: the repo is
    C:\\... to the harness and /mnt/c/... to the agent.

    Consequence for the real interface: `ticket["repo_dir"]` cannot be a plain
    string shared by all adapters. Either the ticket carries a namespace-aware
    path object, or every adapter owns a translation seam. This adapter takes
    the second option so that adapters #1 and #2 stay untouched — but the
    finding is that the FIRST option is probably right, and that is an interface
    change discovered by adapter #3.

Other divergences:
  A2  Cursor uses --output-format json|text|stream-json (closest to #1's shape).
  A3  no cost field; token accounting not exposed on the CLI surface at all —
      third vendor, third accounting story (#1 last-call tokens, #2 cumulative
      session tokens, #3 nothing).
  A5  permissions via --force (non-interactive approval), a third spelling of
      the same idea.
"""

import json
import shutil
import subprocess
import time

WSL = shutil.which("wsl")
GIT = shutil.which("git")
CURSOR_WSL = "$HOME/.local/bin/cursor-agent"


def to_wsl_path(win_path):
    """A7: C:\\Users\\x -> /mnt/c/Users/x. The translation seam."""
    p = str(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def run(ticket):
    if not WSL:
        raise RuntimeError("wsl not found; Cursor CLI is linux/darwin only")
    wsl_dir = to_wsl_path(ticket["repo_dir"])
    goal = ticket["goal"].replace("'", "'\\''")
    inner = (
        f"cd '{wsl_dir}' && {CURSOR_WSL} --print --force --output-format json '{goal}'"
    )
    t0 = time.time()
    proc = subprocess.run(
        [WSL, "-d", "Ubuntu", "-e", "bash", "-lc", inner],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=ticket.get("timeout_s", 600),
    )
    duration = time.time() - t0

    result = {}
    try:
        result = json.loads((proc.stdout or "").strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        pass

    diff = subprocess.run(  # A4 holds — git is the common ground across all three
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout

    return {
        "ticket_id": ticket["id"],
        "agent": "cursor",
        "ok": proc.returncode == 0 and not result.get("is_error", False),
        "diff": diff,
        "tokens_in": None,  # A3 BREAK: not exposed
        "tokens_out": None,
        "cost_usd": None,
        "duration_s": round(duration, 1),
        "raw_tail": ((proc.stdout or "") + (proc.stderr or ""))[-500:],
    }

"""
EXP-05 adapter #2: Codex CLI (codex-cli 0.148.0), headless via `codex exec`.

RULE OF THE EXPERIMENT: adapter #1 (adapter_claude_code.py) was NOT modified to
accommodate this file. Every place this adapter had to diverge from #1's baked
assumptions A1-A6 is a measured interface break, recorded in findings-exp05.md.

Divergences implemented here (see findings for the full list):
  A2 BREAK  — Codex emits a JSONL *event stream* (--json), not one result
              object; the final message goes to a FILE (--output-last-message).
              The "parse the last stdout line as the result" contract dies.
  A3 BREAK  — no total_cost_usd anywhere; token usage arrives as token_count
              events in the stream with different field names.
  A5 BREAK  — permission pre-grant is a two-axis model (sandbox mode x approval
              policy), not one flag. Mapped: --dangerously-bypass-approvals-
              and-sandbox for scratch repos (the closest semantic match, not an
              equivalent).
  A6 BREAK  — working root is an explicit flag (-C), not the process cwd, and
              non-git directories additionally need --skip-git-repo-check.
"""

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CODEX = shutil.which("codex")
GIT = shutil.which("git")


def run(ticket):
    if not CODEX:
        raise RuntimeError("codex CLI not found on PATH")
    last_msg = Path(tempfile.mkstemp(prefix="codex_last_", suffix=".txt")[1])
    t0 = time.time()
    proc = subprocess.run(
        [
            CODEX,
            "exec",
            ticket["goal"],
            "--json",  # A2: JSONL stream
            "-C",
            ticket["repo_dir"],  # A6: explicit root
            "--dangerously-bypass-approvals-and-sandbox",  # A5: scratch repos only
            "--ephemeral",
            "-o",
            str(last_msg),  # A2: result via file
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=ticket.get("timeout_s", 600),
    )
    duration = time.time() - t0

    # A3: mine the event stream for usage; field names differ per event schema
    tok_in = tok_out = None
    err_events = []
    for line in (proc.stdout or "").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = ev.get("msg", ev)
        if "error" in str(ev.get("type", msg.get("type", ""))).lower():
            err_events.append(str(ev)[:200])
        info = msg.get("info") or msg.get("usage") or {}
        if isinstance(info, dict):
            ti = info.get("total_token_usage") or info
            tok_in = ti.get("input_tokens", tok_in)
            tok_out = ti.get("output_tokens", tok_out)

    diff = subprocess.run(  # A4 holds unchanged
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout

    final = last_msg.read_text(encoding="utf-8") if last_msg.exists() else ""
    return {
        "ticket_id": ticket["id"],
        "agent": "codex",
        "ok": proc.returncode == 0,
        "diff": diff,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": None,  # A3 BREAK: not reported
        "duration_s": round(duration, 1),
        "raw_tail": (final or proc.stderr or proc.stdout or "")[-500:],
        "errors": err_events[:3],
    }

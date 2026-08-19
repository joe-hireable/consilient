"""
EXP-05 adapters #4 and #5: local models (Ollama) and OpenRouter — both driven
through the Codex harness rather than a loop of our own.

    run_local(ticket, model)       -> Ollama on this machine, £0
    run_openrouter(ticket, model)  -> any OpenRouter model, metered

THE FINDING THIS FILE EXISTS TO RECORD, and it is the most consequential one in
EXP-05 so far:

    The architecture sketch splits execution into "delegated" (hand the task to
    someone's agent) and "native" (the harness runs its own loop against an open
    model). Codex collapses that split: `codex exec --oss --local-provider
    ollama` and a custom `model_providers` entry pointing at OpenRouter both give
    a full agent loop — tools, file edits, sandboxing — over an arbitrary model,
    for free.

    So the harness may never need to BUILD a native loop. It needs a *provider
    seam* inside an adapter it already has. That is ADR-0005's "wrap, don't
    build" arriving one layer higher than expected, and it is worth an explicit
    architecture-sketch amendment: "native execution" is a PROVIDER CHOICE, not
    a second execution path.

    Honest caveat: this makes the cheap tier inherit Codex's harness quality,
    which is a confound for any cascade measurement — cheap-vs-frontier would
    then compare MODELS with the harness held constant (good for ADR-0025's
    probe, which wants exactly that) but would NOT tell us how a cheap model
    performs under a *worse* harness, which is the realistic deployment. Record
    which question is being asked before quoting any number from it.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CODEX = shutil.which("codex")
GIT = shutil.which("git")


def _run_codex(ticket, extra_args, agent_name):
    if not CODEX:
        raise RuntimeError("codex CLI not found on PATH")
    last_msg = Path(tempfile.mkstemp(prefix="codex_last_", suffix=".txt")[1])
    t0 = time.time()
    proc = subprocess.run(
        [
            CODEX,
            "exec",
            ticket["goal"],
            "--json",
            "-C",
            ticket["repo_dir"],
            "--dangerously-bypass-approvals-and-sandbox",
            "--ephemeral",
            "-o",
            str(last_msg),
        ]
        + extra_args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=ticket.get("timeout_s", 900),
    )
    duration = time.time() - t0

    tok_in = tok_out = None
    for line in (proc.stdout or "").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = ev.get("msg", ev)
        info = msg.get("info") or msg.get("usage") or {}
        if isinstance(info, dict):
            ti = info.get("total_token_usage") or info
            tok_in = ti.get("input_tokens", tok_in)
            tok_out = ti.get("output_tokens", tok_out)

    diff = subprocess.run(
        [GIT, "diff"],
        cwd=ticket["repo_dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    final = last_msg.read_text(encoding="utf-8") if last_msg.exists() else ""

    return {
        "ticket_id": ticket["id"],
        "agent": agent_name,
        "ok": proc.returncode == 0,
        "diff": diff,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": None,
        "duration_s": round(duration, 1),
        "raw_tail": (final or proc.stderr or "")[-500:],
    }


def run_local(ticket, model="qwen3:8b"):
    """Ollama on this machine. Cheap tier for the cascade; £0 per token."""
    return _run_codex(
        ticket,
        ["--oss", "--local-provider", "ollama", "-m", model],
        f"ollama:{model}",
    )


def run_openrouter(ticket, model="qwen/qwen3-coder"):
    """Any OpenRouter model, via a Codex custom provider. Needs OPENROUTER_API_KEY."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return _run_codex(
        ticket,
        [
            "-c",
            'model_providers.openrouter.name="OpenRouter"',
            "-c",
            'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"',
            "-c",
            'model_providers.openrouter.env_key="OPENROUTER_API_KEY"',
            "-c",
            'model_provider="openrouter"',
            "-m",
            model,
        ],
        f"openrouter:{model}",
    )


# adapter-shaped entry point, so run_exp05.py can import this like the others
def run(ticket):
    model = ticket.get("model", "qwen3:8b")
    if ticket.get("backend") == "openrouter":
        return run_openrouter(ticket, model)
    return run_local(ticket, model)

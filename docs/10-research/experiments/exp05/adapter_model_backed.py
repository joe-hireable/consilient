"""
EXP-05 coding compositions #4 and #5: the Codex execution harness over local
Ollama and the OpenRouter provider.

    run_local(ticket, model)       -> Codex × Ollama × local model, £0
    run_openrouter(ticket, model)  -> Codex × OpenRouter × model, metered

THE CORRECTION THIS FILE EXISTS TO RECORD:

    Codex is the execution harness in both functions. Ollama and OpenRouter are
    providers, not coding agents. These compositions are valid coding backends,
    but they do not make OpenRouter itself a coding harness and they say nothing
    about a standalone OpenRouter provider path for non-coding tasks. ADR-0027
    records the domain × harness × provider × model split.

    Honest caveat: these runs make the cheap tier inherit Codex's harness quality,
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


def codex_command(ticket, extra_args, last_msg):
    """Build an isolated Codex command for a scratch experimental repository."""
    return [
        CODEX,
        "exec",
        ticket["goal"],
        "--json",
        "-C",
        ticket["repo_dir"],
        "--dangerously-bypass-approvals-and-sandbox",
        "--ephemeral",
        "--ignore-user-config",
        "-o",
        str(last_msg),
    ] + extra_args


def composition(provider, model):
    return {
        "agent": f"codex+{provider}:{model}",
        "domain": "coding",
        "harness": "codex",
        "provider": provider,
        "model": model,
    }


def codex_run_options(ticket):
    """Non-interactive execution must not inherit an open stdin pipe."""
    return {
        "stdin": subprocess.DEVNULL,
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": ticket.get("timeout_s", 900),
    }


def parse_codex_events(stdout):
    """Extract usage and structured failure events from Codex JSONL."""
    tok_in = tok_out = None
    errors = []
    for line in (stdout or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("msg", event)
        event_type = str(event.get("type", message.get("type", ""))).lower()
        if "error" in event_type or "fail" in event_type:
            errors.append(json.dumps(event, sort_keys=True)[-1000:])
        info = message.get("info") or message.get("usage") or {}
        if isinstance(info, dict):
            total = info.get("total_token_usage") or info
            tok_in = total.get("input_tokens", tok_in)
            tok_out = total.get("output_tokens", tok_out)
    return tok_in, tok_out, errors


def _run_codex(ticket, extra_args, provider, model):
    if not CODEX:
        raise RuntimeError("codex CLI not found on PATH")
    last_msg = Path(tempfile.mkstemp(prefix="codex_last_", suffix=".txt")[1])
    t0 = time.time()
    proc = subprocess.run(
        codex_command(ticket, extra_args, last_msg),
        **codex_run_options(ticket),
    )
    duration = time.time() - t0

    tok_in, tok_out, errors = parse_codex_events(proc.stdout)

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
        **composition(provider, model),
        "ok": proc.returncode == 0,
        "diff": diff,
        "tokens_in": tok_in,
        "tokens_out": tok_out,
        "cost_usd": None,
        "duration_s": round(duration, 1),
        "raw_tail": (final or (errors[-1] if errors else "") or proc.stderr or proc.stdout or "")[
            -500:
        ],
        "errors": errors[:3],
        "return_code": proc.returncode,
    }


def run_local(ticket, model="qwen3:8b"):
    """Ollama on this machine. Cheap tier for the cascade; £0 per token."""
    return _run_codex(
        ticket,
        ["--oss", "--local-provider", "ollama", "-m", model],
        "ollama",
        model,
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
        "openrouter",
        model,
    )


# adapter-shaped entry point, so run_exp05.py can import this like the others
def run(ticket):
    model = ticket.get("model", "qwen3:8b")
    if ticket.get("backend") == "openrouter":
        return run_openrouter(ticket, model)
    return run_local(ticket, model)

"""
EXP-05 adapter #7: Grok Build (@xai-official/grok 1.0.5), headless.

RULE OF THE EXPERIMENT: Adapters #1 through #6 were NOT modified to accommodate
this file. Adapter #7 tests ADR-0001's stopping rule — "if adapter #2 did not force
a redesign, the interface holds; by adapter #7 the stopping rule becomes so well
supported that continuing to test it is no longer informative."

AUTHENTICATION POLICY (ADR-0044):
  Sign-in must use the SuperGrok Heavy subscription (device code or OAuth).
  Metered xAI API keys (XAI_API_KEY, GROK_CODE_XAI_API_KEY, GROK_API_KEY) are
  strictly forbidden because OpenRouter is the only authorised metered vendor.
  This adapter refuses to execute if any metered xAI key is detected.

OBSERVED INTERFACE CONVERGENCE:
  A1  Single invocation via `-p / --single <PROMPT>` and exits. [measured]
  A2  Structured result via `--output-format json`. [measured]
  A3  Token usage in output payload. [measured]
  A4  Artefact collected via `git diff` in `ticket["repo_dir"]`. [measured]
  A5  Permissions pre-granted via `--permission-mode bypassPermissions` and
      `--always-approve`. [measured]
  A6  Working root explicitly set via `--cwd <DIR>`. [measured]
  A7  Windows native binary resolution via `~/.grok/bin/grok.exe` or `grok.cmd`. [measured]
"""

import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping

METERED_KEY_ENV_VARS = (
    "XAI_API_KEY",
    "GROK_CODE_XAI_API_KEY",
    "GROK_API_KEY",
)

GIT = shutil.which("git")


def refuse_metered_key(env: Mapping[str, str] | None = None) -> None:
    """Refuse metered xAI API key usage per ADR-0044.

    Grok must run under the user's SuperGrok Heavy subscription (device code or OAuth).
    Metered xAI keys are forbidden; OpenRouter is the only authorised metered vendor.
    """
    source = os.environ if env is None else env
    for var in METERED_KEY_ENV_VARS:
        if source.get(var):
            raise RuntimeError(
                f"Metered xAI API key detected in environment variable '{var}'. "
                "Per ADR-0044, Grok must use subscription authentication (device code / OAuth) "
                "and metered spend through direct vendor API keys is refused."
            )


def find_grok_binary() -> str | None:
    """Locate the Grok CLI binary on Windows or WSL."""
    candidates = [
        shutil.which("grok.exe"),
        shutil.which("grok.cmd"),
        shutil.which("grok"),
        str(Path.home() / ".grok" / "bin" / "grok.exe"),
        str(Path.home() / ".grok" / "bin" / "grok"),
        "/mnt/c/Users/jpbpr/.grok/bin/grok.exe",
    ]
    for candidate in candidates:
        if candidate and (Path(candidate).exists() or shutil.which(candidate)):
            return candidate
    return None


def to_native_path(path: str | Path) -> str:
    """Ensure path format matches the execution environment."""
    p = str(path)
    if os.name == "nt" and p.startswith("/mnt/"):
        # /mnt/c/Users/... -> C:/Users/...
        parts = p.split("/")
        if len(parts) >= 3 and len(parts[2]) == 1:
            drive = parts[2].upper()
            rest = "/".join(parts[3:])
            return f"{drive}:/{rest}"
    return p


def grok_command(
    ticket: dict[str, Any],
    model: str | None = None,
    grok_bin: str | None = None,
) -> list[str]:
    """Build Grok's headless single-turn command."""
    binary = grok_bin or find_grok_binary() or "grok"
    repo_dir = to_native_path(ticket["repo_dir"])
    cmd = [
        binary,
        "-p",
        ticket["goal"],
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
        "--always-approve",
        "--cwd",
        repo_dir,
    ]
    requested_model = model or ticket.get("model")
    if requested_model:
        cmd.extend(["--model", requested_model])
    if ticket.get("max_turns"):
        cmd.extend(["--max-turns", str(ticket["max_turns"])])
    return cmd


def _kill_process_tree(proc: subprocess.Popen[str]) -> None:
    """Kill process tree on Windows or POSIX to prevent orphan grandchildren."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except subprocess.SubprocessError:
            pass
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, AttributeError):
            pass
    if proc.poll() is None:
        try:
            proc.kill()
        except (ProcessLookupError, PermissionError):
            pass


def is_unauthenticated_output(stdout: str, stderr: str) -> bool:
    """Check if stdout/stderr indicates unauthenticated state."""
    combined = f"{stdout}\n{stderr}".lower()
    return (
        "not signed in" in combined
        or "not authenticated" in combined
        or "grok login --device-code" in combined
        or "grok login" in combined
        and "to authenticate" in combined
    )


def parse_result(stdout: str) -> dict[str, Any]:
    """Extract structured JSON result object from Grok's output."""
    raw = (stdout or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    # Try finding trailing JSON object from lines
    for line in reversed(raw.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    return {}


def usage_fields(result: dict[str, Any]) -> dict[str, Any]:
    """Extract usage fields observed in Grok's result."""
    if not isinstance(result, dict):
        result = {}
    usage = result.get("usage") or result.get("tokens") or {}
    if not isinstance(usage, dict):
        usage = {}
    cache = usage.get("cache") if isinstance(usage.get("cache"), dict) else {}
    return {
        "tokens_in": usage.get("input_tokens")
        or usage.get("inputTokens")
        or usage.get("input"),
        "tokens_out": usage.get("output_tokens")
        or usage.get("outputTokens")
        or usage.get("output"),
        "cache_read_tokens": usage.get("cache_read_tokens")
        or usage.get("cacheReadTokens")
        or cache.get("read"),
        "cache_write_tokens": usage.get("cache_write_tokens")
        or usage.get("cacheWriteTokens")
        or cache.get("write"),
    }


def identity_fields(result: dict[str, Any]) -> dict[str, Any]:
    """Preserve runtime identifiers when Grok emits them."""
    if not isinstance(result, dict):
        result = {}
    return {
        "session_id": result.get("session_id")
        or result.get("sessionId")
        or result.get("sessionID"),
        "request_id": result.get("request_id") or result.get("requestId"),
    }


def model_fields(
    requested_model: str | None, result: dict[str, Any]
) -> dict[str, Any]:
    """Keep requested model separate from evidence of selected model."""
    if not isinstance(result, dict):
        result = {}
    selected_model = (
        result.get("model")
        or result.get("selected_model")
        or result.get("selectedModel")
    )
    return {
        "model": selected_model
        or (requested_model if requested_model else "unknown:not-reported-by-runtime"),
        "model_requested": requested_model,
        "model_selected": selected_model,
    }


def run(
    ticket: dict[str, Any],
    model: str | None = None,
    env: Mapping[str, str] | None = None,
    grok_bin: str | None = None,
) -> dict[str, Any]:
    """Run one coding ticket through Grok headless CLI under subscription auth."""
    refuse_metered_key(env)

    binary = grok_bin or find_grok_binary()
    if not binary:
        raise RuntimeError(
            "grok CLI not found on PATH or ~/.grok/bin/grok.exe"
        )

    requested_model = model or ticket.get("model")
    cmd = grok_command(ticket, requested_model, binary)
    timeout_s = ticket.get("timeout_s", 600)

    effective_env = dict(os.environ if env is None else env)
    effective_env["PYTHONDONTWRITEBYTECODE"] = "1"

    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=ticket["repo_dir"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=effective_env,
        **kwargs,
    )

    timed_out = False
    stdout = ""
    stderr = ""
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", "Process tree kill timed out"
    duration = time.time() - t0

    unauth = is_unauthenticated_output(stdout, stderr)
    result = parse_result(stdout)
    usage = usage_fields(result)
    identity = identity_fields(result)
    models = model_fields(requested_model, result)

    diff = ""
    if GIT and Path(ticket["repo_dir"]).exists():
        diff_res = subprocess.run(
            [GIT, "diff"],
            cwd=ticket["repo_dir"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        diff = diff_res.stdout

    ok = (
        not timed_out
        and not unauth
        and proc.returncode == 0
        and not result.get("is_error", False)
    )

    raw_tail = ((stdout or "") + (stderr or ""))[-500:]
    if timed_out:
        raw_tail = f"TIMEOUT: Grok run exceeded deadline of {timeout_s}s\n" + raw_tail

    return {
        "ticket_id": ticket["id"],
        "agent": "grok",
        "domain": "coding",
        "harness": "grok",
        "provider": "xai-subscription",
        **models,
        **identity,
        "ok": ok,
        "authenticated": not unauth,
        "status": "not_ready" if unauth else ("timeout" if timed_out else ("ok" if ok else "error")),
        "diff": diff,
        **usage,
        "cost_usd": None,
        "duration_s": round(duration, 1),
        "raw_tail": raw_tail[-500:],
    }

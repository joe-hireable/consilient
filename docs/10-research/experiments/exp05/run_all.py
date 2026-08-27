"""
Run one ticket through every configured backend and print the comparison.

Run:  python run_all.py [backend ...]     (default: every backend that is ready)

Backends: claude · codex · cursor · cursor-acp · ollama:<model> · openrouter:<model> ·
          opencode+openrouter:<model>

This is the practical form of the meta-harness claim: one ticket, one outcome
schema, N execution paths. It is also EXP-05's instrument — every row that
fails, and every field that comes back None, is an interface finding.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_exp05 import GOAL, make_repo, verify

GIT = shutil.which("git")


def composition_for(name):
    """Map a requested shorthand to its explicit routing composition."""
    if name == "claude":
        return {
            "agent": "claude-code",
            "domain": "coding",
            "harness": "claude-code",
            "provider": "anthropic-first-party",
            "model": "unknown:not-recorded-by-adapter",
        }
    if name == "codex":
        return {
            "agent": "codex",
            "domain": "coding",
            "harness": "codex",
            "provider": "openai-subscription",
            "model": "unknown:not-recorded-by-adapter",
        }
    if name == "cursor":
        return {
            "agent": "cursor",
            "domain": "coding",
            "harness": "cursor",
            "provider": "cursor-subscription",
            "model": "unknown:not-recorded-by-adapter",
        }
    if name == "cursor-acp":
        return {
            "agent": "cursor-acp",
            "domain": "coding",
            "harness": "cursor",
            "provider": "cursor-subscription",
            "model": "unknown:not-recorded-by-adapter",
            "control_protocol": "acp-v1-stdio",
        }
    if name.startswith("ollama:"):
        model = name.split(":", 1)[1]
        return {
            "agent": f"codex+ollama:{model}",
            "domain": "coding",
            "harness": "codex",
            "provider": "ollama",
            "model": model,
        }
    if name.startswith("openrouter:"):
        model = name.split(":", 1)[1]
        return {
            "agent": f"codex+openrouter:{model}",
            "domain": "coding",
            "harness": "codex",
            "provider": "openrouter",
            "model": model,
        }
    if name.startswith("opencode+openrouter:"):
        model = name.split(":", 1)[1]
        return {
            "agent": f"opencode+openrouter:{model}",
            "domain": "coding",
            "harness": "opencode",
            "provider": "openrouter",
            "model": model,
        }
    if name.startswith("antigravity:"):
        model = name.split(":", 1)[1]
        return {
            "agent": f"antigravity:{model}",
            "domain": "coding",
            "harness": "antigravity",
            "provider": "google-account:plan-unverified",
            "model": model,
        }
    if name == "grok":
        return {
            "agent": "grok",
            "domain": "coding",
            "harness": "grok",
            "provider": "xai-subscription",
            "model": "unknown:not-recorded-by-adapter",
        }
    if name.startswith("grok:"):
        model = name.split(":", 1)[1]
        return {
            "agent": f"grok:{model}",
            "domain": "coding",
            "harness": "grok",
            "provider": "xai-subscription",
            "model": model,
        }
    return {
        "agent": name,
        "domain": "coding",
        "harness": "unknown:not-registered",
        "provider": "unknown:not-registered",
        "model": "unknown:not-registered",
    }


def merge_rows(existing, new):
    """Replace rerun backends while preserving comparison rows not selected."""
    merged = list(existing)
    positions = {row["agent"]: index for index, row in enumerate(merged)}
    for row in new:
        index = positions.get(row["agent"])
        if index is None:
            positions[row["agent"]] = len(merged)
            merged.append(row)
        else:
            merged[index] = row
    return merged


def claude_auth_ready(stdout, return_code):
    try:
        return return_code == 0 and json.loads(stdout).get("loggedIn") is True
    except json.JSONDecodeError:
        return False


def codex_auth_ready(stdout, return_code):
    return return_code == 0 and "Logged in using" in (stdout or "")


def cursor_auth_ready(stdout, return_code):
    return return_code == 0 and "Logged in as" in (stdout or "")


def grok_auth_ready(stdout, return_code):
    if return_code != 0 or not stdout:
        return False
    text = stdout.lower()
    return (
        "not authenticated" not in text
        and "not signed in" not in text
        and "grok login" not in text
    )


def available():
    have = []
    claude = shutil.which("claude")
    if claude:
        try:
            status = subprocess.run(
                [claude, "auth", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if claude_auth_ready(status.stdout, status.returncode):
                have.append("claude")
        except Exception:
            pass
    codex = shutil.which("codex")
    if codex:
        try:
            status = subprocess.run(
                [codex, "login", "status"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if codex_auth_ready(status.stdout, status.returncode):
                have.append("codex")
        except Exception:
            pass
        try:
            out = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=30
            ).stdout
            for line in out.splitlines()[1:]:
                if line.strip():
                    have.append("ollama:" + line.split()[0])
                    break
        except Exception:
            pass
        if os.environ.get("OPENROUTER_API_KEY"):
            have.append("openrouter:qwen/qwen3-coder")
    if shutil.which("wsl"):
        if os.environ.get("OPENROUTER_API_KEY"):
            try:
                opencode = subprocess.run(
                    [
                        "wsl",
                        "-d",
                        "Ubuntu",
                        "-e",
                        "/home/jpbpr/.opencode/bin/opencode",
                        "--version",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if opencode.returncode == 0:
                    have.append("opencode+openrouter:qwen/qwen3-coder")
            except Exception:
                pass
        r = subprocess.run(
            [
                "wsl",
                "-d",
                "Ubuntu",
                "-e",
                "bash",
                "-lc",
                "$HOME/.local/bin/cursor-agent status 2>&1 | head -1",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if cursor_auth_ready(r.stdout, r.returncode):
            have.append("cursor")
            have.append("cursor-acp")
    grok_cand = [
        shutil.which("grok.cmd"),
        shutil.which("grok.exe"),
        shutil.which("grok"),
        str(Path.home() / ".grok" / "bin" / "grok.exe"),
        str(Path.home() / ".grok" / "bin" / "grok"),
        "/mnt/c/Users/jpbpr/.grok/bin/grok.exe",
    ]
    for cand in grok_cand:
        if cand and (Path(cand).exists() or shutil.which(cand)):
            try:
                status = subprocess.run(
                    [cand, "models"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                if grok_auth_ready(status.stdout, status.returncode):
                    have.append("grok")
                break
            except Exception:
                pass
    return have


def run_one(name):
    repo = make_repo()
    ticket = {
        "id": f"smoke-{name}",
        "goal": GOAL,
        "repo_dir": str(repo),
        "timeout_s": 900,
    }
    t0 = time.time()
    try:
        if name == "claude":
            import adapter_claude_code as a

            out = a.run(ticket)
        elif name == "codex":
            import adapter_codex as a

            out = a.run(ticket)
        elif name == "cursor":
            import adapter_cursor as a

            out = a.run(ticket)
        elif name == "cursor-acp":
            import adapter_cursor_acp as a

            out = a.run(ticket)
        elif name.startswith("ollama:"):
            import adapter_model_backed as a

            out = a.run_local(ticket, name.split(":", 1)[1])
        elif name.startswith("openrouter:"):
            import adapter_model_backed as a

            out = a.run_openrouter(ticket, name.split(":", 1)[1])
        elif name.startswith("opencode+openrouter:"):
            import adapter_opencode as a

            out = a.run(ticket, name.split(":", 1)[1])
        elif name.startswith("antigravity:"):
            import adapter_antigravity as a

            out = a.run(ticket, name.split(":", 1)[1])
        elif name == "grok" or name.startswith("grok:"):
            import adapter_grok as a

            model = name.split(":", 1)[1] if ":" in name else None
            out = a.run(ticket, model=model)
        else:
            raise ValueError(name)
    except Exception as e:
        out = {
            **composition_for(name),
            "ok": False,
            "diff": "",
            "duration_s": round(time.time() - t0, 1),
            "raw_tail": f"ADAPTER ERROR: {type(e).__name__}: {e}"[:400],
            "tokens_in": None,
            "tokens_out": None,
            "cost_usd": None,
        }
    out["verifier"] = verify(repo)
    out["repo"] = str(repo)
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or available()
    print(f"backends: {names}\n")
    rows = []
    for n in names:
        print(f"--- {n} ---", flush=True)
        r = run_one(n)
        rows.append(r)
        print(
            f"    ok={r['ok']} verifier={r['verifier']['passed']} "
            f"{r['duration_s']}s tok_in={r['tokens_in']} "
            f"cost={r['cost_usd']}",
            flush=True,
        )
        if not r["ok"]:
            print(f"    tail: {r['raw_tail'][:200]}", flush=True)

    print("\n" + "=" * 78)
    print(
        f"{'backend':28s} {'ok':>5} {'verified':>9} {'secs':>7} "
        f"{'tok_in':>9} {'cost':>8}"
    )
    print("-" * 78)
    for r in rows:
        print(
            f"{r['agent'][:28]:28s} {str(r['ok']):>5} "
            f"{str(r['verifier']['passed']):>9} {r['duration_s']:>7} "
            f"{str(r['tokens_in']):>9} {str(r['cost_usd']):>8}"
        )
    out = Path(__file__).parent / "backend-comparison.json"
    try:
        existing = json.loads(out.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []
    serialised = [{k: v for k, v in r.items() if k != "diff"} for r in rows]
    out.write_text(
        json.dumps(merge_rows(existing, serialised), indent=1),
        encoding="utf-8",
    )
    print(f"\nupdated: {out.name}")

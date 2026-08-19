"""
Run one ticket through every configured backend and print the comparison.

Run:  python run_all.py [backend ...]     (default: every backend that is ready)

Backends: claude · codex · cursor · ollama:<model> · openrouter:<model>

This is the practical form of the meta-harness claim: one ticket, one outcome
schema, N execution paths. It is also EXP-05's instrument — every row that
fails, and every field that comes back None, is an interface finding.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_exp05 import GOAL, make_repo, verify  # noqa: E402

GIT = shutil.which("git")


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


def available():
    have = []
    if shutil.which("claude"):
        have.append("claude")
    if shutil.which("codex"):
        have.append("codex")
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
        import os

        if os.environ.get("OPENROUTER_API_KEY"):
            have.append("openrouter:qwen/qwen3-coder")
    if shutil.which("wsl"):
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
        if "Not logged in" not in (r.stdout or ""):
            have.append("cursor")
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
        elif name.startswith("ollama:"):
            import adapter_model_backed as a

            out = a.run_local(ticket, name.split(":", 1)[1])
        elif name.startswith("openrouter:"):
            import adapter_model_backed as a

            out = a.run_openrouter(ticket, name.split(":", 1)[1])
        else:
            raise ValueError(name)
    except Exception as e:
        out = {
            "agent": name,
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

"""
EXP-01: estimate beta = P(checks accepted | artifact was bad) from repo history.

Run:  python mine_beta.py <owner/repo> <local_clone_path> [--days 14] [--limit 300]

Route: mine RECORDED CI verdicts (statusCheckRollup at merge) rather than replay
checks — the verdicts already ran historically; replay is the expensive fallback
for PRs with no recorded checks. Fetch is paged per-PR (a single GraphQL query
for 300 PRs x files x rollup 504s — measured 19 Aug 2026).

Labels (proxy, per ADR-0002; noise measured by the 30-PR manual sample):
  BAD if merged PR was (a) reverted (a later commit message reverts it by PR
  number or merge sha), or (b) hot-fixed: a later merged PR within --days whose
  changed files overlap this PR's files and whose title matches fix-ish patterns.
  GOOD otherwise (survived the window untouched).

Outputs:
  data/<repo>-prs.json   full per-PR record — PRIVATE, gitignored, never committed
  stdout                 aggregate beta-hat with Wilson 95% interval — the only
                         thing that may appear in docs (privacy rule, AGENTS.md)
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

FIX_RE = re.compile(r"\b(fix|hotfix|bug|regress|revert|broke|repair)\b", re.I)


def gh(args, retries=3):
    for attempt in range(retries):
        p = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, encoding="utf-8", timeout=180
        )
        if p.returncode == 0:
            return json.loads(p.stdout) if p.stdout.strip() else None
        if attempt < retries - 1:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(p.stderr[:300])


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main(repo, clone, days=14, limit=300):
    print(f"[exp01] listing merged PRs for {repo} ...", flush=True)
    prs = gh(
        [
            "pr",
            "list",
            "-R",
            repo,
            "--state",
            "merged",
            "--limit",
            str(limit),
            "--json",
            "number,title,mergedAt,mergeCommit",
        ]
    )
    prs.sort(key=lambda p: p["mergedAt"])
    print(
        f"[exp01] {len(prs)} merged PRs; fetching files+checks per PR ...", flush=True
    )

    for i, p in enumerate(prs):
        detail = gh(
            [
                "pr",
                "view",
                str(p["number"]),
                "-R",
                repo,
                "--json",
                "files,statusCheckRollup",
            ]
        )
        p["_files"] = {f["path"] for f in (detail.get("files") or [])}
        roll = detail.get("statusCheckRollup") or []
        states = {c.get("conclusion") or c.get("state") for c in roll}
        p["_ci"] = (
            "none"
            if not roll
            else "green"
            if states <= {"SUCCESS", "NEUTRAL", "SKIPPED", None}
            else "red"
        )
        if (i + 1) % 25 == 0:
            print(f"[exp01]   {i + 1}/{len(prs)}", flush=True)

    # revert detection from the local clone (no API cost)
    log = subprocess.run(
        ["git", "log", "--pretty=%H %s"],
        cwd=clone,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    revert_lines = [l for l in log if re.search(r"\brevert", l, re.I)]

    n_bad = 0
    for i, p in enumerate(prs):
        sha = (p.get("mergeCommit") or {}).get("oid", "")
        reverted = any(
            f"#{p['number']}" in l or (sha and sha[:8] in l) for l in revert_lines
        )
        hotfixed = False
        if not reverted:
            t0 = p["mergedAt"]
            for q in prs[i + 1 :]:
                dt = (
                    time.mktime(time.strptime(q["mergedAt"][:19], "%Y-%m-%dT%H:%M:%S"))
                    - time.mktime(time.strptime(t0[:19], "%Y-%m-%dT%H:%M:%S"))
                ) / 86400
                if dt > days:
                    break
                if FIX_RE.search(q["title"]) and p["_files"] & q["_files"]:
                    hotfixed = True
                    p["_fixer"] = q["number"]
                    break
        p["_bad"] = reverted or hotfixed
        p["_why"] = "reverted" if reverted else ("hotfixed" if hotfixed else "clean")
        n_bad += p["_bad"]

    accepted = [p for p in prs if p["_ci"] == "green"]
    bad_acc = [p for p in accepted if p["_bad"]]
    k, n = len(bad_acc), len(accepted)
    lo, hi = wilson(k, n)
    no_ci = sum(1 for p in prs if p["_ci"] == "none")

    out = Path(__file__).parent / "data"
    out.mkdir(exist_ok=True)
    safe = repo.split("/")[-1]
    (out / f"{safe}-prs.json").write_text(
        json.dumps(prs, indent=1, default=list), encoding="utf-8"
    )

    print(f"\n[exp01] {repo} AGGREGATES (the only publishable numbers):")
    print(f"  merged PRs analysed:        {len(prs)}")
    print(f"  CI green at merge:          {n}")
    print(f"  CI red-but-merged:          {sum(1 for p in prs if p['_ci'] == 'red')}")
    print(f"  no recorded checks:         {no_ci}")
    print(
        f"  bad outcomes (all):         {n_bad} "
        f"({sum(1 for p in prs if p['_why'] == 'reverted')} reverted / "
        f"{sum(1 for p in prs if p['_why'] == 'hotfixed')} hotfixed)"
    )
    print(f"  beta-hat = P(bad | green):  {k}/{n} = {k / n if n else float('nan'):.4f}")
    print(f"  Wilson 95%:                 [{lo:.4f}, {hi:.4f}]")
    print(f"  per-PR record: data/{safe}-prs.json (PRIVATE, gitignored)")


if __name__ == "__main__":
    repo, clone = sys.argv[1], sys.argv[2]
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 14
    limit = (
        int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 300
    )
    main(repo, clone, days, limit)

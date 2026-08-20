"""Where two blind adjudicators disagree — the only judgements worth Joe's attention.

Two model families adjudicated the same 75 bad-and-red PRs without seeing each other's work.
Their corrected beta agreed to within 0.0085 while their underlying labels differed by 16 PRs,
and `beta_convergence.py` shows that agreement is 14x narrower than the input disagreement
warrants. So beta's real interval is [0.81, 0.93], and what closes it is not more model
adjudication — it is the one person who actually remembers these changes.

He does not need to judge 75. Where both families agree, a third opinion buys almost nothing:
that is Howard's expected value of clairvoyance, which ADR-0033 already adopts as the test for
whether asking is rational at all. **Ask only where they diverge.**

This prints the disagreement set, smallest first, with the evidence pre-digested to what a
human needs to answer in one glance. Aggregate counts to stdout; the per-PR queue is written to
the gitignored data directory because it carries private-corpus detail.

Run: python disagreements.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
GPT = DATA / "bad-and-red-audit.json"
GEM = DATA / "badred-cursor.json"
OUT = DATA / "verdict-queue.json"


def load(path: Path) -> dict[int, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("records", raw if isinstance(raw, list) else [])
    return {r["number"]: r for r in records if isinstance(r, dict) and "number" in r}


def norm(v: object) -> str:
    if v is True:
        return "yes"
    if v is False:
        return "no"
    return "unclear"


def main() -> None:
    for p in (GPT, GEM):
        if not p.exists():
            raise SystemExit(f"missing {p.name}")

    gpt, gem = load(GPT), load(GEM)
    evidence = {
        r["number"]: r
        for r in json.loads(
            (DATA / "red-cells-evidence.json").read_text(encoding="utf-8")
        )
    }

    shared = sorted(set(gpt) & set(gem))
    print(
        f"gpt-5.6 records {len(gpt)} | gemini-3.7 records {len(gem)} | shared {len(shared)}"
    )

    agree_bad = disagree_bad = 0
    agree_red = disagree_red = 0
    queue: list[dict] = []

    for n in shared:
        a, b = gpt[n], gem[n]
        ab, bb = norm(a.get("bad_label_correct")), norm(b.get("bad_label_correct"))
        ar, br = norm(a.get("red_meaningful")), norm(b.get("red_meaningful"))

        bad_split = ab != bb
        red_split = ar != br
        agree_bad += not bad_split
        disagree_bad += bad_split
        agree_red += not red_split
        disagree_red += red_split

        if not (bad_split or red_split):
            continue

        ev = evidence.get(n, {})
        fixer = ev.get("fixer") or {}
        queue.append(
            {
                "number": n,
                "asks": (["was_it_really_broken"] if bad_split else [])
                + (["did_the_check_really_reject"] if red_split else []),
                "n_files": ev.get("n_files"),
                "overlap_files": len(fixer.get("overlap") or []),
                "days_to_fixer": None,
                "gpt": {"bad": ab, "red": ar, "why_bad": a.get("bad_reason", "")[:90]},
                "gemini": {
                    "bad": bb,
                    "red": br,
                    "why_bad": b.get("bad_reason", "")[:90],
                },
                "title": ev.get("title", ""),
                "fixer_title": fixer.get("title", ""),
                "failing_checks": [
                    c["name"]
                    for c in ev.get("checks", [])
                    if c.get("conclusion")
                    not in ("SUCCESS", "NEUTRAL", "SKIPPED", None)
                ],
            }
        )

    # Cheapest first: a small PR with a small overlap is decidable in seconds.
    queue.sort(key=lambda q: ((q["overlap_files"] or 99), (q["n_files"] or 99)))

    print(f"\n  bad label   agree {agree_bad:>3}   disagree {disagree_bad:>3}")
    print(f"  red meaning agree {agree_red:>3}   disagree {disagree_red:>3}")
    print(f"\n  PRs needing a human verdict: {len(queue)} of {len(shared)}")
    print(
        f"  of those, {sum(1 for q in queue if len(q['asks']) == 2)} need both questions"
    )

    only_bad = sum(1 for q in queue if q["asks"] == ["was_it_really_broken"])
    only_red = sum(1 for q in queue if q["asks"] == ["did_the_check_really_reject"])
    print(f"  {only_bad} need only 'was it really broken?'")
    print(f"  {only_red} need only 'did the check really reject it?'")

    OUT.write_text(json.dumps(queue, indent=1), encoding="utf-8")
    print(f"\n  queue written to data/{OUT.name} (gitignored — carries private detail)")
    print(
        f"  at 15 seconds a judgement that is about "
        f"{round(sum(len(q['asks']) for q in queue) * 15 / 60)} minutes of attention,\n"
        f"  against 75 PRs x 2 questions = {round(75 * 2 * 15 / 60)} minutes for the full cell."
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Independent replication script for EXP-01 claims and cross-family audit reconciliation.
Derived directly from primary data records without running prior analysis scripts.
"""

import json
import math
import statistics
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

def wilson_score_interval(k: int, n: int, confidence: float = 0.95):
    if n == 0:
        return (0.0, 1.0)
    # z for 95% = 1.959963984540054
    # Note: 1.96 standard approximation
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / n) + ((z ** 2) / (4 * (n ** 2))))
    return (max(0.0, center - margin), min(1.0, center + margin))

def wilson_196(k: int, n: int):
    # Using exact z=1.96 as in mine_beta.py
    if n == 0:
        return (0.0, 1.0)
    z = 1.96
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))

def load_data(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        # Fallback to base repo data if not in worktree
        path = Path("/mnt/c/Users/jpbpr/Repositories/consilience/docs/10-research/experiments/exp01/data") / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_replication():
    print("=" * 70)
    print("INDEPENDENT REPLICATION OF EXP-01 PRIMARY RECORDS")
    print("=" * 70)

    jb = load_data("jobboard-v2-prs.json")
    hp = load_data("hireable-platform-prs.json")
    red_evidence = load_data("red-cells-evidence.json")

    # -------------------------------------------------------------
    # 1. Inspect datasets and contingency tables
    # -------------------------------------------------------------
    for name, ds in [("jobboard-v2", jb), ("hireable-platform", hp)]:
        print(f"\n--- DATASET: {name} (Total PRs: {len(ds)}) ---")
        
        # Breakdown by _bad and _ci
        counts = {}
        for p in ds:
            bad = p.get("_bad")
            ci = p.get("_ci")
            counts[(bad, ci)] = counts.get((bad, ci), 0) + 1
        
        print("Contingency grid (bad, ci):")
        for bad in [False, True]:
            for ci in ["green", "red", "none"]:
                print(f"  bad={bad:<5} ci={ci:<5}: {counts.get((bad, ci), 0)}")
        
        # Total bad / good
        n_bad = sum(1 for p in ds if p.get("_bad"))
        n_good = sum(1 for p in ds if not p.get("_bad"))
        
        # Total by CI
        n_green = sum(1 for p in ds if p.get("_ci") == "green")
        n_red = sum(1 for p in ds if p.get("_ci") == "red")
        n_none = sum(1 for p in ds if p.get("_ci") == "none")
        
        print(f"Totals: Good={n_good}, Bad={n_bad} | Green={n_green}, Red={n_red}, None={n_none}")

        # Claim 1: Alpha = P(verifier rejects | artefact good)
        # Rejection = red. Good = bad is False.
        # Treatment A: Excluding _ci == 'none' from denominator (only PRs with verdict)
        good_red = counts.get((False, "red"), 0)
        good_green = counts.get((False, "green"), 0)
        good_none = counts.get((False, "none"), 0)
        
        denom_verdicts_only = good_green + good_red
        denom_all_good = good_green + good_red + good_none
        
        alpha_verdicts = good_red / denom_verdicts_only if denom_verdicts_only else 0
        w_verdicts = wilson_196(good_red, denom_verdicts_only)
        
        alpha_all = good_red / denom_all_good if denom_all_good else 0
        w_all = wilson_196(good_red, denom_all_good)

        print("\nCLAIM 1 (Alpha):")
        print(f"  Good & Red = {good_red}, Good & Green = {good_green}, Good & None = {good_none}")
        print(f"  Treatment A (Verdict only, excl none): {good_red}/{denom_verdicts_only} = {alpha_verdicts:.4f} {list(w_verdicts)}")
        print(f"  Treatment B (All good, incl none in denom): {good_red}/{denom_all_good} = {alpha_all:.4f} {list(w_all)}")

        # Claim 2: Bad labels source (_why)
        whys = {}
        for p in ds:
            if p.get("_bad"):
                whys[p.get("_why")] = whys.get(p.get("_why"), 0) + 1
        print("\nCLAIM 2 (Bad labels proxy decomposition):")
        print(f"  Total bad = {n_bad}")
        print(f"  Breakdown by _why: {whys}")
        print(f"  Reverted count: {whys.get('reverted', 0)}, Hotfixed count: {whys.get('hotfixed', 0)}")

        # Claim 3: File counts distribution (bad-and-red vs bad-and-green)
        bad_red_files = [len(p.get("_files", [])) for p in ds if p.get("_bad") and p.get("_ci") == "red"]
        bad_green_files = [len(p.get("_files", [])) for p in ds if p.get("_bad") and p.get("_ci") == "green"]
        
        med_bad_red = statistics.median(bad_red_files) if bad_red_files else 0
        mean_bad_red = statistics.mean(bad_red_files) if bad_red_files else 0
        med_bad_green = statistics.median(bad_green_files) if bad_green_files else 0
        mean_bad_green = statistics.mean(bad_green_files) if bad_green_files else 0
        ratio_med = med_bad_red / med_bad_green if med_bad_green else 0
        
        print("\nCLAIM 3 (File counts):")
        print(f"  Bad & Red count: {len(bad_red_files)}, Median files: {med_bad_red}, Mean: {mean_bad_red:.2f}")
        print(f"  Bad & Green count: {len(bad_green_files)}, Median files: {med_bad_green}, Mean: {mean_bad_green:.2f}")
        print(f"  Median ratio (Red/Green): {ratio_med:.2f}")

    # -------------------------------------------------------------
    # 4. Red cells evidence and Cancelled CI runs
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CLAIM 4 & ADJUDICATION OF RED CELLS EVIDENCE")
    print("=" * 70)
    
    print(f"Total entries in red-cells-evidence.json: {len(red_evidence)}")
    
    # Check structure of red-cells-evidence
    # Check if entries correspond to jobboard-v2 (or also hireable-platform)
    # Let's see PR numbers, conclusions, etc.
    
    bad_red_prs = [p for p in jb if p.get("_bad") and p.get("_ci") == "red"]
    good_red_prs = [p for p in jb if not p.get("_bad") and p.get("_ci") == "red"]
    
    print(f"jobboard-v2 Bad & Red PR count: {len(bad_red_prs)}")
    print(f"jobboard-v2 Good & Red PR count: {len(good_red_prs)}")
    print(f"Sum of jobboard-v2 Red PRs: {len(bad_red_prs) + len(good_red_prs)}")

    # Analyze failure reasons for red cells
    # A PR is "cancelled-only" if every failed check has conclusion == "CANCELLED" (and no check has FAILURE/TIMED_OUT/ACTION_REQUIRED etc)
    
    red_by_pr = {}
    for entry in red_evidence:
        pr_num = entry["number"]
        red_by_pr[pr_num] = entry
        
    print(f"Entries in red_evidence mapped: {len(red_by_pr)}")
    
    # Classify each red PR
    def classify_red_pr(entry):
        # checks rollup
        checks = entry.get("checks", [])
        # Look at conclusions of failed checks
        failed_conclusions = set()
        has_failure = False
        has_cancelled = False
        has_timed_out = False
        
        for c in checks:
            conc = c.get("conclusion")
            state = c.get("state")
            status = conc or state
            if status not in ("SUCCESS", "NEUTRAL", "SKIPPED", None):
                failed_conclusions.add(status)
                if status == "CANCELLED":
                    has_cancelled = True
                elif status in ("FAILURE", "FAILED"):
                    has_failure = True
                elif status in ("TIMED_OUT", "TIME_OUT"):
                    has_timed_out = True
                else:
                    has_failure = True
        
        # Is it cancelled only?
        cancelled_only = (failed_conclusions == {"CANCELLED"})
        return {
            "failed_conclusions": failed_conclusions,
            "cancelled_only": cancelled_only,
            "has_failure": has_failure,
            "has_cancelled": has_cancelled,
            "has_timed_out": has_timed_out
        }

    bad_red_cancelled_only = []
    bad_red_other = []
    for p in bad_red_prs:
        num = p["number"]
        if num in red_by_pr:
            res = classify_red_pr(red_by_pr[num])
            if res["cancelled_only"]:
                bad_red_cancelled_only.append(num)
            else:
                bad_red_other.append(num)
        else:
            print(f"Warning: Bad & Red PR {num} not in red-cells-evidence")

    good_red_cancelled_only = []
    good_red_other = []
    for p in good_red_prs:
        num = p["number"]
        if num in red_by_pr:
            res = classify_red_pr(red_by_pr[num])
            if res["cancelled_only"]:
                good_red_cancelled_only.append(num)
            else:
                good_red_other.append(num)
        else:
            print(f"Warning: Good & Red PR {num} not in red-cells-evidence")

    print("\nClaim 4 Breakdown:")
    print(f"  Bad & Red: Total={len(bad_red_prs)}, Cancelled-only={len(bad_red_cancelled_only)}, Other-failed={len(bad_red_other)}")
    print(f"    Cancelled-only bad PRs: {bad_red_cancelled_only}")
    print(f"  Good & Red: Total={len(good_red_prs)}, Cancelled-only={len(good_red_cancelled_only)}, Other-failed={len(good_red_other)}")
    print(f"    Cancelled-only good PRs: {good_red_cancelled_only}")

    # Beta before and after removing cancelled-only
    # Baseline beta:
    # On jobboard-v2:
    # Accepted = CI green = 203 bad_green + 74 good_green = 277 (wait, let's check counts)
    # Beta = bad_green / green_total
    
    bad_green = sum(1 for p in jb if p.get("_bad") and p.get("_ci") == "green")
    good_green = sum(1 for p in jb if not p.get("_bad") and p.get("_ci") == "green")
    total_green = bad_green + good_green
    beta_base = bad_green / total_green
    
    print("\nBaseline Beta & Alpha on jobboard-v2:")
    print(f"  Bad & Green: {bad_green}, Good & Green: {good_green}, Total Green: {total_green}")
    print(f"  Baseline Beta = {bad_green}/{total_green} = {beta_base:.4f} {list(wilson_196(bad_green, total_green))}")
    
    alpha_base = len(good_red_prs) / (len(good_red_prs) + good_green)
    print(f"  Baseline Alpha = {len(good_red_prs)}/({len(good_red_prs)}+{good_green}) = {alpha_base:.4f} {list(wilson_196(len(good_red_prs), len(good_red_prs) + good_green))}")

    # If cancelled-only is treated as "no verdict" (removed from red, not counted as reject):
    # What happens to Beta and Alpha?
    # Wait, how does removing cancelled runs affect Beta?
    # Does removing cancelled runs change Green?
    # Wait! If cancelled runs were in RED, removing them from red doesn't change GREEN directly unless the definition of Beta is P(accepted | bad).
    # Let's check: P(accepted | bad) = bad_green / (bad_green + bad_red) !
    # In classic verifier terms:
    # Verifier True Positive = verifier rejects bad artefact = bad_red.
    # Verifier False Negative = verifier accepts bad artefact = bad_green.
    # So P(verifier accepts | bad) = bad_green / (bad_green + bad_red)!
    # Let's check this calculation:
    # Baseline: bad_green = 128 (let's see what bad_green is!), bad_red = 75.
    # Total bad with verdicts = 128 + 75 = 203.
    # 128 / 203 = 0.6305418... = 0.6305!
    # If 15 cancelled bad_red are removed: bad_red becomes 75 - 15 = 60.
    # Total bad with verdicts = 128 + 60 = 188.
    # Beta = 128 / 188 = 0.680851... = 0.6809!
    # And for Alpha:
    # Baseline good_red = 23, good_green = 74. Total good with verdicts = 23 + 74 = 97.
    # Alpha = 23 / 97 = 0.23711... = 0.2371!
    # If 3 cancelled good_red are removed: good_red becomes 23 - 3 = 20.
    # Total good with verdicts = 20 + 74 = 94.
    # Alpha = 20 / 94 = 0.212765... = 0.2128!
    
    print("\nVerification of Claim 4 arithmetic:")
    print("  P(accept | bad) = bad_green / (bad_green + bad_red)")
    print(f"  Baseline: {bad_green} / ({bad_green} + {len(bad_red_prs)}) = {bad_green / (bad_green + len(bad_red_prs)):.4f}")
    print(f"  Post-removal of 15 cancelled bad: {bad_green} / ({bad_green} + {len(bad_red_prs) - 15}) = {bad_green / (bad_green + len(bad_red_prs) - 15):.4f}")
    print("  P(reject | good) = good_red / (good_red + good_green)")
    print(f"  Baseline: {len(good_red_prs)} / ({len(good_red_prs)} + {good_green}) = {len(good_red_prs) / (len(good_red_prs) + good_green):.4f}")
    print(f"  Post-removal of 3 cancelled good: ({len(good_red_prs)} - 3) / ({len(good_red_prs)} - 3 + {good_green}) = {(len(good_red_prs) - 3) / (len(good_red_prs) - 3 + good_green):.4f}")

    # -------------------------------------------------------------
    # 5. Codex Audit Analysis & Cross-Family Reconciliation
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("CODEX AUDIT RECONCILIATION")
    print("=" * 70)
    
    codex_removed = [397, 399, 400, 465, 505, 512, 517, 518, 525]
    codex_unclear = [407, 411, 416]
    cancelled_3 = good_red_cancelled_only

    print(f"Codex 9 removed PRs: {sorted(codex_removed)}")
    print(f"Cancelled-only 3 good-and-red PRs: {sorted(cancelled_3)}")
    print(f"Codex 3 unclear PRs: {sorted(codex_unclear)}")
    
    overlap = set(codex_removed) & set(cancelled_3)
    print(f"\nOverlap between Codex 9 and Cancelled 3: {sorted(list(overlap))}")
    print(f"Cancelled 3 NOT in Codex 9: {sorted(list(set(cancelled_3) - set(codex_removed)))}")
    print(f"Codex 9 NOT in Cancelled 3: {sorted(list(set(codex_removed) - set(cancelled_3)))}")

    # Let's inspect each of the 23 good-and-red PRs in detail:
    print(f"\nDetailed inspection of all {len(good_red_prs)} Good & Red PRs:")
    for p in good_red_prs:
        num = p["number"]
        entry = red_by_pr.get(num, {})
        checks = entry.get("checks", [])
        
        # summary of checks
        check_summary = []
        for c in checks:
            status = c.get("conclusion") or c.get("state")
            if status not in ("SUCCESS", "NEUTRAL", "SKIPPED", None):
                check_summary.append((c.get("name", "unknown"), status))
        
        in_codex_rem = num in codex_removed
        in_codex_unc = num in codex_unclear
        is_canc = num in cancelled_3
        
        print(f"  PR #{num}: checks_failed={len(check_summary)} {check_summary[:3]} | is_cancelled={is_canc} | in_codex_removed={in_codex_rem} | in_codex_unclear={in_codex_unc}")

    # Reconciled contingency tables under various treatments
    print("\n" + "-" * 70)
    print("RECONCILED CONTINGENCY TABLES & ALPHA CALCULATIONS")
    print("-" * 70)

    # All good PRs on jobboard-v2:
    # Total = 97 (74 green, 23 red, 0 none)
    # Let's verify total good PRs on jobboard-v2:
    good_prs = [p for p in jb if not p.get("_bad")]
    print(f"Total good PRs: {len(good_prs)}")
    
    # What are the candidate treatments?
    # Let's analyze:
    # 1. Baseline: 23 red / 97 good = 0.2371
    # 2. Opus Cancelled-Removal (remove 3 cancelled as no-verdict from both num & denom):
    #    red = 20, green = 74, total = 94 -> 20/94 = 0.2128
    # 3. Codex Audit (remove 9 non-meaningful from num, but keep in denom):
    #    red = 14, green = 74, non_meaningful_in_denom = 9 -> 14/97 = 0.1443
    # 4. Codex Audit (remove 9 non-meaningful from BOTH num & denom):
    #    red = 14, green = 74, total = 88 -> 14/88 = 0.1591
    # 5. Combined / Reconciled:
    #    Union of (Cancelled 3) and (Codex 9):
    union_removals = set(codex_removed) | set(cancelled_3)
    print(f"\nUnion of Codex 9 and Cancelled 3: {sorted(list(union_removals))} (Total: {len(union_removals)})")
    
    # Remaining legitimate red rejections if union removed:
    rem_red_union = len(good_red_prs) - len(union_removals)
    print(f"Remaining good-and-red after union removal: {rem_red_union} (out of 23)")
    
    # Treatment A: Union removed from numerator only (kept in denominator as non-rejections / good artifacts evaluated)
    alpha_union_num_only = rem_red_union / 97
    w_union_num = wilson_196(rem_red_union, 97)
    print(f"Treatment (Union removed from numerator only, N=97): {rem_red_union}/97 = {alpha_union_num_only:.4f} {list(w_union_num)}")
    
    # Treatment B: Union removed from BOTH numerator and denominator (treated as uninformative/no-verdict)
    denom_union = 97 - len(union_removals)
    alpha_union_both = rem_red_union / denom_union
    w_union_both = wilson_196(rem_red_union, denom_union)
    print(f"Treatment (Union removed from BOTH num & denom, N={denom_union}): {rem_red_union}/{denom_union} = {alpha_union_both:.4f} {list(w_union_both)}")

    # What if Codex unclear (3 PRs) are also removed?
    union_plus_unclear = union_removals | set(codex_unclear)
    rem_red_strict = len(good_red_prs) - len(union_plus_unclear)
    print(f"\nIf Codex 3 unclear are also removed (Total excluded: {len(union_plus_unclear)}):")
    print(f"  Remaining red: {rem_red_strict}")
    print(f"  Num only (N=97): {rem_red_strict}/97 = {rem_red_strict/97:.4f} {list(wilson_196(rem_red_strict, 97))}")
    print(f"  Both num & denom (N={97-len(union_plus_unclear)}): {rem_red_strict}/{97-len(union_plus_unclear)} = {rem_red_strict/(97-len(union_plus_unclear)):.4f} {list(wilson_196(rem_red_strict, 97-len(union_plus_unclear)))}")

if __name__ == "__main__":
    run_replication()

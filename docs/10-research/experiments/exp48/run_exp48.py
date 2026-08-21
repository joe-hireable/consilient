"""EXP-48: Systematic Cross-Reference of Mutation Survivors vs P2 Guard Catalogue.

Executes deterministic cross-referencing between:
1. P2's 25 hand-catalogued defective guards (+1 control C1) in docs/50-publications/P2-guards.md
2. EXP-47's 586 true surviving mutants and 61 survivor clusters from docs/10-research/experiments/exp47/results-exp47.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

P2_CATALOGUE = [
    # Class A: Structurally inert (13)
    {
        "id": "A1",
        "class": "A",
        "description": "ADR-0015 Gate A2: cmd_replay built projection twice and compared rebuilds (unlink destroyed drift)",
        "layer": "code",
        "file": "src/consilient/cli.py",
        "functions": ["cmd_replay"],
        "lines": (80, 133),
        "other_file": "src/consilient/projection.py",
        "other_lines": (63, 75),
    },
    {
        "id": "A2",
        "class": "A",
        "description": "ADR-0015 Gate B2: n_max ceiling formula floor is 3.125 > 1 for all beta",
        "layer": "governance_adr",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A3",
        "class": "A",
        "description": "V0-18: _check_human_authority early return on missing human_decision while _apply_outcome read human_verdict",
        "layer": "code",
        "file": "src/consilient/events.py",
        "functions": ["_check_human_authority"],
        "lines": (223, 275),
        "other_file": "src/consilient/projection.py",
        "other_lines": (141, 145),
    },
    {
        "id": "A4",
        "class": "A",
        "description": "Beta.__post_init__: measured beta constructed with 0 rejections, inverted interval, or lower floor",
        "layer": "code",
        "file": "src/consilient/beta.py",
        "functions": ["Beta.__post_init__", "compute"],
        "lines": (64, 118),
        "other_file": "src/consilient/beta.py",
        "other_lines": (189, 194),
    },
    {
        "id": "A5",
        "class": "A",
        "description": "lower_bound_on_joint_error = True hardcoded dataclass default asserted by test",
        "layer": "code",
        "file": "src/consilient/beta.py",
        "functions": ["Beta"],
        "lines": (58, 62),
    },
    {
        "id": "A6",
        "class": "A",
        "description": "Event schema ts format checked RFC3339 format/offset but never verified true timestamp against clock",
        "layer": "code",
        "file": "src/consilient/events.py",
        "functions": ["validate", "_check_clock", "append"],
        "lines": (111, 115),
        "other_file": "src/consilient/events.py",
        "other_lines": (284, 306),
    },
    {
        "id": "A7",
        "class": "A",
        "description": "AGENTS.md private corpus publication rule declared in governance with no check",
        "layer": "governance_rule",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A8",
        "class": "A",
        "description": "V0-26: _check_evidence_class returns early whenever contributors is absent (opt-in invariant)",
        "layer": "code",
        "file": "src/consilient/events.py",
        "functions": ["_check_evidence_class"],
        "lines": (130, 173),
    },
    {
        "id": "A9",
        "class": "A",
        "description": "ADR-0014 / skills-mirror.yml symlink assertion passes on Linux CI where checkout creates it, false on Windows",
        "layer": "ci_workflow",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A10",
        "class": "A",
        "description": "ADR-0023 gate-bypass-log.md empty because audited process (PRs) never occurred",
        "layer": "governance_log",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A11",
        "class": "A",
        "description": "MIN_REJECTIONS = 30 floor: Wilson interval at 0/30 (0.11352) cannot clear beta* = 0.111",
        "layer": "code",
        "file": "src/consilient/beta.py",
        "functions": ["MIN_REJECTIONS"],
        "lines": (38, 38),
    },
    {
        "id": "A13",
        "class": "A",
        "description": "mypy --strict claimed clean in docs, but CI ran weaker non-strict mypy.ini",
        "layer": "ci_workflow",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A14",
        "class": "A",
        "description": "append() documented as sole trajectory writer, but 92 of 93 events bypassed it directly",
        "layer": "code",
        "file": "src/consilient/events.py",
        "functions": ["append", "validate"],
        "lines": (309, 340),
    },
    # Class A': Inverse (2)
    {
        "id": "A12",
        "class": "A'",
        "description": "V0-02/ADR-0006 byte-identical SQLite state impossible due to SQLite header/freelist non-determinism",
        "layer": "spec_adr_text",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "A15",
        "class": "A'",
        "description": "ADR-0015 Gate B4 requires 20 tickets on external repo before Stage 3, but Stage 3 forbidden before Gate B",
        "layer": "spec_adr_text",
        "file": None,
        "functions": [],
        "lines": None,
    },
    # Class B: Uninformative pass (10)
    {
        "id": "B1",
        "class": "B",
        "description": "Heartbeat inferred running from frozen byte count of stopped process",
        "layer": "research_harness",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B2",
        "class": "B",
        "description": "subprocess.run(timeout=T) failed to kill surviving grandchild processes holding pipes",
        "layer": "research_harness",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B3",
        "class": "B",
        "description": "Single-instance lock release_lock() deleted lock it never held",
        "layer": "research_harness",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B4",
        "class": "B",
        "description": "No duplicate cells check in experiment runner rewriting whole file per checkpoint",
        "layer": "research_harness",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B5",
        "class": "B",
        "description": "CI red in retrospective mining counted CANCELLED runs and informational checks as rejections",
        "layer": "research_script",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B6",
        "class": "B",
        "description": "Revert arm of label detector fired 0 times because repos were fix-forward",
        "layer": "research_script",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B7",
        "class": "B",
        "description": "ADR-0002 false-safe rate is 0 transcribed from ~0",
        "layer": "governance_adr",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B8",
        "class": "B",
        "description": "Blind grader flat summary tally under balanced randomized arms",
        "layer": "research_protocol",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B9",
        "class": "B",
        "description": "Gate script piped into tail which discarded non-zero exit code",
        "layer": "shell_pipeline",
        "file": None,
        "functions": [],
        "lines": None,
    },
    {
        "id": "B10",
        "class": "B",
        "description": "External PM projection accepted invalid state without error",
        "layer": "external_service",
        "file": None,
        "functions": [],
        "lines": None,
    },
    # Class C: Positive Control (1)
    {
        "id": "C1",
        "class": "C",
        "description": "Parent-commit baseline in forward test replay preventing drift from inflating beta",
        "layer": "research_method",
        "file": None,
        "functions": [],
        "lines": None,
    },
]


def cluster_mutants(mutants: list[dict[str, Any]], max_gap: int = 5) -> list[dict[str, Any]]:
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in mutants:
        by_file[m["file"]].append(m)

    clusters: list[dict[str, Any]] = []
    cluster_id = 1
    for file_path, file_mutants in sorted(by_file.items()):
        sorted_m = sorted(file_mutants, key=lambda x: x["line"])
        current_cluster: list[dict[str, Any]] = []
        for m in sorted_m:
            if not current_cluster:
                current_cluster.append(m)
            else:
                last_line = current_cluster[-1]["line"]
                if m["line"] - last_line <= max_gap:
                    current_cluster.append(m)
                else:
                    clusters.append({
                        "cluster_id": f"CLUST-{cluster_id:02d}",
                        "file": file_path,
                        "start_line": current_cluster[0]["line"],
                        "end_line": current_cluster[-1]["line"],
                        "count": len(current_cluster),
                        "operators": sorted(list(set(x.get("operator", "unknown") for x in current_cluster))),
                        "mutants": current_cluster,
                    })
                    cluster_id += 1
                    current_cluster = [m]
        if current_cluster:
            clusters.append({
                "cluster_id": f"CLUST-{cluster_id:02d}",
                "file": file_path,
                "start_line": current_cluster[0]["line"],
                "end_line": current_cluster[-1]["line"],
                "count": len(current_cluster),
                "operators": sorted(list(set(x.get("operator", "unknown") for x in current_cluster))),
                "mutants": current_cluster,
            })
            cluster_id += 1

    return clusters


def match_guard_to_mutants(guard: dict[str, Any], mutants: list[dict[str, Any]]) -> dict[str, Any]:
    if guard["layer"] != "code" or not guard["file"]:
        return {
            "guard_id": guard["id"],
            "in_scope": False,
            "matched_mutants_count": 0,
            "matched_mutants": [],
            "matched_clusters": [],
        }

    target_file = guard["file"]
    start, end = guard["lines"] if guard["lines"] else (0, 0)
    other_file = guard.get("other_file")
    other_start, other_end = guard.get("other_lines") if guard.get("other_lines") else (0, 0)

    matched = []
    for m in mutants:
        m_file = m["file"]
        m_line = m["line"]
        if m_file == target_file and start <= m_line <= end:
            matched.append(m)
        elif other_file and m_file == other_file and other_start <= m_line <= other_end:
            matched.append(m)

    return {
        "guard_id": guard["id"],
        "in_scope": True,
        "matched_mutants_count": len(matched),
        "matched_mutants": matched,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    exp47_results_path = repo_root / "docs/10-research/experiments/exp47/results-exp47.json"
    with open(exp47_results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    weak_mutants = data.get("weakest_guards", [])
    clusters = cluster_mutants(weak_mutants, max_gap=5)

    print("================================================================================")
    print("EXP-48: MUTATION SURVIVOR CLUSTERING VS P2 GUARD CATALOGUE")
    print("================================================================================\n")
    print(f"Total EXP-47 Surviving True Defects Analyzed: {len(weak_mutants)}")
    print(f"Total Spatial Clusters Formed (max_gap <= 5 lines): {len(clusters)}")

    # 1. P2 Scope and Guard Mapping
    total_p2_defects = 25  # A1-A11, A13, A14 (13) + A12, A15 (2) + B1-B10 (10)
    
    code_resident_guards = [g for g in P2_CATALOGUE if g["layer"] == "code"]
    non_code_guards = [g for g in P2_CATALOGUE if g["layer"] != "code" and g["id"] != "C1"]

    print("\nP2 Catalogue Breakdown:")
    print(f"  Total Defective Guards in P2: {total_p2_defects}")
    print(f"  - In-Scope Python Code-Resident (`src/consilient/`): {len(code_resident_guards)} ({len(code_resident_guards)/total_p2_defects*100:.1f}%)")
    print(f"  - Out-of-Scope (ADRs, CI Workflows, Governance, Harness, Scripts): {len(non_code_guards)} ({len(non_code_guards)/total_p2_defects*100:.1f}%)")

    # 2. Check Match for each P2 Guard
    print("\n--------------------------------------------------------------------------------")
    print("MAPPING P2 DEFECTIVE GUARDS TO EXP-47 MUTATION SURVIVORS")
    print("--------------------------------------------------------------------------------")
    
    matched_guards = []
    unmatched_code_guards = []
    
    for g in P2_CATALOGUE:
        if g["id"] == "C1":
            continue
        res = match_guard_to_mutants(g, weak_mutants)
        if not res["in_scope"]:
            print(f"[{g['id']}] OUT-OF-SCOPE ({g['layer']}): {g['description'][:70]}...")
        else:
            c = res["matched_mutants_count"]
            if c > 0:
                matched_guards.append(g["id"])
                ops = list(set(m["operator"] for m in res["matched_mutants"]))
                lines = [m["line"] for m in res["matched_mutants"]]
                print(f"[{g['id']}] MATCHED ({c} survivors, lines {min(lines)}-{max(lines)}): {g['description'][:65]}... | Ops: {ops}")
            else:
                unmatched_code_guards.append(g["id"])
                print(f"[{g['id']}] UNMATCHED (0 survivors): {g['description'][:70]}...")

    # Compute Recall Metrics
    overall_recall = len(matched_guards) / total_p2_defects
    code_recall = len(matched_guards) / len(code_resident_guards)

    print("\nRECALL ANALYSIS:")
    print(f"  Overall Catalogue Recall: {len(matched_guards)}/{total_p2_defects} = {overall_recall*100:.2f}%")
    print(f"  In-Scope Code-Resident Recall: {len(matched_guards)}/{len(code_resident_guards)} = {code_recall*100:.2f}%")
    print(f"  Matched Guards: {matched_guards}")
    print(f"  Unmatched Code Guards: {unmatched_code_guards}")

    # 3. Precision Analysis across the 61 Clusters
    print("\n--------------------------------------------------------------------------------")
    print("CLUSTER PRECISION TAXONOMY (61 Clusters)")
    print("--------------------------------------------------------------------------------")

    # Map each cluster to P2 guard if overlapping
    cluster_mappings = []
    for cl in clusters:
        f = cl["file"]
        s, e = cl["start_line"], cl["end_line"]
        overlapping_guards = []
        for g in code_resident_guards:
            g_f = g["file"]
            g_s, g_e = g["lines"] if g["lines"] else (0, 0)
            g_o_f = g.get("other_file")
            g_o_s, g_o_e = g.get("other_lines") if g.get("other_lines") else (0, 0)

            if (f == g_f and not (e < g_s or s > g_e)) or (g_o_f and f == g_o_f and not (e < g_o_s or s > g_o_e)):
                overlapping_guards.append(g["id"])

        cluster_mappings.append({
            "cluster": cl,
            "overlapping_guards": overlapping_guards,
        })

    p2_matched_clusters = [cm for cm in cluster_mappings if cm["overlapping_guards"]]
    unmatched_clusters = [cm for cm in cluster_mappings if not cm["overlapping_guards"]]

    print(f"Clusters matching P2 Catalogued Guards: {len(p2_matched_clusters)}/{len(clusters)} ({len(p2_matched_clusters)/len(clusters)*100:.1f}%)")
    print(f"Clusters unmatched to P2 Catalogue: {len(unmatched_clusters)}/{len(clusters)} ({len(unmatched_clusters)/len(clusters)*100:.1f}%)")

    # Inspect top unmatched clusters
    print("\n--------------------------------------------------------------------------------")
    print("TOP 10 UNMATCHED SURVIVOR CLUSTERS (P2 MISSES / NEW CANDIDATES)")
    print("--------------------------------------------------------------------------------")
    
    unmatched_clusters.sort(key=lambda x: x["cluster"]["count"], reverse=True)
    for i, um in enumerate(unmatched_clusters[:10]):
        cl = um["cluster"]
        print(f"#{i+1:02d} [{cl['cluster_id']}] {cl['file']}:{cl['start_line']}-{cl['end_line']} ({cl['count']} mutants)")
        print(f"    Operators: {cl['operators']}")
        sample = cl["mutants"][0]
        print(f"    Sample: L{sample['line']} | {sample['orig_snippet'][:70]} ==> {sample['mut_snippet'][:70]}")

    # Output JSON summary for artifact retention
    summary_output = {
        "experiment_id": "EXP-48",
        "sample_size": len(weak_mutants),
        "total_clusters": len(clusters),
        "p2_defects_total": total_p2_defects,
        "p2_code_resident_count": len(code_resident_guards),
        "p2_non_code_count": len(non_code_guards),
        "matched_p2_guard_ids": matched_guards,
        "unmatched_code_guard_ids": unmatched_code_guards,
        "overall_recall": overall_recall,
        "code_resident_recall": code_recall,
        "cluster_precision_p2_matched": len(p2_matched_clusters) / len(clusters),
        "top_unmatched_clusters": [
            {
                "id": um["cluster"]["cluster_id"],
                "file": um["cluster"]["file"],
                "lines": [um["cluster"]["start_line"], um["cluster"]["end_line"]],
                "mutant_count": um["cluster"]["count"],
                "operators": um["cluster"]["operators"],
                "sample_orig": um["cluster"]["mutants"][0]["orig_snippet"],
                "sample_mut": um["cluster"]["mutants"][0]["mut_snippet"],
            }
            for um in unmatched_clusters[:15]
        ],
    }
    
    out_json = repo_root / "docs/10-research/experiments/exp48/results-exp48.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2)
    print(f"\nWrote summary results to {out_json}")


if __name__ == "__main__":
    main()

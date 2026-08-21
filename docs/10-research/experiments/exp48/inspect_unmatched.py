"""EXP-48: Detailed Deep-Dive on Top Unmatched Clusters."""

from __future__ import annotations

import json
from pathlib import Path

from run_exp48 import P2_CATALOGUE, cluster_mutants


def inspect_clusters() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    exp47_results_path = repo_root / "docs/10-research/experiments/exp47/results-exp47.json"
    with open(exp47_results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    weak_mutants = data.get("weakest_guards", [])
    clusters = cluster_mutants(weak_mutants, max_gap=5)

    code_resident_guards = [g for g in P2_CATALOGUE if g["layer"] == "code"]

    unmatched = []
    matched = []
    for cl in clusters:
        f = cl["file"]
        s, e = cl["start_line"], cl["end_line"]
        overlapping = []
        for g in code_resident_guards:
            g_f = g["file"]
            g_s, g_e = g["lines"] if g["lines"] else (0, 0)
            g_o_f = g.get("other_file")
            g_o_s, g_o_e = g.get("other_lines") if g.get("other_lines") else (0, 0)

            if (f == g_f and not (e < g_s or s > g_e)) or (g_o_f and f == g_o_f and not (e < g_o_s or s > g_o_e)):
                overlapping.append(g["id"])

        if overlapping:
            matched.append((cl, overlapping))
        else:
            unmatched.append(cl)

    print(f"Total Clusters: {len(clusters)}")
    print(f"Matched Clusters: {len(matched)}")
    print(f"Unmatched Clusters: {len(unmatched)}")

    # Classify unmatched clusters
    print("\n--- CLASSIFICATION OF UNMATCHED CLUSTERS ---")
    
    cli_format_clusters = []
    cli_gate_logic_clusters = []
    events_validation_clusters = []
    projection_indexing_clusters = []
    beta_stats_clusters = []
    other_clusters = []

    for cl in unmatched:
        f = cl["file"]
        s, e = cl["start_line"], cl["end_line"]
        
        # Read the actual lines from the file
        full_path = repo_root / f
        file_lines = full_path.read_text(encoding="utf-8").splitlines()
        code_slice = "\n".join(f"{i+1:4d}| {line}" for i, line in enumerate(file_lines[max(0, s-2):min(len(file_lines), e+2)], start=max(0, s-2)))

        if f == "src/consilient/cli.py":
            if any(term in code_slice.lower() for term in ["print(", "render", "table", "formatter", "header", "format"]):
                cli_format_clusters.append((cl, code_slice))
            elif any(term in code_slice for term in ["_condition", "REQUIREMENTS", "gate", "_experiment_entry", "EXPERIMENT_REGISTER"]):
                cli_gate_logic_clusters.append((cl, code_slice))
            else:
                cli_format_clusters.append((cl, code_slice))
        elif f == "src/consilient/events.py":
            events_validation_clusters.append((cl, code_slice))
        elif f == "src/consilient/projection.py":
            projection_indexing_clusters.append((cl, code_slice))
        elif f == "src/consilient/beta.py":
            beta_stats_clusters.append((cl, code_slice))
        else:
            other_clusters.append((cl, code_slice))

    print(f"1. CLI Human Formatting & Output Strings: {len(cli_format_clusters)} clusters (Mutants: {sum(c[0]['count'] for c in cli_format_clusters)})")
    print(f"2. CLI Gate Inspection Logic (`consil gate` / requirements): {len(cli_gate_logic_clusters)} clusters (Mutants: {sum(c[0]['count'] for c in cli_gate_logic_clusters)})")
    print(f"3. Events Validation Edge Cases & Error Messages: {len(events_validation_clusters)} clusters (Mutants: {sum(c[0]['count'] for c in events_validation_clusters)})")
    print(f"4. Projection Digest / Indexing / Null Handling: {len(projection_indexing_clusters)} clusters (Mutants: {sum(c[0]['count'] for c in projection_indexing_clusters)})")
    print(f"5. Beta Interval / Filtering Defaults: {len(beta_stats_clusters)} clusters (Mutants: {sum(c[0]['count'] for c in beta_stats_clusters)})")

    print("\n--- SAMPLE CLUSTERS IN DETAIL ---")
    print("\nTop CLI Gate Evaluation Cluster:")
    for cl, code in cli_gate_logic_clusters[:3]:
        print(f"\n[{cl['cluster_id']}] {cl['file']}:{cl['start_line']}-{cl['end_line']} ({cl['count']} mutants)")
        print(code[:400])

    print("\nTop CLI Rendering Cluster:")
    for cl, code in cli_format_clusters[:3]:
        print(f"\n[{cl['cluster_id']}] {cl['file']}:{cl['start_line']}-{cl['end_line']} ({cl['count']} mutants)")
        print(code[:400])

    print("\nTop Events / Projection Clusters:")
    for cl, code in (events_validation_clusters + projection_indexing_clusters)[:3]:
        print(f"\n[{cl['cluster_id']}] {cl['file']}:{cl['start_line']}-{cl['end_line']} ({cl['count']} mutants)")
        print(code[:400])


if __name__ == "__main__":
    inspect_clusters()

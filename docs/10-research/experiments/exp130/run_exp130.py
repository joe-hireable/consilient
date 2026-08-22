"""EXP-130: can claim sets be derived from the import graph, and what does derivation cost?

Single pre-registered pass over frozen local artefacts. No model call, no network, stdlib only.

Inputs:
  - the four stream plans (unit id, declared claim paths, depends-on edges)
  - the hand-written serial lane table in the build plan
  - a file-level import graph over src/, scripts/, tests/ derived with stdlib ast
  - the local trajectory logs 2026-08-19 .. 2026-08-22 (dispatch claims and terminal events)

Analyses A1-A5 as registered in docs/10-research/experiment-register.md (EXP-130).
Output: results-exp130.json beside this script.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PLANS_GLOB = "docs/superpowers/plans/2026-08-22-*-plan.md"
BUILD_PLAN = "docs/superpowers/plans/2026-08-22-build-plan.md"
LOG_GLOB = ".harness/log/2026-08-*.jsonl"
PY_ROOTS = ("src", "scripts", "tests")

UNIT_RE = re.compile(r"\b([A-Z]\d{2})\b")
EVENT_KIND_RE = re.compile(r"[\"']([a-z][a-z_0-9]*\.[a-z][a-z_0-9.]+)[\"']")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ---------- import graph (ast, file level) ----------

def module_to_file(module: str, importing: Path, pyfiles: set[str]) -> str | None:
    """Resolve one imported module name to a repo-relative posix path, or None."""
    parts = module.split(".") if module else []
    candidates: list[Path] = []
    if not parts:
        return None
    for base in (ROOT, ROOT / "src", importing.parent):
        cand = base.joinpath(*parts)
        candidates.append(cand.with_suffix(".py"))
        candidates.append(cand / "__init__.py")
    for cand in candidates:
        try:
            rel = cand.resolve().relative_to(ROOT).as_posix()
        except (OSError, ValueError):
            continue
        if rel in pyfiles:
            return rel
    return None


def build_import_graph(
    pyfiles: set[str],
) -> tuple[dict[str, set[str]], dict[str, int], list[str]]:
    """Edge importer -> imported, both repo-relative posix paths. Returns (graph,
    unresolved_counts, unparseable_files). Unresolved imports are split into
    internal-looking (relative imports, or a top-level module naming a repo root
    package) and external (stdlib/third-party), because only the former can
    indicate a resolution weakness in the instrument."""
    graph: dict[str, set[str]] = {f: set() for f in pyfiles}
    unresolved = {"internal": 0, "external": 0}
    unparseable: list[str] = []
    repo_packages = {p.split("/", 1)[0] for p in pyfiles} | {
        p.split("/")[1] for p in pyfiles if p.startswith("src/") and p.count("/") > 1
    }

    def miss(module: str, *, relative: bool) -> None:
        top = module.split(".", 1)[0] if module else ""
        if relative or top in repo_packages:
            unresolved["internal"] += 1
        else:
            unresolved["external"] += 1

    for rel in sorted(pyfiles):
        path = ROOT / rel
        try:
            tree = ast.parse(read_text(path), filename=rel)
        except SyntaxError:
            unparseable.append(rel)
            continue
        for node in ast.walk(tree):
            target: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = module_to_file(alias.name, path, pyfiles)
                    if target is None:
                        miss(alias.name, relative=False)
                    elif target != rel:
                        graph[rel].add(target)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    # relative: from . import x / from .mod import x
                    pkg = path.parent
                    for _ in range(node.level - 1):
                        pkg = pkg.parent
                    base_module = node.module or ""
                    try:
                        base_rel = pkg.relative_to(ROOT).as_posix()
                    except ValueError:
                        miss(base_module, relative=True)
                        continue
                    dotted = (
                        base_rel.replace("/", ".")
                        + ("." + base_module if base_module else "")
                    )
                    # src-layout: drop a leading 'src.' so consilient.x resolves
                    for prefix in ("src.", "scripts.", "tests."):
                        if dotted.startswith(prefix):
                            dotted = dotted[len(prefix):]
                            break
                    base_target = module_to_file(dotted, path, pyfiles)
                    if base_target is None:
                        miss(dotted, relative=True)
                    elif base_target != rel:
                        graph[rel].add(base_target)
                    # from pkg import submodule: the imported names may be modules
                    for alias in node.names:
                        sub = module_to_file(
                            f"{dotted}.{alias.name}" if dotted else alias.name,
                            path,
                            pyfiles,
                        )
                        if sub is not None and sub != rel:
                            graph[rel].add(sub)
                else:
                    base_module = node.module or ""
                    base_target = module_to_file(base_module, path, pyfiles)
                    if base_target is None:
                        miss(base_module, relative=False)
                    elif base_target != rel:
                        graph[rel].add(base_target)
                    for alias in node.names:
                        sub = module_to_file(
                            f"{base_module}.{alias.name}" if base_module else alias.name,
                            path,
                            pyfiles,
                        )
                        if sub is not None and sub != rel:
                            graph[rel].add(sub)
    return graph, unresolved, unparseable


def cycle_count(nodes: dict[str, set[str]] | dict[str, list[str]]) -> int:
    """Number of non-trivial strongly connected components (Tarjan, iterative)."""
    index_of: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    counter = 0
    sccs = 0
    for root in nodes:
        if root in index_of:
            continue
        work = [(root, iter(sorted(nodes[root])))]
        while work:
            node, it = work[-1]
            if node not in index_of:
                index_of[node] = lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            advanced = False
            for nxt in it:
                if nxt not in nodes:
                    continue
                if nxt not in index_of:
                    work.append((nxt, iter(sorted(nodes[nxt]))))
                    advanced = True
                    break
                if nxt in on_stack:
                    lowlink[node] = min(lowlink[node], index_of[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])
            if lowlink[node] == index_of[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == node:
                        break
                if len(scc) > 1 or node in set(nodes[node]):
                    sccs += 1
    return sccs


def transitive_dependents(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    """Reverse reachability: file -> every file that imports it, transitively."""
    reverse: dict[str, set[str]] = defaultdict(set)
    for importer, imported_set in graph.items():
        for imported in imported_set:
            reverse[imported].add(importer)
    closure: dict[str, set[str]] = {}
    for f in graph:
        seen: set[str] = set()
        queue = deque(reverse.get(f, ()))
        while queue:
            cur = queue.popleft()
            if cur in seen or cur == f:
                continue
            seen.add(cur)
            queue.extend(reverse.get(cur, ()))
        closure[f] = seen
    return closure


# ---------- plan parsing ----------

def parse_plans() -> dict[str, dict]:
    units: dict[str, dict] = {}
    for plan in sorted(ROOT.glob(PLANS_GLOB)):
        if plan.name.endswith("build-plan.md"):
            continue
        text = read_text(plan)
        for m in re.finditer(r"^## ([A-Z]\d+) [—-] (.*?)\n(.*?)(?=^## |\Z)", text, re.M | re.S):
            uid, title, body = m.group(1), m.group(2), m.group(3)
            cm = re.search(r"\*\*Claim exactly:\*\*\n((?:\n- .*)+)", body)
            paths = re.findall(r"`([^`]+)`", cm.group(1)) if cm else []
            dm = re.search(r"\*\*Depends on:\*\*(.*)", body)
            depends = UNIT_RE.findall(dm.group(1)) if dm else []
            units[uid] = {
                "title": title.strip(),
                "paths": paths,
                "depends": sorted(set(d for d in depends if d != uid)),
                "plan": plan.name,
            }
    return units


def parse_lanes() -> dict[str, list[str]]:
    text = read_text(ROOT / BUILD_PLAN)
    section = text.split("## Parallelism and claim lanes", 1)[1]
    lanes: dict[str, list[str]] = {}
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        lane_file = cells[0].strip("`")
        lanes[lane_file] = UNIT_RE.findall(cells[1])
    return lanes


# ---------- claim semantics (mirror coordination.paths_overlap) ----------

def norm(path: str) -> str:
    return path.replace("\\", "/").strip("/").casefold()


def paths_overlap(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def sets_overlap(first: list[str], second: list[str]) -> bool:
    return any(paths_overlap(a, b) for a in first for b in second)


# ---------- dependency order ----------

def reachable(units: dict[str, dict], start: str) -> set[str]:
    seen: set[str] = set()
    queue = deque(units[start]["depends"])
    while queue:
        cur = queue.popleft()
        if cur in seen or cur not in units:
            continue
        seen.add(cur)
        queue.extend(units[cur]["depends"])
    return seen


# ---------- maximum independent set (exact, branch and bound) ----------

def max_independent_set(nodes: list[str], edges: set[frozenset]) -> list[str]:
    adj: dict[str, set[str]] = {n: set() for n in nodes}
    for e in edges:
        a, b = tuple(e)
        adj[a].add(b)
        adj[b].add(a)
    best: list[str] = []

    def branch(candidates: set[str], chosen: list[str]) -> None:
        nonlocal best
        if len(chosen) + len(candidates) <= len(best):
            return
        if not candidates:
            if len(chosen) > len(best):
                best = list(chosen)
            return
        v = max(candidates, key=lambda n: len(adj[n] & candidates))
        branch(candidates - {v} - adj[v], chosen + [v])
        branch(candidates - {v}, chosen)

    branch(set(nodes), [])
    return best


# ---------- trajectory replay ----------

def parse_claims() -> list[dict]:
    claims: dict[str, dict] = {}
    terminal_kinds = {"dispatch.outcome", "dispatch.refused", "dispatch.fanout"}
    for log in sorted(ROOT.glob(LOG_GLOB)):
        for line in read_text(log).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = event.get("data", {})
            kind = event.get("event")
            ts = event.get("ts", "")
            if kind == "work_item.opened":
                ticket = data.get("ticket", "")
                if isinstance(ticket, str) and ticket.startswith("dispatch:"):
                    claims[ticket] = {
                        "run_id": data.get("run_id", ""),
                        "paths": [p for p in data.get("paths", []) if isinstance(p, str)],
                        "opened_at": data.get("opened_at", ts),
                        "expires_at": data.get("expires_at", ts),
                        "end": None,
                        "log": log.name,
                    }
            elif kind == "work_item.completed":
                ticket = data.get("ticket", "")
                if ticket in claims and claims[ticket]["end"] is None:
                    claims[ticket]["end"] = ts
            elif kind in terminal_kinds:
                run_id = data.get("run_id", "")
                ticket = f"dispatch:{run_id}"
                if ticket in claims and claims[ticket]["end"] is None:
                    claims[ticket]["end"] = ts
    out = []
    for claim in claims.values():
        claim["end"] = claim["end"] or claim["expires_at"]
        out.append(claim)
    out.sort(key=lambda c: c["opened_at"])
    return out


def reopen_counts() -> dict[str, int]:
    """How many times each dispatch ticket was opened (a claim widened mid-run)."""
    counts: dict[str, int] = defaultdict(int)
    for log in sorted(ROOT.glob(LOG_GLOB)):
        for line in read_text(log).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "work_item.opened":
                ticket = event.get("data", {}).get("ticket", "")
                if isinstance(ticket, str) and ticket.startswith("dispatch:"):
                    counts[ticket] += 1
    return dict(counts)


def max_concurrent_by_day(claims: list[dict]) -> dict[str, int]:
    per_day: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for c in claims:
        per_day[c["log"]].append((c["opened_at"], 1))
        per_day[c["log"]].append((c["end"], -1))
    out: dict[str, int] = {}
    for day, points in per_day.items():
        points.sort()
        cur = mx = 0
        for _, delta in points:
            cur += delta
            mx = max(mx, cur)
        out[day] = mx
    return out


def replay(claims: list[dict], derived: dict[str, list[str]]) -> dict:
    """Interval replay in opened_at order. Control admits on declared-path overlap;
    treatment admits on derived-set overlap. A claim is live until its end."""
    def run(policy_paths) -> dict:
        live: list[dict] = []
        admitted = refused = 0
        conflict_pairs: list[list[str]] = []
        for claim in claims:
            live = [c for c in live if c["end"] > claim["opened_at"]]
            mine = policy_paths(claim)
            hit = None
            for other in live:
                if sets_overlap(mine, policy_paths(other)):
                    hit = other
                    break
            if hit is None:
                live.append(claim)
                admitted += 1
            else:
                refused += 1
                conflict_pairs.append([claim["run_id"], hit["run_id"]])
        return {"admitted": admitted, "refused": refused, "conflict_pairs": conflict_pairs}

    control = run(lambda c: c["paths"])
    treatment = run(lambda c: derived.get(c["run_id"], c["paths"]))
    # what actually happened: concurrent pairs with overlapping declared paths
    actual_overlap_pairs: list[list[str]] = []
    for i, a in enumerate(claims):
        for b in claims[i + 1 :]:
            if b["opened_at"] >= a["end"]:
                break
            if sets_overlap(a["paths"], b["paths"]):
                actual_overlap_pairs.append([a["run_id"], b["run_id"]])
    return {
        "claims_total": len(claims),
        "control": control,
        "treatment": treatment,
        "actual_concurrent_overlapping_pairs": len(actual_overlap_pairs),
        "actual_concurrent_overlapping_pair_ids": actual_overlap_pairs,
    }


def main() -> int:
    pyfiles: set[str] = set()
    for root_name in PY_ROOTS:
        for path in (ROOT / root_name).rglob("*.py"):
            pyfiles.add(path.relative_to(ROOT).as_posix())

    graph, unresolved, unparseable = build_import_graph(pyfiles)
    dependents = transitive_dependents(graph)
    edge_count = sum(len(v) for v in graph.values())

    units = parse_plans()
    lanes = parse_lanes()

    # derived claim set per unit: declared paths union transitive dependents of the .py ones
    derived_unit: dict[str, list[str]] = {}
    for uid, unit in units.items():
        extra: set[str] = set()
        for p in unit["paths"]:
            np = norm(p)
            if np.endswith(".py") and np in dependents:
                extra |= dependents[np]
        derived_unit[uid] = sorted(set(unit["paths"]) | extra)

    # ---- A1: lane-table drift
    lane_of: dict[str, set[str]] = defaultdict(set)
    for lane_file, order in lanes.items():
        for uid in order:
            lane_of[uid].add(lane_file)
    lane_lists_unit_without_claim = []
    for lane_file, order in lanes.items():
        for uid in order:
            if uid in units and units[uid]["paths"] and not any(
                paths_overlap(p, lane_file) for p in units[uid]["paths"]
            ):
                lane_lists_unit_without_claim.append([lane_file, uid])
    unit_claims_lane_file_but_not_in_lane = []
    for uid, unit in units.items():
        for lane_file in lanes:
            if any(paths_overlap(p, lane_file) for p in unit["paths"]) and lane_file not in lane_of[uid]:
                unit_claims_lane_file_but_not_in_lane.append([uid, lane_file])
    overlapping_pairs = []
    uids = sorted(units)
    dep_reach = {u: reachable(units, u) for u in uids}
    for i, a in enumerate(uids):
        for b in uids[i + 1 :]:
            if units[a]["paths"] and units[b]["paths"] and sets_overlap(units[a]["paths"], units[b]["paths"]):
                shared_lane = lane_of[a] & lane_of[b]
                dep_ordered = b in dep_reach[a] or a in dep_reach[b]
                overlapping_pairs.append(
                    {
                        "pair": [a, b],
                        "ordered_by_lane": bool(shared_lane),
                        "ordered_by_dependency": dep_ordered,
                    }
                )
    under_serialised = [p["pair"] for p in overlapping_pairs if not p["ordered_by_lane"]]
    unordered_by_anything = [
        p["pair"]
        for p in overlapping_pairs
        if not p["ordered_by_lane"] and not p["ordered_by_dependency"]
    ]

    # ---- A2: concurrency width, control vs treatment
    def conflict_edges(claim_map: dict[str, list[str]]) -> set[frozenset]:
        edges: set[frozenset] = set()
        for i, a in enumerate(uids):
            deps_a = reachable(units, a)
            for b in uids[i + 1 :]:
                if b in deps_a or a in reachable(units, b):
                    edges.add(frozenset((a, b)))
                elif claim_map[a] and claim_map[b] and sets_overlap(claim_map[a], claim_map[b]):
                    edges.add(frozenset((a, b)))
        return edges

    control_edges = conflict_edges({u: units[u]["paths"] for u in uids})
    treatment_edges = conflict_edges(derived_unit)
    control_width = len(max_independent_set(uids, control_edges))
    treatment_width = len(max_independent_set(uids, treatment_edges))
    derived_sizes = [len(derived_unit[u]) for u in uids if units[u]["paths"]]
    derived_sizes.sort()
    median_derived = derived_sizes[len(derived_sizes) // 2] if derived_sizes else 0
    god_node_share = (
        sum(1 for u in uids if "src/consilient/events.py" in derived_unit[u])
        / max(1, sum(1 for u in uids if units[u]["paths"]))
    )
    # per-file dependents-closure distribution over all py files (god-node check)
    closure_sizes = sorted((len(v) for v in dependents.values()), reverse=True)
    max_closure = closure_sizes[0] if closure_sizes else 0
    max_closure_file = max(dependents, key=lambda f: len(dependents[f])) if dependents else ""
    files_ge_50pct = sum(1 for n in closure_sizes if n >= 0.5 * len(pyfiles))
    files_ge_30pct = sum(1 for n in closure_sizes if n >= 0.3 * len(pyfiles))

    # lane order inversions: within one lane's list, a later unit that an earlier
    # unit depends on (the lane lists them in an order the dependency forbids)
    lane_inversions: list[list[str]] = []
    for lane_file, order in lanes.items():
        for i, earlier in enumerate(order):
            if earlier not in units:
                continue
            deps_of_earlier = reachable(units, earlier)
            for later in order[i + 1 :]:
                if later in deps_of_earlier:
                    lane_inversions.append([lane_file, earlier, later])

    unit_dep_graph = {u: set(units[u]["depends"]) & set(units) for u in units}

    # ---- A3: failure coverage (counts only; classification is in the findings)
    events_py_dependents = len(dependents.get("src/consilient/events.py", set()))

    # ---- A4: coupling the import graph misses
    kind_files: dict[str, set[str]] = defaultdict(set)
    for rel in pyfiles:
        for kind in set(EVENT_KIND_RE.findall(read_text(ROOT / rel))):
            kind_files[kind].add(rel)
    shared_kinds = {k: v for k, v in kind_files.items() if len(v) >= 2}
    schema_coupled_no_import = 0
    examples: list[list[str]] = []
    files = sorted(pyfiles)
    for i, a in enumerate(files):
        for b in files[i + 1 :]:
            if b in graph[a] or a in graph[b]:
                continue
            shared = [k for k, v in shared_kinds.items() if a in v and b in v]
            if shared:
                schema_coupled_no_import += 1
                if len(examples) < 5:
                    examples.append([a, b, shared[0]])
    claimed_paths_all = [p for u in units.values() for p in u["paths"]]
    non_py_claimed = [p for p in claimed_paths_all if not norm(p).endswith(".py")]

    # ---- A5: replay
    claims = parse_claims()
    reopens = reopen_counts()
    reopened = {k: v for k, v in reopens.items() if v > 1}
    derived_claim: dict[str, list[str]] = {}
    for c in claims:
        extra: set[str] = set()
        for p in c["paths"]:
            np = norm(p)
            # trajectory paths are canonicalised absolute; map back to repo-relative by
            # taking the suffix after the LAST repo-root marker (worktree or main checkout)
            for marker in ("consilience-cto/", "consilience/"):
                if marker in np:
                    np = np.rsplit(marker, 1)[1]
                    break
            if np.endswith(".py") and np in dependents:
                extra |= dependents[np]
        derived_claim[c["run_id"]] = sorted(set(c["paths"]) | extra)
    replay_result = replay(claims, derived_claim)

    results = {
        "experiment": "EXP-130",
        "inputs": {
            "py_files": len(pyfiles),
            "import_edges": edge_count,
            "import_graph_cycles": cycle_count(graph),
            "unresolved_imports_internal": unresolved["internal"],
            "unresolved_imports_external": unresolved["external"],
            "unparseable_files": unparseable,
            "plan_units": len(units),
            "units_with_declared_paths": sum(1 for u in units.values() if u["paths"]),
            "declared_dependency_edges": sum(len(u["depends"]) for u in units.values()),
            "unit_dependency_cycles": cycle_count(unit_dep_graph),
            "lane_count": len(lanes),
            "trajectory_claims": len(claims),
        },
        "A1_lane_drift": {
            "lane_lists_unit_that_does_not_claim_file": lane_lists_unit_without_claim,
            "unit_claims_lane_file_but_absent_from_lane": unit_claims_lane_file_but_not_in_lane,
            "overlapping_unit_pairs": len(overlapping_pairs),
            "under_serialised_pairs": under_serialised,
            "under_serialised_count": len(under_serialised),
            "unordered_by_lane_or_dependency": unordered_by_anything,
            "unordered_by_lane_or_dependency_count": len(unordered_by_anything),
            "lane_order_inversions": lane_inversions,
            "lane_order_inversion_count": len(lane_inversions),
        },
        "A2_concurrency": {
            "control_max_concurrent_units": control_width,
            "treatment_max_concurrent_units": treatment_width,
            "control_conflict_edges": len(control_edges),
            "treatment_conflict_edges": len(treatment_edges),
            "median_derived_claim_size_paths": median_derived,
            "py_files_total": len(pyfiles),
            "max_dependents_closure_size": max_closure,
            "max_dependents_closure_file": max_closure_file,
            "files_with_closure_ge_50pct_of_repo": files_ge_50pct,
            "files_with_closure_ge_30pct_of_repo": files_ge_30pct,
            "share_of_path_units_whose_derived_claim_includes_events_py": round(god_node_share, 4),
        },
        "A3_failure_coverage_counts": {
            "events_py_transitive_dependents": events_py_dependents,
            "git_index_in_import_graph": False,
        },
        "A4_invisible_coupling": {
            "event_kind_literals_shared_by_2plus_files": len(shared_kinds),
            "file_pairs_schema_coupled_without_import_edge": schema_coupled_no_import,
            "examples": examples,
            "claimed_plan_paths_total": len(claimed_paths_all),
            "claimed_plan_paths_non_python": len(non_py_claimed),
        },
        "A5_replay": replay_result,
        "A5_context": {
            "claims_opened_more_than_once": len(reopened),
            "max_concurrently_live_claims_by_day": max_concurrent_by_day(claims),
        },
    }
    out = Path(__file__).resolve().parent / "results-exp130.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Plan a split as a LAYERING of the reference graph, so no shared module is needed at all.

Three rounds of agent planning failed the same way, and it was never a reasoning failure: a seam
chosen by SUBJECT drags half the module into `shared`, because the fixpoint follows every
reference the moved symbols make. Measured against a 450-line budget: recall.py reached 686,
work_items.py 561, projection.py 530. All refused.

The graph already answers it. Condense the strongly-connected components of the symbol reference
graph, sort the condensation topologically, and fill files from the BOTTOM UP: each file then
references only symbols defined in files below it, which is exactly what the splitter enforces,
and `shared` is empty because nothing needs pulling down. A file is over budget only when one
mutually-recursive component is itself over budget -- a real finding about the module rather than
an arithmetic accident.

TWO CONSTRAINTS THAT ARE NOT ABOUT SIZE.

  * PATCHED NAMES. `monkeypatch.setattr(module, "name", fake)` reaches a caller only while the
    caller resolves that name in the SAME module namespace. Measured: behind a re-exporting facade
    the stale patch is SILENT. So a patched symbol and every caller of it are merged into one node
    before layering, and the layering cannot then separate them. Pass them with --patched.
  * THE ENTRY POINT KEEPS ITS FILENAME, so it must be the TOP layer: it may import the siblings,
    and no sibling may import it.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def defined(node: ast.stmt) -> list[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [
            t.id for t in node.targets if isinstance(t, ast.Name) and t.id != "__all__"
        ]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def analyse(tree: ast.Module) -> tuple[dict[str, int], dict[str, set[str]]]:
    spans: dict[str, int] = {}
    for node in tree.body:
        for name in defined(node):
            spans[name] = (node.end_lineno or node.lineno) - node.lineno + 1
    refs: dict[str, set[str]] = {}
    for node in tree.body:
        names = [n for n in defined(node) if n in spans]
        if not names:
            continue
        seen = {
            s.id for s in ast.walk(node) if isinstance(s, ast.Name) and s.id in spans
        }
        for name in names:
            refs.setdefault(name, set()).update(seen - {name})
    return spans, refs


def condense(
    nodes: set[str], refs: dict[str, set[str]]
) -> tuple[list[frozenset[str]], dict[frozenset[str], set[frozenset[str]]]]:
    """Tarjan, iterative. These modules are deep enough to blow the recursion limit."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on: set[str] = set()
    stack: list[str] = []
    comps: list[frozenset[str]] = []
    counter = 0
    for root in sorted(nodes):
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on.add(root)
        work: list[tuple[str, list[str]]] = [
            (root, sorted(refs.get(root, set()) & nodes))
        ]
        while work:
            v, pending = work[-1]
            if pending:
                w = pending.pop()
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, sorted(refs.get(w, set()) & nodes)))
                elif w in on:
                    low[v] = min(low[v], index[w])
            else:
                work.pop()
                if low[v] == index[v]:
                    comp: set[str] = set()
                    while True:
                        w = stack.pop()
                        on.discard(w)
                        comp.add(w)
                        if w == v:
                            break
                    comps.append(frozenset(comp))
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
    owner = {n: c for c in comps for n in c}
    edges: dict[frozenset[str], set[frozenset[str]]] = {c: set() for c in comps}
    for comp in comps:
        for n in comp:
            for target in refs.get(n, set()) & nodes:
                if owner[target] is not comp:
                    edges[comp].add(owner[target])
    return comps, edges


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("module")
    # 900, not 1000, and the gap is not caution -- it is a UNIT MISMATCH worth stating. This
    # budget counts SYMBOL-lines; check_file_length.py counts PHYSICAL lines, which are ~10-15%
    # higher because of the blank lines between symbols and the file header. Measured 29 August
    # 2026: promote.py plans to one file at budget 1000 and that file is 1,094 physical lines,
    # which breaks a 1,000 cap. 900 is the budget that actually lands under it.
    #
    # It was 430 against a 500 cap, and that 14% margin is why the tree is over-split: at the
    # cap in force the eight measurable modules needed 22 files and the tree contains 38, with
    # 24 files packed into 400-449 and NONE between 500 and 549 -- a censoring cliff at the wall.
    # Target the cap; the cap is the rule (ADR-0111).
    ap.add_argument("--budget", type=int, default=900)
    ap.add_argument(
        "--patched", default="", help="comma-separated names the suite patches"
    )
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    path = Path(args.module)
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    spans, refs = analyse(tree)
    nodes = set(spans)

    patched = {p for p in args.patched.split(",") if p} & nodes
    for name in patched:
        group = {n for n, r in refs.items() if name in r} | {name}
        for member in group:
            refs.setdefault(member, set()).update(group - {member})

    comps, edges = condense(nodes, refs)
    size = {c: sum(spans[n] for n in c) for c in comps}

    depth: dict[frozenset[str], int] = {}
    for comp in sorted(comps, key=lambda c: len(c)):
        pass

    def depth_of(
        c: frozenset[str], seen: frozenset[frozenset[str]] = frozenset()
    ) -> int:
        if c in depth:
            return depth[c]
        value = 1 + max(
            (depth_of(t, seen | {c}) for t in edges[c] if t not in seen), default=-1
        )
        depth[c] = value
        return value

    for comp in comps:
        depth_of(comp)

    over = [c for c in comps if size[c] > args.budget]
    if over:
        worst = max(over, key=lambda c: size[c])
        print(
            f"BLOCKED: a single component is {size[worst]} lines, over the {args.budget} budget."
        )
        print(f"  {len(worst)} symbol(s): {sorted(worst)[:8]}")
        print("  A component is mutually recursive, so it cannot be layered apart.")
        return 1

    files: list[list[frozenset[str]]] = []
    current: list[frozenset[str]] = []
    used = 0
    for comp in sorted(comps, key=lambda c: (depth[c], -size[c], sorted(c)[0])):
        if used + size[comp] > args.budget:
            files.append(current)
            current, used = [], 0
        current.append(comp)
        used += size[comp]
    if current:
        files.append(current)

    # The header is the statements EVERY destination inherits -- the docstring, the imports and
    # any top-level statement defining no symbol. It is emphatically not "file lines minus symbol
    # lines": that difference also contains the blank line PEP 8 puts between definitions, which
    # distributes across the family rather than landing on the entry point. Measured on
    # events.py, the wrong sum reported a 469-line header against a real one of 37, and would
    # have refused a module that layers perfectly well.
    header = 0
    for node in tree.body:
        if defined(node):
            continue
        header += (node.end_lineno or node.lineno) - node.lineno + 1

    # Two blank lines per definition, which ruff format will insert in each destination.
    def entry_estimate(group: list[frozenset[str]]) -> int:
        count = sum(len(c) for c in group)
        return sum(size[c] for c in group) + header + 2 * count

    print(
        f"{path.name}: {len(nodes)} symbols, {sum(spans.values())} symbol-lines, "
        f"{header} header lines, {len(comps)} components"
    )
    print(f"patched, so pinned to their callers: {sorted(patched) or 'none'}")
    print(f"\n{len(files)} file(s) at budget {args.budget}, bottom layer first:")
    for i, group in enumerate(files):
        names = sorted(n for c in group for n in c)
        tag = "ENTRY" if i == len(files) - 1 else f"sib{i}"
        print(
            f"  {tag:>5}: {sum(size[c] for c in group):4d} lines, {len(names):3d} symbols  "
            f"{names[:4]}"
        )
    print(
        f"\n  entry = {sum(size[c] for c in files[-1])} + {header} header = "
        f"~{sum(size[c] for c in files[-1]) + header} lines"
    )
    if args.out:
        Path(args.out).write_text(
            json.dumps([sorted(n for c in g for n in c) for g in files], indent=1),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Move top-level symbols out of one module into siblings, byte-for-byte.

The split is a MOVE or it is nothing: each symbol's source lines -- decorators, the
comment block above it, its whole body -- are copied verbatim into exactly one
destination, so `scripts/verify_split.py` can prove the bodies identical afterwards. A
symbol assigned to no destination is refused; a symbol silently dropped is the failure
this exists to prevent.

THE SHAPE OF A SPLIT FAMILY. The shared module is the BOTTOM: everything imports it, it
imports nothing from the family. The entry point keeps the original filename and
re-exports what left it, so outside callers never notice. Two rules follow and both are
REFUSED rather than written: a sibling may not import from the entry point (a cycle,
which presents as a half-initialised module rather than an error), and the shared module
may not reach upward (a dangling name that only mypy sees).

TEN HAZARDS ARE HANDLED, each documented at the line that handles it rather than
restated here. Every one was found by getting it wrong on 28 August 2026, and EVERY ONE
PRODUCED A GREEN RUFF AND A BROKEN SUITE -- which is the combination worth fearing,
because lint says it worked. Search this file for "MEASURED" to read them: header
scanning, statement order, comment attachment, the main guard, cross-destination
references, the entry-point cycle, __all__ for scripts, staged writes, relative imports
inside a package, and shared-module purity.

WHAT THIS CANNOT FIX, so check before planning: some tests copy a single script file
into a temporary directory and run it there, and a script that imports a sibling cannot
survive that however correct the split. The remedy is a change to those tests.

    python split_module.py <spec.json>

The spec names a `source`, an optional `shared` {path, doc, symbols}, and `targets` of
the same shape -- one of which must keep the source's own filename. A target may also
carry `reexport`: names it imports back and lists in __all__.

Two siblings now sit below this file. `split_module_syntax.py` holds everything that
reads the source -- symbol names and line spans, comment-block attachment, header
statements, the reference scan, the main-guard and registration tests -- together with
the docstring rewrapper, the facade builder and `ROOT`. `split_module_render.py` holds
`render`, which assembles one destination's text from those parts. `main` stays here,
because the spec, the refusals, the layering ranks and the staged write are the same
decision and belong in one place."""

from __future__ import annotations
import ast
import json
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from split_module_syntax import (
    ROOT,
    comment_start,
    facade_block,
    header_nodes,
    is_main_guard,
    referenced,
    registers_a_family_symbol,
    resolves_names_dynamically,
    spans,
    wrap_docstring,
)

from split_module_render import (
    render,
)

from split_module_syntax import (
    DYNAMIC_LOOKUP,
    bound_names,
    symbol_names,
)

__all__ = [
    "DYNAMIC_LOOKUP",
    "ROOT",
    "bound_names",
    "comment_start",
    "facade_block",
    "header_nodes",
    "is_main_guard",
    "main",
    "referenced",
    "registers_a_family_symbol",
    "render",
    "resolves_names_dynamically",
    "spans",
    "symbol_names",
    "wrap_docstring",
]


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    source = (ROOT / spec["source"]).read_text(encoding="utf-8")
    # A module that never resolves a name dynamically cannot depend on a symbol only spelled in
    # a string, so a string mention there is prose and must not refuse a plan. One that DOES is
    # taken at its word and the conservative reading is kept.
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    dynamic = resolves_names_dynamically(tree)
    all_spans = spans(tree, lines)
    head = header_nodes(tree)

    shared = spec.get("shared")
    groups = ([shared] if shared else []) + spec["targets"]
    assigned = [s for g in groups for s in g["symbols"]]
    missing = sorted(set(all_spans) - set(assigned))
    unknown = sorted(set(assigned) - set(all_spans))
    if missing or unknown:
        print("REFUSING: unassigned=" + str(missing) + " unknown=" + str(unknown))
        return 1
    if len(assigned) != len(set(assigned)):
        print("REFUSING: a symbol was assigned to two destinations")
        return 1

    shared_names: list[str] = shared["symbols"] if shared else []

    # NOTHING is written until every destination has rendered and every check has passed.
    # MEASURED 28 August 2026 on src/consilient/beta.py: the tool wrote the entry point, then
    # refused on the next target, and left a half-split package on disk that had to be restored
    # by hand. A refusal must leave the tree exactly as it found it.
    pending: list[tuple[str, str]] = []
    # RELATIVE inside a package, bare outside it. MEASURED 28 August 2026: the shared-helpers
    # import was always emitted bare, so splitting src/consilient/recall.py produced
    # `from recall_candidates import ...` inside a package and mypy --strict reported
    # "Cannot find implementation or library stub for module named recall_candidates". The
    # facade import was already package-aware; this one had been missed.
    module = None
    # name -> the destination stem that will define it, for facade re-exports
    home: dict[str, str] = {}
    for group in groups:
        for name in group["symbols"]:
            home[name] = Path(group["path"]).stem

    if shared:
        shared_dir = (ROOT / shared["path"]).parent
        prefix = "." if (shared_dir / "__init__.py").is_file() else ""
        module = prefix + Path(shared["path"]).stem
    if shared:
        # The shared module is the BOTTOM of the family: everything imports it and it imports
        # nothing from the family. If one of its symbols reaches for a symbol that landed in a
        # sibling, that is a layering violation, and it is silent -- MEASURED 28 August 2026,
        # where it produced `Name "_rebuild" is not defined` in projection_store.py and
        # `pack_events` in recall_candidates.py, only under mypy, after ruff had passed.
        # Refused in the same shape as the cycle refusal so the resolver can repair it by
        # pulling the named symbols down into `shared` as well.
        shared_uses = referenced(
            lines, [all_spans[s] for s in shared_names], strings=dynamic
        )
        stranded = sorted(
            n
            for n in shared_uses
            if n in home
            and n not in shared_names
            and home[n] != Path(shared["path"]).stem
        )
        if stranded:
            print(
                "REFUSING: "
                + shared["path"]
                + " needs "
                + str(stranded)
                + " which the plan leaves above it. The shared module may import nothing from "
                "the family; move these down into it."
            )
            return 1
        out = render(
            '"""' + wrap_docstring(shared["doc"]) + '"""',
            head,
            lines,
            shared_names,
            all_spans,
            [],
            None,
            "",
            False,
        )
        pending.append((shared["path"], out))

    # A DESTINATION MAY IMPORT ONLY FROM DESTINATIONS BELOW IT. The spec lists them in
    # dependency order -- shared, then each target, then the entry point which keeps the source
    # filename -- and that order is the whole safety argument: a split is safe because it is a
    # LAYERING, and a layering with an upward edge is a cycle.
    #
    # MEASURED 28 August 2026. The facade counts a name spelled inside a string as a reference,
    # which is right for imports and wrong for direction, so promote_checks.py was given an
    # import from a destination above it and 76 test modules died at collection with "cannot
    # import name 'Candidate' from partially initialized module". A code reference upward is
    # refused below; a string mention upward needs no import at all, so it is dropped here.
    rank: dict[str, int] = {}
    if shared:
        rank[Path(shared["path"]).stem] = 0
    for position, item in enumerate(spec["targets"], start=1):
        rank[Path(item["path"]).stem] = (
            len(spec["targets"]) + 1 if item["path"] == spec["source"] else position
        )

    for target in spec["targets"]:
        dest = ROOT / target["path"]
        package = (dest.parent / "__init__.py").is_file()
        unknown = [n for n in target.get("reexport", []) if n not in home]
        if unknown:
            print("REFUSING: reexport names no destination defines: " + str(unknown))
            return 1

        # Every name this destination USES that now lives in a different destination must be
        # imported, not only the ones a plan happened to list. MEASURED 28 August 2026 on
        # scripts/bench_overhead.py: only the entry point was given imports, so the sibling
        # overhead_meter.py referenced ROOT, Hooks, default_admit and StreamSample from two
        # other siblings and came out with eight F821. Cross-destination references are
        # derivable, so deriving them beats asking a plan to enumerate them correctly.
        # The HEADER counts too, not only the symbols. A source that does
        # `sys.path.insert(0, str(ROOT / "src"))` at module level has that statement copied into
        # every destination, and ROOT is a symbol that lands in exactly one of them -- measured
        # on scripts/bench_overhead.py, where three siblings came out with F821 ROOT.
        # The main guard is stripped from every destination but the entry point, so its
        # `main()` call must not count as a reference either -- otherwise every sibling looks
        # like it needs `main` from the entry and the cycle check below refuses a plan that is
        # perfectly sound. Measured as four false refusals on 28 August 2026.
        keep_guard = target["path"] == spec["source"]
        header_spans = [
            (comment_start(lines, n.lineno), n.end_lineno or n.lineno)
            for n in head
            if not isinstance(n, (ast.Import, ast.ImportFrom))
            and (keep_guard or not is_main_guard(n))
            # Same reasoning one statement over: `render` gives a registration call to the entry
            # point alone, so counting it as a reference here refuses a plan the tool then would
            # have written correctly. Measured on work_items.py, whose trailing
            # `_register_transition_validator()` refused its own sound layering.
            and (keep_guard or not registers_a_family_symbol(n, lines, set(all_spans)))
        ]
        spans_here = [all_spans[s] for s in target["symbols"]] + header_spans
        uses = referenced(lines, spans_here)
        cross = {
            n
            for n in uses
            if n in home and home[n] != dest.stem and n not in target["symbols"]
        }
        # The facade above may over-import; the refusal below may not over-refuse.
        cross_in_code = {
            n
            for n in referenced(lines, spans_here, strings=dynamic)
            if n in home and home[n] != dest.stem and n not in target["symbols"]
        }
        # A sibling may never import from the entry point: the entry imports the siblings, so
        # that is a cycle. MEASURED 28 August 2026 on scripts/build_anchor_set.py -- the auto
        # cross-import produced `from build_anchor_set import ...` inside anchor_set_drift.py,
        # and every test then failed with "cannot import name 'main'", because under circular
        # initialisation the entry module has not yet reached its own `def main`. A symbol two
        # destinations need belongs in `shared`; refusing says so, instead of writing a file
        # that imports fine as a script and explodes under the suite.
        if target["path"] != spec["source"]:
            owed = sorted(
                n
                for n in cross_in_code
                if rank.get(home[n], -1) >= rank.get(dest.stem, 0)
            )
            if owed:
                print(
                    "REFUSING: "
                    + target["path"]
                    + " needs "
                    + str(owed)
                    + " which the plan leaves in the entry point "
                    + spec["source"]
                    + ". Move them into `shared`, which every destination may import."
                )
                return 1
        wanted_here = cross | {
            n for n in target.get("reexport", []) if home.get(n) != dest.stem
        }
        # Over-importing is free only when the import is legal, and an import from above is
        # never legal. The first version of this filter excluded the entry point alone, which
        # left sibling-to-sibling edges free to point upward -- see the rank comment above.
        here = rank.get(dest.stem, 0)
        wanted_here = {n for n in wanted_here if rank.get(home.get(n, ""), -1) < here}
        reexport = sorted(wanted_here)
        facade = facade_block(reexport, home, target["symbols"], package)
        out = render(
            '"""' + wrap_docstring(target["doc"]) + '"""',
            head,
            lines,
            target["symbols"],
            all_spans,
            shared_names,
            module,
            facade,
            target["path"] == spec["source"],
        )
        pending.append((target["path"], out))
    for path, out in pending:
        (ROOT / path).write_text(out, encoding="utf-8", newline=chr(10))
        print("wrote " + path + " (" + str(out.count(chr(10))) + " lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

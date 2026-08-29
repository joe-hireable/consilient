"""Assemble one destination file: its docstring, the header it still needs, and the
symbol bodies it takes, in source order.

Placement is by line number rather than by category, so a destination reads the way its
source did -- imports interleaved with definitions exactly where the author put them,
each chunk carrying the comment block that introduces it, and consecutive imports left
tight as a block rather than spaced apart. Header statements are dropped when the
destination uses none of the names they bind, with one permanent exception: `from
__future__ import annotations` is kept everywhere, because it changes how the whole
module is compiled rather than binding a name anything reads. A destination that is not
the entry point also loses the `__main__` guard and any bare call reaching a symbol of
the family, both of which belong to the entry point alone.

Two blocks are inserted rather than copied. The import of the shared module goes before
the first statement that needs it but never below the first definition, the earlier of
the two being the only position that satisfies both E402 and the bootstrap case. The
facade goes after the module's own imports and before its first definition, where a
reader looks for the public surface and where mypy wants the explicit re-export.

This layer chooses nothing and touches no filesystem. It is handed a docstring, a symbol
list and a facade already built, and it returns a string; whether that string is ever
written is settled above, after every destination has rendered and every check has
passed."""

from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from split_module_syntax import (
    bound_names,
    comment_start,
    is_main_guard,
    referenced,
    registers_a_family_symbol,
)


__all__ = [
    "bound_names",
    "comment_start",
    "is_main_guard",
    "referenced",
    "registers_a_family_symbol",
    "render",
]


def render(
    docstring: str,
    head: list[ast.stmt],
    lines: list[str],
    symbols: list[str],
    all_spans: dict[str, tuple[int, int]],
    shared_names: list[str],
    module: str | None,
    facade: str = "",
    is_entry: bool = True,
) -> str:
    def text_of(lo: int, hi: int) -> str:
        return "".join(lines[lo - 1 : hi]).rstrip("\n")

    if not is_entry:
        # The main guard belongs to the entry point alone. MEASURED 28 August 2026 on
        # .github/scripts/check_merge_acceptance.py: it defines no symbol, so it was copied into
        # every destination, and each sibling ended with `raise SystemExit(main())` against a
        # `main` it does not define -- F821, and a module that would exit if anyone ran it.
        head = [n for n in head if not is_main_guard(n)]
        head = [
            n for n in head if not registers_a_family_symbol(n, lines, set(all_spans))
        ]

    wanted = [all_spans[s] for s in symbols]
    always = [n for n in head if not isinstance(n, (ast.Import, ast.ImportFrom))]
    always_spans = [(n.lineno, n.end_lineno or n.lineno) for n in always]

    used = referenced(lines, wanted) | referenced(lines, always_spans)

    chunks: list[tuple[int, str, bool]] = []
    imports: list[bool] = []
    for node in head:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # the module docstring, replaced per destination
        names = bound_names(node)
        # A __future__ import is ALWAYS kept, in every destination. It binds a name nothing ever
        # reads, so the usage filter below drops it -- MEASURED 28 August 2026, on every one of
        # the twenty-odd files split that day. `from __future__ import annotations` is not an
        # import in the ordinary sense; it changes how the whole module is compiled, so losing it
        # makes every annotation eagerly evaluated. That was silent until a class annotated its
        # own type: `def from_mapping(cls, ...) -> ImpactContract` inside `class ImpactContract`
        # became F821, and would have been a NameError at import in a file ruff did not scan.
        if (
            not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
            and names
            and not any(n in used for n in names)
        ):
            continue
        begin = comment_start(lines, node.lineno)
        chunks.append((begin, text_of(begin, node.end_lineno or node.lineno), False))
    for lo, hi in wanted:
        chunks.append((lo, text_of(lo, hi), True))
    chunks.sort(key=lambda c: c[0])

    body = [c[1] for c in chunks]

    # An import block reads as a block. ruff format normalises blank lines around
    # definitions but leaves import spacing alone, so separating every statement with a
    # blank line here would ship 58 files with visibly scruffy headers.
    def is_import(text: str, is_symbol: bool) -> bool:
        if is_symbol:
            return False
        # A chunk may now open with the comment block introducing it, so look past those.
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            return bool(re.match(r"^(import|from)\s", stripped))
        return False

    imports = [is_import(text, sym) for _, text, sym in chunks]
    # parallel to `body`, so an insertion above does not move the facade below a definition
    syms = [sym for _, _, sym in chunks]
    if module and shared_names:
        needed = sorted(n for n in shared_names if n in used)
        if needed:
            imp = (
                "from "
                + module
                + " import (\n"
                + "".join("    " + n + ",\n" for n in needed)
                + ")"
            )
            # Before the first statement that needs it, but never later than the first
            # definition -- an import sitting between two test functions is E402, and the
            # bootstrap case (a sys.path line referencing a shared ROOT) needs it earlier
            # still. The earlier of the two is the only position that satisfies both.
            first_use = next(
                (
                    i
                    for i, (_, txt, _) in enumerate(chunks)
                    if any(re.search(r"\b" + re.escape(n) + r"\b", txt) for n in needed)
                ),
                len(body),
            )
            first_def = next(
                (i for i, (_, _, is_sym) in enumerate(chunks) if is_sym), len(body)
            )
            at = min(first_use, first_def)
            body.insert(at, imp)
            imports.insert(at, True)
            syms.insert(at, False)

    if facade:
        # After the module's own imports, before its first definition -- where a reader looks
        # for the public surface, and where mypy wants the explicit re-export.
        #
        # But NEVER later than the first statement that uses one of the re-exported names. A
        # non-defining header statement can need one: scripts/dispatch.py runs
        # `sys.path.insert(0, str(ROOT / "src"))` at module level, ROOT moved to a sibling, and
        # placing the facade before the first DEFINITION put it after that line -- F821, and a
        # NameError for anyone importing the module. Measured 28 August 2026.
        facade_names = {
            alias.name
            for node in ast.parse(facade).body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        first_def = next((i for i, is_sym in enumerate(syms) if is_sym), len(body))
        first_need = next(
            (
                i
                for i, text in enumerate(body)
                if not imports[i]
                and any(
                    re.search(r"\b" + re.escape(n) + r"\b", text)
                    for n in facade_names
                )
            ),
            len(body),
        )
        at = min(first_def, first_need)
        body.insert(at, facade)
        imports.insert(at, False)
        syms.insert(at, False)

    out = docstring.rstrip("\n")
    if body:
        out += "\n\n" + body[0]
        for i in range(1, len(body)):
            # Consecutive imports read as one block -- but an import introduced by its own
            # comment gets the blank line back, or the comment crowds the line above it.
            tight = (
                imports[i] and imports[i - 1] and not body[i].lstrip().startswith("#")
            )
            joiner = "\n" if tight else "\n\n"
            out += joiner + body[i]
    return out.rstrip("\n") + "\n"

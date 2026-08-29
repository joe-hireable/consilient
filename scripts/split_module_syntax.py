"""What the splitter can see in a module, and the small pieces of Python it writes back
out.

Every query here answers a question about source text. Which names a top-level statement
defines; where the comment block introducing it begins; the first and last line of each
symbol, decorators and comments included; which statements define no symbol and so form
the header; which bare names a stretch of lines reaches for; and whether a trailing
statement is the `__main__` guard or a registration call that touches a symbol of the
family. Two go the other way and emit text instead: the rewrapper that fits prose to the
repository's 88 columns while leaving an indented table alone, and the facade builder
that gives a decomposed module back its public surface as imports plus an explicit
`__all__`. `ROOT` is the tree all of it reads from, and `SPLIT_ROOT` redirects that at a
scratch copy, which is how each defect recorded in the comments below was reproduced.

Nothing here decides where a symbol goes. This layer reads no plan, resolves no layering
and writes no file; the layers above it ask questions and act on the answers. That
separation is why the reference scan takes a `strings` flag rather than holding a policy
of its own -- whether an identifier spelled inside a string constant counts is a
question the caller is asking, and the same scan gives opposite and equally correct
answers to generating imports and to judging a plan legal.

The refusals live above too. What this layer owes them is that its answers be exact,
because every one of them is a line number or a set of names that some later check
trusts absolutely."""

from __future__ import annotations
import ast
import os
import re
import sys
import textwrap
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# SPLIT_ROOT points this at a scratch tree, which is how each defect below was reproduced.
ROOT = Path(os.environ.get("SPLIT_ROOT", Path(__file__).resolve().parents[1]))


def symbol_names(node: ast.stmt) -> list[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    # A top-level `if` that DEFINES something is a definition, not a header. MEASURED
    # 29 August 2026: `if sys.platform == "win32": _TRANSACTION_OPEN_FLAGS = ...` bound no
    # name at top level, so header_nodes called it a header and every destination got a
    # copy -- the durability contract landed in sixteen files, fourteen of which never
    # open a descriptor. Change the flags and you edit sixteen files and miss one.
    #
    # Imports are deliberately excluded: `if TYPE_CHECKING: from x import Y` binds a name
    # every destination needs for its annotations, and moving that block to one file would
    # break the rest. A block that only imports stays a header.
    if isinstance(node, (ast.If, ast.Try)):
        defined: list[str] = []
        for inner in ast.walk(node):
            if inner is node:
                continue
            defined.extend(symbol_names(inner) if isinstance(inner, ast.stmt) else [])
        return sorted(dict.fromkeys(defined))
    return []


def comment_start(lines: list[str], first: int) -> int:
    """The first line of the comment block introducing the statement at `first` (1-based).

    Applies to EVERY top-level statement, symbols and header imports alike. Two measurements on
    28 August 2026 shaped this:

      * Stopping at the first blank line orphaned every block written in PEP 8 style, silently
        dropping the ten-line record of the 24 August worktree incident -- "eleven commits of
        finished work were stranded and one unit was built twice". Nothing pointed at it; the
        comment was simply gone. Hence the blank-gap skip.
      * Applying this to symbols only still dropped "# PRODUCT, not instance. Nothing below names
        an account, a credential or a real balance." -- a privacy boundary sitting above an
        `import`, which is a header node emitted by AST line range alone. Hence every statement.

    In this repository the prose IS the forensic record, so the bias is to absorb: a banner pulled
    into the file it introduces is harmless, a deleted incident report is not.
    """
    # Absorb the WHOLE run of comments and blanks above the statement, not one paragraph of it.
    # A third measurement, 28 August 2026: skipping the gap once still stopped at the blank line
    # INSIDE a block, so splitting scripts/dispatch.py kept the paragraph immediately above
    # START_WINDOW_S and orphaned the thirteen lines above that -- the BU-0 supervision floor,
    # carrying "six of six failed dispatches died at startup" [measured, F-13], the 17% usage a
    # provider sat at for two days, and the Kubernetes/systemd/s6 comparison the bar was set
    # against. verify_split reported fourteen dropped comments; nothing else would have.
    i = first - 2
    while i >= 0 and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        if lines[i].lstrip().startswith("#"):
            first = i + 1
        i -= 1
    return first


def spans(tree: ast.Module, lines: list[str]) -> dict[str, tuple[int, int]]:
    """name -> (first line, last line), 1-based inclusive, decorators and comments included."""
    out: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        names = symbol_names(node)
        if not names:
            continue
        start = node.lineno
        decorators = getattr(node, "decorator_list", None)
        if decorators:
            start = min(d.lineno for d in decorators)
        start = comment_start(lines, start)
        for name in names:
            out[name] = (start, node.end_lineno or node.lineno)
    return out


def is_main_guard(node: ast.stmt) -> bool:
    """The `if __name__ == "__main__":` trailer, which belongs to the entry point alone."""
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.comparators) != 1:
        return False
    left, right = test.left, test.comparators[0]
    return (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )


def header_nodes(tree: ast.Module) -> list[ast.stmt]:
    """Every top-level statement that defines no symbol, wherever it sits in the file."""
    return [n for n in tree.body if not symbol_names(n)]


def bound_names(node: ast.stmt) -> list[str]:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return [(a.asname or a.name).split(".")[0] for a in node.names]
    return []


DYNAMIC_LOOKUP = ("globals", "getattr", "eval", "vars", "locals")


def resolves_names_dynamically(tree: ast.Module) -> bool:
    """Whether the module actually CALLS one of the dynamic-lookup builtins.

    Asked of the syntax tree, not of the text. MEASURED 28 August 2026: the substring test this
    replaces read its own source, and THIS file defines the sentinel list, so it declared itself
    dynamic, turned on string scanning, found the word `main` in its own prose, and refused to
    split itself over a dependency that exists only in a comment.
    """
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id in ("globals", "locals", "vars", "eval"):
            return True
        # `getattr(obj, "literal")` is ordinary attribute access and says nothing about
        # namespaces -- `getattr(node, "decorator_list", None)` in this very file is an AST
        # field read. Only a NON-literal attribute is a name resolved at run time.
        if node.func.id == "getattr" and len(node.args) >= 2:
            if not isinstance(node.args[1], ast.Constant):
                return True
    return False


def referenced(
    source_lines: list[str], chunks: list[tuple[int, int]], strings: bool = True
) -> set[str]:
    """Every bare name mentioned across the given line ranges.

    `strings` decides whether identifiers spelled inside STRING CONSTANTS count. They must, for
    generating imports -- a name reached through `getattr(mod, "thing")` is a real dependency and
    over-importing is free, because ruff --fix drops whatever is unused.

    They must NOT for deciding whether a plan is legal. MEASURED 28 August 2026: four correct
    plans were refused by this, and every one was a word in a string that happens to spell a
    symbol. `projection_schema.py` was told it needed `rejections`, `capability_heads` and four
    more, because `SCHEMA` contains `CREATE TABLE rejections (...)`; `recall_vocabulary.py` was
    told it needed `pack`, because a docstring in it uses the English word. A refusal that fires
    on prose is a refusal that gets worked around, so the caller says which question it is asking.
    """
    used: set[str] = set()
    for lo, hi in chunks:
        text = "".join(source_lines[lo - 1 : hi])
        try:
            sub = ast.parse(text)
        except SyntaxError:
            # A span that starts inside a function -- because `comment_start` reached up to the
            # comment block introducing it -- is indented, and indented source does not parse at
            # module level. Dedent and try again before giving up on the AST.
            try:
                sub = ast.parse(textwrap.dedent(text))
            except SyntaxError:
                # Last resort, and it reads COMMENTS, which the AST never would. When the caller
                # has asked about code, strip them: this file own comments discuss `main`, and
                # the fallback saw the word and refused to split this module over a dependency
                # that exists only in prose.
                if not strings:
                    text = re.sub("#[^" + chr(10) + "]*", "", text)
                used.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
                continue
        for node in ast.walk(sub):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                root: ast.expr = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    used.add(root.id)
            elif (
                strings
                and isinstance(node, ast.Constant)
                and isinstance(node.value, str)
            ):
                used.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", node.value))
    return used


def wrap_docstring(doc: str, width: int = 88) -> str:
    """Rewrap prose paragraphs to the repository's 88 columns, leaving layout alone.

    Committed files here cap at 88, which is ruff's default line-length and what every existing
    test module already obeys. A paragraph containing an indented line is left verbatim: that is
    how the measured tables and the small code samples in these docstrings are written, and
    rewrapping one would destroy the thing it was drawn to show.
    """
    out: list[str] = []
    first = True
    for para in doc.strip("\n").split("\n\n"):
        lines = para.split("\n")
        # A paragraph carrying a setext underline is LAYOUT, not prose, and rewrapping it joins
        # the heading to its dashes. scripts/b4_pool.py's `main` parses its own __doc__, splitting
        # on "ADMISSION RULE" and its underline to embed the admission rule in a published
        # artefact, so reflowing that heading would silently change what the sweep publishes --
        # raised by the agent documenting the split before it was applied, on 28 August 2026.
        underlined = any(
            line.strip() and set(line.strip()) <= {"-", "="} and len(line.strip()) > 3
            for line in lines
        )
        if underlined or any(line[:1].isspace() for line in lines) or not para.strip():
            out.append(para)
        else:
            flat = " ".join(line.strip() for line in lines)
            # The opening `"""` occupies three columns of the very first line.
            filled = textwrap.fill(
                flat,
                width=width,
                initial_indent="   " if first else "",
                # Never break a hyphenated word across lines. textwrap does it by default, and it
                # is wrong for this repository: prose here IS the record, and a term broken
                # across lines at its hyphen stops being greppable and reads with a space in
                # the middle once flattened.
                # flattened. MEASURED 28 August 2026 on .harness/build_loop.py, where
                # verify_split reported the line lost -- correctly, because the text had changed.
                break_on_hyphens=False,
            )
            out.append(filled[3:] if first else filled)
        first = False
    return "\n\n".join(out)


def facade_block(
    reexport: list[str], home: dict[str, str], own: list[str], package: bool
) -> str:
    """Imports plus an explicit __all__, so a split product module keeps its public surface.

    Splitting src/consilient/events.py would otherwise break twenty-one importers that say
    `from consilient.events import ...`. The original module therefore re-exports what moved.

    `__all__` rather than the redundant-alias form because mypy.ini sets strict = True, which
    implies no_implicit_reexport, and __all__ additionally documents the public surface of a
    module being decomposed. It is behaviour-neutral here: nothing in the repository does
    `import *` and no test reads __all__, both checked 28 August 2026.
    """
    if not reexport:
        return ""
    by_home: dict[str, list[str]] = {}
    for name in reexport:
        by_home.setdefault(home[name], []).append(name)
    out: list[str] = []
    for stem in sorted(by_home):
        prefix = "." if package else ""
        names = sorted(by_home[stem])
        out.append(
            "from "
            + prefix
            + stem
            + " import (\n"
            + "".join("    " + n + ",\n" for n in names)
            + ")"
        )
    # Emitted whenever anything is re-exported, script or package alike.
    #
    # For a package it satisfies mypy's no_implicit_reexport. For a SCRIPT it does something
    # more immediately necessary: it stops ruff deleting the re-imports as unused. MEASURED 28
    # August 2026 on scripts/exp50_faults.py -- the entry point imported parse_diff_paths back
    # from its sibling, nothing inside the file referenced it, `ruff check --fix` removed it as
    # F401, and tests/test_exp50_faults.py died on AttributeError at collection. The test is an
    # importer ruff cannot see, and naming the surface is what makes the re-export intentional
    # rather than a leftover. An earlier version made this package-only, on the reasoning that a
    # script has no importers to satisfy; that reasoning forgot the suite.
    _ = package
    public = sorted(set(reexport) | {n for n in own if not n.startswith("_")})
    out.append("__all__ = [\n" + "".join('    "' + n + '",\n' for n in public) + "]")
    return "\n\n".join(out)


def registers_a_family_symbol(
    node: ast.stmt, lines: list[str], family: set[str]
) -> bool:
    """A bare top-level call that reaches a symbol this module defines.

    Such a statement is REGISTRATION -- `_register_transition_validator()` at the foot of
    work_items.py -- and it belongs to the entry point alone, for two reasons. It runs its side
    effect once per destination that carries it, and in a sibling below the definition it cannot
    even resolve the name. MEASURED 28 August 2026: it landed in work_items_vocabulary.py and
    mypy reported `Name "_register_transition_validator" is not defined`, which is the lucky
    outcome; had it resolved, the validator would have been registered five times.

    A bare call that touches NO family symbol is the opposite case and must be copied everywhere:
    the `sys.path.insert(...)` bootstrap a non-package sibling needs to be importable at all. So
    the test is what the call reaches, not that it is a call.
    """
    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
        return False
    # What is CALLED, not what is merely mentioned. An earlier version asked whether the
    # statement REFERENCED any family symbol, which is true of
    # `sys.path.insert(0, str(ROOT / "src"))` -- infrastructure every destination needs, dropped
    # from all of them because ROOT had moved to a sibling. MEASURED 28 August 2026:
    # scripts/dispatch.py then imported `consilient` before src reached sys.path and resolved it
    # from a stale copy in site-packages rather than from the working tree.
    del lines
    func: ast.expr = node.value.func
    while isinstance(func, ast.Attribute):
        func = func.value
    return isinstance(func, ast.Name) and func.id in family

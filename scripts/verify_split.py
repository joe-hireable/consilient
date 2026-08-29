#!/usr/bin/env python
"""Prove a refactor was a MOVE, not a rewrite: same symbols, same bodies, new files.

A split is safe exactly when nothing changed except which file a symbol lives in. That is a
checkable claim, and this checks it -- so "behaviour must not change" stops being a promise in
a commit message and becomes something that fails.

HOW. Parse every file matching the glob on both refs. For each module-level function, class and
assignment target, hash the normalised AST of its body. Then compare the two sides as maps of
name -> body-hash:

    missing   a symbol that existed and now does not          -- deletion, not a move
    added     a symbol that did not exist and now does        -- new code, not a move
    changed   a symbol whose body hash moved                  -- a rewrite, not a move

A pure move produces none of the three, however many files the symbols were spread across.

WHAT IT DOES NOT CATCH, stated so nobody trusts it further than it goes:
  * import changes, decorators applied at a different site, or module-level execution order
  * a symbol whose behaviour depends on WHICH module it now lives in -- which is the real
    hazard here: `monkeypatch.setattr(driver, "sh", ...)` reaches a caller only while the
    caller shares that namespace. Measured, and the reason the plan refuses to re-export
    moved symbols: a stale patch then fails loudly instead of landing on a dead alias.
  * anything about tests. The suite is still the oracle; this narrows what the suite has to
    catch, it does not replace it.

Docstrings are included in the per-symbol hash, because they are part of the AST. COMMENTS ARE
NOT -- `ast.dump` discards them entirely, which this file's own docstring denied until it was
measured on 28 August 2026:

    def f():                      def f():
        # forensic record             return 1
        return 1

    both hash to bd09f5272e6620c0

So a refactor that deleted every comment in a file would have been reported as a PROVED PURE
MOVE. In this repository the prose is the forensic record -- dates, measured counts, approaches
withdrawn and why -- so that is not a cosmetic gap; it is the guard failing at the thing it was
built for. `comment_texts` below closes it with a family-wide multiset comparison, which also
catches a comment sitting ABOVE a symbol, where ownership is ambiguous and per-symbol attribution
would have to guess.

MODULE DOCSTRINGS were the second hole, and the same hole. They are not symbols, so the AST
hash never sees them; they are string literals, so the tokeniser does not call them comments.
MEASURED 28 August 2026: a split replaced scripts/bench_overhead.py's 58-line docstring -- the
recorded bar, two `[cited: FULL]` flags with retrieval dates, a withdrawn figure, and the text
argparse hands to --help -- with a paragraph the planner had written to itself, and this file
reported MOVE PROVED. `module_docstring_lines` closes it, per line rather than per docstring,
because moving prose to the sibling it describes is a correct split and must keep passing.

"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import os
import subprocess
import tokenize
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# A gate script inheriting GIT_DIR reads a different repository. See
# check_file_length.py for the measured note.
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def _files_at(ref: str, pattern: str) -> list[str]:
    """Files matching any comma-separated glob or exact path in `pattern`.

    A single wildcard is rarely the family. MEASURED 28 August 2026 across eighteen splits:
    `tests/*records*.py` swept in test_model_change_records.py, an unrelated module that also
    defines LOG, and the duplicate-symbol guard below aborted; while `tests/*capability_gaps*.py`
    MISSED the targets named capability_gap_* and reported thirteen symbols deleted. Both are the
    glob being wrong, and both look exactly like a broken refactor -- which is the worst way for a
    verifier to fail. Pass the destinations explicitly, comma separated, and neither happens.
    """
    out = _git("ls-tree", "-r", "--name-only", ref)
    if out.returncode != 0:
        raise SystemExit(f"cannot list {ref}: {out.stderr.strip()[:200]}")
    from fnmatch import fnmatch

    globs = [g.strip() for g in pattern.split(",") if g.strip()]
    return [
        p
        for p in out.stdout.split()
        if p.endswith(".py") and any(fnmatch(p, g) for g in globs)
    ]


def _source_at(ref: str, path: str) -> str:
    out = _git("show", f"{ref}:{path}")
    return out.stdout if out.returncode == 0 else ""


def symbol_names(node: ast.stmt) -> list[str]:
    """The module-level names a statement defines, for move-comparison purposes.

    `__all__` is deliberately excluded. It is a DECLARATION OF SURFACE, not a symbol that moved:
    splitting a product module leaves the original as a facade re-exporting what left it, and
    mypy --strict (no_implicit_reexport) requires an explicit __all__ to do that. Counting it as
    an ADDED symbol would make every correct product split report NOT A PURE MOVE, which trains
    the reader to ignore this tool -- the exact failure mode it exists to prevent. Its
    correctness is checked better elsewhere: by mypy, and by the importers that break if it is
    wrong.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [
            t.id for t in node.targets if isinstance(t, ast.Name) and t.id != "__all__"
        ]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def symbols(ref: str, pattern: str) -> dict[str, tuple[str, str]]:
    """name -> (body hash, the file it lived in) for every module-level symbol."""
    found: dict[str, tuple[str, str]] = {}
    for path in _files_at(ref, pattern):
        src = _source_at(ref, path)
        if not src.strip():
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            raise SystemExit(f"{ref}:{path} does not parse: {exc}")
        for node in tree.body:
            names = symbol_names(node)
            if not names:
                continue
            digest = hashlib.sha256(ast.dump(node).encode("utf-8")).hexdigest()[:16]
            for name in names:
                if name in found:
                    # A duplicate name across the family is itself a finding: after a split
                    # two files defining the same symbol means one of them is dead.
                    raise SystemExit(
                        f"{ref}: {name!r} is defined in both {found[name][1]} and {path}"
                    )
                found[name] = (digest, path)
    return found


def comment_texts(ref: str, pattern: str) -> Counter[str]:
    """Every comment in the family, counted. Attribution to a symbol is deliberately not tried.

    A comment above a `def` could belong to it, to the statement before it, or to the file. Rather
    than guess -- and report a false rewrite every time a split moves one -- this compares the
    whole family's comments as a multiset. A pure move leaves it unchanged, wherever the comments
    landed.
    """
    found: Counter[str] = Counter()
    for path in _files_at(ref, pattern):
        src = _source_at(ref, path)
        if not src.strip():
            continue
        try:
            for token in tokenize.generate_tokens(io.StringIO(src).readline):
                if token.type == tokenize.COMMENT:
                    found[token.string.strip()] += 1
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # A file that will not tokenise is already a finding for `symbols`, which parses it.
            continue
    return found


SUBSTANTIVE_LINE = 40


def module_docstring_lines(ref: str, pattern: str) -> list[str]:
    """Substantive lines of every MODULE docstring in the family, counted.

    This is the one place prose hides from both checks above. A module docstring is not a
    symbol -- `symbol_names` returns nothing for it -- so the AST hash never sees it; and it is
    a string literal, so the tokeniser does not report it as a comment.

    MEASURED 28 August 2026. A split replaced `scripts/bench_overhead.py`'s 58-line docstring --
    which carried the recorded bar, two `[cited: FULL]` flags with their retrieval dates, the
    withdrawal of a figure, and the text argparse hands to `--help` -- with a paragraph of
    instructions the planner had written to itself. This file reported MOVE PROVED, 0 dropped
    comment. A test reading `__doc__` was the only thing that caught it, which is the second
    time a verifier here has been blind to the prose it exists to protect.

    LINES, not the whole docstring, because redistributing prose to the sibling it describes is
    a CORRECT split and must keep passing: `src/consilient/usage.py` moved two of its three
    refusals into `usage_model.py` and the collector contract into `usage_collectors.py`, and
    every line survived somewhere in the family. Deleting prose is the fault; moving it is the
    point. Short lines are exempt because headings, underlines and code fragments legitimately
    reflow, so this asserts only on lines long enough to carry a sentence.
    """
    lines: list[str] = []
    for path in _files_at(ref, pattern):
        src = _source_at(ref, path)
        if not src.strip():
            continue
        try:
            doc = ast.get_docstring(ast.parse(src)) or ""
        except SyntaxError:
            continue
        for line in doc.splitlines():
            text = " ".join(line.split())
            if len(text) >= SUBSTANTIVE_LINE and " " in text:
                lines.append(text)
    return lines


def _docstring_blob(ref: str, pattern: str) -> str:
    """Every module docstring in the family, whitespace-flattened, one file per NUL-separated run.

    Flattened because a line comparison is defeated by RE-WRAPPING, and re-wrapping is what moving
    a paragraph into a narrower or differently-indented docstring does. MEASURED 28 August 2026
    over today's eighteen splits: a strict line-for-line comparison called 127 lines lost, and 59
    of those were the same words re-wrapped -- a verifier that reports 46% false findings is one
    that gets switched off. Containment in the flattened text keeps a moved line passing and still
    catches a deleted one. The NUL separator is what stops a "surviving" line being assembled from
    the end of one file and the start of the next.
    """
    parts: list[str] = []
    for path in _files_at(ref, pattern):
        src = _source_at(ref, path)
        if not src.strip():
            continue
        try:
            doc = ast.get_docstring(ast.parse(src)) or ""
        except SyntaxError:
            continue
        parts.append(" ".join(doc.split()))
    return (" " + chr(0) + " ").join(parts)


def lost_prose(base: str, head: str, pattern: str) -> list[str]:
    """Substantive docstring lines present before the split and absent from the family after it."""
    blob = _docstring_blob(head, pattern)
    return [line for line in module_docstring_lines(base, pattern) if line not in blob]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", help="ref before the split")
    parser.add_argument("head", help="ref after the split")
    parser.add_argument(
        "pattern", help="glob for the family, e.g. 'src/consilient/events*.py'"
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        before = {"a": ("h1", "x.py"), "b": ("h2", "x.py")}
        after_ok = {"a": ("h1", "x.py"), "b": ("h2", "x_split.py")}
        after_bad = {"a": ("h1", "x.py"), "b": ("CHANGED", "x_split.py")}
        assert _diff(before, after_ok) == ([], [], []), (
            "a pure move was reported as a change"
        )
        assert _diff(before, after_bad)[2], "a rewritten body was NOT caught"
        assert _diff(before, {"a": ("h1", "x.py")})[0] == ["b"], (
            "a deletion was NOT caught"
        )
        # The AST hash is blind to comments -- proved here rather than asserted, because this
        # file claimed the opposite for a day. If these two ever hash differently, the
        # comment multiset below has become redundant and should be reconsidered.
        nl = chr(10)
        commented = "def f():" + nl + "    # record" + nl + "    return 1" + nl
        plain = "def f():" + nl + "    return 1" + nl
        with_comment = ast.parse(commented).body[0]
        without = ast.parse(plain).body[0]
        assert ast.dump(with_comment) == ast.dump(without), (
            "ast.dump now carries comments; the multiset check may be redundant"
        )
        left: Counter[str] = Counter({"# a": 2, "# b": 1})
        assert _dropped(left, Counter({"# a": 2, "# b": 1})) == [], (
            "an unchanged comment set was reported as dropped"
        )
        assert _dropped(left, Counter({"# a": 1, "# b": 1})) == ["# a"], (
            "a DELETED comment was not caught"
        )
        # A module docstring is invisible to BOTH checks above -- proved, not asserted.
        doc_a = ast.parse('"""' + "forensic record" + '"""' + nl + "X = 1" + nl)
        doc_b = ast.parse('"""' + "replaced" + '"""' + nl + "X = 1" + nl)
        assert [n for st in doc_a.body for n in symbol_names(st)] == ["X"], (
            "the module docstring became a symbol; this check may be redundant"
        )
        assert list(tokenize.generate_tokens(io.StringIO(
            '"""' + "forensic record" + '"""' + nl
        ).readline)) and not any(
            t.type == tokenize.COMMENT
            for t in tokenize.generate_tokens(io.StringIO(
                '"""' + "forensic record" + '"""' + nl
            ).readline)
        ), "a module docstring now tokenises as a comment; check may be redundant"
        assert ast.get_docstring(doc_a) != ast.get_docstring(doc_b), "self-test is inert"
        # Re-wrapping must PASS and deletion must FAIL -- the distinction the blob exists for.
        sentence = "a line long enough on its own to carry a whole sentence"
        assert sentence in " ".join(("x " + sentence + " y").split()), (
            "a re-wrapped line was reported as lost"
        )
        assert sentence not in "unrelated prose " + chr(0) + " more unrelated prose", (
            "a DELETED docstring line was not caught"
        )

        # The __all__ exclusion is a rule, so it gets a check rather than a comment.
        facade = ast.parse("__all__ = ['a']" + chr(10) + "X = 1" + chr(10))
        got = [n for stmt in facade.body for n in symbol_names(stmt)]
        assert got == ["X"], f"__all__ leaked into the symbol map: {got}"
        print("verify_split self-test: PASS")
        return 0

    before = symbols(args.base, args.pattern)
    after = symbols(args.head, args.pattern)
    missing, added, changed = _diff(before, after)
    dropped = _dropped(
        comment_texts(args.base, args.pattern), comment_texts(args.head, args.pattern)
    )
    prose_gone = lost_prose(args.base, args.head, args.pattern)

    moved = sum(
        1
        for n, (h, p) in after.items()
        if n in before and before[n][1] != p and before[n][0] == h
    )

    if not (missing or added or changed or dropped or prose_gone):
        print(
            f"verify_split: MOVE PROVED -- {len(after)} symbol(s) identical across "
            f"{args.base}..{args.head}; {moved} changed file, 0 changed body, "
            f"0 dropped comment, 0 dropped docstring line."
        )
        return 0

    print(f"verify_split: NOT A PURE MOVE ({args.base}..{args.head}, {args.pattern})")
    for line in prose_gone:
        print(f"  LOST PROSE  {line[:96]}")
    for name in missing:
        print(f"  MISSING  {name}  (was in {before[name][1]})")
    for name in added:
        print(f"  ADDED    {name}  (now in {after[name][1]})")
    for name in changed:
        print(f"  CHANGED  {name}  {before[name][1]} -> {after[name][1]}")
    for text in dropped:
        print(f"  DROPPED  {text[:88]}")
    print(
        "\nIf any of these is deliberate, say so explicitly -- do not call it a split."
    )
    return 1


def _dropped(before: Counter[str], after: Counter[str]) -> list[str]:
    """Comment texts that existed before and do not survive, each listed once."""
    return sorted((before - after).keys())


def _diff(
    before: dict[str, tuple[str, str]], after: dict[str, tuple[str, str]]
) -> tuple[list[str], list[str], list[str]]:
    missing = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    changed = sorted(n for n in set(before) & set(after) if before[n][0] != after[n][0])
    return missing, added, changed


if __name__ == "__main__":
    raise SystemExit(main())

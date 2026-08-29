"""Every attribute a test reaches on a product module must actually be bound there.

THE FAILURE THIS EXISTS TO MAKE LOUD. `monkeypatch.setattr(module, "name", fake)` reaches a caller
only while that caller resolves `name` in the SAME module namespace. Behind a re-exporting facade
it does not, and — this is the whole problem — it does not raise either. The patch lands on an
alias no code reads, the real function runs, and the test goes on asserting something it is no
longer testing.

MEASURED 28 August 2026, while splitting twenty-eight modules. It bit in four different spellings,
each of which had to be found by hand after a test failed for a confusing reason:

    monkeypatch.setattr(coordination, "_process_still_running", ...)   the caller moved
    events.time.sleep                                                  `time` no longer imported
    loop.ROOT = root                                                   an attribute WRITE
    monkeypatch.setattr("consilient.cli.beta_mod.from_connection", ..) a string target

Three of the four were silent in the sense that mattered: the suite failed somewhere downstream,
saying the liveness check returned False, or that a race never ran, rather than saying the patch
had missed. `coordination._process_still_running` was the only one of ninety-nine patch targets
that a split invalidated, and finding it took an AST sweep, because a single-line regex missed a
call spanning two lines.

So this is the sweep, kept. It reads every test module, resolves each alias to the product module
it names, and refuses an attribute that module does not bind. Bindings include imports, because
patching `cli_replay.sqlite3` is legitimate, and include assignments made inside an `if`, because
`_TRANSACTION_OPEN_FLAGS` is set in one arm of an `os.name` test.

There are two checks, because "the name resolves" turned out to be the weaker question. A facade
re-exports what left it, so `coordination` still BINDS `_process_still_running` long after every
caller of it moved away -- the first check passes and the patch is still dead. The second asks
whether the module the patch names actually USES the name. A module that only re-exports it cannot
be affected by patching it, and that is precisely the coordination case.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "consilient"

# Attributes reached on something that merely shares a name with a module alias, and dunders.
EXEMPT_ATTRS = frozenset({"__file__", "__doc__", "__name__", "__all__"})


def _bindings(path: Path) -> set[str]:
    """Every name the module binds at import: definitions, assignments and imports.

    A full walk rather than `tree.body`, because a conditional assignment binds a name just as
    firmly as an unconditional one, and refusing `_TRANSACTION_OPEN_FLAGS` because it is set
    inside an `if os.name == "nt"` would be this check inventing a fault.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            out |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            out |= {a.asname or a.name.split(".")[0] for a in node.names}
    return out


def _module_aliases(tree: ast.Module) -> dict[str, str]:
    """Local name -> product module stem, for every consilient module a test imports."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and "consilient" in node.module
        ):
            for alias in node.names:
                out[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "consilient" in alias.name:
                    stem = alias.name.split(".")[-1]
                    out[alias.asname or stem] = stem
    return out


def _test_files() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "tests/*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    ).stdout.split()
    return [ROOT / rel for rel in listed]


def test_every_attribute_a_test_reaches_is_bound_in_the_module_it_names() -> None:
    known = {p.stem: _bindings(p) for p in PACKAGE.glob("*.py")}
    offenders: list[str] = []

    for path in _test_files():
        # This file quotes the four broken spellings as EXAMPLES, so scanning it flags its own
        # documentation. Skipping it is honest; the alternative is describing the bug without
        # naming it, which is how the knowledge gets lost.
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        aliases = _module_aliases(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                stem = aliases.get(node.value.id)
                if (
                    stem in known
                    and node.attr not in known[stem]
                    and node.attr not in EXEMPT_ATTRS
                ):
                    offenders.append(
                        f"{path.name}:{node.lineno}: {node.value.id}.{node.attr} "
                        f"-- consilient.{stem} does not bind {node.attr!r}"
                    )

        # The string form of a patch target. Anchored on `setattr(` deliberately: a bare
        # "consilient.x.y" in a test is usually DATA -- three of them are payload values naming
        # a reversal that must not resolve, and flagging those would make this check noise.
        for match in re.finditer(r'setattr\(\s*"consilient\.(\w+)\.(\w+)', text):
            stem, attr = match.group(1), match.group(2)
            if stem in known and attr not in known[stem]:
                offenders.append(
                    f'{path.name}: "consilient.{stem}.{attr}" '
                    f"-- consilient.{stem} does not bind {attr!r}"
                )

    assert not offenders, (
        "these tests reach a name the module does not bind. After a split the name usually "
        "lives in a sibling, and a patch aimed here lands on a facade alias that no code "
        "reads -- silently, which is why this check exists:\n  "
        + "\n  ".join(sorted(offenders))
    )


def _uses_in_code(path: Path, name: str) -> bool:
    """Whether the module references `name` anywhere except its imports and its `__all__`.

    A facade re-export binds the name and reads it nowhere, so patching that module changes
    nothing any caller can observe. This is the question the binding check cannot ask.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name) and inner.id == name:
                return True
    return False


def _setattr_targets(tree: ast.Module, aliases: dict[str, str]) -> list[tuple[str, str, int]]:
    """(module stem, attribute, line) for every monkeypatch.setattr(module, "attr", ...)."""
    out: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            stem = aliases.get(node.args[0].id)
            if stem:
                out.append((stem, node.args[1].value, node.lineno))
    return out


def test_no_test_patches_a_name_its_module_only_re_exports() -> None:
    """The dead patch: bound here, used only over there.

    MEASURED 28 August 2026. `coordination` re-exported `_process_still_running` while its one
    caller moved to `coordination_projection`, so the patch bound an alias nothing read, the real
    liveness check ran, and the failure surfaced three assertions later as "returned False where
    it should have returned None". Of ninety-nine patch targets in the suite this was the only one
    a split invalidated -- and nothing but a confusing downstream failure would have said so.
    """
    offenders: list[str] = []
    for path in _test_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        aliases = _module_aliases(tree)
        for stem, attr, lineno in _setattr_targets(tree, aliases):
            module = PACKAGE / f"{stem}.py"
            if not module.is_file() or attr not in _bindings(module):
                continue  # the first test owns that case
            if _uses_in_code(module, attr):
                continue
            # A patch is also live when a caller elsewhere reaches it as `module.attr(...)`,
            # because that attribute lookup happens at call time against the patched object.
            # `projection.build` is exactly this: the entry point re-exports it and never calls
            # it, while the doctor calls `projection.build(log, db)` -- six patches that are
            # perfectly effective and would otherwise be reported dead.
            if any(
                f"{stem}.{attr}" in q.read_text(encoding="utf-8")
                for q in PACKAGE.glob("*.py")
            ):
                continue
            homes = [
                q.stem
                for q in PACKAGE.glob(f"{stem}_*.py")
                if attr in _bindings(q) and _uses_in_code(q, attr)
            ]
            offenders.append(
                f"{path.name}:{lineno}: patches {stem}.{attr}, which {stem} only re-exports"
                + (f" -- it is used in {', '.join(homes)}" if homes else "")
            )
    assert not offenders, (
        "these patches land on a facade alias no code reads, so they change nothing and the "
        "test goes on asserting something it is no longer testing:\n  "
        + "\n  ".join(sorted(offenders))
    )

"""Make a monkeypatched name reachable across a split, by calling it through its module.

THE CONSTRAINT, measured all day on 28 August 2026. `monkeypatch.setattr(m, "name", fake)` binds
an attribute on ONE module object. A caller written `name(...)` resolves `name` in its OWN
module's globals, so once caller and callee are in different files the patch reaches nothing --
silently, because the facade still binds the name and the import still succeeds.

That is why .harness/build_driver.py and scripts/dispatch.py could not be layered at all. `sh`,
`ROOT`, `BRIEFS` and `LOG` are patched AND called throughout, so pinning each patched name to
every caller welded sixty symbols into one 3,272-line component. The graph was never the problem.

A caller written `mod.name(...)` resolves the attribute AT CALL TIME against the module object,
which is the object the patch mutates. One patch then reaches every caller in every file. So this
rewrites cross-module references to patched symbols into attribute access and adds `import mod`
beside the existing `from mod import name`.

The name import STAYS. It is the facade -- what keeps `dispatch.run_process` resolvable for every
existing caller, and what `__all__` refers to. An earlier version replaced it, which unbound 53
names that `__all__` still listed: ruff reported F822 and every importer would have broken. The
call sites change; the surface does not.

It is a REAL CODE CHANGE and is deliberately not part of split_module, which is a pure mover
whose output verify_split can prove. This runs afterwards, on the already-split family, and its
diff is meant to be read.

What it does not touch: a reference inside the module that defines the symbol. A bare name there
already resolves in the namespace the patch mutates, so prefixing it would be noise.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path


def bound_at_module_level(tree: ast.Module) -> set[str]:
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            out |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out


def imported_from(tree: ast.Module, name: str) -> str | None:
    """The sibling module a name is imported from, if any."""
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            if any((alias.asname or alias.name) == name for alias in node.names):
                return node.module.lstrip(".")
    return None


def rewrite(path: Path, patched: set[str], family: set[str]) -> tuple[int, set[str]]:
    """Prefix cross-module uses of patched names, and return how many and from where."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    defined = bound_at_module_level(tree)

    targets: dict[str, str] = {}
    for name in sorted(patched):
        if name in defined:
            continue  # defined here: a bare name already resolves in the patched namespace
        source = imported_from(tree, name)
        if source and source in family:
            targets[name] = source
    if not targets:
        return 0, set()

    # Collect the Name sites first; rewriting by offset must run back-to-front.
    sites: list[tuple[int, int, int, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id in targets
            and isinstance(node.ctx, ast.Load)
        ):
            end = node.end_col_offset
            if end is None:  # pragma: no cover - every Name node carries an end offset
                continue
            sites.append((node.lineno, node.col_offset, end, node.id))
    rows = text.splitlines(keepends=True)
    for lineno, start, end, name in sorted(sites, reverse=True):
        row = rows[lineno - 1]
        rows[lineno - 1] = row[:start] + f"{targets[name]}.{name}" + row[end:]
    text = "".join(rows)

    # ADD the module import; do not remove the name import that is already there. The name
    # import is the FACADE -- it is what keeps `dispatch.run_process` resolvable for every
    # existing caller, and it is what `__all__` refers to. Removing it unbound 53 names that
    # __all__ still listed, which ruff reported as F822 and which would have broken every
    # importer. The call sites now go through the module; the surface is unchanged.
    # After any `from __future__`, which must stay first, and only for modules a site actually
    # went through -- importing a module nothing calls is an unused import, which ruff removes
    # and which says nothing true about the file.
    used_modules = {targets[name] for _, _, _, name in sites}
    # Beside the first SIBLING import, not at the top of the file. scripts/ is not a package,
    # so a sibling is importable only after the sys.path bootstrap runs -- and the splitter has
    # already placed that first sibling import in a position that works. Inserting at the top
    # instead put `import dispatch_invocation` above the bootstrap and the module raised
    # ModuleNotFoundError on its own sibling. Measured 28 August 2026, twice in one evening.
    sibling_imports = [
        n
        for n in tree.body
        if isinstance(n, ast.ImportFrom)
        and n.module
        and n.module.lstrip(".") in family
    ]
    ordinary = [
        n
        for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
        and not (isinstance(n, ast.ImportFrom) and n.module == "__future__")
    ]
    anchor = sibling_imports or ordinary
    first_import = anchor[0].lineno if anchor else 1
    rows = text.splitlines(keepends=True)
    for module in sorted(used_modules, reverse=True):
        if re.search(r"^import " + re.escape(module) + r"$", text, re.M):
            continue
        rows.insert(first_import - 1, "import " + module + chr(10))
    text = "".join(rows)

    path.write_text(text, encoding="utf-8", newline="\n")
    return len(sites), set(targets.values())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stem", help="the family's entry-point stem, e.g. dispatch")
    ap.add_argument("--dir", default="scripts")
    ap.add_argument("--patched", required=True, help="comma-separated patched names")
    args = ap.parse_args(argv)

    directory = Path(args.dir)
    files = [
        directory / f"{args.stem}.py",
        *sorted(directory.glob(f"{args.stem}_*.py")),
    ]
    family = {p.stem for p in files}
    patched = {p for p in args.patched.split(",") if p}

    total = 0
    for path in files:
        if not path.is_file():
            continue
        count, modules = rewrite(path, patched, family)
        if count:
            print(f"  {path.name}: {count} reference(s) via {sorted(modules)}")
            total += count
    print(f"{total} cross-module reference(s) now resolved at call time")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""ADR-0065's second owed check: adoption is recorded, or it does not happen (R36).

The tier-1 import ban (tests/test_tier1_imports.py) made the core stdlib-only, but
nothing recorded an *adopted* dependency — so the enforced position was "adopt
nothing", the opposite of the instruction. This checker is the other half:

- a third-party import in a tier-1 module fails, registered or not;
- a third-party import in any other tracked `src/consilient` module fails unless
  the package is in `docs/decisions/adopted-deps.json` and names that module;
- a registry entry no listed module imports is stale and fails;
- the licence must be permissive (checked at registration, not after use) and the
  adopting ADR must exist.

Only TRACKED files are scanned: uncommitted work belongs to its author; the gate
binds at the moment work enters the tree. Git IO scrubs GIT_* (the
check_private_corpus.py pattern).

    python .github/scripts/check_adopted_deps.py             # scan the real tree
    python .github/scripts/check_adopted_deps.py --self-test # fixtures

Standard library only. Exit 0 clean, 1 on a violation, 2 on misuse.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = ROOT / "src" / "consilient"
REGISTRY = ROOT / "docs" / "decisions" / "adopted-deps.json"
DECISIONS = ROOT / "docs" / "decisions"

# GIT_DIR overrides cwd. A git subprocess that inherits it from a hook reads the wrong repo.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

# The tier-1 module list of ADR-0065, duplicated from tests/test_tier1_imports.py;
# tests/test_adopted_deps.py fails if the two copies ever disagree.
TIER1_MODULES = (
    "beta",
    "events",
    "projection",
    "recall",
    "budget",
    "work_items",
    "coordination",
    "routing",
)

# Licences this project may redistribute under. Checked when a dependency is
# registered, not after it ships — principle 10. Copyleft and unknown licences
# are not adopted by accident; widening this set is a registry edit with a reason.
PERMISSIVE_LICENCES = frozenset(
    {
        "MIT",
        "MIT-0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "Apache-2.0",
        "ISC",
        "PSF-2.0",
        "Python-2.0",
        "CC0-1.0",
        "Unlicense",
    }
)

ADR_REF = re.compile(r"^\d{4}$")


def third_party_imports(source: str) -> set[str]:
    """Top-level package names imported by one module, minus stdlib and our own."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return {
        name
        for name in names
        if name and name not in sys.stdlib_module_names and name != "consilient"
    }


def tracked_modules(root: Path = ROOT) -> list[str]:
    """Tracked `src/consilient/*.py` paths, relative to the repository root."""
    out = subprocess.run(
        ["git", "ls-files", "src/consilient/*.py"],
        cwd=root,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(f"git ls-files failed: {out.stderr.strip()[:200]}")
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def load_registry(path: Path = REGISTRY) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Validated registry entries, plus schema violations found on the way."""
    problems: list[str] = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"registry {path} is unreadable: {exc}"]
    adopted = raw.get("adopted") if isinstance(raw, dict) else None
    if not isinstance(adopted, dict):
        return {}, ["registry must carry an 'adopted' object"]
    entries: dict[str, dict[str, object]] = {}
    for package, body in adopted.items():
        if not isinstance(body, dict):
            problems.append(f"{package}: entry must be an object")
            continue
        upstream = body.get("upstream")
        if not isinstance(upstream, str) or not upstream.startswith("https://"):
            problems.append(f"{package}: upstream must be an https URL")
        licence = body.get("licence")
        if licence not in PERMISSIVE_LICENCES:
            problems.append(
                f"{package}: licence {licence!r} is not in the permissive set "
                "(checked at registration, not after use)"
            )
        adr = body.get("adr")
        if not isinstance(adr, str) or not ADR_REF.match(adr):
            problems.append(f"{package}: adr must be a four-digit ADR number")
        elif not any(DECISIONS.glob(f"{adr}-*.md")):
            problems.append(f"{package}: ADR-{adr} does not exist in docs/decisions/")
        modules = body.get("modules")
        if (
            not isinstance(modules, list)
            or not modules
            or not all(isinstance(m, str) and m for m in modules)
        ):
            problems.append(f"{package}: modules must be a non-empty list of module names")
            modules = []
        rationale = body.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            problems.append(
                f"{package}: rationale must say why adoption beats native, in a sentence"
            )
        entries[package] = {"modules": modules, "licence": licence, "adr": adr}
    return entries, problems


def check_tree(
    modules: list[str], entries: dict[str, dict[str, object]], root: Path = ROOT
) -> list[str]:
    """Every import rule above, over the given tracked modules."""
    problems: list[str] = []
    imported_by: dict[str, set[str]] = {package: set() for package in entries}
    for rel in modules:
        module = Path(rel).stem
        try:
            source = (root / rel).read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"{rel}: unreadable: {exc}")
            continue
        for package in sorted(third_party_imports(source)):
            if module in TIER1_MODULES:
                problems.append(
                    f"{rel}: tier-1 module imports third-party {package!r}; "
                    "ADR-0065's ban is absolute for the core, registered or not"
                )
                continue
            entry = entries.get(package)
            if entry is None:
                problems.append(
                    f"{rel}: imports unregistered third-party {package!r}; adopt it in "
                    "docs/decisions/adopted-deps.json (upstream, licence, ADR, modules) "
                    "or remove the import"
                )
                continue
            modules_allowed = entry["modules"]
            assert isinstance(modules_allowed, list)
            if module not in modules_allowed:
                problems.append(
                    f"{rel}: {package!r} is adopted but not for module {module!r}; "
                    "name the module in the registry entry"
                )
                continue
            imported_by[package].add(module)
    for package, users in imported_by.items():
        if not users:
            problems.append(
                f"registry entry {package!r} is stale: no listed module imports it; "
                "the registry records what is adopted, not what might be"
            )
    return problems


def _self_test() -> int:
    fixture = {
        "good.py": "import requests\nimport json\n",
        "rogue.py": "import requests\n",
        "quiet.py": "import json\n",
    }
    assert third_party_imports(fixture["good.py"]) == {"requests"}
    assert third_party_imports(fixture["quiet.py"]) == set()

    entries = {"requests": {"modules": ["good"], "licence": "Apache-2.0", "adr": "0065"}}
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src/consilient").mkdir(parents=True)
        for name, text in fixture.items():
            (root / "src/consilient" / name).write_text(text, encoding="utf-8")

        clean = check_tree(["src/consilient/good.py"], entries, root)
        assert not clean, clean

        (root / "src/consilient" / "events.py").write_text(
            fixture["rogue.py"], encoding="utf-8"
        )
        tier1 = check_tree(["src/consilient/events.py"], entries, root)
        assert any("tier-1" in p for p in tier1), tier1

        unregistered = check_tree(["src/consilient/good.py"], {}, root)
        assert any("unregistered" in p for p in unregistered), unregistered

        wrong_module = check_tree(["src/consilient/rogue.py"], entries, root)
        assert any("not for module" in p for p in wrong_module), wrong_module

        stale = check_tree(["src/consilient/quiet.py"], entries, root)
        assert any("stale" in p for p in stale), stale
    print("self-test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    entries, problems = load_registry()
    try:
        modules = tracked_modules()
    except RuntimeError as exc:
        print(str(exc))
        return 2
    problems.extend(check_tree(modules, entries))
    if problems:
        print("adopted-dependency invariant FAILED:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(
        f"adopted-dependency invariant passes "
        f"({len(modules)} tracked modules, {len(entries)} adopted packages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

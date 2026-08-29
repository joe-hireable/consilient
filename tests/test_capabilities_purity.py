"""The policy module stays pure stdlib policy, checked by reading its source.

These scan src/consilient/capabilities*.py rather than calling it, so they see what a
behavioural test cannot: a new third-party import, or a domain branch reintroduced. The glob is
deliberately a family glob -- a split of the module under test must not move half of it out of
the ban's reach, which is the same hazard tests/test_repo_shape.py guards for the promoter.
"""

import ast

import re

import sys


from capabilities_helpers import (
    CORE,
    PACKAGE,
    ROOT,
    SCRIPT,
)

sys.path.insert(0, str(ROOT / "src"))


def test_policy_module_is_pure_stdlib_policy() -> None:
    """The purity ban covers the whole capabilities FAMILY, not one file.

    Two things here were pinned to a single path and would have narrowed silently, or
    failed for the wrong reason, the moment capabilities.py was split [measured 28 Aug
    2026]:

      * it parsed CORE alone, so a `capabilities_parse.py` carrying the impure import
        would sail through a ban that still reported green;
      * it had no `node.level` guard, so `from .capabilities_parse import X` -- an
        INTRA-package import, exactly what the ban permits -- would be read as an
        external dependency named 'capabilities_parse' and fail outright.

    test_tier1_imports._external_imports already gets the level test right; this did
    not. Relative imports are skipped because intra-package structure is not a
    dependency, which is the whole point of being allowed to split the file.
    """
    family = sorted(PACKAGE.glob("capabilities*.py"))
    assert family, "no capabilities module found -- has it been renamed?"
    imported: set[str] = set()
    for path in family:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue  # intra-package, not a dependency
                imported.add((node.module or "").split(".", 1)[0])
    assert imported <= {"__future__", "dataclasses", "datetime", "re", "typing"}

    forbidden_calls = {
        "connect",
        "getenv",
        "open",
        "read_text",
        "request",
        "run",
        "urlopen",
        "write_text",
    }
    called = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    assert called.isdisjoint(forbidden_calls)


def test_policy_has_no_domain_or_document_mode_branch() -> None:
    forbidden = {"code", "document", "domain", "mode"}
    violations: list[str] = []
    for path in (CORE, SCRIPT):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        predicates: list[ast.AST] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.While)):
                predicates.append(node.test)
            elif isinstance(node, ast.Match):
                predicates.append(node.subject)
            elif isinstance(node, ast.comprehension):
                predicates.extend(node.ifs)
        for predicate in predicates:
            words: set[str] = set()
            for part in ast.walk(predicate):
                if isinstance(part, ast.Name):
                    words.update(re.findall(r"[a-z]+", part.id.casefold()))
                elif isinstance(part, ast.Attribute):
                    words.update(re.findall(r"[a-z]+", part.attr.casefold()))
                elif isinstance(part, ast.Constant) and isinstance(part.value, str):
                    words.update(re.findall(r"[a-z]+", part.value.casefold()))
            if words & forbidden:
                violations.append(f"{path.name}:{predicate.lineno}")
    assert not violations, f"domain-keyed branch found: {violations}"

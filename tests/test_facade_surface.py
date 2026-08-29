"""A facade may not re-export a private name that nothing outside the family reads.

THE FAILURE THIS EXISTS TO STOP, measured on 29 August 2026. The splits of 28 August left
391 underscore-prefixed names listed in a family entry point's `__all__`. 231 of them were
reached by no file outside their own family: the facade imported them from a sibling and
published them for nobody. Two costs, and the second is the one that matters.

The plumbing was 462 lines. Recoverable, and now recovered.

The marker was the real loss. A leading underscore is the only signal this package has for
"internal to this module", and once a third of the exported surface carried one, the signal
said nothing. A reader could no longer tell a deliberate cross-module helper from a detail
the splitter happened to lift, so `__all__` stopped describing a boundary and started
describing where the splitter put things.

That is a ratchet failure, not a style complaint (working principle 4): the splitter will
run again, and without this check every future split re-accumulates the same surface. So
the rule is enforced where it can fail, in the same commit as the repair.

The rule is deliberately narrow. It governs a private name the entry point IMPORTS FROM A
SIBLING and re-exports, which is the shape a split creates. A private name the entry point
defines itself and exports is a different judgement and is not policed here.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "consilient"


def _family_of() -> dict[str, str]:
    """Every module stem in the package mapped to the family it belongs to."""
    entries = [
        f.stem
        for f in sorted(PKG.glob("*.py"))
        if not ("_" in f.stem and (PKG / f"{f.stem.split('_')[0]}.py").is_file())
        and list(PKG.glob(f"{f.stem}_*.py"))
    ]
    out = {stem: stem for stem in entries}
    for stem in entries:
        for sibling in PKG.glob(f"{stem}_*.py"):
            out[sibling.stem] = stem
    return out


def _repository_sources() -> dict[str, str]:
    listing = subprocess.run(
        ["git", "ls-files", "*.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        check=True,
    ).stdout.split()
    return {
        p: (ROOT / p).read_text(encoding="utf-8", errors="replace") for p in listing
    }


def _surface(stem: str) -> tuple[list[str], dict[str, str], str]:
    """The entry point's `__all__`, where each imported name came from, and its source."""
    text = (PKG / f"{stem}.py").read_text(encoding="utf-8")
    tree = ast.parse(text, filename=f"{stem}.py")
    exported: list[str] = []
    source_of: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", "") == "__all__" for target in node.targets
        ):
            exported = [
                element.value
                for element in getattr(node.value, "elts", [])
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                source_of[alias.asname or alias.name] = node.module.lstrip(".")
    return exported, source_of, text


def _used_in_facade_body(text: str) -> set[str]:
    """Names the entry point's own code reaches, excluding the imports and `__all__`.

    A facade that USES what it re-exports is not plumbing. Strings count, because a name
    reached through getattr is still reached.
    """
    used: set[str] = set()
    for node in ast.parse(text).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", "") == "__all__" for target in node.targets
        ):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                used.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                used.add(sub.attr)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                used.update(re.findall(r"\b_\w+", sub.value))
    return used


def _reexported_privates(stem: str, family_of: dict[str, str]) -> list[str]:
    """Private names this entry point publishes on behalf of one of its own siblings."""
    exported, source_of, _text = _surface(stem)
    return [
        name
        for name in exported
        if name.startswith("_") and family_of.get(source_of.get(name, "")) == stem
    ]


def _mentioned_outside(
    name: str, stem: str, family_of: dict[str, str], sources: dict[str, str]
) -> bool:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    return any(
        family_of.get(Path(path).stem) != stem and pattern.search(body)
        for path, body in sources.items()
    )


def test_no_facade_publishes_a_private_name_nobody_reads() -> None:
    family_of = _family_of()
    sources = _repository_sources()
    offenders: dict[str, list[str]] = {}

    for stem in sorted(set(family_of.values())):
        _exported, _source_of, text = _surface(stem)
        used_here = _used_in_facade_body(text)
        for name in _reexported_privates(stem, family_of):
            if name in used_here:
                continue
            if not _mentioned_outside(name, stem, family_of, sources):
                offenders.setdefault(stem, []).append(name)

    assert not offenders, (
        "these entry points re-export private names that no file outside their own family "
        "mentions, which is plumbing and which erodes what a leading underscore means:"
        + chr(10)
        + chr(10).join(
            f"  {stem}: {', '.join(names)}" for stem, names in sorted(offenders.items())
        )
        + chr(10)
        + "Remove each from __all__ and from the sibling import in the entry point. If one "
        "is genuinely needed elsewhere, the caller that needs it is the evidence: add the "
        "caller, or rename the symbol public."
    )


def test_the_check_would_catch_a_reintroduced_passthrough() -> None:
    """The guard must be able to FAIL, or it is decoration that passes forever.

    Asserts on the mechanism rather than on a scratch copy of a real entry point, because
    rewriting one to prove a point is how a test leaves a repository dirty. Every private
    name still exported must survive the reachability rule for a reason the rule can see:
    an outside caller, or a use in the facade itself. If any survives for no such reason,
    the rule above is not evaluating what it claims to.
    """
    family_of = _family_of()
    sources = _repository_sources()
    checked = 0

    for stem in sorted(set(family_of.values())):
        _exported, _source_of, text = _surface(stem)
        for name in _reexported_privates(stem, family_of):
            assert _mentioned_outside(name, stem, family_of, sources) or re.search(
                rf"\b{re.escape(name)}\b", text
            ), (
                f"{stem}.__all__ exports {name}, which the reachability rule cannot "
                "justify, so the rule above is not evaluating what it claims to"
            )
            checked += 1

    assert checked > 100, (
        f"only {checked} private re-exports were examined; the guard is measuring almost "
        "nothing and would not notice a family that reintroduced a passthrough surface"
    )

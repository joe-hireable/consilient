"""Splitting a governed module must not un-govern half of it.

MEASURED 28 August 2026, while planning the refactor that brings 48 files under the 500-line
cap. `promote.PROTECTED_PREFIXES` names governed modules by their FULL FILENAME --
`"src/consilient/beta.py"` -- and `path_status` matches with `startswith`. So:

    src/consilient/beta.py            -> protected
    src/consilient/beta_upstream.py   -> not_allowlisted

"beta_upstream.py" does not start with "beta.py". Every sibling a split creates falls out of
the protected set, and `promote.py` is the SELF-EDITING promoter: `not_allowlisted` is the
verdict that lets it rewrite a file. So a purely mechanical, behaviour-preserving split would
have quietly handed the promoter write access to half of `events.py`, `cli.py` and
`instructions.py` -- the last of which exists precisely because "the one layer that may never
be adapted lives where the promoter cannot reach".

Nothing would have failed. That is the whole point of this file: AGENTS.md principle 3 says an
invariant ships with the check that enforces it, and the invariant "a governed family stays
governed" had no check at all.

This test passes today, when no family has been split. It fails the moment a split creates a
sibling that was not added to PROTECTED_PREFIXES -- which is exactly when someone needs to be
told.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from consilient.promote import (  # noqa: E402
    PROTECTED,
    PROTECTED_PREFIXES,
    path_status,
)

PACKAGE = ROOT / "src" / "consilient"


def _governed_families() -> list[str]:
    """The module stems named individually in PROTECTED_PREFIXES, e.g. 'beta'."""
    stems = []
    for prefix in PROTECTED_PREFIXES:
        if prefix.startswith("src/consilient/") and prefix.endswith(".py"):
            stems.append(Path(prefix).stem)
    return sorted(stems)


def _siblings(stem: str) -> list[Path]:
    """Every file in the family: the module itself and any `<stem>_*.py` split off it.

    `<stem>_*` rather than `<stem>*` deliberately. A bare prefix glob would make `cli` claim a
    hypothetical `client.py`, which is a different module -- and a protection that over-reaches
    teaches people to work around it.
    """
    found = [PACKAGE / f"{stem}.py"]
    found.extend(sorted(PACKAGE.glob(f"{stem}_*.py")))
    return [p for p in found if p.is_file()]


def test_every_governed_family_is_named_and_present() -> None:
    """The prefixes must describe files that exist, or the protection is theatre."""
    families = _governed_families()
    assert families, (
        "PROTECTED_PREFIXES names no individual module -- has it been rewritten?"
    )
    for stem in families:
        assert (PACKAGE / f"{stem}.py").is_file(), (
            f"PROTECTED_PREFIXES protects src/consilient/{stem}.py, which does not exist. "
            "Either the module was renamed and the prefix was not, or the prefix is dead."
        )


def test_a_split_may_not_un_govern_part_of_a_governed_module() -> None:
    """Every file in a governed family is protected, not just the original.

    If this fails after a split, the fix is to add the new file to PROTECTED_PREFIXES as an
    EXPLICIT string. Do not widen the prefix to `src/consilient/beta` -- that would silently
    change matching for paths nobody has considered yet, which is the same class of mistake
    one level up.
    """
    unprotected: list[str] = []
    for stem in _governed_families():
        for path in _siblings(stem):
            rel = path.relative_to(ROOT).as_posix()
            if path_status(rel) != PROTECTED:
                unprotected.append(rel)

    assert not unprotected, (
        "these files belong to a governed family but the self-editing promoter may rewrite "
        "them:\n  " + "\n  ".join(unprotected) + "\n"
        "Add each to promote.PROTECTED_PREFIXES as an explicit string, in the same commit as "
        "the split."
    )


def test_the_guard_would_actually_catch_an_un_governed_sibling() -> None:
    """The check must fail on the thing it exists to catch, or it guards nothing.

    Rather than trust the assertion above, ask `path_status` directly about the sibling a split
    of each governed family WOULD create. Every one must currently be un-governed -- which is
    the measured defect -- proving the test above is not vacuously true.
    """
    would_be_unprotected = [
        f"src/consilient/{stem}_probe_only.py" for stem in _governed_families()
    ]
    leaked = [p for p in would_be_unprotected if path_status(p) != PROTECTED]
    assert leaked == would_be_unprotected, (
        "some hypothetical sibling is already protected, so the prefix matching has changed "
        "and the assertion above may now be vacuous. Re-derive what this test is proving."
    )

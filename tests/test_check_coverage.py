"""Every check script runs somewhere, or is exempt for a stated reason. No silent third state.

MEASURED 28 August 2026. `.github/scripts/` held twenty-three check scripts and the workflows
invoked thirteen of them. The other ten ran nowhere, and one of those ten was
`check_private_repo_names.py` -- the boundary check -- which was RED against the tracked tree at
that moment: `docs/publications/README.md` still carried the private-corpus carve-out the
principal rescinded on 23 August, and the checker's own EXISTING_BREACHES list exempted the very
file that breached it.

Nothing reported this. `tests/test_living_document_ci.py` already asserts "a check that is not
invoked is not a check" -- but only over the five commands in one documentation gate, so it could
not see the other eighteen. This file is that invariant taken to its proper scope.

WHY AN EXEMPTION LIST IS ACCEPTABLE HERE, when a boundary check's baseline is not. A baseline of
permitted violations on a BOUNDARY guarantees the check cannot catch the thing that motivated it
-- which is exactly how the carve-out survived. This is a COVERAGE count, not a boundary: the
exemptions name scripts that cannot run in CI or do not pass yet, each with a reason, and the
number may only fall. That distinction is the whole of why this list is allowed to exist.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"
WORKFLOWS = ROOT / ".github" / "workflows"

# Scripts no workflow invokes, each with the reason. This may only shrink.
# Lower it in the same commit as the fix, exactly like the file-length ratchet.
EXEMPT: dict[str, str] = {
    "check_private_corpus.py": (
        "Deliberate and already pinned by its own test: it cannot run on a runner, and a gate "
        "that silently no-ops is worse than no gate."
    ),
    "check_error_recurrence.py": (
        "Runs as a local pre-commit hook and takes a record argument, so it fires where the "
        "defect is created rather than for somebody else later."
    ),
    "check_heldout_isolation.py": (
        "Takes --heldout-contract and runs per measurement, not per commit."
    ),
    "check_record_numbers.py": (
        "FAILS on the tracked tree today: the experiment register has two EXP-58 headings. "
        "Wire it in the commit that resolves the duplicate."
    ),
    "check_source_depth.py": (
        "FAILS on the tracked tree today: 60 [SNIP]/[2ND] citations across two files in "
        "docs/50-publications/, both headed 'DRAFT -- not submitted, not published, not "
        "transmitted'. Whether a labelled draft in a public repository counts as citing "
        "publicly is the principal's call, not a check's."
    ),
    "check_restatement.py": (
        "FAILS on the tracked tree today: adverse=42, down from 46 once it was taught to "
        "recognise the two inline regions scripts/build_counts.py maintains. Of the 42, 38 are "
        "ADR numbers CITED in dated plan documents rather than counts restated, and the other 4 "
        "are counts that were correct on the date those documents carry -- '39 ADRs' when there "
        "were 39. Rewriting a dated record to today's numbers would falsify it, so this cannot "
        "be closed by editing the documents. It needs a decision about whether a citation is a "
        "restatement and whether dated records are exempt, which is not a check's call."
    ),
}


def _invoked() -> set[str]:
    """Every check script named anywhere in a workflow file."""
    found: set[str] = set()
    for workflow in WORKFLOWS.glob("*.yml"):
        text = workflow.read_text(encoding="utf-8", errors="replace")
        found.update(re.findall(r"\.github/scripts/([a-z0-9_]+\.py)", text))
    return found


def _present() -> set[str]:
    return {p.name for p in SCRIPTS.glob("check_*.py")}


def test_every_check_script_is_invoked_or_exempt_with_a_reason() -> None:
    """The third state -- present, uninvoked, unexplained -- is the one that hid the breach."""
    unaccounted = sorted(_present() - _invoked() - set(EXEMPT))
    assert not unaccounted, (
        "these check scripts run nowhere and give no reason:\n  "
        + "\n  ".join(unaccounted)
        + "\nEither add them to a workflow, or add an entry to EXEMPT saying why not. A check "
        "that runs nowhere reports nothing, which is working principle 3."
    )


def test_the_exemption_list_names_only_scripts_that_exist_and_are_not_invoked() -> None:
    """A stale exemption is how a list stops meaning anything."""
    present, invoked = _present(), _invoked()
    missing = sorted(name for name in EXEMPT if name not in present)
    assert not missing, (
        f"EXEMPT names scripts that do not exist: {missing}. Remove them."
    )
    redundant = sorted(name for name in EXEMPT if name in invoked)
    assert not redundant, (
        f"EXEMPT names scripts a workflow already invokes: {redundant}. Delete those entries "
        "-- keeping them lets a later un-wiring pass unnoticed."
    )


def test_every_exemption_carries_a_reason() -> None:
    """A list of names without reasons is a list nobody can shrink."""
    thin = sorted(name for name, why in EXEMPT.items() if len(why.strip()) < 40)
    assert not thin, f"these exemptions give no usable reason: {thin}"


def test_the_guard_would_actually_catch_an_unwired_script() -> None:
    """Prove the first assertion is not vacuous, rather than trusting that it holds.

    The failure being guarded against is a script that exists, runs nowhere and is not listed.
    Ask the same set arithmetic about a script in exactly that position.
    """
    planted = "check_planted_probe_only.py"
    assert planted not in _present(), "the probe name collides with a real script"
    would_be = ({planted} | _present()) - _invoked() - set(EXEMPT)
    assert planted in would_be, (
        "an unwired, unexempt script did NOT show up as unaccounted -- the set arithmetic above "
        "has changed and the first test may now pass vacuously."
    )

"""The source-file cap may not move without a decision, and the ratchet may not lie.

THE GAP THIS CLOSES. Until 29 August 2026 nothing asserted `LIMIT` at all. No ADR established
500 -- a grep of `docs/decisions/` for the cap or the checker returned nothing -- and
`tests/test_living_document_ci.py` only asserts the command is wired into `invariants.yml`, never
its constants. So the only enforced size invariant in the repository was a number any agent could
have edited in passing, in a file nobody re-reads. Working principle 3 says a chokepoint without
an enforcement rule is not a chokepoint; that is what the cap was.

ADR-0111 moved it to 1,000 and this is the rule shipped in the same commit, as principle 3
requires. Moving the cap again now fails here, and the failure names the ADR it needs.

THE SECOND HALF is the reversibility repair, and it is subtler. The checker fails in BOTH
directions -- too many offenders, and too few for a stale ceiling -- so raising the limit forces
the ceiling down in the same commit. If "never raise CEILING" were then absolute, LOWERING the
limit later would be permanently forbidden, because a smaller limit means more offenders. The cap
would be a one-way door welded shut by its own anti-loosening rule. `CEILING_AT_LIMIT` records
which limit the ceiling was counted against, so the monotonicity rule can be "may only fall at a
given limit" rather than "may only fall", and the door opens both ways.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_file_length.py"
SPEC = importlib.util.spec_from_file_location("check_file_length", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_the_cap_is_the_value_its_adr_decided() -> None:
    """Change this and you must change ADR-0111, or write the one that supersedes it."""
    assert CHECKER.LIMIT == 1000, (
        f"LIMIT is {CHECKER.LIMIT}; ADR-0111 decided 1000. A cap is a governance decision, not a "
        "tuning parameter: move it by writing the ADR that supersedes 0111, recording the corpora "
        "the new number is derived from, and updating this test in the same commit."
    )


def test_the_limit_names_a_decision_that_exists_and_is_settled() -> None:
    """A pinned number whose ADR does not exist is a citation to nothing."""
    adrs = list((ROOT / "docs" / "decisions").glob(f"{CHECKER.LIMIT_ADR}-*.md"))
    assert len(adrs) == 1, (
        f"LIMIT_ADR names {CHECKER.LIMIT_ADR!r} and {len(adrs)} matching ADR file(s) exist"
    )
    text = adrs[0].read_text(encoding="utf-8")
    status = re.search(r"^\s*-\s*\*\*Status:?\*\*:?\s*(.+)$", text, re.MULTILINE)
    assert status is not None, f"{adrs[0].name} has no Status line"
    assert status.group(1).strip().upper().startswith(("ACCEPTED", "SUPERSEDED")), (
        f"{adrs[0].name} is {status.group(1).strip()!r}. The cap in force must rest on a decision "
        "that was actually taken -- a PROPOSED ADR is a suggestion, and enforcing a suggestion as "
        "an invariant is how the unnamed 500 happened in the first place."
    )


def test_the_ceiling_records_the_limit_it_was_counted_against() -> None:
    assert CHECKER.CEILING_AT_LIMIT == CHECKER.LIMIT, (
        f"CEILING={CHECKER.CEILING} was counted at {CHECKER.CEILING_AT_LIMIT} lines but LIMIT is "
        f"{CHECKER.LIMIT}. Re-derive both in one commit; a ceiling without its limit is a number "
        "with no meaning, and pretending otherwise is what makes the cap irreversible."
    )


def test_the_ceiling_matches_what_is_actually_in_the_tree() -> None:
    """The ratchet must be exactly the count, so it can never be left slack."""
    count = len(CHECKER.offenders())
    assert count == CHECKER.CEILING, (
        f"{count} file(s) exceed {CHECKER.LIMIT} lines but CEILING is {CHECKER.CEILING}. "
        "Lower CEILING to the count in the commit that does the work; a ratchet that is not "
        "tightened when the work is done stops meaning anything."
    )


def test_both_halves_of_the_size_rule_run_in_ci() -> None:
    """A gate that exists but is not invoked is the failure ADR-0111's context section describes.

    The per-FUNCTION half matters more than the per-file half and is the newer of the two, so it
    is the one likeliest to be quietly dropped from the workflow. Both are asserted here because
    a size rule enforced on files alone is satisfied by a facade split that improves nothing.
    """
    workflow = (ROOT / ".github" / "workflows" / "invariants.yml").read_text(
        encoding="utf-8"
    )
    for script in ("check_file_length.py", "check_function_size.py"):
        assert f".github/scripts/{script}" in workflow, (
            f"{script} is not invoked by invariants.yml, so nothing enforces it"
        )


def test_the_mismatch_guard_can_actually_fail() -> None:
    """Prove the reversibility check rejects a desynchronised pair, rather than assuming it.

    Runs `main()` with the pair deliberately broken. A guard nobody has watched fail is a guard
    nobody knows the shape of, and this repository has already shipped one that passed on a file
    broken with a SyntaxError.
    """
    original = CHECKER.CEILING_AT_LIMIT
    try:
        CHECKER.CEILING_AT_LIMIT = original + 1
        assert CHECKER.main([]) == 1, (
            "main() accepted a CEILING counted at a different limit than LIMIT, so the "
            "reversibility repair in ADR-0111 is not actually enforced"
        )
    finally:
        CHECKER.CEILING_AT_LIMIT = original
    assert CHECKER.main([]) == 0, "the guard did not restore cleanly"

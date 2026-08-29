"""Invariant I1, which the original module docstring states: a declared chokepoint ships
with the check that bans bypassing it, in the same commit. These are the checks on the
checks, and they read the repository's own artefacts rather than the package. A checker
with no CI step is a checker nobody runs — `check_foreign_identifiers.py` was written on
21 August 2026 after 71 private commit identifiers were found in a tracked file and
shipped with no step at all — and a step that cannot fail is worse: the replay step ran
`beta` before `replay` "so that replay has a subject" until the same day, and the
subject `cmd_beta` leaves behind is a rebuild from the same log, so `identical: true`
was guaranteed and deliberate out-of-band drift still exited 0. The subject is now a
committed fixture, asserted non-empty, and the comment prose is stripped before the
commands are searched, because a workflow comment may legitimately name the thing the
step must not do. `check_private_corpus.py` is deliberately absent from CI: its subject
does not exist on a runner, so wiring it in would scan nothing and report green, and a
green tick is read as evidence. ADR-0047 retired "N adapters fit" as evidence and this
replaced it — the contract's field names pinned from the first adapter's docstring,
where they were written before any second runtime existed, plus a size ratchet measured
20 August 2026 across eight modules at 78, 90, 107, 124, 130, 148, 233 and 295 lines,
the newest 3.8x the smallest. Working principles 9 and 11 are enforced here too: a
superlative in public-facing prose carries its citation, because `README.md` claimed
"Nothing on the market measures it" while eight published systems measured β and this
repository's own register said so [measured]; and a PROVISIONAL decision names an
experiment the register knows, because an estimate with no route to becoming a
measurement is a guess that has stopped trying. Both patterns are deliberately narrow —
a check that fires on innocent prose gets suppressed and then protects nothing."""

import argparse
import re
import sys
from pathlib import Path
import pytest
from v0_invariants_helpers import (
    _spend_scripts,
)


def test_ci_static_gate_runs_mypy_strict():
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    static_step = workflow.partition("- name: Static checks")[2].partition("- name:")[0]
    assert "run: python -m mypy --strict src/consilient" in static_step


def test_ci_ruff_gate_matches_release_command():
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    ruff_step = workflow.partition("- name: Repository-wide Ruff")[2].partition(
        "- name:"
    )[0]
    assert "run: python -m ruff check ." in ruff_step


# ---------------------------------------------------------------- ADR-0047
ADAPTERS = Path("docs/10-research/experiments/exp05")


def _adapter_lines() -> dict[str, int]:
    return {
        path.stem.replace("adapter_", ""): sum(
            1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        for path in sorted(ADAPTERS.glob("adapter_*.py"))
    }


def test_the_adapter_contract_is_asserted_not_counted():
    """ADR-0047 retired "N adapters fit" as evidence. This is what replaces it.

    Seven backends fitting the boundary told us it was stable; an eighth tells us nothing.
    What the count was really guarding — that nobody quietly redesigns the boundary — is
    guarded here instead, by naming the fields.
    """
    outcome_fields = {
        "ticket_id",
        "agent",
        "domain",
        "harness",
        "provider",
        "model",
        "ok",
        "diff",
        "tokens_in",
        "tokens_out",
        "cost_usd",
        "duration_s",
        "raw_tail",
    }
    ticket_fields = {"id", "goal", "repo_dir", "timeout_s"}

    # The canonical declaration lives in the FIRST adapter's module docstring, where it was
    # written before any second runtime existed. That is the text seven backends were built
    # against, so it is the text worth pinning.
    canonical = (ADAPTERS / "adapter_claude_code.py").read_text(encoding="utf-8")
    missing = {
        name for name in outcome_fields | ticket_fields if f'"{name}"' not in canonical
    }
    assert not missing, (
        f"the adapter contract lost {sorted(missing)}; ADR-0047 promoted this boundary and a "
        "redesign must be argued in an ADR, not absorbed"
    )

    # And every adapter must still speak it. A contract only the first adapter remembers is
    # documentation, not a boundary.
    for path in sorted(ADAPTERS.glob("adapter_*.py")):
        text = path.read_text(encoding="utf-8")
        absent = {
            name for name in ("ticket_id", "ok", "diff", "raw_tail") if name not in text
        }
        assert not absent, (
            f"{path.name} does not speak {sorted(absent)} of the outcome contract"
        )


def test_a_new_adapter_may_not_silently_exceed_the_largest_one():
    """A boundary that never moves while what sits behind it grows is not obviously right.

    Measured 20 Aug 2026 across eight adapter modules: 78, 90, 107, 124, 130, 148, 233, and
    **295** for Grok — the newest is 3.8x the smallest. The contract held; that is not the
    same as adapters being cheap, and conflating the two is the easy mistake ADR-0047 exists
    to prevent.

    This does not forbid a larger adapter. It forces the excess to be argued in the commit
    rather than absorbed silently, which is the ratchet shape used for `append()` bypass and
    the A3 refusal baseline. Raising the constant is the permitted edit; doing it without a
    reason in the message is not.
    """
    lines = _adapter_lines()
    assert lines, "no adapters found; the path in ADR-0047's check is wrong"
    worst = max(lines.values())
    assert worst <= 295, (
        f"an adapter now exceeds the recorded maximum: {max(lines, key=lines.get)} at {worst} "
        "lines. Say in the commit what forced it — contract, vendor, platform or policy."
    )


def without_comments(yaml_text: str) -> str:
    """What the runner would execute, with the prose stripped out.

    A workflow comment may legitimately name the thing the step must not do — that is how a
    repair explains itself. A test that greps the comments is testing prose, and it fails on
    the sentence that documents the fix.
    """
    return "\n".join(
        line for line in yaml_text.splitlines() if not line.strip().startswith("#")
    )


def test_ci_replay_step_carries_a_control_that_can_fail():
    """The CI replay step must not manufacture the subject it then compares against.

    Until 21 August 2026 it ran `beta` before `replay` "so that replay has a subject". The
    subject `cmd_beta` leaves behind is a rebuild from the same log — it calls
    `projection.build`, which unlinks the database — so `identical: true` was guaranteed.
    A fresh checkout carries no `.harness/state.db` at all; it is gitignored. Measured:
    with that sequence, deliberate out-of-band drift produced `identical: true` and the
    gate exited 0.

    It then read `.harness/log`, which ADR-0057 gitignored on the same day, so on a fresh
    checkout the first assertion aborted the step before the detector was exercised at all.
    The subject is now a committed synthetic fixture: the step must read that, and must not
    read a user's trajectory.
    """
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    step = workflow.partition("- name: Replay invariant")[2]
    assert step, "the replay invariant step is gone"
    assert "cli --json beta" not in step, (
        "the replay step seeds its own comparison subject again; a rebuild is not evidence "
        "that the state on disk was intact"
    )
    assert "identical'] is False" in step or 'identical"] is False' in step, (
        "the replay step lost the drift control that proves it can fail"
    )
    commands = without_comments(step)
    assert "tests/fixtures/replay-ci" in commands, (
        "the replay step must read the committed fixture trajectory; anything gitignored is "
        "empty on a fresh checkout and the step aborts before it proves anything"
    )
    assert ".harness/log" not in commands, (
        "the replay step reads a user's trajectory again; it is gitignored (ADR-0057), so in "
        "CI it is empty, and where it is not empty it is not CI's to read"
    )


def test_the_ci_replay_fixture_is_a_non_empty_trajectory(tmp_path):
    """The fixture is the subject of the drift control. If it were empty or unreadable, the
    step's first assertion would abort and the detector would go unexercised — which is the
    exact failure this repair exists to remove."""
    from consilient.cli import cmd_replay

    fixture = Path("tests/fixtures/replay-ci")
    assert fixture.is_dir(), "the committed fixture trajectory is gone"
    result = cmd_replay(
        argparse.Namespace(log=str(fixture), db=str(tmp_path / "replay.db"))
    )
    assert result["events"] == 1


def test_foreign_identifier_check_is_wired_into_ci_and_cannot_be_silently_unwired():
    """A leak class with a checker and no CI step is a checker nobody runs.

    `check_foreign_identifiers.py` was written on 21 August 2026 after an audit found 71
    commit identifiers from a private commercial repository in a tracked results file, and
    it shipped with no CI step: the tracked tree was scanned only when someone remembered.
    """
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    step = workflow.partition("- name: Foreign identifier invariant check")[
        2
    ].partition("- name:")[0]

    assert "run: python .github/scripts/check_foreign_identifiers.py" in step
    assert Path(".github/scripts/check_foreign_identifiers.py").is_file()
    checkout = workflow.partition("- uses: actions/checkout@v4")[2].partition(
        "- uses:"
    )[0]
    assert "fetch-depth: 0" in checkout, (
        "a shallow clone cannot tell this repository's own commits from foreign ones; "
        "the foreign-identifier step would fail red on history it cannot see"
    )


def test_the_private_corpus_check_is_deliberately_not_in_ci():
    """The declined half of the same repair, pinned so nobody "helpfully" adds it later.

    `check_private_corpus.py` matches paths inside `../hireable-3.0` and `../jobboard-v2`,
    which do not exist on a GitHub runner; its own docstring says so. Wired into CI it would
    scan nothing and report green, which is worse than no gate — a green tick is read as
    evidence. It runs locally, in the pre-push hook, or not at all.
    """
    workflow = without_comments(
        Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    )

    assert "check_private_corpus" not in workflow, (
        "a check that cannot see its subject on a runner must not report green there; "
        "check_private_corpus runs locally and in .githooks, not in GitHub Actions"
    )


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

# ------------------------------------------ working principle 9, find the bar, 21 Aug 2026
SUPERLATIVE = re.compile(
    # Deliberately narrow: a claim about EVERYONE ELSE's work, not a self-limiting statement.
    # A first draft matched a bare "nothing else" and fired on README:142, "records trajectory
    # events ... and does nothing else" -- which limits our own scope and claims nothing about
    # anyone. A check that fires on innocent prose gets suppressed and then protects nothing,
    # so the pattern names the shapes that actually went wrong.
    r"\b(nothing (?:on the market|out there|in the (?:field|literature))|"
    r"no (?:one|body) else|no other (?:system|harness|tool|project|product)|"
    r"the only (?:system|harness|tool|project|product)|"
    r"the first (?:system|harness|tool|project|product))\b",
    re.IGNORECASE,
)

# A superlative is a claim about everyone else's work, so it needs a source like any other claim.
CITATION = re.compile(
    r"arXiv:|doi\.|https?://|\[cited\]|\(\d{4}\)|et al\.", re.IGNORECASE
)

PUBLIC_PROSE = ("README.md", "CONSILIENCE.md")


def test_a_superlative_claim_carries_its_citation():
    """Public-facing prose may not claim to beat everyone without saying who it beat.

    Joe, 21 August 2026: "we should always enforce aiming for better than the best that
    already exists", and "we need to always be finding where the bar is and raising it."
    Finding the bar is the work. A superlative is the moment a bar is claimed to be cleared,
    so it is exactly where the evidence has to be.

    This exists because we breached it. `README.md` claimed "Nothing on the market measures
    it" while eight published systems measured beta, Reflexion among them since 2023 -- and
    this repository's own experiment register said so while the README contradicted it.
    [measured] The claim sat in the public shop window of a project about measurement honesty.

    A citation on the same line or the two lines below satisfies this. The check is
    deliberately narrow: it catches the specific shape that went wrong rather than policing
    confident prose, because a check that fires on everything gets suppressed and then
    protects nothing.
    """
    offenders: list[str] = []
    for name in PUBLIC_PROSE:
        path = Path(name)
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines):
            if not SUPERLATIVE.search(line):
                continue
            window = " ".join(lines[number : number + 3])
            if not CITATION.search(window):
                offenders.append(f"{name}:{number + 1}: {line.strip()[:90]}")
    assert not offenders, (
        "a superlative claim in public-facing prose carries no citation. Name the incumbent "
        "and the evidence, or drop the claim:\n  " + "\n  ".join(offenders)
    )


# ------------------------------------------ working principle 11, decide under uncertainty
def test_provisional_adrs_name_a_live_experiment():
    """A PROVISIONAL decision must name the experiment that would settle it.

    Joe, 22 August 2026: "If we cant get definitive answers we need to get to the best
    estimate and ensure those answers are constantly strived for with experimentation."

    PROVISIONAL is the honest status for a decision resting on `[asserted]` evidence, and the
    writing-adrs skill already requires it to carry "a named experiment that would confirm or
    kill it". Nothing enforced that. An estimate with no route to becoming a measurement is a
    guess that has stopped trying, and this repository has thirteen catalogued cases of a
    documented rule with nothing behind it.

    The check is deliberately narrow. It does not judge whether the experiment is good, only
    that the ADR names one and that the register knows it. A check that tried to judge quality
    would fire on everything and get suppressed, and then protect nothing.
    """
    register = Path("docs/10-research/experiment-register.md")
    if not register.exists():  # pragma: no cover - repository-only check
        pytest.skip("no experiment register in this checkout")
    known = set(
        re.findall(
            r"^###\s+(EXP-\d+)\b",
            register.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    )

    offenders: list[str] = []
    for adr in sorted(Path("docs/decisions").glob("0*.md")):
        text = adr.read_text(encoding="utf-8")
        if not re.search(
            r"^\s*-?\s*\*\*Status:\*\*.*PROVISIONAL", text, re.MULTILINE | re.IGNORECASE
        ):
            continue
        status = re.search(
            r"^\s*-?\s*\*\*Status:\*\*.*PROVISIONAL.*$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        overturn = re.search(
            r"^## What would overturn this[^\n]*\n(.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.IGNORECASE | re.DOTALL,
        )
        updates = "\n".join(
            re.findall(
                r"^## Update:[^\n]*\n(.*?)(?=^## |\Z)",
                text,
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            )
        )
        nominated = set(
            re.findall(
                r"EXP-\d+",
                (status.group(0) if status else "")
                + "\n"
                + (overturn.group(1) if overturn else "")
                + "\n"
                + updates,
            )
        )
        if not nominated:
            offenders.append(f"{adr.name}: PROVISIONAL but nominates no experiment")
        elif not nominated & known:
            unknown = ", ".join(sorted(nominated))
            offenders.append(
                f"{adr.name}: nominates {unknown}, absent from register headings"
            )

    assert not offenders, (
        "a PROVISIONAL decision must name the experiment that would settle it, and that "
        "experiment must exist in the register:\n  " + "\n  ".join(offenders)
    )


def test_no_effect_path_bypasses_action_and_decision_admission():
    """ADR-0079: raw reach hosts must consume effects.admit_effect / dispatch admission."""

    effects_source = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(Path("src/consilient").glob("effects*.py"))
    )
    # The whole dispatch family: admission moved into a sibling in the 28 August 2026 split,
    # and ADR-0079 is about the dispatch unit, not about one file of it.
    dispatch_source = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(Path("scripts").glob("dispatch*.py"))
    )
    assert "def admit_effect" in effects_source
    assert "run_admitted_fake_effect" in dispatch_source
    assert "admit_effect(" in dispatch_source
    assert "subprocess" not in effects_source
    assert "urllib" not in effects_source
    assert "smtplib" not in effects_source

    # Outbound and computer-use migration are A05/A06; they remain listed here so the
    # allowlist cannot silently grow. Dispatch is the only admitted fake host in A04.
    assert Path("src/consilient_connectors/outbound.py").exists()

    from consilient.effects import admit_effect
    from tests.test_action_boundary import manifest_record

    refusal = admit_effect(
        manifest_record(),
        disposition="execute",
        prefix=(),
        intent_id="ratchet-intent",
        receipt_id="ratchet-receipt",
    )
    from consilient.effects import EffectAdmissionRefusal

    assert isinstance(refusal, EffectAdmissionRefusal)


def test_the_loop_prunes_every_workspace_form_not_just_worktrees() -> None:
    """The mechanism behind the test above, asserted separately so a regression names itself.

    Removing the call, or reverting to registration-pruning alone, silently reintroduces a 580GB
    leak that takes days to become visible. The outcome test would eventually catch it; this one
    catches it immediately.
    """
    # The pruner moved to a build_loop sibling in the 28 August 2026 split; this ratchet is
    # about the loop reclaiming clone-form workspaces, wherever in the family that is written.
    loop = Path(".harness/build_loop.py")
    if not loop.is_file():  # pragma: no cover - repository-only check
        pytest.skip("build_loop.py not present in this checkout")
    source = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted(Path(".harness").glob("build_loop*.py"))
    )
    assert "def prune_spent_workspace_dirs(" in source, (
        "the clone-form workspace pruner is gone; only registered worktrees would be reclaimed"
    )
    assert source.count("prune_spent_workspace_dirs(") >= 2, (
        "prune_spent_workspace_dirs is defined but never called from the tick"
    )

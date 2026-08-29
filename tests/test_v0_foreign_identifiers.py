"""The gates standing between this repository and a publication it cannot take back. A
pre-publication audit on 21 August 2026 blocked a push over 71 forty-character commit
identifiers from a private commercial repository sitting in a tracked results file — a
leak class no path-matcher can see, because `check_private_corpus.py` matches file paths
and passed. Measured the same day: run standalone that checker enumerated 2854
distinctive needles and passed; run from the `pre-push` hook it enumerated **17**,
because the inherited GIT_DIR sent both `git ls-files` calls to the repository the hook
came from, reporting 2123 findings that were this repository's own files matching
themselves — and, worse, it would have reported PASS on a tree where those seventeen
wrong needles happened not to match. Hence the scrubbed environment asserted
behaviourally on the script that was unsound and structurally across every checker, and
the binding of an enumeration to the corpus it claims to have read: `cwd=` is a request,
`git rev-parse --show-toplevel` is the answer, and an empty listing is refused because a
gate that checked nothing must never report PASS. The ratchets are three: the un-
allowlisted count is pinned at zero, the bare-identifier total may only fall (25 → 10 on
23 August 2026 once permalinks into public upstreams stopped counting, the first
downward move), and the allowlist may only shrink. The percent-encoding test pins the
escape found on 27 August 2026 in tracked content, written down in plain prose beside
the identifier it hid — `[0-9a-f]{40}` does not match across a `%39`, and it defeated an
independent hand-written sweep the same day for the identical reason."""

from family_source import seam

import os
import re
import subprocess
import sys
from pathlib import Path
import pytest
from v0_invariants_helpers import (
    _spend_scripts,
)


# ------------------------------------------- publication safety, after the 21 Aug 2026 block
def test_foreign_commit_identifiers_may_only_decrease():
    """A pre-publication audit blocked a public push over identifiers no path-matcher can see.

    `check_private_corpus.py` matches FILE PATHS from the private corpora and passed. What it
    could not see: `results-exp43.json` carries **71 forty-character commit SHAs**, none of
    which resolves in this repository. They are commits from a private commercial repository.

    `AGENTS.md` permits the corpora's names and AGGREGATE measured metrics. A list of specific
    commits is neither — it is a list of incidents.

    The count below is the measured state at the moment of discovery and may only ever go DOWN.
    Lowering it is the permitted edit; the fix for EXP-43 is to aggregate the identifiers, not
    to raise this number.
    """
    import subprocess

    script = Path(".github/scripts/check_foreign_identifiers.py")
    if not script.exists():  # pragma: no cover - repository-only check
        pytest.skip("checker not present in this checkout")
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    # One reported line per offending file, plus the header and the two-line explanation.
    offenders = [line for line in result.stdout.splitlines() if line.startswith("- ")]
    total = 0
    for line in offenders:
        match = re.search(r": (\d+) identifier", line)
        if match:
            total += int(match.group(1))

    # Lowered from 85 to 14 on 21 Aug 2026 after EXP-43's 71 private-corpus commit identifiers
    # were pseudonymised. The 14 that remained were benign and identified: ten GitHub permalinks
    # citing upstream projects (julep-ai/julep, mlflow/mlflow), three EXP-49's pre-registration
    # commit, one EXP-05's.
    #
    # Re-based on 21 Aug 2026 from the TOTAL to the UN-ALLOWLISTED count, and this is a
    # tightening rather than a loosening. `total <= 14` conflated two different things: a
    # private-corpus identifier, which must never appear at all, and a public upstream permalink
    # pinning an exact blob, which is ordinary provenance and the reason ten are already cleared
    # below. Under the old form, citing one more upstream file failed the build while a *swap* of
    # a benign identifier for a private one passed it, because the total was unchanged. Under this
    # form every identifier must be individually tested against both corpora with a scrubbed
    # environment and justified in ALLOWLIST before it may appear, and the count that may never
    # rise is the count of unexamined ones. That is strictly harder to satisfy.
    unallowlisted = sum(
        int(m.group(1))
        for line in offenders
        if (m := re.search(r"(\d+) NOT allowlisted", line))
    )
    assert unallowlisted == 0, (
        f"{unallowlisted} foreign commit identifier(s) are not allowlisted; publishing them "
        "could put another repository's commit history into a public one. Test each against "
        "both private corpora with a scrubbed environment, then allowlist it with a reason or "
        "aggregate it away."
    )
    # Raised 16 → 17 on 21 Aug 2026: 4c0b901 made EXP-96's `run_exp96.py` tracked, adding
    # its second per-file copy of the itsdangerous 2.2.0 pin 096c8d4… — the identifier
    # corpus-tested against both private corpora and allowlisted in f83f6c1 ("resolves in
    # neither"). The unexamined count above is unchanged and remains the guard that bites.
    # Raised 17 → 18 on 22 Aug 2026: a spec-critic dispatch cited ruvnet/ruflo in
    # `bibliography.md` by public permalink. Cleared by positive public provenance — the URL
    # was fetched and resolves inside that repository's public history — rather than by the
    # corpus test the entries above used. The private corpora were not scanned; see the
    # ALLOWLIST reason. The unexamined count above is unchanged and remains the guard that bites.
    # Raised 18 → 20 on 22 Aug 2026. This ceiling counts OCCURRENCES, not distinct entries: the
    # gap-register cites both ends of a public ruvnet/ruflo compare link, and its base revision
    # was already allowlisted via `bibliography.md`, so distinct entries rose by one (15 → 16)
    # while occurrences rose by two. Its eighteen sibling identifiers were NOT allowlisted —
    # they were our own HEAD and working-tree blob digests, and were truncated to twelve
    # characters instead, the convention ALLOWLIST itself uses to avoid tripping this detector.
    # Allowlisting those would have taken this ceiling past 30 and made it meaningless. Every
    # identifier in that file was resolved against both private corpora: none resolved in either.
    # Raised 20 → 21 on 22 Aug 2026: `exp96/results-exp96.json` became tracked, adding one
    # occurrence of the itsdangerous 2.2.0 pin 096c8d4… already allowlisted from
    # `experiment-register.md` and `run_exp96.py` — corpus-tested against both private corpora
    # in f83f6c1, "resolves in neither". The full revision is kept in the results artefact
    # because it is the provenance that makes EXP-96 reproducible, the same class as
    # `results-exp49.json`. The same day's second new occurrence, a duplicate ruvnet/ruflo
    # permalink in `agentic-organisation-bar-2026-08-22.md`, was truncated to twelve
    # characters instead (the gap-register convention), so it adds nothing here. The
    # unexamined count above is unchanged and remains the guard that bites.
    # Raised 21 → 23 on 23 Aug 2026: the triggered-recall research cited two upstream
    # permalinks as prior art — a pinned NousResearch/hermes-agent revision and a
    # ruvnet/ruflo one. Both resolved against BOTH private corpora and appear in neither;
    # the Hermes URL was fetched and resolves. THIS CEILING IS NOW RISING ONCE PER RESEARCH
    # STREAM, which is a growth the ratchet was not designed to absorb: it is meant to fall
    # as citations are aggregated away, not climb as prior art is cited properly. The
    # structural answer is to separate a BARE identifier — how the original leak actually
    # looked — from one embedded in a public forge URL that names its own repository, and
    # that is queued as a unit rather than decided inside a ratchet raise.
    #
    # 25 → 10, downward, because the queued structural fix landed on 23 Aug 2026. The check
    # now strips permalinks into public upstreams before counting -- a bare 40-hex string is
    # what the leak actually looked like, while `github.com/OWNER/REPO/commit/<sha>` names its
    # own repository in public in the same string. Twelve public upstreams are cited in `docs/`
    # today; each of them was previously inflating this number, which is why it rose once per
    # research stream.
    #
    # This is the first time this ceiling has moved down, and moving down is the whole point:
    # a ratchet that only ever loosens is not a ratchet, it is a record of surrender (F-12).
    # Occurrences fell 25 → 10 and distinct identifiers 18 → 6, so twelve ALLOWLIST entries
    # are now unused. They are left in place deliberately -- removing entries from a security
    # allowlist by hand, in the same change that alters what the gate counts, is two edits
    # whose interaction nobody can review. It is queued on its own.
    assert total <= 10, (
        f"the bare foreign-identifier total rose to {total}. Every one is individually cleared, "
        "so this is not yet a leak. But these are BARE identifiers now -- permalinks into public "
        "upstreams no longer count here -- so a rise means something leak-shaped entered the "
        "tree, not that someone cited prior art. Sharpen the discriminator or clear the "
        "identifier against both corpora; do not raise this ceiling to make it pass."
    )


# ------------------------------------ the 21 Aug 2026 environment-leak repair, three invariants
GATE_SCRIPTS = sorted(Path(".github/scripts").glob("check_*.py"))


def _load_gate(name):
    """Import a .github/scripts checker by path, without putting it on sys.path for good."""
    import importlib.util

    path = Path(".github/scripts") / name
    if not path.exists():  # pragma: no cover - repository-only check
        pytest.skip(f"{name} not present in this checkout")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny_repo(directory):
    """A real git repository with one commit, for binding tests."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "kept.txt").write_text("x", encoding="utf-8")
    for command in (
        ["init", "-q"],
        ["config", "user.email", "t@example.invalid"],
        ["config", "user.name", "t"],
        ["add", "."],
        ["commit", "-qm", "c"],
    ):
        subprocess.run(
            ["git", *command], cwd=directory, env=env, capture_output=True, check=True
        )
    return directory


def test_gate_scripts_scrub_the_git_environment(tmp_path, monkeypatch):
    """Git hands every hook GIT_DIR, and GIT_DIR overrides cwd.

    Measured 21 August 2026: run standalone, `check_private_corpus.py` enumerated 2854
    distinctive needles from the two private corpora and passed. Run from the `pre-push` hook
    it enumerated **17**, because the inherited GIT_DIR sent both `git ls-files` calls to the
    repository the hook came from. It then reported 2123 findings that were this repository's
    own files matching themselves -- and, worse, would have reported PASS on a tree where those
    seventeen wrong needles happened not to match.

    Two assertions. The first is behavioural on the script that was actually unsound: poison
    GIT_DIR and the enumeration must still describe the directory it was handed. The second is
    structural across every checker, because behavioural coverage of all four is expensive and
    the leak is a one-line omission that reappears the moment someone adds a git call.
    """
    module = _load_gate("check_private_corpus.py")
    wanted = _tiny_repo(tmp_path / "wanted")
    decoy = _tiny_repo(tmp_path / "decoy")
    (decoy / "decoy-only.txt").write_text("y", encoding="utf-8")

    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))
    # GIT_ENV is captured at import; re-derive it the way the module does so the test proves
    # the scrub itself and not a stale snapshot taken before monkeypatch ran.
    monkeypatch.setattr(
        seam("dispatch_vocabulary"),
        "GIT_ENV",
        {k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert module.ls_files(wanted) == ["kept.txt"], (
        "an inherited GIT_DIR redirected the enumeration to another repository"
    )

    assert len(GATE_SCRIPTS) >= 4, (
        "the structural half of this test found nothing to check"
    )
    for script in GATE_SCRIPTS:
        source = script.read_text(encoding="utf-8")
        assert source.count("subprocess.run(") == source.count("env=GIT_ENV"), (
            f"{script.name} spawns a subprocess without env=GIT_ENV; a git call that "
            "inherits GIT_DIR reads whatever repository the hook came from"
        )


def test_corpus_enumeration_is_bound_to_the_corpus(tmp_path, monkeypatch):
    """`--require-corpora` must mean "I read those corpora", not "those directories exist".

    The old check was `(corpus / ".git").exists()` and nothing more. Under the environment leak
    it printed "from 2 corpora" while enumerating a different repository entirely, so on a tree
    where the wrong needles did not match, the one gate protecting private commercial code
    would have reported PASS having read neither corpus. [measured 21 Aug 2026]

    `cwd=` is a request. `git rev-parse --show-toplevel` is the answer, and a mismatch is now a
    hard failure rather than a quiet substitution.
    """
    module = _load_gate("check_private_corpus.py")
    repo = _tiny_repo(tmp_path / "repo")
    inner = repo / "inner"
    inner.mkdir()
    # Tracked content inside `inner`, so `git ls-files` run from there returns a NON-EMPTY
    # listing. Without it this test passes through the empty-listing branch instead of the
    # binding check, and is inert against the mutation it exists to catch. Measured.
    (inner / "inner.txt").write_text("y", encoding="utf-8")
    for command in (["add", "."], ["commit", "-qm", "inner"]):
        subprocess.run(
            ["git", *command],
            cwd=repo,
            env=module.GIT_ENV,
            capture_output=True,
            check=True,
        )

    # A subdirectory of a repository: git answers happily, with the WRONG toplevel.
    with pytest.raises(module.BindingError):
        module.ls_files(inner)

    # An empty listing is refused too: a corpus that yields no paths yields no needles, and a
    # gate that checked nothing must never report PASS.
    empty = _tiny_repo(tmp_path / "empty")
    subprocess.run(
        ["git", "rm", "-q", "kept.txt"],
        cwd=empty,
        env=module.GIT_ENV,
        capture_output=True,
        check=True,
    )
    with pytest.raises(module.BindingError):
        module.ls_files(empty)

    # And the failure must reach the exit status, not just the stack.
    monkeypatch.setattr(module, "CORPORA", [inner])
    monkeypatch.setattr(sys, "argv", ["check_private_corpus.py", "--require-corpora"])
    (inner / ".git").mkdir()  # satisfies the old, insufficient presence test
    assert module.main() == 1, (
        "a corpus that could not be bound to its enumeration must fail the gate"
    )


def test_foreign_identifier_gate_can_pass_and_still_refuses_the_unknown():
    """A condition that can never pass teaches people to bypass it.

    `check_foreign_identifiers.py` exited non-zero on fourteen occurrences that had already
    been examined and cleared, and `pre-push` refuses on any non-zero exit -- so the gate could
    never pass, which is the defect catalogued in
    `docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`.

    The allowlist is the ratchet: it may shrink, never grow, and every entry carries a
    justification. Entries are SHA-256 digests, so the allowlist cannot itself become the leak
    and cannot trip its own detector.
    """
    module = _load_gate("check_foreign_identifiers.py")

    # Raised 12 -> 13 on 21 Aug 2026 for a public permalink into nexu-io/open-design, added by
    # the `using-open-design` skill and cleared by the test this ratchet exists to compel:
    # `git cat-file -e <sha>^{commit}` against BOTH private corpora with a scrubbed environment,
    # resolving in neither.
    #
    # Recorded rather than silently bumped, because the tension is real and the next person will
    # meet it too. This ceiling makes allowlisting costly so nobody allowlists their way past a
    # leak, which is right. But the gate's own failure message instructs the reader to test a
    # benign identifier and add it here — so a ceiling that forbids growth makes the sanctioned
    # path impossible and turns the gate into a wall, which is the defect catalogued in
    # `docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`. The protection
    # that actually matters is the corpus test, and it is enforced by the un-allowlisted count
    # being pinned at zero in `test_foreign_commit_identifiers_may_only_decrease`. This number
    # stays as a speed bump: raising it requires the corpus result in the same commit.
    # Raised 14 → 15 on 22 Aug 2026 for the ruvnet/ruflo permalink. Note that entry is the
    # first cleared by public resolution rather than by the corpus test, so the wording below
    # no longer describes every entry; the ALLOWLIST reason records which route was used.
    # Raised 15 → 16 on 22 Aug 2026 for the second ruvnet/ruflo revision in a public compare
    # link. Cleared the same way: the URL was fetched and both revisions resolve.
    # Raised 16 → 18 on 23 Aug 2026 for the two upstream prior-art permalinks above.
    # NOT raised on 24 Aug 2026, deliberately. Gate B4's pytest pin first arrived as a bare
    # forty-hex constant and would have needed an entry here. Writing it as a public permalink
    # instead — which names its own repository in the same string — removed the need for one.
    # An allowlist that grows every time the tree cites something public is a gate being paid
    # off in instalments; the entry avoided is worth more than the entry justified.
    assert len(module.ALLOWLIST) <= 18, (
        f"the foreign-identifier allowlist grew to {len(module.ALLOWLIST)}; each entry means "
        "someone cleared that identifier — by the scrubbed corpus test, or by positive public "
        "provenance recorded in its reason. Raise this only with that result in the same commit."
    )
    assert all(reason.strip() for reason in module.ALLOWLIST.values()), (
        "an allowlist entry without a justification is an unexplained exemption"
    )
    assert not module.allowlisted("0" * 40), (
        "an unexamined identifier must never be allowlisted"
    )
    for digest in module.ALLOWLIST:
        assert not module.SHA_RE.search(digest), (
            "a stored digest that reads as a commit id would make this file its own finding"
        )

    # The gate must actually pass. This is the half that a wall fails.
    script = Path(".github/scripts/check_foreign_identifiers.py")
    if not script.exists():  # pragma: no cover - repository-only check
        pytest.skip("checker not present in this checkout")
    result = subprocess.run(
        [sys.executable, str(script), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert result.returncode == 0, (
        "the foreign-identifier gate cannot pass on a clean tree, so pre-push can only ever "
        f"refuse:\n{result.stdout}\n{result.stderr}"
    )


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


def test_a_percent_encoded_identifier_cannot_walk_past_the_gate(
    tmp_path, monkeypatch
) -> None:
    """MEASURED 27 August 2026 by a pre-publication audit, in tracked content.

    `docs/00-context/grok-arm-2026-08-23.md` carried a 40-hex upstream revision whose final
    character was written `%39`, and said in plain prose on the same line that it was encoded
    "so the public-repository foreign-identifier gate does not mistake cited upstream provenance
    for a private commit". A working, documented technique for stepping around the one check
    that exists because 71 private commit identifiers reached a results file.

    It also defeated an independent hand-written sweep run the same day, for the identical
    reason: `[0-9a-f]{40}` does not match across a `%39`. Two checks, one escape, both blind.

    The escape was not even needed -- `strip_public_citations` already exempts a permalink into
    a public forge, which that line was. But a gate a contributor can step around by escaping a
    single character is not a gate, and this one had the escape written down beside it where the
    next person would copy it.
    """
    gate = _load_gate("check_foreign_identifiers.py")

    foreign = "d" * 40  # resolves in no repository
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "resolves_here", lambda _sha: False)

    plain = tmp_path / "plain.md"
    plain.write_text(f"see commit {foreign} upstream\n", encoding="utf-8")
    assert gate.scan(["plain.md"]), "a bare foreign identifier must be caught"

    # The same identifier, last character percent-encoded. This is the exact shape found.
    encoded = tmp_path / "encoded.md"
    encoded.write_text(f"see commit {foreign[:-1]}%64 upstream\n", encoding="utf-8")
    assert gate.scan(["encoded.md"]), (
        "a percent-encoded foreign identifier walked past the gate; the escape still works"
    )

    # And the legitimate case still passes: a permalink into a PUBLIC forge is a citation,
    # whether or not anyone escaped a character in it.
    cited = tmp_path / "cited.md"
    cited.write_text(
        f"[upstream](https://github.com/xai-org/grok-build/blob/{foreign}/src/x.rs)\n",
        encoding="utf-8",
    )
    assert not gate.scan(["cited.md"]), (
        "a public-forge permalink is a citation and must not need an escape to pass"
    )

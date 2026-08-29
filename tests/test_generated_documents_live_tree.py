"""The committed tree, not the checker's mechanics.

Every test in the sibling modules exercises the checker and the producers against
throwaway roots, and all of them can pass while the real generated documents are drifted
— which is exactly what happened. On 23 August 2026 all eight tests then in the file
passed while both `docs/decisions/index.md` and `docs/40-spec/requirements.md` were
drifted. The checker itself said so, exiting 1 with `checked=2 adverse=2`, and nothing
consumed that exit code: it was wired into no workflow and no test. [measured] A check
whose result nobody reads is a report.

So these four read the repository. The committed manifest lists exactly the three
generated outputs; the checker exits 0 over the live tree; `README.md`'s stated counts
match what is on disk — they were out by roughly a factor of three on 23 August 2026,
claiming 34 ADRs and 35 registered experiments while the tree held 95 and 109 [measured]
— and `docs/project-facts.md` agrees with the ADRs, experiments, specs and version it is
derived from, with the checker reporting `checked=3 adverse=0`. A number in public prose
is a claim like any other."""

import pathlib
import re
import os
import json
import subprocess
import sys
import pytest
from generated_documents_helpers import (
    CHECKER,
    MANIFEST,
    ROOT,
    _fact_value,
)

EXP_HEADING = re.compile(r"^#{2,4}\s*EXP-\d+", re.MULTILINE)


def test_repository_manifest_matches_committed_generated_documents() -> None:
    if not MANIFEST.is_file():
        pytest.skip("manifest not built yet")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    outputs = [entry["output"] for entry in manifest["entries"]]
    assert outputs == [
        "docs/40-spec/requirements.md",
        "docs/decisions/index.md",
        "docs/project-facts.md",
    ]


def test_the_committed_generated_documents_are_not_currently_drifted():
    """The live tree, not the checker's mechanics.

    Every other test in this file exercises the checker against fixtures, and all eight passed on
    23 August 2026 while BOTH real generated documents were drifted -- `docs/decisions/index.md`
    and `docs/40-spec/requirements.md`. The checker itself said so, exiting 1 with
    `checked=2 adverse=2`, and nothing consumed that exit code: it was wired into no workflow and
    no test. A check whose result nobody reads is a report. [measured]
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    script = root / ".github" / "scripts" / "check_generated_documents.py"
    assert script.is_file(), "the generated-document checker must exist"
    run = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert run.returncode == 0, (
        "a generated document has drifted from its producer. Re-run the producer and commit the "
        f"result; do not edit the generated file by hand. {run.stdout} {run.stderr}"
    )


def test_the_readme_counts_match_what_is_on_disk():
    """Restated numbers drift, and these drifted by a factor of three.

    On 23 August 2026 README.md claimed 34 ADRs and 35 registered experiments while the tree held
    95 and 109. [measured] The counts sit in the public shop window of a project whose subject is
    measurement honesty, which makes a stale count the same class of defect as an uncited
    superlative -- and that one already has a check.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace")
    adrs = len(list((root / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")))
    register = (root / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8", errors="replace"
    )
    exps = len(re.findall(r"^#{2,4}\s*EXP-\d+", register, re.M))
    for claimed, actual, what in (
        (re.search(r"(\d+) ADRs", readme), adrs, "ADRs"),
        (
            re.search(r"(\d+) registered experiments", readme),
            exps,
            "registered experiments",
        ),
    ):
        assert claimed, (
            f"README no longer states a count of {what}; update this check with it"
        )
        assert int(claimed.group(1)) == actual, (
            f"README claims {claimed.group(1)} {what}; the tree holds {actual}. "
            "Correct the README — a number in public prose is a claim like any other."
        )


def test_live_project_facts_counts_match_disk() -> None:
    facts = ROOT / "docs" / "project-facts.md"
    assert facts.is_file(), "docs/project-facts.md must be generated"
    text = facts.read_text(encoding="utf-8")
    adrs = len(list((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")))
    register = (ROOT / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8"
    )
    experiments = len(EXP_HEADING.findall(register))
    specs = len(list((ROOT / "docs" / "superpowers" / "specs").glob("*.md")))
    version = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert version is not None
    assert _fact_value(text, "adr_count") == str(adrs)
    assert _fact_value(text, "experiment_count") == str(experiments)
    assert _fact_value(text, "spec_count") == str(specs)
    assert _fact_value(text, "version") == version.group(1)
    run = subprocess.run(
        [sys.executable, str(CHECKER), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "docs/project-facts.md" in run.stdout
    assert "checked=3" in run.stdout
    assert "adverse=0" in run.stdout

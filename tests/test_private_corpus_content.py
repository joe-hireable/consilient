"""Behavioural check for private-corpus content fingerprints.

Each long normalised line is one shingle. Changing one word invalidates that line's hash,
but a multi-line excerpt still matches its unchanged surrounding shingles. An isolated
single-line excerpt with an edited word is deliberately below this detector's guarantee.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(".github/scripts/check_private_corpus.py")
SPEC = importlib.util.spec_from_file_location("check_private_corpus", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

EXCERPT = """\
The synthetic review records a deliberately distinctive sequence of operational decisions so a copied passage cannot resemble routine project boilerplate by accident.
Its middle sentence identifies the stewardship boundary and explains why the fabricated material belongs only to this temporary test corpus during verification.
The closing sentence supplies another unusually specific run of words so one local edit still leaves an independent neighbouring fingerprint for the detector.
"""


def test_content_scan_detects_an_excerpt_and_survives_one_changed_word(
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "corpus"
    public = tmp_path / "public"
    corpus.mkdir()
    public.mkdir()
    (corpus / "assessment.md").write_text(EXCERPT, encoding="utf-8")

    (public / "leak.md").write_text(EXCERPT, encoding="utf-8")
    (public / "clean.md").write_text(
        "A separate synthetic document uses unrelated language throughout and therefore "
        "must not be mistaken for material copied from the temporary corpus fixture.\n",
        encoding="utf-8",
    )
    (public / "edited.md").write_text(
        EXCERPT.replace("stewardship", "custodianship"), encoding="utf-8"
    )

    needles = CHECKER.content_needles(corpus, ["assessment.md"])

    verbatim = CHECKER.scan_content(public, ["leak.md"], needles)
    assert verbatim and {finding[0] for finding in verbatim} == {"leak.md"}
    assert all(len(finding[2]) == 64 for finding in verbatim)
    assert CHECKER.scan_content(public, ["clean.md"], needles) == []

    edited = CHECKER.scan_content(public, ["edited.md"], needles)
    assert edited and {finding[0] for finding in edited} == {"edited.md"}
    assert {finding[1] for finding in edited} == {1, 3}

    with pytest.raises(CHECKER.BindingError):
        CHECKER.content_needles(corpus, ["missing.md"])
    (corpus / "short.txt").write_text("not distinctive", encoding="utf-8")
    with pytest.raises(CHECKER.BindingError):
        CHECKER.content_needles(corpus, ["short.txt"])

"""EXP-50 arm-B generator: schema, tests/ refusal, no working-tree mutation."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "exp50_faults.py"
SRC = ROOT / "src" / "consilient"

_spec = importlib.util.spec_from_file_location("exp50_faults", SCRIPT)
assert _spec is not None and _spec.loader is not None
exp50 = importlib.util.module_from_spec(_spec)
sys.modules["exp50_faults"] = exp50
_spec.loader.exec_module(exp50)

CandidateError = exp50.CandidateError
generate_candidates = exp50.generate_candidates
load_arm_b_context = exp50.load_arm_b_context
main = exp50.main
parse_diff_paths = exp50.parse_diff_paths
reject_test_contents = exp50.reject_test_contents
tree_sha256 = exp50.tree_sha256
validate_candidate = exp50.validate_candidate


VALID_DIFF = """--- a/src/consilient/beta.py
+++ b/src/consilient/beta.py
@@ -35,7 +35,7 @@
 MIN_REJECTIONS = 30
"""


def _candidate(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "arm": "B",
        "family": "xai",
        "invariant": "a measured beta needs at least MIN_REJECTIONS rejections",
        "diff": VALID_DIFF,
        "files": ["src/consilient/beta.py"],
        "ts": "2026-08-21T15:34:07+00:00",
    }
    record.update(overrides)
    return record


def test_schema_accepts_well_formed_arm_b_record():
    got = validate_candidate(_candidate())
    assert got["arm"] == "B"
    assert got["family"] == "xai"
    assert got["files"] == ["src/consilient/beta.py"]
    assert "MIN_REJECTIONS" in got["invariant"]


def test_schema_rejects_missing_fields():
    with pytest.raises(CandidateError, match="missing required field"):
        validate_candidate({"arm": "B", "family": "xai"})


def test_schema_rejects_naive_timestamp():
    with pytest.raises(CandidateError, match="RFC3339"):
        validate_candidate(_candidate(ts="2026-08-21T15:34:07"))


def test_candidate_whose_diff_touches_tests_is_rejected():
    diff = """--- a/tests/test_v0_invariants.py
+++ b/tests/test_v0_invariants.py
@@ -1,3 +1,3 @@
-keep
+break
"""
    with pytest.raises(CandidateError, match="rejected"):
        validate_candidate(
            _candidate(diff=diff, files=["tests/test_v0_invariants.py"])
        )


def test_candidate_whose_files_escape_into_tests_is_rejected():
    diff = """--- a/src/consilient/../../tests/secret.py
+++ b/src/consilient/../../tests/secret.py
@@ -1,2 +1,2 @@
-a
+b
"""
    with pytest.raises(CandidateError):
        validate_candidate(
            _candidate(
                diff=diff,
                files=["src/consilient/../../tests/secret.py"],
            )
        )


def test_parse_diff_paths_strips_ab_prefix():
    assert parse_diff_paths(VALID_DIFF) == ["src/consilient/beta.py"]


def test_generator_rejects_test_file_contents_in_context():
    context = {
        "src/consilient/beta.py": "MIN_REJECTIONS = 30\n",
        "tests/test_v0_invariants.py": "def test_x():\n    assert False\n",
    }
    with pytest.raises(CandidateError, match="must not be passed test file"):
        reject_test_contents(context)
    with pytest.raises(CandidateError, match="must not be passed test file"):

        def proposer(_ctx: dict[str, str]) -> list[dict[str, object]]:
            return [_candidate()]

        generate_candidates(context, proposer, n=1)


def test_load_arm_b_context_does_not_include_tests():
    spec = ROOT / "docs" / "40-spec" / "v0-draft.md"
    context = load_arm_b_context(SRC, spec)
    assert any(path.startswith("src/consilient/") for path in context)
    assert spec.as_posix().replace("\\", "/") in {
        path.replace("\\", "/") for path in context
    } or "docs/40-spec/v0-draft.md" in context
    assert not any(exp50.is_test_path(path) for path in context)


def test_stub_proposer_does_not_mutate_repo(tmp_path: Path):
    before = tree_sha256(SRC)
    src_listing = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
    )

    def proposer(_context: dict[str, str]) -> list[dict[str, object]]:
        return [_candidate()]

    code = main(
        [
            "--src",
            str(SRC),
            "--spec",
            str(ROOT / "docs" / "40-spec" / "v0-draft.md"),
            "--out",
            str(tmp_path / "exp50"),
            "--n",
            "1",
            "--model-id",
            "stub",
        ],
        proposer=proposer,
    )
    assert code == 0
    assert tree_sha256(SRC) == before
    after_listing = sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    assert after_listing == src_listing
    written = tmp_path / "exp50" / "candidates.jsonl"
    manifest = json.loads((tmp_path / "exp50" / "manifest.json").read_text(encoding="utf-8"))
    assert written.is_file()
    lines = written.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["arm"] == "B"
    assert record["files"] == ["src/consilient/beta.py"]
    assert manifest["tests_shown"] is False
    assert manifest["adjudication"] == "pending"
    assert manifest["n"] == 1
    assert manifest["src_consilient_sha256"] == before
    assert not (SRC / "candidates.jsonl").exists()

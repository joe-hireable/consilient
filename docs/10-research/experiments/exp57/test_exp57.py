"""Paired tests for EXP-57.

Every guard here is exercised against input it should reject, not only against its
happy path. Two checks in this repository were found structurally incapable of
failing and both had passing tests; that is the failure mode these tests target.

    python -m pytest docs/10-research/experiments/exp57/test_exp57.py -q
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import run_exp57 as R  # noqa: E402


# ------------------------------------------------------------------------- statistics


def test_wilson_interval_and_its_empty_denominator():
    assert R.wilson_interval(0, 0) == (0.0, 0.0)
    low, high = R.wilson_interval(0, 10)
    assert low == 0.0 and 0.0 < high < 1.0
    low, high = R.wilson_interval(10, 10)
    assert high == 1.0 and 0.0 < low < 1.0
    low, high = R.wilson_interval(5, 10)
    assert low < 0.5 < high


def test_newcombe_interval_spans_zero_only_when_it_should():
    same = R.newcombe_interval(32, 64, 32, 64)
    assert same[0] <= 0.0 <= same[1], "identical proportions must not show a difference"

    apart = R.newcombe_interval(60, 64, 4, 64)
    assert apart[0] > 0.0, "a 0.88 gap at n=64 must exclude zero"

    marginal = R.newcombe_interval(36, 64, 32, 64)
    assert marginal[0] <= 0.0 <= marginal[1], "a 4/64 gap must not read as a difference"

    assert R.newcombe_interval(1, 0, 1, 4) == (-1.0, 1.0)


# ------------------------------------------------------------------------- adjudication


@pytest.mark.parametrize(
    "reply, expected",
    [
        ("REJECT", "reject"),
        ("accept", "accept"),
        ("The answer is ACCEPT.", "accept"),
        ("", None),
        ("maybe", None),
        ("ACCEPT or REJECT", None),
        ("I would REJECT, though some would ACCEPT", None),
        ("unacceptable", None),
    ],
)
def test_parse_verdict_refuses_what_is_not_a_verdict(reply, expected):
    assert R.parse_verdict(reply) == expected


# ----------------------------------------------------------------------------- corpus


def test_corpus_equivalence_check_rejects_a_doctored_document():
    document = json.loads(R.CORPUS.read_text(encoding="utf-8"))
    counts = R.verify_corpus_excludes_equivalents(document)
    assert counts["equivalent_mutants_excluded_by_exp47"] == 60
    assert counts["non_equivalent_survivors"] == len(document["weakest_guards"])

    doctored = copy.deepcopy(document)
    doctored["raw_counts"]["equivalent_mutants"] = 0
    with pytest.raises(RuntimeError):
        R.verify_corpus_excludes_equivalents(doctored)

    # Trips the arithmetic check alone, leaving the length check satisfied, so
    # neither of the two guards can pass on the other's evidence.
    miscounted = copy.deepcopy(document)
    miscounted["raw_counts"]["true_defects_survived"] = 999
    with pytest.raises(RuntimeError):
        R.verify_corpus_excludes_equivalents(miscounted)

    truncated = copy.deepcopy(document)
    truncated["weakest_guards"] = truncated["weakest_guards"][:-1]
    with pytest.raises(RuntimeError):
        R.verify_corpus_excludes_equivalents(truncated)


def test_locate_requires_a_unique_line():
    lines = ["a = 1", "b = 2", "a = 1", "c = 3"]
    assert R.locate("b = 2", lines) == 1
    assert R.locate("  b = 2  ", lines) == 1
    assert R.locate("a = 1", lines) is None, "ambiguous snippets must not be located"
    assert R.locate("z = 9", lines) is None


def test_build_pool_drops_what_it_cannot_address():
    sources = {"f.py": "x = 1\ny = 2\ny = 2\n"}
    document = {
        "weakest_guards": [
            {
                "id": 1,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "x = 1",
                "mut_snippet": "x = 2",
            },
            {
                "id": 2,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "y = 2",
                "mut_snippet": "y = 3",
            },
            {
                "id": 3,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "a\nb",
                "mut_snippet": "c",
            },
            {
                "id": 4,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "q" * 120,
                "mut_snippet": "r",
            },
            {
                "id": 5,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "x = 1",
                "mut_snippet": "x = 1",
            },
            {
                "id": 6,
                "file": "f.py",
                "operator": "o",
                "orig_snippet": "nope",
                "mut_snippet": "n",
            },
        ]
    }
    pool = R.build_pool(document, sources)
    assert [entry["id"] for entry in pool] == [1], (
        "only the unique, single-line, changed entry"
    )
    assert pool[0]["index"] == 0


def test_select_items_is_deterministic_balanced_and_disjoint():
    pool = [
        {
            "id": n,
            "file": "f.py",
            "index": n,
            "operator": "o",
            "orig_snippet": f"a{n}",
            "mut_snippet": f"b{n}",
        }
        for n in range(R.N_DEFECT + R.N_FIX + 40)
    ]
    first = R.select_items(pool)
    second = R.select_items(list(reversed(pool)))
    assert [i["item_id"] for i in first] == [i["item_id"] for i in second]
    assert sum(i["direction"] == "defect" for i in first) == R.N_DEFECT
    assert sum(i["direction"] == "fix" for i in first) == R.N_FIX
    assert len({i["mutant_id"] for i in first}) == len(first), "no mutant used twice"
    assert all(
        i["truth"] == ("reject" if i["direction"] == "defect" else "accept")
        for i in first
    )


def test_the_control_subset_covers_both_classes():
    """A prefix of item_id is all-defect; the control must exercise alpha too."""
    pool = [
        {
            "id": n,
            "file": "f.py",
            "index": n,
            "operator": "o",
            "orig_snippet": f"a{n}",
            "mut_snippet": f"b{n}",
        }
        for n in range(R.N_DEFECT + R.N_FIX + 40)
    ]
    items = R.select_items(pool)
    prefix = items[: R.CONTROL_ITEMS]
    assert len({i["direction"] for i in prefix}) == 1, "the trap this guards against"

    stride = items[:: len(items) // R.CONTROL_ITEMS]
    assert len(stride) == R.CONTROL_ITEMS
    assert sum(i["direction"] == "defect" for i in stride) == R.CONTROL_ITEMS // 2
    assert sum(i["direction"] == "fix" for i in stride) == R.CONTROL_ITEMS // 2


# ---------------------------------------------------------------------------- prompts


def test_mutate_preserves_indentation_and_changes_one_line():
    text = "def f():\n    return 1\n"
    assert R.mutate(text, 1, "return 2") == "def f():\n    return 2\n"
    assert R.mutate(text, 0, "def g():") == "def g():\n    return 1\n"


def test_directions_are_exact_reverses():
    sources = {"f.py": "def f():\n    return 1\n"}
    base = {
        "file": "f.py",
        "index": 1,
        "orig_snippet": "return 1",
        "mut_snippet": "return 2",
    }
    d_before, d_after = R.before_after({**base, "direction": "defect"}, sources)
    f_before, f_after = R.before_after({**base, "direction": "fix"}, sources)
    assert (d_before, d_after) == (f_after, f_before)
    assert "return 2" in d_after and "return 2" not in d_before


def test_arms_differ_only_in_context_and_never_leak_the_answer():
    sources = {path: R.git_show(R.CORPUS_REV, path) for path in R.SOURCE_FILES}
    tests = {path: R.git_show(R.CORPUS_REV, path) for path in R.TEST_FILES}
    document = json.loads(R.CORPUS.read_text(encoding="utf-8"))
    items = R.select_items(R.build_pool(document, sources))
    padding = R.load_padding()

    defect = next(i for i in items if i["direction"] == "defect")
    fix = next(i for i in items if i["direction"] == "fix")

    sizes = {}
    for arm in R.ARMS:
        prompt, meta = R.build_prompt(arm, defect, sources, tests, padding["body"])
        sizes[arm] = meta["prompt_chars"]
        lowered = prompt.lower()
        for leak in (
            "mutant",
            "mutation",
            "mutmut",
            "ground truth",
            "exp-47",
            "defect item",
        ):
            assert leak not in lowered, f"{arm} prompt leaks {leak!r}"
        assert prompt.count("```diff") == 1

    assert sizes["minimal"] < sizes["relevant"] <= sizes["full"] < sizes["padded"]

    minimal_defect, _ = R.build_prompt(
        "minimal", defect, sources, tests, padding["body"]
    )
    minimal_fix, _ = R.build_prompt("minimal", fix, sources, tests, padding["body"])
    assert minimal_defect != minimal_fix

    full_prompt, _ = R.build_prompt("full", defect, sources, tests, padding["body"])
    padded_prompt, _ = R.build_prompt("padded", defect, sources, tests, padding["body"])
    assert "src/consilient/events.py" in full_prompt
    assert "src/consilient/events.py" not in minimal_defect
    assert padding["body"][:200] in padded_prompt
    assert padding["body"][:200] not in full_prompt


def test_full_arm_shows_the_after_state_so_the_tree_cannot_reveal_the_direction():
    """A tree rendered pristine would mark every defect item as the odd one out.

    This asserts on `build_prompt` itself. An earlier version rebuilt the rendering
    inline and passed while `build_prompt` shipped the pristine tree; it tested its
    own copy of the logic, which is the defect class P2-guards.md catalogues.
    """
    sources = {path: R.git_show(R.CORPUS_REV, path) for path in R.SOURCE_FILES}
    tests = {path: R.git_show(R.CORPUS_REV, path) for path in R.TEST_FILES}
    document = json.loads(R.CORPUS.read_text(encoding="utf-8"))
    items = R.select_items(R.build_pool(document, sources))
    padding = R.load_padding()

    checked = 0
    for item in items[:16]:
        before, after = R.before_after(item, sources)
        prompt, _ = R.build_prompt("full", item, sources, tests, padding["body"])
        for path in R.SOURCE_FILES:
            expected = after if path == item["file"] else sources[path]
            block = f"## {path}\n\n```python\n{expected.rstrip()}\n```"
            assert block in prompt, f"{item['item_id']} {path} is not the after state"
        stale = f"```python\n{before.rstrip()}\n```"
        assert stale not in prompt, f"{item['item_id']} still shows the before state"
        checked += 1
    assert checked == 16


# ------------------------------------------------------------------------ the verdict


def _arm(beta_errors: int, alpha_errors: int, n: int = 64) -> dict:
    return {
        "beta": {"point": beta_errors / n, "errors": beta_errors, "adjudicated": n},
        "alpha": {"point": alpha_errors / n, "errors": alpha_errors, "adjudicated": n},
        "error_rate": {
            "point": (beta_errors + alpha_errors) / (2 * n),
            "errors": beta_errors + alpha_errors,
            "adjudicated": 2 * n,
        },
    }


def _decide(betas: dict[str, int]) -> list[str]:
    arms = {name: _arm(errors, 0) for name, errors in betas.items()}
    return R.decide(arms, R.pairwise(arms, "beta"))["rules_fired"]


def test_every_stopping_rule_including_the_adverse_one_is_reachable():
    flat = _decide({"minimal": 20, "relevant": 20, "full": 20, "padded": 20})
    assert "insufficient power" in flat[0]

    # The outcome that contradicts the principal: full's beta far below minimal's.
    adverse = _decide({"minimal": 60, "relevant": 40, "full": 4, "padded": 6})
    assert "THE PREMISE IS WRONG" in adverse[0]

    degrades = _decide({"minimal": 4, "relevant": 6, "full": 60, "padded": 62})
    assert "minimal materially beats full" in degrades[0]

    poisoned = _decide({"minimal": 4, "relevant": 6, "full": 8, "padded": 60})
    assert "irrelevant context actively degrades" in poisoned[1]

    clean = _decide({"minimal": 20, "relevant": 21, "full": 22, "padded": 60})
    assert "irrelevant context actively degrades" in clean[1]

    not_poisoned = _decide({"minimal": 4, "relevant": 6, "full": 60, "padded": 62})
    assert "no measured context poisoning" in not_poisoned[1]


def test_summarise_excludes_unparsable_replies_from_the_rates():
    def rec(direction, verdict, ok=True, usage=True, tokens=10):
        return {
            "direction": direction,
            "truth": "reject" if direction == "defect" else "accept",
            "verdict": verdict,
            "ok": ok,
            "usage_reported": usage,
            "input_tokens": tokens,
            "model_input_tokens": {"claude-sonnet-5": tokens, "claude-haiku-4-5": 7},
            "seconds": 1.0,
        }

    records = [
        rec("defect", "accept"),
        rec("defect", "reject"),
        rec("defect", None, ok=False),
        rec("fix", "accept"),
        rec("fix", "reject"),
    ]
    summary = R.summarise_arm(records)
    assert summary["beta"] == {
        "point": 0.5,
        "interval_95": list(R.wilson_interval(1, 2)),
        "errors": 1,
        "adjudicated": 2,
        "unparsable": 1,
    }
    assert summary["alpha"]["point"] == 0.5
    assert summary["error_rate"]["adjudicated"] == 4
    assert summary["failed_calls"] == 1
    assert summary["input_tokens"]["total"] == 40
    assert summary["auxiliary_model_input_tokens"]["total"] == 28


def test_a_call_that_reported_no_usage_is_not_counted_as_a_token_measurement():
    """125 calls in the first pass returned a verdict and no usage block.

    Averaging their zeros would have understated the padded arm by a factor of six.
    """
    silent = {
        "direction": "defect",
        "truth": "reject",
        "verdict": "reject",
        "ok": True,
        "usage_reported": False,
        "input_tokens": 0,
        "model_input_tokens": {},
        "seconds": 1.0,
    }
    loud = {**silent, "usage_reported": True, "input_tokens": 41000}
    assert R.usable(loud) and not R.usable(silent)
    summary = R.summarise_arm([silent, loud])
    assert summary["input_tokens"]["mean"] == 41000
    assert summary["input_tokens"]["measured_calls"] == 1
    assert summary["input_tokens"]["usage_not_reported"] == 1
    # the verdict still counts: the answer was given, only the meter was missing
    assert summary["beta"]["adjudicated"] == 2


def test_retry_mode_reopens_exactly_the_unusable_calls(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    rows = [
        {"arm": "full", "item_id": "a", "ok": True, "verdict": "reject", "usage_reported": True, "input_tokens": 9},
        {"arm": "full", "item_id": "b", "ok": True, "verdict": "reject", "usage_reported": False, "input_tokens": 0},
        {"arm": "full", "item_id": "c", "ok": False, "verdict": None, "usage_reported": False, "input_tokens": 0},
        {"arm": "full", "item_id": "d", "ok": True, "verdict": None, "usage_reported": True, "input_tokens": 9},
    ]
    path.write_text("".join(json.dumps(r) + chr(10) for r in rows), encoding="utf-8")
    assert set(R.load_checkpoint(path)) == {("full", k) for k in "abcd"}
    assert set(R.load_checkpoint(path, retry=True)) == {("full", "a")}


def test_discordance_counts_disagreement_the_error_rate_hides():
    """Two arms with identical error rates that disagree on every item."""
    truth = {"a": "reject", "b": "reject", "c": "accept", "d": "accept"}

    def arm(verdicts):
        return [
            {"item_id": k, "verdict": v, "truth": truth[k], "direction": "defect"}
            for k, v in verdicts.items()
        ]

    same = {
        "minimal": arm({"a": "accept", "b": "reject", "c": "accept", "d": "accept"}),
        "full": arm({"a": "reject", "b": "reject", "c": "accept", "d": "reject"}),
    }
    (pair,) = R.discordance(same)
    assert pair["items_in_common"] == 4
    assert pair["verdicts_that_differ"] == 2
    assert (pair["wrong_in_a_only"], pair["wrong_in_b_only"]) == (1, 1)

    agreed = {"minimal": arm(dict(truth)), "full": arm(dict(truth))}
    (clean,) = R.discordance(agreed)
    assert clean["verdicts_that_differ"] == 0
    assert clean["mcnemar_exact_two_sided_p"] == 1.0


def test_mcnemar_exact_matches_the_binomial_by_hand():
    assert R.mcnemar_exact(0, 0) == 1.0
    assert R.mcnemar_exact(1, 1) == 1.0
    assert R.mcnemar_exact(0, 1) == 1.0
    assert R.mcnemar_exact(0, 5) == pytest.approx(2 / 32)
    assert R.mcnemar_exact(1, 9) == pytest.approx(2 * 11 / 1024)
    assert R.mcnemar_exact(0, 20) < 0.001


# ----------------------------------------------------------------------- the executor


def test_call_model_records_a_failure_instead_of_raising(monkeypatch, tmp_path):
    monkeypatch.setattr(R, "claude_argv", lambda: ["definitely-not-a-real-binary-57"])
    outcome = R.call_model("hello", tmp_path)
    assert outcome["ok"] is False
    assert "spawn" in outcome["error"]


def test_call_model_kills_a_call_that_overruns(monkeypatch, tmp_path):
    monkeypatch.setattr(
        R, "claude_argv", lambda: [sys.executable, "-c", "import time; time.sleep(60)"]
    )
    monkeypatch.setattr(R, "CALL_TIMEOUT_S", 3)
    outcome = R.call_model("hello", tmp_path)
    assert outcome["ok"] is False and outcome["error"] == "timeout"
    assert outcome["seconds"] < 30, "the timeout must not be waited out"


def test_checkpoint_replay_prefers_the_later_line(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    path.write_text(
        json.dumps({"arm": "minimal", "item_id": "a", "verdict": None})
        + "\n"
        + json.dumps({"arm": "minimal", "item_id": "a", "verdict": "reject"})
        + "\n\n",
        encoding="utf-8",
    )
    done = R.load_checkpoint(path)
    assert done[("minimal", "a")]["verdict"] == "reject"
    assert R.load_checkpoint(tmp_path / "absent.jsonl") == {}

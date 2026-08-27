"""Z09 — upstream maintainer β with admission bar and decoupled submission."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import beta as beta_mod

ROOT = Path(__file__).resolve().parents[1]


def _ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _upstream_row(
    *,
    verifier_accept: bool = True,
    upstream_ci_outcome: str = "pass",
    human_decision: str = "reject",
    rejection_kind: str | None = "correctness",
    admission_bar_passed: bool = True,
    submission_ts: str | None = None,
    verifier_verdict_ts: str | None = None,
    task_family: str = "upstream_contribution",
    verifier_version: str = "v1",
    authored_by: str = "agent-author",
    classified_by: str = "independent-classifier",
    maintainer_words: str = "this logic is wrong",
) -> dict[str, object]:
    submission = submission_ts or _ts(0)
    verdict = verifier_verdict_ts or _ts(100)
    return {
        "ts": submission,
        "submission_ts": submission,
        "verifier_verdict_ts": verdict,
        "task_family": task_family,
        "verifier_version": verifier_version,
        "verifier_accept": verifier_accept,
        "upstream_ci_outcome": upstream_ci_outcome,
        "human_decision": human_decision,
        "rejection_kind": rejection_kind,
        "admission_bar_passed": admission_bar_passed,
        "estimand_kind": beta_mod.UPSTREAM_MAINTAINER_ESTIMAND_KIND,
        "auth_status": "third_party_maintainer",
        "maintainer_words": maintainer_words,
        "authored_by": authored_by,
        "classified_by": classified_by,
    }


def test_upstream_proxy_rows_are_excluded_from_gate_human_beta() -> None:
    row = _upstream_row()
    assert beta_mod.UPSTREAM_MAINTAINER_ESTIMAND_KIND == (
        beta_mod.UPSTREAM_MAINTAINER_PROXY_BETA
    )
    assert not beta_mod.admits_human_beta_row(row)
    assert not beta_mod.admits_sizing_input(row)
    assert beta_mod.admits_upstream_maintainer_proxy_row(row)


def test_register_preregisters_admission_bar_protocol() -> None:
    text = (ROOT / "docs" / "10-research" / "experiment-register.md").read_text(
        encoding="utf-8"
    )
    heading = "### EXP-144 · Can β be measured on upstream maintainer verdicts"
    start = text.index(heading)
    body = text[start : start + 4000]
    assert "admission bar" in body
    assert "submission timestamp is recorded before the composite verifier" in body
    assert "upstream_maintainer_proxy_beta" in body
    assert "Floor: 0.05" in body
    assert "never weaken" in body
    assert "may not classify its own" in body
    assert "MIN_REJECTIONS" in body


def test_upstream_ci_failure_alone_cannot_enter_numerator() -> None:
    row = _upstream_row(upstream_ci_outcome="fail", human_decision="reject")
    assert beta_mod.refuse_upstream_row(row) == "upstream_ci_not_passed"
    assert beta_mod.upstream_human_verdict_for_beta(row) is None
    assert not beta_mod.counts_toward_upstream_beta_numerator(row)
    mapped = beta_mod.upstream_rows_for_compute([row])
    assert mapped == []


def test_fit_rejection_cannot_enter_numerator() -> None:
    row = _upstream_row(rejection_kind="fit")
    assert beta_mod.upstream_human_verdict_for_beta(row) is None
    assert not beta_mod.counts_toward_upstream_beta_numerator(row)


def test_both_cells_are_representable() -> None:
    accepted_rejected = _upstream_row(verifier_accept=True, human_decision="reject")
    rejected_merged = _upstream_row(verifier_accept=False, human_decision="merge")
    assert beta_mod.both_upstream_cells_representable(
        [accepted_rejected, rejected_merged]
    )
    rejected_merged.pop("verifier_accept")
    assert not beta_mod.both_upstream_cells_representable(
        [accepted_rejected, rejected_merged]
    )


def test_submission_must_precede_the_verifier_verdict() -> None:
    unconditioned = _upstream_row(
        submission_ts=_ts(0),
        verifier_verdict_ts=_ts(100),
    )
    conditioned = _upstream_row(
        submission_ts=_ts(100),
        verifier_verdict_ts=_ts(0),
    )

    assert beta_mod.refuse_upstream_row(unconditioned) is None
    assert beta_mod.refuse_upstream_row(conditioned) is not None
    assert beta_mod.upstream_rows_for_compute([conditioned]) == []

    for invalid_verdict_ts in (
        unconditioned["submission_ts"],
        "2026-08-25T12:00:01",
        "not-a-timestamp",
    ):
        invalid = _upstream_row(
            submission_ts=str(unconditioned["submission_ts"]),
            verifier_verdict_ts=str(invalid_verdict_ts),
        )
        assert beta_mod.refuse_upstream_row(invalid) is not None

    missing = _upstream_row()
    missing.pop("submission_ts")
    assert beta_mod.refuse_upstream_row(missing) is not None


def test_admission_bar_must_pass_before_measurement() -> None:
    row = _upstream_row(admission_bar_passed=False)
    assert beta_mod.refuse_upstream_row(row) == "admission_bar_not_passed"
    assert not beta_mod.counts_toward_upstream_beta_numerator(row)

    row["admission_bar_passed"] = "true"
    assert beta_mod.refuse_upstream_row(row) == "admission_bar_not_passed"

    invalid_verdict = _upstream_row()
    invalid_verdict["verifier_accept"] = "false"
    assert beta_mod.refuse_upstream_row(invalid_verdict) == "invalid_verifier_verdict"


def test_rejection_record_requires_words_and_independent_classifier() -> None:
    missing_words = _upstream_row(maintainer_words="  ")
    assert beta_mod.refuse_upstream_row(missing_words) == "maintainer_words_missing"

    self_classified = _upstream_row(
        authored_by="agent-author",
        classified_by="agent-author",
    )
    assert (
        beta_mod.refuse_upstream_row(self_classified)
        == "author_classified_own_rejection"
    )


def test_composite_rejection_fraction_below_floor_is_insufficient_data() -> None:
    rows = [
        _upstream_row(verifier_accept=True, human_decision="reject") for _ in range(40)
    ]
    result = beta_mod.compute_upstream_maintainer_beta(rows)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.n_rejected == 40
    assert "rejection fraction" in result.caveat.lower()


def test_rejection_fraction_is_scoped_and_the_floor_cannot_be_lowered() -> None:
    rows = [
        _upstream_row(verifier_accept=True),
        _upstream_row(verifier_accept=False, task_family="other"),
        _upstream_row(verifier_accept=False, upstream_ci_outcome="fail"),
    ]
    assert (
        beta_mod.composite_verifier_rejection_fraction(
            rows,
            task_family="upstream_contribution",
            verifier_version="v1",
        )
        == 0.0
    )
    with pytest.raises(ValueError, match="may only raise the floor"):
        beta_mod.compute_upstream_maintainer_beta(
            rows,
            min_composite_rejection_fraction=0.0,
        )


def test_valid_upstream_rows_map_into_compute() -> None:
    rows = [
        _upstream_row(verifier_accept=True, human_decision="reject"),
        _upstream_row(verifier_accept=False, human_decision="merge"),
    ]
    mapped = beta_mod.upstream_rows_for_compute(rows)
    assert len(mapped) == 2
    assert {r["human_verdict"] for r in mapped} == {"reject", "accept"}


def test_upstream_beta_reports_rejection_fraction() -> None:
    rows = []
    for i in range(35):
        rows.append(
            _upstream_row(
                verifier_accept=i % 5 != 0,
                human_decision="reject",
            )
        )
    result = beta_mod.compute_upstream_maintainer_beta(rows)
    assert result.composite_rejection_fraction is not None
    assert 0.0 < result.composite_rejection_fraction < 1.0
    assert result.lower_bound_on_joint_error
    assert "NOT a bound" not in result.render()
    assert "rejection fraction" in result.render().lower()

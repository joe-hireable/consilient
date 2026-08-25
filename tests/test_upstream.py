"""Z11: upstream contribution is a standing capability; its rate is not beta."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from consilient.beta import HUMAN_VERDICT_BETA, admits_human_beta_row, admits_sizing_input
from consilient.harvest import DEFAULT_RELATIVE as HARVEST_DEST
from consilient.harvest import HarvestError
from consilient.upstream import (
    ESTIMAND_KIND,
    MACHINE_AUTHORED_DISCLOSURE,
    OUTCOME_CLASSES,
    OUTCOMES_FILE,
    QUANTITY_NAME,
    AutomatedPolicy,
    HostCIReport,
    HostPolicy,
    OutcomeClass,
    PreparedContribution,
    UpstreamError,
    as_meter_row,
    compute_false_accept_among_accepted,
    parse_host_policy,
    persist_outcome,
    prepare_contribution,
    record_outcome,
    render_false_accept_among_accepted,
    submit_contribution,
    verify_host_ci,
)


ROOT = Path(__file__).resolve().parent.parent
PROHIBITED_CONTRIBUTING = (
    "Thank you for contributing.\n"
    "Automated pull requests are prohibited.\n"
    "Please open an issue first.\n"
)


def _policy(*, automated: AutomatedPolicy = "disclose_required") -> HostPolicy:
    return HostPolicy(
        repository="example/lib",
        automated_pull_requests=automated,
        contributing_text="",
    )


def _prepared(
    *,
    policy: HostPolicy | None = None,
    wanted_on_merits: bool = True,
    verifier_accept: bool = True,
    weakened_to_probe_verifier: bool = False,
    host_ci: HostCIReport | None = None,
) -> PreparedContribution:
    return prepare_contribution(
        repository="example/lib",
        title="Fix the sliding-window estimate",
        body="The estimator misses the architecture.",
        diff="--- a/est.py\n+++ b/est.py\n",
        policy=policy or _policy(),
        wanted_on_merits=wanted_on_merits,
        verifier_accept=verifier_accept,
        weakened_to_probe_verifier=weakened_to_probe_verifier,
        host_ci=host_ci,
    )


def _green(prepared: PreparedContribution) -> HostCIReport:
    return HostCIReport(green=True, summary="all checks passed")


def _red(prepared: PreparedContribution) -> HostCIReport:
    return HostCIReport(green=False, summary="tests failed")


def _sink(prepared: PreparedContribution) -> dict[str, str]:
    return {"locator": "https://example.invalid/example/lib/pull/1"}


def test_prepare_discloses_machine_authorship() -> None:
    prepared = _prepared()
    assert MACHINE_AUTHORED_DISCLOSURE in prepared.body
    assert prepared.repository == "example/lib"
    assert prepared.verifier_accept is True


def test_submit_refuses_when_host_ci_is_not_green(tmp_path: Path) -> None:
    prepared = verify_host_ci(_prepared(), _red)
    assert prepared.host_ci is not None
    assert prepared.host_ci.green is False
    with pytest.raises(UpstreamError, match="CI is not green"):
        submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)


def test_submit_refuses_when_host_ci_was_never_run(tmp_path: Path) -> None:
    with pytest.raises(UpstreamError, match="CI is not green"):
        submit_contribution(_prepared(), sink=_sink, dest=tmp_path, root=ROOT)


def test_submit_refuses_when_policy_prohibits_automated_prs(tmp_path: Path) -> None:
    policy = parse_host_policy("example/lib", PROHIBITED_CONTRIBUTING)
    assert policy.automated_pull_requests == "prohibited"
    prepared = verify_host_ci(_prepared(policy=policy), _green)
    with pytest.raises(UpstreamError, match="prohibits automated"):
        submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)


def test_submit_refuses_a_contribution_not_wanted_on_its_merits(tmp_path: Path) -> None:
    prepared = verify_host_ci(_prepared(wanted_on_merits=False), _green)
    with pytest.raises(UpstreamError, match="wanted on its own merits"):
        submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)


def test_submit_refuses_a_change_weakened_to_probe_the_verifier(
    tmp_path: Path,
) -> None:
    prepared = verify_host_ci(_prepared(weakened_to_probe_verifier=True), _green)
    with pytest.raises(UpstreamError, match="weaken"):
        submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)


def test_submit_refuses_when_our_verifier_did_not_accept(tmp_path: Path) -> None:
    prepared = verify_host_ci(_prepared(verifier_accept=False), _green)
    with pytest.raises(UpstreamError, match="verifier accepted"):
        submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)


def test_prepare_ci_verify_and_submit_when_host_ci_is_green(tmp_path: Path) -> None:
    prepared = verify_host_ci(_prepared(), _green)
    submitted = submit_contribution(prepared, sink=_sink, dest=tmp_path, root=ROOT)
    assert submitted.locator == "https://example.invalid/example/lib/pull/1"
    assert submitted.repository == "example/lib"
    rows = [
        json.loads(line)
        for line in (tmp_path / OUTCOMES_FILE).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows[-1]["kind"] == "upstream.submitted"
    assert rows[-1]["verifier_accept"] is True


def test_every_outcome_class_is_recorded_with_maintainer_words_verbatim(
    tmp_path: Path,
) -> None:
    assert OUTCOME_CLASSES == frozenset(
        {
            "merged",
            "rejected",
            "revised_then_merged",
            "closed_without_decision",
            "non_response",
        }
    )
    words: dict[OutcomeClass, str] = {
        "merged": "LGTM, merging.",
        "rejected": "This breaks the public API.",
        "revised_then_merged": "Please rename the helper; then this is fine.",
        "closed_without_decision": "Closing as stale.",
        "non_response": "",
    }
    comments = ("Please add a test.",)
    for outcome_class, verbatim in words.items():
        recorded = record_outcome(
            contribution_id=f"c-{outcome_class}",
            repository="example/lib",
            outcome_class=outcome_class,
            maintainer_words=verbatim,
            review_comments=comments if outcome_class == "rejected" else (),
            dest=tmp_path,
            root=ROOT,
        )
        assert recorded.outcome_class == outcome_class
        assert recorded.maintainer_words == verbatim
        if outcome_class == "rejected":
            assert recorded.review_comments == comments
    persisted = persist_outcome(
        record_outcome(
            contribution_id="c-roundtrip",
            repository="example/lib",
            outcome_class="rejected",
            maintainer_words="This breaks the public API.",
            review_comments=comments,
            dest=tmp_path,
            root=ROOT,
        ),
        dest=tmp_path,
        root=ROOT,
    )
    rows = [
        json.loads(line)
        for line in persisted.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    last = rows[-1]
    assert last["kind"] == "upstream.outcome"
    assert last["outcome_class"] == "rejected"
    assert last["maintainer_words"] == "This breaks the public API."
    assert last["review_comments"] == ["Please add a test."]
    assert last["estimand_kind"] == ESTIMAND_KIND


def test_false_accept_among_accepted_is_not_beta_and_cannot_enter_the_gate() -> None:
    outcomes = (
        record_outcome(
            contribution_id="c-merge",
            repository="example/lib",
            outcome_class="merged",
            maintainer_words="LGTM",
            dest=Path("."),
            root=ROOT,
            persist=False,
        ),
        record_outcome(
            contribution_id="c-reject",
            repository="example/lib",
            outcome_class="rejected",
            maintainer_words="Wrong.",
            dest=Path("."),
            root=ROOT,
            persist=False,
        ),
        record_outcome(
            contribution_id="c-silence",
            repository="example/lib",
            outcome_class="non_response",
            maintainer_words="",
            dest=Path("."),
            root=ROOT,
            persist=False,
        ),
        record_outcome(
            contribution_id="c-stale",
            repository="example/lib",
            outcome_class="closed_without_decision",
            maintainer_words="Closing as stale.",
            dest=Path("."),
            root=ROOT,
            persist=False,
        ),
    )
    report = compute_false_accept_among_accepted(outcomes)
    assert report.quantity_name == QUANTITY_NAME
    assert "beta" not in report.quantity_name.casefold()
    assert report.quantity_name != "beta"
    assert report.n_submitted == 4
    assert report.n_decided == 2
    assert report.n_rejected == 1
    assert report.n_non_response == 1
    assert report.n_closed_without_decision == 1
    assert report.false_accept_among_accepted == 0.5
    rendered = render_false_accept_among_accepted(report)
    assert "false_accept_among_accepted" in rendered
    assert "NOT beta" in rendered
    assert "NOT a bound" not in rendered
    row = as_meter_row(outcomes[1])
    assert row["estimand_kind"] == ESTIMAND_KIND
    assert row["estimand_kind"] != HUMAN_VERDICT_BETA
    assert not admits_human_beta_row(row)
    assert not admits_sizing_input(row)
    with pytest.raises(UpstreamError, match="not beta"):
        as_meter_row(outcomes[1], estimand_kind=HUMAN_VERDICT_BETA)


def test_non_response_is_not_evidence_of_quality() -> None:
    silent = record_outcome(
        contribution_id="c-silence",
        repository="example/lib",
        outcome_class="non_response",
        maintainer_words="",
        dest=Path("."),
        root=ROOT,
        persist=False,
    )
    report = compute_false_accept_among_accepted((silent,))
    assert report.n_rejected == 0
    assert report.false_accept_among_accepted is None
    assert report.verdict == "insufficient_data"


def test_harvested_outcomes_are_untracked_instance_data() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/training/" in ignored
    from consilient.upstream import DEFAULT_RELATIVE

    assert DEFAULT_RELATIVE == HARVEST_DEST
    assert DEFAULT_RELATIVE.as_posix() == ".harness/training"


def test_persist_refuses_a_path_git_would_publish(tmp_path: Path) -> None:
    outcome = record_outcome(
        contribution_id="c-leak",
        repository="example/lib",
        outcome_class="merged",
        maintainer_words="LGTM",
        dest=tmp_path,
        root=ROOT,
        persist=False,
    )
    with pytest.raises((UpstreamError, HarvestError), match="permits only"):
        persist_outcome(outcome, dest=ROOT / "docs", root=ROOT)

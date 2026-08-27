"""Upstream contribution as a standing capability, with every outcome recorded.

A pull request sent only after our verifier accepted it measures

    P(a maintainer rejects | our verifier accepted)

which is the false-accept rate among accepted work. That is a real number and
this module computes it under the name ``false_accept_among_accepted``.

It is not β. β is P(our verifier accepts | the artefact is bad). The other cell
— artefacts a human judged bad that our verifier rejected — is never submitted,
so it is unobservable here. Reporting the conditional rate as β would be the
failure this project exists to detect.

Live network, subprocess and credentials stay outside this tree. A caller
injects the host-CI runner and the submission sink; this module decides whether
the change may leave and records what came back.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from .beta import HUMAN_VERDICT_BETA, admits_human_beta_row, admits_sizing_input
from .harvest import HarvestError, assert_unpublishable

ESTIMAND_KIND = "false_accept_among_accepted"
QUANTITY_NAME = "false_accept_among_accepted"
OUTCOMES_FILE = "upstream-outcomes.jsonl"
DEFAULT_RELATIVE = Path(".harness") / "training"
MACHINE_AUTHORED_DISCLOSURE = (
    "This change was machine-authored by Consilient under a human operator's "
    "direction. The operator remains responsible for the submission."
)
OUTCOME_CLASSES = frozenset(
    {
        "merged",
        "rejected",
        "revised_then_merged",
        "closed_without_decision",
        "non_response",
    }
)
_DECIDED_CLASSES = frozenset({"merged", "rejected", "revised_then_merged"})
_PROHIBITED_MARKERS = (
    "automated pull requests are prohibited",
    "no automated pull requests",
    "no automated prs",
    "automated submissions are prohibited",
    "ai-generated contributions are prohibited",
    "bots may not open pull requests",
    "do not submit automated",
)
AutomatedPolicy = Literal["allowed", "prohibited", "disclose_required"]
OutcomeClass = Literal[
    "merged",
    "rejected",
    "revised_then_merged",
    "closed_without_decision",
    "non_response",
]
AUTOMATED_POLICIES = frozenset({"allowed", "prohibited", "disclose_required"})


class UpstreamError(ValueError):
    """A contribution that must not be sent, or a rate that must not be β."""


@dataclass(frozen=True)
class HostPolicy:
    repository: str
    automated_pull_requests: AutomatedPolicy
    contributing_text: str

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise UpstreamError("repository must be a non-empty string")
        if self.automated_pull_requests not in AUTOMATED_POLICIES:
            raise UpstreamError(
                "automated_pull_requests must be allowed, prohibited or disclose_required"
            )


@dataclass(frozen=True)
class HostCIReport:
    green: bool
    summary: str


@dataclass(frozen=True)
class PreparedContribution:
    contribution_id: str
    repository: str
    title: str
    body: str
    diff: str
    policy: HostPolicy
    wanted_on_merits: bool
    verifier_accept: bool
    weakened_to_probe_verifier: bool
    host_ci: HostCIReport | None


@dataclass(frozen=True)
class SubmittedContribution:
    contribution_id: str
    repository: str
    locator: str
    verifier_accept: bool


@dataclass(frozen=True)
class UpstreamOutcome:
    contribution_id: str
    repository: str
    outcome_class: OutcomeClass
    maintainer_words: str
    review_comments: tuple[str, ...]


@dataclass(frozen=True)
class FalseAcceptAmongAccepted:
    quantity_name: str
    verdict: Literal["measured", "insufficient_data"]
    n_submitted: int
    n_decided: int
    n_rejected: int
    n_non_response: int
    n_closed_without_decision: int
    false_accept_among_accepted: float | None


def parse_host_policy(repository: str, contributing_text: str) -> HostPolicy:
    """Read the host project's contribution rules. Default is disclose, not silence."""
    lowered = contributing_text.casefold()
    automated: AutomatedPolicy = "disclose_required"
    if any(marker in lowered for marker in _PROHIBITED_MARKERS):
        automated = "prohibited"
    return HostPolicy(
        repository=repository,
        automated_pull_requests=automated,
        contributing_text=contributing_text,
    )


def prepare_contribution(
    *,
    repository: str,
    title: str,
    body: str,
    diff: str,
    policy: HostPolicy,
    wanted_on_merits: bool,
    verifier_accept: bool,
    weakened_to_probe_verifier: bool,
    host_ci: HostCIReport | None = None,
) -> PreparedContribution:
    """Assemble a contribution. Disclosure is added wherever a maintainer would want it."""
    if not title.strip() or not diff.strip():
        raise UpstreamError("a contribution needs a title and a diff")
    if policy.repository != repository:
        raise UpstreamError("policy repository does not match the contribution")
    text = body.rstrip()
    if MACHINE_AUTHORED_DISCLOSURE not in text:
        text = f"{text}\n\n{MACHINE_AUTHORED_DISCLOSURE}\n" if text else (
            MACHINE_AUTHORED_DISCLOSURE + "\n"
        )
    contribution_id = hashlib.sha256(
        f"{repository}\n{title}\n{diff}".encode()
    ).hexdigest()[:16]
    return PreparedContribution(
        contribution_id=contribution_id,
        repository=repository,
        title=title.strip(),
        body=text,
        diff=diff,
        policy=policy,
        wanted_on_merits=wanted_on_merits,
        verifier_accept=verifier_accept,
        weakened_to_probe_verifier=weakened_to_probe_verifier,
        host_ci=host_ci,
    )


def verify_host_ci(
    prepared: PreparedContribution,
    runner: Callable[[PreparedContribution], HostCIReport],
) -> PreparedContribution:
    """Attach the host project's CI result. The runner is injected; this tree does not shell out."""
    return replace(prepared, host_ci=runner(prepared))


def _refuse_unsubmittable(prepared: PreparedContribution) -> None:
    if prepared.policy.automated_pull_requests == "prohibited":
        raise UpstreamError(
            f"{prepared.repository} prohibits automated pull requests"
        )
    if not prepared.wanted_on_merits:
        raise UpstreamError(
            "refusing a change that is not wanted on its own merits"
        )
    if prepared.weakened_to_probe_verifier:
        raise UpstreamError("refusing to weaken a contribution to probe the verifier")
    if not prepared.verifier_accept:
        raise UpstreamError("this channel submits only work our verifier accepted")
    if prepared.host_ci is None or not prepared.host_ci.green:
        raise UpstreamError("host CI is not green")


def _write(dest: Path, root: Path, row: dict[str, object]) -> Path:
    try:
        dest = assert_unpublishable(dest, root=root)
    except HarvestError as exc:
        raise UpstreamError(str(exc)) from exc
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / OUTCOMES_FILE
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(
        existing + json.dumps(row, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def submit_contribution(
    prepared: PreparedContribution,
    *,
    sink: Callable[[PreparedContribution], dict[str, str]],
    dest: Path,
    root: Path,
) -> SubmittedContribution:
    """Hand a prepared, CI-green change to the injected sink and record the locator."""
    _refuse_unsubmittable(prepared)
    receipt = sink(prepared)
    locator = receipt["locator"]
    submitted = SubmittedContribution(
        contribution_id=prepared.contribution_id,
        repository=prepared.repository,
        locator=locator,
        verifier_accept=True,
    )
    _write(
        dest,
        root,
        {
            "v": 1,
            "kind": "upstream.submitted",
            "contribution_id": submitted.contribution_id,
            "repository": submitted.repository,
            "locator": submitted.locator,
            "verifier_accept": True,
            "estimand_kind": ESTIMAND_KIND,
            "auth_status": "unauthenticated",
            "quantity_name": QUANTITY_NAME,
        },
    )
    return submitted


def record_outcome(
    *,
    contribution_id: str,
    repository: str,
    outcome_class: OutcomeClass,
    maintainer_words: str,
    dest: Path,
    root: Path,
    review_comments: Sequence[str] = (),
    persist: bool = True,
) -> UpstreamOutcome:
    """Record one host-project outcome, including silence, with the maintainer's words verbatim."""
    if outcome_class not in OUTCOME_CLASSES:
        raise UpstreamError(f"unknown outcome class {outcome_class!r}")
    if not contribution_id.strip():
        raise UpstreamError("contribution_id must be a non-empty string")
    if outcome_class == "rejected" and not maintainer_words.strip():
        raise UpstreamError("rejected outcomes need the maintainer's words verbatim")
    comments = tuple(review_comments)
    outcome = UpstreamOutcome(
        contribution_id=contribution_id,
        repository=repository,
        outcome_class=outcome_class,
        maintainer_words=maintainer_words,
        review_comments=comments,
    )
    if persist:
        persist_outcome(outcome, dest=dest, root=root)
    return outcome


def persist_outcome(
    outcome: UpstreamOutcome, *, dest: Path, root: Path
) -> Path:
    """Append an outcome to gitignored instance storage (ADR-0057)."""
    return _write(
        dest,
        root,
        {
            "v": 1,
            "kind": "upstream.outcome",
            "contribution_id": outcome.contribution_id,
            "repository": outcome.repository,
            "outcome_class": outcome.outcome_class,
            "maintainer_words": outcome.maintainer_words,
            "review_comments": list(outcome.review_comments),
            "estimand_kind": ESTIMAND_KIND,
            "auth_status": "unauthenticated",
            "verifier_accept": True,
            "quantity_name": QUANTITY_NAME,
        },
    )


def as_meter_row(
    outcome: UpstreamOutcome,
    *,
    estimand_kind: str | None = None,
) -> dict[str, object]:
    """Shape an outcome as a meter row that cannot enter human-β or the gate."""
    kind = ESTIMAND_KIND if estimand_kind is None else estimand_kind
    if kind == HUMAN_VERDICT_BETA or "beta" in kind.casefold():
        raise UpstreamError(
            "upstream outcomes are not beta and cannot be recorded as human_verdict_beta"
        )
    if outcome.outcome_class in {"non_response", "closed_without_decision"}:
        human_verdict = "undecided"
    elif outcome.outcome_class == "rejected":
        human_verdict = "reject"
    else:
        human_verdict = "accept"
    row: dict[str, object] = {
        "estimand_kind": kind,
        "auth_status": "unauthenticated",
        "verifier_accept": True,
        "human_verdict": human_verdict,
        "task_family": "upstream_contribution",
    }
    if admits_human_beta_row(row) or admits_sizing_input(row):
        raise UpstreamError(
            "upstream outcomes cannot enter the human-beta projection or the gate"
        )
    return row


def compute_false_accept_among_accepted(
    outcomes: Iterable[UpstreamOutcome],
) -> FalseAcceptAmongAccepted:
    """P(maintainer rejects | our verifier accepted) among decided submissions.

    Non-response and closure without a decision are counted, then excluded from
    the rate: a PR nobody judged is not evidence of quality.
    """
    rows = tuple(outcomes)
    n_rejected = sum(1 for row in rows if row.outcome_class == "rejected")
    n_non_response = sum(1 for row in rows if row.outcome_class == "non_response")
    n_closed = sum(1 for row in rows if row.outcome_class == "closed_without_decision")
    n_decided = sum(1 for row in rows if row.outcome_class in _DECIDED_CLASSES)
    rate = (n_rejected / n_decided) if n_decided else None
    return FalseAcceptAmongAccepted(
        quantity_name=QUANTITY_NAME,
        verdict="measured" if n_decided else "insufficient_data",
        n_submitted=len(rows),
        n_decided=n_decided,
        n_rejected=n_rejected,
        n_non_response=n_non_response,
        n_closed_without_decision=n_closed,
        false_accept_among_accepted=rate,
    )


def render_false_accept_among_accepted(report: FalseAcceptAmongAccepted) -> str:
    """Render the conditional rate under its own name. Impossible to read as β."""
    rate = (
        "insufficient_data"
        if report.false_accept_among_accepted is None
        else f"{report.false_accept_among_accepted}"
    )
    return (
        f"{QUANTITY_NAME}={rate} "
        f"(n_rejected={report.n_rejected}, n_decided={report.n_decided}, "
        f"n_non_response={report.n_non_response}). "
        "NOT beta. Beta is P(our verifier accepts | the artefact is bad) and is "
        "unobservable through this channel: artefacts the verifier rejected are "
        "never submitted."
    )

"""β — the rate at which the automated verifier accepts an artefact the human rejected.

V0-06: routing consumes the composite-verifier β with its sample count and interval.
Per-check outcomes are diagnostics only, because their dependence is unknown (ADR-0012).

β is conditional on an oracle that is itself a test. The human verdict is error-prone, is
not independent of the automated checks, and may not be stationary (Q30). β measures the
pair, not the checks alone, and no caller may present it otherwise.

`lower_bound_on_joint_error` was a hard-coded `True` until 20 August 2026, with a test
asserting it was `True`. That test enforced the *claim*, not the property — the same
"assert the mechanism, not the property" failure this repository has now found in four
separate checks.

The bound only follows if the sample is **not conditioned on the verifier's own outcome**.
If artefacts reach a human only when the checks already accepted them, every rejected row
has `verifier_accept=True` and β is 1 by construction rather than by measurement. The
arithmetic in `compute` is correct; the exposure is entirely in which rows exist.

Nothing recorded or checked that property, and there is no collection protocol at all —
the meter has received zero rows. So the honest default is that **no bound is claimed**.
A caller who has a sampling protocol that does not condition on the verifier may declare
it, and only then does the bound hold. Found by a cross-family prior-art audit reading this
file against its own defect record.
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from typing import Literal, assert_never, cast

# Below this many human rejections there is no interval worth showing. ADR-0002 puts verifier
# calibration at 50-200 labels; 30 is the floor for reporting anything at all and is
# [asserted], not derived.
MIN_REJECTIONS = 30

HUMAN_VERDICT_BETA = "human_verdict_beta"
UPSTREAM_MAINTAINER_PROXY_BETA = "upstream_maintainer_proxy_beta"
# One-line switch after the principal accepts ADR-0106: assign HUMAN_VERDICT_BETA.
# Gate admission still requires removing this kind from PROXY_ESTIMAND_KINDS.
UPSTREAM_MAINTAINER_ESTIMAND_KIND = UPSTREAM_MAINTAINER_PROXY_BETA
PROXY_ESTIMAND_KINDS = frozenset(
    {
        "mutation_proxy_beta",
        "critic_proxy_beta",
        "repository_consequence_false_shipment_cohort_lower_bound",
        UPSTREAM_MAINTAINER_PROXY_BETA,
    }
)
AUTHENTICATED_AUTH_STATUS = "authenticated"
THIRD_PARTY_MAINTAINER_AUTH_STATUS = "third_party_maintainer"

# EXP-144: below this fraction of admitted artefacts rejected by the composite verifier,
# variation collapses and the protocol is declared failed.
MIN_COMPOSITE_REJECTION_FRACTION = 0.05

UpstreamCiOutcome = Literal["pass", "fail"]
HumanDecision = Literal["merge", "reject", "close_without_decision", "pending"]
RejectionKind = Literal["correctness", "fit"]

Verdict = Literal["measured", "insufficient_data"]

INSUFFICIENT: Verdict = "insufficient_data"
MEASURED: Verdict = "measured"


@dataclass(frozen=True)
class Beta:
    verdict: Verdict
    task_family: str | None
    verifier_version: str | None
    n_rejected: int
    n_false_accept: int
    point: float | None
    interval: tuple[float, float] | None
    window: tuple[str, str] | None
    # False unless the caller declares a sampling protocol that does not condition on the
    # verifier's outcome. Defaulting to True asserted a property of data that did not exist.
    lower_bound_on_joint_error: bool = False
    caveat: str = field(
        default="beta is conditional on a human verdict that is itself fallible, "
        "not independent of the checks, and possibly non-stationary (Q30)"
    )
    declared_principal_verdict_count: int = 0
    # Reported with every upstream-maintainer figure (EXP-144 self-check).
    composite_rejection_fraction: float | None = None

    def __post_init__(self) -> None:
        """A measured beta must carry its point and interval; insufficient_data must not.

        Found by `mypy --strict`, not by the 24 tests: render() unpacked self.interval
        unconditionally, so a payload with verdict=measured and interval=None crashed on
        the JSON round-trip with `cannot unpack non-iterable NoneType`. The tests were
        structurally blind to it because beta on the real trajectory is insufficient_data,
        so the measured render path was never exercised.

        Guarding render() would have left the bad state constructable and moved the crash
        elsewhere. Principle 4: the fix is a constraint, so the state cannot exist.
        """
        if self.verdict == MEASURED and (self.point is None or self.interval is None):
            raise ValueError(
                "a measured beta must carry both a point estimate and an interval; got "
                f"point={self.point!r} interval={self.interval!r}"
            )
        if self.verdict == INSUFFICIENT and (
            self.point is not None or self.interval is not None
        ):
            raise ValueError(
                "insufficient_data must not carry a point estimate or an interval"
            )

        # The checks above were the whole guard until 20 Aug 2026, and they only asked
        # whether the fields were present. A `measured` beta could therefore be constructed
        # with zero rejections behind it, a point outside [0, 1], or an inverted interval,
        # and it would render without complaint. `compute` enforced the sample floor, but
        # the floor is not an invariant if the constructor beneath it does not hold.
        # Found by Cursor auditing code Claude wrote.
        if not 0 <= self.n_false_accept <= self.n_rejected:
            raise ValueError(
                f"n_false_accept must lie in [0, n_rejected]; got "
                f"{self.n_false_accept} of {self.n_rejected}"
            )
        if self.point is not None and not 0.0 <= self.point <= 1.0:
            raise ValueError(
                f"beta is a rate and must lie in [0, 1]; got {self.point!r}"
            )
        if self.interval is not None:
            low, high = self.interval
            if not 0.0 <= low <= high <= 1.0:
                raise ValueError(
                    f"interval must satisfy 0 <= low <= high <= 1; got {self.interval!r}"
                )
            if self.point is not None and not low <= self.point <= high:
                raise ValueError(
                    f"point {self.point!r} lies outside its own interval {self.interval!r}"
                )
        if self.verdict == MEASURED and self.n_rejected < MIN_REJECTIONS:
            raise ValueError(
                f"a measured beta needs at least {MIN_REJECTIONS} rejections behind it; "
                f"got {self.n_rejected}. Report insufficient_data instead — an underpowered "
                "number presented as measured is the failure this project exists to catch"
            )

    def as_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["interval"] = list(self.interval) if self.interval else None
        d["window"] = list(self.window) if self.window else None
        return d

    def render(self) -> str:
        """Human output is a rendering of this object, never a second semantics (V0-14)."""
        scope = (
            " / ".join(x for x in (self.task_family, self.verifier_version) if x)
            or "all"
        )
        match self.verdict:
            case "insufficient_data":
                suffix = ""
                if self.composite_rejection_fraction is not None:
                    suffix = (
                        f"; composite rejection fraction "
                        f"{self.composite_rejection_fraction:.3f}"
                    )
                return (
                    f"beta [{scope}]: insufficient data "
                    f"({self.n_rejected} human rejections, need {MIN_REJECTIONS})"
                    f"{suffix}"
                )
            case "measured":
                # __post_init__ guarantees both are present. Restating it here is what
                # lets the checker prove it rather than take our word for it.
                assert self.point is not None and self.interval is not None
                low, high = self.interval
                # The bound clause is conditional now. It was unconditional until 20 Aug
                # 2026, so the rendered output asserted a property of the sample that
                # nothing had established — the strongest possible way to state a claim,
                # in the one place a reader actually looks.
                bound = (
                    " — lower bound on a joint human-plus-checks error"
                    if self.lower_bound_on_joint_error
                    else " — NOT a bound: sampling not declared unconditioned on the verifier"
                )
                fraction = ""
                if self.composite_rejection_fraction is not None:
                    fraction = (
                        f"; composite rejection fraction "
                        f"{self.composite_rejection_fraction:.3f}"
                    )
                return (
                    f"beta [{scope}]: {self.point:.3f} [{low:.3f}, {high:.3f}] "
                    f"from {self.n_false_accept}/{self.n_rejected} rejections{bound}"
                    f"{fraction}"
                )
            case _:
                # A verdict added without handling it here fails the type check, by name.
                assert_never(self.verdict)


def wilson(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Behaves at 0 and at n, unlike the normal approximation."""
    if trials == 0:
        raise ValueError("no trials")
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def _parse_iso_ts(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"timestamp must be a string; got {value!r}")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp must include a UTC offset; got {value!r}")
    return parsed


def admits_upstream_maintainer_proxy_row(row: dict[str, object]) -> bool:
    """Upstream maintainer rows are recorded under a proxy estimand until ADR-0106 applies."""
    return row.get("estimand_kind") == UPSTREAM_MAINTAINER_ESTIMAND_KIND


def upstream_human_verdict_for_beta(row: dict[str, object]) -> Literal["accept", "reject"] | None:
    """Map maintainer outcome to beta's human_verdict, excluding CI-only and fit rejections."""
    if row.get("upstream_ci_outcome") == "fail":
        return None
    decision = row.get("human_decision")
    if decision == "merge":
        return "accept"
    if decision != "reject":
        return None
    if row.get("rejection_kind") != "correctness":
        return None
    return "reject"


def counts_toward_upstream_beta_numerator(row: dict[str, object]) -> bool:
    """A maintainer correctness rejection with verifier_accept=True enters the numerator."""
    return (
        refuse_upstream_row(row) is None
        and upstream_human_verdict_for_beta(row) == "reject"
        and row.get("verifier_accept") is True
    )


def verifier_verdict_did_not_gate_submission(row: dict[str, object]) -> bool:
    """Submission must be recorded before the composite verifier's verdict."""
    submission = row.get("submission_ts")
    verdict_ts = row.get("verifier_verdict_ts")
    if not isinstance(submission, str) or not isinstance(verdict_ts, str):
        return False
    try:
        return _parse_iso_ts(submission) < _parse_iso_ts(verdict_ts)
    except (TypeError, ValueError):
        return False


def refuse_upstream_row(row: dict[str, object]) -> str | None:
    """Return a refusal reason, or None when the row may enter measurement."""
    if row.get("estimand_kind") != UPSTREAM_MAINTAINER_ESTIMAND_KIND:
        return "wrong_estimand_kind"
    if row.get("admission_bar_passed") is not True:
        return "admission_bar_not_passed"
    ci_outcome = row.get("upstream_ci_outcome")
    if ci_outcome not in ("pass", "fail"):
        return "invalid_upstream_ci_outcome"
    if ci_outcome != "pass":
        return "upstream_ci_not_passed"
    if not isinstance(row.get("verifier_accept"), bool):
        return "invalid_verifier_verdict"
    decision = row.get("human_decision")
    if decision not in ("merge", "reject", "close_without_decision", "pending"):
        return "invalid_human_decision"
    if decision == "reject":
        if row.get("rejection_kind") not in ("correctness", "fit"):
            return "invalid_rejection_kind"
        words = row.get("maintainer_words")
        if not isinstance(words, str) or not words.strip():
            return "maintainer_words_missing"
        authored_by = row.get("authored_by")
        classified_by = row.get("classified_by")
        if not isinstance(authored_by, str) or not authored_by.strip():
            return "classifier_not_recorded"
        if not isinstance(classified_by, str) or not classified_by.strip():
            return "classifier_not_recorded"
        if authored_by == classified_by:
            return "author_classified_own_rejection"
    if not verifier_verdict_did_not_gate_submission(row):
        return "verifier_verdict_did_not_follow_submission"
    return None


def both_upstream_cells_representable(rows: Iterable[dict[str, object]]) -> bool:
    """Both table cells must be expressible or conditioning returns in the schema."""
    accepted_rejected = False
    rejected_merged = False
    for row in rows:
        if refuse_upstream_row(row) is not None:
            continue
        if row.get("verifier_accept") is True and upstream_human_verdict_for_beta(row) == "reject":
            accepted_rejected = True
        if row.get("verifier_accept") is False and row.get("human_decision") == "merge":
            rejected_merged = True
    return accepted_rejected and rejected_merged


def composite_verifier_rejection_fraction(
    rows: Iterable[dict[str, object]],
    task_family: str | None = None,
    verifier_version: str | None = None,
) -> float | None:
    """Fraction of admission-bar-passed artefacts the composite verifier rejects."""
    admitted = [
        row
        for row in rows
        if (task_family is None or row.get("task_family") == task_family)
        and (verifier_version is None or row.get("verifier_version") == verifier_version)
        and refuse_upstream_row(row) is None
    ]
    if not admitted:
        return None
    rejected = sum(1 for row in admitted if row.get("verifier_accept") is False)
    return rejected / len(admitted)


def upstream_rows_for_compute(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Project admitted upstream rows into the shape `compute` expects."""
    projected: list[dict[str, object]] = []
    for row in rows:
        if refuse_upstream_row(row) is not None:
            continue
        human_verdict = upstream_human_verdict_for_beta(row)
        if human_verdict is None:
            continue
        projected.append(
            {
                "ts": row["submission_ts"],
                "task_family": row.get("task_family"),
                "verifier_version": row.get("verifier_version"),
                "verifier_accept": row["verifier_accept"],
                "human_verdict": human_verdict,
                "estimand_kind": row.get("estimand_kind"),
                "auth_status": row.get("auth_status"),
            }
        )
    return projected


def compute_upstream_maintainer_beta(
    rows: Iterable[dict[str, object]],
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
    min_composite_rejection_fraction: float = MIN_COMPOSITE_REJECTION_FRACTION,
) -> Beta:
    """β among upstream contributions that passed the declared admission bar (EXP-144)."""
    if not MIN_COMPOSITE_REJECTION_FRACTION <= min_composite_rejection_fraction <= 1:
        raise ValueError(
            "min_composite_rejection_fraction may only raise the floor from "
            f"{MIN_COMPOSITE_REJECTION_FRACTION} and cannot exceed 1"
        )
    material = list(rows)
    projected = upstream_rows_for_compute(material)
    result = compute(
        projected,
        task_family,
        verifier_version,
        min_rejections,
        sampling_unconditioned=True,
    )
    fraction = composite_verifier_rejection_fraction(
        material,
        task_family,
        verifier_version,
    )
    if fraction is None or fraction < min_composite_rejection_fraction:
        caveat = (
            "beta is conditional on a human verdict that is itself fallible, "
            "not independent of the checks, and possibly non-stationary (Q30); "
            "composite rejection fraction below the EXP-144 floor — protocol failed"
        )
        return replace(
            result,
            verdict=INSUFFICIENT,
            point=None,
            interval=None,
            lower_bound_on_joint_error=False,
            caveat=caveat,
            composite_rejection_fraction=fraction,
        )

    return replace(
        result,
        composite_rejection_fraction=fraction,
        caveat=(
            f"{result.caveat}; upstream maintainer estimand conditional on admission bar "
            f"(EXP-144); composite rejection fraction {fraction:.3f}"
        ),
    )


def admits_human_beta_row(row: dict[str, object]) -> bool:
    """Only authenticated human-verdict beta rows may enter the human-beta projection."""
    estimand = row.get("estimand_kind")
    if estimand in PROXY_ESTIMAND_KINDS:
        return False
    return (
        estimand == HUMAN_VERDICT_BETA
        and row.get("auth_status") == AUTHENTICATED_AUTH_STATUS
    )


def admits_sizing_input(row: dict[str, object]) -> bool:
    """Sizing consumers share the same admission rule as the human-beta projection."""
    return admits_human_beta_row(row)


def compute(
    rows: Iterable[dict[str, object]],
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
    sampling_unconditioned: bool = False,
) -> Beta:
    """β over outcome rows.

    A row needs `verifier_accept` and a `human_verdict` of 'accept' or 'reject'. Rows with
    no human verdict are excluded from both numerator and denominator: an unlabelled
    artefact is not evidence of agreement. No proxy label is accepted here — the caller
    must have resolved a real verdict before the row reaches this function.

    `min_rejections` may only be raised. A knob that can lower an evidence floor is a
    bypass path around it, which is the shape of failure principle 3 names.
    """
    if min_rejections < MIN_REJECTIONS:
        raise ValueError(
            f"min_rejections may only raise the floor, never lower it; "
            f"{min_rejections} is below MIN_REJECTIONS={MIN_REJECTIONS}"
        )
    selected = [
        r
        for r in rows
        if (task_family is None or r.get("task_family") == task_family)
        and (verifier_version is None or r.get("verifier_version") == verifier_version)
    ]
    rejected = [r for r in selected if r.get("human_verdict") == "reject"]
    n = len(rejected)
    false_accepts = sum(1 for r in rejected if r["verifier_accept"])

    stamps = sorted(cast(str, r["ts"]) for r in selected if r.get("ts"))
    window = (stamps[0], stamps[-1]) if stamps else None

    if n < min_rejections:
        return Beta(
            INSUFFICIENT,
            task_family,
            verifier_version,
            n,
            false_accepts,
            None,
            None,
            window,
            sampling_unconditioned,
        )

    return Beta(
        MEASURED,
        task_family,
        verifier_version,
        n,
        false_accepts,
        false_accepts / n,
        wilson(false_accepts, n),
        window,
        sampling_unconditioned,
    )


def from_connection(
    conn: sqlite3.Connection,
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
    sampling_unconditioned: bool | None = None,
) -> Beta:
    from . import projection as projection_mod

    derived = projection_mod.sampling_unconditioned(conn)
    if projection_mod.review_queue_row(conn) is not None:
        sampling = derived
    elif sampling_unconditioned is None:
        sampling = derived
    else:
        sampling = sampling_unconditioned
    rows = [
        {
            "ts": ts,
            "task_family": fam,
            "verifier_version": ver,
            "verifier_accept": bool(acc),
            "human_verdict": verdict,
            "estimand_kind": estimand,
            "auth_status": auth,
        }
        for ts, fam, ver, acc, verdict, estimand, auth in conn.execute(
            "SELECT ts, task_family, verifier_version, verifier_accept, human_verdict,"
            " estimand_kind, auth_status FROM outcomes ORDER BY position"
        )
    ]
    declared_principal_verdict_count = sum(
        1
        for row in rows
        if row["auth_status"] == "declared_principal"
        and (task_family is None or row["task_family"] == task_family)
        and (verifier_version is None or row["verifier_version"] == verifier_version)
    )
    result = compute(
        [row for row in rows if admits_human_beta_row(row)],
        task_family,
        verifier_version,
        min_rejections,
        sampling,
    )
    if not declared_principal_verdict_count:
        return result
    return replace(
        result,
        caveat=(
            f"{result.caveat}; declared-principal verdicts recorded and excluded from "
            f"beta: {declared_principal_verdict_count} (not machine-authenticated)"
        ),
        declared_principal_verdict_count=declared_principal_verdict_count,
    )

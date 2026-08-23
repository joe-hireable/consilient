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
from typing import Literal, assert_never, cast

# Below this many human rejections there is no interval worth showing. ADR-0002 puts verifier
# calibration at 50-200 labels; 30 is the floor for reporting anything at all and is
# [asserted], not derived.
MIN_REJECTIONS = 30

HUMAN_VERDICT_BETA = "human_verdict_beta"
PROXY_ESTIMAND_KINDS = frozenset(
    {
        "mutation_proxy_beta",
        "critic_proxy_beta",
        "repository_consequence_false_shipment_cohort_lower_bound",
    }
)
AUTHENTICATED_AUTH_STATUS = "authenticated"

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
                return (
                    f"beta [{scope}]: insufficient data "
                    f"({self.n_rejected} human rejections, need {MIN_REJECTIONS})"
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
                return (
                    f"beta [{scope}]: {self.point:.3f} [{low:.3f}, {high:.3f}] "
                    f"from {self.n_false_accept}/{self.n_rejected} rejections{bound}"
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

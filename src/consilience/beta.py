"""β — the rate at which the automated verifier accepts an artefact the human rejected.

V0-06: routing consumes the composite-verifier β with its sample count and interval.
Per-check outcomes are diagnostics only, because their dependence is unknown (ADR-0012).

β is conditional on an oracle that is itself a test. The human verdict is error-prone, is
not independent of the automated checks, and may not be stationary (Q30). Every result
therefore carries `lower_bound_on_joint_error: True` — β measures the pair, not the checks
alone, and no caller may present it otherwise.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Iterable

# Below this many human rejections there is no interval worth showing. ADR-0002 puts verifier
# calibration at 50-200 labels; 30 is the floor for reporting anything at all and is
# [asserted], not derived.
MIN_REJECTIONS = 30

INSUFFICIENT = "insufficient_data"
MEASURED = "measured"


@dataclass(frozen=True)
class Beta:
    verdict: str
    task_family: str | None
    verifier_version: str | None
    n_rejected: int
    n_false_accept: int
    point: float | None
    interval: tuple[float, float] | None
    window: tuple[str, str] | None
    lower_bound_on_joint_error: bool = True
    caveat: str = field(
        default="beta is conditional on a human verdict that is itself fallible, "
        "not independent of the checks, and possibly non-stationary (Q30)"
    )

    def as_dict(self) -> dict:
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
        if self.verdict == INSUFFICIENT:
            return (
                f"beta [{scope}]: insufficient data "
                f"({self.n_rejected} human rejections, need {MIN_REJECTIONS})"
            )
        low, high = self.interval
        return (
            f"beta [{scope}]: {self.point:.3f} [{low:.3f}, {high:.3f}] "
            f"from {self.n_false_accept}/{self.n_rejected} rejections "
            f"— lower bound on a joint human-plus-checks error"
        )


def wilson(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Behaves at 0 and at n, unlike the normal approximation."""
    if trials == 0:
        raise ValueError("no trials")
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def compute(
    rows: Iterable[dict],
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
) -> Beta:
    """β over outcome rows.

    A row needs `verifier_accept` and a `human_verdict` of 'accept' or 'reject'. Rows with
    no human verdict are excluded from both numerator and denominator: an unlabelled
    artefact is not evidence of agreement. No proxy label is accepted here — the caller
    must have resolved a real verdict before the row reaches this function.
    """
    selected = [
        r
        for r in rows
        if (task_family is None or r.get("task_family") == task_family)
        and (verifier_version is None or r.get("verifier_version") == verifier_version)
    ]
    rejected = [r for r in selected if r.get("human_verdict") == "reject"]
    n = len(rejected)
    false_accepts = sum(1 for r in rejected if r["verifier_accept"])

    stamps = sorted(r["ts"] for r in selected if r.get("ts"))
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
    )


def from_connection(
    conn,
    task_family: str | None = None,
    verifier_version: str | None = None,
    min_rejections: int = MIN_REJECTIONS,
) -> Beta:
    rows = [
        {
            "ts": ts,
            "task_family": fam,
            "verifier_version": ver,
            "verifier_accept": bool(acc),
            "human_verdict": verdict,
        }
        for ts, fam, ver, acc, verdict in conn.execute(
            "SELECT ts, task_family, verifier_version, verifier_accept, human_verdict"
            " FROM outcomes ORDER BY position"
        )
    ]
    return compute(rows, task_family, verifier_version, min_rejections)

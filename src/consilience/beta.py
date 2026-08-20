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
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Literal, assert_never

# Below this many human rejections there is no interval worth showing. ADR-0002 puts verifier
# calibration at 50-200 labels; 30 is the floor for reporting anything at all and is
# [asserted], not derived.
MIN_REJECTIONS = 30

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
    lower_bound_on_joint_error: bool = True
    caveat: str = field(
        default="beta is conditional on a human verdict that is itself fallible, "
        "not independent of the checks, and possibly non-stationary (Q30)"
    )

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
                return (
                    f"beta [{scope}]: {self.point:.3f} [{low:.3f}, {high:.3f}] "
                    f"from {self.n_false_accept}/{self.n_rejected} rejections "
                    f"— lower bound on a joint human-plus-checks error"
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

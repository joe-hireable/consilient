"""β-conditioned candidate ceilings — the mechanism, deliberately unwired.

README.md states the project's contribution: nothing else "conditions its own routing,
its parallelism or its acceptance threshold on a measured β". This module is that
conditioning mechanism. **Nothing in the run path calls it.** It is not imported by
`scripts/dispatch.py`, it does not touch `routing_orchestration_enabled`, and it changes
no gate condition: Stage 3 authorises *building* orchestration, and *depending* on it is
Gate B, which is not passed.

The identity is ADR-0051's, registered in `docs/20-design/work-modes.md`: an attempt
that resamples until the verifier accepts exposes the verifier n times, so
P(bad ships) = 1 − (1−β)ⁿ, inverted for a declared exposure ceiling ε as
n_max = ⌊ln(1−ε) / ln(1−β)⌋. At EXP-47's measured β = 0.3132 [0.2926, 0.3346] that is
n_max = 1 for any ε ≤ 0.40 across the whole interval [algebra].

Two design points are load-bearing:

- **An absent β refuses.** `consil beta` on the real trajectory reports insufficient
  data (0 human rejections, need 30). A policy that routed on a default β would be
  routing on a fabricated measurement — the worst failure available here. So an
  unmeasured β is a refusal, not an assumption.
- **The ceiling is computed at the top of the interval.** n_max is monotone decreasing
  in β (ADR-0051), so the interval's upper bound is the conservative routing input;
  routing on the point estimate would understate exposure half the time.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from . import beta, projection

# `from .beta import …` would name the module in an import the product capability
# allowlist (test_budget.py) does not grant; the package-relative form is the one
# it permits.


@dataclass(frozen=True)
class Ceiling:
    """How many candidates may be attempted against one verifier contract.

    `n_max` is None when the interval's upper bound is exactly 0: P(bad ships) is then
    0 for every n, and no finite ceiling follows from the identity. That is a statement
    about the arithmetic, not a licence — a measured β of exactly 0.0 should be read
    with the sample size it came from.
    """

    n_max: int | None
    beta_used: float
    epsilon: float


@dataclass(frozen=True)
class RoutingRefusal:
    """Routing declined to produce a ceiling. Refusing is the success path here."""

    reason: str


def candidates_ceiling(estimate: beta.Beta, epsilon: float) -> Ceiling | RoutingRefusal:
    """Invert P(bad ships) = 1 − (1−β)ⁿ for an exposure ceiling ε.

    A measured β yields the largest n with P(bad ships) ≤ ε, computed at the interval's
    upper bound. Anything else — insufficient data, an unmeasurable oracle — is a
    refusal, because the alternative is routing on a number nobody measured.
    """
    if not 0.0 < epsilon < 1.0:
        raise ValueError(
            f"epsilon is an exposure ceiling and must lie in (0, 1); got {epsilon!r}"
        )
    if estimate.verdict != beta.MEASURED:
        return RoutingRefusal(
            f"beta is not measured ({estimate.n_rejected} human rejections, need "
            f"{beta.MIN_REJECTIONS}); routing refuses to assume one. A default beta "
            "would be a fabricated measurement."
        )
    # Beta.__post_init__ guarantees a measured beta carries its interval.
    assert estimate.interval is not None
    upper = estimate.interval[1]
    if upper <= 0.0:
        return Ceiling(n_max=None, beta_used=upper, epsilon=epsilon)
    if upper >= 1.0:
        # Every attempt is accepted-and-bad; even one candidate busts any ε < 1.
        return Ceiling(n_max=0, beta_used=upper, epsilon=epsilon)
    n_max = math.floor(math.log(1.0 - epsilon) / math.log(1.0 - upper))
    return Ceiling(n_max=max(n_max, 0), beta_used=upper, epsilon=epsilon)


def ceiling_for_trajectory(
    log: Path, db: Path, epsilon: float
) -> Ceiling | RoutingRefusal:
    """The ceiling the real trajectory currently supports — today, a refusal.

    This is the bridge a wired router would call. On the trajectory as it stands the
    meter holds zero human rejections, so the honest answer is the refusal, and a test
    pins exactly that so the mechanism cannot silently start routing.
    """
    conn = projection.build(log, db)
    try:
        estimate = beta.from_connection(conn)
    finally:
        conn.close()
    return candidates_ceiling(estimate, epsilon)

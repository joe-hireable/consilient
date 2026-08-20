"""
EXP-20 companion: how cheap can a capability probe be and still estimate Delta?

Run: python probe_delta_ci.py        (needs numpy)

THE ESTIMATOR (and why it is pretty)
------------------------------------
Run BOTH models on the same n probe tasks (paired design). Under the Rasch/1PL
model, condition on the DISCORDANT pairs (exactly one model succeeded):

    P(frontier is the winner | discordant) = e^{k*Delta} / (1 + e^{k*Delta})

Task difficulty d cancels from this conditional likelihood by the same algebra
that makes beta* distribution-free. So:

    Delta_hat = (1/k) * logit( m_f / (m_f + m_c) )

with m_f = frontier-only successes, m_c = cheap-only successes. No difficulty
estimates, no calibrated task set, no IRT fitting — count two numbers.

CAVEATS INHERITED FROM THE CLOSED FORM: everything that breaks beta*
(robustness_beta_star.py) breaks this identically — unequal slopes, non-logistic
links, guessing floors make Delta_hat distribution-dependent. The probe is
therefore honest exactly where the routing rule is honest, which is the point of
EXP-20's consilience check: probe-derived beta*(Delta_hat) vs directly measured
beta must agree, or one of the two (likely the model) is wrong.

BONUS: the same 2x2 outcome table estimates the outcome correlation phi_hat —
the quantity V4 showed collapses beta* and which independent benchmark scores
can never give you. One probe, both parameters.
"""

import numpy as np

rng = np.random.default_rng(11)
sig = lambda x: 1 / (1 + np.exp(-x))
K, S_C, S_F, TRUE_DELTA = 8.0, 0.45, 0.72, 0.27
ALPHA = 0.03


def probe(n, rho=0.0, reps=4000):
    """Monte Carlo: paired probe of size n; Gaussian-copula outcome correlation rho."""
    d = rng.beta(2, 2, (reps, n))
    pc, pf = sig(K * (S_C - d)), sig(K * (S_F - d))
    z = rng.standard_normal((reps, n))
    zc = rho * z + np.sqrt(1 - rho**2) * rng.standard_normal((reps, n))
    zf = rho * z + np.sqrt(1 - rho**2) * rng.standard_normal((reps, n))
    from scipy.stats import norm

    ok_c = norm.cdf(zc) < pc
    ok_f = norm.cdf(zf) < pf
    m_f = (ok_f & ~ok_c).sum(1).astype(float)
    m_c = (ok_c & ~ok_f).sum(1).astype(float)
    disc = m_f + m_c
    valid = disc >= 3
    # Haldane-Anscombe correction for zero cells
    dh = (np.log((m_f + 0.5) / (m_c + 0.5)) / K)[valid]
    phi = []
    for r in range(min(reps, 2000)):
        a = (ok_f[r] & ok_c[r]).mean()
        b = (ok_f[r] & ~ok_c[r]).mean()
        c = (~ok_f[r] & ok_c[r]).mean()
        e = (~ok_f[r] & ~ok_c[r]).mean()
        den = np.sqrt((a + b) * (c + e) * (a + c) * (b + e))
        if den > 0:
            phi.append((a * e - b * c) / den)
    return dh, np.mean(disc), np.array(phi)


if __name__ == "__main__":
    print(
        f"true Delta {TRUE_DELTA}, closed-form beta* {(1 - ALPHA) * np.exp(-K * TRUE_DELTA):.4f}\n"
    )
    print(
        f"{'n':>5} {'rho':>5} {'E[discordant]':>14} {'Delta_hat mean':>15} "
        f"{'SE':>7} {'beta* 68% band':>22} {'SE(phi_hat)':>12}"
    )
    for rho in [0.0, 0.6]:
        for n in [20, 50, 100, 200]:
            dh, disc, phi = probe(n, rho)
            se = dh.std()
            lo = (1 - ALPHA) * np.exp(-K * (dh.mean() + se))
            hi = (1 - ALPHA) * np.exp(-K * (dh.mean() - se))
            print(
                f"{n:5d} {rho:5.1f} {disc:14.1f} {dh.mean():15.3f} "
                f"{se:7.3f} [{lo:9.4f}, {hi:9.4f}] {phi.std():12.3f}"
            )
    print("""
-> the information is in the DISCORDANT pairs; correlation makes them rarer,
   so a correlated pair of models needs a larger probe for the same CI.
-> n=20 is a coarse screen (beta* known to ~2x); n=100 gives a usable band;
   n=200 approaches decision grade. Drawing probe tasks adaptively near the
   models' ability band (CAT-style, per IRT-Router precedent) and from the
   user's own trajectory log both concentrate discordant pairs and shrink n.
-> phi_hat from the same table gives the correlation input V4 requires, at
   ~0.1 precision by n=100 — coarse, but the only local estimate available.""")

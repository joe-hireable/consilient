"""
How does beta* = (1-alpha)*exp(-k*gap) fail when the competence model is wrong?

Run: python robustness_beta_star.py          (needs numpy; scipy for the copula)

CONTEXT
-------
ADR-0002's closed form is exact *given* a logistic (Rasch/1PL) competence model:
p_m = sigmoid(k*(s_m - d)) with the SAME slope k for both models. Then the
log-odds gap is constant in d, the pointwise threshold

    beta*(d) = (1-alpha) * odds_c(d) / odds_f(d)

does not depend on d, and the difficulty distribution drops out. That is the
entire mechanism of the "distribution-free" claim. This file breaks each
assumption in turn and measures how far the aggregate beta* moves.

Aggregate beta* needs no root-finding: the pointwise advantage
    Delta(d) = (1-alpha)*(p_c - p_cf) - beta*(p_f - p_cf)
is linear in beta (p_cf = P(both succeed); = p_c*p_f under independence), so

    beta*_agg = (1-alpha) * E[p_c - p_cf] / E[p_f - p_cf]

computed by quadrature over each difficulty distribution. No Monte Carlo noise.

VIOLATIONS TESTED
-----------------
V1  2PL: unequal slopes k_c != k_f (models degrade with difficulty at
    different rates). The log-odds gap becomes linear in d; d no longer cancels.
V2  Link function: probit and cloglog (Gompertz) instead of logistic,
    slope-matched at p=0.5.
V3  4PL: cheap model has a guessing floor g (pattern-matches easy fixes);
    frontier has a lapse ceiling lambda (slips on anything).
V4  Correlated successes given d (Gaussian copula, rho > 0). The Rasch model
    makes the two models' successes conditionally independent given a scalar d.
    Real models share training data and failure modes: tasks hard for one are
    hard for the other BEYOND what scalar difficulty captures. Note this is the
    repo's own philosophy applied to its own simulation: two correlated
    inductions are not two classes of facts.
V5  Difficulty-dependent beta(d). The decision rule compares a MEASURED
    aggregate beta-hat (weighted by where bad artifacts occur) to the pointwise
    beta*. Those weightings differ by a factor p_f(d), so if beta varies with d
    the comparison can mislead — in the dangerous direction when beta is HIGH on
    EASY tasks (plausible: trivial changes in undertested corners pass checks;
    core-logic changes hit the covered paths).
"""

import numpy as np

ALPHA, K, S_C, S_F = 0.03, 8.0, 0.45, 0.72
GAP = S_F - S_C
CLOSED = (1 - ALPHA) * np.exp(-K * GAP)  # 0.1118

sig = lambda x: 1 / (1 + np.exp(-x))

# quadrature grid over difficulty
D = np.linspace(1e-6, 1 - 1e-6, 4001)


def beta_pdf(a, b):
    from math import lgamma

    ln = (
        (a - 1) * np.log(D)
        + (b - 1) * np.log(1 - D)
        - (lgamma(a) + lgamma(b) - lgamma(a + b))
    )
    return np.exp(ln)


DISTS = {
    "unimodal Beta(2,2)  ": beta_pdf(2, 2),
    "bimodal 90% easy    ": 0.90 * beta_pdf(2, 12) + 0.10 * beta_pdf(12, 2),
    "bimodal 70% easy    ": 0.70 * beta_pdf(2, 12) + 0.30 * beta_pdf(12, 2),
    "bimodal 50% easy    ": 0.50 * beta_pdf(2, 12) + 0.50 * beta_pdf(12, 2),
    "bimodal 30% easy    ": 0.30 * beta_pdf(2, 12) + 0.70 * beta_pdf(12, 2),
}


def bstar_agg(p_c, p_f, f, p_cf=None):
    if p_cf is None:
        p_cf = p_c * p_f
    num = np.trapezoid((p_c - p_cf) * f, D)
    den = np.trapezoid((p_f - p_cf) * f, D)
    return (1 - ALPHA) * num / den


def quality_gain_at(beta, p_c, p_f, f, p_cf=None):
    """cascade quality minus frontier quality, in points, at a given beta."""
    if p_cf is None:
        p_cf = p_c * p_f
    delta = (1 - ALPHA) * (p_c - p_cf) - beta * (p_f - p_cf)
    return np.trapezoid(delta * f, D)


# ---------------------------------------------------------------- V1  2PL
def rasch(k_c=K, k_f=K):
    return sig(k_c * (S_C - D)), sig(k_f * (S_F - D))


# ---------------------------------------------------------------- V2  links
from math import erf, log

Phi = np.vectorize(lambda x: 0.5 * (1 + erf(x / np.sqrt(2))))
# slope-matched at p=0.5: logistic slope k/4  ==  probit slope k_p/sqrt(2*pi)
K_PROBIT = K * np.sqrt(2 * np.pi) / 4
# cloglog p = 1 - exp(-ln2 * exp(k_g*x)) has slope ln2/2*k_g at x=0 -> match k/4
K_GOMP = K / (2 * log(2))
cloglog = lambda x: 1 - np.exp(-log(2) * np.exp(K_GOMP * x))

LINKS = {
    "logistic (baseline)": lambda s: sig(K * (s - D)),
    "probit             ": lambda s: Phi(K_PROBIT * (s - D)),
    "cloglog/Gompertz   ": lambda s: cloglog(s - D),
}


# ---------------------------------------------------------------- V3  4PL
def four_pl(g=0.10, lam=0.02):
    p_c = g + (1 - g) * sig(K * (S_C - D))
    p_f = (1 - lam) * sig(K * (S_F - D))
    return p_c, p_f


# ---------------------------------------------------------------- V4  copula
def p_both(p_c, p_f, rho):
    """P(both succeed) under a Gaussian copula with correlation rho."""
    if rho == 0:
        return p_c * p_f
    from scipy.stats import multivariate_normal, norm

    mvn = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])
    a, b = (
        norm.ppf(np.clip(p_c, 1e-12, 1 - 1e-12)),
        norm.ppf(np.clip(p_f, 1e-12, 1 - 1e-12)),
    )
    return mvn.cdf(np.column_stack([a, b]))


if __name__ == "__main__":
    hdr = "".join(f"{n.strip()[:18]:>20}" for n in DISTS)

    print(f"closed form beta* at gap {GAP:.2f}: {CLOSED:.4f}\n")

    print("V1 — unequal slopes (2PL). aggregate beta* by distribution")
    print(f"{'(k_c, k_f)':22s}{hdr}   spread")
    for kc, kf in [(8, 8), (6, 10), (10, 6), (4, 12), (12, 4)]:
        p_c, p_f = rasch(kc, kf)
        row = [bstar_agg(p_c, p_f, f) for f in DISTS.values()]
        print(
            f"  ({kc:2d},{kf:2d})              "
            + "".join(f"{b:20.3f}" for b in row)
            + f"   {max(row) - min(row):7.3f}"
        )
    print(
        "  -> equal slopes: spread ~0 (the ADR-0002 result reproduces)."
        "\n  -> unequal slopes: beta* moves ACROSS DISTRIBUTIONS."
        " Distribution-freeness is a knife-edge property of parallel"
        " log-odds curves, not a general fact.\n"
    )

    print("V2 — link function (slopes matched at p=0.5)")
    print(f"{'link':22s}{hdr}   spread")
    for name, fn in LINKS.items():
        p_c, p_f = fn(S_C), fn(S_F)
        row = [bstar_agg(p_c, p_f, f) for f in DISTS.values()]
        print(
            f"  {name:20s}"
            + "".join(f"{b:20.3f}" for b in row)
            + f"   {max(row) - min(row):7.3f}"
        )
    print(
        "  -> the LEVEL of beta* depends on the link even when the spread"
        " stays modest. The closed form's VALUE is link-specific.\n"
    )

    print("V3 — 4PL: cheap guessing floor g, frontier lapse lambda")
    print(f"{'(g, lambda)':22s}{hdr}   spread")
    for g, lam in [(0.0, 0.0), (0.05, 0.02), (0.10, 0.02), (0.20, 0.05)]:
        p_c, p_f = four_pl(g, lam)
        row = [bstar_agg(p_c, p_f, f) for f in DISTS.values()]
        print(
            f"  ({g:.2f},{lam:.2f})         "
            + "".join(f"{b:20.3f}" for b in row)
            + f"   {max(row) - min(row):7.3f}"
        )
    print(
        "  -> a guessing floor RAISES apparent beta* and reintroduces"
        " distribution dependence.\n"
    )

    try:
        import scipy  # noqa: F401

        have_scipy = True
    except ImportError:
        have_scipy = False
        print("V4 skipped (scipy not installed)\n")

    if have_scipy:
        print("V4 — correlated successes given d (Gaussian copula), 1PL curves")
        print(
            f"{'rho':>6} {'beta* (Beta(2,2))':>18} {'quality gain @ beta=0':>22}"
            f" {'@ beta=0.10':>12}"
        )
        p_c, p_f = rasch()
        f = DISTS["unimodal Beta(2,2)  "]
        for rho in [0.0, 0.3, 0.6, 0.9]:
            pcf = p_both(p_c, p_f, rho)
            b = bstar_agg(p_c, p_f, f, pcf)
            g0 = quality_gain_at(0.0, p_c, p_f, f, pcf)
            g10 = quality_gain_at(0.10, p_c, p_f, f, pcf)
            print(f"{rho:6.1f} {b:18.3f} {g0:+22.4f} {g10:+12.4f}")
        print(
            "  -> correlation collapses BOTH the quality advantage and beta*."
            "\n  -> the '+4.0pp at beta=0' headline assumes the two models fail"
            " independently given d. Correlated failure modes (shared training"
            " data) erase it. The scalar-difficulty model builds this"
            " assumption in silently.\n"
        )

    print("V5 — difficulty-dependent beta(d): measured beta-hat vs the truth")
    print("     beta(d) linear from beta(0)=b_easy to beta(1)=b_hard; 1PL curves")
    print(
        f"{'(b_easy,b_hard)':>16} {'distribution':>22} {'beta-hat':>9}"
        f" {'verdict vs beta*':>17} {'true gain':>10} {'truth':>7}"
    )
    p_c, p_f = rasch()
    for be, bh in [(0.02, 0.20), (0.20, 0.02), (0.16, 0.02), (0.11, 0.11)]:
        beta_d = be + (bh - be) * D
        for name, f in DISTS.items():
            w_bad = (1 - p_c) * f  # where bad artifacts live
            bhat = np.trapezoid(beta_d * w_bad, D) / np.trapezoid(w_bad, D)
            true = np.trapezoid(
                ((1 - ALPHA) * p_c * (1 - p_f) - beta_d * p_f * (1 - p_c)) * f, D
            )
            verdict = "SAFE" if bhat < CLOSED else "unsafe"
            truth = "GOOD" if true > 0 else "BAD"
            flag = "  <-- FALSE SAFE" if (verdict == "SAFE" and true < 0) else ""
            print(
                f"  ({be:.2f},{bh:.2f})    {name:>22} {bhat:9.3f}"
                f" {verdict:>17} {true:+10.4f} {truth:>7}{flag}"
            )
    print(
        "  -> beta-hat weights bad artifacts by (1-p_c)f; the decision-"
        "relevant weight carries an extra p_f(d)."
        "\n  -> when beta is high on EASY tasks (undertested trivial changes)"
        " the measured beta-hat UNDERSTATES the harm and can declare SAFE"
        " while the cascade loses quality. The dangerous direction is the"
        " plausible one."
    )

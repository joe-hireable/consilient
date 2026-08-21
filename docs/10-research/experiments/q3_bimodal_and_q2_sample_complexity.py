"""
Q3 (bimodal difficulty) and Q2 (beta sample complexity).
Run: python q3_bimodal_and_q2_sample_complexity.py     (needs numpy)

Q3 RESULT: beta* is INVARIANT to the difficulty distribution. Closed form:
    beta* = (1 - alpha) * exp(-k * gap)
derived by setting the POINTWISE advantage to zero; d cancels under a logistic
(Rasch / 1PL) competence model. See ADR-0002.

Q2 RESULT: the conservative rule (declare safe only if the Wilson upper bound
clears beta*) has a zero false-safe rate at every n tested, but is underpowered
near the threshold. 50-200 accepted diffs suffice when beta is far from beta*.
"""
import numpy as np

rng = np.random.default_rng(23)


def sig(x):
    return 1 / (1 + np.exp(-x))


K, ALPHA, S_F = 8.0, 0.03, 0.72


# ---------------------------------------------------------------- Q3
def mix(N, w_easy):
    """easy mode Beta(2,12) mean .14 ; hard mode Beta(12,2) mean .86. d = DIFFICULTY."""
    m = rng.random(N) < w_easy
    return np.where(m, rng.beta(2, 12, N), rng.beta(12, 2, N))


DISTS = {
    "unimodal Beta(2,2)  ": lambda N: rng.beta(2, 2, N),
    "bimodal 70% easy    ": lambda N: mix(N, .70),
    "bimodal 50% easy    ": lambda N: mix(N, .50),
    "bimodal 90% easy    ": lambda N: mix(N, .90),
    "bimodal 30% easy    ": lambda N: mix(N, .30),
}


def delta(dfn, beta, s_c, N=300_000):
    d = dfn(N)
    okc = rng.random(N) < sig(K * (s_c - d))
    okf = rng.random(N) < sig(K * (S_F - d))
    p = np.where(okc, rng.random(N) > ALPHA, rng.random(N) < beta)
    return np.where(p, okc, okf).mean() - okf.mean()


def bstar_empirical(dfn, s_c):
    lo, hi = 1e-4, .99
    if delta(dfn, lo, s_c) < 0:
        return None
    if delta(dfn, hi, s_c) > 0:
        return 1.0
    for _ in range(26):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if delta(dfn, m, s_c) > 0 else (lo, m)
    return (lo + hi) / 2


def bstar_closed_form(gap, alpha=ALPHA, k=K):
    return (1 - alpha) * np.exp(-k * gap)


# ---------------------------------------------------------------- Q2
def wilson(k_, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k_ / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


if __name__ == "__main__":
    gaps = [(0.30, 0.42), (0.40, 0.32), (0.45, 0.27), (0.55, 0.17), (0.62, 0.10)]

    print("Q3 — empirical beta* (rows = difficulty distribution, cols = capability gap)")
    print(f"{'':22s}" + "".join(f"{g:>10.2f}" for _, g in gaps))
    for name, dfn in DISTS.items():
        print(f"{name}" + "".join(f"{bstar_empirical(dfn, s_c):10.3f}" for s_c, _ in gaps))
    print(f"{'CLOSED FORM         ':22s}"
          + "".join(f"{bstar_closed_form(g):10.3f}" for _, g in gaps))
    print("  -> distribution-free. beta* = (1-alpha)*exp(-k*gap)\n")

    print("Q3 — escalation rate varies hugely even though beta* does not (beta=0.10)")
    for name, dfn in DISTS.items():
        N = 200_000
        d = dfn(N)
        okc = rng.random(N) < sig(K * (0.45 - d))
        p = np.where(okc, rng.random(N) > ALPHA, rng.random(N) < 0.10)
        print(f"  {name} cheap solves {okc.mean()*100:5.1f}%  escalates {(~p).mean()*100:5.1f}%")
    print("  -> SAFETY (beta*) and SAVINGS (escalation rate) separate cleanly.\n")

    BSTAR = bstar_closed_form(0.27)
    print(f"Q2 — Wilson 95% CI on beta (beta* = {BSTAR:.3f} at a 0.27 gap)")
    print(f"{'accepted diffs':>15} {'true beta':>10} {'95% CI':>22}")
    for n in [20, 50, 100, 200, 500]:
        for tb in [0.05, 0.15]:
            lo, hi = wilson(round(tb * n), n)
            print(f"{n:15d} {tb:10.2f}   [{lo:.3f}, {hi:.3f}]")

    print("\nQ2 — conservative rule: declare SAFE only if Wilson upper bound < beta*")
    print(f"{'n':>6}" + "".join(f"{t:>10.2f}" for t in [0.04, 0.08, 0.15, 0.25]))
    for n in [20, 50, 100, 200, 400, 800]:
        row = []
        for tb in [0.04, 0.08, 0.15, 0.25]:
            ks = rng.binomial(n, tb, 8000)
            row.append(np.mean([wilson(int(x), n)[1] < BSTAR for x in ks]))
        print(f"{n:6d}" + "".join(f"{v:10.3f}" for v in row))
    print("  cols 0.04/0.08 are TRULY SAFE  -> higher is better (power)")
    print("  cols 0.15/0.25 are TRULY UNSAFE -> this is the FALSE-SAFE rate, must be ~0")

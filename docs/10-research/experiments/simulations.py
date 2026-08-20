"""
All five simulations behind docs/10-research/findings.md, consolidated.

Run:  python simulations.py            (needs numpy; exp2 also needs scipy)

READ THIS FIRST
---------------
These answer SIGN and THRESHOLD questions ("does the answer flip, and where?").
They do NOT produce point estimates about the real world. The competence model
(sigmoid over Beta-distributed difficulty) was invented. Attack it: in particular
try a bimodal difficulty distribution, which is the most likely way these results
are wrong. See "What would falsify the thesis" in findings.md.

Symbols
-------
  beta   P(verifier accepts | artifact is bad)   <- the master parameter
  alpha  P(verifier rejects | artifact is good)  <- flaky-test rate
  s_m    competence of model m (higher = solves harder tasks)
  k      sharpness of the competence curve
"""
import numpy as np

rng = np.random.default_rng(7)
sig = lambda x: 1 / (1 + np.exp(-x))


# --------------------------------------------------------------------------
# EXP 1 — cascade economics with an imperfect verifier
# --------------------------------------------------------------------------
def exp1(N=400_000, k=8.0, s_c=0.45, s_f=0.72, alpha=0.03, beta=0.15,
         c_cheap=1.0, c_front=25.0, c_v=0.4):
    d = rng.beta(2, 2, N)
    ok_c = rng.random(N) < sig(k * (s_c - d))
    ok_f = rng.random(N) < sig(k * (s_f - d))
    passes = np.where(ok_c, rng.random(N) > alpha, rng.random(N) < beta)
    esc = ~passes
    shipped = np.where(passes, ok_c, ok_f)
    cost = c_cheap + c_v + esc * (c_front + c_v)
    return dict(escalation=esc.mean(), quality=shipped.mean(), cost=cost.mean(),
                frontier_quality=ok_f.mean(), frontier_cost=c_front + c_v)


# --------------------------------------------------------------------------
# EXP 2 — critical beta*, and whether depth helps
# --------------------------------------------------------------------------
def quality_delta(beta, s_c=0.45, s_f=0.72, k=8.0, N=300_000, alpha=0.03):
    d = rng.beta(2, 2, N)
    ok_c = rng.random(N) < sig(k * (s_c - d))
    ok_f = rng.random(N) < sig(k * (s_f - d))
    passes = np.where(ok_c, rng.random(N) > alpha, rng.random(N) < beta)
    return np.where(passes, ok_c, ok_f).mean() - ok_f.mean()


def three_tier(N=300_000, k=8.0, alpha=0.03, beta=0.10,
               s=(0.45, 0.60, 0.72), c=(1.0, 6.0, 25.0), c_v=0.4):
    d = rng.beta(2, 2, N)
    ok = [rng.random(N) < sig(k * (si - d)) for si in s]
    pas = [np.where(o, rng.random(N) > alpha, rng.random(N) < beta) for o in ok]
    shipped = np.where(pas[0], ok[0], np.where(pas[1], ok[1], ok[2]))
    e1 = ~pas[0]
    e2 = e1 & ~pas[1]
    cost = c[0] + c_v + e1 * (c[1] + c_v) + e2 * (c[2] + c_v)
    return shipped.mean(), cost.mean(), e1.mean(), e2.mean()


# --------------------------------------------------------------------------
# EXP 3 / 4a — is a LEARNED router worth building?
# --------------------------------------------------------------------------
K = 8
TRUE_S_C = np.array([0.62, 0.40, 0.28, 0.70, 0.80, 0.68, 0.30, 0.45])
S_F, KK, LAM = 0.78, 8.0, 0.004
CP = np.array([.22, .14, .16, .12, .08, .10, .06, .12]); CP = CP / CP.sum()


def episode(cls, use_cheap, rs, c_cheap=1.0, c_front=25.0, c_v=0.4, waste=1.0):
    d = rs.beta(2, 2)
    ok_c = rs.random() < sig(KK * (TRUE_S_C[cls] - d))
    ok_f = rs.random() < sig(KK * (S_F - d))
    if use_cheap:
        passes = (rs.random() > 0.03) if ok_c else (rs.random() < 0.08)
        if passes:
            return ok_c, c_cheap + c_v
        return ok_f, c_cheap + c_v + (c_front + c_v) * waste
    return ok_f, c_front + c_v


def evaluate(policy, n=40_000, seed=99):
    rs = np.random.default_rng(seed)
    q = c = 0
    for _ in range(n):
        cls = rs.choice(K, p=CP)
        ok, cost = episode(cls, policy(cls), rs)
        q += ok; c += cost
    return q / n, c / n


def learn(n_traj, seed=1):
    """Thompson sampling over {cheap, frontier} per task class."""
    rs = np.random.default_rng(seed)
    a = np.ones((K, 2)); b = np.ones((K, 2))
    for _ in range(n_traj):
        cls = rs.choice(K, p=CP)
        arm = int(np.argmax(rs.beta(a[cls], b[cls])))   # 0 = cheap
        ok, cost = episode(cls, arm == 0, rs)
        r = float(np.clip(ok - LAM * cost, 0, 1))
        a[cls, arm] += r; b[cls, arm] += 1 - r
    post = a / (a + b)
    return lambda cls: bool(np.argmax(post[cls]) == 0)


# --------------------------------------------------------------------------
# EXP 5 — review bottleneck. EXACT ALGEBRA, no simulation assumptions.
# --------------------------------------------------------------------------
def max_agents(T_agent_cycle, T_effective_review):
    return T_agent_cycle / T_effective_review


def with_critic(T_a=25.0, T_r=8.0, p_good=0.55, recall=0.0):
    """recall = fraction of BAD diffs the critic rejects before a human sees them.
    NOTE: recall == 1 - beta. Same quantity as exp1. That identity is the thesis."""
    frac_seen = p_good + (1 - p_good) * (1 - recall)
    T_eff = frac_seen * T_r
    return max_agents(T_a, T_eff), (60 / T_eff) * p_good


if __name__ == "__main__":
    print("EXP1 baseline (beta=0.15):", {k: round(v, 4) for k, v in exp1().items()})
    print("\nEXP1 sweep — beta : quality delta vs frontier : cost %")
    for beta in [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.60]:
        r = exp1(beta=beta)
        print(f"  {beta:.2f}  {r['quality'] - r['frontier_quality']:+.4f}  "
              f"{100 * r['cost'] / r['frontier_cost']:.1f}%")

    try:
        from scipy.optimize import brentq
        print("\nEXP2 critical beta* by capability gap")
        for s_c in [0.30, 0.40, 0.45, 0.55, 0.62]:
            bstar = brentq(lambda b: quality_delta(b, s_c=s_c), 1e-3, 0.95, xtol=1e-3)
            print(f"  gap {0.72 - s_c:.2f} -> beta* {bstar:.3f}")
    except ImportError:
        print("\nEXP2 skipped (scipy not installed)")

    q3, c3, e1, e2 = three_tier()
    print(f"\nEXP2b three-tier: quality {q3:.4f}  cost {c3:.2f} "
          f"({100 * c3 / 25.4:.1f}% of frontier)  esc {e1:.1%}/{e2:.1%}")

    qc, cc = evaluate(lambda c_: True)
    qf, cf = evaluate(lambda c_: False)
    best_fixed = max(qc - LAM * cc, qf - LAM * cf)
    print(f"\nEXP3 best fixed policy utility {best_fixed:.4f}")
    for n in [500, 2500, 5000, 25000]:
        us = []
        for s in range(4):
            q, c = evaluate(learn(n, seed=s + 1), n=12_000, seed=1000 + s)
            us.append(q - LAM * c)
        print(f"  {n:6d} trajectories -> {np.mean(us) - best_fixed:+.4f} vs best fixed")

    print("\nEXP5 review ceiling (exact)")
    for R in [0.0, 0.5, 0.85, 0.95]:
        n, g = with_critic(recall=R)
        print(f"  critic recall {R:.2f} -> {n:.1f} agents, {g:.1f} good merges/hr")

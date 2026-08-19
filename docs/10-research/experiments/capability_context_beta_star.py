"""
Two claimed Delta-narrowing mechanisms, checked against the closed form.

Run: python capability_context_beta_star.py      (needs numpy)

CLAIM 1 (capability layer): "a cheap model without browse/docx/search tools has a
wider capability gap Delta; supplying tools natively narrows Delta and loosens
beta* = (1-alpha)*exp(-k*Delta)."

VERDICT FROM THIS MODEL: the arithmetic on beta* is right but the mechanism is
wrong. Delta in the Rasch model is REASONING competence; a 4B model with a
browser is still a 4B model, so s_c does not move. Missing capabilities are not
a competence shift — they are STRUCTURAL ZEROS: tasks the cheap tier cannot
attempt at all (p_c = 0 regardless of difficulty). What structural zeros do to
the cascade depends entirely on whether the verifier catches capability
failures:

  r = P(checks accept | capability-blocked bad artifact) / beta
  r = 0  -> blocked tasks ALWAYS escalate. beta*_eff is UNCHANGED; the cost is
            pure waste (extra guaranteed escalations). Tool layer = cost lever.
  r = 1  -> blocked failures pass checks as often as any bad artifact.
            beta*_eff drops BELOW the closed form (false-safe direction again).
            Tool layer = safety lever.

Which regime a repo is in is a per-check-class measurement (ADR-0012), not a
derivable fact. "Hallucinated instead of searching" is plausibly r >= 1 (tests
cannot check facts); "failed to produce the docx" is plausibly r ~= 0 (file
existence is checkable).

CLAIM 2 (context discipline): "loading irrelevant tools degrades the model's
effective competence on the SAME task; fewer irrelevant tools -> higher s_c ->
narrower Delta -> looser beta*."

VERDICT FROM THIS MODEL: unlike claim 1 this IS a competence effect, so the
Delta mapping is legitimate GIVEN the Rasch frame. The load-bearing assumptions
are (a) the degradation-with-tool-count effect is real for current small models
(empirical, EXP-18) and (b) it is ASYMMETRIC — the delegated frontier path
already has progressive disclosure (Claude Code ships tool search), so clutter
taxes the cheap/native path more. The "optimum number of tools" is real but it
is a COMPOSITE of two different mechanisms, not one curve: below n_req you hit
claim 1's feasibility cliff (structural zero); above it you ride claim 2's
competence slope. The optimum is simply "exactly the required set".
"""

import numpy as np

ALPHA, K, S_C, S_F = 0.03, 8.0, 0.45, 0.72
sig = lambda x: 1 / (1 + np.exp(-x))
D = np.linspace(1e-6, 1 - 1e-6, 4001)


def beta22(a=2, b=2):
    from math import lgamma

    ln = (
        (a - 1) * np.log(D)
        + (b - 1) * np.log(1 - D)
        - (lgamma(a) + lgamma(b) - lgamma(a + b))
    )
    return np.exp(ln)


F = beta22()
P_C, P_F = sig(K * (S_C - D)), sig(K * (S_F - D))
N0 = np.trapezoid(P_C * (1 - P_F) * F, D)  # E[p_c(1-p_f)] on feasible tasks
D0 = np.trapezoid(P_F * (1 - P_C) * F, D)  # E[p_f(1-p_c)]
EPF = np.trapezoid(P_F * F, D)  # E[p_f]
EPC = np.trapezoid(P_C * F, D)  # E[p_c]
BSTAR0 = (1 - ALPHA) * N0 / D0


def beta_star_eff(phi, r):
    """phi = fraction of tasks capability-blocked for the cheap tier;
    r scales how often blocked failures pass checks relative to generic beta."""
    num = (1 - ALPHA) * (1 - phi) * N0
    den = (1 - phi) * D0 + phi * r * EPF
    return num / den


if __name__ == "__main__":
    print(f"baseline: gap {S_F - S_C:.2f}, closed-form beta* = {BSTAR0:.4f}")
    print(
        f"sanity: (1-a)e^-k*gap at gap 0.42 -> {(1 - ALPHA) * np.exp(-K * 0.42):.4f} "
        f"(user said 3.3%); at 0.17 -> {(1 - ALPHA) * np.exp(-K * 0.17):.4f} (24.9%)  OK\n"
    )

    print("CLAIM 1 — structural zeros, not Delta. beta*_eff by blocked fraction phi")
    print(
        f"{'phi':>6} {'r=0 (caught)':>14} {'r=0.5':>10} {'r=1 (passes)':>14}"
        f" {'waste: extra escalations':>26}"
    )
    for phi in [0.0, 0.1, 0.2, 0.3, 0.5]:
        row = [beta_star_eff(phi, r) for r in (0.0, 0.5, 1.0)]
        waste = phi * (1 - 0.0)  # r=0: every blocked task escalates
        print(f"{phi:6.1f} {row[0]:14.4f} {row[1]:10.4f} {row[2]:14.4f} {waste:26.1%}")
    print("  -> r=0: threshold UNCHANGED (tool layer buys cost, not safety).")
    print("  -> r=1: threshold tightens below the closed form — the closed form is")
    print("     false-safe about capability-blocked tasks it does not model.")
    print("  -> tool provision restores the phi mass to normal Rasch behaviour; the")
    print(
        f"     recovered tasks still succeed only at the cheap tier's rate"
        f" E[p_c]={EPC:.1%} — reasoning competence s_c is untouched.\n"
    )

    print("CLAIM 2 — context clutter as a genuine competence term (illustrative)")
    print("  If deferred loading moves mid-difficulty task success 0.49 -> 0.74")
    print("  (Anthropic Tool Search figure, metric pending verification):")
    ds = (np.log(0.74 / 0.26) - np.log(0.49 / 0.51)) / K
    print(f"  implied competence shift delta_s = {ds:.3f} (vs total gap 0.27)")
    for label, s_c in [("cluttered", S_C - ds), ("disciplined", S_C)]:
        gap = S_F - s_c
        print(
            f"  {label:12s} gap {gap:.3f} -> beta* {(1 - ALPHA) * np.exp(-K * gap):.4f}"
        )
    print(
        "  -> clutter tightens beta* ~%.1fx. Direction robust; magnitude rests on"
        % (np.exp(K * ds))
    )
    print("     what the 49->74 metric actually measured, and on the asymmetry")
    print("     assumption (frontier path already context-disciplined). [asserted]\n")

    print("The composite curve: success(n tools) for a task needing n_req=4, d=0.45")
    n_req, gamma = 4, 0.017  # gamma: competence lost per irrelevant tool [asserted]
    for n in [2, 3, 4, 6, 10, 15, 25, 40]:
        feasible = n >= n_req
        s_eff = S_C - gamma * max(0, n - n_req)
        p = feasible * sig(K * (s_eff - 0.45))
        print(f"  n={n:3d}  feasible={str(bool(feasible)):5s}  p_success={p:.3f}")
    print("  -> left of n_req: cliff (claim 1's mechanism). Right: slope (claim 2's).")
    print("  -> the 'optimum' is exactly the required set; it is two mechanisms, one")
    print("     of which (the slope, gamma) is unmeasured for local models -> EXP-18.")


# ---------------------------------------------------------------------------
# PART C — CLAIM 3 (reasoning layer). Two results, both [algebra]:
#
# C1. Self-consistency (majority-of-n) does NOT shift the competence curve —
#     it STEEPENS it. Majority-of-5 multiplies the logistic slope at the
#     midpoint by 1.875, i.e. k_c,eff ~= 1.875*k_c. That is exactly the
#     unequal-slopes case V1 of robustness_beta_star.py, which destroys the
#     distribution-freeness of beta*. A reasoning layer modelled honestly
#     does not slide along the closed form; it breaks out of it.
#
# C2. VERIFIER-SHOPPING. Best-of-n against an imperfect verifier (generate
#     candidates until one passes) exposes the verifier n times. For a task
#     the cheap model cannot solve, P(a bad artifact ships) = 1-(1-beta)^n,
#     not beta. Retry loops on the cheap tier inflate effective beta roughly
#     n-fold at small beta. "Best-of-n plus tests" is not free safety.
# ---------------------------------------------------------------------------
from math import comb

def majority(p, n=5):
    p = np.asarray(p)
    return sum(comb(n, j) * p**j * (1 - p)**(n - j) for j in range((n // 2) + 1, n + 1))

def part_c():
    dists = {
        "unimodal Beta(2,2)": beta22(2, 2),
        "bimodal 90% easy  ": .90 * beta22(2, 12) + .10 * beta22(12, 2),
        "bimodal 50% easy  ": .50 * beta22(2, 12) + .50 * beta22(12, 2),
        "bimodal 30% easy  ": .30 * beta22(2, 12) + .70 * beta22(12, 2),
    }
    print("C1 — majority-of-5 self-consistency steepens the curve (slope x1.875 at p=0.5)")
    p_sc = majority(P_C, 5)
    print(f"   E[p_c] single {EPC:.3f} -> majority-of-5 "
          f"{np.trapezoid(p_sc * F, D):.3f}   (token cost x5)")
    print(f"{'distribution':22s}{'beta* single':>14}{'beta* maj-5':>13}")
    for name, f in dists.items():
        b1 = (1 - ALPHA) * np.trapezoid(P_C * (1 - P_F) * f, D) / np.trapezoid(P_F * (1 - P_C) * f, D)
        b5 = (1 - ALPHA) * np.trapezoid(p_sc * (1 - P_F) * f, D) / np.trapezoid(P_F * (1 - p_sc) * f, D)
        print(f"  {name:20s}{b1:14.3f}{b5:13.3f}")
    print("   -> single-sample column is flat (closed form holds); majority-5 column")
    print("      VARIES BY DISTRIBUTION: the scaffolded cheap tier is a 2PL model and")
    print("      the distribution-free property is gone. Gain is real, formula is not.\n")

    print("C2 — verifier-shopping: P(bad ships | model cannot solve task) = 1-(1-beta)^n")
    print(f"{'beta':>8}" + "".join(f"{n:>10}" for n in [1, 2, 3, 5, 8]))
    for b in [0.02, 0.05, 0.10, 0.15]:
        print(f"{b:8.2f}" + "".join(f"{1-(1-b)**n:10.3f}" for n in [1, 2, 3, 5, 8]))
    print("   -> best-of-n / retry-on-fail multiplies verifier exposure. At beta=0.10,")
    print("      five attempts ship a bad artifact 41% of the time the task is beyond")
    print("      the model. Any reasoning layer that resamples must count this.")

if __name__ == "__main__":
    print()
    part_c()

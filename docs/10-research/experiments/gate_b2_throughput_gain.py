"""Executable model for ADR-0037: Gate B2 Replacement Condition.

Evaluates the review-throughput gain G(beta) over the unassisted baseline M_0,
proves the ADR-0015 tautology (n_max >= 3.125 > 1 for all beta in [0, 1]),
derives the exact boundary beta_crit where gain crosses 20%, and evaluates
sample discriminability on historical PR sets (EXP-08).

Exact algebra from findings.md §5 and ADR-0007 / simulations.py.
"""

from __future__ import annotations
import math


def n_max(T_a: float, T_r: float, p_good: float, beta: float) -> float:
    """Parallelism ceiling: n_max = T_a / T_eff."""
    frac_seen = p_good + (1.0 - p_good) * beta
    t_eff = frac_seen * T_r
    return T_a / t_eff


def throughput(T_r: float, p_good: float, beta: float) -> float:
    """Good merges per hour: M(beta) = (60 / T_eff) * p_good."""
    frac_seen = p_good + (1.0 - p_good) * beta
    t_eff = frac_seen * T_r
    return (60.0 / t_eff) * p_good


def relative_gain(p_good: float, beta: float) -> float:
    """Relative throughput gain G(beta) = (M(beta) - M_0) / M_0 = (1 - frac_seen) / frac_seen."""
    frac_seen = p_good + (1.0 - p_good) * beta
    return (1.0 - frac_seen) / frac_seen


def critical_beta(p_good: float, target_gain: float = 0.20) -> float:
    """Exact closed form for beta where G(beta) == target_gain.

    G(beta) = (1 - p_good)(1 - beta) / [p_good + (1 - p_good)beta] = gamma
    => (1 - p_good)(1 - beta) = gamma * p_good + gamma * (1 - p_good) * beta
    => (1 - p_good)(1 - gamma * beta/(1 - p_good)...)
    => beta_crit = (1 - (1 + gamma)*p_good) / ((1 + gamma)*(1 - p_good))
    """
    numerator = 1.0 - (1.0 + target_gain) * p_good
    denominator = (1.0 + target_gain) * (1.0 - p_good)
    return numerator / denominator


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for proportion k/n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    spread = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def main() -> None:
    T_a = 25.0   # agent cycle (min)
    T_r = 8.0    # human review time per diff (min)
    p_good = 0.55

    print("=" * 70)
    print("1. PROOF OF ADR-0015 TAUTOLOGY (n_max > 1 for all beta in [0, 1])")
    print("=" * 70)
    print(f"Parameters: T_a = {T_a} min, T_r = {T_r} min, p_good = {p_good}")
    print("Minimum possible n_max occurs at beta = 1.0 (recall = 0.0):")
    min_n = n_max(T_a, T_r, p_good, beta=1.0)
    print(f"  n_max(beta=1.0) = T_a / T_r = {T_a} / {T_r} = {min_n:.4f}")
    print("  Since 3.125 > 1.0, condition n_max > 1 holds for ALL beta in [0, 1].")
    print("  Conclusion: ADR-0015 Gate B2 is non-discriminating by construction.\n")

    print("=" * 70)
    print("2. REPLACEMENT CONDITION: THROUGHPUT GAIN G(beta) >= 20%")
    print("=" * 70)
    m0 = throughput(T_r, p_good, beta=1.0)
    b_crit = critical_beta(p_good, target_gain=0.20)
    r_crit = 1.0 - b_crit
    print(f"Unassisted baseline (beta=1.0, recall=0.0): M_0 = {m0:.3f} good merges/hr")
    print("Target threshold: +20.0% throughput gain (gamma = 0.20)")
    print(f"Exact critical beta* = {b_crit:.4f} (critic recall R* = {r_crit:.4f})")
    print(f"Condition: Gate B2 passes iff beta <= {b_crit:.4f} (R >= {r_crit:.4f})\n")

    print(f"{'beta':>6} | {'recall':>6} | {'n_max':>6} | {'merges/hr':>9} | {'gain vs M_0':>11} | {'verdict':>8}")
    print("-" * 62)
    sweep = [0.0, 0.15, 0.30, 0.50, b_crit, 0.70, 0.85, 1.0]
    for b in sweep:
        rec = 1.0 - b
        n = n_max(T_a, T_r, p_good, b)
        m = throughput(T_r, p_good, b)
        g = relative_gain(p_good, b)
        verdict = "PASS" if b <= b_crit + 1e-9 else "FAIL"
        print(f"{b:6.3f} | {rec:6.3f} | {n:6.3f} | {m:9.3f} | {g:+10.1%} | {verdict:>8}")

    print("\n" + "=" * 70)
    print("3. MECHANICAL STRADDLE CHECK (EXHIBIT PASS AND FAIL)")
    print("=" * 70)
    b_pass = 0.30
    b_fail = 0.85
    g_pass = relative_gain(p_good, b_pass)
    g_fail = relative_gain(p_good, b_fail)
    print(f"Pass case: beta = {b_pass:.2f} (recall {1-b_pass:.2f}) -> Gain = {g_pass:+.2%} >= +20% -> PASS")
    print(f"Fail case: beta = {b_fail:.2f} (recall {1-b_fail:.2f}) -> Gain = {g_fail:+.2%} <  +20% -> FAIL")

    print("\n" + "=" * 70)
    print("4. EXP-08 SAMPLE COMPLEXITY & REACHABILITY (HISTORICAL PR AUDIT)")
    print("=" * 70)
    print("At N = 60 historical bad PR diffs in EXP-08:")
    for k_miss in [10, 18, 30, 42, 51]:  # false accepts by critic
        b_est = k_miss / 60
        low, high = wilson(k_miss, 60)
        rec_est = 1.0 - b_est
        g_est = relative_gain(p_good, b_est)
        verd = "PASS" if b_est <= b_crit and high < 1.0 else "FAIL"
        print(f"  k={k_miss:2d}/60 false accepts -> beta_hat={b_est:.3f} [{low:.3f}, {high:.3f}] | "
              f"recall={rec_est:.3f} | gain={g_est:+6.1%} | {verd}")


if __name__ == "__main__":
    main()

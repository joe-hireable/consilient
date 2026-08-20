"""Does EXP-01's pre-registered stopping rule fire on all available history?

Rule, fixed 19 Aug 2026: "if the interval cannot be narrowed below +/-0.05 with all
available history, beta is not measurable at solo-founder volumes and ADR-0002 fails."

Everything below is arithmetic over counts already measured and recorded in
findings-alpha-2026-08-20.md. No new mining, no private detail.
"""
from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def half_width(k: int, n: int) -> float:
    lo, hi = wilson(k, n)
    return (hi - lo) / 2


def n_required(p: float, target_half: float = 0.05, z: float = 1.96) -> int:
    """Smallest n whose Wilson half-width at rate p is <= target."""
    n = 10
    while n < 10_000_000:
        if half_width(round(p * n), n) <= target_half:
            return n
        n += 1
    return -1


print("MEASURED, from findings-alpha-2026-08-20.md")
rows = [
    ("jobboard-v2 metadata proxy", 128, 188),
    ("jobboard-v2, as first recorded", 128, 203),
]
for label, k, n in rows:
    lo, hi = wilson(k, n)
    print(f"  {label:<34} beta = {k}/{n} = {k/n:.4f}  [{lo:.4f}, {hi:.4f}]  half-width {half_width(k,n):.4f}")

# hireable-platform: 22 bad PRs, 21 carrying a recorded verdict.
POOLED_N = 188 + 21
print(f"\n  pooled evaluable bad artefacts across BOTH corpora: {POOLED_N}")

print("\nWHAT +/-0.05 WOULD REQUIRE")
for p, note in ((0.6809, "at the measured proxy rate"), (0.50, "at the worst case p=0.5")):
    need = n_required(p)
    print(f"  p = {p:.4f} {note:<28} needs n = {need}")

need = n_required(0.6809)
print(f"\n  available {POOLED_N} vs required {need}  ->  shortfall {need - POOLED_N} "
      f"({POOLED_N / need:.1%} of what the rule demands)")

print("\nTHE OTHER ROUTE — executable replay (EXP-43)")
lo, hi = wilson(0, 50)
print(f"  beta = 0/50 = 0.0000  [{lo:.4f}, {hi:.4f}]  half-width {half_width(0,50):.4f}  "
      f"-> below 0.05: {half_width(0,50) <= 0.05}")
print("  ...but censored on 72.8-75.9% of merges (greenfield blindness), so the interval")
print("     is narrow over roughly a quarter of the population.")

print("\nTHE GAP BETWEEN THE TWO INSTRUMENTS")
print(f"  proxy point 0.6809 vs replay point 0.0000  ->  difference {0.6809:.4f}")
print(f"  the stopping rule's tolerance is +/-0.05, which is {0.6809/0.05:.0f}x smaller")
print("     than the disagreement between the two ways of measuring the same quantity.")

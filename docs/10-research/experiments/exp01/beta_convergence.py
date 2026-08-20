"""Is the two-family agreement on corrected beta real, or arithmetic cancellation?

Two blind adjudications of the same 75 bad-and-red PRs report beta within 1 point of each
other - 0.862 and 0.871 - while disagreeing by 16 PRs on how many bad labels are genuine.
That is suspicious. beta's corrected form moves confirmed-bad-with-spurious-red PRs INTO the
numerator and drops refuted-bad PRs FROM the denominator, so an adjudicator that refutes more
labels also tends to promote fewer, and the ratio can be stable while its inputs are not.

The test: recompute beta under every CROSS combination of the two adjudications' inputs. If
the cross terms stay inside the reported range, the agreement is robust. If they spread wider,
the headline convergence is partly cancellation and must be reported as such.

Aggregate counts only.
"""

BAD_GREEN = 128
BAD_TOTAL = 203

# (label, confirmed-bad-with-non-meaningful-red -> moves to numerator, refuted-bad -> leaves denominator)
ADJUDICATIONS = {
    "gpt-5.6": {"promote": 16, "refute": 36},
    "gemini-3.7": {"promote": 27, "refute": 25},
}


def beta(promote: int, refute: int) -> float:
    return (BAD_GREEN + promote) / (BAD_TOTAL - refute)


print(f"uncorrected beta = {BAD_GREEN}/{BAD_TOTAL} = {BAD_GREEN / BAD_TOTAL:.4f}\n")

print("as each adjudication reports it:")
for name, v in ADJUDICATIONS.items():
    b = beta(v["promote"], v["refute"])
    print(
        f"  {name:12} promote={v['promote']:>3} refute={v['refute']:>3}  "
        f"beta = {BAD_GREEN + v['promote']}/{BAD_TOTAL - v['refute']} = {b:.4f}"
    )

print("\nevery cross combination of the two adjudications' inputs:")
values = []
for pname, p in ADJUDICATIONS.items():
    for rname, r in ADJUDICATIONS.items():
        b = beta(p["promote"], r["refute"])
        values.append(b)
        marker = "  <- as reported" if pname == rname else ""
        print(f"  promote from {pname:12} refute from {rname:12} -> {b:.4f}{marker}")

lo, hi = min(values), max(values)
reported = [beta(v["promote"], v["refute"]) for v in ADJUDICATIONS.values()]
r_lo, r_hi = min(reported), max(reported)

print(f"\nreported spread : {r_lo:.4f} to {r_hi:.4f}  (width {r_hi - r_lo:.4f})")
print(f"cross spread    : {lo:.4f} to {hi:.4f}  (width {hi - lo:.4f})")
print(f"inflation factor: {(hi - lo) / (r_hi - r_lo):.1f}x")
print(
    "\nThe reported agreement is narrower than the disagreement in its inputs warrants.\n"
    "Both adjudications happen to trade a larger numerator against a smaller denominator in\n"
    "roughly compensating amounts, so beta is stable while the labels underneath are not.\n"
    "The honest interval is the cross spread, and the honest claim is the SIGN: beta is far\n"
    "above the recorded 0.6305, and the two families agree on that without qualification."
)

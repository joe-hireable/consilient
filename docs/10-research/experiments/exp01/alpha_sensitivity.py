"""What the measured alpha does to beta*, computed rather than reasoned about.

`capability_context_beta_star.py` hardcodes `ALPHA = 0.03` and states the model as
`beta* = (1 - alpha) * exp(-k * Delta)` with `k = 8.0`. beta* is linear in `(1 - alpha)`,
so a wrong alpha rescales every threshold by a constant factor at every capability gap.

The 0.03 was invented. EXP-01's mined records carry the labels alpha needs — alpha and beta
are the two off-diagonal cells of one contingency table, and beta discards exactly the rows
alpha requires. See `two_by_two.py` for the table these rates are read off.

Run: python alpha_sensitivity.py
"""

from __future__ import annotations

import math

K = 8.0
ALPHA_ASSUMED = 0.03

# Measured on EXP-01's mined records, 20 August 2026. `two_by_two.py` prints these with
# their Wilson intervals; the counts are repeated here so the script is self-contained.
CANDIDATES = [
    ("0.03 assumed, invented", 0.03, None),
    ("jobboard-v2, measured", 23 / 97, (0.1635, 0.3307)),
    ("hireable-platform, measured", 4 / 28, (0.0570, 0.3149)),
    ("hireable-platform, unrun checks counted", 10 / 34, (0.1683, 0.4617)),
    ("0.327, merge-decision-selected (NOT alpha)", 98 / 300, None),
]

GAPS = [0.17, 0.27, 0.42]


def beta_star(alpha: float, gap: float) -> float:
    return (1 - alpha) * math.exp(-K * gap)


def main() -> None:
    print(f"beta* = (1 - alpha) * exp(-{K} * gap)\n")
    header = "  ".join(f"gap {g:.2f}" for g in GAPS)
    print(f"{'alpha':44} {'value':>7}  {header}   scale vs assumed")
    for label, alpha, interval in CANDIDATES:
        row = "  ".join(f"{beta_star(alpha, g):8.4f}" for g in GAPS)
        scale = (1 - alpha) / (1 - ALPHA_ASSUMED)
        print(f"{label:44} {alpha:7.4f}  {row}   {scale:.4f}")
        if interval is not None:
            lo, hi = interval
            span = f"{beta_star(hi, 0.27):.4f} to {beta_star(lo, 0.27):.4f}"
            print(f"{'':44} {'':7}  Wilson95 on alpha -> beta*(0.27) in {span}")

    print(
        "\nThe scale factor is exact and gap-independent because beta* is linear in (1 - alpha).\n"
        "Every measured candidate, and every Wilson bound of every measured candidate, lies\n"
        "above 0.03. The assumed value is not merely imprecise; it is outside the interval.\n"
        "\n"
        "0.327 is listed because it circulated as a substitute and it is NOT alpha: it is\n"
        "P(CI red | merged), selected on the merge decision rather than on artefact quality.\n"
        "It is shown only to demonstrate that the direction of the error does not depend on\n"
        "which wrong quantity you reach for."
    )


if __name__ == "__main__":
    main()

# Gate B2 cannot fail, and the β meter is not connected to the β experiment

**20 August 2026.** Three claims were left unverified when the same-family control was recorded.
An unverified claim in this evidence base is a debt, so all three were put to an independent
verification pass. Verdicts: **CONFIRMED**, **PARTLY**, **PARTLY** — and the two partials are more
interesting than the confirmation.

---

## 1. Gate B2 cannot fail — CONFIRMED, and worse than the claim stated

ADR-0015 Gate B condition 2: *"EXP-08 complete: critic recall measured, and the derived
parallelism ceiling is > 1."*

The model it rests on is `findings.md` § 5, implemented in `simulations.py`:

```
frac_seen = p_good + (1 − p_good)(1 − recall)
T_eff     = frac_seen · T_r
n_max     = T_a / T_eff
```

Since `recall ∈ [0,1]` and `p_good ∈ [0,1]`, `frac_seen ≤ 1`, so `T_eff ≤ T_r` and therefore

> **`n_max ≥ T_a / T_r = 25 / 8 = 3.125`**

**for every value of critic recall, and therefore for every value of β — including β = 1.0**, a
critic that catches nothing at all. The gate asks whether a quantity whose floor is 3.125 exceeds
1. [measured]

**A threshold below the minimum possible value of the quantity it gates passes by tautology.**

The ADR states its own belief plainly, and the belief is false under its own model:

> *"If measured critic recall yields a ceiling of 1, orchestration provides no throughput at all
> and Stage 3 is pure risk."* — ADR-0015

Critic recall cannot yield a ceiling of 1. Recall only ever *raises* `n_max` above the 3.125
floor set by the cycle-to-review ratio; it has no path to lowering it.

**Why this matters more than an arithmetic slip.** Gate B2 is the project's **only** gate
condition whose value depends on β. Every other condition asks whether something exists, ran, or
completed. So as the gate system currently stands, **β is not load-bearing on any decision it
makes.** The project's central quantity gates nothing. [asserted]

**A second defect found in passing.** The ceiling table (3.1 through 5.5 agents) is tagged
`[algebra]`. The formula is algebra; the *numbers* are that formula evaluated on three unmeasured
point estimates — `T_a = 25 min`, `T_r = 8 min`, `p_good = 0.55`. [measured] Algebra evaluated on
invented inputs is not algebra about the world, and working principle 2 — sign and threshold,
never point estimates — applies to it.

**What would fix the gate.** Not a bigger threshold: the condition needs to name a quantity that
β can actually move. The honest candidates are `good merges/hr` at measured recall against the
recall-0 baseline, or a directly measured β against β\*. Both require EXP-08, which has not run.
Until then Gate B2 should be marked **non-discriminating** rather than merely unmet.

---

## 2. The mining route cannot feed β — PARTLY: right outcome, wrong mechanism, bigger problem

The claim was that `mine_beta.py` fetches `--state merged`, so every row is a human accept and
`n_rejected` is zero forever.

The fetch filter is real — `mine_beta.py` does pass `--state merged`. But the stated mechanism is
**not** why the route fails, and the real reason is worse:

- **There is no pipeline at all.** `mine_beta.py` writes private JSON to `data/<repo>-prs.json`.
  Nothing in `src/consilience/` reads it. No adapter, no loader, no ingestion path converts it
  into schema-v1 `attempt.outcome` events. [measured]
- **The product explicitly forbids what the experiment produces.** `beta.py`: *"No proxy label is
  accepted here — the caller must have resolved a real verdict before the row reaches this
  function."* `mine_beta.py` produces nothing *but* proxy labels — reverted or hotfixed. [measured]
- **They compute different quantities.** `mine_beta.py` gives P(bad | CI green); `beta.py` gives
  P(verifier accepted | human rejected). Different conditioning, different data, different
  validation rules.

**So the correct statement is not "the denominator is empty". It is that the retrospective
experiment and the prospective meter are two unconnected pieces of software computing two
different quantities from disjoint sources, and nothing has ever joined them.** [measured]

That reframes the axis defect recorded earlier. It is not only that `mine_beta.py` conditions the
wrong way round — it is that even conditioned correctly, its output could not reach `compute()`,
because proxy labels are inadmissible by design and there is no path for them to travel.

`findings-exp01.md` documents the proxy-label noise honestly — 7% hotfix precision, ~20% clean
miss rate — and does not address the architectural disconnect at all.

---

## 3. β\* is absent from the specification and the code — PARTLY

**Confirmed:** `β*` (in every spelling) appears **zero times** in `docs/40-spec/v0-draft.md` and
zero times in `src/consilience/`. Nothing in the code compares a measured β against any
threshold; `beta.py` computes a point estimate and a Wilson interval and checks a sample floor,
and that is all. [measured]

**Refuted:** the claim that it lives in "research notes and one ADR". It is in **three** ADRs —
0002, 0005, 0025 — plus seven design documents and three context documents. [measured]

**The honest reading is between the two.** β\* is thoroughly documented and entirely absent from
the two artefacts that would make it operative. That is *defensible* today, because the
observe-only increment deliberately has no routing surface and a test enforces that. It becomes a
defect the moment a routing surface lands — and, with § 1 above, it means the threshold is
currently unreachable by any code path **and** the one gate that could use it cannot
discriminate.

---

## What this adds up to

Three separate findings, one shape: **the quantity the project is named for is not yet wired to
anything that acts on it.**

- The meter has never received a row of input (`morning-briefing-2026-08-20.md` § 2).
- The experiment that produces β cannot reach the meter that computes it (§ 2 above).
- The only gate that consumes β cannot be moved by it (§ 1 above).
- The threshold β is compared against exists in no executable form (§ 3 above).

None of this makes the thesis wrong. It makes the thesis **untested**, which is a different and
more fixable problem — and it is precisely what the pre-spec phase is for. Every one of these is
cheaper to fix now than after a routing surface exists.

**Recommended order, for Joe:** wire the meter's input first, because everything else is
downstream of having any β at all. Then fix Gate B2's condition, because a gate that cannot fail
is worse than no gate — it manufactures the appearance of a check.

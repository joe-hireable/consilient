# EXP-01 addendum — α is measured, and the `_bad` proxy is not one instrument

**Date:** 20 August 2026
**Instruments:** [`two_by_two.py`](two_by_two.py), [`alpha_sensitivity.py`](alpha_sensitivity.py),
[`proxy_diagnostics.py`](proxy_diagnostics.py)
**Status:** `[measured]` for the rates below; `[algebra]` for the β\* consequences, which are
one linear rescaling of an existing model.

This file **adds** a measurement. It does not amend `findings-exp01.md`, whose β estimates and
their audit corrections stand exactly as recorded.

---

## 1. What was wrong

`β* = (1 − α) · e^(−kΔ)` has two inputs. β had two mined estimates. **α had one value
anywhere in the repository — `α = 0.03`, in `capability_context_beta_star.py` line 47, and it
was invented.** [measured]

α is the flaky-verifier rate, `P(verifier rejects | artefact is good)`. It is named in
ADR-0002, ADR-0026 and twice in the specification, and never measured.

The reason it went unmeasured for so long is worth stating, because it is a reasoning error
rather than a data gap. **α and β are the two off-diagonal cells of one contingency table over
one set of mined records.** `mine_beta.py` filtered to `_ci == "green"` and computed one rate
over what survived. The rows it discarded as a nuisance are exactly the rows α needs. Nothing
had to be collected. The scarcity even inverts: β wants human *rejections*, which are scarce;
α wants human *accepts*, which any merge-mined corpus has in abundance.

## 2. The table, printed rather than remembered

`two_by_two.py` reads EXP-01's gitignored per-PR records and prints the whole contingency
table. It exists because this project has now made the same error twice — reading a
conditional off a remembered marginal — once in the document written to correct the first
occurrence. A tool that prints the table cannot make that mistake.

**`jobboard-v2`, 300 merged PRs** [measured]

|  | CI green | CI red | no CI | verifier ran |
|---|---|---|---|---|
| bad | 128 | 75 | 0 | 203 |
| good | 74 | 23 | 0 | 97 |

**`hireable-platform`, 56 merged PRs** [measured]

|  | CI green | CI red | no CI | verifier ran |
|---|---|---|---|---|
| bad | 18 | 3 | 1 | 21 |
| good | 24 | 4 | 6 | 28 |

## 3. α

| corpus | α = P(red \| good) | Wilson 95% |
|---|---|---|
| `jobboard-v2` | **23/97 = 0.2371** | [0.1635, 0.3307] |
| `hireable-platform` | **4/28 = 0.1429** | [0.0570, 0.3149] |
| `hireable-platform`, unrun checks counted as a miss | 10/34 = 0.2941 | [0.1683, 0.4617] |

**Every interval excludes 0.03, including the lowest bound of the weakest corpus (0.0570).**
The assumed value is not imprecise; it is outside the interval on both repositories and under
both treatments of unrun checks. [measured]

The two point estimates differ by a factor of 1.66, but their intervals overlap substantially,
so **these data do not establish that α differs between repositories.** They establish that it
is not 0.03. Anyone wanting a per-verifier α needs a larger sample per verifier, not this one.

### The `no CI` fork, named rather than buried

Seven `hireable-platform` PRs have no recorded checks: the verifier never ran, so it neither
accepted nor rejected. Two treatments are defensible and they answer different questions.

- **Exclude them** — "when the verifier ran, how often was it wrong?" This is the conditional
  the architecture uses, because β\* models a verifier's error rate. It is what the table above
  reports.
- **Count them as a miss** — "how often did nothing stop a bad artefact?" This is arguably
  what a practitioner wants. It gives α = 0.2941 and β = 18/22 = 0.8182.

`jobboard-v2` has no such rows, so its α and β are unaffected by the choice. `two_by_two.py`
prints both readings for any corpus that has them.

**This resolves a discrepancy rather than creating one.** The 20 August briefing quoted
`hireable-platform` β as 18/22 = 0.8182 — the *count-them* treatment — while the exclude-them
reading gives 18/21 = 0.8571. Both are correct; they were never labelled, so they looked like
a contradiction.

## 4. What it does to every threshold

β\* is linear in `(1 − α)`, so a wrong α rescales β\* by a constant at every capability gap.
`alpha_sensitivity.py` computes it: [algebra]

| α | β\* at Δ=0.17 | Δ=0.27 | Δ=0.42 | scale vs assumed |
|---|---|---|---|---|
| 0.03, assumed | 0.2490 | 0.1119 | 0.0337 | 1.0000 |
| **0.2371, `jobboard-v2`** | **0.1958** | **0.0880** | **0.0265** | **0.7865** |
| 0.1429, `hireable-platform` | 0.2200 | 0.0989 | 0.0298 | 0.8837 |
| 0.2941, unrun counted | 0.1812 | 0.0814 | 0.0245 | 0.7277 |

**Every threshold derived from β\* is roughly 21% looser than it should be on the stronger
corpus, and the error is in the optimistic direction** — the system believes its verifiers are
more reliable than they are. [algebra]

Propagating `jobboard-v2`'s Wilson interval on α gives β\*(0.27) in [0.0772, 0.0965]. The
whole interval sits below the assumed 0.1119.

## 5. What 0.327 is, and is not

`98/300 = 0.3267` circulated as a substitute for α. **It is not α.** It is
`P(CI red | merged)` — selected on the merge decision, not on artefact quality, and it mixes
the bad-and-red and good-and-red cells. It is listed in `alpha_sensitivity.py` only to show
that the *direction* of the error does not depend on which wrong quantity you reach for. It
must not be quoted as α.

## 6. What is still owed, and it is small

**The good-and-red cell — 23 PRs on `jobboard-v2` — is α's entire numerator and has never been
label-audited.** Every EXP-01 audit to date sampled the bad-and-green cell. α therefore
inherits exactly the label noise β does, from the same proxy: `_bad` means reverted or
hot-fixed within 14 days, and `good` means survived that window untouched. A "good" PR merged
over red CI might be one the checks correctly flagged and nobody got round to reverting.

The bad-and-red audit already commissioned covers 75 PRs. **Adding the 23 good-and-red PRs to
it audits α's numerator for a quarter more work, and completes the red column of the table.**
That is the recommended next step and it is cheaper than anything else outstanding.

Until it is done, α is `[measured]` **against the proxy labels**, exactly as β is, and the two
carry correlated noise because they come from one labelling pass.

## 7. The larger finding: `_bad` is not the same instrument in every cell

Running `proxy_diagnostics.py` on the same records produced something more consequential than
α. Two results, both `[measured]`, both on both corpora.

### 7.1 The strong signal never fired. Not once.

`mine_beta.py` labels a PR bad if it was **reverted**, or if it was **hot-fixed** — a later PR
merged within 14 days whose title matches `fix|hotfix|bug|regress|revert|broke|repair` and
whose changed files overlap.

| corpus | bad PRs | labelled by revert | labelled by hotfix |
|---|---|---|---|
| `jobboard-v2` | 203 | **0** | 203 |
| `hireable-platform` | 21 | **0** | 21 |

**Every `_bad` label in EXP-01 — all 224 across both repositories — comes from the weak
circumstantial proxy. The revert arm of the detector never fired on a single PR.**

A revert is a direct statement by the maintainer that the change was wrong. A hotfix match is
circumstantial: it infers a defect from a title regex plus a file-set intersection. β rests
entirely on the second, and the corpus contains no instance of the first.

There were two readings — the repositories genuinely never revert, or the detector is broken —
and a detector returning zero on 356 PRs deserves a positive control before it is trusted.

**The control was run rather than recommended.** [measured] Aggregate counts only:

| corpus | commits | subjects mentioning "revert" | of those, carrying a `#<PR>` reference |
|---|---|---|---|
| `jobboard-v2` | 1,511 | **2** (0.13%) | **0** |
| `hireable-platform` | 995 | **4** (0.40%) | **0** |

**The first reading is correct: these repositories essentially do not revert.** Six revert-ish
commits in 2,506, and not one references a PR number — which is the detector's primary match
path, the other being an 8-character merge-SHA prefix. So the zero is a true negative and the
instrument is not silently broken.

That is the more useful answer, and it is worse news than a bug would have been. **A bug could
be fixed. This says the strong signal does not exist in this corpus at all**, so β here is not
resting on the weak proxy by an implementation oversight — it has no alternative. Every future
β estimate mined from a fix-forward repository inherits the same constraint, and ADR-0013's
"evaluate on repository history" therefore buys a weaker label than it appears to. The audit
in §6 is not a refinement; it is the only check this design has.

### 7.2 The proxy's weakest cell is the one β leans hardest on

The hotfix rule's false-positive rate rises with the number of files a PR touches, because
overlap with some later "fix" gets easier the more files you have. A 100-file PR overlaps
almost anything.

| corpus | bad-and-green median files | bad-and-red median files | ratio |
|---|---|---|---|
| `jobboard-v2` | 5 (mean 9.4) | **13 (mean 26.7)** | **2.60** |
| `hireable-platform` | 2 (mean 8.7) | **6 (mean 22.3)** | **3.00** |

**The bad-and-red cell — 37% of β's denominator, and the cell no audit has ever examined — is
2.6× to 3.0× larger by file count than the bad-and-green cell that every audit did examine.
Same direction on both corpora.** [measured]

So the two cells are enriched for different populations, and the cell where the proxy is least
reliable is precisely the one whose labels were never checked. **The published β corrections
were measured on bad-and-green and propagated to a denominator that includes bad-and-red.**
The 20 August briefing already flagged that propagation as an assumption; this is the
mechanism that makes it a bad one, and it is measurable rather than merely arguable.

### 7.3 Which way it moves the answer

If `x` of the 75 bad-and-red PRs are false positives, they move to the good row. Then

- β = 128/(203 − x) **rises** — the checks look *worse*, not better;
- α = (23 + x)/(97 + x) **rises** — the verifiers look flakier;

and both move in the pessimistic direction. This is not a correction that would let the
project relax; the size bias predicts the audit makes both numbers worse. The good-and-red
cell (23 PRs, median 2 files) is the small-change cell, which is what genuine flaky or
lint-only failures ought to look like.

### 7.4 And the evidence needed to adjudicate it was thrown away

`mine_beta.py` fetched `statusCheckRollup` for every PR, collapsed it to `green`/`red`/`none`,
and **did not retain the check identities**. So "was this red meaningful, or was it a
lint-only job, a cancelled run, or flaky infrastructure?" cannot be answered from the stored
records at all. It needs a re-fetch from the API. [measured]

Per this programme's own rule, that gap is recorded rather than retrofitted: the records stay
as they are, and the instrument is what changes. `mine_beta.py` should retain the per-check
conclusion list. **It is not amended here** — EXP-01's recorded outputs must not be altered
under a live audit — and it is filed as the next instrument repair.

## 8. Reversal and falsifier

**Reversal:** `git revert` the commit carrying this file and the two scripts. Nothing else
changed; `findings-exp01.md` and `capability_context_beta_star.py` are untouched, so the
repository's existing β figures and the assumed α both still stand exactly where they were.

**Falsifier:** the good-and-red audit in §6 finds that a large share of those 23 PRs are
mislabelled `good` — they were genuinely defective and the red CI was correct. That moves them
into the bad row, lowering α and raising β simultaneously. If enough move, α could fall back
toward the assumed value and this finding's headline would be wrong. **The audit is the test,
and it has not been run.**

A second falsifier: if `_ci` conflates non-blocking or lint-only checks with correctness
checks, then "red" overcounts genuine rejections and α is inflated for a mechanical reason.
This is the same question the bad-and-red audit asks, applied to the other row.

# Crowd verdict supply for beta — specification, 23 August 2026

Commissioned as *design and build as a priority*. **It came back recommending against most of it**,
and the reasoning is this project's own evidence rather than caution:

- The gate it would feed **was retired the same day it was proposed**. ADR-0103 makes contract-beta
  the Gate A1 quantity and human-beta never-blocking, so crowd supply feeds a number with no
  consumer.
- **The binding constraint was never supply.** `projection.py` admits only `via == phone_webauthn`,
  `events.py` refuses that channel at append, and `scripts/verdict.py` hardcodes `cli`. A thousand
  strangers hit the same closed door the principal does.
- **There is no crowd.** 495 commits, one human author, and `CONTRIBUTORS.md` reads "None yet".

**What it does recommend is cheap and worth doing anyway**, because it repairs the closed door
whether or not a contributor ever arrives: signature-based identity via `ssh-keygen -Y`, with the
principal derived from the signature rather than declared by the caller — which is precisely the
hole ADR-0080 recorded. No credential custody, no new dependency, and a verdict a third party can
verify years later from a clone.

**And its sharpest observation is about itself.** Ten agents on one base model, and eight converged
independently on the same three mechanisms: *"That is shared training data, not consilience — the
exact correlation each of them recommended correcting for, occurring in the process that produced
the recommendation."* Nine angles asked how; one asked whether; the dissent is the best-evidenced
section and is 10% of the corpus by construction.

---

## Decision, 24 August 2026

**Joe chose option (a): build the signing subset only.**

What is built: `ssh-keygen -Y` signature identity, with a verdict's principal **derived from the
signature** rather than declared by the caller. That closes the hole ADR-0080 recorded, where a
local agent process can write a syntactically valid declared-principal verdict. It is worth doing
whether or not a contributor ever arrives, because the forgeable boundary exists today. Dispatched
as unit CB1.

What is NOT built, and should not be started without a new decision: WebAuthn relying-party
hosting, expertise verification, Dawid-Skene rater fusion, gold-item seeding, Sybil resistance, and
the contributor-facing probe surface. The specification argues against each of them at this stage
and the argument holds: the gate they would feed was retired the same day they were proposed, and
there is no crowd — 495 commits, one human author.

**The condition that would reopen this:** actual contributors. Not a release, not interest —
people submitting verdicts. Until then the remaining units are documented and unbuilt.

# Specification: `crowd_panel_beta` — a public verdict-supply channel that never gates

British English throughout. Every claim tagged `[measured]` (read from this tree), `[cited]` (published source), `[simulated]` (arithmetic I or another agent ran), `[asserted]` (judgement, no evidence).

---

## 1. Should this be built at all

**Mostly no. Build one afternoon of it, and not the part that was asked for.**

The critic is right and the evidence is this project's own:

- The gate this would feed was retired the same day it was proposed. ADR-0103 makes β_T the Gate A1 quantity and β_H "never blocking" `[measured]`. Crowd supply feeds a number with no consumer.
- The binding constraint is not supply. `projection.py:602` admits only `via == "phone_webauthn"`; `events.py` (V0-28) refuses that channel at append; `scripts/verdict.py:86` hardcodes `"via": "cli"` `[measured]`. Every verdict the principal can produce is dropped. A thousand strangers hit the same closed door.
- No sample size clears the threshold. β\* = 0.1119 with both inputs invented (ADR-0104); measured β̂ = 0.12 and 0.14; at true β ≥ 0.111 no n clears the bound, searched to 200,000 `[measured]`.
- Convergent validity already failed in-house: two oracles, one corpus, [0.81, 0.93] against 0.0 [0.0, 0.2039], non-overlapping `[measured]`. That is the signature of an under-specified construct, not of a missing third instrument (Cronbach & Meehl 1955) `[cited]`.
- There is no crowd. 495 commits, one human author, `CONTRIBUTORS.md`: "None yet", and an existing contributor doc that recruited nobody `[measured]`.

**The different class of facts.** A crowd verdict introduces *human judgement from someone with no stake in this repository's checks* — a fact class a second model cannot supply, because a second model shares training distribution with the first (Zhang, Liao & Bellamy, aligned error boundaries, arXiv:2001.02114) `[cited]`. That is genuinely worth having. It is worth having as **research data**, not as a gate input.

**Note on the input to this specification.** Ten research agents, one base model, one brief. Eight independently converged on Dawid–Skene, gold items and influence caps `[measured, from the research corpus]`. That is shared training data, not consilience — the exact correlation each of them recommended correcting for, occurring in the process that produced the recommendation. Nine angles asked *how*; one asked *whether*. The dissent is the strongest-evidenced section and 10% of the corpus by construction.

**Decision.** Build Units 1–6 (bug fix, signing, Tier-2 quarantine, ADR). Build Unit 7 (probe surface, public corpus only) only if the principal wants contributors for their own sake. Do not build WebAuthn relying-party hosting, expertise verification, Dawid–Skene fusion, or Sybil resistance — under the stated constraints (no credential custody, no principal spend) the last is closed, not hard `[asserted, from Douceur 2002` `[cited]``]`.

---

## 2. What a contributor does

A **probe**, not an artefact. One screen, no scrolling, no links, hard cap 2,000 characters.

```
PROBE p-3f9a2c    est. 40s

REQUIREMENT (verbatim, from the frozen contract)
  "Exit code must be non-zero when any check fails."

OBSERVED (executed, not diffed)
  checks: 3 run, 1 failed  ->  process exit code: 0

Q: Does the observed behaviour violate the requirement AS STATED?
   [y] yes   [n] no   [?] can't tell
   why (optional, <=140 chars): ______
```

Rules, each with its enforcement check (a chokepoint without one is not a chokepoint):

| Rule | Enforcement |
|---|---|
| Never a diff, never "is this good?" | Probe generator refuses any probe whose OBSERVED block is not an executed value or failing assertion; test asserts refusal |
| The rater is never shown what the checks said | `probe_digest` covers rendered bytes; a scan rejects any probe containing `verifier_accept` or check output |
| Rater judges the observation, not the requirement | Only three answers exist |
| >2,000 chars ⇒ not in this queue | Generator raises; test asserts |

Abstain (`?`) is first-class and is the highest-value output: ≥3 of 5 abstains emits `probe.unadjudicable` with the rendered bytes attached — a finding about the *generator*, not the rater `[asserted]`. Warrant for the format: judges shown selectively-revealed evidence reached 84% accuracy versus 74% for single-expert consultancy (Michael et al., arXiv:2311.08702) `[cited]`.

Transport is a git clone of `probes/*.jsonl`. No server, no hosting bill, no credential `[asserted]`.

---

## 3. Identity, without holding credentials

`ssh-keygen -Y sign -n consilient.verdict.v1` over `events.canonical(event)` minus the signature field; `ssh-keygen -Y verify -f allowed_signers` returns exit 0 on success `[cited, OpenSSH man page]`. Principal derived from `-Y find-principals`, **never declared by the caller** — that declaration is the hole ADR-0080 records `[measured]`.

Enrolment: contributor opens a PR adding one `allowed_signers` line; CI confirms the key via `GET /users/{u}/ssh_signing_keys`, public and unauthenticated `[measured]`; the merge commit timestamps the binding; `valid-after` pins the window. Third-party verification years later needs only the clone.

**The project must never hold:** a private key, an OAuth client secret, an SMTP credential, a phone number, a TLS key for an HTTPS origin, or any government-ID document. WebAuthn is rejected as the identity primitive: if we are the relying party, the key-to-person binding lives only in our database, so a third party must trust us — the failure being escaped `[cited, W3C WebAuthn L3]`. Delete the dead `phone_webauthn` branch rather than implement it.

**No new dependency.** `adopted-deps.json` is empty and tier-1 modules may import nothing outside stdlib `[measured]`; verification is `subprocess` to `ssh-keygen`, present on Windows 10 1809+, macOS and Linux. Pass `encoding="utf-8", errors="replace"`. Failed verification quarantines into the existing `rejections` table, which `state_digest` already covers `[measured]` — that is what makes ingest reproducible.

A signature proves a key signed. It does not prove a human read the screen `[asserted]`.

---

## 4. Expertise, without a gatekeeper

Do not verify it. Measure it, and only where measurement is possible.

Gold probes at **1 in 8**, indistinguishable from live ones, manufactured from the existing mutation machinery (40 of 40 injected faults killed, 23 Aug 2026) `[measured]`. Cold start: first 16 probes at 50% gold; weight 0 until ≥8 gold answered. Gold must be **label-uniform**, not distribution-matched — raters detect a skewed prior and answer it (Le et al. 2010, uniform arm 87.67% vs matched 85%, baseline 82.67%) `[cited]`. β's natural base rate is heavily skewed towards "no violation", so distribution-matched gold would train the corps to accept and measure the base rate instead of β `[asserted]`.

Declared credentials (ORCID, GitHub age) set routing only. Never weight.

**Two honest limits.** Gold requires a known past answer, which at launch exists only in coding — outside coding the first ~100 probes per domain are calibration, not measurement, and must be labelled so `[asserted]`. And inference of competence from agreement structure is not identifiable: high agreement is equally generated by accurate independents, by copying, and by a shared misleading input — this repository's own `formalising-echo-2026-08-20.md` records exactly that `[measured]`. Agreement never establishes competence; gold does, or nothing does.

---

## 5. The estimator

**Model:** Dawid & Skene (1979), latent-class EM over per-rater confusion matrices; β read off as `π_verifier[bad, good]` with the automated verifier entered as one more annotator `[cited; recovery to within 0.03 of truth at ≥2 human raters,` `[simulated]``]`.

**Assumptions, stated because they are what fails:** raters conditionally independent given the true label; stationary per-rater error; item difficulty homogeneous.

**Minimum raters per item: 2 humans** (the verifier is the third view; three conditionally independent views is the identifiability floor, Allman/Matias/Rhodes 2009) `[cited]`. One rater is not merely imprecise but confidently wrong: 0.050 against a truth of 0.200 `[simulated]`.

**Badness as probability.** β is a posterior over a confusion-matrix cell, reported as a credible interval. Do **not** aggregate labels then divide: the plug-in limit is `[β·π·Se + α·(1−π)·FPR] / [π·Se + (1−π)·FPR]`, biased upward by up to 2.2× `[simulated]`. Do **not** soft-weight by the posterior — that was worse than majority vote in all eight configurations tested (0.233–0.667 against 0.200) `[simulated]`.

**Disagreement is an output.** Publish contested-share (posterior p_bad ∈ [0.2, 0.8]) and Krippendorff's α per domain, and refuse to report where α < 0.667 `[cited, Krippendorff's own threshold]`. Expect low agreement: single expert evaluators find 20–51% of known defects (Nielsen & Molich, CHI '90) `[cited]`; journal peer review pools at κ = .17 `[cited, Bornmann et al. 2010]`.

**The correlation that matters is rater↔verifier, not rater↔rater.** If human blind spots overlap the checks' blind spots, H fails to reject exactly where A wrongly accepts, and β is biased **downward** — the flattering direction, uncaught. Unanimity-of-3 makes this worse by selecting for unanimous shared blind spots `[asserted]`. The only proposed test (double-fault rate on gold) needs ground truth, which is the thing absent outside coding. **This is circular and unresolved.**

**Therefore: do not build the estimator now.** Ship majority-of-2-after-abstain — no aggregator dominates and MV is competitive (SQUARE, HCOMP 2013) `[cited]` — record every raw signed verdict, and fit anything else retrospectively when ≥50 raters × ≥20 items exist. Fitting a latent-variable model to data that cannot identify it is the expensive mistake.

---

## 6. Poisoning, and what detects it

Ordered by expected harm.

**1. Selection (highest harm, ~£0, undetectable).** The checks are open source. Clone, run locally, learn `verifier_accept`, then reject **only** artefacts the checks already rejected. Every verdict enters the denominator, none the numerator; β → 0 monotonically. Gold scores 100%. Dawid–Skene rates the attacker as the best rater. Blinding is void because the oracle is public. Leave-one-out shows nothing — every verdict is individually correct. **Nothing in any proposed design detects this.**

**2. Declining (zero cost, zero expertise, no key).** Assigned an artefact the checks wrongly accepted, say nothing. Timeout. No artefact, no signature, no row. Rogan–Gladen `[cited]` converts the loss into a wider interval via seeded-defect sensitivity; it never names the liar. Its exchangeability assumption (seeded defects as hard to find as real ones) is validated for code mutants only (Just et al., FSE 2014, 73% of cases) `[cited]` and nowhere else. And gold indistinguishability is itself attackable — colluding workers identify gold items (Checco et al., HCOMP 2018) `[cited]`. **Bounded, not detected.**

**3. Fabrication (loud, ~£15).** 136 rows declared `--checks fail` drag a published upper bound under 0.10 `[simulated, using this repo's own `wilson()`]`. Detected by binding `verifier_accept` to a runner-appended `attempt.check` event rather than a caller flag. Nobody would use this attack when attack 1 exists.

**4. Sybil.** Free accounts; without a trusted certifying authority, identity-counting defences always fail (Douceur 2002) `[cited]`. Unsolvable under "no credential custody, no principal spend" — both a price and an identity anchor are forbidden `[asserted]`.

**Conclusion: no crowd-derived number may gate anything.** This is the single reason for Unit 5.

---

## 7. Privacy

**Lawful basis.** Rating is a *new purpose*. UK GDPR Article 8A (inserted by DUAA 2025, in force 5 Feb 2026) requires fresh consent where the original basis was consent; Annex 2 does not cover it `[cited, legislation.gov.uk]`. Article 14(5)(b) was omitted 5 Feb 2026 `[cited]`, so third parties named inside an artefact (a client in a fixture, a colleague in a commit trailer) are owed a notification that cannot be delivered — there is no lawful route to disclosing third-party personal data you never needed.

**Minimum sufficient view.** A domain is reviewable-under-minimisation *iff its contract is separable from its content* `[asserted]`. Code, config and data analysis pass. Prose and design fail — their MSV is approximately the whole artefact.

**Default: public and project-owned artefacts only. No user artefact enters the probe corpus, at all, in this specification.**

**The scenario that ends the project.** A contributor reviews a packet from a real user's private repository containing a client's name or regulated data, and posts it. Not a rule breach — a headline.

**Does the default prevent it? Yes, and only this default does.** Per-artefact opt-in prevents the default case, not the first exception, and this project's automated gates have a **measured false negative on exactly this class**: on 21 Aug 2026 `check_private_corpus.py` (2,854 paths) and `check_secrets.py --history` both PASSED on a diff carrying 71 foreign commit SHAs from a private commercial repository; a human audit caught it `[measured]`. The price of the safe default is honest and large: β measured on public artefacts excludes every artefact anyone had a reason not to publish `[asserted]`.

Erasure against an append-only log after publication is **undesigned**.

---

## 8. Domains

**1. Coding.** The only domain with a runnable check suite today, an automatic oracle for gold, and an existing harness. Start and possibly finish here.

**2. Research-summary grounding.** Checks are exact (every reference resolves; every quoted string appears verbatim; every number appears in the source), sources are public so privacy is solved outright, and **this repository already runs the protocol on itself** — `bibliography.md`'s [FULL]/[ABS]/[SNIP] ladder *is* the check suite `[measured]`. Free dogfooding.

**3. Accessibility conformance.** Chosen *because* the checker is known incomplete, so β is expected large and therefore informative; the human oracle (a screen-reader user) is genuinely different-class from a rule engine; expertise is register-verifiable (IAAP) `[asserted]`.

**Where β is simply undefined:** strategy memos, email, general prose, aesthetic design quality, whether a plan is a *good* plan. No runnable pre-human check suite exists, so there is nothing for an acceptance to be an acceptance *of*. A thousand verified experts produce a valuable dataset and **zero β**. This must appear on the face of any output, not in a footnote. ADR-0101's gap narrows; it does not close `[asserted]`.

Legal is deferred despite having the best expertise register on earth: worst privacy posture, and a check suite so narrow (citation existence) that experts would reject for reasons the checks never attempted, driving β towards 1 and telling you nothing `[asserted]`.

---

## 9. Incentives

**No points, no badges, no leaderboard, no streaks.** Threshold badges provably steer *which action* a user takes: activity on the badged action rises sharply before the threshold and "almost immediately returns to near-baseline levels" after, with measured substitution away from unbadged actions (Anderson, Huttenlocher, Kleinberg & Leskovec, WWW 2013, several million Stack Overflow users) `[cited]`. β is a rate over judgement acts. A mechanism that reallocates the judgement mix and then withdraws effort at a threshold corrupts the instrument directly, not incidentally.

Tangible expected rewards undermine free-choice intrinsic motivation (d = −0.28 to −0.40); positive informational feedback enhances it (d = +0.33) (Deci, Koestner & Ryan 1999, 128 experiments) `[cited]`. So: feedback, never score.

What a professional gets, none of it insulting:

- **Named, citable credit.** `CITATION.cff` naming contributors whose verdicts entered any published figure, CRediT role `Validation` (ANSI/NISO Z39.104-2022, CC BY 4.0) `[cited]`. Precedent: Foldit player groups appear in the author line of *Nat. Struct. Mol. Biol.* 18(10):1175 `[cited]`.
- **Informational feedback per closed probe:** your answer, the consensus, the disagreement.
- **Peer commendations** — signed, discretionary, unrankable. A single barnstar raised 90-day Wikipedia productivity ~60% in a 200-editor RCT (z = 3.222, p = 0.001) `[cited]`.
- **One honest line:** "your verdicts moved published `crowd_panel_beta` for coding from X to Y."

Permitted progress reporting: "coding needs 4 more rejections before this figure can be published" — a genuine threshold, not a manufactured one. That is the bright line.

**No money.** Never per-verdict: an explicit price displaces a norm and the displacement does not revert (Gneezy & Rustichini 2000) `[cited]`. If money ever enters, only as a payment the contributor may redirect to charity — that framing fully counteracted crowding-out (Mellström & Johannesson 2008) `[cited]`.

---

## 10. Build units

No two units claim the same file. Order puts identity and the never-gates quarantine before any collection surface.

**U1 — ADR-0105.** Deliverable: the decision record for §1, §3, §6, §7. Done: file exists, carries an "Evidence against" section quoting the critic's selection attack and the convergent-validity failure verbatim, and every claim carries a tag. Files: `docs/decisions/0105-crowd-verdicts-are-tier-2-and-never-gate.md`. Depends: none.

**U2 — Signature verifier.** Deliverable: `verify(event) -> (ok, principal)` shelling to `ssh-keygen -Y verify` / `-Y find-principals`, stdlib + `subprocess` only, `encoding="utf-8", errors="replace"`. Done: one runnable test generates a throwaway keypair, verifies a signed payload, and asserts a one-byte tamper fails. Files: `src/consilient/attest.py`, `tests/test_attest.py`, `config/allowed_signers`. Depends: U1.

**U3 — Append accepts signed verdicts.** Deliverable: `_check_human_authority` accepts `via == "ssh_sig"` when `attest.verify` returns ok; principal derived, never declared; failures land in `rejections`. Done: `consil beta --json` shows `n_rejected >= 1` with `auth_status == "authenticated"` — verified by artefact, not exit code. Files: `src/consilient/events.py`. Depends: U2.

**U4 — Projection admits it.** Deliverable: `_verdict_auth_status` maps `ssh_sig` → `authenticated`; the `phone_webauthn` branch is deleted. Done: a test asserts a verdict produced by the shipped tool reaches `outcomes.human_verdict` — this test fails today `[measured]`. Files: `src/consilient/projection.py`. Depends: U3.

**U5 — Quarantine the estimand.** Deliverable: `"crowd_panel_beta"` added to `PROXY_ESTIMAND_KINDS`, so `admits_human_beta_row` refuses every crowd row by construction. Done: a test asserts a crowd row cannot enter `compute()` and cannot close a gate. Files: `src/consilient/beta.py`. Depends: U1.

**U6 — Verdict tool signs.** Deliverable: `--sign` flag; `via` no longer hardcoded. Done: a verdict produced by this tool passes U2's verifier and appears in U4's projection. Files: `scripts/verdict.py`. Depends: U4.

**U7 — Absolute-path scan.** Deliverable: the fourth redaction check the consent design names and does not have. Done: refuses on a `C:\Users\…`-shaped string; mutation test flips it. Files: `scripts/check_absolute_paths.py`. Depends: U1.

**U8 — Rater undertaking.** Deliverable: ICLA-pattern click-through: no retention of probe bytes, no republication, no re-identification, notify on discovering personal data. Done: file exists and is linked from the enrolment PR template. Files: `docs/legal/rater-undertaking.md`. Depends: U1.

**U9 — Probe surface (optional; build only if contributors are wanted for their own sake).** Deliverable: generator + `consil rate` over local JSONL; hard refusal on any artefact not public or project-owned; 2,000-char cap; abstain; gold at 1-in-8; dwell timing. Done: run solo on 100 self-generated probes and report probe precision **before recruiting anyone**. Files: `scripts/probe.py`, `probes/`. Depends: U6, U7, U8.

**Not built:** WebAuthn relying party, Dawid–Skene fusion, Sybil resistance, expertise credentialing, viewer-side controls. Add when — and only when — ≥50 raters × ≥20 items exist and a gate quantity genuinely consumes the output.

Cost model, so the recruitment target is derived rather than hoped: 40 s × 2 raters × (30 / probe_precision). At precision 0.30, ~5.5 rater-hours; at 0.05, ~33 `[simulated]`. **Probe precision, not rater supply, is the binding constraint**, and U9's solo run measures it with zero contributors.

---

## 11. What this does not solve

- **The selection attack (critic §1) is undetected by every mechanism here.** Open-source checks mean the oracle is readable; a rater who rejects only what the checks already rejected drives β to zero while scoring perfectly on gold. This is the reason for U5, not a residual risk `[asserted]`.
- **The declining attack leaves no artefact.** Bounded by seeded sensitivity, never identified `[asserted]`.
- **Rater↔verifier correlation biases β downward and its only test is circular** (needs gold, which needs the ground truth that is absent outside coding) `[asserted]`.
- **This is not the same β.** Different rater, different aggregation, different artefact population; ADR-0103 already renamed β_H to alignment-with-the-principal `[measured]`. Comparison with the existing rejection, the retro-verifier estimate, and β\* is void. Hence the name `crowd_panel_beta`.
- **The gate is untouched.** Replacing the instrument is the third attempt; replacing the *quantity* — bounded reversibility, oracle = byte equality on a start-state digest the system did not choose, one counterexample fails it — is the alternative this specification does not build and recommends the principal consider instead `[asserted]`. Its own cost: a smaller claim ("our mistakes are bounded", not "our checks are good"), and `external_exposure` is irreversible by construction `[measured, events.py:108]`, so it certifies the classes with least consequence.
- **Erasure against an append-only log after publication is undesigned.**
- **Contributors may not exist.** 495 commits, zero external `[measured]`. U9 is the cheapest possible test of that and should be run before anything is announced.
- **Citation debt.** Dawid & Skene 1979, GLAD, MACE, Krippendorff's thresholds, Douceur and Cronbach & Meehl are cited from the research corpus, several of which recorded exhausted search budgets and cited from memory `[measured, from the corpus]`. None may appear in an ADR's `[cited]` line until fetched.

*~3,400 words.*

---

## Hostile review

## 1. Cheapest attack, end to end

- **Not fabrication — selection.** The checks are open source. Attacker clones, runs them locally, learns `verifier_accept` per item. Then rejects **only artefacts the checks already rejected**. Every such verdict lands in β's denominator, none in the numerator. β → 0 monotonically. Cost: one local test run per item, ~£0.
- This defeats every proposed defence simultaneously: gold items score 100% (they're answered honestly), Dawid–Skene rates the attacker as the *best* rater (perfect agreement with truth), the influence cap only slows it, blinding is void because the oracle is public, and leave-one-out shows nothing because the attacker's verdicts are all individually correct.
- **The declining attack is worse and cheaper still.** Assigned a bad artefact the checks accepted, say nothing. Timeout. No artefact, no signature, no row. Cost: zero, no expertise, no key. Detection requires seeded gold that is (a) indistinguishable and (b) hard — Checco 2018 shows colluding raters identify gold. Rogan–Gladen widens the interval; it never names the liar.
- Fabricating `--checks fail` rows (~£15 for 136) is the *loud* attack. Nobody would use it.

## 2. Where the design trusts people, not mechanisms

Blinding (raters must not run the public checks) · gold indistinguishability · no out-of-band coordination — commit/reveal stops in-band anchoring and nothing else · one key per human · vouchers vouching carefully (single root, unbounded subtree) · packet non-retention after review · dwell time (self-reported by a client the contributor compiled) · consent honoured downstream. Every one is a norm with a cryptographic costume.

## 3. Correlated raters

- Dawid–Skene, GLAD, MACE all assume conditional independence given the true label. Correlation doesn't add noise — it **shrinks the interval around a wrong value**. Confidently wrong is the worst failure mode for a gate.
- The fatal correlation isn't rater↔rater, it's **rater↔verifier**. β = P(A | H). If H's blind spots overlap A's — same conventions, same idioms, same training — then H fails to reject exactly where A wrongly accepts, and β is biased **downward**. Flattering direction. Nobody catches it.
- Unanimity-of-3 makes this *worse*: it selects for the cases where the shared blind spot is unanimous.
- The only proposed test (double-fault rate on gold) needs gold, which needs ground truth, which is the thing that doesn't exist outside coding. Circular.

## 4. Privacy: the ending scenario

- A contributor reviews one packet from a real user's private repo containing a client's name / regulated data, and posts it. Project over — not because of a rule, because of a headline.
- **The default does not prevent it.** Per-artefact opt-in prevents the *default*, not the *first exception*, and this project's automated gates have a **measured false negative on exactly this class** (21 Aug: 71 foreign commit SHAs, `check_private_corpus.py` + `check_secrets.py --history` both PASSED). Public-corpus-only (Lane A) genuinely prevents it — and measures a population that excludes every artefact anyone had a reason not to publish.
- Erasure against an append-only log after β has been published: undesigned in all ten.

## 5. Is it the same β?

**No, and nobody said so.** Different rater (one principal → panel of strangers), different estimand (ADR-0103 explicitly renamed β_H to *alignment with the principal*), different artefact population (opted-in/public, not the exposure stream), different aggregation (single verdict → unanimity-after-abstain). β\* = 0.1119 was invented against neither. Comparison with the one existing rejection, with the retro-verifier estimate, and with the threshold is **void**. Call it `crowd_panel_beta` or the record becomes non-comparable by construction.

## 6. Third instrument, two falsified

- Lakatos: degenerating problemshift. Measurement theory: convergent-validity failure. The project already ran the test — two oracles, one corpus, **[0.81, 0.93] vs 0.0 [0.0, 0.2039]**, non-overlapping. The inference is that the construct is under-specified, not that a third instrument is needed.
- Tell him: **stop.** Fix the three-line verdict-channel bug (worth it regardless). Then replace the gate quantity, not the instrument. Gate on **bounded reversibility** — forward-then-inverse restores the declared start-state digest, K trials per effect class, zero escaped protected effects. Oracle is byte equality: unreadable, unwritable, no crowd, no threshold, no privacy surface, one counterexample fails it. Smaller claim ("our mistakes are bounded", not "our checks are good") and the only one currently evidenceable.

## 7. What all ten missed

- **They are correlated raters.** One base model, one brief, ten prompts. Eight independently "converge" on Dawid–Skene, Douceur, gold items, influence caps. That is shared training data wearing consilience as a costume — the exact failure they each recommend correcting for, occurring in the process that produced the recommendation.
- **The brief presupposed the answer.** Nine angles ask *how to build it*; one asks *whether*. The negative case is 10% of the corpus by construction, so the aggregate reads as consensus even though the dissent is the strongest-evidenced section.
- **None costed the principal's attention** — the stated bottleneck. Ten designs, ten ADRs, one reviewer.
- **None checked whether contributors exist.** 495 commits, one author, `CONTRIBUTORS.md`: "None yet", and an existing recruitment doc that drew nobody. One agent found this; nine designed for a crowd.
- **Several admit exhausted search budgets and cite from memory anyway** — then build recommendations on those citations.
- **None proposed not measuring β.**

# Specification-set correctness audit — 22 August 2026

- **Auditor:** dispatch `20260822T135600-db5bc7d48c` (cursor-composer), a different model family
  from the Codex authors, verifying by execution rather than by reading for plausibility.
- **Stamp:** run 2026-08-22T13:56Z–14:05Z. Report written against the working tree at
  2026-08-22T14:04Z.
- **Scope as found on disk, not as briefed:** the brief says "thirteen specifications, twelve
  ADRs and four research documents". The tree holds **eleven** specs dated 2026-08-22 under
  `docs/superpowers/specs/`, **thirteen** ADRs written today (`0067`, `0068`, `0070`–`0080`;
  `0069` does not exist anywhere), and the four research documents in `docs/00-context/`.
  Twenty-eight documents audited. Still in flight at finish time and **not** audited: the
  consilience-gate spec and ADR-0081 (claim `20260822T135325-cecc1df0a3`), and
  `docs/00-context/subscription-reach-2026-08-22.md` (claim `20260822T134953-04998632ab`,
  expired 14:54Z with nothing on disk). The verdict-supply spec and ADR-0080 landed during the
  run and **are** included.

## Sampling method (stated, per the brief)

- **`[measured]` claims (381 tags extracted):** verified *exhaustively* where a check exists:
  every claim bearing an explicit `file:line` locator, every claim about `consil` CLI output
  (reproduced live), every EXP-id reference in today's ADRs (21 distinct ids, each checked for a
  register heading), every uniqueness claim (exhaustive grep for single/sole/only +
  writer/boundary/orchestrator/selector), and every V0-18 framing (exhaustive grep). Prose
  `[measured]` claims without locators were spot-checked across six documents.
- **`[cited]` claims (336 tags, 240 unique URLs):** retrievability checked *exhaustively* —
  every URL fetched (scripted, browser-agent headers, redirects followed). Content checked by
  stratified sample: load-bearing empirical citations got full text retrieval and figure
  comparison; the remainder carry retrievability status only.
- **ADR cross-references:** exhaustive for EXP nominations, amendment claims, numbering and
  index coverage. Contradiction pairs from the brief were read in full, plus pairs found by the
  uniqueness-claim sweep.
- **Gate state:** `python -m pytest tests/ -q` run in full; `consil doctor` and
  `consil beta --json` run live.

## Verdict

**Not yet fit to build from.** Five confirmed defects (D1–D5) block, all cheap to repair:
three experiment ids claim registration that does not exist, five of today's ADRs have no index
row, and one shipped executable model fails its own self-check. The full test suite is red
(7 failed, 890 passed, 1 skipped against a claimed 891-passing baseline). **Everything else
sampled was good** — every code-locator `[measured]` claim reproduced, both live CLI outputs
matched their quotations to the field, and the one content-checked citation matched its source
exactly. The set's evidence discipline is real; the failures are concentrated exactly where the
brief predicted: concurrent authors who could not see each other, and registration claims
written before the registration happened.

## CONFIRMED defects (verified against the artefact)

### D1 — False `[measured]`: "pre-registered as EXP-118" — EXP-118 does not exist (high)

- **File/line:** `docs/00-context/hermes-teardown-2026-08-22.md:288-289`.
- **Claim:** "The comparison is pre-registered as **EXP-118** in
  `docs/10-research/experiment-register.md`. [measured]"
- **Check:** repo-wide search for `EXP-118` (all tracked and untracked content). The string
  occurs only inside `hermes-teardown-2026-08-22.md` itself. The register has no heading and no
  mention. Worse, the same paragraph (lines 291-292) admits the searches "found no prior
  `EXP-118`" — i.e. the id was verified *free* and never registered, so the document contradicts
  itself within four lines.
- **Should say:** "The comparison is proposed here as EXP-118; no register entry exists yet."
  (The pattern was available: `product-bar-2026-08-22.md:238-244` frames the identical situation
  honestly — "Proposed pre-registration; no register change made" — for EXP-100.)

### D2 — ADR-0080's killing experiment EXP-105 is not registered (high)

- **File/line:** `docs/decisions/0080-keep-consequence-signals-out-of-human-beta.md:3,9,99,209`
  ("T3 pre-registered as EXP-105, not run"; "EXP-105 is the killing experiment").
- **Check:** register search — zero `### EXP-105` headings; one prose mention at
  `experiment-register.md:4256-4257`, inside EXP-106's entry, which records that "EXP-104 and
  EXP-105 had been allocated concurrently outside the register". The register itself documents
  the collision; the entries were never written.
- **Consequence:** fails the shipped invariant
  `tests/test_v0_invariants.py::test_provisional_adrs_name_a_live_experiment` (run today:
  FAIL, naming this ADR). Working principle 11 makes this the failure mode that test exists to
  stop.

### D3 — ADR-0076's nominated EXP-104 is not registered (high)

- **File/line:** `docs/decisions/0076-owner-gates-persistent-self-change-and-the-instrument-is-sealed.md`
  (nominates EXP-104; named by the failing invariant test).
- **Check:** as D2 — no heading, one prose mention at `experiment-register.md:4256`.
- **Consequence:** same failing test, same principle-11 violation.

### D4 — Index omits five of today's ADRs (high)

- **File/line:** `docs/decisions/index.md` — no rows for **0070, 0072, 0078, 0079, 0080**.
  (The brief named three; the shipped test finds the same five I found manually.)
- **Check:** `python -m pytest tests/test_adr_trail.py::test_trail_integrity_runs_on_the_real_tree`
  fails listing exactly those five "no row in index.md". Manual link-pattern count agrees.
- **Consequence:** the amendment trail is invisible at the index: 0079 explicitly amends 0078,
  and 0077 corrects 0051/0067 — but a reader of the index cannot discover 0078 or 0079 exist.
  The index is the load-bearing navigation artefact for the decision record; a fifth of today's
  decisions are missing from it.

### D5 — ADR-0068's executable model fails its own self-check (high)

- **File/line:** `docs/decisions/0068-model.py:205` (self-check), branch logic at lines 130-142.
- **Check:** `python docs/decisions/0068-model.py` → `AssertionError` at line 205. Today's new
  `tests/test_decision_models.py::test_executable_decision_models` fails on the same assertion.
- **Defect:** branch ordering. With `joint_gain_over_matched_single = 0.0` (the matched control
  is not beaten at all), `beats_matched` is false, so the earlier branch
  `if beats_operational and not beats_matched: return CUT_AS_COMPUTE` fires first — the model
  classifies the observation `CUT_AS_COMPUTE` where its own self-check requires `CUT_OVERHEAD`.
  The regimes feed EXP-98's stopping rule, so the misclassification is decision-relevant, not
  cosmetic. The model was committed failing. (`0067-model.py` passes: "ADR-0067 regime
  boundaries pass".)
- **Should do:** reorder so the matched-control failure (`gain <= 0` or review ratio over
  ceiling) is tested before the `CUT_AS_COMPUTE` branch, or narrow that branch — whichever the
  author intends; the self-check and the code must agree before EXP-98 may use this classifier.

### D6 — Repository gates red on the working tree (medium; causes identified)

- **Check:** `python -m pytest tests/ -q` → **7 failed, 890 passed, 1 skipped** (52 s). The
  brief's baseline was 891 passing. The seven:
  1. `test_provisional_adrs_name_a_live_experiment` — D2/D3 plus older ADRs 0056 (EXP-94), 0059
     (no experiment), 0060 (EXP-95). Note: this test was *tightened today* (uncommitted) from
     "mentioned in register text" to "has a `### EXP-nn` heading"; EXP-94/95/104/105 all appear
     in register prose but have no headings. The older three ADRs pass at HEAD's weaker test and
     fail the tightened one.
  2. `test_adr_trail.py::test_trail_integrity_runs_on_the_real_tree` — D4.
  3. `test_decision_models.py::test_executable_decision_models` — D5.
  4. `test_no_new_event_may_bypass_append` — 95 bypassing events against a ceiling of 92. The
     uncommitted `src/consilient/events.py` changes (+49 lines) added three. In-flight code work,
     not a spec defect, but it directly contradicts the "single writer" property several of
     today's specs assert as current fact.
  5-6. `test_foreign_commit_identifiers_may_only_decrease` and
     `test_foreign_identifier_gate_can_pass_and_still_refuses_the_unknown` — one un-allowlisted
     identifier: a **public** GitHub permalink pinning `ruvnet/ruflo` at a revision, added in
     today's uncommitted `docs/10-research/bibliography.md` edit (line 54). Benign in kind —
     exactly the "public upstream permalink" category the test docstring calls ordinary
     provenance — but the allowlist ritual (test against both private corpora, record reason)
     was not done, so the gate is red. Not a private-corpus leak.
  7. `test_historical_refusal_digests_pin_real_log_rejections` — digests drifted against the
     live log (related to the same in-flight trajectory changes; not further isolated).

### D7 — ADR-0071 treats V0-18 as a trust boundary (medium)

- **File/line:** `docs/decisions/0071-commit-to-a-delivery-window-and-prove-liveness-with-sealed-checkpoints.md:166-167`.
- **Claim:** "Only the principal may later author the human `attempt.verdict` … through the
  trusted first-party path enforced by V0-18 and V0-28. [measured]"
- **Check:** `src/consilient/events.py:957-978` checks `actor == principal` and
  `via == "cli"` — declared provenance, and the code's own comment says "this build has no
  signature verifier (V0-28)". `scripts/verdict.py:116` takes `--principal` from the caller.
  Nothing is authenticated, so nothing is "enforced" as first-party. Today's other documents
  state this correctly (`0076:167` "not treated as authentication"; `0080:35-39`; hermes
  teardown line 228 "declaration consistency, not authenticated"). 0071 is the outlier and is
  the overclaim the brief predicted.
- **Should say:** "through the declared-provenance check V0-18/V0-28 currently apply — a
  consistency check, not authentication (V0-28)."

### D8 — The corrected `n_max` claim persists uncorrected in the organisation bar (low)

- **File/line:** `docs/00-context/agentic-organisation-bar-2026-08-22.md:129-130` —
  "`n_max=1` for `epsilon <= 0.40`".
- **Check:** ADR-0077 corrected this to `n_max <= 1` because `epsilon < beta_upper` admits zero
  attempts. Verified numerically: at ε = 0.29, β = 0.3346, `floor(ln(0.71)/ln(0.6654)) = 0`.
  ADR-0051 carries an explicit update notice recording the correction (uncommitted edit, proper
  append-style supersession — good practice); the research doc does not. Note the audit brief
  itself repeats the pre-correction form in its constraint 2 ("gives **1** … for any exposure
  ceiling <= 0.40") — the correction has not propagated.

### D9 — Brief's document counts do not match the tree (low; recorded for the record)

- "Thirteen specifications, twelve ADRs" vs eleven specs and thirteen ADRs on disk; ADR-0069
  has never existed (numbering gap 0068 → 0070). No document claims 0069 exists, so this is a
  brief inaccuracy, not a set defect — recorded so the count discrepancy is not later read as
  missing files.

## SUSPECTED — could not confirm or refute with the available checks

- **S1 — Two homes for "the single admission boundary".**
  `2026-08-22-autonomy-and-friction.md:303` extends `scripts/dispatch.py` "with the single
  action/escalation admission and principal-rendering boundary";
  `2026-08-22-decision-protocol.md:92` puts "the general chokepoint … inside ADR-0078's single
  effect boundary". These may compose (dispatch hosting 0078's boundary; action vs effect tiers),
  but no document states the relationship, the vocabularies differ, and the two specs were
  written by agents that could not see each other. Reads as one chokepoint claimed for two
  locations. Needs one sentence in either spec naming the other.
- **S2 — ADR-0080:107 compresses `Beta.compute()`.** "Admits only records with
  `human_verdict='reject'`" — the code (`src/consilient/beta.py:181,200`) admits rows with
  accept *or* reject and counts rejects for the numerator. Semantics preserved, phrasing
  imprecise; a strict reader could implement admission wrongly from the ADR alone.
- **S3 — 38 of 240 cited URLs unverifiable by scripted fetch** (35×403, 2×429, 1×203):
  `help.openai.com` (9), `doi.org` publisher bot-blocks (8), `help.clickup.com` (7),
  `www.sec.gov` (5), `openai.com` (5), `devin.ai` (2 + 2 rate-limited), `www.microsoft.com` (1),
  `pubmed.ncbi.nlm.nih.gov` (1, HTTP 203). None returned 404; all are plausibly bot-protection
  rather than dead links, but per the brief's rule an unverified tag is reported. Content behind
  these was not confirmed.

## Verified clean — the checks that passed

- **ADR-0077's amendment claims are accurate.** ADR-0051 decision 5 exists and says what 0077
  characterises (`0051:355-356`: positive correlation "makes the identity an upper bound");
  ADR-0067's "Composition and beta" clause exists (`0067:98`) and carries the corrected
  `n_max = 1` claim (`0067:118-120`). 0077's algebra is correct (D8's counterexample verifies
  it). 0051's uncommitted update notice records the supersession properly; the index records
  both 0077 corrections.
- **ADR-0080's code claims all reproduce.** `consil beta --json` live: `n_rejected=1`,
  `n_false_accept=1`, `quarantined=6`, `insufficient_data` — field-for-field as quoted at
  0080:104-106. `verdict.py` caller-chosen `--principal` (line 116). `beta.from_connection`
  accepts `sampling_unconditioned` (line 238) and drops it in the `compute` call (line 253) —
  exactly as 0080:110 claims.
- **`events.py:957-978`** enforces `actor == principal` and `via == "cli"` and its own comments
  disclaim authentication (V0-28) — as the brief stated.
- **decision-protocol:79**: `REVERSAL_KINDS = {revert, command, inverse}` (three typed shapes),
  legacy `USER_ONLY` rejected (`events.py:50,52,884`). Locators in action-surface
  (`dispatch.py:638-654` = `git_diff_bytes` over `diff --stat`; `budget.py:1-5` = refuse-only
  docstring, no provider capability) accurate.
- **EXP-45's ~59%**: findings file records 59.3% dropped (40.71% mean retention).
- **EXP-100 framing in product-bar is honest** ("Proposed pre-registration; no register change
  made", id verified free by search) — the correct pattern D1/D2/D3 departed from.
- **Citation content check**: bibliography's self-play-judge figures (judge acceptance
  0.716 → 0.938±0.016, hidden accuracy 0.209 → 0.202±0.005, GSM8K/Qwen3-4B) match the source
  paper (arXiv:2607.05904) exactly.
- **No duplicate ADR numbers** (0067/0068 pairs are the ADR plus its `-model.py` companion, a
  deliberate pairing). **No TBD/placeholder markers** in any of the 28 documents. **No V0-18
  overclaim** outside D7. **`consil doctor` quotations** in today's docs (Gates A and B FAIL,
  routing disabled) match live output; A2 passes in this worktree (494 events compared).
- **0078/0079 compose**: 0078:78 requires decision identity in every `effect.intent`; 0079:76-77
  explicitly amends that to admit pure observations with `decision_id: null`, without exempting
  reads from the boundary. The amendment is scoped and recorded — but see D4: the pair is
  invisible in the index.
- **0067's one-Owner boundary holds** across the decomposition work: 0068 keeps one accountable
  Owner per stream and one Delivery Owner for integration; no document sizes a larger structure
  against it.
- **0077/0080 do not double-define**: 0080 extends 0077's separation to verdict supply and makes
  the oracle explicit (`q_upper := beta_upper` is human-oracle-relative); no quantity is defined
  twice with different semantics.

## What must change before this set is built from

1. Register EXP-104 and EXP-105 properly (headings, stopping rules fixed in advance) or
   re-nominate existing experiments in ADRs 0076 and 0080; register or withdraw EXP-118 in the
   hermes teardown. Three register entries or three edits — an hour's work.
2. Add index rows for 0070, 0072, 0078, 0079, 0080, recording the 0079→0078 amendment.
3. Fix `0068-model.py`'s branch order so the shipped classifier agrees with its own self-check.
4. Complete the in-flight work that is holding the suite red (events.py bypass additions,
   bibliography allowlist entry), then re-run: the bar is 7 failed → 0.
5. Correct 0071:166-167's "trusted … enforced" phrasing to declared-provenance language.

Everything else sampled stood up. The defects are real but they are clerical and one branch
ordering — not conceptual. The set's authors documented their own gaps honestly more often than
not (EXP-100's framing, the register's own record of the 104/105 collision, the friction log's
torn-append entry); the failure was that three documents claimed registrations the register
shows they knew were never made.

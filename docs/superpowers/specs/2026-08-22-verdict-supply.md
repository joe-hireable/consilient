# Verdict supply: automate the preparation, never the principal

**Correction: a later repair does not make a consequence-derived rate a lower bound on beta;
without an independently known-bad denominator it identifies only a lower-bound count for candidate
false shipments, and the current CLI does not authenticate the principal.** [algebra] [measured]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0080 is PROVISIONAL and EXP-105 decides whether the
  consequence signal survives even as a preparation signal. [asserted]
- **Author:** Codex dispatch `20260822T125607-1c160bb1c8`; the principal supplied the request for a
  smarter agent to do the preparatory work, while every mechanism and threshold below is this
  dispatch's provisional design. [measured]
- **Scope:** this repository only. No other repository is read, no gate changes, the six-command
  CLI is unchanged, and `routing_orchestration_enabled` stays `false`. [measured] [asserted]

## 1. Answer first: zero verdicts may be automated

`consil beta --json` currently reports one **declared-principal** rejection, one false accept, no
point estimate and a minimum of 30 human rejections. It also reports six quarantined lines. The row
passes current V0-18 self-consistency checks, but the record does not prove first-party presence.
[measured: live command and source trace, 2026-08-22]

**Automated replacements: 0 of 30. Required source: 30 of 30 principal-authored. Under current
declared-principal semantics, 29 further rejections are outstanding. Under the authenticated standard
specified here, the existing row must be re-attested or 30 authenticated rejections are needed.
Either route probably needs more cards because human acceptances and `unclear` responses do not enter
the denominator.** [measured] [algebra]

Tier 1 can discover candidate false shipments and Tier 2 can harden a verifier. Neither is a human
verdict, neither enters `Beta.compute()`, and neither is a candidate-exposure sizing input. [measured]
The machine can nevertheless reduce the irreducible action to one authenticated answer on a prepared
phone card, with a design target of at most 5 seconds median and 10 seconds at the 90th percentile.
That latency is `[asserted]` until EXP-105 measures it. [asserted]

## 2. Three estimands, never one column with three labels

Let `A` mean the frozen composite verifier accepted an artefact, `T` mean the artefact was latently
bad under the frozen contract, `H` mean the independently obtained human verdict rejects it, and `C`
mean a later consequence instrument proves that the artefact was repaired. Human-verdict beta is:
[algebra]

$$
\beta_H = P(A \mid H).
$$

Repository history can count observed `A intersection C` events. If the strict repair proof makes
`C` a subset of latent badness `T`, then: [algebra]

$$
P(A \cap C) \leq P(A \cap T) = q.
$$

Dividing the observed count by all frozen attempts therefore gives a lower bound on ADR-0077's
candidate false-shipment probability `q = P(A intersection T)`. It supplies no bound on
`P(A intersection H)` or `P(A | H)` until human labels are observed. Even an independently enumerated
latent-bad denominator would estimate an oracle-relative `P(A | T)`, not human-verdict beta. A
consequence-only history supplies neither denominator and misses silently bad cases. `P(A | C)` or
`P(C | A)` is not beta and may be biased in either direction. [algebra]

The exact label is therefore:

> `repository-consequence lower bound on candidate false-shipment probability q; not human-verdict beta; not a gate or sizing input`

[algebra] [asserted]

This direction matters. ADR-0077 sizes **candidate exposure** from an upper bound on bad-shipment
risk; it keeps that union separate from **composite verification**, the intersection of component
passes on one known-bad artefact, and from **evidence fusion**, the Owner's combination of readings.
A lower bound cannot serve as `q_upper`. Substituting it would admit too many attempts, under either
the robust `floor(epsilon / q_upper)` ceiling or the iid ceiling where that formula is admissible.
[algebra]

## 3. Tier 1: a strict consequence signal, research-only today

Tier 1 reuses EXP-01's history collector. Its `gh()` reader, per-artefact check-rollup retrieval,
file manifest and local Git history join remain one collector; the smallest required extension is
to ingest this repository's push-workflow runs because the present PR reader has no merged-PR rows
here. A second history reader is a defect. [measured]

EXP-01's title-plus-file-overlap hotfix rule is discovery only. Its own diagnostics show why: a
fix-like word, temporal proximity and an overlapping file do not establish that the earlier change
was wrong, and larger changes overlap more later work. [measured] Every discovery that cannot pass
the proof below is `unclassifiable`, never a repair. [asserted]

### Frozen population and horizon

- The population is candidate revisions on this repository's default branch with a recorded frozen
  composite outcome and complete component conclusions. A merge or process exit is not an accepted
  outcome. [asserted]
- The consequence horizon is the next **50 verifier-recorded candidate revisions** on that branch.
  A revision without the complete horizon is right-censored. The volume horizon is fixed before
  inspection so changes in commit velocity do not change the observation opportunity. The value 50
  is `[asserted]`; EXP-105 may show that it yields no evaluable population. [asserted]
- Consequence classification is frozen before the original verifier outcome and human verdict are
  revealed. Errors, missing checks, rewritten history and unexecutable old revisions remain visible
  terminal classes. [asserted]

### Repair, iteration and abstention

A later revision is a **repair** only through one of two causal anchors: [asserted]

1. It is a generated revert or carries a validated causal `Fixes:` reference to the candidate, and
   the complete verifier passes after the revert. A fix-like subject, abbreviated hash match or file
   overlap does not qualify. [asserted]
2. A regression test introduced with the repair passes on the candidate's parent, fails on the
   candidate, and passes on the repair revision under pinned environments. Reverting the repair hunk
   at the repair revision must make the test fail again. [asserted]

If the test also fails on the candidate's parent, the later work expresses a new requirement,
pre-existing defect or drift rather than proving that candidate introduced the failure. It is
ordinary iteration. Refactors, enhancements, dependency updates, documentation corrections without
an external source, and agent-authored claims that something was fixed remain iteration or
`unclassifiable`. [asserted]

Every result reports the full counts: repair, iteration, unclassifiable, right-censored, verifier
error, replay error and timeout, including explicit zeros. The consequence numerator is shown as a
count and as `count / all frozen attempts`; no beta headline is rendered. [asserted]

### What Tier 1 may do

A confirmed `A intersection C` event establishes that at least one accepted artefact in the frozen
sample had a demonstrated bad consequence. It can direct verifier hardening, attach a prepared
counterexample to a phone card and show that zero false accepts is untenable. [algebra] [asserted]
It cannot author `attempt.verdict`, set `sampling_unconditioned`, close a gate or enlarge
`n_attempt_max`. EXP-105 must confirm its alignment before even the preparation path is described as
validated. [asserted]

## 4. Tier 2: a proxy that cannot masquerade as beta

A different-family critic earns a different evidence class only when it executes the artefact,
drives a real interface, or checks a citation against its retrieved source. A family label plus a
second reading of the same material is echo. [cited: ADR-0067 and the frozen organisation bar]

Tier 2 follows the tracked EXP-96 instrument's refusal shape, not any current result file. The result
must carry a typed `estimand_kind`, sample counts, verifier contract and version, task family,
coverage, unclassifiable count, every error/timeout/refusal, and a partial-identification range.
[measured] [asserted]

Allowed exact estimands are `mutation_proxy_beta`, `critic_proxy_beta` and
`repository_consequence_q_lower_bound`; only `human_verdict_beta` may reach the beta projection or a
sizing consumer. Human prose is not the separation mechanism. [asserted]

The renderer prefixes every Tier 2 result with `PROXY —` and suppresses a headline figure when the
census is incomplete, an execution error occurred, fewer than 50 classifiable cases exist,
unclassifiable share exceeds 0.10, or the partial-identification width exceeds 0.10. It still reports
all counts and the refusal reason. These thresholds match EXP-96's registered standard; they do not
make its synthetic-fault distribution human ground truth. [measured] [asserted]

The enforcing check is
`tests/test_verdict_supply.py::test_proxy_estimands_never_project_as_human_beta_or_sizing_input`.
It must construct all four estimands, prove that only an authenticated `human_verdict_beta` record
can enter the human-beta projection, and source-scan routing for a proxy bypass. It ships with any
implementation, not with this specification-only change. [asserted]

## 5. Tier 3: one prepared question on a phone

### Selection before presentation

The beta queue is frozen independently of verifier acceptance, consequence labels and critic
outputs. Otherwise the measured beta is for a selected stratum, and showing only verifier-accepted
artefacts makes beta equal one by construction. Consequence and proxy results may prepare evidence
after inclusion; they may not decide inclusion or order. [algebra] [asserted]

Every card is bound to an existing `attempt.outcome`, exact artefact SHA-256, frozen acceptance
contract, verifier receipt/version and presentation digest. The current `--checks pass|fail` manual
assertion is insufficient evidence that a verifier ran. [measured] [asserted]

### The card

The phone shows only what the person needs for one decision: [asserted]

1. **Contract** — one sentence stating the criterion that applied when the artefact was produced,
   with a source locator. [asserted]
2. **Artefact** — the relevant rendered behaviour, diff fragment, screenshot, citation passage or
   executed counterexample; never a request to open a repository path. [asserted]
3. **Question** — `At that time, should this artefact have been rejected?` with `Reject`, `Accept`
   and `Unclear`. Existing `attempt.verdict` remains restricted to `accept|reject`; `Unclear`
   appends a separate audit-only `attempt.review` disposition bound to the attempt and carries no
   `human_verdict`. It is terminal, excluded from beta, never coerced and never silently replaced.
   [asserted]
4. **Reveal** — only after the signed answer, show what the frozen checks concluded and advance to
   the next card. Hiding the check before the answer reduces anchoring while still giving the
   principal the promised conclusion. [asserted]

The machine performs retrieval, minimises the evidence to the contract, runs the reproduction,
checks every locator and records the preparation trace. The principal supplies one thing only: the
answer. [asserted]

### First-party authorship is the floor

Current enforcement is self-consistency, not authentication: `events.py` accepts a declared actor
equal to a declared principal with `via=cli`, and `scripts/verdict.py --principal` lets the caller
choose both. Projection then drops the principal and channel. An agent process sharing the OS account
can therefore manufacture a syntactically valid principal verdict. [measured: source trace and
executed validation fixture, 2026-08-22]

The phone surface is read-only until the response carries an authenticated user-presence assertion
from a device enrolled by the principal. The assertion binds the one-time challenge, attempt id,
artefact digest, presentation digest, chosen verdict and expiry. `scripts/verdict.py` remains the
single ingress and verifies that assertion before calling `events.append()`; `via=cli` alone never
satisfies authorship. No secret or private key enters the repository or trajectory. [asserted]

This does not require a seventh `consil` command. It is a future mode of the existing script, and the
platform authenticator is an authority boundary rather than a new model or agent. Until that boundary
exists, the admissible route remains an actual principal using the local script, and the phone design
cannot claim to have supplied a verdict. [asserted]

### An interrupted answer must not jam beta

`scripts/verdict.py` currently appends the outcome before the verdict, which makes interruption leave
an unlabelled outcome rather than an orphan verdict. The general writer is still not transactional,
and a locally valid verdict for an unknown attempt can append and later brick projection. This
happened once and required hand deletion; the fatal behaviour remains pinned by a test. [measured]

Future implementation keeps the existing writer and adds three guards: [asserted]

- the verdict writer resolves the existing outcome and exact artefact before append inside a new
  process-serialised relational transaction; `events.append()` remains the sole event writer;
  [asserted]
- a duplicate or unknown-attempt verdict is rejected before write; if a malformed historical or
  interrupted line is read, the existing `Rejection`/quarantine projection records it and beta still
  renders; [asserted]
- flush and `fsync` complete before the UI acknowledges the answer. A crash before acknowledgement
  safely offers the same card again; a duplicate assertion is idempotently refused. [asserted]

The smallest checks are
`test_authenticated_phone_verdict_binds_attempt_artefact_and_choice`,
`test_unclear_review_is_terminal_and_never_enters_beta`,
`test_interruption_leaves_only_an_unlabelled_outcome`, and
`test_unknown_attempt_verdict_is_quarantined_and_beta_still_renders`. [asserted]

## 6. EXP-105: agreement without substitution

EXP-105 creates no separately selected human-review sample. It attaches a consequence classification
to the same independently frozen queue used to collect the remaining human-beta verdicts: re-attest the
existing row and collect 29 further rejections, or collect 30 authenticated rejections if
re-attestation is unavailable. Every intervening `Accept` and `Unclear` card stays in the experiment;
no response is replaced. [asserted]

The principal is blinded to consequence and verifier outcomes until after each verdict. The strict
instrument emits `consequence_reject` or abstains; absence of a repair never becomes an automatic
`Accept`. The result reports emitted-signal by `human_reject`/`human_accept`, plus `unclear`, coverage,
abstention, censoring, every error and latency. Positive predictive value is never reported without
coverage and the full table because a signal that fires once can agree perfectly while preparing
almost nothing. [asserted]

EXP-105 can confirm Tier 1 only as a separate preparation signal. It cannot change the 0/30
automation answer, V0-18, any gate or candidate sizing. Its exact procedure and stopping rule are
pre-registered in the experiment register. [asserted]

## 7. The bar, search and delta

The frozen organisation bar requires one accountable Owner, a new class of facts for every added
role, structured artefacts, independent outcome verdicts and comparison with a capable single Owner.
This design adds no review agent: repository consequence, executed regression and authenticated
human presence are the different classes; one Owner prepares the card. [measured] [asserted]

For history linkage, the incumbent is the SZZ family: revision history plus issue/fix links are used
to locate bug-inducing changes. A developer-informed evaluation built a manually filtered oracle
because researcher-only labels are a known weakness, and a Linux-kernel evaluation used 76,046
developer-labelled fix/inducing pairs while still finding ghost-commit failures. [cited: Rosa et al.,
2021, arXiv:2102.03300; Lyu et al., 2023, arXiv:2308.05060; retrieved 2026-08-22]

Herbold et al. found that standard and improved SZZ variants retained substantial false-positive
labelling when bug-fix identification was noisy. That is the direct bar for EXP-01's weaker
title-plus-file-overlap heuristic. [cited: Herbold et al., 2022, *Problems with SZZ and features*,
doi:10.1007/s10664-021-10092-4; retrieved 2026-08-22]

Searches on 2026-08-22 covered `SZZ algorithm defect inducing commits evaluation precision recall`,
`SZZ Unleashed`, developer-informed SZZ oracles, ghost commits and regression-based bug origin.
Near misses that used only issue keywords, researcher labels or vendor summaries were excluded.
[measured]

The delta is deliberately narrow: reuse the existing collector, replace circumstantial hotfix labels
with an executable parent/candidate/repair proof, abstain aggressively, preserve the full table, and
test agreement against the principal without ever upgrading the estimand. Whether that beats the
bar is `[asserted]` until EXP-105. [asserted]

## 8. Reuse and implementation boundary

No second orchestrator, store, writer, history collector or CLI command is introduced. Future work
extends `mine_beta.py` for push workflow receipts, `scripts/verdict.py` for prepared/authenticated
answers, and `events.py` for authenticated authorship plus relational quarantine. [asserted]

`dispatch.py` remains fan-out; `coordination.py` claims work; `recall.py` supplies bounded verbatim
context; `work_items.py` remains the task substrate; `routing.py` owns candidate-exposure ceilings;
`budget.py` owns spend; `instructions.py` layers context; and `events.py` remains the sole append-only
writer. [measured]

Tier 1 remains in the research tree until EXP-105 confirms it. Tier 2 remains a typed proxy. Tier 3
is the only path to human-verdict beta, and a phone renderer without authenticated user presence is
not Tier 3. [asserted]

## 9. Evidence against: none of this may be admissible

The strongest objection wins today. This repository's history is small, fast-changing and
self-referential; its current PR-centred EXP-01 collector has no merged-PR population here, verifier
contracts have moved, generated reverts are absent, and agent-authored changes share one Git author
identity. A later change is often one agent correcting another under a new requirement, not the world
grading an artefact. [measured]

Even a perfect causal repair link observes only failures that were noticed, made legible as a test
and fixed inside the horizon. Silent failures, abandoned work, external harms and defects fixed after
the horizon remain invisible. The missingness is outcome-dependent, so no algebra turns coverage
into an upper bound suitable for sizing. [algebra] [asserted]

Tier 2 is still an automated judgement; a different family without a new anchor is echo, and an
execution-bearing critic still measures a proxy oracle. The current phone path can be forged by a
local agent and can still jam projection with a relationally invalid verdict. [measured]

Accordingly the objection is conceded. Today Tier 1 supplies no admissible rate and Tier 2 supplies no
human verdict. Tier 3 still needs 29 additional current-semantics rejections plus re-attestation of
the existing row, or 30 new authenticated rejections. If EXP-105 is underpowered, contaminated or
adverse, delete Tier 1 from the product plan and keep only the prepared human card plus proxy-labelled
verifier hardening. [asserted]

# Verdict supply: automate the preparation, never the principal

**Correction: a later repair does not make a consequence-derived rate a lower bound on
human-verdict beta; at best it proves a lower-bound count for latent-contract false shipments in one
frozen cohort, and the current CLI does not authenticate the principal.** [algebra] [measured]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0080 is PROVISIONAL and EXP-105 decides whether the
  consequence signal survives even as a preparation signal. [asserted]
- **Author:** Codex dispatch `20260822T125607-1c160bb1c8`; the principal supplied the request for a
  smarter agent to do the preparatory work, while every mechanism and threshold below is this
  dispatch's provisional design. [measured]
- **Scope:** this repository only. No other repository is read, no gate changes, the six-command
  CLI is unchanged, and `routing_orchestration_enabled` stays `false`. [measured] [asserted]

## 1. Answer first: zero verdicts may be automated

`consil beta --json` currently reports one **declared-principal** rejection, projected
`n_false_accept=1`, no point estimate and a minimum of 30 human rejections. It also reports six
quarantined lines. The projected false-accept count rests on a manually asserted verifier Boolean;
the row has no artefact digest, frozen contract, verifier receipt/version or sampling provenance and
does not prove first-party presence. [measured: live command, source trace and trajectory row,
2026-08-22]

**Automated replacements: 0 of 30. Required source: 30 of 30 principal-authored. Under current
declared-principal semantics, 29 further rejections are outstanding. Under the authenticated standard
specified here, the existing row counts only if its artefact, candidate-time contract, verifier
receipt/version, independent queue provenance and human choice can all be reconstructed and
append-only attested; re-attesting the choice alone is insufficient. Otherwise 30 new authenticated
rejections are needed. Either route probably needs more cards because human acceptances and
`unclear` responses do not enter the denominator.** [measured] [algebra]

Tier 1 can discover candidate false shipments and Tier 2 can harden a verifier. Neither is a human
verdict, neither enters `Beta.compute()`, and neither is a candidate-exposure sizing input. [measured]
The machine can nevertheless reduce the irreducible action to one authenticated answer on a prepared
phone card, with a design target of at most 5 seconds median and 10 seconds at the 90th percentile.
That latency is `[asserted]` until EXP-105 measures it. [asserted]

## 2. Three estimands, never one column with three labels

Let `A` mean the frozen composite verifier accepted an artefact, `T` mean the artefact violated the
candidate-time contract, `H` mean the independently obtained human verdict rejects it, and `C` mean
a later consequence instrument proves that the artefact was repaired. Human-verdict beta and its
same-oracle joint candidate risk are: [algebra]

$$
\beta_H = P(A \mid H),
\qquad
q_H = P(A \cap H) = P(H)\beta_H \leq \beta_H.
$$

Repository history can count observed `A intersection C` events. If an executable candidate-time
contract proof makes `C` a subset of latent badness `T`, then at the population level: [algebra]

$$
P(A \cap C) \leq P(A \cap T) = q_T \leq \beta_T = P(A \mid T).
$$

For a frozen finite cohort `S`, the exact claim is only
`count_S(A intersection C) <= count_S(A intersection T)`. Dividing by `|S|` gives an empirical cohort
lower bound on latent-contract `q_T,S` and, weakly, `beta_T,S`; it is not a lower confidence bound for
either future population quantity. Population transfer would additionally require coverage-valid
sampling and pre-registered one-sided inference. The cohort result supplies no bound on operational
`q_H = P(A intersection H)` or human-verdict `beta_H` until human labels are observed.
Consequence-only history also misses silently bad cases. `P(A | C)` or `P(C | A)` is neither beta and
may be biased in either direction. [algebra]

The exact label is therefore:

> `observed finite-cohort repository-consequence lower bound on latent-contract false shipments; not operational q_H, human-verdict beta_H, a gate or a sizing input`

[algebra] [asserted]

This direction and oracle both matter. ADR-0077's substitution `q_upper := beta_upper` is valid only
when `q` and beta share the same badness event; under the current human-verdict meter that is `H`, so
the operational quantity is `q_H`. A Tier 1 lower bound concerns `T`, not `H`, and cannot serve as an
upper bound on either. Substituting it would admit too many attempts under either the robust
`floor(epsilon / q_upper)` ceiling or the iid diagnostic where that formula is admissible. The
current human-oracle-relative ceiling remains unchanged; it is not a bound on latent-contract harm.
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

- The population is every `candidate.exposed` record on this repository's default branch, appended
  before its verifier outcome. Its record binds the candidate identity, artefact digest and verifier
  contract.
  Missing or incomplete outcomes remain in the denominator as terminal classes; a merge or process
  exit is not an accepted outcome. [asserted]
- The consequence horizon is the next **50 verifier-recorded candidate exposures** on that branch.
  A revision without the complete horizon is right-censored. The volume horizon is fixed before
  inspection so changes in commit velocity do not change the observation opportunity. The value 50
  is `[asserted]`; EXP-105 may show that it yields no evaluable population. [asserted]
- Consequence classification is frozen before the original verifier outcome and human verdict are
  revealed. Errors, missing checks, rewritten history and unexecutable old revisions remain visible
  terminal classes. [asserted]

### Repair, iteration and abstention

A later revision is a **proved repair** only when all of the following hold: [asserted]

1. A versioned contract predicate and its source locator existed before the candidate. The later
   test must be mechanically entailed by that frozen predicate; a new requirement, later preference
   or agent-authored assertion is not candidate-time evidence. [asserted]
2. Under pinned environments, one executable witness passes on the candidate's parent, fails on the
   candidate, and passes on the repair revision. Reverting only the repair hunk at the repair revision
   must make the same witness fail again. [asserted]
3. The later revision has a full validated causal reference to the candidate or is its generated
   revert. This locates the proposed relation but cannot replace the contract and execution proof.
   A fix-like subject, abbreviated hash or file overlap is discovery only. [asserted]

If the witness also fails on the candidate's parent, is not entailed by the pre-candidate contract,
or cannot isolate the repair hunk, the later work is ordinary iteration or `unclassifiable`, not
proof that the candidate was bad. Refactors, enhancements, dependency updates, documentation
corrections without a pre-candidate checkable contract, and agent-authored claims that something was
fixed remain iteration or `unclassifiable`. [asserted]

Every result reports the full counts: proved repair, iteration, unclassifiable, right-censored,
verifier error, replay error and timeout, including explicit zeros. The consequence numerator is
shown as a count and as `count / all frozen attempts`, explicitly limited to that cohort; no beta or
population-`q` headline is rendered. [asserted]

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
`repository_consequence_false_shipment_cohort_lower_bound`; only `human_verdict_beta` may reach the
beta projection or a sizing consumer. Human prose is not the separation mechanism. [asserted]

The renderer prefixes every Tier 2 result with `PROXY —` and suppresses a headline figure unless all
registered conditions for that proxy pass. For the EXP-96-shaped mutation proxy those conditions are:
both baselines pass; both censuses complete; each corpus has at least 50 classifiable non-equivalent
mutants; every Wilson 95% interval has half-width at most 0.05; unclassifiable share is at most 0.10;
and partial-identification width is at most 0.10. It still reports all counts and the refusal reason.
Passing those conditions does not make a synthetic-fault distribution human ground truth.
[measured] [asserted]

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

That independence is not recordable today: there is no pre-outcome candidate-exposure/queue manifest,
and
`beta.from_connection(..., sampling_unconditioned=...)` currently drops the argument before calling
`compute()`. The future path appends `review.queue.opened` before any eligible exposure, fixing
`stream_cap=90`, `EXP105_prefix_n=30`, the target rejection count, one task-family population, one
composite verifier protocol/version and contract, start position and the label-blind rule "the first
90 matching `candidate.exposed` events in trajectory order". No verifier hardening or version change
enters that stream. `review.queue.frozen` records the complete eligible-universe digest, presented
prefix and ordered ids at the stopping event. Projection replays the selector from exposure events,
requires an exact manifest and complete outcome join, and derives `sampling_unconditioned` only
when replay succeeds; no caller may set it. A metamorphic check changes every verifier, consequence
and critic value before replay and requires the same identities and order. [measured] [asserted]

The exposure record itself is mandatory at the shared verification-start boundary before any
component runs; failure to append it refuses execution. Every component-outcome producer requires the
prior receipt, and projection rejects an outcome whose exposure is absent or later in trajectory
order. An integration/source-scan check enumerates every verification launch path and fails on a
bypass. Until that coverage check passes, `sampling_unconditioned` remains false even if a manifest
replays. [asserted]

Every card joins one selected `candidate.exposed` record to the complete protocol-defined set of
existing component `verification.outcome` records, reusing their artefact SHA-256 and verifier
ids/versions rather than creating a second outcome path. Projection derives the composite Boolean
only when the exact component key-set is complete and stores a rollup digest; a missing/error
component remains terminal. A separate `review.presentation.frozen` record binds the candidate-time
contract source/digest, composite rollup digest and rendered presentation digest. The current
`attempt.outcome` plus `--checks pass|fail` manual assertion is insufficient evidence that a verifier
ran. [measured] [asserted]

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
choose both. The generic event ledger preserves those fields, but the outcomes/beta projection drops
them. An agent process sharing the OS account can therefore manufacture a syntactically valid
principal verdict. [measured: source trace and executed validation fixture, 2026-08-22]

Presence is insufficient. WebAuthn Level 3 says a presence test is normally a touch and explicitly
does not constitute user verification; `userVerification=required` fails the ceremony unless the UV
flag is set. It also requires the relying party to verify the challenge, expected origin, RP ID hash,
credential and signature. [cited: [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/),
sections 4, 5.8.6 and 7.2, retrieved 2026-08-22]

The phone surface is therefore read-only until a principal-controlled WebAuthn enrolment and recovery
policy exists. Enrolment/revocation records map a credential public key to the principal in the
gitignored trajectory; private key material stays in the authenticator. Every ceremony requires user
verification and binds a fresh durable challenge to the trajectory instance, canonical workspace,
protocol and queue ids, attempt id, artefact, candidate-time contract, verifier receipt,
presentation, chosen answer, expiry and idempotency key. The verifier checks credential status,
signature, challenge, origin, RP ID, UV flag and the registered counter/replay policy, then derives
actor/principal from the credential mapping rather than caller data. Shared authenticators remain a
documented residual identity risk. [cited] [asserted]

The trusted return protocol is the same first-party HTTPS WebAuthn relying-party session that renders
the phone card. `transport.py` may relay only the opaque signed assertion envelope; plaintext
verdict-shaped Slack, Twilio, email, SMS or webhook payloads remain refused. The event records
`via=phone_webauthn` and the actual HTTPS relay separately, never `via=cli`. No connector, outward
service or credential is activated by this specification. [asserted]

A phone cannot use the desktop's HTTP `localhost` exception. The recommended deployment class is a
principal-approved HTTPS origin on a private interface, with its RP ID, allowed origin, network scope,
TLS certificate and key held only in gitignored instance state; a hosted endpoint is a separately
approved alternative, not a fallback. Both create credential/network-exposure decisions reserved to
the principal. Until one is explicitly configured, the card may be prepared locally but is not
phone-accessible or write-capable. [cited: W3C WebAuthn Level 3 sections 4 and 7.2] [asserted]

`scripts/verdict.py` remains the user-facing command and gains a future phone mode; there is no
seventh `consil` command. The append-only trajectory records credential public keys, revocations,
card/challenge issuance and the signed answer, so no second product store is introduced. The current
AST boundary and installed dependencies cannot verify WebAuthn/COSE signatures in the shared writer,
however. A separately approved audited verifier dependency or OS-isolated broker, with its own ADR
and amended enforcement allowlist, is a real prerequisite. This task adds neither. Until it lands,
phone responses cannot write a verdict and the existing local script remains declared-principal,
not machine-authenticated, evidence. [measured] [asserted]

The shared append boundary, not the phone script, is the authority chokepoint. `events.append()` must
verify the ceremony before any `attempt.verdict`, `attempt.verdict.correction` or `attempt.review`;
`consil record` and direct Python callers reach the same branch. Corrections use a new challenge bound
to the prior and replacement verdict plus reason. Projection joins the authenticated event to the
queue, presentation and `verification.outcome` records and exposes auth method, credential,
principal, channel, protocol and all bound digests. Legacy or incomplete rows fail closed from the
authenticated-beta view rather than being upgraded by prose. [asserted]

### An interrupted answer must not jam beta

`scripts/verdict.py` currently appends the outcome before the verdict, which makes interruption leave
an unlabelled outcome only when the first full line committed and the second never began. The shared
writer is unlocked and not fsynced, so a kill can instead leave no line or a truncated line; another
event kind can interleave. A locally valid verdict for an unknown attempt can also append and brick
projection. Both torn append and hand-deletion incidents are recorded in this repository. [measured]

Future implementation keeps one writer and adds one per-log transaction boundary for **all** event
kinds: an OS-released lock, not an existence lock that survives process death; a single UTF-8 byte
record written with append semantics; and flush plus `fsync` before acknowledgement. For a
human-only event, the same lock covers challenge lookup/unused check, credential verification,
one-to-one relational joins, duplicate comparison and append. The verdict event itself consumes the
challenge. [asserted]

The idempotency key has exact retry semantics. A retry after commit but before acknowledgement returns
the original committed receipt as success when every bound field and answer match; a conflicting
reuse is refused. Fault injection covers before append, partial append, after append before `fsync`,
after `fsync` before acknowledgement and retry. [asserted]

Parsing/schema failures continue through `events.Rejection`. Relational failures—unknown/duplicate
outcome or verdict, invalid correction, missing queue/card/verification join—belong in
`projection.py`: each becomes a deterministic quarantine row carrying source path, line and digest,
and replay continues. Human and JSON beta output both show quarantine count/reasons or their exact
locator, projection-derived sampling status and the human-oracle caveat. A render that merely avoids
crashing while hiding a rejected row fails. [asserted]

The smallest checks are `test_authenticated_phone_verdict_binds_every_receipt_and_uv`,
`test_record_and_direct_append_cannot_bypass_authenticated_human_events`,
`test_authenticated_correction_requires_a_new_bound_challenge`,
`test_unclear_review_is_terminal_and_never_enters_beta`,
`test_append_faults_are_replayable_and_retry_returns_the_committed_receipt`,
`test_relational_rejections_are_quarantined_and_beta_remains_complete`, and
`test_beta_outputs_show_quarantine_sampling_and_oracle_caveat`. [asserted]

## 6. EXP-105: agreement without substitution

EXP-105 creates no consequence-selected human-review sample. It uses the first **30 new cards** from
the independently precommitted queue above, then stops when all 30 are terminal or 30 days after the
first card, whichever comes first. The already unblinded legacy row never enters agreement or
latency, whatever its later provenance disposition. `Accept`, `Reject`, `Unclear`, unanswered and
invalid cards keep their frozen slots; no response is replaced. After that fixed EXP-105 prefix, the
same precommitted stream may continue only until the predeclared 29-or-30 authenticated-rejection
target, 90 terminal cards, or the same 30-day deadline. Failing to reach the target is
`insufficient_data`; no second unmanifested stream is implied. [asserted]

The principal is blinded to consequence and verifier outcomes until after each verdict. The strict
instrument emits `consequence_reject` or abstains; absence of a repair never becomes an automatic
`Accept`. The result reports emitted-signal by `human_reject`/`human_accept`, plus `unclear`, coverage,
abstention, censoring, every error and latency. Per-card latency starts when the complete card is
rendered and actionable and ends only when the answer is durably fsynced and acknowledged; it
includes the authenticator prompt, retry and reveal. `Unclear` is included and any unanswered card at
the deadline prevents confirmation. Enrolment, recovery and setup minutes are reported separately
and amortised over all 30 slots. Positive
predictive value is never reported without coverage and the full table because a signal that fires
once can agree perfectly while preparing almost nothing. [asserted]

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

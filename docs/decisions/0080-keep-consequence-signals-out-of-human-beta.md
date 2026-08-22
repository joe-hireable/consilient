# 0080. Keep consequence signals out of human-verdict beta

- **Status:** PROVISIONAL — the estimand separation is fixed; EXP-105 decides whether the strict
  repository-consequence signal is useful even for preparing human review
- **Date:** 2026-08-22
- **Deciders:** Codex dispatch `20260822T125607-1c160bb1c8` for the provisional mechanism. The
  principal requested less preparatory labour; that request is product input, not authorship of this
  decision.
- **Inquiry tier reached:** T2 algebra and source trace; T3 pre-registered as EXP-105, not run
- **Executable model:** none — the identification result is exact, while usefulness and agreement
  require the blinded human observations pre-registered in EXP-105

## Context

The human-beta projection requires at least 30 recorded human rejections before it
reports an estimate. It currently reports one declared-principal rejection, projected
`n_false_accept=1`, six quarantined lines and insufficient data. The projected count rests on a
manually asserted verifier Boolean; the row lacks the artefact, contract, verifier receipt and queue
provenance required below. Current semantics therefore need 29 additional rejections. The
authenticated standard admits the existing row only if all of those bindings and first-party choice
can be independently reconstructed and append-only attested; re-attesting the choice alone is
insufficient. Otherwise it needs 30 new authenticated rejections. [measured] [algebra]

The proposed shortcut was to derive verdicts from later repository consequences: a repair following
an artefact might show that the earlier artefact was bad. This contains useful evidence but the
suggested direction is wrong for human-verdict beta. Let `A` mean verifier acceptance, `T` mean a
candidate-time contract violation, `H` mean an independent human rejection, and `C` mean a causally
demonstrated later repair. Current human beta is `beta_H = P(A | H)` and its same-oracle candidate
risk is `q_H = P(A intersection H) <= beta_H`. Even if `C` is a subset of `T`, history observes a
different quantity: `A intersection C`. In one frozen cohort its count and ratio lower-bound only the
cohort's latent-contract `q_T` and, weakly, `beta_T`; they are not population confidence bounds without
coverage-valid sampling and one-sided inference, say nothing about `H` without labels, and cannot be
used as ADR-0077's `q_H` sizing upper bound. [algebra]

The current human-verdict boundary is also weaker than its name. `events.py` checks that the declared
actor equals the declared principal and that the declared channel is `cli`; `scripts/verdict.py`
lets its caller choose that principal. The generic event ledger preserves both fields, but the
outcomes/beta projection drops them. A local agent process can thus write a syntactically valid
declared-principal verdict. [measured]

ADR-0077 already separates candidate exposure, composite verification and evidence fusion. This ADR
extends that separation to verdict supply and makes its implicit oracle explicit: the current
`q_upper := beta_upper` substitution is human-oracle-relative because both quantities use `H`; it is
not a bound on latent-contract `T`. The operational ceiling, Gate A, Gate B, V0-18 and current CLI are
otherwise unchanged. [algebra] [asserted]

## Decision

Consilient will keep three verdict-supply tiers separate. [asserted]

1. **Repository consequence is a research signal.** Tier 1 may emit only
   `repository_consequence_false_shipment_cohort_lower_bound`, labelled exactly
   `observed finite-cohort repository-consequence lower bound on latent-contract false shipments; not operational q_H, human-verdict beta_H, a gate or a sizing input`. It may find counterexamples and prepare evidence; it may not
   author `attempt.verdict`, set `sampling_unconditioned`, enter beta, close a gate or enlarge a
   candidate-exposure ceiling. [algebra] [asserted]
2. **Automated critique remains a typed proxy.** Tier 2 may emit `mutation_proxy_beta`,
   `critic_proxy_beta` or `repository_consequence_false_shipment_cohort_lower_bound`. A result carries
   its estimand kind, frozen verifier contract, sample and coverage counts, every
   refusal/error/timeout, and its partial-identification range. Only `human_verdict_beta` may reach
   the human-beta projection or the same-human-oracle sizing consumer; no current result sizes latent
   `T` risk. [asserted]
3. **Only authenticated principal verification supplies the residual verdict.** Tier 3 prepares one
   blinded phone card and accepts `Reject`, `Accept` or terminal `Unclear`. Existing
   `attempt.verdict` remains `accept|reject`; `Unclear` is an audit-only `attempt.review` with no
   `human_verdict`. The phone stays read-only until an enrolled WebAuthn credential completes a
   user-verification-required ceremony binding workspace/trajectory, protocol/queue, attempt,
   artefact, contract, complete composite receipt, presentation, answer, expiry and idempotency key.
   The shared append boundary verifies challenge, credential, signature, origin, RP ID, UV and replay
   policy and derives the principal/channel. Presence, `via=cli` and caller identity are insufficient.
   A phone-reachable HTTPS RP origin, TLS key/certificate and network exposure require separate
   principal approval; no endpoint is activated here.
   [cited: [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/)] [asserted]
4. **The beta queue is selected before preparation.** Verifier, consequence and critic outcomes may
   prepare a card only after its independent inclusion. They never choose or order the human-beta
   sample. A queue-open event precommits a label-blind 90-exposure stream, fixed 30-card EXP-105
   prefix, target rejection count and deadline before any eligible `candidate.exposed` event under
   one frozen task family and composite verifier protocol/version; a frozen manifest records the
   complete universe digest, presented prefix and ordered ids.
   Projection replays that selector, joins each exposure to its exact protocol-defined component set
   and derives the composite outcome and
   unconditioned-sampling flag only after exact agreement rather than trusting a caller Boolean.
   Otherwise the estimand changes to a selected stratum. [algebra] [asserted]
5. **Interrupted or relationally invalid verdicts do not jam the record.** The existing verdict
   script remains the user-facing command and `events.append()` remains the sole enforcing writer. A
   future authenticated mode uses one OS-released per-log lock for every event kind; verifies the
   ceremony, challenge and joins; writes one append-only byte record; fsyncs before acknowledgement;
   and returns the same committed receipt on an identical retry. Parse/schema rejection stays in
   `events`; relational rejection becomes a deterministic quarantine row in `projection.py` and
   replay continues. Corrections and direct/generic-record callers use the same boundary. [asserted]

The honest automation count is therefore **0 of 30**. All 30 denominator observations remain
principal-authored. Current semantics need 29 additional rejections; authenticated semantics need
those 29 only if the existing row's artefact, candidate-time contract, complete verifier receipt,
independent queue provenance and choice can all be reconstructed and append-only attested; otherwise
they need 30 new rejections. Tier 1 and Tier 2 automate preparation and verifier learning, never
verdict authorship. [measured] [asserted]

The complete protocol, causal repair rule and phone card are specified in
`../superpowers/specs/2026-08-22-verdict-supply.md`. EXP-105 is the killing experiment for Tier 1's
continued place in that preparation path. [asserted]

## Evidence

- `[measured]` The live `consil beta --json` projection on 2026-08-22 returned
  `insufficient_data`, `n_rejected=1`, `n_false_accept=1`, `quarantined=6` and a minimum of 30
  human rejections.
- `[measured]` `Beta.compute()` admits only records with `human_verdict='reject'`; consequence and
  proxy observations are not inputs. The generic event ledger preserves principal/channel fields,
  while the outcomes/beta projection does not.
- `[measured]` `beta.from_connection(..., sampling_unconditioned=...)` currently drops that argument,
  and no queue manifest lets projection derive it. An independent queue is therefore a required
  implementation artefact, not a prose assertion.
- `[measured]` `scripts/verdict.py` orders outcome before verdict, so interruption in that script
  leaves an unlabelled outcome. The generic append path can still accept a verdict for an unknown
  attempt, which makes projection fail; the repository records an earlier hand deletion for this
  failure class.
- `[measured]` EXP-01 already contains the history reader, check-rollup retrieval, local Git join and
  deliberately weak hotfix diagnostics. Reusing it avoids a second consequence collector.
- `[measured]` The tracked EXP-96 runner and tests already separate a proxy estimand, denominator,
  coverage, refusal and incomplete-census states. Its current untracked result is not evidence for
  this decision.
- `[algebra]` If a candidate-time contract proof makes `C` a subset of latent badness `T`, then
  `P(A intersection C) <= q_T = P(A intersection T) <= beta_T`. In a frozen cohort only the
  corresponding count inequality is exact; its observed ratio is not a population confidence bound.
  Neither supplies a relationship to operational `q_H` or `beta_H` until labels are observed.
- `[cited]` Rosa et al. (2021), arXiv:2102.03300, use a developer-informed oracle to evaluate SZZ;
  Lyu et al. (2023), arXiv:2308.05060, evaluate SZZ on 76,046 developer-labelled Linux-kernel pairs
  and retain ghost-commit failure modes.
- `[cited]` Herbold et al. (2022), doi:10.1007/s10664-021-10092-4, show that noisy bug-fix
  identification leaves substantial false-positive SZZ labels. EXP-01's title-plus-file-overlap
  discovery rule is weaker still.

## Evidence against

- `[measured]` This repository currently supplies no merged-PR population to EXP-01's PR reader,
  generated reverts are absent, verifier contracts have changed, and agent-authored changes share
  one Git author identity. A push-workflow extension can increase coverage but not independence.
- `[asserted]` A strict executable regression proof will abstain on most documentation, architecture
  and requirements changes. It may produce no useful Tier 1 population.
- `[algebra]` Consequence observation is outcome-dependent missingness: unnoticed, abandoned,
  external and post-horizon failures are absent. No observed agreement rate repairs that selection.
- `[asserted]` A device authenticator reduces authorship ambiguity but adds enrolment and recovery
  friction. If the card still takes longer than an ordinary local verdict, it has failed its purpose.
- `[asserted]` A capable Owner may prepare the same card directly with less machinery. Proxy critics
  and historical repair mining can create confident ceremony without reducing principal effort.

The strongest objection is conceded today: **none of the automated signals may prove admissible.**
Until EXP-105 reports, Tier 1 supplies no admissible rate and Tier 2 supplies no human verdict. Tier 3
still requires 29 current-semantics rejections plus re-attestation of the existing row, or 30 new
authenticated rejections. An adverse, contaminated or underpowered EXP-105 result removes Tier 1
from the product plan; the prepared human card and explicitly proxy-labelled verifier hardening
remain. [asserted]

## Consequences

**Positive** — the principal receives a small prepared decision rather than a request to inspect a
repository; automated consequences can still expose concrete failures without contaminating beta;
and a lower bound cannot silently loosen candidate sizing. [algebra] [asserted]

**Negative** — the human-beta denominator receives no automated credit, so at least 29 remaining
rejections are still human work and the existing row needs full provenance reconstruction, not mere
re-attestation, for an authenticated claim. WebAuthn verification needs a separately approved
dependency or OS broker before phone delivery can write. [asserted]

**Neutral but load-bearing** — an automated result may be accurate and useful while remaining the
wrong estimand. Evidence value does not grant authorship or sizing authority. [algebra]

## Enforcement

This is a specification and pre-registration change; no phone or proxy implementation ships here.
The implementation boundary is the existing `scripts/verdict.py`, `transport.py`, `events.py`,
`projection.py`, beta projection and EXP-01 collector. It adds no CLI command, writer, product store
or orchestrator; credential public records and challenges use the existing gitignored trajectory.
The preferred audited WebAuthn dependency or OS-isolated broker requires separate approval and an
ADR/allowlist change, so this ADR does not pretend the phone writer is implementable under today's
AST boundary. [measured] [asserted]

- Check: `tests/test_verdict_supply.py::test_proxy_estimands_never_project_as_human_beta_or_sizing_input`
  constructs every allowed estimand and proves that only an authenticated `human_verdict_beta`
  record reaches either consumer. It source-scans routing for a proxy bypass. [asserted]
- Check: `test_authenticated_phone_verdict_binds_every_receipt_and_uv` rejects a missing, replayed,
  wrong-origin/RP, non-UV or mismatched assertion. [asserted]
- Check: `test_record_and_direct_append_cannot_bypass_authenticated_human_events` invokes both paths
  for verdict, correction and unclear review with a declared principal but no ceremony and requires
  refusal. [asserted]
- Check: `test_authenticated_correction_requires_a_new_bound_challenge` binds prior/replacement
  verdict and reason. [asserted]
- Check: `test_unclear_review_is_terminal_and_never_enters_beta` preserves an explicit abstention
  without widening `attempt.verdict` or allowing a replacement card. [asserted]
- Check: `test_queue_manifest_is_invariant_to_verifier_consequence_and_critic_values` and
  `test_beta_sampling_flag_is_projection_derived_not_caller_set` replay the precommitted selector,
  protect independent admission and require the complete component-set join. [asserted]
- Check: `test_every_verification_path_records_exposure_before_execution` refuses a verifier launch
  without the prior exposure receipt, rejects a late/absent receipt and source-scans every component
  producer for a bypass. [asserted]
- Check: `test_append_faults_are_replayable_and_retry_returns_the_committed_receipt`,
  `test_relational_rejections_are_quarantined_and_beta_remains_complete`, and
  `test_beta_outputs_show_quarantine_sampling_and_oracle_caveat` protect the append/read/reporting
  boundary. [asserted]
- Check: the Tier 1 analyser refuses a repair unless a pre-candidate versioned contract entails the
  witness, the pinned parent/candidate/repair plus revert-hunk proof passes, and a full causal
  reference or generated revert locates the candidate. It reports every terminal class and never
  renders a beta or population-`q` headline. [asserted]
- Fails CI: not yet — each check above must ship in the same commit as the implementation it guards;
  the current change introduces no executable proxy or phone path. [measured] [asserted]

## What would overturn this

EXP-105 confirms Tier 1 only as a preparation signal when its frozen stopping rule meets both
pre-registered agreement thresholds without invalid causal proofs, hidden replacement, excessive
unclassifiable cases or suppressed errors. Failure removes Tier 1 rather than weakening the rule.
[asserted]

No EXP-105 result can overturn the 0-of-30 automation answer. Changing that requires a new ADR with
an independently justified human-ground-truth standard and an authenticated authorship boundary;
agreement with the principal on the same sample is validation of a proxy, not transfer of the
principal's authority. [algebra] [asserted]

The latency target is separately falsified if the prepared card exceeds 5 seconds median or 10
seconds at the 90th percentile across all answered cards, including `Unclear`. Any unanswered card at
the deadline prevents confirmation; missing responses remain visible and are never replaced to
rescue the target. [asserted]

## Publication candidate?

**No.** The estimand correction is elementary identification, the consequence instrument is
unvalidated and authenticated phone ingress does not exist. Publication would require a complete
EXP-105 result and an independent replication repository that may legally be disclosed. [asserted]

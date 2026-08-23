# Autonomy and friction: the machine decides; protected one-way effects reach the principal

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** § 11 (EXP-103 and the cheaper adapter-escape case named there).

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

**Correction:** R30 is **PARTIAL**, not absent: `events.py` already validates
`decision.autonomous` records and typed reversal shapes under V0-22/V0-23/V0-24, while
`tests/test_decisions.py` exercises that schema; no producer executes or verifies the reversal,
no escalation boundary exists, and no projection counts friction. [measured]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0075 is PROVISIONAL and EXP-103 can kill its mechanism. [asserted]
- **Author:** Codex dispatch `20260822T122851-29970aed66`; the quoted requirement is the
  principal's, while every mechanism below is this dispatch's provisional design. [measured]
- **Scope:** future extension of the existing dispatcher, work-item substrate and trajectory;
  no gate, CLI command or product implementation changes here. [asserted]

## 1. Requirement and success condition

The principal said the system must avoid duplicating model safety and must remove work, stress and
approval load; the default is maximum agent authority, permission, capability and autonomy, with law
as the minimum floor. [measured: `docs/00-context/the-machine-2026-08-22.md`]

The implementable success condition is narrower and falsifiable: a material decision which does not
commit a protected one-way effect is taken without asking; every state-changing autonomous decision
carries an executable, tested inverse; and every attempted transfer of work to the principal is
recorded and classified by a controller rather than by model confidence. [asserted]

This extends ADR-0067 rather than adding a committee. One accountable Owner may propose an action;
the different class of facts is the observed result of executing the forward and inverse operations
in isolation. A second agent rereading the proposal adds no evidence and is not part of this design.
[asserted]

## 2. The bar and the delta

The current local baseline is ADR-0033 plus `events.py`: decide by default, keep seven user-only
labels, require reasoning/falsifier/reversal, and accept a syntactically valid commit reference,
argv list or dotted symbol. [measured]

That baseline does not clear the frozen external bar. A nonexistent seven-character SHA, an
uninstalled command and a nonexistent dotted symbol all pass the present shape check; the decision
class may be absent, unknown, mixed-case or non-text; and delegated harness actions do not pass
through an action admission boundary. [measured]

The delta is four executable properties: the controller derives class from a capability's effect
manifest; forward then inverse is run against the exact starting state; state equality and escaped
effects are checked; and the user-facing renderer cannot wait for a response without a valid
escalation record. [asserted]

The frozen organisation bar requires one owner, provenance-bearing artefacts, independent execution
facts, a capable single-owner comparator and outcome measurement rather than confidence or agreement.
This design uses those tests unchanged. [measured: `docs/00-context/agentic-organisation-bar-2026-08-22.md`]

## 3. Mechanical reversibility

### 3.1 The controller's inputs

The model does not declare an action reversible. Each side-effecting capability adapter emits a
typed effect manifest which the controller recomputes from the actual invocation before execution.
Raw shell, network, credential, payment and external-write paths that cannot emit such a manifest
are unclassified and are not admitted to live execution. [asserted]

The manifest contains: [asserted]

| Field | Required value |
|---|---|
| `operation_id` | Stable decision/action identity. |
| `adapter` | Adapter identifier, version and implementation digest. |
| `forward` | Structured invocation with secret values replaced by broker references. |
| `scope` | Canonical state URIs the invocation may mutate. |
| `start_state` | Immutable revision or canonical digest for every scoped URI. |
| `effects` | Exact enum set produced by the adapter, never free text. |
| `observer` | Trusted broker or outer-sandbox identity and policy digest, independent of the adapter. |
| `expected_state` | State predicate or digest expected after the forward operation. |
| `reversal` | Typed revert, argv or named inverse plus its input values. |
| `residuals` | Effects no inverse can recover, including elapsed time, consumed included quota and append-only evidence. |
| `ceilings` | Maximum wall time, writes and local resource consumption for the proof and live action. |

The manifest is an admission declaration, not evidence that the adapter told the truth. Protected
sinks must pass through a trusted broker or OS-level outer sandbox which independently records and
refuses network, credential, payment, external-write and out-of-root filesystem attempts. An adapter
is admitted only with fixtures showing the right enum and a lying-adapter negative control whose
undeclared outbound attempt is observed and refused. A model-supplied manifest is data to reject,
not authority to classify itself. [asserted]

### 3.2 The test

For a material state-changing action, the controller applies this fixed algorithm: [asserted]

1. Recompute the effect manifest from the adapter and invocation. Reject a missing field, unknown
   enum, free-text class, case variant or whitespace variant. [asserted]
2. If an effect intersects the closed escalation set in section 5 and no matching first-party
   standing authority already covers it, create an escalation attempt; do not run the action.
   [asserted]
3. Otherwise create an isolated copy from `start_state` under the independent outer sandbox. Deny
   and log every network, credential, payment and external-transport attempt, including one the
   adapter did not declare. [asserted]
4. Run `forward`, assert `expected_state`, run `reversal`, and compare the canonical digest of every
   scoped URI with `start_state`. Diff the enclosing admitted root as well; any undeclared mutation
   or denied protected-effect attempt fails the proof. [asserted]
5. Record the proof bound to the operation, adapter digest, starting-state digest and verifier
   digest, including the independently produced broker/sandbox log digest. Only then may the same
   structured forward invocation run against live state, and only through those same brokers.
   [asserted]

The decision is **mechanically reversible** only when steps 1-5 pass. Model confidence, agreement,
rationale quality and a process exit code are not inputs. [asserted]

Restoration means restoration of the declared governed state, not reversal of time. Unrecoverable
residuals remain visible; a residual that enters the closed consequential set changes the disposition
to escalation rather than being hidden behind a successful state digest. [asserted]

Pure reads use the existing knowledge/usage event paths and need no invented undo. A material choice
which changes no external state is reversed by a later superseding decision linked to the prior
`decision_id`; append-only history itself is never erased. [asserted]

### 3.3 When proof cannot be produced

Failure to prove an inverse is not an approval request. The Owner must choose, in order: use a
versioned/transactional adapter, stage a local draft, take a restorable snapshot, or terminate the
work item as an unclosed capability gap. Only an independently derived protected effect from section
5 may reach the principal. [asserted]

This rule removes approval friction without pretending the unavailable action ran. It can reduce
capability until mediated adapters exist, which is an explicit interim cost rather than a hidden
safety claim. [asserted]

## 4. Reversal record and proof

`events.py` remains the only trajectory writer. `decision.autonomous` links to the existing
work-item ticket and to an `attempt.outcome` carrying the scratch forward/inverse proof. A later
inverse exercise is another linked `attempt.outcome`; neither event edits the original decision or
requires a second outcome store. [asserted]

The autonomous-decision record contains: [asserted]

- `decision_id`, existing work-item ticket, proof/live attempt identities, actor and Owner;
  [asserted]
- the decision, reasoning, option not taken, evidence references and falsifier; [asserted]
- the canonical decision class, effect-manifest digest, adapter/version, scope and starting-state
  digests; [asserted]
- the exact typed reversal with secret-free broker references, expiry, and cost/write ceilings;
  [asserted]
- proof environment, forward result digest, inverse result digest, full-scope equality result,
  independent observer/log digest, escaped-effect result, verifier contract/digest, timestamp and
  residuals; [asserted]
- live action outcome and the identity of any later reversal-exercise attempt. [asserted]

Validation must resolve a revert target to an object, resolve a named inverse to an allowlisted
callable, and prove an argv executable is admitted; regex/list shape alone is not execution.
[asserted]

EXP-35 remains the sampler of live reversals. Its fixed rule is reused: at least 30 sampled reversals
and under 10% misclassification are required for a sound aggregate claim; above 25% flips the
default; 10-25% or fewer than 30 is insufficient evidence. EXP-103 measures the distinct downstream
outcome and friction question rather than duplicating that sampler. For this run EXP-103 fixes a
100% sample of eligible Arm-B inverses, a digest-derived order and a 300-second wall-time ceiling
before any outcome is seen. [measured] [asserted]

The record is not yet reliable enough to carry this load. The current cross-process trajectory has
three new bypassed/malformed lines above its ratchet (`95 > 92`), and ordinary `append()` writes are
neither locked across processes nor fsynced. Any implementation must first serialise all event kinds,
flush and fsync before returning, and retain the existing bypass ratchet; otherwise a concurrent
escalation can disappear from the denominator it is meant to govern. [measured: targeted test,
2026-08-22; `docs/00-context/friction-log.md`]

## 5. Closed escalation set

There are exactly six top-level classes. Adding one requires a superseding ADR and a same-commit
exact-set test. [asserted]

| Canonical class | Mechanical trigger | Required evidence before delivery |
|---|---|---|
| `money` | The action commits funds or creates a new metered liability not covered by an exact first-party authorisation. Prepaid included quota is not a new debit. | Amount, currency, payee/provider, purpose, ceiling and authority reference; never a credential value. [asserted] |
| `credential` | The action acquires, reveals or expands the scope of a credential/permission. Use of a brokered credential inside its already authorised scope is not a new decision. | Broker and requested scope; no secret in the event. [asserted] |
| `external_exposure` | A write/send/publish operation exposes an artefact, message or non-public instance data outside the machine. Read-only public retrieval carrying no non-public data is not a publication. | Channel, recipient, payload digest, privacy classification and authority reference. [asserted] |
| `unrecoverable_state_loss` | A delete/overwrite cannot produce and verify a restorable snapshot or transaction rollback under section 3. | Canonical targets, failed recovery proof and consequence description. [asserted] |
| `principal_authority` | The requested result is one V0-18 reserves: `approval`, `consent`, `gate_lift`, `spend_authorisation` or `verdict`. | Exact subtype, first-party arrival channel and principal identity; an agent-authored response never satisfies it. [asserted] |
| `preference` | Two or more surviving options pass the same frozen acceptance contract, none dominates on any declared measurable dimension, and the remaining dimension belongs to the user's stated preferences. | Options, contract/verifier digest, comparison table and preference key or explicit absence of an objective comparator. [asserted] |

`feedback.answered` remains principal-authored, skippable task-close evidence. V0-18's authority
list is the five subtypes in `principal_authority`; feedback is not an approval, escalation or live
routing input and cannot satisfy one. Its first-party authorship check remains intact. `HUMAN_ONLY`
therefore remains an authorship set, not a second escalation taxonomy; an exact mapping test sends
its five authority values to `principal_authority` and `feedback` to evidence-only. [measured]
[asserted]

The controller, not the proposing model, derives the class from effect facts and the frozen task
contract. Unknown, omitted, mixed-case, whitespace-padded and non-text class values are invalid;
they are never normalised into permission. [asserted]

The controller computes disposition and appends one canonical `escalation.attempted` event carrying
`delivered` or `refused` **before** any rendering. A principal-facing transport accepts only an event
id whose recorded disposition is delivered; a child harness's stdout cannot itself pause work or
solicit authority. [asserted]

A delivered response enters through the existing V0-18 first-party authorship path. A role name,
manager, remembered preference, prior agent summary or `principal` field cannot author it. Authority-
shaped aliases such as an agent-authored `approval` or `gate_lift` event with the
`human_decision` field omitted are rejected rather than left for a future consumer to misread.
[asserted]

Enforcement consists of one exact enum in `events.py`, one `request_principal()` boundary used by
`dispatch.py` and projections, class-specific validators, a source scan banning another delivery
path, and fixtures proving all six valid classes plus arbitrary invalid strings. A future test must
also prove that an out-of-set attempt is recorded, refused, returned to the Owner and never rendered
as a blocking question. [asserted]

The current `capability.gap` rule and dashboard form a second escalation path: `silent`,
`not_implemented` and unknown refusals are presently forced to “escalate” and rendered as requiring
a human. Future closure becomes machine-owned `repair`, `retry`, `local_surrogate` or `defer`; only a
separately proven class from the table above may use `request_principal()`. [measured] [asserted]

## 6. Legitimate Consilient constraint versus duplicate content policy

A Consilient core constraint is admitted only when all four statements are true: [asserted]

1. It protects `record_integrity`, `principal_authority` or `private_instance_data`, including a
   boundary the principal configured through a first-party event. [asserted]
2. Its trigger consumes typed operation/effect facts, not topic words, sentiment, a persona or a
   model's confidence. [asserted]
3. It names the source invariant/authority and the executable check that fails on bypass. [asserted]
4. Its admission decision is invariant under a semantic-content change that leaves effects fixed,
   and changes when the protected effect changes while content is held fixed. [asserted]

The required differential fixture is therefore two-by-two: the same local-draft effect with benign
and controversial text must receive the same Consilient disposition; the same text changing from
`local.draft` to `external.publish` must change disposition. A constraint which fails either arm, or
names `content` as its protected asset, is a redundant content policy and cannot enter the core.
[asserted]

This supersedes ADR-0022's proposed Consilient-local topic list as a core implementation mechanism;
it does not weaken the safety training/refusal behaviour of Claude, Codex, Cursor, Grok or another
dispatched model. [asserted]

“Bound by law” is not implemented by a keyword list here. A future legal constraint needs its own
jurisdiction-specific primary source, typed effect facts, verifier and measured error boundary; this
specification makes no claim that model safety is legal compliance. [asserted]

A clearly unlawful action is refused rather than converted into a seventh approval class. Genuine
legal uncertainty triggers retrieval/replanning under the best available evidence; it reaches the
principal only if the proposed effect independently matches one of the six classes. [asserted]

## 7. Friction metric and ratchet

The metric is derived from trajectory events, not a new mutable counter: [asserted]

`avoidable_escalation_ratio = refused_avoidable_attempts / all_escalation_attempts`. [algebra]

An attempt is mechanically avoidable when it is refused because it is outside the closed set, is a
duplicate open request, asks for authority already present in a matching first-party event, or has a
verified local reversible surrogate. The denominator includes delivered, refused, timed-out and
unanswered attempts. When the denominator is zero the result is `unavailable`, never zero. [asserted]

Every report shows the numerator and denominator, delivered/refused counts, six-class distribution,
duplicate/standing-authority/surrogate reasons, timeouts and unavailable state, including explicit
zeros. The ratio is a lower bound on avoidable human work because a wrongly admitted in-set request
is not detected by this classifier. [asserted]

The existing generic `events` projection already stores every valid event, so friction needs a query
and renderer, not a new table or counter. Deleting and replaying the projection must reproduce the
same numerator and denominator. [measured] [asserted]

Non-overlapping windows contain 30 attempted escalations in trajectory order. The first complete
instrumented window establishes the automatic ceiling; each later ceiling is the lower of the prior
ceiling and that window's avoidable count. A higher later count emits a ratchet breach but never asks
the principal to diagnose it. The reported ratio is always calculated directly from the source
events, and a fixture reconstructs it after deleting the SQLite projection. [asserted]

The manually reviewed session baseline is about `3 / 8 = 0.375`, but it predates the event contract
and must not be backfilled as though automatically measured. It is a design prior; the first
prospective window is the operational baseline. [measured] [algebra]

EXP-33 remains the broader 30-day interrupt/affordability experiment. EXP-103 records the new
closed-boundary ratio but uses paired avoidable-attempt count as its confirmatory friction estimand,
so zero treatment attempts remain `ratio=unavailable` without making the comparison undefined. It
also measures the paired bad-outcome question. [measured] [asserted]

## 8. Maximum autonomy while beta is unmeasured

`consil beta` currently reports one human rejection against a minimum of 30, so human-labelled beta
is unestimated. [measured: `consil beta`, 2026-08-22]

Maximum autonomy is therefore **not established safe today**. More autonomous actions create more
opportunities for bad actions; without human-labelled beta, this project cannot estimate how often
its checks accept those bad outcomes. [asserted]

The interim does not add approvals. It permits live autonomous mutation only through the per-action
proof in section 3, within local/restorable state and one Owner/one candidate exposure. It converts an
unproven action into a local draft, snapshot-backed operation or explicit capability gap. Protected
one-way effects still use the closed principal path. [asserted]

This is maximum autonomy over the capability the machine can currently prove, not maximum ambient
permission for an unmediated child process. `routing_orchestration_enabled` remains `false`; current
supervised dispatch with bypass flags is not evidence that external side effects are mediated.
[measured] [asserted]

Aggregate widening requires both EXP-35's reversal-soundness result and EXP-103's non-inferior human
outcome result. Missing conditional human rejections remain `insufficient_safety_evidence`; a zero
count is not beta equal to zero. [asserted]

## 9. Reuse and implementation boundary

No second orchestrator or seventh command is introduced. Future implementation extends: [asserted]

- `scripts/dispatch.py` with the single action/escalation admission and principal-rendering boundary;
  [asserted]
- `events.py` with durable serialised writes, strict effect/escalation records and exact enums;
  [asserted]
- `work_items.py` and `coordination.py` with stable decision/action identities and Owner linkage;
  [asserted]
- `routing.py` with the existing unmeasured-beta refusal, applied to any widening of exposure;
  [asserted]
- `budget.py` with existing spend authority/ceilings rather than a second ledger; [asserted]
- `instructions.py` only for portable explanation and the constraint-admission manifest; its current
  generic “Refuse rather than guess” is narrowed, and prompts do not enforce the boundary. [asserted]

`recall.py` may quote decision/escalation records but remains a bounded projection, never authority.
`routing_orchestration_enabled` stays false, the six-command CLI is unchanged, and product code
retains its AST lock. [asserted]

Policy/schema validation stays in `events.py`; scratch-worktree execution stays at the existing
script/process boundary because the product AST lock forbids subprocess, network and credential
capability in `src/consilient/`. No new CLI surface or executor module is introduced. [asserted]

## 10. Checks that must ship with implementation

The smallest sufficient check set is: [asserted]

1. exact-set/schema tests for effect and escalation enums, including current case/omission/type
   bypasses; [asserted]
2. adapter fixtures that execute forward/inverse and detect undeclared writes; [asserted]
3. action-boundary integration tests proving raw unclassified shell/network/credential/payment/
   external-write paths cannot execute live, including a lying adapter whose undeclared outbound
   attempt is independently observed and refused; [asserted]
4. V0-18 fixtures proving only a first-party response satisfies `principal_authority`; [asserted]
5. the content/effect differential fixture in section 6; [asserted]
6. event durability/concurrency and no-bypass ratchets; [asserted]
7. projection deletion/replay proving identical friction counts and explicit adverse outcomes;
   [asserted]
8. a source scan proving no second principal-delivery path and no blocking out-of-set ask. [asserted]

No implementation claim is made by this specification. All eight checks are same-commit conditions
on the code that introduces the corresponding behaviour. [asserted]

## 11. What would falsify this design

EXP-103 kills the automatic reversible-decision policy if it increases human rejection by more than
its fixed margin, crosses one protected boundary without authority, or fails its reversal-soundness
condition. It also withholds the friction claim if the avoidable ratio does not fall. [asserted]

The cheaper falsifier is one admitted adapter whose forward/inverse proof passes while a protected
effect escapes the manifest. That demonstrates the classifier is observing its own declaration, not
the world, and the affected operation class returns to local-draft-only until a different verifier
exists. [asserted]

## 12. Strongest case against maximum autonomy

Maximum autonomy may be wrong here. If autonomous action `i` has bad-outcome probability `p_i`, the
expected number of bad actions is `sum(p_i)` without any independence assumption; under independence,
the chance of at least one is `1 - product(1 - p_i)`. Doing more therefore increases exposure even
when each decision is individually competent. [algebra]

The machine's own classifier and undo verifier can share the same blind spot; a perfect digest over
an incomplete scope proves the wrong boundary perfectly. A sent message, leaked secret, paid invoice
or reputational effect cannot be made unsent by `git revert`. The current human-labelled beta cannot
quantify this risk, and the append-only instrument proposed to measure friction is presently losing
atomicity under concurrency. [measured] [asserted]

Reversibility itself can also be overvalued: [Shin and Ariely
(2004)](https://doi.org/10.1287/mnsc.1030.0148) found spending to keep options open, while
[Gilbert and Ebert (2002)](https://pubmed.ncbi.nlm.nih.gov/11999920/) found lower satisfaction with
changeable outcomes. This design therefore uses reversal as a safety property, never an objective
to maximise. [cited]

The answer is not that maximum autonomy is safe. It is that approval volume is a poor substitute for
evidence, so the interim bounds effects mechanically and measures the bet prospectively. If EXP-103
or EXP-35 fires against it, the policy contracts without narrating the result away. [asserted]

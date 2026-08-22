# 0075. Prove reversibility, close escalation to six classes, and ratchet friction

**Correction:** R30 is **PARTIAL**, not absent: V0-22/V0-23/V0-24 already validate the shape of
`decision.autonomous` records, but no producer, executed undo proof, escalation boundary, projection
or outcome measurement exists. [measured]

- **Status:** PROVISIONAL — EXP-103 can kill the automatic reversible-decision policy
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (maximum-autonomy and minimum-friction requirement, quoted in the source
  context); Codex dispatch `20260822T122851-29970aed66` (provisional mechanism)
- **Inquiry tier reached:** T1 ground; T3 registered as EXP-103, not run
- **Executable model:** none — the decision uses exact effect classes and executed state equality;
  EXP-103 measures the unknown outcome rates rather than a simulated world value

## Context

The principal specified maximum authority, permission, capability and autonomy by default; models
already carry safety constraints; and the system must not transfer avoidable decisions or approval
work back to him. [measured: `docs/00-context/the-machine-2026-08-22.md`]

ADR-0033 already chose “decide by default” and named user-only classes. The implementation which
later landed is only a schema substrate: `events.py` accepts a syntactically plausible commit id,
argv list or dotted symbol as a reversal without resolving or executing it; `class` may be omitted
or unknown; and no runtime emits a decision event. [measured]

The newest requirement changes two earlier mechanisms. It explicitly includes unrecoverable
deletion/overwrite in the principal set and rejects a second Consilient content policy because child
models already carry safety training. Current `USER_ONLY` instead contains `outside_safety_floor`
and no unrecoverable-state class. [measured] This ADR therefore supersedes ADR-0033's escalation
taxonomy and ADR-0022's proposed Consilient-local topic list where they conflict, while retaining
their evidence and historical text. [asserted]

The design must also fit ADR-0067. A deterministic forward/inverse executor brings observed state
from a different class of facts; a second agent reading the same action description does not. One
Owner and one candidate remain the unmeasured-beta default. [asserted]

## Decision

Consilient will decide every material choice except a protected one-way effect in a closed six-class
set. A state-changing autonomous decision is admitted only when a capability adapter derives a typed
effect manifest and an isolated execution proves that forward then inverse restores the exact
declared starting state without an escaped protected effect. Confidence, agreement, rationale and
exit code are not inputs. [asserted]

### Mechanical reversibility

The adapter, not the model, supplies canonical scope, start-state digests, typed forward invocation,
effect enum, expected result, typed inverse, residual effects and hard ceilings. The controller
recomputes the manifest from the actual invocation. The manifest is an admission declaration rather
than proof of truth: a trusted broker or OS-level outer sandbox independently records and refuses
protected sink attempts. Unknown, absent, mixed-case, padded or non-text classes fail closed.
[asserted]

Before live mutation, the controller creates an isolated copy at the exact start state under that
independent sandbox; denies and logs external transport, credential, payment and out-of-root write
attempts; runs forward; verifies the expected state; runs the inverse; compares canonical digests
for every scoped object; and scans the enclosing admitted root. The proof is bound to the operation,
adapter, start-state, verifier and observer-log digests. A lying-adapter fixture must prove that an
undeclared outbound attempt is observed and refused independently of its manifest. [asserted]

If proof fails, the Owner chooses a versioned adapter, local draft, snapshot-backed form or explicit
capability-gap termination. Proof failure is not an approval class. Existing capability-gap closure
must be changed accordingly: `silent`, `not_implemented` or an unknown refusal cannot require a human
unless its proposed effect independently enters the closed set. [asserted]

### Reversal record

`decision.autonomous` records the stable decision id, existing work-item ticket and proof/live
attempt identities; Owner and actor;
decision, reasoning, rejected option, evidence and falsifier; adapter and effect-manifest digest;
scope and preimage digests; exact secret-free inverse and ceilings; proof environment and verifier
and observer-log digests; forward/inverse/state-equality/escape results; residuals; and live outcome.
Proof and later reversal exercise reuse linked `attempt.outcome` events. No second outcome store or
history rewrite is introduced. [asserted]

`events.py` remains the sole writer, but this record cannot become load-bearing until all event kinds
are process-serialised, flushed and fsynced. On 22 August the real no-bypass ratchet failed at
`95 > 92` after concurrent malformed writes; an undo record which can disappear while its action
survives is not an undo mechanism. [measured]

EXP-35 continues to sample actual inverses and measure reversal misclassification. EXP-103 measures
the distinct paired downstream-outcome and escalation-friction question. [measured] [asserted]

### Closed escalation set

The only top-level escalation classes are: [asserted]

1. `money` — a new debit or metered liability not already covered by exact first-party authority;
   [asserted]
2. `credential` — acquiring, revealing or expanding credential/permission scope; [asserted]
3. `external_exposure` — writing, sending or publishing an artefact/message/non-public instance
   data outside the machine; [asserted]
4. `unrecoverable_state_loss` — deletion or overwrite for which the recovery proof fails; [asserted]
5. `principal_authority` — V0-18 `approval`, `consent`, `gate_lift`, `spend_authorisation` or
   `verdict`; [asserted]
6. `preference` — surviving non-dominated options differ only on a principal-owned preference which
   the frozen acceptance contract cannot settle. [asserted]

Use of prepaid quota, a brokered credential inside existing scope and read-only public retrieval
carrying no non-public data do not create a new principal decision. [asserted]

`feedback.answered` remains principal-authored, skippable task-close evidence. V0-18's authority
list is the five subtypes under `principal_authority`; feedback is not an approval, escalation or
live routing input and cannot satisfy one. Its existing first-party authorship check remains.
`HUMAN_ONLY` remains an authorship set, not a second escalation taxonomy; an exact mapping test sends
its five authority values to `principal_authority` and `feedback` to evidence-only. [measured]
[asserted]

The controller computes disposition and appends one canonical `escalation.attempted` event carrying
delivered or refused before rendering; principal-facing transports accept only a delivered event id;
and the V0-18 first-party authorship path alone accepts the answer. Authority-shaped alias events
which omit `human_decision` are rejected at validation. An unknown class is recorded and refused,
never normalised into permission or rendered as a blocking question. [asserted]

The controller cannot prove from prose alone that a preference is genuine. The admissible mechanical
case requires a frozen objective contract, non-dominance on every declared measurable dimension and
a principal-owned preference dimension; anything weaker remains a machine decision rather than a
new “uncertain” escalation class. [asserted]

Existing capability-gap closure is superseded where it forces `silent`, `not_implemented` or an
unknown refusal to a human. Those states close through machine-owned repair, retry, local surrogate
or defer; only an independently proven protected effect may invoke the principal boundary.
[measured] [asserted]

### Constraint admission

A core Consilient constraint must protect record integrity, principal authority or private instance
data; consume typed effects rather than content/topic words; name its source authority; and ship a
runnable bypass check. [asserted]

The killing differential fixture holds effects fixed while changing semantic content and requires
the same disposition, then holds content fixed while changing `local.draft` to `external.publish`
and requires the disposition to change. A constraint whose decision follows the content arm, whose
protected asset is `content`, or which has no executable bypass check is duplicate content policy
and cannot enter `instructions.INVARIANT_CORE`. [asserted]

Clearly unlawful action remains a refusal floor rather than a seventh approval class. This ADR does
not pretend a keyword rule or child model refusal is legal verification; a future legal constraint
needs jurisdiction-specific primary authority, typed action facts and a measured verifier. [asserted]

Genuine legal uncertainty is researched or replanned; it reaches the principal only when the action
independently matches one of the six classes. [asserted]

The generic instruction “Refuse rather than guess” must be narrowed to malformed evidence and
protected-boundary inputs. On ordinary reversible uncertainty it contradicts the newer rule to decide
at the best estimate and creates exactly the avoidable escalation this ADR measures. [asserted]

### Friction measurement

No mutable counter is added. From trajectory events: [asserted]

`avoidable escalation ratio = refused avoidable attempts / all escalation attempts`. [algebra]

The existing generic event projection carries the source rows; the metric adds a pure query and
renderer, not a table or second counter. [measured] [asserted]

Mechanically avoidable means outside the closed set, duplicate, already answered by matching
first-party authority, or replaceable by a verified reversible surrogate. Delivered, refused,
unanswered and timed-out attempts stay in the denominator; zero attempts is `unavailable`, not zero.
[asserted]

Scratch forward/inverse execution stays in the existing script/process boundary, not the AST-locked
product package; `events.py` owns only policy and record validation. [asserted]

The system reports the raw numerator/denominator and every adverse class. Non-overlapping 30-attempt
windows ratchet the avoidable-count ceiling down to the lowest completed-window count; a later rise is
a harness defect and never a request for the principal to diagnose it. The first prospective window
is the automatic baseline because today's manually reviewed `3/8` predates the event schema and
cannot honestly be backfilled. [measured] [asserted]

EXP-103 uses paired avoidable-attempt count as its confirmatory friction estimand. The ratio remains
descriptive and `unavailable` for a zero denominator, so eliminating every Arm-B attempt is a defined
count reduction rather than an invented `0/0 = 0`. [asserted]

This automatically derived ratio is a lower bound: an admitted in-set ask may still be semantically
avoidable. EXP-103 therefore retains blinded outcome/authority review rather than calling the
controller its own ground truth. [asserted]

### Interim while beta is unmeasured

`consil beta` reports one human rejection against the minimum 30; human-labelled beta is unestimated.
[measured: 2026-08-22]

Maximum autonomy is not established safe. The interim adds no approvals: one Owner may execute one
local/restorable candidate only after the per-action recovery proof; unproven actions are made local
and reversible or terminate as capability gaps; protected one-way effects use the closed principal
path. `routing_orchestration_enabled` remains false. [asserted]

Current dispatch is not enforcement: it gives child harnesses bypass flags, exposes no general action
sink, and does not route their tool effects through this classifier. The policy may be claimed only
after `dispatch.py` mediates those effects or an outer sandbox proves they cannot bypass it.
[measured] [asserted]

## Evidence

- `[measured]` `events.py` defines `decision.autonomous`, three reversal shapes and seven exact
  `USER_ONLY` values; `tests/test_decisions.py` exercises syntax and round-trip only.
- `[measured]` Current validation accepts omitted/unknown decision classes and resolves neither
  reverts, commands nor inverse symbols; no live autonomous-decision producer or sampler exists.
- `[measured]` `consil beta` reported one human rejection and a minimum of 30 on 22 August 2026.
- `[measured]` The current session's manual review found roughly eight escalations, three avoidable;
  all three transferred uncertainty rather than reserved authority.
- `[measured]` The real trajectory no-bypass ratchet currently fails at 95 bypasses against 92,
  while non-budget append has no cross-process lock or fsync.
- `[cited]` [Ao, Gao and Simchi-Levi (2026)](https://arxiv.org/html/2603.26993) show why another
  same-information role adds no decision evidence; executed state is the exogenous signal used
  here.
- `[cited]` [Shin and Ariely (2004)](https://doi.org/10.1287/mnsc.1030.0148) and [Gilbert and Ebert
  (2002)](https://pubmed.ncbi.nlm.nih.gov/11999920/) found costs and misprediction around keeping
  options reversible. Reversibility is therefore a safety property, not an objective to maximise.
- `[algebra]` For action-level bad-outcome probabilities `p_i`, the expected bad-action count is
  `sum(p_i)` without independence; under independence, exposure to at least one is
  `1 - product(1 - p_i)`.
- `[asserted]` Effect manifests plus executed recovery proofs will bound bad consequences better
  than transferring every uncertain decision to the principal.

## Evidence against

- `[measured]` The relevant human-labelled beta is unestimated. This project cannot say how often
  its checks accept bad autonomous outcomes, so “maximum autonomy is safe” would be false today.
- `[asserted]` The model, adapter and undo verifier may share one blind spot. An exact digest over an
  incomplete scope proves the wrong scope exactly; the controller may systematically miss the
  effect that matters.
- `[asserted]` More decisions create more bad actions whenever per-action risk is non-zero. Even a
  lower error rate can yield more total harm after autonomy raises action volume.
- `[asserted]` Undo cannot unsend a message, unpublish private data, recover a revealed credential,
  reverse elapsed time or restore reputation. A misleading “reversible” label can invite riskier
  actions than a simpler permission boundary.
- `[measured]` The trajectory intended to measure and prove the mechanism is currently corruptible
  by concurrent writers. Building more records on it before atomic append is a false foundation.
- `[cited]` Human evidence in ADR-0033 cuts directly against maximising reversibility: people paid to
  retain options and sometimes valued the reversible outcome less.
- `[asserted]` The six classes may omit a genuinely consequential case. Because the list is closed,
  that omission will initially appear as autonomy rather than uncertainty, and may be discovered by
  harm.
- `[asserted]` The content-policy differential can remove a useful domain safeguard whose protected
  interest was poorly specified. The rule favours fewer constraints and therefore needs the same
  adversarial treatment as a rule that adds them.
- `[asserted]` This ADR increases agent authority and is written by an agent. EXP-103 and first-party
  boundary labels, not this record's confidence, must decide whether the mechanism stays.

## Consequences

**Positive** — reversible work proceeds without approval; the principal receives only typed
authority/preference questions; each autonomous mutation carries an executed recovery proof and an
auditable outcome. [asserted]

**Negative** — unmediated capabilities become local-draft-only until adapters and an outer boundary
exist; proof adds latency and compute; exact state comparison is infeasible for some systems; more
autonomous action may create more bad outcomes. [asserted]

**Neutral but load-bearing** — `events.py` remains authority, `dispatch.py` remains the sole outer
runner, `work_items.py`/`coordination.py` retain one Owner, `routing.py` retains unmeasured-beta
refusal, `budget.py` remains refuse-only, and `instructions.py` explains rather than enforces.
[asserted]

## Enforcement

This commit records the specification, ADR, index row and EXP-103 only; it changes no gate, command
or product code. [measured]

Future implementation must ship these checks with the corresponding code: exact effect/escalation
enum tests; real forward/inverse and escaped-write fixtures; resolution of reversal targets; raw
action-path bypass tests; V0-18 first-party response fixtures; content/effect differential fixtures;
atomic/fsynced append and no-bypass ratchets; projection-delete/replay equality for friction; and a
source scan proving no second principal-delivery path. The action-path fixture includes a lying
adapter whose undeclared outbound attempt is independently observed and refused. [asserted]

- **Check:** the named future checks above; none is claimed to exist in this specification-only
  commit. [asserted]
- **Fails CI:** no — no implementation ships in this commit. [measured]
- **Added in the same commit as the implementation:** required; this decision does not authorise an
  implementation without its matching check. [asserted]

## What would overturn this

EXP-103 kills automatic recovery-certified decisions if the treatment exceeds its human-rejection
margin, crosses one protected boundary without first-party authority, or fails the reused EXP-35
reversal condition. It withholds the friction claim unless the avoidable ratio falls. [asserted]

One cheaper counterexample also kills an operation class immediately: a protected side effect escapes
an admitted adapter while its forward/inverse proof passes. The class returns to local-draft-only
until an independent verifier observes the escaped effect. [asserted]

## Publication candidate?

**No.** The central safety claim is unmeasured, the authoritative event writer is not yet durable
under concurrency, and the experiment has not run. [measured] [asserted]

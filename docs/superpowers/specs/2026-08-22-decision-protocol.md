# Structural decision protocol: persist the choice before consequence

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** EXP-106 (equivalent outcomes with greater overhead, worse outcomes, one boundary escape or one protected-authority violation).

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

**Correction:** no dedicated or automatic producer emits `decision.autonomous`, and the valid
trajectory contains zero such events, but the generic `consil record --event` command can manually
append any caller-supplied valid event; “nothing can emit it” would therefore be false. [measured]
ADR-0075 supersedes the old seven-value `USER_ONLY` escalation taxonomy and ADR-0067's generic
irreversibility escalation with a closed six-class boundary. [asserted] ADR-0077 corrects the
candidate result to `n_attempt_max <= 1`, with zero admitted below `beta_upper`. [algebra]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0079 is PROVISIONAL and EXP-106 can kill structural enforcement.
  [asserted]
- **Author:** Codex dispatch `20260822T125137-bc6a412e07`; the requirement to integrate the
  protocol structurally while retaining the skill is the principal's, while the mechanism below is
  this dispatch's provisional design. [measured]
- **Scope:** future wiring of the existing decision event into ADR-0078's effect boundary; no gate,
  CLI command, product implementation or routing flag changes here. [asserted]

## 1. Answer first

The decision record becomes a write-ahead condition of material actuation. ADR-0078's one typed
effect boundary derives the actual effect manifest; ADR-0075 classifies it; the controller durably
appends either a valid `decision.autonomous` record or the ADR-0075-specified protected-action
proposal plus matching first-party authority chain; only then may `effect.intent` make the
capability reachable.
A missing, duplicated, mismatched or non-durable decision/authority chain refuses the effect.
[asserted]

This amends ADR-0075 and ADR-0078 where they place decision disposition after the effect receipt or
say the decision contains the later outcome. That order can record an outcome but cannot make
pre-action reasoning structural. The immutable decision instead preallocates the operation and
receipt identities; the intent carries `decision_id`; and replay joins the later receipt/outcome
without embedding it or rewriting the decision. ADR-0078's manifest, intent, receipt and
reconciliation contracts otherwise stand, except that intent admission becomes a discriminated
union: observation-only intents carry `{kind: observation, observation_id}` and
`decision_id: null`; material intents carry exactly one decision/authority chain. [measured]
[asserted]

This is one extension of the existing boundary, not a second orchestrator, action manifest,
decision kind, outcome store, principal path or CLI command. `events.py` remains the writer;
`dispatch.py`, the capability adapters, work items, coordination, budget and routing retain their
current responsibilities. [asserted]

The structure buys complete-mediation pressure: an omitted record becomes a mechanically visible
refusal instead of an instruction violation nobody notices. It cannot force a good judgement. A
schema can require alternatives, evidence and a falsifier; it cannot prove that they are sincere,
relevant or sound. [asserted]

## 2. The frozen bar and the delta

The pre-registered external bar was frozen before this design was opened. It favours one accountable
owner, provenance-bearing artefacts, explicit alternatives and risks, genuinely exogenous checks,
and independent outcome measurement over role labels, consensus or self-confidence. [measured:
`docs/00-context/agentic-organisation-bar-2026-08-22.md`]

Amazon's primary self-description supplies a retrievable incumbent for single-threaded ownership
and narrative decision artefacts, but no qualifying causal evaluation shows that its memo practice
caused better outcomes. Magentic-One supplies task and progress ledgers, while its own error analysis
records weak verification and risky web actions. [cited: Amazon/AWS 2017 and Microsoft et al. 2024,
both `[FULL]` in `docs/10-research/bibliography.md`,
https://www.aboutamazon.com/news/company-news/2017-letter-to-shareholders and
https://arxiv.org/html/2411.04468, retrieved 2026-08-22]

The frozen search covered human organisation practices, nine agent-system families, controlled
multi-agent comparisons, verifier hacking and execution feedback; it found no controlled test of a
pre-action decision schema which refuses an otherwise executable agent action. No post-freeze
source was added to move that yardstick after this proposal was visible. Absence from that bounded
search is not proof of absence. [measured]

The delta over the plain answer is narrow: combine write-ahead recording from transactional systems
with complete mediation from security engineering, so the selected action cannot outrun its
decision record. The killing measurement is not schema conformance; it is whether that boundary
improves independent outcomes enough to repay its overhead. [asserted]

## 3. What exists and what does not

| Surface | Current fact | Consequence |
|---|---|---|
| Decision schema | `events.py` validates non-empty `decision`, `reasoning`, `falsifier` and one of three typed reversal shapes, and rejects the current legacy `USER_ONLY` values. [measured] | Shape is enforced; existence before action is not. [measured] |
| Producer | `tests/test_decisions.py` constructs fixtures. `consil record` can append a caller-supplied event, but no dispatcher, work-item, routing, budget or instruction path produces one automatically. [measured] | A generic manual writer is not an operating protocol. [asserted] |
| Dispatch | Single and fan-out execution converge on `run_harness()`, which calls `run_process()` without looking up a decision. [measured: `scripts/dispatch.py`] | A harness can launch with no decision record. [measured] |
| Other effects | The unattended loop has a separate `Popen`, and child harness, browser and outbound effects occur beyond the dispatch launch boundary. [measured: `scripts/run_loop.py`, `docs/superpowers/specs/2026-08-22-action-surface.md`] | Gating only `run_harness()` would cover delegation, not every consequential action. [measured] |
| Durability | Ordinary event append is neither process-serialised nor fsynced, and the current bypass ratchet has recorded concurrent malformed writes. [measured: ADR-0075] | A pre-action record which can disappear while its effect survives is not an enforcement boundary. [asserted] |

The generic record command remains an observation surface. A manually appended event grants no
capability: admission also requires a unique operation id, matching work item, manifest and command
digest, correct append order and the authenticated authority/effect facts owned by ADR-0075 and
ADR-0078. [asserted]

## 4. The chokepoint and the rule banning bypass

The general chokepoint sits **inside ADR-0078's single effect boundary**, after the controller has
recomputed the typed manifest and ADR-0075 disposition, but before `effect.intent` exposes any OS
handle, route, credential, provider operation or live target. This position lets consequence drive
the record level and makes the decision a prerequisite of reach rather than a post-hoc explanation.
[asserted]

The fixed order is: [asserted]

1. Resolve the existing capability inventory and recompute the ADR-0078 effect manifest from the
   actual invocation. [asserted]
2. If ADR-0075 needs an isolated forward/inverse proof, admit that trial as its own operation through
   the existing proof process boundary. Before reach, append its minimal decision and intent. Its
   capability contains only a newly created scratch root and verifier log; the independent outer
   sandbox withholds live targets, network, credentials, spend and external transport. Destruction
   of the scratch root plus the enclosing-root scan is its inverse. That sandbox/verifier policy is
   the explicit trusted base; a missing handle restriction or failed scan refuses the live action.
   [asserted]
3. Apply the resulting recovery proof and protected-effect classification to the proposed live
   operation; do not ask on generic uncertainty or proof failure. [asserted]
4. Derive the record level mechanically and durably append the pre-action decision or protected
   proposal. The cross-process append transaction rejects a second decision/proposal for the same
   `operation_id`. If append, flush or fsync cannot be proved, refuse. [asserted]
5. Under the same exclusive admission primitive, resolve the complete discriminated admission chain,
   compare-and-append the first `effect.intent`, fsync it, and issue one single-use capability handle.
   A prior intent, missing chain or failed append refuses; provider idempotency is defence in depth,
   not the uniqueness boundary. [asserted]
6. Append `effect.receipt` and the existing linked `attempt.outcome`. The pre-action decision names
   the operation id; replay joins the later receipt rather than editing history or inventing a
   `decision.outcome` kind. [asserted]

The bypass rule is exact: **no effect primitive may become reachable except through this ordered
boundary. A pure observation is admitted by its own durable intent under the closed observation
predicate below; every material operation requires exactly one earlier valid autonomous decision or
first-party protected-action authority chain.** Validation, operation-id reservation, first-intent
append/durability and single-use handle issuance are one atomic cross-process admission; two callers
cannot consume the same chain. A prompt, an `instructions.assembled` row, a work claim or a manually
recorded event is not admission. [asserted]

For the first implementation slice, `run_harness()` is the existing convergence point immediately
before `run_process()`. It must require the matching durable decision and operation digest before
either process call. That slice remains blocked while the child retains ambient permission-bypass
reach: `process.run` cannot be recovered. It becomes `contained_execution` only when the outer
sandbox grants no live mutable/external handle, accounts for CPU/time/log residuals under frozen
ceilings, proves process-tree termination, and sends every child effect through a separate admitted
operation. `scripts/run_loop.py` and every connector must use the same effect boundary or remain
unable to obtain live reach; otherwise the launch gate is honestly only a delegation gate.
[measured] [asserted]

The outer source/sandbox rule from ADR-0078 remains load-bearing. A child launched with ambient
permission-bypass reach could perform an unrecorded child effect after its launch decision; the
boundary is not complete until the sandbox withholds every unmanifested child capability and the
source ratchet bans raw effect paths elsewhere. [measured] [asserted]

## 5. Scale the record to consequence

Record depth and evidence-squad size are separate. ADR-0067 continues to default to one Owner and
adds a reader only for a different material anchor. ADR-0077 continues to own fusion, dependence
and candidate exposure. The table below changes neither. [asserted]

| Mechanically derived case | Record and action | Human friction |
|---|---|---|
| Pure observation or read-only acquisition. [asserted] | No autonomous-decision record and no invented undo. Its intent carries `{kind: observation, observation_id}` and `decision_id: null`; the later knowledge/usage record links that id. [asserted] | None. [asserted] |
| Contained local computation or `process.run` with no live mutable/external handle and separately admitted child effects. [asserted] | A material launch uses `decision.autonomous`; every mechanical verifier gets a unique child `operation_id` plus `parent_operation_id` and may reuse the parent's decision id. The receipt proves process-tree termination and records bounded CPU/time/log residuals without calling them reversed. [asserted] | None; an uncontained process is a capability gap. [asserted] |
| An isolated ADR-0075 recovery proof with only its new scratch root and verifier log reachable. [asserted] | Append a minimal `decision.autonomous` for a unique `proof_operation`; its receipt supplies the proof result to the separate live-operation decision. [asserted] | None; missing containment is a capability gap. [asserted] |
| A material choice with no live effect. [asserted] | Append `decision.autonomous`; ADR-0072's work-item readiness projector refuses any dependent contract or claim without that earlier id and matching decision digest. Its reversal is `{kind: inverse, value: consilient.events.supersede_decision}`; a later decision links `supersedes`. [asserted] | None. [asserted] |
| A non-protected state mutation admitted by ADR-0075's executed recovery proof. [asserted] | Append `decision.autonomous`, then use the atomic admission above. A failed proof instead selects a transactional adapter, local draft, snapshot or capability-gap termination. [asserted] | None; asking on proof failure is a defect. [asserted] |
| A protected class with exact matching first-party standing authority. [asserted] | Append the ADR-0075-specified full proposal, bind the prior authority event, and admit atomically. Never emit `decision.autonomous` for the reserved class. [asserted] | None; a duplicate question is an avoidable escalation. [asserted] |
| A protected class without matching standing authority. [asserted] | Append and deliver the ADR-0075-specified full proposal; only a valid first-party response can complete the chain before intent. [asserted] | One bounded question to the principal. [asserted] |

This corrects the brief's shorthand: generic irreversibility is not a seventh escalation class. A
non-restorable operation is reshaped, kept local or closed as a capability gap unless its typed
effects independently enter ADR-0075's closed six-class set. [asserted]

The pure-observation predicate is closed: effects are a non-empty subset of `data.read` and
`network.call`; scope and provider operation are read-only; the request sends no non-public bytes;
any broker reference is already authorised and never revealed; there is no new metered liability,
mutable child or other effect enum; and the broker independently confirms those facts. Anything
else cannot use `decision_id: null`. [asserted]

The admission class is the closed enum `observation`, `contained_execution`, `proof_operation`,
`material_choice`, `recoverable_mutation`, `protected_covered`, `protected_uncovered` or
`capability_gap`. The controller derives it from the effect enum, outer-sandbox reach, executed
proof, canonical scope/residuals and exact first-party authority join; unknown or missing input is
`capability_gap`. Record depth is independently `minimal` unless the versioned conservative
Better-Than-Best proxy threshold fires or the class is protected, in which case it is `full`. Thus a
full protected proposal may still record `protocol: not_warranted`. Confidence, stated difficulty,
agreement and prose claims about reversibility are excluded. [asserted]

## 6. Record reasoning and planning in the existing event

Extend `decision.autonomous`; do not add a parallel decision event. Before action, every autonomous
record carries these common fields: [asserted]

- stable `decision_id`, `operation_id`, work-item ticket, Owner and actor; [asserted]
- `record_level` equal to `minimal` or `full`, derived by the controller; [asserted]
- the existing `decision`, `reasoning`, `falsifier` and typed `reversal`; [measured] [asserted]
- `alternatives`, a list of `{option, rejected_because}` objects; [asserted]
- immutable evidence/result references, not copied verifier payloads; [asserted]
- the acceptance-contract digest; and [asserted]
- `protocol`, recording whether `better-than-best` was `not_warranted` or `completed`, the
  mechanical threshold inputs, the `instructions.assembled` reference, bar reference and killing
  check when completed. [asserted]

The remaining binding is discriminated by admission class. `material_choice` has no invented effect
or proof digest. `proof_operation` and `contained_execution` carry the effect-manifest,
sandbox/verifier-policy and expected-receipt digests but no future result. `recoverable_mutation`
carries those fields plus the already completed recovery-proof digest. Later receipts/outcomes point
back to the decision and never backfill it. [asserted]

At either depth, `alternatives` contains only options actually evaluated. When one admissible path
exists, it may be empty only alongside `only_admissible`, whose non-empty `rule_refs` identify the
closed effect, authority or accepted-answer rules that eliminated every other path. This explicitly
amends ADR-0075's unconditional rejected-option clause; fabricated losers are worse than an honest
deterministic disposition. [asserted]

The `falsifier` remains what would change the answer. The later `effect.receipt` and
`attempt.outcome` show what happened; they do not rewrite the prior reasoning. A superseding
decision links the earlier `decision_id`, preserving reversal and dissent. [asserted]

For a protected class, the same nested planning shape is validated inside ADR-0075's already
specified escalation event, but it is explicitly a proposal. The principal's first-party event is
the decision. Reusing the shape does not weaken V0-23 or create an agent-authored reserved decision.
[asserted]

## 7. Evidence class as computable data

This is feasible, but a provenance tag is not an evidence class. `[measured]`, `[cited]`,
`[simulated]`, `[algebra]` and `[asserted]` describe how a claim is warranted; they do not identify
the truth-relevant anchor. Two independent executed tests can both be `[measured]`, while two
different prose tags can still derive from one source. Treating tag inequality as independence
would make echo computable incorrectly. [asserted]

The decision therefore stores immutable `evidence_refs` of exactly
`{event_id, event_kind, event_sha256}`. Every referenceable event gains a stable id; the atomic
writer rejects a reused id, and replay fails closed on historical duplicates. `event_sha256` binds
the canonical complete earlier event without serving as its identity. Legacy rows without an id are
`unmeasured` inputs and cannot satisfy structural admission. Replay then reads whatever provenance,
`evidence_class`, anchor/hash and dependence metadata that source kind actually validates.
ADR-0077's specified `verification.outcome` owns verification class, calibration and correlation;
this protocol only records which inputs the Owner used and how each alternative was disposed. It
neither copies likelihood weights nor creates a second fusion table. [asserted]

The projection can then report repeated classes, shared anchors, missing references and unmeasured
dependence. A repeated class is a possible echo/dependence flag, not an automatic rejection;
ADR-0077 deliberately permits repeated observations so their correlation can be measured. A
different label is never proof of independence. [asserted]

When `knowledge.retrieved`, `attempt.outcome` or another referenced kind lacks a validated class,
anchor or dependence identity, replay returns `unmeasured` for that property and never infers
independence from the actor or label. Do not widen `events.PROVENANCE`: it is the three-value
usage/spend provenance guard, not a general claim-tag enum. The implementation cost is canonical
event hashing, reference validation against earlier events and replay joins. Storage cost is small;
classification and dependence error are the real cost. [measured] [asserted]

## 8. The skill stays and does the judgement

`.agents/skills/better-than-best/SKILL.md` remains unchanged and remains the procedure which shapes
the judgement. Code decides only whether its own three documented threshold conditions are met and
whether the required output references exist. It does not reimplement the five stages. [measured]
[asserted]

The threshold uses three versioned conservative proxies for the skill's semantic test; it does not
claim to compute meaning: [asserted]

1. **A decision turns on the answer:** the work-item dependency/effect contract contains at least
   one typed `later_work`, `money`, `public_claim` or `design_constraint` consumer. [asserted]
2. **The question is open:** a complete lookup of the generated decision/document index finds no
   verified answer with the same question, scope and version digests. Bounded or condensed recall
   cannot prove absence; it triggers index repair/retrieval and remains `unknown` if completeness
   still cannot be established.
   [asserted]
3. **Being wrong costs more than the protocol:** the frozen downstream-rework ceiling exceeds the
   versioned protocol-cost ceiling under the same accepted review-adjusted-minutes policy. Missing,
   incomparable or unversioned cost inputs yield `unknown`, not model discretion.
   [asserted]

When all three are true, or none is false and at least one is `unknown`, `instructions.py` selects
the existing skill conservatively and the pre-action record must
reference an earlier `instructions.assembled` for the same task containing the exact skill name,
path and digest whose body reconstructs from the pinned tree, plus bar, search and killing-check
artefacts. When any condition is false, the record
— minimal or full according to admission class — records which one and requires no completion
artefacts. Nobody is asked to decide whether the skill feels worthwhile. [asserted]

This records that the skill was loaded and that its required outputs exist. It cannot prove that an
agent genuinely performed the reasoning rather than manufacturing compliant text. That is the
central limit, not an implementation detail. [asserted]

## 9. Enforcement that must ship with implementation

Durable process-serialised append/fsync and ADR-0078's outer effect boundary are prerequisites. The
decision protocol must not be described as structural while either is absent. [measured]
[asserted]

The implementation commit must include these checks: [asserted]

1. `tests/test_decision_protocol.py::test_action_boundary_refuses_without_matching_pre_action_decision`
   proves absent, duplicate, malformed, mismatched and post-action records refuse before the fake
   effect primitive is reached. [asserted]
2. `tests/test_dispatch.py::test_run_harness_refuses_before_launch_without_a_matching_recorded_decision`
   binds the first live launch slice to work item, run, command/manifest digest and append order.
   [asserted]
3. `tests/test_v0_invariants.py::test_no_effect_path_bypasses_action_and_decision_admission`
   scans the complete tracked executable tree and dependency closure for raw process, filesystem,
   network, message, provider, credential and money sinks outside the one broker/boundary allowlist.
   The sandbox fixture separately attempts an undeclared child effect and proves it is denied.
   [asserted]
4. Conditional schema tests derive admission class and record depth from frozen manifests; validate
   alternatives or `only_admissible` at both depths; require skill completion artefacts exactly when
   `protocol == completed`; reject reserved autonomous decisions; and keep confidence out of the
   input. [asserted]
5. Replay tests reject duplicate `event_id`, resolve every id/hash reference, preserve missing/
   refused/timeout outcomes and reproduce the same decision-to-effect joins after deleting
   projections. [asserted]
6. Concurrency/crash tests prove the decision and intent are durable before reach; one lost record
   or effect outside the admitted order fails the boundary. Two concurrent admissions for one
   operation must reach the fake primitive exactly once. [asserted]
7. A skill-binding test proves a firing threshold has an earlier same-task
   `instructions.assembled` row containing the exact Better-Than-Best name, path and digest and that
   `instructions.reconstruct()` verifies its body; a non-firing threshold requires none of its
   completion artefacts. [asserted]
8. `tests/test_work_items.py::test_material_choice_cannot_make_dependent_item_ready_without_prior_decision`
   proves ADR-0072 readiness and claim issuance refuse an absent, late or digest-mismatched decision;
   the executable-tree ratchet bans another binding consumer. [asserted]

The source ratchet is the rule banning bypass. Functional tests alone prove the known path; the AST
check makes a newly added second path fail the same commit in which it appears. [asserted]

## 10. Evidence against: leave this as a skill

The strongest case is that structural enforcement produces box-ticking rather than thought. An
agent can emit a plausible losing option, a vague falsifier and an executable-looking inverse more
cheaply than it can reconsider a decision. The present validator already accepts a nonexistent
commit, unavailable command or unresolved dotted symbol because it checks shape, not reality.
[measured]

A registered-report experiment on explicit code-review strategies found no general effectiveness
gain from the guided checklist and lower effectiveness on one change after controls; both checklist
interfaces received poor usability grades. Its participants, task and human-review setting do not
establish transfer to agents, but it is direct counter-evidence to the assumption that forcing a
structured checklist improves judgement. [cited: Wurzel Gonçalves et al. 2022,
https://doi.org/10.1007/s10664-022-10123-8, `[FULL]` in
`docs/10-research/bibliography.md`]

The hard gate also creates a new failure mode: a correct, time-sensitive action can be refused
because its record is malformed, while a wrong action with polished fields passes. More fields add
tokens, latency, storage and verifier surface; the full protocol can become ceremony that agents
learn to satisfy and humans learn to ignore. [asserted]

That objection is not answered by a richer schema. The proposed answer is narrower: enforce only
pre-action existence, binding, ordering and mechanically derived tiers; keep the skill as the place
where judgement happens; and let EXP-106 decide whether even that enforcement earns its cost. If
outcomes are equivalent and overhead is higher, the hard decision gate is removed and the protocol
stays a skill. [asserted]

## 11. What structure buys, and what it cannot

**It buys:** a durable before/after causal order; refusal on omission; exact linkage among work,
decision, effect and outcome; mechanical routing of routine versus full protocol; visible
alternatives, falsifiers and skill use; and replayable evidence/dependence references. [asserted]

**It cannot buy:** sound reasoning, genuine consideration of alternatives, a meaningful falsifier,
correct evidence classification, independent inputs, a sound recovery proof, legal judgement,
principal authority, low beta or a good outcome. Those require execution, primary sources,
independent verdicts and measurement. [asserted]

EXP-106 compares the same Owner, skill, tools, controller and budget with and without the hard
pre-action record requirement. It kills structural enforcement on equivalent outcomes with greater
overhead, worse outcomes, one boundary escape or one protected-authority violation. [asserted]

## 12. Plain answer and delta

The plain answer is “call `events.append()` before `run_harness()` and keep the skill”. That is the
correct first slice, but it is not a complete chokepoint because the unattended loop, child tools and
connectors can still act elsewhere. [measured] [asserted]

The added delta is to place the record inside ADR-0078's already required complete effect boundary,
derive its depth from ADR-0075 rather than model confidence, reference ADR-0077 evidence instead of
duplicating fusion, and pre-register the result that would send the whole structural layer back to
the skill. [asserted]

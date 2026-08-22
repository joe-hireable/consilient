# 0079. Require a durable decision before material actuation and keep judgement in the skill

**Correction:** there is no dedicated or automatic `decision.autonomous` producer and the valid
trajectory contains zero such events, but `consil record --event` can manually append a valid
caller-supplied one; the missing property is automatic pre-action enforcement, not literal
emitability. [measured]

- **Status:** PROVISIONAL — EXP-106 can remove the hard decision gate and leave the protocol as a
  skill
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (structural-integration and keep-the-skill requirement); Codex dispatch
  `20260822T125137-bc6a412e07` (provisional mechanism)
- **Inquiry tier reached:** T1 ground; T3 pre-registered as EXP-106, not run
- **Executable model:** none — the boundary and conditional schema are exact; EXP-106 measures the
  unknown outcome and overhead effects

## Context

`events.py` already validates the shape of `decision.autonomous`: decision, reasoning and falsifier
must be non-empty, reversal must have one of three executable-looking shapes, and the current legacy
`USER_ONLY` values cannot be recorded as autonomous. `tests/test_decisions.py` proves those schema
properties. [measured]

No dispatcher, work-item, routing, budget or instruction path automatically produces the event.
Single and fan-out execution converge on `run_harness()` and reach `run_process()` without a
decision lookup; the unattended loop and connectors expose further effect paths. `events.append()`
can validate a record but cannot require a later action to have one. [measured]

ADR-0075 now owns executed recovery, the closed six-class principal boundary and friction. ADR-0078
owns typed effects, least-privilege reach and write-ahead effect intent/receipts. ADR-0077 owns
evidence fusion, dependence and candidate exposure. A decision protocol which rebuilds any of those
would create another path to the same authority and repeat the bypass failure this project records.
[measured] [asserted]

ADR-0075's closed set also amends ADR-0067 where that older ADR sends generic irreversible action to
the principal. Proof failure is reshaped or closed as a capability gap unless an independently
derived effect enters the six-class boundary. [asserted]

ADR-0075 and ADR-0078 currently place decision disposition after the effect receipt or say the
decision contains/references the later live outcome, even though `effect.intent` already carries
`decision_id`. That order supports an audit but cannot refuse an action for missing pre-action
reasoning, and an immutable pre-action event cannot contain a later result. This ADR amends those
clauses: the decision preallocates operation/receipt identity and precedes intent and reach; replay
joins the later receipt/outcome without embedding it or rewriting the decision. ADR-0078's manifest,
intent, receipt and reconciliation contracts otherwise stand, except that intent admission becomes
a discriminated union: observation-only intents carry `{kind: observation, observation_id}` and
`decision_id: null`; material intents carry exactly one decision/authority chain. [measured]
[asserted]

The frozen external bar asks for one accountable owner, provenance-bearing artefacts, explicit
alternatives and risks, exogenous checks and independent outcome measurement. Amazon's narrative
practice and Magentic-One's ledgers are retrievable incumbents, but neither supplies causal evidence
that a hard pre-action schema improves agent decisions. [cited: Amazon/AWS 2017 and Microsoft et al.
2024, https://www.aboutamazon.com/news/company-news/2017-letter-to-shareholders and
https://arxiv.org/html/2411.04468, `[FULL]` in `docs/10-research/bibliography.md`, retrieved
2026-08-22] [asserted]

This is a protocol boundary with broad future dependence and a genuine risk of adding ceremony.
The decision is therefore provisional rather than accepted. [asserted]

## Decision

Every material effect will be refused unless ADR-0078's single action boundary can resolve exactly
one matching, durable, earlier decision chain. For an autonomous action that chain contains
`decision.autonomous`; for an ADR-0075 protected class it contains the full proposal and the
existing first-party authority event. No new decision kind, orchestrator, manifest, outcome store,
principal path or CLI command is introduced. [asserted]

The check sits after the actual typed effect manifest and ADR-0075 disposition are derived, but
before `effect.intent` exposes the capability. The order is decision, effect intent, reach, effect
receipt and existing attempt outcome. Every row shares stable work-item, operation and decision
identity; replay joins later results without editing the pre-action record. [asserted]

Every adapter invocation resolves one discriminated admission. A pure observation is admitted by its
own durable intent under a closed predicate; material work requires one earlier autonomous decision
or protected proposal plus first-party authority. This explicitly amends ADR-0078's universal
non-null `decision_id` contract without exempting reads from intent/receipt or the action boundary.
[asserted]

ADR-0075's scratch recovery proof is itself a bounded effect. The controller first emits an
automatic minimal decision and intent for that isolated proof operation. Its single-use capability
contains only a new scratch root and verifier log; the independent outer sandbox withholds every
live target, network, credential, spend and external transport. Scratch deletion plus the enclosing-
root scan is the inverse. This sandbox/verifier policy is the explicit trusted base; the resulting
proof informs the separate live-action record. [asserted]

The bypass rule is: **no material effect primitive becomes reachable except through the ordered
action-and-decision boundary.** Chain validation, operation-id reservation, first-intent append and
fsync, and issuance of one single-use handle are one atomic cross-process admission; two callers
cannot consume the same decision. `run_harness()` is the first current launch slice immediately
before `run_process()`, but gating it alone is not the universal property: `run_loop.py`, child
effects and connectors must use the same boundary or remain unable to obtain live reach. [measured]
[asserted]

Because `process.run` cannot be unrun, the named `run_harness()` slice stays blocked while a child
has ambient permission-bypass reach. It becomes `contained_execution` only after the outer sandbox
withholds all live mutable/external handles, every child effect receives its own admission, bounded
CPU/time/log residuals are recorded, and process-tree termination is proved. Containment is not
mislabelled as restoration. [measured] [asserted]

Record depth is derived mechanically: [asserted]

1. Pure observation/read-only acquisition uses existing knowledge/usage records and no invented
   undo. Its intent uses `{kind: observation, observation_id}` and `decision_id: null`; the later
   knowledge/usage record links that id. This variant is valid only when effects are a non-empty
   subset of `data.read` and `network.call`, operations are read-only, no non-public request bytes,
   new metered liability, mutable child or other effect exists, and the broker confirms the facts.
   [asserted]
2. Contained local computation has no mutable/external handle and admits every child effect
   separately. A material launch receives `decision.autonomous`; every mechanical verifier receives
   a unique child `operation_id` plus `parent_operation_id` and may reuse the parent's decision id.
   An uncontained process is a capability gap. [asserted]
3. An isolated ADR-0075 recovery proof uses the `proof_operation` class and receives a minimal
   `decision.autonomous`; its receipt supplies the proof result to the separate live-operation
   decision. Anything beyond the new scratch root and verifier log is a capability gap. [asserted]
4. A material choice with no live effect emits `decision.autonomous`; ADR-0072's work-item readiness
   projector refuses a dependent contract or claim without that earlier id and matching decision
   digest. Its existing reversal shape is
   `{kind: inverse, value: consilient.events.supersede_decision}`; a later decision links
   `supersedes` without erasing history. [asserted]
5. A non-protected mutation emits `decision.autonomous` and reaches the atomic boundary only after
   ADR-0075's proof. Failure selects a transactional adapter, local draft, snapshot or capability
   gap, never an uncertainty-based ask. [asserted]
6. A protected class with exact first-party standing authority emits the full proposal, binds that
   authority and proceeds without another question. Without standing authority it delivers one
   bounded proposal and waits for a valid first-party response. Neither case emits
   `decision.autonomous`. Generic irreversibility is not a seventh class. [asserted]

The admission enum is `observation`, `contained_execution`, `proof_operation`, `material_choice`,
`recoverable_mutation`, `protected_covered`, `protected_uncovered` or `capability_gap`, derived from
typed effects, sandbox reach, executed recovery, scope/residuals and exact authority joins; missing
input is `capability_gap`. Record depth is independently `minimal` unless the versioned conservative
Better-Than-Best proxy threshold fires or the class is protected, when it is `full`. A full
protected proposal may therefore record
`protocol: not_warranted`. Confidence, agreement, role count and stated difficulty are not inputs.
ADR-0067's default one Owner and ADR-0077's exposure policy remain unchanged. [asserted]

The existing decision event is extended with stable decision/operation/work-item identity,
`record_level`, alternatives with reasons they lost, immutable evidence references, an acceptance-
contract digest and a `protocol` record. Its class binding is discriminated: `material_choice` has
no effect/proof digest; `proof_operation` and `contained_execution` bind manifest, sandbox/verifier
policy and expected receipt but no future result; `recoverable_mutation` also binds the already
completed proof digest. Later outcomes point back and never backfill the decision. At either depth,
an empty alternative list requires `only_admissible.rule_refs` naming the rules which eliminated
every other path. This explicitly amends ADR-0075's unconditional rejected-option clause and does
not reward fabricated losers. The existing `falsifier` records what would change the answer.
[asserted]

The protected proposal reuses the same nested planning validator inside ADR-0075's already specified
escalation event. It is not an autonomous decision; only the principal's first-party event supplies
reserved authority. [asserted]

Evidence provenance and evidence class remain distinct. Each decision reference is exactly
`{event_id, event_kind, event_sha256}`. Every referenceable event gains a unique stable id enforced
by atomic append/replay; the hash binds canonical content but is not identity. Legacy rows without an
id are `unmeasured` and cannot satisfy admission. Replay reads only metadata validated by that event
kind; missing class, anchor or dependence data is `unmeasured`, never inferred from actor or label.
ADR-0077's specified `verification.outcome` remains the owner of fusion data. This makes repeated
classes, shared anchors and missing links queryable without copying correlation weights or building
another fusion table. Do not widen the usage/spend-specific `events.PROVENANCE` set. [asserted]

`.agents/skills/better-than-best/SKILL.md` stays. The structural layer uses conservative versioned
proxies for its three semantic conditions: a typed later-work/money/public-claim/design-constraint
consumer relies on the answer; a complete generated-index lookup finds no verified same-question/
scope/version answer; and the frozen downstream-rework ceiling exceeds the versioned protocol-cost
ceiling under one review-adjusted-minutes policy. Each proxy returns true, false or unknown;
condensed recall and missing/incomparable inputs are unknown. All true, or no false plus at least one
unknown, runs the skill conservatively. Then `instructions.py` selects the skill and the decision
references an earlier same-task `instructions.assembled` containing its exact name, path and digest;
the body reconstructs from the pinned tree and includes the bar, search and killing-check outputs.
Any false condition skips it; the record, at whichever depth the admission class requires, records
the false condition and needs no completion artefacts. [measured] [asserted]

No safety claim attaches until ordinary event append is process-serialised, flushed and fsynced and
ADR-0078's source/sandbox bypass checks pass. A record that can disappear while its effect survives
is not structural enforcement. [measured] [asserted]

## Evidence

- `[measured]` `events.py` defines and validates `decision.autonomous`; `tests/test_decisions.py`
  covers shape and round-trip.
- `[measured]` The valid local trajectory contains zero `decision.autonomous` events.
- `[measured]` `consil record --event` is a generic manual append path, not an automatic decision
  producer and not an authority grant.
- `[measured]` Both normal and fan-out dispatch call `run_harness()`, which reaches `run_process()`
  without a decision record; `scripts/run_loop.py` and connector effects are separate paths.
- `[measured]` Ordinary append is not fsynced or fully process-serialised, and ADR-0075 records the
  current no-bypass ratchet above its baseline.
- `[measured]` ADR-0075, ADR-0077 and ADR-0078 already specify recovery/escalation, fusion and typed
  effect admission respectively.
- `[cited]` Amazon/AWS describe single-threaded ownership and narrative decisions, without a
  qualifying causal evaluation of the practice. Primary pages read 2026-08-22.
- `[cited]` Microsoft et al. (2024), *Magentic-One*, arXiv:2411.04468, use task/progress ledgers and
  report risky web action and verification failure modes.
- `[asserted]` A durable record bound to the actual operation and checked before reach is more
  enforceable than prose guidance or a post-action audit row. EXP-106 is the killing test.

## Evidence against

- `[measured]` Current decision validation proves only shape. A nonexistent commit, unavailable
  command or unresolved dotted symbol can satisfy its reversal field; richer prose fields would
  remain equally gameable without execution.
- `[cited]` Wurzel Gonçalves et al. (2022), https://doi.org/10.1007/s10664-022-10123-8,
  found no general
  effectiveness gain from a guided code-review checklist and lower effectiveness on one change
  after controls; both checklist interfaces had poor usability. The novice-heavy human review
  setting limits transfer, but it directly challenges “more required structure means better
  judgement”.
- `[asserted]` Structural enforcement can optimise agents for schema compliance: plausible losing
  options, falsifiers and rationales may be filler produced after the choice was already made.
- `[asserted]` The boundary can refuse a correct time-sensitive action for a record defect while a
  wrong decision with polished fields passes. It adds tokens, latency, storage, validation and a
  new availability dependency on the trajectory writer.
- `[asserted]` The Better-Than-Best skill already contains an anti-ceremony threshold and can evolve
  its judgement procedure without a schema migration. Leaving the protocol there is cheaper and may
  produce the same outcomes.
- `[asserted]` This objection is conceded unless EXP-106 defeats it. The schema is deliberately
  limited to presence, binding, ordering and mechanical tiering; if outcomes are equivalent and
  overhead is higher, the hard gate is removed and the protocol remains a skill.

## Consequences

**Positive** — omission becomes refusable; every material effect is linked to a prior choice,
alternatives, falsifier, evidence and reversal; routine decisions remain automatic; protected
authority remains first-party; skill use and possible echo become replayable. [asserted]

**Negative** — every admitted effect now depends on the availability and durability of the record
boundary; full records consume time and tokens; schema-valid filler may create false assurance; a
complete sandbox/adapter boundary is required before the invariant is true. [asserted]

**Neutral but load-bearing** — ADR-0075 owns recovery/escalation, ADR-0077 owns fusion, ADR-0078 owns
effect reach, `events.py` owns the record, `dispatch.py` remains the outer runner, and the existing
skill remains the judgement procedure. `routing_orchestration_enabled` stays false and the
six-command CLI is unchanged. [asserted]

## Enforcement

This documentation commit implements no boundary and changes no gate, command or product code.
[measured]

- **Check:** future implementation must add
  `tests/test_decision_protocol.py::test_action_boundary_refuses_without_matching_pre_action_decision`
  and prove absent, duplicate, malformed, mismatched and late records refuse before a fake effect is
  reached. [asserted]
- **Check:** the first dispatch slice adds
  `tests/test_dispatch.py::test_run_harness_refuses_before_launch_without_a_matching_recorded_decision`.
  [asserted]
- **Bypass check:**
  `tests/test_v0_invariants.py::test_no_effect_path_bypasses_action_and_decision_admission`
  scans the complete tracked executable tree and dependency closure for raw sinks outside the one
  broker/boundary allowlist; an outer sandbox fixture proves an undeclared child effect cannot
  escape. [asserted]
- **Ordering/durability check:** concurrent/crash fixtures prove decision then intent are durable
  before reach, replay reconstructs the same decision/effect/outcome chain, and two concurrent
  admissions for one operation reach the fake primitive exactly once. [asserted]
- **Conditional schema:** alternatives or `only_admissible` validate at both depths; skill
  completion artefacts are required exactly when `protocol == completed`, not merely because a
  protected proposal is `full`. [asserted]
- **Skill binding:** a firing threshold requires an earlier same-task `instructions.assembled` row
  containing the exact Better-Than-Best name, path and digest and a passing
  `instructions.reconstruct()` body check; a non-firing threshold requires none of its completion
  artefacts. [asserted]
- **Planning binding:**
  `tests/test_work_items.py::test_material_choice_cannot_make_dependent_item_ready_without_prior_decision`
  refuses absent, late and digest-mismatched decisions before ADR-0072 readiness or claim issuance;
  the executable-tree ratchet bans another binding consumer. [asserted]
- **Evidence identity:** append/replay rejects duplicate `event_id` and every decision reference
  resolves both id and canonical content digest. [asserted]
- **Fails CI:** no — no implementation ships in this commit. [measured]
- **Added in the same commit as the implementation:** required. [asserted]

## What would overturn this

EXP-106 removes the hard pre-action decision gate if the structurally enforced arm has equivalent
independent outcomes with greater overhead, worse outcomes, one protected-authority violation or one
effect-boundary escape. The existing schema may remain as an optional audit format, and the skill
continues to guide judgement. [asserted]

A cheaper counterexample also blocks activation: one material effect becomes reachable before its
matching durable decision, one manual event grants capability without matching operation facts, or
one protected class is recorded as autonomous. [asserted]

Passing EXP-106 would establish only a benefit for its frozen task mixture and versioned boundary.
It would not prove good reasoning, evidence independence, legal correctness, low beta or universal
transfer. [asserted]

## Publication candidate?

**No.** The boundary is unimplemented, its event writer is not yet durable under concurrency, and
the decisive experiment has not run. [measured] [asserted]

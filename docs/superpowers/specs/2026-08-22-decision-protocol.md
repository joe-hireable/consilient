# Structural decision protocol: persist the choice before consequence

**Correction:** no dedicated or automatic producer emits `decision.autonomous`, and the valid
trajectory contains zero such events, but the generic `consil record --event` command can manually
append any caller-supplied valid event; “nothing can emit it” would therefore be false. ADR-0075
also supersedes the old seven-value `USER_ONLY` escalation taxonomy, and ADR-0077 corrects the
candidate result to `n_attempt_max <= 1`, with zero admitted below `beta_upper`. [measured]
[algebra]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0079 is PROVISIONAL and EXP-104 can kill structural enforcement.
  [asserted]
- **Author:** Codex dispatch `20260822T125137-bc6a412e07`; the requirement to integrate the
  protocol structurally while retaining the skill is the principal's, while the mechanism below is
  this dispatch's provisional design. [measured]
- **Scope:** future wiring of the existing decision event into ADR-0078's effect boundary; no gate,
  CLI command, product implementation or routing flag changes here. [asserted]

## 1. Answer first

The decision record becomes a write-ahead condition of material actuation. ADR-0078's one typed
effect boundary derives the actual effect manifest; ADR-0075 classifies it; the controller durably
appends either a valid `decision.autonomous` record or the existing protected-action escalation
record; only then may `effect.intent` make the capability reachable. A missing, duplicated,
mismatched or non-durable decision refuses the effect. [asserted]

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
both `[FULL]` in `docs/10-research/bibliography.md`, retrieved 2026-08-22]

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
2. Apply ADR-0075's recovery proof and protected-effect classification; do not ask on generic
   uncertainty or proof failure. [asserted]
3. Derive the record level mechanically and durably append the pre-action decision or protected
   proposal. If append, flush or fsync cannot be proved, refuse. [asserted]
4. Append `effect.intent` with the same `operation_id` and `decision_id`, then expose the minimum
   capability handle and execute once. [asserted]
5. Append `effect.receipt` and the existing linked `attempt.outcome`. The pre-action decision names
   the operation id; replay joins the later receipt rather than editing history or inventing a
   `decision.outcome` kind. [asserted]

The bypass rule is exact: **no material effect primitive may become reachable except through this
ordered boundary, and every admitted operation must reference exactly one earlier valid decision or
first-party protected-action authority chain.** A prompt, an `instructions.assembled` row, a work
claim or a manually recorded event is not admission. [asserted]

For the first implementation slice, `run_harness()` is the existing convergence point immediately
before `run_process()`. It must require the matching durable decision and operation digest before
either process call. `scripts/run_loop.py` and every connector must use the same effect boundary or
remain unable to obtain live reach; otherwise the launch gate is honestly only a delegation gate.
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
| No material choice and an empty effect set, such as projection or observation through an existing read event. [asserted] | No autonomous-decision record. Existing knowledge, usage or work-item events retain provenance. [asserted] | None. [asserted] |
| ADR-0075 proves recovery; all effects, residuals, loss and reversal cost fit the frozen task-local ceilings; no protected class is present. [asserted] | Append a **minimal** `decision.autonomous` record automatically. Run no full Better-Than-Best protocol. [asserted] | None; asking is a defect. [asserted] |
| No protected class is present, but consequence exceeds the routine ceiling, reversal is costly, or the structured Better-Than-Best threshold fires. [asserted] | Append a **full** `decision.autonomous` record, including genuine alternatives and the skill result. Execute autonomously only if ADR-0075's proof passes. [asserted] | None. Proof failure becomes a transactional adapter, local draft, snapshot or capability gap, not an ask. [asserted] |
| ADR-0075 derives one of `money`, `credential`, `external_exposure`, `unrecoverable_state_loss`, `principal_authority` or `preference`. [asserted] | Record the full proposal inside ADR-0075's `escalation.attempted` path and wait for the existing first-party authority event. Never emit `decision.autonomous` for the reserved class. [asserted] | One bounded question to the principal. [asserted] |

This corrects the brief's shorthand: generic irreversibility is not a seventh escalation class. A
non-restorable operation is reshaped, kept local or closed as a capability gap unless its typed
effects independently enter ADR-0075's closed six-class set. [asserted]

The sort uses manifest enums, executed recovery, canonical scope, residuals, task loss/reversal
ceilings, existing authority records and accepted bar/version records. Model confidence, stated
difficulty, agreement and prose claims about reversibility are excluded. [asserted]

## 6. Record reasoning and planning in the existing event

Extend `decision.autonomous`; do not add a parallel decision event. Before action, every autonomous
record carries: [asserted]

- stable `decision_id`, `operation_id`, work-item ticket, Owner and actor; [asserted]
- `record_level` equal to `minimal` or `full`, derived by the controller; [asserted]
- the existing `decision`, `reasoning`, `falsifier` and typed `reversal`; [measured] [asserted]
- `alternatives`, a list of `{option, rejected_because}` objects; [asserted]
- immutable evidence/result references, not copied verifier payloads; [asserted]
- the effect-manifest, recovery-proof and acceptance-contract digests; and [asserted]
- `protocol`, recording whether `better-than-best` was `not_warranted` or `completed`, the
  mechanical threshold inputs, the `instructions.assembled` reference, bar reference and killing
  check when completed. [asserted]

A full record requires at least one rejected alternative. A minimal record may carry an empty list
only when the frozen rules leave one admissible path; the record states that rule rather than
inventing a losing option. This is deliberately stricter where consequence is higher and avoids
forcing filler into routine work. [asserted]

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

The decision therefore stores immutable `evidence_refs`. Replay resolves each reference to the
source event's provenance, `evidence_class`, anchor/hash and dependence metadata. ADR-0077's planned
`verification.outcome` owns those fields, calibration and correlation; this protocol only records
which inputs the Owner used and how each alternative was disposed. It neither copies likelihood
weights nor creates a second fusion table. [asserted]

The projection can then report repeated classes, shared anchors, missing references and unmeasured
dependence. A repeated class is a possible echo/dependence flag, not an automatic rejection;
ADR-0077 deliberately permits repeated observations so their correlation can be measured. A
different label is never proof of independence. [asserted]

The implementation cost is a stable id on decision inputs, reference validation against earlier
events, replay joins, and migration of claim provenance to the full five-value tag set because
`events.PROVENANCE` currently accepts only three. Storage cost is small; classification and
dependence error are the real cost. [measured] [asserted]

## 8. The skill stays and does the judgement

`.agents/skills/better-than-best/SKILL.md` remains unchanged and remains the procedure which shapes
the judgement. Code decides only whether its own three documented threshold conditions are met and
whether the required output references exist. It does not reimplement the five stages. [measured]
[asserted]

The threshold maps to structured facts: [asserted]

1. **A decision turns on the answer:** the effect/acceptance contract marks a public, spend,
   load-bearing design or above-routine consequence. [asserted]
2. **The question is open:** no accepted, in-scope bar/decision artefact with matching version and
   scope digest exists in bounded recall. [asserted]
3. **Being wrong costs more than the protocol:** the frozen worst-case loss exceeds the recorded
   acquisition and delay ceiling. [asserted]

When all three hold, `instructions.py` must select the existing skill and the pre-action record must
reference its assembly plus bar, search and killing-check artefacts. When one fails, the minimal
record states which fact failed and proceeds without ceremony. Nobody is asked to decide whether the
skill feels worthwhile. [asserted]

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
   AST-scans task process, loop, connector and provider paths and fails on a second raw effect path.
   The sandbox fixture separately attempts an undeclared child effect and proves it is denied.
   [asserted]
4. Conditional schema tests derive minimal/full/protected disposition from frozen manifests,
   require alternatives and skill outputs only at the full level, reject reserved autonomous
   decisions, and keep confidence out of the input. [asserted]
5. Replay tests resolve every evidence reference, preserve missing/refused/timeout outcomes and
   reproduce the same decision-to-effect joins after deleting projections. [asserted]
6. Concurrency/crash tests prove the decision and intent are durable before reach; one lost record
   or effect outside the admitted order fails the boundary. [asserted]

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
doi:10.1007/s10664-022-10123-8, `[FULL]` in `docs/10-research/bibliography.md`]

The hard gate also creates a new failure mode: a correct, time-sensitive action can be refused
because its record is malformed, while a wrong action with polished fields passes. More fields add
tokens, latency, storage and verifier surface; the full protocol can become ceremony that agents
learn to satisfy and humans learn to ignore. [asserted]

That objection is not answered by a richer schema. The proposed answer is narrower: enforce only
pre-action existence, binding, ordering and mechanically derived tiers; keep the skill as the place
where judgement happens; and let EXP-104 decide whether even that enforcement earns its cost. If
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

EXP-104 compares the same Owner, skill, tools, controller and budget with and without the hard
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

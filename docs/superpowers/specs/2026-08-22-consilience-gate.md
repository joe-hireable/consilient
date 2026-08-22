# Consilience gate: refuse high-consequence conclusions that rest on echo

**Correction:** ADR-0079 specifies but does not implement the single action-and-decision boundary;
this document extends that future boundary and claims no running gate. [measured]

- **Status:** design only; PROVISIONAL under ADR-0081 and EXP-109. [measured]
- **Extends:** section 7 of `2026-08-22-decision-protocol.md` and ADR-0079. It changes neither
  the immutable `evidence_refs` shape nor ADR-0077's ownership of calibration, correlation and
  fusion. [asserted]
- **Non-goals:** no product implementation, gate-condition change, routing-flag change, new CLI
  command, second orchestrator, second event writer or human review requirement. [measured]

## 1. Answer first

A conclusion which would authorise an irreversible, protected or mechanically high-consequence
decision is refused unless its immutable `evidence_refs` contain a convergent pair of structurally
distinct acquisition anchors. A reversible low-consequence decision proceeds on its available
anchor and records `consilience_required: false`; difficulty, confidence, role count and model
agreement do not raise the tier. [asserted]

The countable acquisition channels are artefact execution, observed browser interaction, retrieval
of an actual primary source and a non-derived corpus demonstrably absent from the deciding context.
A different model family is recorded but receives no structural slot: training overlap and error
decorrelation are unmeasured, and a family reading the same facts adds no exogenous fact. Human
authority is kept separate and is never acquired merely to satisfy this gate. [asserted]

This is a structural admission heuristic, not a claim of statistical independence. No verified
source in the repository establishes that two such anchors are sufficient or universally necessary.
The threshold is therefore `[asserted]`, consequence-tiered and killed by EXP-109 if it only converts
answers into refusals without improving independently checked outcomes. [measured] [asserted]

## 2. The incumbent bar and the delta

The incumbent inside this repository is section 7 of the decision protocol: resolve immutable
references, expose repeated classes and shared anchors, and report `unmeasured` rather than infer
independence. ADR-0077 already provides calibrated fusion and preserves repeated observations so
their dependence can be measured. The new gap is only that a high-consequence action may still
proceed after the projection reports one anchor. [measured]

The strongest external constraint remains Ao, Gao and Simchi-Levi's information bound: delegation
with the same exogenous signals is weakly dominated by an ideal central decision-maker, while an
external verifier can move the information boundary. Kim et al.'s matched comparison also found
task-dependent gains and losses rather than a universal multi-agent benefit. Both sources are
`[FULL]` in `docs/10-research/bibliography.md`, retrieved before this design. [cited]

The plain answer would add `if anchor_count < 2: refuse`. The delta here is the part that makes that
answer usable and falsifiable: a closed structural-channel predicate, an exact consequence trigger,
autonomous acquisition before refusal, preservation of disagreement, one existing action boundary,
and an experiment whose adverse result removes the rule. [asserted]

## 3. Keep provenance, class and independence separate

The decision continues to store each reference as exactly
`{event_id, event_kind, event_sha256}`. The referenced earlier event, validated by its own event-kind
contract, owns its acquisition channel, observation anchor, derivation roots, sealed result and
dependence metadata. The decision event does not copy those fields and this specification adds no
fusion table. [asserted]

The **truth target** and the **observation anchor** are different. Two checks may inspect the same
artefact while observing different facts; sharing the artefact hash does not by itself collapse
them. They collapse when their observation was acquired from the same source, fixture, generated
expectation, peer output or derivation root. Missing derivation information is `unmeasured`, not an
empty root set. [asserted]

For two references `r1` and `r2`, the projection returns `structurally_distinct: true` only when all
of these predicates hold: [asserted]

1. both resolve to unique, valid, earlier events and their recorded hashes match the canonical
   complete events;
2. both events have terminal `completed` observations under the same frozen conclusion and
   acceptance-contract digest;
3. both event kinds validate one countable acquisition channel, and the channels differ;
4. their canonical observation-anchor identities differ;
5. their complete derivation-root sets are known and disjoint; and
6. their sealed outcomes support the same alternative under the frozen contract.

An existential qualifying pair is enough; extra observations do not increase authority. Refusal,
timeout, error, `not_run`, `inconclusive`, malformed, late and unresolved references remain visible
but do not satisfy the predicate. Repeated observations in one channel remain legal for ADR-0077's
correlation measurement and contribute at most one structural slot here. [asserted]

String equality is not convergence. Executable channels report the frozen contract outcome;
source/corpus channels seal a proposition identifier, stance and locator before synthesis. An event
cannot be admitted under two channel labels, and the Owner cannot relabel a transport after seeing
the result. [asserted]

## 4. Channels admitted by construction

| acquisition channel | event-kind proof required | structural credit and limits |
|---|---|---|
| `artefact_execution` | A frozen `verification.outcome` or linked attempt receipt with artefact hash, verifier contract/version, environment, terminal component outcomes and observation-anchor digest. [asserted] | One slot. A second test, compiler or sensor in this broad channel remains the same slot until a narrower mechanism and its dependence are measured under ADR-0077. A test generated from the claimant's expected output names that derivation root. [asserted] |
| `browser_observation` | A `verification.outcome` bound to executed interaction, browser/version and artefact hash, plus a retained screenshot, accessibility tree, DOM/runtime, console/network or interaction receipt. [asserted] | One slot for rendered/runtime behaviour. A browser used only to fetch prose is `primary_source_retrieval`, and a prose visual review is unmeasured. [asserted] |
| `primary_source_retrieval` | A `knowledge.retrieved` event with canonical identifier/URI, retrieval time, content hash, claim locator and verification status `[FULL]` or claim-bounded `[ABS]`. [asserted] | One slot for what that source says, not for whether the source is true. Two readers or transports for the same source are one anchor. [asserted] |
| `novel_corpus_observation` | A `knowledge.retrieved` event with corpus manifest, provenance, licence, retrieval time, selection rule, content hash and the earlier assembled-context digest proving the corpus was absent. Public-API responses use the same contract. [asserted] | One slot only when the corpus is non-derived and absent from every deciding context. A paraphrase, cached summary or overlapping corpus exposes the shared root and does not count. [asserted] |

The following are recorded as `unmeasured` and receive zero structural credit: model family or
provider; role, persona or prompt difference; another pass over the same context; self-reported
confidence; majority vote; evidence-tag inequality; unexecuted static opinion; an algebraic or
simulated result with unvalidated premises; a source snippet; and any event missing channel, anchor
or derivation data. [asserted]

Different model families are useful correlation metadata under ADR-0077, but their discount is
exactly **unmeasured** here. No universal numeric discount is imported. A family may acquire a
countable world anchor; the credit belongs to that anchor, not the family label. [asserted]

A human verdict is a distinct first-party fact only for that person's preference, authority or
lived impact. It cannot be minted by an agent, is not a likelihood weight, and is never requested to
manufacture a second objective anchor. The existing ADR-0075 protected path still obtains exact
principal authority where required; convergence can improve the proposal but cannot supply that
authority. [asserted]

## 5. The gate and its exact tier

The tier reuses facts ADR-0075 and ADR-0079 already derive. No new consequence score is introduced.
[asserted]

`requires_consilience` is true when either: [asserted]

- ADR-0079's mechanically derived `record_level` is `full`; or
- ADR-0075's disposition is `protected_covered` or `protected_uncovered`.

`record_level: full` already means a versioned conservative proxy found that later work, money, a
public claim or a design constraint relies on the answer, or that the class is protected. The
protected dispositions cover the one-way classes which a recovery proof cannot make ordinary.
`capability_gap` remains refused by ADR-0075 before this rule can weaken it. [asserted]

All other valid `minimal` dispositions, including observation, contained execution, proof
operation, material choice and recovery-proved mutation, proceed without a second anchor. They
record `consilience_required: false`, the referenced anchors and whether the available evidence was
`single_anchor` or `unmeasured`; they do not summon a squad because the task appears hard. [asserted]

For `requires_consilience: true`, convergence is necessary but never sufficient. Recovery,
authority, beta, budget, law, gate status and typed-effect checks still apply independently. The
consilience gate cannot open a capability another boundary refused. [asserted]

## 6. One boundary, before reach

The check sits inside ADR-0079's specified atomic action-and-decision admission, after the actual
typed effect manifest, ADR-0075 disposition and `record_level` are derived, and before
`effect.intent` exposes a single-use handle. It does not sit in `events.append()`, because the writer
can validate a record but cannot know whether another path is about to actuate. [measured]
[asserted]

For a material choice with no immediate effect, ADR-0079 already binds the same admission to
ADR-0072 work-item readiness; no dependent claim becomes ready until the check passes. The first
current dispatch slice remains `run_harness()` immediately before `run_process()`, but this document
does not mistake that slice for a universal boundary. Child effects, connectors and the unattended
loop must obtain the same admission or remain without live reach. [measured] [asserted]

The implementation commit must add
`tests/test_decision_protocol.py::test_high_consequence_admission_refuses_single_structural_anchor`.
The fixture must prove that one valid anchor, two family/label variants of one anchor, a shared
derivation root and missing dependence metadata all refuse before a fake effect is reached, while a
minimal recovery-proved action records one anchor and proceeds. The existing ADR-0079 executable-
tree bypass test remains the universal path check. [asserted]

No implementation ships with this specification. `routing_orchestration_enabled` remains `false`,
Gate A and Gate B are unchanged, and the `consil` command set remains six. [measured]

## 7. Disagreement is the result

The projection returns `converged`, `insufficient`, `disagreed` or `unmeasured`; it never turns two
completed but opposed outcomes into a failed run. Every raw reading is sealed and appended before
the Owner sees the set. [asserted]

When two structurally distinct anchors disagree, the Owner: [asserted]

1. records both proposition/alternative stances, their evidence refs, scope, estimand, limits and
   consequence branch without averaging, voting or deleting a minority reading;
2. checks first whether the observations answer different questions or scopes;
3. acquires one pre-specified discriminating world observation when an available outcome could
   change the action and its cost fits the remaining budget;
4. otherwise runs a bounded reversible probe when that probe can create the missing observation;
   or
5. records `disagreed_unresolved`, returns both consequences and refuses the high-consequence
   action.

A third model reading the same anchors cannot break the tie. The principal is contacted only when
the unresolved action independently enters ADR-0075's exact authority or preference class, never
as an epistemic vote. Dissent remains in the trajectory after any later evidence resolves the
decision. [asserted]

## 8. Acquire the missing anchor without a human

An insufficient high-consequence decision enters bounded acquisition before terminal refusal. The
Owner selects the cheapest available countable channel whose possible result could change the
action; if no such channel exists, acquisition has zero value and is not dispatched. [asserted]

The implementation reuses the existing substrate: [asserted]

1. `capabilities.py` validates an available allowlisted capability mapped to the missing acquisition
   channel. Availability in prompt text is not live reach; ADR-0078 still brokers the handle.
2. `work_items.py` opens one child acquisition item and `coordination.py` claims its paths. The item
   carries the frozen conclusion, acceptance-contract digest, required channel, anchor contract,
   budget and expiry.
3. `instructions.py` assembles the bounded acquisition instruction. `recall.py` may supply frozen
   task context but withholds peer outcomes until this reading is sealed.
4. `scripts/dispatch.py` runs the child with the validated capability request. Generic `--fan-out`
   and family diversity do not satisfy the request.
5. The event-kind validator appends the actual completed/refused/timeout/error observation as
   `verification.outcome` for execution/browser channels or `knowledge.retrieved` for source/corpus
   channels through `events.py`, the sole writer; `work_items.py` then closes the child.
6. The Owner appends a superseding `decision.autonomous` with the new immutable references and
   re-enters the same action admission. It never rewrites the earlier insufficient decision. No
   acquisition route may actuate the original high-consequence effect, approve the conclusion or
   bypass budget/routing.

The current capability inventory records provenance but not a validated acquisition channel or
anchor contract, and the current recall-packed brief has no sealed assembled-context digest. The
implementation must extend those existing schemas with exactly that mechanism and sealing metadata;
inventory provenance, a family label or prompt text alone never counts as an anchor. [measured]
[asserted]

Acquisition stops when a qualifying convergent pair exists, the remaining structurally different
channels cannot change the action, the frozen budget/expiry is exhausted, or a disagreement is
unresolved. An unavailable second anchor records `refused_insufficient_consilience`; it never
silently downgrades `full` to `minimal` and never asks a human for generic confirmation. [asserted]

Each child acquisition is classified independently as observation or contained execution and holds
no handle to the parent effect. If it cannot meet that low-tier contract it is a capability gap, so
acquiring anchor two cannot recurse into another high-consequence consilience requirement.
[asserted]

`routing.py` continues to own beta ceilings and candidate exposure; `budget.py` continues to refuse
spend; and `events.py` continues to own the append-only record. A new coordinator, queue, database,
fusion table or CLI command would be a design defect. [asserted]

## 9. Evidence against: superstition with a schema

The strongest objection is correct: acquisition-mechanism difference is provenance, not measured
statistical independence. A test and a browser can share the same mistaken requirement; a source
and corpus can share an upstream publisher; two independent implementations can share training and
evaluation priors. A closed enum can make those common causes less visible by replacing honest
uncertainty with a green `channel_count = 2`. [asserted]

Most legitimate decisions rest on one good anchor. A compiler error, a signed primary authority, a
reproducible counterexample or an exact account balance may dominate ten weaker readings. Requiring
another channel can add latency, cost and a new availability dependency while reducing competence
through lossy acquisition. Kim et al.'s controlled comparison shows that added agent structure can
lose to the strongest single control; this repository's EXP-16 measured substantial coordination
overhead, while its blinded decision-quality comparison remains outstanding. [cited] [measured]

A refusal gate can appear safe by refusing everything. It may reduce bad actuation without improving
correct completion, and a missing browser, source or corpus can become a denial-of-service against a
correct time-sensitive action. Required structure can also become schema-compliant filler; Wurzel
Gonçalves et al.'s registered code-review study found no general effectiveness gain from explicit
review strategies and lower effectiveness in one controlled change, with important population and
power limits. [cited] [asserted]

The two-anchor threshold therefore has no `[cited]` warrant. The defence is deliberately limited:
trivial reversible work stays single-anchor; structural admission never claims numeric weight;
shared or missing derivation data fail visibly; acquisition is automatic and bounded; disagreement
is retained; and EXP-109 measures correct completion, bad actuation, refusals, cost and missingness
together. If the treatment merely refuses more, the hard gate is removed and section 7's visibility
rule survives. [asserted]

That is a concession, not a rhetorical answer. Until EXP-109 reports, calling this gate safer would
be false; it is a provisional policy whose purpose is to make the hypothesis executable. [asserted]

## 10. Validation and report

EXP-109 compares section 7's flag-only incumbent with this refusal-plus-autonomous-acquisition rule
under the same Owner, capabilities and total budget. It can activate the gate only for its frozen
high-consequence mixture; it cannot establish universal independence or relax any other boundary.
[asserted]

The report required from any implementation or experiment is: [asserted]

- countable channels used and every reference marked `unmeasured`;
- the exact qualifying pair or refusal reason;
- `record_level`, ADR-0075 disposition and why the threshold fired;
- every disagreement, minority reading and next observation attempted;
- acquisition work items, budget, timeout/refusal/error counts and terminal state;
- correct completions, bad actuations and refusals side by side; and
- confirmation, kill or inconclusive application of EXP-109's frozen stopping rule.

## 11. Plain answer and delta

**Plain answer:** require two anchors before an important action. [asserted]

**Delta:** only four validated world-touching channels can count; model-family difference is
`unmeasured`; low-consequence reversible work stays on one anchor; disagreement is preserved; the
existing dispatch/work-item/capability/event path acquires the missing observation; one future
action boundary refuses bypass; and EXP-109 removes the rule if its only measured product is more
refusal. [asserted]

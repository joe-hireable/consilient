# Work taxonomy and the threshold-gated three-phase protocol

**Correction:** the principal's later 23 August instruction requires every work category to be
executable as a native agent and separates worker method from subject expertise; companion ADR-0093
owns that composition. Model-family difference alone still has zero evidence credit, beta bounds
candidate exposure rather than squad size, and tool-enabled frontier harnesses already execute code
and retrieval. This specification owns the work meanings and threshold, not the agent catalogue.
[measured: `../../00-context/the-machine-2026-08-22.md`; ADR-0077; ADR-0081; ADR-0090; ADR-0093]
[asserted]

- **Date:** 2026-08-23. [measured]
- **Status:** specification only; [ADR-0092](../../decisions/0092-classify-durable-work-and-stop-deliberation-at-an-external-threshold.md)
  is PROVISIONAL. [measured]
- **Killing experiment:**
  [EXP-135](../../10-research/experiment-register.md#exp-135--does-threshold-gated-deliberation-improve-accepted-outcomes-over-fixed-budget-deliberation-at-the-same-total-budget-blocked)
  compares threshold stopping with fixed-budget stopping at the same total budget. [asserted]
- **Scope:** durable `full + better-than-best` work. `full + fast` retains its ordinary checks but
  makes no better-than-best claim; `light` creates no durable work item and is outside this taxonomy.
  [measured: ADR-0090] [asserted]
- **Supersession:** this specification and ADR-0092 supersede ADR-0090 only where its in-flight draft
  defines category meanings, transition admission and threshold/give-up semantics. They reuse
  ADR-0090's `phase`, `effort.transition` and status names; ADR-0090 retains modes, profiles,
  aggregate effort, `effort.plan`, `effort.charge`, `exceed_cap`, `realisation_reserve` and
  `effort.summary`. [measured] [asserted]
- **Non-goals:** effort allocation, a configured phase ratio, category-agent composition or
  training, a seventh CLI command, a gate change, a second task store/writer/orchestrator,
  implementation, or a claim that Consilient uniquely runs tools. [asserted]

## 1. Answer first

Every new durable full-mode work unit carries one closed `work_category` and one compatible ADR-0090
`phase`: `locate`, `exceed` or `realise`. ADR-0090's `effort.charge` accounts that pair; this
specification owns what the categories mean and when an `effort.transition` may move between them.
ADR-0093 maps each category to a native worker profile and composes subject expertise without
creating worker-by-domain identities. [asserted]

`locate` opens `exceed` only with a cited `bar_located` package; `bar_unresolved` is an honest terminal
outcome and cannot open the better-than-best phase. `exceed` ends as `bar_beaten` when the frozen,
external threshold is discharged, or as `bar_not_beaten` when the pre-declared give-up condition
fires. `realise` builds the selected candidate, runs the frozen acceptance checks and delivers or
records why delivery did not occur. Each `effort.transition` consumes a content-addressed handover
rather than an agent's assertion that it feels ready. [asserted]

`bar_not_beaten` means the protocol did not demonstrate that the bar was beaten; it is not an
affirmative measured loss. If no matched comparison ran, `gap` is `unavailable`. If the give-up
condition fires before ADR-0090's hard total is exhausted, the best safe candidate proceeds with that
limitation at delivery. If the hard total is exhausted first, ADR-0090 governs: the request returns
`incomplete` and implementation does not start. [asserted]

## 2. Existing owners and this decision's boundary

| Concern | Existing owner | Boundary here |
|---|---|---|
| Modes, profiles, aggregate budget, phase/category charges, `exceed_cap`, `realisation_reserve`, forecasts and total exhaustion | ADR-0090 and `budget.py` [measured] | This protocol defines category-agent meanings and transition admission inside that frozen envelope; it allocates no ratio or second budget. [asserted] |
| Consequence tier, qualifying anchor channels, disagreement and echo | ADR-0081 [measured] | A `bar_beaten` claim in this durable better-than-best profile is `record_level=full` and reuses the provisional ADR-0081 rule; this document invents no fifth channel or independence weight. [asserted] |
| Candidate exposure, verifier fusion and dependence | ADR-0077 and `routing.py` [measured] | Threshold assessment cannot change candidate exposure or use the obsolete iid logarithmic expression as policy. [asserted] |
| Inquiry cost and whether modelling or measurement is warranted | `inquiry-tier.md`, ADR-0049 and ADR-0050 [measured] | A category agent never makes an unnecessary experiment valuable; largest plausible effect must still change the decision. [asserted] |
| Tasks, claims, bounded context and execution | `work_items.py`, `coordination.py`, `recall.py`, `instructions.py` and `scripts/dispatch.py` [measured] | Future implementation extends these paths; a second workflow engine is a defect. [asserted] |
| Authoritative record | `events.py` [measured] | Every category, phase status and handover reference reaches the append-only trajectory through the existing writer. [asserted] |
| Native category agents and subject expertise | In-flight ADR-0093, consuming ADR-0074/0084/0086 and ADR-0036/0065 [measured] | This document supplies the closed work meanings; the companion stream is responsible for worker profiles, fact contracts, expertise bundles, portable binding, open-data/adoption requirements and the training boundary. It has not implemented them. [asserted] |
| Principal authority | V0-18/V0-23 and ADR-0033 [measured] | A threshold result may support a proposal; it cannot approve, spend, publish, expose, supply credentials or lift a gate. [asserted] |

ADR-0090's phase, charge and transition records remain the one operational vocabulary. Its in-flight
draft also defined the taxonomy and threshold while this companion was being written; ADR-0092
supersedes only those overlapping meanings because this brief assigns them here. No implementation
may choose between two state machines. [measured] [asserted]

ADR-0090's deciding stages remain useful procedure. This taxonomy classifies their actual work:
Frame becomes `framing`; Discover becomes `discovery`; Research becomes `research`; Model or
simulate becomes `simulation`; Experiment becomes `experiment`; Innovate and Decide use `debate`,
`innovation`, `synthesis` and `assessment`; Plan becomes `planning`. Hypotheses are frozen artefacts,
mathematical modelling is an instrument mode, data science is classified by its work purpose, and
specification is synthesis/planning unless it is itself the requested implementation artefact. The
taxonomy does not duplicate ADR-0090's scheduling or ADR-0093's worker catalogue. [asserted]

Categories are not passive labels: ADR-0093 must make each one executable as a native task-scoped
profile. This document nevertheless labels work rather than defining roles. One Owner remains the
default, and another runtime is admitted only for a named decision-relevant fact unavailable to the
Owner or non-overlapping artefact scope. A reviewer reading the author's same diff is `assessment`
work but supplies no new anchor. [measured: ADR-0067; ADR-0081; ADR-0093] [asserted]

## 3. Closed work taxonomy

The v1 worker-type list is closed at runtime. There is no free-text category and no `other`: either would make
phase measurement incomparable and let new behaviour bypass its checks. A new category requires a
versioned schema change and successor decision with an explicit migration; historical records with
no category remain `unavailable`, never guessed. [asserted]

| Label | One-sentence definition | Protocol phase | Pre-doing or doing |
|---|---|---|---|
| `framing` | Freeze the objective, user, scope, authority, consequence, success contract, reversal and material unknowns before looking for an answer. [asserted] | `locate` | pre-doing |
| `discovery` | Inspect the actual system, data, constraints and candidate incumbents to produce a provenance-bearing map of what exists and what is unknown. [asserted] | `locate` | pre-doing |
| `research` | Retrieve and verify primary sources or open data to establish the incumbent, its achievement, its limits, the search log and near misses. [asserted] | `locate` | pre-doing |
| `experiment` | Pre-register and execute an intervention or observation against the real system, retaining raw results, adverse outcomes and the stopping-rule verdict. [asserted] | `exceed` | pre-doing |
| `simulation` | Execute a formal model under declared assumptions to locate sign changes, thresholds or regimes without presenting its output as an empirical fact. [asserted] | `exceed` | pre-doing |
| `debate` | Adversarially test competing claims against their evidence, preserve dissent and add no anchor credit unless a participant acquires a genuinely new fact. [asserted] | `exceed` | pre-doing |
| `innovation` | Import an evidenced mechanism from a genuinely different field or fact class, state why it transfers and name the observation that would falsify the transfer. [asserted] | `exceed` | pre-doing |
| `synthesis` | Turn the surviving evidence into one operational candidate and record why each viable alternative lost. [asserted] | `exceed` | pre-doing |
| `assessment` | Apply the frozen comparison and acceptance contract to a frozen candidate, retain the receipts and classify every claimed anchor or echo. [asserted] | `exceed` | pre-doing |
| `planning` | Translate the selected candidate into the fewest verifiable work units with dependencies, claims, authority, budget, verifier and reversal fixed. [asserted] | `exceed` | pre-doing |
| `implementation` | Create or change the target artefact from the frozen realisation package without silently reopening its goal or verifier. [asserted] | `realise` | doing |
| `verification` | Execute the frozen acceptance checks against the realised artefact and retain every pass, failure, refusal, timeout and unavailable result. [asserted] | `realise` | doing |
| `delivery` | Return or expose the artefact and its evidence within existing authority, including an explicit `bar_not_beaten` limitation when applicable. [asserted] | `realise` | doing |

Code executed to learn is `experiment`, `simulation` or `assessment`; code changed to become the
user's artefact is `implementation`. A prototype produced during `exceed` remains quarantined
evidence until the realisation handover selects it. Final acceptance after implementation is
`verification`, not a retroactive `assessment`. [asserted]

A work unit has exactly one category. If its purpose changes from research to implementation, it is
closed with its artefact and a new linked unit is opened; relabelling in place would corrupt the
measurement and the provenance trail. [asserted]

### 3.1 Native-agent boundary

The in-flight ADR-0093 stream consumes this closed taxonomy and is responsible for giving every
category a native task-scoped worker profile. It must separately discharge fact contracts,
subject-expertise bundles, capability/instruction assembly, portable harness bindings, open-data
requirements, adoption before custom capability code and the retrieval/training boundary. This ADR
does not claim those controls exist. The stored `work_category` remains the measurement identity; it
is not a second agent manifest, a standing member or evidence credit. [measured] [asserted]

### 3.2 Recording contract

Future implementation adds the minimum typed fields to the existing substrate. [asserted]

- `work_items.py` accepts `work_category` and `phase` as required, immutable fields on every new
  durable full-mode `work_item.opened`; helpers do not accept arbitrary substitutes. ADR-0093's role
  request, when present, references that same immutable category rather than redefining it.
  [asserted]
- `events.py`, the sole writer, validates the closed enum, the fixed category-to-phase mapping and
  the transition rule at the universal append boundary; helper-only validation is insufficient
  because generic append paths already exist. [measured] [asserted]
- Completion carries a content digest and `handover_ref` for any phase-producing unit; projections
  and bounded recall resolve the reference rather than copy an unbounded artefact into every event.
  [asserted]
- ADR-0090's `effort.charge` carries the same phase/category snapshot and work-item identity; the
  writer rejects a mismatch rather than allowing a second mutable label. [asserted]
- Historical events stay readable. A missing historical category reports `unavailable`, never zero
  work and never an inferred label. [asserted]
- Light mode remains intentionally absent because ADR-0090 promises no durable work item or event;
  adding a synthetic light category would break that contract. [measured] [asserted]

Current `work_items.py` records only open/comment/complete data and has no category, protocol phase or
handover contract; `events.py` has no universal validation for those fields. This document therefore
claims future behaviour only and writes no implementation. [measured: source inspection,
2026-08-23]

## 4. Phase 1 — locate the bar

Phase 1 consumes ADR-0090's frozen request contract and produces one **bar package**. [asserted]

The package contains: [asserted]

1. the incumbent's canonical identity, revision/date and exact scope;
2. primary-source references with retrieval date, content digest and claim locator;
3. what the incumbent demonstrably achieves, on which measure and under which conditions;
4. the search queries, repositories/catalogues searched, inclusion rule and near misses;
5. known limitations and every claim that remains `[asserted]`;
6. the task-native comparison procedure, smallest materially meaningful improvement `delta_marked`
   and non-regression constraints; and
7. whether the proposed threshold is prospectively measurable before realisation.

Phase 1 opens Phase 2 only through an `effort.transition` carrying `bar_located`, when the incumbent
and achievement are cited from a
retrieved `[FULL]` source, or an `[ABS]` source limited to what its abstract actually states, and the
comparison contract is frozen. A snippet, model memory or uncited claim that nothing exists cannot
open Phase 2. [measured: citing-sources skill; working principle 9] [asserted]

If the bounded search cannot locate a citable bar, Phase 1 returns `bar_unresolved` with the search
record and the best prior labelled `[asserted]`. It is terminal for this better-than-best protocol
and does not open `exceed`. The Owner may return the best supported ordinary answer without a
better-than-best claim. [asserted]

## 5. Phase 2 — exceed the bar

Phase 2 consumes the frozen bar package. It may retrieve, run experiments, execute simulations,
create quarantined prototypes, challenge claims and compare candidates; its output is evidence and a
decision package, not the delivered artefact. [asserted]

"Any means necessary" means any existing capability admitted by the frozen authority, safety,
spend, privacy, gate and effect boundaries. It does not authorise a credential, metered call,
publication, unsafe action or gate bypass. [measured] [asserted]

Before any candidate result is visible, the package freezes this threshold contract: [asserted]

- comparator identity, scope, measure, direction and bar value or executable bar procedure;
- `delta_marked`, derived from the user success contract, task-native materiality or the instrument's
  resolution rather than from the candidate's observed score;
- must-pass safety, correctness, accessibility, cost and authority constraints relevant to the task;
- fixtures/corpora, environment, verifier versions and candidate-free comparison procedure;
- the ADR-0081 consequence and anchor contract, including known derivation roots;
- the pre-declared give-up contract in section 6; and
- the exact rule selecting the best safe candidate if the threshold is missed.

If no prospective measure and material delta can be stated before candidate results, set
`threshold_testability: unavailable`. That value makes `bar_beaten` unreachable; it is not
silently replaced by a confidence score or retrospective taste. [asserted]

### 5.1 What discharges the threshold

`bar_beaten` requires all of the following: [asserted]

1. a frozen candidate evaluated under the bar package's scope and comparison contract;
2. an executed matched comparison showing improvement in the required direction of at least
   `delta_marked` against the bar's own stated or reproduced achievement;
3. every frozen non-regression and must-pass constraint satisfied, with missing results treated as
   unavailable rather than passing;
4. a convergent pair of ADR-0081-qualified anchors with different acquisition channels, distinct
   observation identities, known disjoint derivation roots and the same frozen conclusion and
   acceptance contract; and
5. a mechanically derived assessment record carrying the bar package, candidate digest, comparison
   receipts and qualifying evidence references.

This durable better-than-best conclusion is recorded as `record_level=full`; ADR-0081 remains
PROVISIONAL and unimplemented, so this is a future contract rather than a claim about today's source.
[measured] [asserted]

A matched executable benchmark plus a held-out public corpus, or an executable comparison plus
authenticated first-party outcome evidence, can provide different anchors when their derivation
roots are known and disjoint. A fetched primary source establishes what the bar reports; it does not
by itself establish that the candidate exceeded it. [asserted]

A different-family assessor receives zero credit for family difference. It can contribute only by
retrieving or executing a qualifying anchor that the candidate proposer did not derive; the credit
belongs to that observation. [measured: ADR-0081] [asserted]

### 5.2 What is refused as echo

None of these can discharge the threshold: the proposer's opinion; self-reported confidence;
majority vote; another role, persona, prompt or model family reading the same corpus; two checks
derived from the same fixture or expected output; normalised answer agreement; an unexecuted code
review; a search-result snippet; or an unvalidated simulation. They remain visible evidence or
diagnostics, but contribute no qualifying anchor. [measured: ADR-0081] [asserted]

When qualifying anchors disagree, retain both readings and acquire one pre-declared discriminating
observation only if its possible result can change the decision and fits the give-up contract. A
vote or third reader of the same evidence cannot resolve the disagreement. Unresolved disagreement
cannot produce `bar_beaten`. [measured: ADR-0081] [asserted]

### 5.3 Phase 2 handover

Phase 2 produces one **realisation package** containing the selected candidate and digest;
`bar_beaten` or `bar_not_beaten`; the measured gap to the bar or `unavailable`; comparison and anchor receipts;
adverse evidence and rejected viable alternatives; the frozen implementation plan, verifier,
authority, dependencies, budget and reversal; and the experiment that could improve any remaining
uncertainty. This is ADR-0090's deciding exit package with threshold fields added, not a second
decision record. [asserted]

## 6. The give-up condition

Before Phase 2 sees a candidate result, ADR-0090's `effort.plan` freezes: [asserted]

- an `exceed_cap` containing an absolute deadline inside the request wall-clock ceiling;
- a finite ordered set of remaining acquisition/assessment steps, each with cost, largest plausible
  effect and the threshold status it could change; and
- ADR-0090's component-wise `realisation_reserve` for the minimum feasible realisation.

The give-up condition fires at the earliest of: `exceed_cap`; exhaustion of that finite step set;
the next step not fitting inside the remaining authorised total while preserving
`realisation_reserve`; or, when an executed comparison produced a numeric gap, every remaining
step's largest plausible effect being smaller than the gap to `delta_marked`. An unavailable gap
cannot fire the last branch. This is a task-specific ceiling frozen before results, not a universal
phase percentage. [asserted]

On give-up, select the best candidate under the frozen objective and must-pass constraints, append
an `effort.transition` carrying `bar_not_beaten`, record which branch fired, the measured gap or
`unavailable` and the next experiment that could change it, then enter Phase 3 if ordinary authority,
safety and remaining budget permit. The status records that superiority was not demonstrated; it is
not an error, an affirmative loss claim or permission to call an unsafe candidate "best". [asserted]

Crossing ADR-0090's soft decide forecast does not itself fire this rule. Exhausting its hard total
does: ADR-0090 returns `incomplete` with no implementation, even if this protocol would otherwise
carry a candidate forward. [measured: ADR-0090] [asserted]

## 7. Phase 3 — realise it

Phase 3 consumes the realisation package. `implementation` creates the target artefact without
changing the goal or acceptance contract; `verification` runs the frozen checks; `delivery` returns
or exposes the result only under existing authority. [asserted]

Phase 3 exits when the realised artefact and terminal verification receipts exist and the authorised
delivery action is recorded as completed, refused, unavailable or awaiting the principal. A failed
verifier remains failed; a delivery delay does not turn it into success. [asserted]

The final **delivery package** contains the artefact/diff or stable reference, exact verification
receipts, resource use or `unavailable`, the bar and candidate comparison, threshold outcome,
adverse results, reversal and any principal-only action still required. A `bar_not_beaten` package
states that phrase plainly and cannot advertise better-than-best. [asserted]

## 8. Handover summary

| Transition | Exit condition | Artefact handed forward |
|---|---|---|
| `locate -> exceed` | `bar_located`: retrieved citation, incumbent achievement and frozen comparison contract all exist. [asserted] | Bar package: incumbent, citations/digests, achievement, search log, limits, measure, `delta_marked`, non-regressions and testability. [asserted] |
| `exceed -> realise` | `bar_beaten`, or the pre-declared give-up condition fires before hard-total exhaustion and records `bar_not_beaten`. [asserted] | Realisation package: candidate, `bar_beaten|bar_not_beaten`, gap or `unavailable`, receipts/anchors, dissent, rejected alternatives, plan, verifier, authority, budget and reversal. [asserted] |
| `realise -> user/system` | Realised artefact has terminal verification and an authorised delivery disposition. [asserted] | Delivery package: artefact reference, verifier receipts, usage, threshold result, limitations and reversal. [asserted] |

`bar_unresolved`, hard-total exhaustion, no safe candidate and a principal-only boundary are terminal
states, not silent phase transitions. [asserted]

## 9. What executed reasoning adds — and does not

Standalone model inference can transform the prompt and its internal state into tokens; it cannot
create a new process result, browser observation, retrieved source or real-system intervention after
the prompt. A system around a model can do those things and feed their receipts back into later
inference. Executable code actions and software-agent interfaces have measured gains over intrinsic
reflection in some settings, while those results do not establish verifier reliability or universal
superiority. [cited: Wang et al. (2024), PMLR 235; Yang et al. (2024), SWE-agent; Huang et al.,
*Large Language Models Cannot Self-Correct Reasoning Yet*]

This is not unique to Consilient. OpenHands, MetaGPT and other contemporary agent systems already
execute code and exchange artefacts, and ADR-0084 already records portable agent configuration as an
incumbent capability. Their cited evaluations do not establish this externally discharged threshold
or outcome advantage, but their existence defeats any claim that tools or portable
configuration are the product differentiator by themselves. [cited: OpenHands,
arXiv:2407.16741; MetaGPT, arXiv:2308.00352; bibliography read 2026-08-22] [measured]

The proposed design hypothesis is narrower: Phase 2 turns external execution into retained,
provenance-bearing observations; compares them against a cited incumbent under a frozen material
delta; refuses echo as threshold evidence; and records a threshold miss rather than narrating one
away. Whether threshold stopping produces better accepted outcomes is `[asserted]` until EXP-135
runs. ADR-0093 separately tests category-agent composition in EXP-136. [asserted]

It can also be worse. Retrieval and execution add latency, cost, tool failure, proxy optimisation,
environment drift and context handoff loss; a strong frontier model can answer self-contained tasks
whose relevant facts are already in context faster and with less machinery. EXP-16's nearest local
comparison found the simpler single-agent arm winning 9 of 12 substituted blind judgements while the
Owner meeting used 4.8 times the tokens and 3.7 times the wall time. That experiment is not a phase
protocol test, but it is direct evidence against assuming that more organised reasoning is better.
[measured]

## 10. Evidence against: the threshold may be unmeasurable

The strongest objection is that "markedly better than the best existing answer" often cannot be
known before the thing is built. Integration, migration, browser behaviour, deployment and user
response may be the only valid measures; any Phase 2 proxy can optimise an imagined artefact rather
than the delivered one. The system will then fail to discharge the threshold, consume every planned
assessment and stop at its ceiling. Operationally that is a fixed budget with a threshold-shaped
dashboard and extra overhead. [asserted]

The objection is conceded for tasks whose bar package sets `threshold_testability: unavailable` or
whose only valid comparison requires the final realised artefact. Those tasks cannot record
`bar_beaten`; if a citable bar was located they proceed, when safe and resourced, through
`bar_not_beaten` with `gap: unavailable`. On that scope the protocol is a budget plus honest
provenance and handover fields, not a demonstrated intelligence advantage. [asserted]

The remaining defence is falsifiable rather than rhetorical. Some tasks admit a pre-realisation
matched benchmark, executable prototype, simulation with validated premises or held-out corpus; on
those tasks the threshold can stop deliberation before its ceiling and move capacity to realisation.
EXP-135 stratifies prospectively testable and build-dependent tasks. If threshold runs mostly reach
the ceiling or fail to improve joint acceptance over fixed-budget stopping, a successor ADR removes
the threshold as a quality claim and retains only the taxonomy and explicit outcome record.
[asserted]

## 11. Search record, plain answer and delta

Repository search on 2026-08-23 covered `threshold`, `stopping`, `budget`, `reasoning`, `tool`,
`experiment`, `simulation`, `agent config`, `worker type`, `subject matter`, `OpenHands`, `MetaGPT`,
`AutoGen`, `CrewAI`, `SWE-agent` and `Superpowers`; it read ADR-0036, ADR-0065, ADR-0074, ADR-0077,
ADR-0081, ADR-0084, ADR-0086, ADR-0090, ADR-0093, their companion specifications,
`inquiry-tier.md`, the
capability-layer research and `[FULL]` bibliography entries for executable agents, team patterns and
intrinsic self-correction. [measured]

The nearest internal bar for this decision is ADR-0090's artefact-driven deciding phase and
total-budget boundary; ADR-0093 separately owns the native category-agent bar. The nearest external
systems execute tools, while the pinned Superpowers workflow supplies structured brainstorming and
planning; no verified source in this repository establishes an externally discharged
better-than-best threshold with this exact handover contract. That absence is not a novelty claim.
[measured] [asserted]

The plain answer is: label deciding and doing work, research the incumbent, stop deciding when an
objective comparison clears it, otherwise stop at a budget and build the best safe option. ADR-0093
makes those categories executable as native agents. [asserted]

The delta is the closed thirteen-category taxonomy, one authoritative ADR-0090 transition
vocabulary, content-addressed handovers, ADR-0081 anchor rule, explicit echo refusal, pre-declared
give-up contract and the `bar_not_beaten` delivery obligation. EXP-135 decides whether threshold
stopping improves accepted outcomes; ADR-0093/EXP-136 owns whether category-agent profiles add value.
[asserted]

## 12. Checks owed by implementation

This specification changes no product behaviour. A future implementation must ship these checks in
the same commit as the fields and transitions: [measured] [asserted]

- reject any new durable full work item with a missing, unknown or phase-incompatible category;
- prove each category resolves one-to-one to the same immutable ADR-0093 worker profile when native
  role assembly is implemented, without creating a second taxonomy;
- reject category mutation and require a linked successor unit when purpose changes;
- reject a phase transition with no valid content-addressed handover;
- reject `bar_located` without retrievable citations, achievement and frozen comparison contract;
- reject `bar_beaten` on opinion, confidence, family/role difference, shared derivation roots,
  missing results, disagreement or an unfrozen material delta;
- prove `bar_not_beaten` survives through delivery and cannot be rendered as better-than-best;
- prove the give-up condition cannot enlarge ADR-0090's total and that hard-total exhaustion starts
  no implementation;
- prove principal-only authority remains unforgeable and no threshold result changes a gate; and
- prove all records pass through `events.py`, with no second store, writer, router, budget ledger,
  orchestrator or CLI command.

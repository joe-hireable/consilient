# Routing, memory, capability and learning substrate assessment

**Correction:** ADR-0025 is `PROPOSED`, not an accepted decision that can literally be reopened; its rejected-GNN section already covers memory as well as routing, and the trajectory is an append-ordered log rather than a general DAG. [measured]

The brief's data premise is also wrong: at `2026-08-23T11:30:06Z` the validated trajectory contained 149 operational `dispatch.outcome` records, one joined verifier outcome with a human verdict, and **zero model-attributed labelled routing outcomes**. [measured] The five EXP-07 pairs are synthetic experiment fixtures, not five live routing labels. [measured] The current exposure ceiling in `routing.py` uses the distribution-free union bound `floor(epsilon / beta_upper)`, not the independence formula quoted in the brief. [measured]

## Direct verdict

**Gather data first; build nothing now.** [asserted] Keep the append-only event stream as the authority, keep routing, recall, capability selection and learned state as separate bounded mechanisms, and derive a disposable read-only relationship view only when a measured operation needs it. [asserted] Do not build a graph database, a GNN, a shared neural network, a second orchestrator, or a new training path. [asserted]

No ADR is required because this recommendation changes no accepted or proposed architecture, and no experiment is proposed because the first unmet prerequisite is a joinable outcome record rather than a candidate algorithm. [measured] If a reopen trigger later fires, a separate EXP entry with a fixed stopping rule must be written before any comparison is run. [asserted]

Confidence is **high** that no ADR-0025 reopen condition fires and **moderate** that a derived relationship projection will eventually be useful; the latter has no measured demand yet. [asserted]

## Data to gather before architecture

The present event shapes cannot join a route choice to an independent verifier or human verdict while retaining the selected model: `dispatch.outcome` has harness/family and operational status, whereas the sole `attempt.outcome` has task and verifier result but no harness, family or model. [measured] Passive accumulation of those shapes would increase the event count without increasing the model-attributed labelled set. [measured]

The minimum future evidence row needs an immutable attempt/run identifier, task family, eligible pool, selected harness and model version, frozen feature/capability digests, full cost and latency, verifier result, human verdict and evaluator identity. [asserted] This is a proposed measurement contract, not a property of the current records. [asserted]

That requirement extends the existing event authority; it does not justify a new store, graph or learning path, and this report deliberately makes no source change. [asserted] ADR-0074 assigns `events.py` as the writer but does not define the cross-domain dependency semantics needed here, so a later event-link contract must be reviewed explicitly rather than assumed to be authorised by that ADR. [measured] [asserted]

## ADR-0025 reopen conditions

ADR-0025's status and conditions were read from [ADR-0025](../decisions/0025-model-discovery-and-capability-probing.md), and ADR-0003 remains `ACCEPTED` in [ADR-0003](../decisions/0003-no-learned-routing-policy-in-v0.md). [measured]

| Condition | Current evidence | Fires? | What would change the answer |
|---|---|---|---|
| Roughly 5,000 labelled routing outcomes **and** an EXP-07 wasted-work multiplier of at least 2x | The conjunction is explicit in ADR-0025. [measured] The live log has zero model-attributed labelled outcomes. [measured] EXP-07 measured a 1.693x single-attempt median with `insufficient_evidence`; its 17.953x best-of-five result crossed only in the scaffolded arm and remained above the threshold at 16.75x after conservative clamping. [measured] | **No.** The labelled-volume requirement is absent, and the unscaffolded arm did not establish 2x. [measured] | ADR-0025's exact trigger is about 5,000 labelled routing outcomes plus an EXP-07 multiplier of at least 2x. [measured] Model attribution and externally authored labels are additional safeguards proposed by this report, not extra words in the ADR trigger. [asserted] |
| Measured evidence that retrieval, rather than representation, is the memory bottleneck | Current recall is bounded token matching with priority event kinds and oldest-first dropping; it emits no recall or precision measurement. [measured] EXP-45 measured condensation and entity-retention proxies, not retrieval recall or precision on the user's log. [measured] | **No.** The required recall/precision evidence does not exist. [measured] | A frozen, representative query bank over this trajectory showing that retrieval recall or precision is the binding error after controlling for source-record quality and context bounds. [asserted] |
| A published learned router that beats cascade-with-oracle in a domain with cheap verification | The bounded primary-source search below found learned routers and a unified routing/cascading formulation, but no learned router compared against and beating the specific policy “try cheap, execute the cheap verifier, then escalate on failure”. [measured] The unified ICML 2025 paper assumes a perfect SWE-Bench test oracle as an input; it does not report the required learned-router victory. [cited] | **No.** A formulation that assumes the oracle is not the named comparison. [measured] | A published, reproducible comparison in which both policies see the same models, tasks, costs and executed verifier, and the learned policy improves verified success/cost without worsening false acceptance. [asserted] |

The two broader ADR-0025 overturners do not fire either: EXP-20 remains unrun, so neither persistent probe/direct disagreement nor a measured need for more than its 200-task cap has been established. [measured]

## What is graph-shaped now

The project has several relations, but they do not yet form one authoritative graph. [measured]

| Structure | What exists | Architectural consequence |
|---|---|---|
| Plan-unit dependencies | The current plan artefact was a genuine DAG at the runtime snapshot: 57 nodes, 95 edges, no missing dependency targets and no cycles. [measured] `work_items.py` itself records open, comment and complete events but no dependency edge. [measured] | Keep dependency semantics with planning; do not infer that every work item or trajectory event belongs in that DAG. [asserted] |
| Coordination claims | [`coordination.py`](../../src/consilient/coordination.py) projects live claims from events and detects equality or containment between canonical paths with a bounded linear scan. [measured] | Path containment is a relation, but current volume does not justify a graph index. [asserted] |
| Capability records | [`capabilities.py`](../../src/consilient/capabilities.py) currently returns flat `kind`, `name`, `provenance` and `reason` selection metadata. [measured] [ADR-0084](../decisions/0084-compile-portable-capabilities-per-harness-and-refuse-semantic-loss.md) and the memory/capability specification describe prospective version, provenance, `supersedes` and `duplicate_of` edges, but no portable capability is active. [measured] | Preserve stable identifiers and provenance in records; do not pre-emptively materialise a capability graph. [asserted] |
| Trajectory | [`events.py`](../../src/consilient/events.py) is the single append-only writer and exact references must resolve to earlier events. [measured] At the snapshot it had 924 accepted events, six quarantined lines, six top-level event IDs, no explicit top-level dependency or parent references, and seven timestamp inversions. [measured] | Backward references are acyclic, but the file is an ordered source log, not a general DAG and not safe to reinterpret from timestamps. [measured] |
| Recall | [`recall.py`](../../src/consilient/recall.py) is a bounded verbatim projector over events, not a semantic or graph retrieval system. [measured] | Improve it only after recall/precision shows retrieval is the bottleneck. [asserted] |
| Source dependencies | [EXP-130 findings](../10-research/experiments/exp130/findings-exp130.md) measured a Python import graph and derived claim closure over 55 plan units, 127 declared dependencies, 106 Python files and 165 internal imports. [measured] It also found 122 of 180 overlapping pairs without a shared lane, 104 event-kind-coupled pairs without import edges, and a safe-concurrency fall from nine to seven under the derived treatment. [measured] | Use derivation as a disagreement check, never as the authority or replacement for declared claims. [measured] |

EXP-130 was consumed as recorded and was not re-run or re-derived for this report. [measured]

## The one operation a shared relationship view could make cheap

The concrete useful operation is **reverse impact and provenance closure**: given an immutable source, model, harness, verifier, capability or learned-state digest, return every route decision, capability binding, recall receipt, training input, evaluation receipt and published conclusion that depended on it. [asserted] Today that question cannot be answered completely: the event contracts have no typed dependency relation spanning those domains, and scans cannot reconstruct missing causal links. [measured] [asserted]

That operation does **not** justify one physical substrate at current scale. [asserted] After a typed event-link contract exists, the append-only writer could feed a disposable SQLite or in-memory projection while source records remain authoritative; existing IDs alone are insufficient today. [asserted] EXP-130 measured that import-derived closure should check rather than replace declared claims; applying that boundary to a wider substrate is an analogy, not an EXP-130 result. [measured] [asserted]

A persistent shared graph becomes warranted only if repeated impact queries are measured to be slow or error-prone with ordinary joins, or if a required graph algorithm cannot be expressed within the current bounded projection. [asserted] Until then, one graph would mostly make one diagram while adding migration, access-control and common-mode failure costs. [asserted]

## Learning boundary and sealed evaluation

[ADR-0074](../decisions/0074-preserve-records-version-capabilities-and-reserve-training-for-parameter-updates.md) defines training as persistent mutation of learned model state; record, recall and capability selection remain deterministic projections or retrieval. [measured] [ADR-0076](../decisions/0076-owner-gates-persistent-self-change-and-the-instrument-is-sealed.md) requires a frozen impact contract, immutable instrument and baseline digests, a hidden calibration set, an incumbent-controlled evaluator and principal approval before persistent activation. [measured]

A future relationship view must therefore expose two unequal projections rather than one universally readable graph. [asserted]

| Boundary | Candidate may | Candidate must not |
|---|---|---|
| Training view | Read frozen, provenance-complete training records and write a new quarantined learned-state version. [asserted] | Rewrite source events, labels, capability history or the incumbent state. [asserted] |
| Serving view | Read the frozen feature prefix and emit a route or retrieval result. [asserted] | Gate on its own confidence, select its evaluator, or alter thresholds and budgets. [asserted] |
| Evaluation view | Receive only the evaluation input and return a candidate action. [asserted] | Read or write holdout labels, the sealed instrument, calibration cases, verifier policy, human verdicts, beta computation or promotion state. [measured] |
| Promotion | Supply an immutable candidate digest and independently measured outcomes. [asserted] | Approve itself, author a principal verdict, or mutate the incumbent after observing the holdout. [measured] |

Self-reported confidence may be logged for diagnosis but can never be a routing, acceptance or promotion signal; executed verifier outcomes and genuine human verdicts are the signals. [measured] The current same-user dispatch process does not provide the isolation ADR-0076 requires, so putting candidate state and its instrument behind one writable substrate would make the prohibited influence easier, not harder. [measured]

Multiple routers or graph views trained on the same trajectory introduce no different class of facts; consilience comes from executing the artefact, checking an external source or receiving an independently authored human verdict. [asserted]

The useful cross-disciplinary transfer is blinded-trial design: fix endpoints and stopping rules before outcomes, conceal the holdout from the candidate, and let an independent controller compare immutable candidate and incumbent digests. [asserted] A shared logical schema is compatible with that separation; a shared writable authority is not. [asserted]

## The incumbent bar

The repository's citable bar is split between benchmark routing, capability estimation and idealised routing/cascading; none measures this harness's human-labelled false acceptance. [measured]

This report does not claim an absolute August 2026 pinnacle because later retrieved papers are not registered `[FULL]` in the mandatory bibliography and therefore cannot carry a public claim. [measured] Within admissible evidence, the hardest relevant results are RouterBench's failure of learned KNN/MLP to beat its static `Zero` comparator overall, the unified routing/cascading formulation with a perfect SWE-Bench oracle, and IRT-Router's roughly 489,000-tuple capability model. [cited] That bounded bar is sufficient to reject a zero-label GNN build, but not to claim that this project beats the newest literature. [asserted]

| Baseline or bar | Retrieved result | Limit relevant here |
|---|---|---|
| **Live dispatch selector** | `dispatch.py` calls `harness.select`: an explicit eligible harness wins when requested; otherwise installed, known-headroom candidates are ranked by remaining subscription headroom with harness ID as the tie-break. [measured] | This is operational resource selection, not task-quality routing; it supplies no learned or verifier-gated quality baseline. [measured] |
| Proposed probe-and-derive design | ADR-0025 proposes provider discovery, bounded probes and derived capability summaries without needing routing labels. [measured] | ADR-0025 is `PROPOSED`, so this is a design comparator rather than the live incumbent. [measured] |
| Provisional beta-gated cascade | [ADR-0002](../decisions/0002-organise-around-beta-verifier-false-accept-rate.md) makes beta the safety parameter for cheap-first escalation, but [`routing.py`](../../src/consilient/routing.py) is deliberately unwired. [measured] | Human-labelled beta is currently unestimated: `consil beta` reported one rejection, one false accept and `insufficient_data` against the minimum of 30. [measured] |
| Static and learned benchmark routing | [RouterBench, arXiv:2403.12031v2](https://arxiv.org/abs/2403.12031), registered `[FULL]` in the [bibliography](../10-research/bibliography.md), contains 405,467 outcomes over 11 models, eight datasets and 64 tasks; its learned KNN and MLP routers did not significantly beat the static cost-quality `Zero` router overall. [cited] | It evaluates benchmark outcome matrices, not this harness's executed artefacts or human beta. [cited] |
| Preference-trained binary routing | [RouteLLM, arXiv:2406.18665v4, ICLR 2025](https://arxiv.org/abs/2406.18665), registered `[FULL]` in the [bibliography](../10-research/bibliography.md), trains on 65,000 retained pairwise comparisons and routes between a prespecified strong/weak pair. [cited] | Arena-only training was worse than random on GSM8K until in-domain data were added, and the reported transfer is not arbitrary unseen-model adoption. [cited] |
| Capability estimation | [IRT-Router, arXiv:2506.01048, ACL 2025](https://arxiv.org/abs/2506.01048), registered `[FULL]` in the [bibliography](../10-research/bibliography.md), uses about 489,000 graded model-query tuples and reports roughly one-thirtieth of GPT-4o cost. [cited] | Its held-out Claude 3.5 Haiku metadata-only cold start reached 0.67 accuracy and was reported as limited unseen-model generalisation. [cited] |
| Graph routing | [GraphRouter, arXiv:2410.03834v2, ICLR 2025](https://arxiv.org/abs/2410.03834), registered `[FULL]` in the [bibliography](../10-research/bibliography.md), evaluates ten models on 2,400 benchmark queries and still uses 80 measured interactions for an unseen model. [cited] | It uses benchmark accuracy/F1, not repository artefact acceptance, and it is evidence against zero-data graph adoption. [cited] |
| Unified routing/cascading | [A Unified Approach to Routing and Cascading for LLMs, arXiv:2410.10347, ICML 2025](https://proceedings.mlr.press/v267/jitkrittum25a.html), registered `[FULL]` in the [bibliography](../10-research/bibliography.md), jointly optimises routing and cascading against fitted quality/cost estimators. [cited] | Its SWE-Bench evaluation assumes a perfect ground-truth test oracle and does not measure systematic verifier false acceptance. [cited] |

The comparison floor is therefore not “a GNN”; it is the live headroom selector for operational usefulness, the static `Zero` comparator for labelled benchmark routing, and the proposed beta-gated cascade for verified safety under the same task, model, cost and information budget. [asserted]

A shared substrate or learned network would have to demonstrate all of the following before replacement is rational. [asserted]

1. Higher independently verified task success, or lower wall time and cost per independently accepted outcome, than the live selector, probe-and-derive/cascade comparators and strongest reproducible registered learned baseline on the same frozen split. [asserted]
2. A human-labelled false-accept interval no worse than the incumbent, with the ADR-0076 minimum evidence and no candidate access to verdicts or the evaluation instrument. [asserted]
3. Improvement that survives unseen tasks and models, a frozen data/compute budget, and a dominated-choice or routing-collapse check. [asserted]
4. A measured saving from the shared relationship operation itself; if an ordinary event-log join gives the same result within the operational budget, the graph is killed. [asserted]
5. No loss of declared non-Python claims, protocol dependencies, source provenance, principal authority or the ability to rebuild every projection from immutable records. [asserted]

These are acceptance conditions, not an experiment proposal. [asserted] No EXP number is allocated in this report. [measured]

## Evidence against

- The brief's “about five measured units of routing data” overstates the usable evidence: five EXP-07 pairs are synthetic, 149 live dispatch outcomes are operational telemetry without joined verifier labels, and there are zero model-attributed labelled routing outcomes. [measured]
- The only joined human-labelled outcome is a false accept, so beta has no point estimate or interval and `routing_orchestration_enabled` remains `false`. [measured]
- A learned graph fitted now would be determined mainly by schema choices, priors and duplicated operational events rather than outcome evidence; calling that structure “learned” would encode noise with extra authority. [asserted]
- Separate stores reflect real semantic and authority boundaries: a plan dependency, a path claim, a capability provenance edge, a memory selection and a human verdict do not have the same mutability, reader or failure cost. [measured]
- At hundreds rather than millions of events, bounded scans and ordinary joins are cheaper to operate and audit than a graph service or neural training pipeline. [asserted]
- EXP-130 measured that import-derived closure caught hazards but also reduced safe concurrency and missed protocol, event-kind and non-Python relations. [measured] Treating that as a warning about substrate unification is an asserted analogy because EXP-130 did not compare storage architectures. [asserted]
- One writable substrate would enlarge the blast radius of corruption and let a learned candidate approach the labels and instrument that must remain sealed from it. [asserted]
- The registered graph-routing prior art used 2,400 benchmark queries and still required 80 measured interactions for an unseen model; one human verdict here cannot support a stronger learned-graph claim. [cited] [asserted]

## Better-than-best stress-test

- **Mathematical and computational:** relation closure is useful, but the present data fit in bounded scans and joins; a GNN adds estimation error and optimisation variance before it removes a measured bottleneck. [asserted]
- **Physical and mechanical:** one service adds migration, locking, backup and permission failure modes to four mechanisms that currently fail separately. [asserted]
- **Psychological and cognitive:** one diagram makes unlike edges look interchangeable and increases the risk that a reviewer mistakes structural completeness for evidence quality. [asserted]
- **Philosophical and epistemological:** a learner sharing writable state with its evaluator makes evidence circular; the candidate would help construct the test by which it is accepted. [asserted]

The standard answer survives this stress-test: event-sourced facts plus rebuildable, purpose-specific projections are enough until a measured query or labelled outcome volume defeats them. [asserted] The “better” move is not a novel network but a stricter killing rule for one. [asserted]

## Search and source record

Primary-source retrieval was performed on 23 August 2026, but only sources already recorded as `[FULL]` in `docs/10-research/bibliography.md` carry cited claims above. [measured] Later retrieved candidates were excluded because unregistered sources cannot carry a claim under the repository's citation rule. [measured]

Search queries included `learned LLM routing 2026 cost quality cascade`, `cascade-with-oracle LLM router cheap verifier`, `execution-verified agent routing`, `personalized LLM router interaction graph`, and `joint routing cascading MDP`. [measured]

Registered near misses were GraphRouter, whose graph uses benchmark outcomes and 80 interactions for an unseen model; RouteLLM, whose 65,000 comparisons support a fixed strong/weak pair; IRT-Router, whose roughly 489,000 graded tuples still produced limited metadata-only unseen-model generalisation; RouterBench, whose learned routers did not significantly beat its static `Zero` router overall; and the unified ICML 2025 formulation, which assumes the SWE-Bench oracle rather than measuring its false acceptance. [cited] None tests a learned router against the exact cheap executed-verifier cascade named by ADR-0025. [measured]

Internal sources were ADR-0002, ADR-0003, ADR-0025, ADR-0068, ADR-0074, ADR-0076, ADR-0077, ADR-0084 and ADR-0091; `coordination.py`, `events.py`, `work_items.py`, `recall.py`, `capabilities.py` and `routing.py`; EXP-07, EXP-45 and EXP-130 findings; and the read-only `consil beta` and `consil doctor` outputs captured during this run. [measured]

## Plain answer and delta

The plain answer is **gather data first and build nothing**. [asserted] The additional work establishes why: every ADR-0025 trigger is false, the live model-attributed labelled routing set is empty, the registered literature does not test the named oracle cascade, the only concrete cross-domain graph operation first needs an explicit link contract, and a shared writable substrate would weaken the sealed evaluation boundary. [measured] [asserted]

The decision can be reversed without undoing code: accumulate typed immutable outcomes, re-check the three named conditions, and preregister a matched comparison only after a condition fires. [asserted]

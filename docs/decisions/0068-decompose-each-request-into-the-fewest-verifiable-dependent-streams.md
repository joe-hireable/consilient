# 0068. Decompose each request into the fewest verifiable dependent streams before composing squads

- **Status:** PROVISIONAL — EXP-98 can confirm or kill the protocol only for its frozen v0 mixture
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product direction only, quoted in the source note); Codex dispatch
  `20260822T120918-df89e4f59d` (provisional mechanism pending EXP-98)
- **Inquiry tier reached:** T2 model; T3 registered as EXP-98, not run
- **Executable model:** `0068-model.py` — encodes EXP-98's decision regimes; it does not estimate
  decomposition value or duration

## Context

The claim that large deliverables become large organisations because they contain more scoped
decisions is this ADR's interpretation, not Joe Brown's wording. [asserted] Joe said that a website
needs branding, development, motion, QA and automation teams; a single document does not; every task
still needs a better-than-best definition; and Consilient may estimate a long duration before
returning the finished product. [measured: textual attribution in
`../00-context/the-machine-2026-08-22.md`] He did not specify the mechanism below. [measured]

This ADR extends ADR-0067 rather than changing it. [asserted] ADR-0067 governs the evidence
composition for one scoped decision: default one member, one candidate and one accountable Owner;
another member is admitted only for a concrete, non-overlapping, decision-changing evidence anchor.
[cited: ADR-0067] A work-stream name, specialism or model family creates no new evidence. [cited:
ADR-0067]

The local trajectory records a sharp decline in dispatch success but does not identify its cause.
[measured] At 22 August 2026 13:15 BST, its first 35 dispatch outcomes contained 24 `ok` results
(68.6%), while all 84 then
recorded contained 36 `ok` results (42.9%) and 29 timeouts. [measured: `.harness/log/*.jsonl`, full
`dispatch.outcome` census] The brief's earlier 27-timeout figure was a true earlier snapshot, not the
current count. [measured] One timed-out dispatch recorded 3,492,819 artefact bytes; the ADR it was
writing was committed from retained worktree state two minutes after the timeout. [measured:
dispatch `20260822T111814-b49738fe69` and commit `e2412a1`] A timeout can therefore discard
execution state even while worktree artefacts survive; persistence is not resumability. [measured]
The association justifies bounded slices, not a causal claim that decomposition repairs it.
[asserted]

The current runtime resumes accounting, not work. [measured] `scripts/run_loop.py` records intent and
appends transcript bytes; on restart `loop.py` marks an unsettled tick abandoned and advances rather
than resuming its process or deliverable. [measured] `coordination.py` provides expiring path claims,
but no dependency, readiness, checkpoint or shared-artefact disagreement state. [measured] Dispatch
also checks a claim snapshot and appends its new claim in separate operations, so two contenders can
pass the same stale check. [measured: deterministic source interleaving] These primitives are the
base to extend; they are not already the mechanism this ADR specifies. [asserted]

### Incumbent bar

[Magentic-One's central Orchestrator](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/)
decomposes work while maintaining separate task and progress ledgers. [cited: Microsoft Research,
*Magentic-One*, 2024] [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
exposes a shared task list with dependencies and a lead that synthesises results, while its own
documentation warns that teams add substantial token and coordination cost and are a poor fit for
sequential or same-file work. [cited: Anthropic, *Orchestrate teams of Claude Code sessions*,
retrieved 22 August 2026] [Temporal](https://docs.temporal.io/) is the durability bar: workflow
state is persisted so execution can replay after a process or infrastructure failure. [cited:
Temporal documentation, retrieved 22 August 2026]

This ADR must beat that composite without adding a dependency: ledgered decomposition, dependency
readiness and restart from durable state, plus Consilient's stricter frozen verifiers, measured beta,
smallest-organisation rule and preserved dissent. [asserted] EXP-98 decides whether that extra
discipline beats the actual incumbent that matters here — one capable Owner with the full request,
all tools and the same aggregate budget. [asserted]

This is a wide protocol and future schema decision with dispersed priors. [asserted] The formal
decision variable is organisation versus coherent single Owner, the objective is verified-and-human
accepted output per review-adjusted minute, and the unknown is the coordination penalty. [asserted]
`0068-model.py` therefore fixes the decision regimes while EXP-98 measures the unknown. [asserted]

## Decision

Before execution, Consilient will turn one request into the **smallest directed acyclic graph of
independently verifiable streams** that satisfies the request contract. [asserted] Each leaf is one
scoped decision composed under ADR-0067; one Delivery Owner owns the final integrated candidate, and
final integration is itself a stream with a frozen end-to-end verifier. [asserted]

The organisation is large only when the minimum graph has many leaves. [asserted] Headcount inside a
leaf remains ADR-0067's separate evidence decision and defaults to one. [cited: ADR-0067]

### 1. Freeze the request contract before making the map

The Delivery Owner appends one canonical `organisation.plan.frozen` record to the private trajectory
before any stream is claimable. [asserted] It contains: [asserted]

- request, authority, non-goals, total quota and expiry; [asserted]
- the incumbent artefact or process, its source/version/retrieval date, and the bounded search used
  to find it; [asserted]
- the measurable delta that would be better than that incumbent, plus the final human acceptance
  boundary; [asserted]
- every success condition, verifier identifier and verifier digest; [asserted]
- stream identifiers, one deliverable per stream, owned paths, dependencies, hand-off schema,
  checkpoint requirement and ADR-0067 composition manifest; [asserted]
- the integration stream, duration range and derivation, and the digest of the whole record.
  [asserted]

For a small task, the incumbent may be the last accepted repository analogue, its current test, or a
named reference document; finding the bar does not require a market survey when the acceptance
boundary is local and obvious. [asserted] If a bounded search finds no incumbent, the record names
the sources and queries searched, uses the strongest observed baseline, labels the criterion
`[asserted]`, and still proceeds. [asserted] The Delivery Owner writes this technical contract; the
principal is asked only for a preference or authority that no artefact can decide. [cited: ADR-0033]

Every claim, checkpoint and verifier receipt carries the frozen plan digest. [asserted] Once any arm
has executed, neither Owner nor worker may edit that criterion or verifier in place. [asserted] A
legitimate requirement change appends a new plan version with its cause and predecessor digest; an
outcome produced against the old criterion cannot satisfy the new one and affected checks rerun.
[asserted] A dependency-only revision may reuse a sealed predecessor only when its deliverable,
verifier and plan-relevant inputs are byte-identical. [asserted] This permits a living plan without
outcome-aware rebaselining. [asserted]

### 2. Decompose to the minimum graph, then stop

A proposed boundary survives only when **both** tests pass: [asserted]

1. Each side ends in a separately named deliverable or constraint, a frozen verifier and a sealed
   hand-off that a consumer can check without reading the producer's reasoning. [asserted]
2. Removing the boundary would erase a real dependency, require two owners for incompatible mutable
   scope, hide which independently rejectable outcome failed, or make the next execution slice exceed
   the empirical completion cap recorded in the plan. [asserted]

This is the stopping condition against collapse: two outcomes must not be merged when one can fail
and be rejected independently, or when a consumer could otherwise start before its prerequisite is
verified. [asserted] It is also the stopping condition against runaway decomposition: stop as soon as
every leaf has one deliverable, one Owner and mutable scope, one frozen verifier contract, and a
bounded next slice, and no proposed child passes both tests. [asserted] Among all graphs that pass,
choose the one with the fewest leaves and then the fewest dependency edges. [asserted]

| Candidate distinction | Treatment |
|---|---|
| A second verifier checks the same artefact | One stream; the verifier is an ADR-0067 evidence role, not another stream. [asserted] |
| A different specialism, title, prompt or model reads the same inputs | No boundary; it is organisation theatre. [cited: ADR-0067] |
| A separately checkable output constrains a downstream output | Two streams with a digest-bound dependency edge. [asserted] |
| Two disjoint outputs have separate verifiers and mutable scopes | Parallel streams if quota and review capacity admit both. [asserted] |
| Two outputs edit the same integration surface | Producers stay isolated; one downstream integration stream owns the surface. [asserted] |
| Work is long but has no separately verifiable hand-off | One stream across bounded execution slices; time alone does not invent a team. [asserted] |

The empirical completion cap comes from comparable trajectory outcomes under the same task and
verifier class, never prompt length or apparent importance. [asserted] With fewer than five
comparable completions, the plan records a low-evidence estimate and requires an early checkpoint
rather than pretending a measured cap. [asserted] An execution slice may be shorter than a stream;
another slice resumes the same ownership and acceptance exposure from the sealed checkpoint.
[asserted]

### 3. Make duration a visible, immutable forecast contract

Before work starts, the user sees a duration range, its evidence class, the frozen success criterion
and the point at which Consilient will return the finished artefact. [asserted] Comparable completed
runs supply per-stream duration ranges; the organisation range is the resource-constrained critical
path through the DAG plus integration, final verification and human review. [algebra] Parallel
worker-minutes are summed for quota even when wall time overlaps. [algebra]

With no comparable runs, the Owner still gives a range derived from frozen slice budgets, labels it
`[asserted: low evidence]`, and names EXP-98 as its calibration path. [asserted] The original range is
append-only. [asserted] If new evidence predicts a miss, Consilient records the cause and replacement
range before the original upper bound and sends one exception notice; it does not silently move the
old range. [asserted] Routine stream-by-stream progress reports are omitted. [asserted] Work continues
within the frozen authority and quota; a reforecast crossing spend, expiry or an irreversible action
stops at the existing authority boundary. [cited: ADR-0033]

The completion response contains the finished artefact, verifier outcomes, unresolved dissent, the
original range and actual duration. [asserted] An incomplete artefact is reported as incomplete, not
renamed progress. [asserted] No user-visible duration commitment exists in current code, and EXP-98
must calibrate this method before it is described as reliable. [measured] [asserted]

### 4. Sequence dependencies and survive restart

Every stream records immutable predecessor identifiers and expected predecessor artefact digests.
[asserted] A stream is ready only when every predecessor is terminally complete, its frozen verifier
accepted, and its sealed digest matches the dependency. [asserted] Refused, expired, invalid or
failed predecessors block consumers; changing the route requires a new plan version, not pretending
the dependency was optional. [asserted] Cycles and missing predecessors are rejected before the first
claim. [asserted]

`coordination.py` remains the claim chokepoint, extended so read-conflict-open is serialised under a
kernel-released acquisition lock. [asserted] Mutable streams must claim explicit paths; a pathless
claim cannot authorise parallel mutation. [asserted] Only ready streams may claim, and the claim binds
the plan digest, stream identifier and predecessor digests. [asserted]

At the end of every bounded slice, the stream seals a checkpoint containing the plan digest, base
tree, attributed Git tree or commit, owned paths, artefact digests, verifier receipts, terminal state
and next action. [asserted] The Git object remains reachable from a local per-stream checkpoint ref;
transcript bytes or a process identifier are not a checkpoint. [asserted] Existing trajectory,
transcript, work-item and attribution primitives are reused. [measured]

After restart, `run_loop.py` may keep its honest `abandoned/outcome=unknown` tick. [asserted] The plan
projector reconstructs the DAG, verifies checkpoint objects and digests, and dispatches a new attempt
for the ready unfinished stream; it never claims that the killed process resumed. [asserted] A
completed stream is not rerun, and no consumer starts from an unverifiable checkpoint. [asserted]

### 5. Resolve shared-artefact disagreement without last-write-wins

Parallel producers work in isolated trees and cannot write the integration surface. [asserted] The
integration Owner receives sealed alternatives only after their streams finish. [asserted] If a
frozen verifier distinguishes them, its result decides; if a new execution can decide within budget,
that execution becomes one bounded resolution stream. [asserted] If facts cannot decide, the
Delivery Owner selects any option above the recorded acceptance floor, records why the other lost and
its reversal, or escalates only a principal-reserved preference or authority. [cited: working
principle 11 and ADR-0033]

Every material conflict is dispositioned as `resolved_by_evidence`, `owner_selected_reversible`,
`escalated`, or `recorded_unresolved` before downstream work unblocks. [asserted] Voting, averaging,
message volume and last writer never select a shared artefact. [asserted] Dissent remains in the
trajectory and the final response. [asserted]

## Evidence

- `[measured]` The trajectory census above shows falling artefact-producing dispatch reliability
  across its sequence, 29 timeouts, and a 3.49 MB timed-out run whose file changes outlived the
  process; it does not identify why the decline occurred.
- `[measured]` Current loop state preserves intent/transcript but marks interrupted work abandoned;
  current claims have no dependencies or checkpoint identities, and claim acquisition is not atomic.
- `[measured]` EXP-16's strong single arm won 9/12 blind model-grader judgements; its Owner meeting
  won 2/12 at 4.8 times the tokens and 3.7 times the wall-clock. Its planned human oracle was not
  obtained, so the two substituted model-family graders answered a narrower question. The
  operational prior still favours one, weakly.
- `[cited]` Magentic-One demonstrates central task/progress ledgers; Claude Code Agent Teams
  demonstrates dependency-aware shared tasks and documents its overhead and poor-fit regimes;
  Temporal demonstrates durable replay after failure.
- `[cited]` [Kim et al. (2026), *Capable language models can outgrow the benefits of
  collaboration*](https://www.nature.com/articles/s42256-026-01268-y), *Nature Machine
  Intelligence*, held prompts, tools and compute budgets constant across 260 configurations and
  found the strong single baseline the most robust predictor of coordination's sign.
- `[algebra]` Total worker quota sums parallel effort, while elapsed duration follows a
  resource-constrained critical path plus serial integration, verification and review.
- `[asserted]` The minimum-graph predicates will preserve coherence while exposing independently
  rejectable boundaries. EXP-98 is the killing test.

## Evidence against

- `[measured]` The strongest direct result in this repository favours one capable agent, not an
  organisation: 9/12 blind model-grader wins versus 2/12 for the Owner meeting, at much lower token
  and wall cost. The sample is small and the planned human oracle was replaced by two model-family
  graders that the result file says answered a different question.
- `[cited]` Kim et al.'s controlled comparison found coordination gains and losses by task, with
  single-agent strength the robust selection signal. A generic rule that “bigger work needs more
  agents” is therefore not supported.
- `[cited]` Anthropic's own Agent Teams guidance says sequential work, same-file edits and dense
  dependencies are better handled by a single session, and that teams use substantially more tokens.
- `[asserted]` One capable Owner holding the whole website can preserve brand intent through code,
  motion and QA without lossy hand-offs, duplicated reading, interface drift or an integration
  bottleneck. Four streams can each be locally correct while their assembled product is incoherent.
- `[measured]` This worktree already has a check-then-open claim race and pathless live claims. Adding
  a DAG above unsafe acquisition would make collisions more systematic, not less.
- `[algebra]` More streams add edges and review surfaces; parallel execution reduces wall time only
  where the critical path and quota allow it, while human review minutes still sum.
- `[asserted]` EXP-98 itself requires 240 arm results and blind verdicts, so its attempt to protect
  principal attention imposes substantial one-off review debt. Its frozen coding mixture cannot
  establish website or non-coding transfer.

The coherence objection is **conceded provisionally**, not answered by architecture prose. [asserted]
One remains the operational default, tightly coupled work should collapse aggressively, and EXP-98
must beat both a normal-budget and aggregate-budget coherent single Owner before decomposition is
called better. [asserted]

## Consequences

**Positive** — request size becomes an auditable graph of acceptance boundaries rather than a guessed
headcount; dependencies, original success criteria, duration misses, checkpoints and dissent survive
restart and synthesis. [asserted]

**Negative** — every retained boundary adds plan state, Git objects, integration work and review
cost. [asserted] Long indivisible work gains checkpoints but no artificial parallelism. [asserted]

**Neutral but load-bearing** — ADR-0067 still decides each stream's composition; one Delivery Owner
submits one final candidate; `routing_orchestration_enabled` stays `false`; Gate A and Gate B do not
move; orchestration remains `scripts/dispatch.py`; no seventh CLI command or dependency is added.
[asserted] Temporal is a benchmark, not an adopted component. [asserted]

## Enforcement

EXP-98 was preregistered before this ADR in commit `fc6c321`; before any run, this commit makes its
safety regime explicit and records the protocol, executable decision regimes, CI check and index
row. It adds no product implementation or gate change. [measured]

- Check now: `tests/test_decision_models.py` executes every `NNNN-model.py`; ADR trail and provisional
  experiment-reference checks cover the record. [measured]
- Future same-commit checks at `dispatch.py`, `coordination.py`, work items and loop replay must reject:
  an unfrozen or changed success digest; a cycle or unready claim; non-atomic conflicting claims;
  mutable pathless streams; a consumer with a missing/mismatched predecessor; a completed stream
  rerun after restart; a lost checkpoint; a shared-artefact write outside integration; and a material
  conflict without disposition. [asserted]
- A fixture must prove an atomic request stays one stream, a separately verifiable dependency splits,
  and specialism alone does not split. [asserted]
- A process-tree kill test must preserve a sealed checkpoint, mark the killed attempt unknown, resume
  with a new attempt and never duplicate the completed predecessor. [asserted]
- A duration fixture must retain the original range and append a pre-breach reforecast rather than
  overwriting it. [asserted]
- Fails CI today: only the model and record checks; protocol checks await the implementation they
  govern. [measured]
- Added in the same commit as implementation: no implementation is added here; every future protocol
  invariant above is a same-commit condition. [asserted]

## What would overturn this

EXP-98 compares an operational single, an aggregate-budget-matched single and this organisation over
80 frozen requests spanning atomic, separable and tightly coupled work. [asserted] Decomposition is
confirmed only if it beats both singles by at least 0.10 joint human-and-verifier success with both
paired interval lower bounds above zero, stays within the registered beta/alpha and review-adjusted
cost limits, collapses all atomic requests, and loses no dependency, shared artefact or checkpoint.
[asserted]

Beating only the operational single attributes the gain to compute; B meeting or beating C, or C
increasing blinded review minutes per accepted success, concedes the overhead objection for the
mixture. [asserted] Any checkpoint loss or early dependent cuts the resumable claim immediately;
an isolated dependency violation or overwrite prevents confirmation but does not alone kill the
whole protocol. [asserted] Duration is
confirmed separately only at 80% or greater original-range coverage with every predicted miss recorded
before breach. [asserted] Any other result is unresolved, not equivalence. [asserted]

## Publication candidate?

**No.** The mechanism is provisional, the local reliability figures are instance data, and the
coherence objection is unresolved. [asserted] Reconsider after EXP-98 publishes its full outcome,
safety, review, duration, invalidity and recovery tables. [asserted]

## Update: 2026-08-22 — executable regime ordering corrected

The model's first CI execution failed its own matched-control boundary check. An observation that
beat the operational single but had zero gain over the matched-compute single satisfied both the
`CUT_AS_COMPUTE` and `CUT_OVERHEAD` predicates; branch order returned `CUT_AS_COMPUTE` before the
more specific matched-control failure could be applied. [measured: `0068-model.py` self-check]

The matched-control non-improvement and review-overhead predicate now runs first. This changes the
executable conclusion for that overlapping regime to `CUT_OVERHEAD`, matching this ADR's statement
that a matched single meeting or beating the organisation concedes the overhead objection. It does
not change the provisional decision or any observed EXP-98 result; EXP-98 has not run. [measured]

This correction is appended because the ADR is PROVISIONAL and the failed executable conclusion is
part of its evidence trail. [asserted]

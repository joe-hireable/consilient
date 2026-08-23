# Agent catalogue: task profiles over four fact-bearing contracts, crossed with subject expertise

**Correction:** beta bounds candidate exposure, not squad headcount; model or provider family alone
has zero evidence credit; a missing required capability is a refusal rather than a degradation; and
live dispatch now assembles and records layered instructions but still does not bind selected
capability metadata or task-scoped role requirements to native runtime surfaces. [measured:
ADR-0077; ADR-0082; ADR-0084; `scripts/dispatch.py:969-981,1280-1304`]

- **Date:** 2026-08-23. [measured]
- **Status:** specification only; [ADR-0093](../../decisions/0093-compose-agent-roles-from-worker-method-and-subject-expertise.md)
  is PROVISIONAL. [measured]
- **Killing experiment:**
  [EXP-136](../../10-research/experiment-register.md#exp-136--does-a-worker-method-profile-beat-the-same-capable-generalist-with-the-same-facts-tools-and-budget-blocked)
  tests whether these profiles add outcome value or are one model in different costumes. [asserted]
- **Scope:** portable, task-scoped role composition for the closed work taxonomy in
  `2026-08-23-work-taxonomy.md`; no product implementation, source-path promise, new CLI command,
  gate change, routing activation or model training is included. [measured] [asserted]

## 1. Decision first

An agent role is composed for one work item from two independent axes: a **worker-method profile**
says what work category is being performed and selects one of four fact-bearing execution contracts,
while one or more **subject-expertise bundle references** say which domain sources, vocabulary,
examples and tools are admissible. The task contract, fact contract, bounded memory and target-
harness binding complete the run-local instance. [asserted]

`role_instance = worker_profile + worker_contract + expertise_refs + task_contract + fact_contract + capability_binding + bounded_recall`
[asserted]

The repository stores thirteen small category profiles, four worker contracts and each versioned
expertise bundle once. It does not store `researcher-in-genomics`, `researcher-in-payments` or any
other pair. A role instance is a content-addressed, run-local compilation and expires with its work-
item assignment. For `P` profiles, `C` contracts and `E` expertise bundles, durable catalogue state
is `O(P + C + E)`, not `O(P x E)`; compiled instances are receipts rather than catalogue members.
[algebra] [asserted]

The default is still one accountable Owner, usually the strongest eligible generalist, which may
execute several worker methods sequentially. A second runtime is admitted only when a task-scoped
fact contract requires isolated acquisition, a capability/state unavailable to the Owner, or a
non-overlapping artefact scope whose output can change the decision. Repeating the same method,
sources and context through another persona or model is echo. [measured: ADR-0067; ADR-0082]
[asserted]

The work-taxonomy stream owns the thirteen measurement labels and their three phases. This document
gives every category a native task-scoped profile, but a profile does not imply a separate runtime.
Only four contracts earn evidence-bearing worker status; framing, innovation, synthesis and planning
remain Owner methods. This resolves the principal's "categories are agents" outcome without turning
measurement labels into standing staff. [measured] [asserted]

## 2. The two axes

### 2.1 Worker method

`worker_profile` is a closed, versioned mapping from one of the thirteen `work_category` values to a
procedure, output and refusal rule. An evidence-bearing profile selects one `worker_contract` from
`acquirer`, `instrumenter`, `realiser` or `assessor`; an Owner profile selects no additional worker.
This is one method axis with a measurement view and an execution view, not a third taxonomy.
[asserted]

A capable generalist may execute any profile. That does not make the profile redundant: it freezes
method and receipts. It also does not justify another squad member. Another runtime appears only
when the selected contract needs isolated acquisition or non-overlapping state/capability; otherwise
the Owner executes the profile directly. [asserted]

### 2.2 Subject expertise

`expertise_refs` names zero or more ADR-0086 capability-bundle digests. A bundle supplies scoped
primary sources, open datasets, vocabulary, worked examples, tools, provenance, licence/consent,
validity and a sealed evaluation record. It never supplies authority, a verdict, a gate lift or an
independence claim. [measured: ADR-0086] [asserted]

No global list of domains is maintained. `genomics`, `payments` or a narrower subject exists only as
the purpose and postcondition of an immutable expertise bundle. Cross-domain work composes the
smallest set of independently valid bundles; incompatible permissions, destinations or verifier
semantics refuse rather than merge. [asserted]

A bundle is not automatically an evidence anchor. Three roles reading the same payments bundle
have one source class. Evidence credit belongs to the independently acquired observation named by
the fact contract, never to the bundle label, role label, harness or model family. [measured:
ADR-0081; ADR-0082] [asserted]

## 3. The worker catalogue

The fact-bearing catalogue has four contracts. Each must produce the named sealed observable; if a
task-specific fact contract cannot bind that observable to an admitted source or execution surface,
the role does not launch. [asserted]

| `worker_contract` | Eligible different class of facts | Minimum execution contract | Category profiles |
|---|---|---|---|
| `acquirer` | A new primary-source record, public/open dataset observation, browser/live-system observation or repository-state observation absent from the Owner's frozen evidence manifest. [measured: ADR-0081] [asserted] | Retrieve or inspect the named anchor, retain identity/time/digest/locator, licence where relevant, omissions and failures, then seal before synthesis. Snippets and model memory do not satisfy it. [measured: citing-sources skill] [asserted] | `discovery`, `research` [asserted] |
| `instrumenter` | An executed experiment, simulation, formal/algebraic check or data analysis with frozen premises/procedure and raw outputs. A model-imagined result contributes nothing. [asserted] | Pre-register when empirical, execute the producing script or formal model, retain adverse/missing outcomes and apply the fixed stopping or sensitivity rule. `[simulated]`, `[algebra]` and `[measured]` remain distinct. [measured: running-experiments skill] [asserted] | `experiment`, `simulation`; supports `innovation` only through an executed transfer test. [asserted] |
| `realiser` | The target artefact, diff, build observation or authorised delivery/read-back receipt from owned state. This is responsible work, not independent evidence that the result is correct. [asserted] | Work from the frozen realisation package, retain artefact and tool-result digests, never reopen the goal/verifier, and perform an effect only inside existing authority. [asserted] | `implementation`, `delivery`; specification when the specification itself is the requested artefact. [asserted] |
| `assessor` | An independently executed frozen oracle/comparison, hostile counterexample or isolated reacquisition against a candidate hidden from the author path. [measured: ADR-0067; ADR-0081] [asserted] | Bind candidate, comparator and acceptance digests; execute once; retain every unavailable result; give same-diff opinion, persona and family difference zero credit. [asserted] | `assessment`, `verification`; `debate` only when it becomes an executed counterexample or new source acquisition. [asserted] |

The Owner/generalist is accountable but is not a fifth evidence role. It supplies governance
provenance and runs the profiles whose outputs are decisions or plans rather than new facts.
[measured: ADR-0067; ADR-0082] [asserted]

### 3.1 Every category still has a native profile

| Work category | Native task-scoped profile |
|---|---|
| `framing` | Owner resolves the authenticated task, authority, scope, consequence, reversal and unknowns; it receives no independent anchor credit. [asserted] |
| `discovery` | `acquirer` inspects actual system state and candidate incumbents. [asserted] |
| `research` | `acquirer` retrieves and verifies primary sources or open data. [asserted] |
| `experiment` | `instrumenter` freezes and runs the empirical protocol. [asserted] |
| `simulation` | `instrumenter` runs the declared formal model and sensitivity analysis. [asserted] |
| `debate` | `assessor` executes a counterexample or contrary acquisition; rhetorical exchange stays Owner deliberation and earns zero credit. [asserted] |
| `innovation` | Owner proposes the transfer; `acquirer` retrieves the foreign mechanism and `instrumenter` runs its falsifier when those facts are needed. [asserted] |
| `synthesis` | Owner applies the frozen decision rule to sealed evidence, emits one candidate and dispositions dissent; this is derivation, not another anchor. [asserted] |
| `assessment` | `assessor` executes the frozen comparison/acceptance contract. [asserted] |
| `planning` | Owner derives the smallest verifiable work graph; live dependency/import facts are acquired through `acquirer` rather than invented. [asserted] |
| `implementation` | `realiser` creates the target artefact. [asserted] |
| `verification` | `assessor` executes the independent oracle against the realised artefact. [asserted] |
| `delivery` | `realiser` performs the authorised hand-off and retains destination read-back or refusal. [asserted] |

Thus every category is executable natively, but only a concrete fact contract can justify another
runtime. Most requests should still use one Owner/generalist across several profiles. [asserted]

## 4. Techniques and titles deliberately cut

These names do not become additional `worker_contract` values. Their useful mechanics remain inside
the profiles or subject axis. [asserted]

| Cut role | Why it is cut | Where the real work goes |
|---|---|---|
| `framer`, `innovator`, `synthesiser`, `planner` | Their outputs are governance, hypotheses, decisions or work graphs rather than independent evidence. A second agent would add a title without a fact class. [asserted] | Keep the native category profile in the accountable Owner; dispatch an `acquirer` or `instrumenter` only for a concrete missing fact. [asserted] |
| `hypothesiser` | A hypothesis is a falsifiable candidate statement, not a class of observed facts; a persona generating more guesses adds echo. [asserted] | Freeze a content-addressed hypothesis inside `framing`, `innovation`, `experiment` or `simulation` before the run. [asserted] |
| `mathematical_modeller` | Mathematical modelling is an instrument mode; exact derivation and assumed-model output need different evidence tags, not different agents. [asserted] | `instrumenter` returns `[algebra]` proof/counterexample where exact and `[simulated]` sensitivity otherwise. [asserted] |
| `data_scientist` | Data science names a broad discipline, not one work purpose; the same dataset operation may discover, experiment, simulate or assess. [asserted] | Use `acquirer`, `instrumenter` or `assessor` according to the estimand, with data tooling in the capability request and domain data in the expertise bundle. [asserted] |
| `specifier` | A specification is a contract artefact, not an independent fact source. [asserted] | Use Owner `planning` when preparatory or `realiser`/`implementation` when the specification is the requested deliverable. [asserted] |
| `domain_specialist` | Domain is the orthogonal expertise axis. Encoding it as a worker contract recreates pairwise agents and ambiguous inheritance. [asserted] | Bind one or more ADR-0086 `expertise_refs` to any category profile. [asserted] |
| `reviewer`, `critic`, `auditor`, `adversary` | The title says nothing about the observation. A review that only rereads the author's material is echo. [measured: ADR-0067] [asserted] | Use `assessor` for an executed oracle/counterexample or `acquirer` for a contrary primary source. [asserted] |
| `replicator` | Replication is an isolation constraint on acquisition, not a method or evidence class; another model seeing the same evidence is not replication. [measured: ADR-0067; ADR-0082] [asserted] | Re-run `acquirer`, `instrumenter` or `assessor` in an isolated snapshot against a separately named anchor. [asserted] |
| `manager`, `coordinator`, `middle_manager` | Existing work items, claims and one Owner already coordinate; another agent adds no truth-relevant fact and cannot inherit the principal's authority. [measured: ADR-0067; ADR-0082] [asserted] | `work_items.py` holds responsibility, `coordination.py` claims work and the Owner decides within existing rights. [measured] |
| `persona` or model-family roles | Tone, title, prompt and provider change no source class. [measured: ADR-0081; ADR-0082] | Keep model/harness as routing and correlation metadata; credit only the executed observation. [asserted] |

This cut is load-bearing. Adding a new worker contract requires a fact class none of the four can
express and an EXP-136-class matched test. Adding a category profile requires a successor to the
work taxonomy. Catalogue growth is not a marketplace count. [asserted]

## 5. Dynamic assembly, fail closed

### 5.1 What one role declares

A work-item revision requests a role using the existing ADR-0074 capability and ADR-0084 binding
path. The semantic record contains only these concerns; it is not a second manifest format.
[asserted]

1. `worker_profile`, `worker_contract|null`, their versions and the matching immutable
   `work_category`/phase. [asserted]
2. `expertise_refs`, each an immutable ADR-0086 manifest digest or an empty list for a generalist.
   [asserted]
3. `fact_contract`: acquisition channel, source/anchor contract, expected receipt, evidence-tag
   ceiling, possible decision change, isolation and derivation-root exclusions. [asserted]
4. `capability_request`: exact kind/name, required semantics, reason and whether the semantic is
   required or optional. Existing kinds stay `tool`, `mcp`, `skill`, `plugin` and `connection`.
   [measured: `capabilities.py`] [asserted]
5. `context_request`: task/authority refs, workspace/destination, bounded memory query and permitted
   source refs; raw protected content is filtered before rendering. [asserted]
6. `effects`, `limits`, `postcondition`, `verifier`, output schema and expiry. [asserted]
7. Optional, pre-declared fallback role contracts, each with its own digest, reduced postcondition
   and evidence ceiling. [asserted]

`capabilities.py` remains the sole selector. `instructions.py` assembles invariant core, selected
skills, bounded recall and adapted content. `dispatch.py` remains the caller and harness adapter;
`events.py` records the pre-launch binding and later outcome. `work_items.py`, `coordination.py`,
`routing.py` and `budget.py` retain their current responsibilities. A role registry, second loader,
second memory service or second orchestrator is a defect. [measured: ADR-0074; ADR-0084] [asserted]

Today this end-to-end role path does not exist. `select_capabilities()` validates an exact allowlist
and raises on malformed, unknown or unavailable items, but returns metadata only; it has no required
semantics, optional-loss or application receipt. Live dispatch now calls and records
`instructions.assemble()`, but exact role requirements are not inputs to that selector and a
required selected skill can still lose to the general skill/count/character limits. The design
therefore claims future binding behaviour only. [measured: source inspection, 2026-08-23]

### 5.2 Resolution states

Binding finishes before any child starts in exactly one state. [asserted]

- **`applied`:** every required semantic and chosen optional semantic is represented on the probed
  harness version, generated artefacts re-read by digest and the fact contract remains attainable.
  [asserted]
- **`degraded`:** only an optional semantic is absent or narrowed; the exact loss, reduced
  postcondition and evidence ceiling appear in both brief and trajectory receipt. If the missing
  semantic supplied the role's fact class, the role loses evidence credit and is removed or becomes
  non-contributing rather than pretending to have run. [asserted]
- **`refused`:** a required capability, semantic, boundary, credential isolation, version proof,
  expertise validity, fact contract or post-bind digest is absent. The original role does not launch.
  [measured: ADR-0084] [asserted]

A required loss may use a pre-declared fallback only by opening a new work-item/role revision with a
new digest and explicit `degraded_from` reference. That fallback is a different, weaker contract;
calling the original role degraded would make its false belief durable. No runtime may invent a
fallback after seeing the unavailable capability or a candidate result. [asserted]

The receipt records the role-instance digest, task/work-item revision, worker/expertise/capability
versions, harness/adapter probe, generated artefact digests, memory receipt, state, every loss and
reason, effective effects and fact-contract eligibility. Later observed use is `yes`, `no` or
`unknown`; selection or loading is not evidence of use. [asserted]

## 6. Portability: what travels and what does not

Portability extends ADR-0084; it does not reopen the decision or promise equivalence where native
surfaces differ. The semantic source travels, and a tested adapter compiles it for one installed
harness version. [measured] [asserted]

| Artefact | Honest portability |
|---|---|
| Canonical worker-method and role-request manifests | **High as data.** Names, fact/postcondition contracts, capability semantics, rights, limits and output schemas travel. A rendered Claude/Codex/Cursor/Grok agent file is generated output, not the authority. [asserted] |
| Subject-expertise bundle | **Conditional.** Public/licensed sources, examples, tool declarations and provenance travel to an authorised compatible destination; private, consent-scoped, stale or destination-bound payloads do not. [measured: ADR-0086] [asserted] |
| Memory | **High for the scope policy, bounded selected bytes and receipt; low for vendor memory.** The same filtered pack can travel; vendor-native retrieval, curation and ambient persistence remain uncontrolled or destination-specific. [measured: ADR-0084] [asserted] |
| Skills | **High for the Agent Skills core.** Markdown instructions and bundled files travel; scripts still require a compatible OS/runtime, and vendor permission/model/hook extensions do not. [cited: Agent Skills specification, retrieved 2026-08-22] [asserted] |
| MCP | **Medium.** Protocol, server identity and common transports travel; host negotiation, auth, consent, environment and tool filtering vary. Credentials never travel in the manifest. [cited: MCP architecture, retrieved 2026-08-22] [asserted] |
| Plugins | **Low as a vendor package.** A canonical bundle may unpack into portable skills/MCP/config, but marketplace metadata, install lifecycle, native commands and extension APIs are harness-specific. [asserted] |
| Tools | **Low outside MCP or a constrained local executable contract.** Native browser, shell, sandbox, approval and result schemas are not equivalent because their names match. [measured: ADR-0084] [asserted] |
| Hooks | **Lowest.** Intent, matcher and required timing can travel; lifecycle events, tool coverage, handler types and blocking semantics often cannot. A required unmatched hook refuses; an optional one records exact loss. [cited: Claude and Codex hook documentation, retrieved 2026-08-22] [asserted] |
| Dataset or training-example manifest | **Conditional.** Digests, provenance, licence/consent, split identity and evaluation exclusions travel; payload bytes travel only where rights and destination permit. Hidden qualification data never enters a role package. [measured: ADR-0074; ADR-0086] [asserted] |
| Tuned checkpoint and optimiser state | **Narrow.** They travel only to a compatible base architecture, tokenizer, runtime, licence and hardware; they do not port into another vendor's closed model or establish behavioural equivalence. [measured: ADR-0085] [asserted] |
| Credentials and principal authority | **Never.** Opaque references may reach an instance-local broker; values, approvals, verdicts, gate lifts and spend authority never enter the child, manifest, generated files or trajectory. [measured: ADR-0084; V0-18] [asserted] |

The portable floor is therefore a canonical method/fact contract, Agent Skills-compatible procedure,
bounded recall bytes and credential-free local/MCP execution where semantics match. Richer native
features remain target-specific. Refusing semantic loss is the portability feature; file conversion
alone is not. [asserted]

## 7. Autonomous role learning and the training boundary

### 7.1 What a role accumulates

Every completed role attempt may append a private, immutable outcome record containing the role,
base model/harness/adapter and expertise digests; task and fact contracts; source/dataset provenance,
licence and consent; exact capability binding; input/output/artefact digests; verifier and human
outcomes; corrections, refusals, timeouts and missingness; critical harms; and resource use. Unknown
telemetry remains unknown rather than zero. [asserted]

Model output is not a truth label. Successful-looking transcripts, self-reported confidence and
same-model agreement cannot enter a training target as correct without an independent oracle or
authenticated human correction. Hidden evaluation items, answers and semantic siblings remain
sealed and never enter examples, retrieval or training. [measured: ADR-0076; ADR-0086] [asserted]

The accumulation is by `worker_contract`, category profile and stable failure signature, not by
every worker/domain pair. Domain facts remain in versioned expertise bundles by default. This
preserves `O(P + C + E)` state and allows a procedural improvement to be evaluated across domains
rather than overfit to a fashionable label. [algebra] [asserted]

### 7.2 Retrieval ends; training begins

Editing a role manifest, skill, worked example, tool configuration, retrieval index or bounded
memory is capability/retrieval work even when the files persist. Computing embeddings with a frozen
encoder is retrieval. **Training begins only when learned model parameters persistently mutate** by
optimiser, closed-form fit or direct edit. A downloaded unchanged model is a capability; a fitted
adapter, LoRA or checkpoint is training. [measured: ADR-0074] [asserted]

The first improvement arm is always the same base model plus a corrected method profile and the
same expertise bundle. A tuning candidate is warranted only when correct retrieval still loses on a
sealed development bank because of a stable behavioural, representation or latency/cost deficit;
the work recurs enough to repay fitting before sources/base/runtime expire; every example has exact
rights; dynamic facts remain in retrieval; and a fresh held-out comparison can isolate tuned over
bundle-only value. [measured: ADR-0086] [asserted]

What would be trained is a worker-contract adapter or checkpoint bound to
`{worker_contract, worker_profile, base_model_revision, instrument_epoch}` for a stable procedural
deficit such as tool selection, formal-output discipline or verifier following. It is not trained
for every subject pair. A domain-conditioned checkpoint is a separate ADR-0085 capability and
remains exceptional; it must beat the same base with the same profile and expertise bundle but
without parameter mutation. [asserted]

The RTX 5090 makes a bounded local candidate technically feasible; it does not supply consent,
labels, a stable deficit or outcome value. The system may accumulate eligible records and propose a
training contract autonomously. Under ADR-0076, no parameter-mutating treatment starts until a
trusted principal-only receipt binds the exact preregistration, data rights, resource ceiling,
candidate surface and sealed instrument. After that receipt, fitting and evaluation may run
autonomously in quarantine; activation remains a separate exact owner-gated promotion. [measured]
[asserted]

The honest automatic deployment frequency today is **zero**. Authenticated ingress, the sealed
host, bundle-conditioned tuning comparison and active promotion are unavailable, while ADR-0086
already places retrieval first. Tuning should therefore be rare by construction, not advertised as
the normal life cycle of every role. [measured]

## 8. The incumbent bar and search record

The direct catalogue-and-portability incumbent found on 23 August 2026 is
[`wshobson/agents` at revision `2b49247f`](https://github.com/wshobson/agents/tree/2b49247f1347d9cbd90edf869e5412563c3945cf),
MIT. Its pinned README reports 92 composable plugins, 202 agents, 181 skills and 105
commands from one Markdown source for Claude Code plus Codex, Cursor, OpenCode, Antigravity and
Copilot. [cited: pinned README and licence, retrieved 2026-08-23]

That is a real bar, not a straw man. Its adapters emit native formats and its branch-cut report used
real CLIs for structural discovery. Its own capability matrix also records semantic losses: Codex
and Cursor drop per-agent tool allowlists, several harnesses lack lifecycle hooks or native command
semantics, and deeper confirmation that a model actually loaded a Codex skill remained interactive.
The same revision's branch-cut report covers 191 agents rather than the current 202, so it does not
establish round-trip coverage for the additional eleven. [cited: pinned `docs/harnesses.md` and
`docs/round-trip-results.md`, retrieved 2026-08-23]

[`CohesiumAI/assemble` at revision `81f7577`](https://github.com/CohesiumAI/assemble/tree/81f757744254aefb6a6294db014566bc6f729878),
MIT, is the target-breadth leader found: its README reports 34 agents generated for 21 platforms and
states that it is a beta configuration generator, not a runtime. It can continue when search is
unavailable by appending a limitation, which is below ADR-0084's required-semantic refusal boundary.
[cited: pinned README and licence, retrieved 2026-08-23]

Ruflo is the orchestration breadth comparison, not the closest catalogue compiler. At the pinned
revision already audited in this repository, its advertised specialised-agent count was principally
Markdown role-prompt/tool manifests; the bounded teardown found 108 Markdown manifests, 97 unique
names and only 13 declaring tools. Markdown roles may still be useful, but the count is not a count
of distinct capabilities or fact classes. [measured: `../../00-context/ruflo-teardown-2026-08-22.md`]

The 23 August search covered the repository's agent-configuration and organisation bars plus
`wshobson/agents`, Assemble, Ruflo, Rulesync, Agent Skills, OpenHands microagents, CrewAI and AutoGen
through their primary repositories/documentation. No one entry led all axes: wshobson led catalogue
breadth/composability, while Assemble led claimed target breadth. Other near misses specialised in
one harness, supplied patterns rather than a portable catalogue, or translated files without a
fail-closed fact and outcome contract. That bounded search does not prove absence. [measured]
[asserted]

The plain incumbent answer is to adopt a permissively licensed Markdown catalogue and its existing
adapter rather than write another persona library. [cited] The proposed delta is narrower: orthogonal
method/expertise composition, a required fact contract, pre-launch `applied|degraded|refused`
receipts, no evidence credit for model/persona agreement, and EXP-136 against the same capable
generalist. None of that is an outcome advantage until the experiment runs. [asserted]

## 9. EXP-136: test the costumes objection directly

EXP-136 compares one role-method instance with the same capable generalist on the same task, facts,
expertise bundle, tools, model/harness revision, candidate exposure and aggregate budget. Subject
knowledge is held equal so the treatment isolates the worker method rather than buying a win with
extra retrieval or compute. Squad composition is excluded; EXP-80/107 already own that question.
[asserted]

The frozen bank contains 80 paired tasks: 20 per retained worker contract, each contract crossed
over the same four open, permissively licensed subject bundles. One category profile is selected
before outcomes for each task. Each task has an executable or primary-source truth contract and a
blinded authenticated/domain acceptance verdict. The worker arm receives the matching profile; the
generalist arm receives the same task-native context and capabilities without it. Order is
counterbalanced with seed `1360093`; isolated copies prevent cross-arm access. Each arm emits one
candidate, with no retry or replacement. Refusals, timeouts, missing results and protocol invalidity
remain in the fixed denominator. [asserted]

The experiment stops at 80 terminal pairs or 120 days after the first pair, whichever comes first;
there is no efficacy early stop and no replacement or retry. It confirms the frozen automatic
role-profile policy only if the role-minus-generalist joint-success point difference is at least
`+0.10`, its 20,000-resample paired bootstrap 95% lower bound exceeds `0`, no worker-contract stratum
has a negative point difference, the one-sided 95% upper bound on human-rejection increase is at
most `0.05`, review-adjusted minutes per success are at most `1.25x` the generalist and no worker-only
critical error occurs. A losing contract is cut. A tie/loss overall or worker-only critical error
kills automatic specialised selection; a harm or cost breach prevents confirmation; every other
result is inconclusive and defaults to the generalist. [asserted]

The largest plausible paired effect is `[-1, +1]`: profiles could repair every generalist failure or
poison every generalist success. The experiment can remove automatic worker profiles while retaining
the work taxonomy, explicit capabilities and one capable generalist. It cannot validate subject
expertise, squads, tuning, portability, gates or principal authority. [algebra] [asserted]

## 10. Evidence against: one model in four costumes

The strongest case against this design is that it is theatre. `wshobson/agents` and Ruflo show how
quickly catalogues grow into hundreds of Markdown manifests. Most of the observable behaviour still
comes from the underlying frontier model, task context and tools; names such as researcher,
architect or reviewer can make the same induction look organisationally independent. Cross-harness
generation then multiplies files and drift while hooks, permissions and tool semantics silently
contract. [cited] [measured] [asserted]

The external outcome evidence cuts both ways. Zheng et al. tested 162 roles across four model
families and 2,410 factual questions and found no overall persona gain, with effects too unstable for
reliable best-persona selection. Kong et al. found strategically designed role-play prompts beat
zero-shot on 10 of 12 reasoning benchmarks, but their treatment manually sampled task-specific role
feedback and selected a response rather than validating a static agent catalogue, independent facts
or automatic dispatch. A profile can therefore be a useful procedure trigger without becoming an
agent or evidence class. [cited: Zheng et al., Findings EMNLP 2024; Kong et al., NAACL 2024]

The local evidence is also hostile: EXP-16's single-agent arm beat the Owner meeting 9 of 12 blind
judgements while using far fewer tokens and wall time, and the current human-labelled beta estimate
does not meet its minimum denominator. A dozen role prompts can therefore cost more, create more
handoffs and make no better decision. [measured: ADR-0067; current beta record]

That objection may be right. The design concedes it structurally: one Owner/generalist remains the
default; worker methods are composable contracts rather than standing staff; domain is a bundle,
not another persona; empty titles are cut; a required execution or source gap refuses; no profile
receives evidence credit for model family; and EXP-136 compares profiles with the same facts, tools
and budget. If EXP-136 loses or ties, automatic role-profile selection is removed and the honest
product is one strong agent using excellent tools and the work labels only for measurement.
[asserted]

## 11. Checks owed by implementation

This document changes no runtime. A future implementation must extend the existing substrates and
ship these checks with the corresponding behaviour. [measured] [asserted]

- reject an unknown worker contract/profile, category mismatch, mutable role identity or stored
  worker-by-domain pair; [asserted]
- prove role-instance identity is derived from immutable worker, expertise, task, fact and binding
  digests and can be reconstructed from the trajectory; [asserted]
- refuse a role with no concrete fact contract or required observable, and give family/persona/title
  zero evidence credit; [asserted]
- prove required loss is `refused` before child launch, optional loss is explicit `degraded`, and a
  fallback creates a new weaker contract rather than mutating the original; [asserted]
- prove workspace, consent and destination admission happen before memory, skill, dataset or
  expertise bytes are rendered; [asserted]
- prove each selected capability is applied or named absent and record observed use separately;
  [asserted]
- prove hooks and tools are mapped only at equivalent semantics and stale adapter versions refuse;
  [asserted]
- prevent credentials, hidden evaluation data and principal authority entering any child or durable
  role artefact; [asserted]
- reject training classification for prompt/skill/memory edits and require dataset, base, run and
  checkpoint digests for every parameter mutation; [asserted]
- keep automatic training and activation disabled without ADR-0076's exact owner/instrument receipts;
  [asserted]
- enforce one Owner, one candidate and ADR-0077's exposure ceiling independently of role count; and
  [asserted]
- scan for a second selector, assembler, task store, writer, coordinator, router, budget ledger,
  orchestrator or CLI command. [asserted]

Until those checks and EXP-136 exist as executed artefacts, the catalogue is a falsifiable design,
not a claim that specialised agents outperform one capable generalist. [asserted]

## 12. Reversal and plain answer

Reverse automatic role selection by dispatching the unchanged generalist with the same task,
capabilities and expertise bundle. Retain the work categories for measurement, capability receipts
for safety and prior results as adverse history. No stored pair catalogue or model weights need to
be deleted. [asserted]

The plain answer is: expose thirteen native task profiles over four fact-bearing contracts, keep
domain expertise separate, compose them per task, and run one strong generalist unless another
runtime brings a named fact that changes the decision. Cut every title that cannot say what it will
retrieve, execute or observe. [asserted]

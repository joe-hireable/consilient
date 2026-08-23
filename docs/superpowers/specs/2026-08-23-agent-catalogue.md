# Agent catalogue: task profiles crossed with subject expertise, reusing existing role contracts

**Correction:** beta bounds candidate exposure, not squad headcount; model or provider family alone
has zero evidence credit; a missing required capability is a refusal rather than a degradation; and
live dispatch now assembles and records layered instructions but still does not bind selected
capability metadata or task-scoped role requirements to native runtime surfaces. [measured:
ADR-0077; ADR-0082; ADR-0084; `scripts/dispatch.py:969-981,1280-1304`]

- **Date:** 2026-08-23. [measured]
- **Status:** specification only; [ADR-0093](../../decisions/0093-compose-agent-roles-from-worker-method-and-subject-expertise.md)
  is PROVISIONAL. [measured]
- **Killing experiment:**
  [EXP-136](../../10-research/experiment-register.md#exp-136--does-a-worker-method-profile-beat-the-same-capable-generalist-with-the-same-starting-evidence-access-tools-and-budget-blocked)
  tests whether these profiles add outcome value or are one model in different costumes. [asserted]
- **Scope:** portable, task-scoped role composition for the closed work taxonomy in
  `2026-08-23-work-taxonomy.md`; no product implementation, source-path promise, new CLI command,
  gate change, routing activation or model training is included. [measured] [asserted]

## 1. Decision first

An agent assignment is composed for one work item from two independent axes: a **worker-method
profile** says what work category and procedure are being performed, while one or more **subject-
expertise bundle references** say which domain sources, vocabulary, examples and tools are
admissible. ADR-0067's existing role contract, ADR-0082's RACI rights, the task/fact contract, bounded
memory and target-harness binding complete the run-local instance. [asserted]

`role_instance = worker_profile + assignment_ref(existing_role_contract, raci_rights) + expertise_refs + task_contract + fact_contract + capability_binding + bounded_recall`
[asserted]

The repository stores thirteen small category profiles and each versioned expertise bundle once; it
reuses the role contracts already fixed by ADR-0067. It does not store `researcher-in-genomics`,
`researcher-in-payments` or any other pair. A role instance is a content-addressed, run-local
compilation and expires with its work-item assignment. For `P` profiles and `E` expertise bundles,
durable catalogue state is `O(P + E)`, not `O(P x E)`; compiled instances are receipts rather than
catalogue members. [algebra] [asserted]

The default is still one accountable Owner, usually the strongest eligible generalist, which may
execute several worker methods sequentially. A second runtime is admitted only when a task-scoped
fact contract requires isolated acquisition, a capability/state unavailable to the Owner, or a
non-overlapping artefact scope whose output can change the decision. Repeating the same method,
sources and context through another persona or model is echo. [measured: ADR-0067; ADR-0082]
[asserted]

The work-taxonomy stream owns the thirteen measurement labels and their three phases. This document
gives every category a native task-scoped profile, but a profile does not imply a separate runtime.
Acquisition, instrumentation, realisation and assessment are reusable execution patterns, not a new
role enum: evidence credit and runtime admission remain exactly ADR-0067/0082's concern. Realisation
is responsible artefact work and supplies no independent anchor. This resolves the principal's
"categories are agents" outcome without turning measurement labels into standing staff. [measured]
[asserted]

## 2. The two axes

### 2.1 Worker method

`worker_profile` is a closed, versioned mapping from one of the thirteen `work_category` values to a
procedure, output and refusal rule. It projects work onto an existing ADR-0067 role contract and
ADR-0082 RACI rights; it does not create a role name. If a profile needs distinct sequential methods,
it opens linked work-item revisions rather than storing a compound persona. Acquisition,
instrumentation, realisation and assessment below are explanatory patterns only. [asserted]

A capable generalist may execute any profile. That does not make the profile redundant: it freezes
method and receipts. It also does not justify another squad member. Another runtime appears only
when the ADR-0067 role contract needs isolated acquisition or non-overlapping state/capability;
otherwise the Owner executes the profile directly. [asserted]

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

The catalogue has thirteen profiles. Non-Owner execution steps are grouped below by four reusable
patterns; Owner-only profiles appear in the following exhaustive category table. The pattern names
are not stored identities and do not replace ADR-0067's `Owner`, `Domain specialist`,
`Executing verifier`, `Adversary`, `Replicator` or `Experimenter` contracts. A fact-bearing assignment
must produce the named sealed observable; otherwise it does not launch as C/evidence work. [measured]
[asserted]

| Execution pattern, not a role enum | Eligible observable | Minimum method | Existing role/RACI projection | Category profiles |
|---|---|---|---|---|
| Acquisition | A new primary-source record, public/open dataset observation, browser/live-system observation or repository observation carried through ADR-0082's admitted `artefact_execution` or `novel_corpus_observation` channel, absent from the Owner's frozen evidence manifest. [measured: ADR-0081; ADR-0082] [asserted] | Retrieve or inspect the named anchor, retain identity/time/digest/locator, licence where relevant, omissions and failures, then seal before synthesis. Snippets and model memory do not satisfy it. [measured: citing-sources skill] [asserted] | ADR-0067 `Domain specialist`; `Adversary` for a hostile source; `Replicator` for isolated reacquisition. ADR-0082 C credit still requires structural admission. [measured] [asserted] | `discovery`, `research` [asserted] |
| Instrumentation | An executed experiment, simulation, formal/algebraic check or data analysis with frozen premises/procedure and raw outputs. A model-imagined result contributes nothing. [asserted] | Pre-register when empirical, execute the producing script or formal model, retain adverse/missing outcomes and apply the fixed stopping or sensitivity rule. `[simulated]`, `[algebra]` and `[measured]` remain distinct. [measured: running-experiments skill] [asserted] | ADR-0067 `Experimenter`, normally ADR-0082 R; a result receives evidence credit only through its sealed observation contract. [asserted] | `experiment`, `simulation`; an `innovation` successor may run a transfer falsifier. [asserted] |
| Realisation | The target artefact, diff, build observation or authorised delivery/read-back receipt from owned state. This is responsible work, not independent evidence that the result is correct. [asserted] | Work from the frozen realisation package, retain artefact and tool-result digests, never reopen the goal/verifier, and perform an effect only inside existing authority. [asserted] | ADR-0082 R, normally co-held by the Owner. It receives zero consilient anchor credit; a second runtime needs non-overlapping owned state/capability, not a new role label. [measured] [asserted] | `implementation`, `delivery`; specification when the specification itself is the requested artefact. [asserted] |
| Assessment | An independently executed frozen oracle/comparison, hostile counterexample or isolated reacquisition against a candidate hidden from the author path. [measured: ADR-0067; ADR-0081] [asserted] | Bind candidate, comparator and acceptance digests; execute once; retain every unavailable result; give same-diff opinion, persona and family difference zero credit. [asserted] | ADR-0067 `Executing verifier`, `Adversary` or `Replicator`, with task-scoped ADR-0082 R/C rights frozen before work. [measured] [asserted] | `assessment`, `verification`; `debate` only when it becomes an executed counterexample or new source acquisition. [asserted] |

The Owner/generalist is accountable but is not a fifth evidence role. It supplies governance
provenance and runs the profiles whose outputs are decisions or plans rather than new facts.
[measured: ADR-0067; ADR-0082] [asserted]

### 3.1 Every category still has a native profile

| Work category | Native task-scoped profile |
|---|---|
| `framing` | Owner resolves the authenticated task, authority, scope, consequence, reversal and unknowns; it receives no independent anchor credit. [asserted] |
| `discovery` | An ADR-0067 `Domain specialist`, `Adversary` or `Replicator` acquisition inspects actual system state and candidate incumbents under the matching R/C rights. [asserted] |
| `research` | An ADR-0067 `Domain specialist` retrieves and verifies primary sources or open data. [asserted] |
| `experiment` | The ADR-0067 `Experimenter` freezes and runs the empirical protocol. [asserted] |
| `simulation` | The ADR-0067 `Experimenter` runs the declared formal model and sensitivity analysis. [asserted] |
| `debate` | An ADR-0067 `Adversary` executes a counterexample or contrary acquisition; rhetorical exchange stays Owner deliberation and earns zero credit. [asserted] |
| `innovation` | Owner proposes the transfer; any missing foreign mechanism or falsifier becomes a linked `discovery` and `experiment|simulation` work item under existing roles. [asserted] |
| `synthesis` | Owner applies the frozen decision rule to sealed evidence, emits one candidate and dispositions dissent; this is derivation, not another anchor. [asserted] |
| `assessment` | An ADR-0067 `Executing verifier`, `Adversary` or `Replicator` executes the frozen comparison/acceptance contract. [asserted] |
| `planning` | Owner derives the smallest verifiable work graph; missing live dependency/import facts become linked `discovery` work rather than inventions. [asserted] |
| `implementation` | The ADR-0082 R assignment creates the target artefact and receives no independent anchor credit. [asserted] |
| `verification` | An ADR-0067 `Executing verifier` executes the independent oracle against the realised artefact. [asserted] |
| `delivery` | The ADR-0082 R assignment performs the authorised hand-off and retains destination read-back or refusal. [asserted] |

Thus every category is executable natively, but only a concrete fact contract can justify another
runtime. Most requests should still use one Owner/generalist across several profiles. [asserted]

## 4. Techniques and titles deliberately cut

These names do not become additional ADR-0067 role contracts. Their useful mechanics remain inside
the profiles, existing contracts or subject axis. [asserted]

| Cut role | Why it is cut | Where the real work goes |
|---|---|---|
| Standing `framer`, `innovator`, `synthesiser`, `planner` roles | Their outputs are governance, hypotheses, decisions or work graphs rather than independent evidence. A second agent would add a title without a fact class. [asserted] | Keep the native category profile in the accountable Owner; open a linked ADR-0067 acquisition/experiment assignment only for a concrete missing fact. [asserted] |
| `hypothesiser` | A hypothesis is a falsifiable candidate statement, not a class of observed facts; a persona generating more guesses adds echo. [asserted] | Freeze a content-addressed hypothesis inside `framing`, `innovation`, `experiment` or `simulation` before the run. [asserted] |
| `mathematical_modeller` | Mathematical modelling is an instrumentation mode; exact derivation and assumed-model output need different evidence tags, not different agents. [asserted] | The `simulation` profile under the existing `Experimenter` contract returns `[algebra]` proof/counterexample where exact and `[simulated]` sensitivity otherwise. [asserted] |
| `data_scientist` | Data science names a broad discipline, not one work purpose; the same dataset operation may discover, experiment, simulate or assess. [asserted] | Select the work-purpose profile and existing role contract according to the estimand, with data tooling in the capability request and domain data in the expertise bundle. [asserted] |
| `specifier` | A specification is a contract artefact, not an independent fact source. [asserted] | Use Owner `planning` when preparatory or ADR-0082 R/`implementation` when the specification is the requested deliverable. [asserted] |
| Permanent domain-specific persona | Domain is the orthogonal expertise axis. A worker type such as `genomics_specialist` recreates pairwise agents and ambiguous inheritance. [asserted] | Bind ADR-0086 `expertise_refs` to the existing ADR-0067 `Domain specialist` contract for one work item. [asserted] |
| Generic `reviewer`, `critic`, `auditor` | The title says nothing about the observation. A review that only rereads the author's material is echo. [measured: ADR-0067] [asserted] | Use the existing `Executing verifier` or `Adversary` contract only for an executed oracle, counterexample or contrary acquisition. [asserted] |
| A new `replicator` worker type | Replication is an isolation constraint; another model seeing the same evidence is not replication. [measured: ADR-0067; ADR-0082] [asserted] | Reuse ADR-0067's existing `Replicator` contract in an isolated snapshot against a separately named anchor. [asserted] |
| `manager`, `coordinator`, `middle_manager` | Existing work items, claims and one Owner already coordinate; another agent adds no truth-relevant fact and cannot inherit the principal's authority. [measured: ADR-0067; ADR-0082] [asserted] | `work_items.py` holds responsibility, `coordination.py` claims work and the Owner decides within existing rights. [measured] |
| `persona` or model-family roles | Tone, title, prompt and provider change no source class. [measured: ADR-0081; ADR-0082] | Keep model/harness as routing and correlation metadata; credit only the executed observation. [asserted] |

This cut is load-bearing. Adding an agent role requires a successor to ADR-0067 and a fact class its
existing contracts cannot express. Adding a category profile requires a successor to the work
taxonomy and an EXP-136-class matched test. Catalogue growth is not a marketplace count. [asserted]

## 5. Dynamic assembly, fail closed

### 5.1 What one role declares

A work-item revision requests a role using the existing ADR-0074 capability and ADR-0084 binding
path. The semantic record contains only these concerns; it is not a second manifest format.
[asserted]

1. `worker_profile`, its version and matching immutable `work_category`/phase, plus an immutable
   ADR-0082 `assignment_ref` resolving the existing ADR-0067 role contract and RACI-rights projection.
   Profile, title and prompt never confer rights. A required second method is a linked successor work
   item, not another field in one persona. [asserted]
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
required selected skill can still lose to the general skill/count/character limits. The main caller
also reports a selection error and returns `2` without writing the canonical `dispatch.refused` and
`capability.gap` receipt. The design therefore claims future binding behaviour only. [measured:
source inspection, 2026-08-23]

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

The receipt records the role-instance digest, task/work-item revision, profile, existing role/RACI,
expertise and capability versions, harness/adapter probe, generated artefact digests, memory receipt,
state, every loss and reason, effective effects and fact-contract eligibility. Later observed use is
`yes`, `no` or `unknown`; selection or loading is not evidence of use. [asserted]

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

The accumulation is by category profile, existing ADR-0067 role contract and stable failure
signature, not by every worker/domain pair. Domain facts remain in versioned expertise bundles by
default. This preserves `O(P + E)` catalogue state and allows a procedural improvement to be
evaluated across domains rather than overfit to a fashionable label. [algebra] [asserted]

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

What would be trained is a profile adapter or checkpoint bound to
`{worker_profile, existing_role_contract, base_model_revision, instrument_epoch}` for a stable
procedural deficit such as tool selection, formal-output discipline or verifier following. It is
not trained for every subject pair. A domain-conditioned checkpoint is a separate ADR-0085
capability and remains exceptional; it must beat the same base with the same profile and expertise
bundle but without parameter mutation. [asserted]

The RTX 5090 makes a bounded local candidate technically feasible; it does not supply consent,
labels, a stable deficit or outcome value. An inferred training proposal must reuse ADR-0086's gate:
within a rolling 90 days, at least six completed applicable items spanning 21 days and four calendar
days, three postcondition signatures, plus either two different-class adverse signals or 180
measured repeated-acquisition minutes across three items; the conservative half-recurrence estimate
must remain positive. Rejection/expiry suppresses the `{worker_profile, existing_role_contract,
base_model_revision, instrument_epoch}` proposal for 90 days absent a new independent critical
failure. Under ADR-0076, no parameter-mutating treatment starts until a trusted principal-only
receipt binds the exact preregistration, data rights, resource ceiling, candidate surface and sealed
instrument. After that receipt, fitting and evaluation may run autonomously in quarantine; activation
remains a separate exact owner-gated promotion. [measured] [asserted]

The honest automatic deployment frequency today is **zero**. Authenticated ingress, the sealed
host, bundle-conditioned tuning comparison and active promotion are unavailable, while ADR-0086
already places retrieval first. Tuning should therefore be rare by construction, not advertised as
the normal life cycle of every role. [measured]

## 8. The incumbent bar and search record

The direct catalogue-and-portability incumbent found on 23 August 2026 is
[`wshobson/agents` at revision `2b49247f1347`](https://github.com/wshobson/agents/tree/2b49247f1347),
MIT at the repository root. Its pinned README reports 92 composable plugins, 202 agents, 181 skills and 105
commands: Claude is the source environment and Codex, Cursor, OpenCode, Antigravity and Copilot are
five generated targets. One counted external plugin is declared Apache-2.0 and referenced without an immutable
revision, so the root revision does not pin all 92 plugins. [cited: pinned README, tree and licence,
retrieved 2026-08-23]

At that verified revision, `git ls-files 'plugins/*/agents/*.md'` followed by parsing each initial
YAML frontmatter block measured 202 tracked and parsed manifests, 202 unique names, 202 `model`
fields, 15 `tools` fields and 187 manifests without `tools`; none bound agent-level `skills` or
`hooks`, although skills exist separately at plugin level. [measured]

That is a real bar, not a straw man. Its adapters emit native formats and its branch-cut report used
real CLIs for structural discovery. Codex and Cursor drop per-agent tool allowlists and lack lifecycle
hooks; commands are transformed into target-native skills, TOML or prompt artefacts, while behavioural
equivalence remains untested. Deeper confirmation that a model actually loaded a Codex skill remained interactive.
The same revision's branch-cut report covers 191 agents rather than the current 202, so it does not
establish round-trip coverage for the additional eleven. [cited: pinned `docs/harnesses.md` and
`docs/round-trip-results.md`, retrieved 2026-08-23]

[`CohesiumAI/assemble` at revision `81f757744254`](https://github.com/CohesiumAI/assemble/tree/81f757744254),
MIT, is the target-breadth leader found: its README reports 34 agents generated for 21 platforms and
states that it is a beta configuration generator, not a runtime. It can continue when search is
unavailable by appending a limitation, which is below ADR-0084's required-semantic refusal boundary.
[cited: pinned README and licence, retrieved 2026-08-23]

Ruflo is the orchestration breadth comparison, not the closest catalogue compiler. At the pinned
revision already audited in this repository, its advertised specialised-agent count was principally
Markdown role-prompt/tool manifests; the bounded teardown found 108 Markdown manifests, 97 unique
names and only 13 declaring tools. Markdown roles may still be useful, but the count is not a count
of distinct capabilities or fact classes. [measured: `../../00-context/ruflo-teardown-2026-08-22.md`]

VoltAgent's `awesome-claude-code-subagents` is a dominated one-harness near miss: its pinned README
advertises 158-plus Claude-only YAML-frontmatter role/tool prompts under MIT and expressly disclaims
security or correctness review. [cited: revision `c9e51ec0b3d4`, retrieved 2026-08-23]

The 23 August search covered the repository's agent-configuration and organisation bars plus
`wshobson/agents`, Assemble, VoltAgent, Ruflo, Rulesync, Agent Skills, OpenHands microagents, CrewAI and AutoGen
through their primary repositories/documentation. No one entry led all axes: wshobson led catalogue
breadth/composability, while Assemble led claimed target breadth. Other near misses specialised in
one harness, supplied patterns rather than a portable catalogue, or translated files without a
fail-closed fact and outcome contract. That bounded search does not prove absence. [measured]
[asserted]

Prompt-disabled, credential-helper-disabled public Git acquisition succeeded for wshobson and
Assemble on 23 August 2026, which establishes no-account source access only. Their generated target
configs may still name proprietary models or platforms requiring accounts; unchanged account-free
execution across targets was not established. [measured] [cited]

The plain incumbent answer is to reuse individually pinned and licence-verified source assets plus
the source-to-target adapter pattern rather than write another persona library. Existing adapters are
not adopted unchanged: every target mapping must prove ADR-0084 semantic fidelity or refuse. The
proposed delta is narrower: orthogonal method/expertise composition, a required fact contract,
pre-launch `applied|degraded|refused` receipts, no evidence credit for model/persona agreement, and
EXP-136 against the same capable generalist. None of that is an outcome advantage until the
experiment runs. [cited] [asserted]

## 9. EXP-136: test the costumes objection directly

EXP-136 compares one profiled assignment with the same capable generalist on the same task, starting
evidence/access, expertise bundle, tools, model/harness revision, candidate exposure and aggregate
budget. The arms may acquire different observations after treatment; that is part of the profile's
effect, not a claim that realised facts remain equal. Squad composition is excluded; EXP-80/107
already own that question. [asserted]

The frozen bank contains 104 paired tasks: eight per work-category profile, with two tasks from each
of the same four open, permissively licensed subject bundles in every profile stratum. The profile,
existing ADR-0067 role contract and ADR-0082 rights are selected before outcomes. Each task has an
executable or primary-source truth contract and a blinded authenticated/domain acceptance verdict.
The worker arm receives the matching profile; the generalist arm receives the same starting context,
sources, access and capabilities without it. Order and all resampling use seed `1360093`; isolated
copies prevent cross-arm access. Each arm emits one candidate, with no retry or replacement.
Refusals, timeouts, missing results and protocol invalidity remain in the fixed denominator.
[asserted]

The experiment stops at 104 terminal pairs or 120 days after the first pair, whichever comes first;
there is no efficacy early stop and no replacement or retry. It confirms profile efficacy conditional
on the frozen correct category/role assignment only if the role-minus-generalist joint-success point
difference is at least `+0.10`, the 2.5th percentile of 20,000 paired bootstrap resamples within
profile strata exceeds `0`, no profile stratum has a negative point difference, the 95th percentile
of the same resamples for the human-rejection increase is at most `0.05`, the cross-multiplied
review-adjusted cost-per-success rule is at most `1.25x`, and no worker-only critical error occurs.
A negative profile stratum cuts that profile treatment. `W <= G` overall or a worker-only critical
error kills profile-defaulting; other non-confirming results are inconclusive and default to the
generalist. Even confirmation does not validate the upstream category classifier or automatic
selector. [asserted]

The largest plausible paired effect is `[-1, +1]`: profiles could repair every generalist failure or
poison every generalist success. The experiment can remove profile defaulting after a frozen assignment while retaining
the work taxonomy, explicit capabilities and one capable generalist. It cannot validate subject
expertise, squads, tuning, portability, gates or principal authority. [algebra] [asserted]

## 10. Evidence against: one model in thirteen profiles

The strongest case against this design is that it is theatre. Wshobson reports 202 Markdown agents;
the local Ruflo teardown found 108 Markdown manifests and 97 unique names; and Assemble explicitly
says it has no runtime, daemon or SDK because the host IDE/CLI's LLM reads the generated configs.
[cited] [measured]

The inference is hostile: most behaviour may come from the underlying model, task context and tools,
while names such as researcher, architect or reviewer make one induction look organisationally
independent. Cross-harness generation can then multiply files and drift as hooks, permissions and
tool semantics contract. [asserted]

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
default; worker profiles are composable procedures over existing contracts rather than standing staff; domain is a bundle,
not another persona; empty titles are cut; a required execution or source gap refuses; no profile
receives evidence credit for model family; and EXP-136 compares profiles with the same starting
evidence, access, tools and budget. If EXP-136 loses or ties, profile defaulting after a frozen
assignment is removed and the honest
product is one strong agent using excellent tools and the work labels only for measurement.
[asserted]

## 11. Checks owed by implementation

This document changes no runtime. A future implementation must extend the existing substrates and
ship these checks with the corresponding behaviour. [measured] [asserted]

- reject an unknown profile, category/existing-role/RACI mismatch, mutable role identity or stored
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
- prove every pre-launch capability/profile refusal appends the canonical refusal/gap receipt before
  returning, including the main dispatch error path; [asserted]
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

Reverse profile defaulting after a frozen assignment by dispatching the unchanged generalist with
the same task, capabilities and expertise bundle. Retain the work categories for measurement,
capability receipts for safety and prior results as adverse history. No stored pair catalogue or
model weights need to be deleted. [asserted]

The plain answer is: expose thirteen native task profiles, reuse ADR-0067/0082 role contracts and
rights, keep domain expertise separate, compose them per task, and run one strong generalist unless
another runtime brings a named fact that changes the decision. Cut every new title that cannot say
what it will retrieve, execute or observe. [asserted]

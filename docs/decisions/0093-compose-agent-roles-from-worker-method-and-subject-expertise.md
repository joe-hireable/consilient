# 0093. Compose agent roles from worker method and subject expertise, and cut evidence-free specialists

**Correction:** beta bounds candidate exposure rather than squad headcount; model family alone has
zero evidence credit; missing required capability semantics refuse before launch; and live dispatch
assembles and records instructions but does not bind selected capabilities or task-scoped role
requirements to native runtime surfaces. [measured: ADR-0077; ADR-0082; ADR-0084]

- **Status:** PROVISIONAL - EXP-136 can remove category-profile defaulting, conditional on a correct
  frozen assignment, while retaining the work taxonomy, explicit capabilities and one capable
  generalist. [asserted]
- **Date:** 2026-08-23. [measured]
- **Deciders:** Joe Brown supplied the two-axis native-agent requirement and delegated the catalogue
  in `../00-context/the-machine-2026-08-22.md`; Codex dispatch
  `20260823T104841-d6abd2f50d` owns this provisional mechanism, which he has not reviewed.
  [measured]
- **Inquiry tier reached:** T1 ground - current source/ADRs and retrieved incumbents were read; T3 is
  pre-registered as EXP-136 and has not run. [measured]
- **Executable model:** none - the composition and refusal rules are categorical; EXP-136 is the
  executable matched outcome comparison. [asserted]

## Context

The work-taxonomy stream has fixed thirteen durable categories and three phases for measurement.
It explicitly does not define an agent per category. The principal separately requires each work
category to be executable as a native agent, with subject expertise as another axis and tools,
plugins, skills, context and memory assembled per task. [measured]

The closest retrieved catalogue incumbent is `wshobson/agents` at revision `2b49247f1347`, MIT: its
pinned README reports 92 plugins, 202 agents, 181 skills, 105 commands and native adapters
from a Claude source into five generated target surfaces. A pinned-tree parse measured 202 tracked
agent Markdown manifests and unique names: all 202 declare `model`, 15 declare `tools`, 187 do not,
and none bind agent-level `skills` or `hooks` (plugin-level skills are separate). Codex and Cursor drop
per-agent allowlists and lack lifecycle hooks; commands are transformed into target-native artefacts,
while behavioural equivalence remains untested. Its branch-cut report covers 191 rather than the
current 202 agents. Assemble at revision `81f757744254`, also MIT, reports the separate target-breadth bar of 34 agents across 21 platforms
but is explicitly a beta configuration generator rather than a runtime. [cited: repository READMEs,
licences, harness matrix and round-trip report, retrieved 2026-08-23]

Ruflo remains serious orchestration prior art, but its advertised specialised-agent count is
principally Markdown role-prompt/tool manifests rather than independently measured capabilities.
The repository's pinned teardown found 108 manifests, 97 unique names and 13 declaring tools; it
also found real cross-harness execution and persistent state, so dismissing the whole product as
prompts would be false. [measured: `../00-context/ruflo-teardown-2026-08-22.md`]

ADR-0074 already fixes the manifest/selection/assembly/writer ownership chain. ADR-0084 already
decides portable capability compilation and explicit `applied|degraded|refused` outcomes. ADR-0086
already decides that expertise is a proven bundle and that tuning follows only after retrieval
demonstrably loses. ADR-0067/0082 already fix one Owner, task-scoped RACI and the distinct-fact rule.
A new orchestrator, domain registry, pairwise agent catalogue or training meaning would duplicate
those decisions. [measured] [asserted]

## Decision

Consilient will represent a task role as a run-local composition of one versioned category profile,
an immutable ADR-0082 assignment reference resolving an existing ADR-0067 role contract and RACI
rights, zero or more versioned subject-expertise bundle references, the work-item/fact contract,
bounded recall and one ADR-0084 target-harness binding. Profile, title and prompt confer no rights.
Only profiles and expertise sources are new persistent catalogue elements; no worker-by-domain pair
becomes an entry. [measured] [asserted]

Every one of the thirteen work categories has a native task-scoped profile. Acquisition,
instrumentation, realisation and assessment are reusable method patterns, not another role enum.
Acquisition projects onto ADR-0067 `Domain specialist`, `Adversary` or `Replicator`; instrumentation
onto `Experimenter`; assessment onto `Executing verifier`, `Adversary` or `Replicator`; realisation
is ADR-0082 R work and receives zero independent-anchor credit. Framing, innovation, synthesis and
planning remain Owner profiles; debate receives credit only through an executed existing role
contract. [measured] [asserted]

A category profile and existing assignment specify method, receipt and rights, not a claim that
another model is needed. The strongest eligible generalist co-holds the Owner and may execute several
profiles sequentially. A second runtime still requires ADR-0067/0082's isolated, decision-relevant
fact or non-overlapping artefact scope. Role, prompt, title, persona, harness and model family alone
add no evidence credit. [measured] [asserted]

Standing `framer|hypothesiser|innovator|synthesiser|planner`, `mathematical_modeller`,
`data_scientist`, `specifier`, domain-pair personas, generic `reviewer|critic|auditor`, a second
`replicator` type, `manager|coordinator` and persona/model roles are cut. Their useful techniques stay
in profiles, ADR-0067's existing contracts or the expertise axis. Specification is planning when
preparatory and ADR-0082 R work when requested; formal modelling is a simulation profile;
ADR-0067's `Domain specialist`, `Adversary` and `Replicator` remain unchanged; and coordination
already belongs to one Owner, work items and claims. [measured] [asserted]

The role request extends the existing canonical capability path with `worker_profile`, immutable
ADR-0082 `assignment_ref`, expertise/fact/context, required-semantics, effects, limits, postcondition,
verifier and optional pre-declared fallback references. `capabilities.py` remains the sole selector,
`instructions.py` the assembler,
`dispatch.py` the caller/adapter and `events.py` the trajectory writer; work items, coordination,
routing and budget keep their current owners. [measured: ADR-0074] [asserted]

Before launch the binding is exactly `applied`, explicit `degraded` for optional semantic loss, or
`refused` for a required loss. A required loss may move only to a pre-declared weaker fallback with
a new work-item/role digest and `degraded_from` record; the original role remains refused. Missing
fact-producing semantics remove evidence credit rather than becoming prompt guidance. [measured:
ADR-0084] [asserted]

Portability extends ADR-0084. Canonical method/fact contracts, bounded memory bytes/receipts and the
Agent Skills core genuinely travel; expertise/data travel only with compatible rights and
destination; MCP travels subject to host/auth semantics; native tools/plugins and hooks generally
do not; checkpoints travel only across compatible base/runtime/licence boundaries; credentials,
hidden instruments and principal authority never travel into a child. Target-specific adapters
compile the portable source and refuse unmatched required semantics. [measured] [cited] [asserted]

Role outcome data accumulate privately by profile, existing role contract and stable failure
signature, not by every domain pair. Skills, examples, retrieval indexes and memory remain
capabilities/retrieval. Training begins only when learned parameters persistently mutate. A profile
adapter or checkpoint is considered only after the same base with corrected retrieval and the same
expertise bundle still loses because of a stable recurring behavioural/representation/cost deficit,
with licensed data and a fresh held-out bundle-only comparison. [measured: ADR-0074; ADR-0086]
[asserted]

Automatic accumulation is permitted within existing privacy boundaries; an inferred proposal must
reuse ADR-0086's rolling-90-day six-item/21-day/four-day, three-postcondition and adverse-signal/time
gate, positive half-recurrence estimate and 90-day rejection/expiry suppression keyed to profile,
existing role, base revision and instrument epoch. A parameter-mutating run requires ADR-0076's
trusted principal-approved impact contract and sealed instrument, and activation requires separate
exact approval. The current automatic tuned-role count is zero. The RTX 5090 changes feasibility,
not consent or evidence. [measured] [asserted]

The detailed catalogue, composition, binding states, portability matrix, training boundary and
EXP-136 protocol are fixed in
`../superpowers/specs/2026-08-23-agent-catalogue.md`. [asserted]

## Evidence

- `[measured]` The work taxonomy defines thirteen closed work categories while leaving agent roles
  to this stream.
- `[measured]` Current `capabilities.py` fails closed on malformed, unknown and unavailable
  inventory items but returns selection metadata only. Live dispatch calls and records
  `instructions.assemble()`, but exact role requirements are not selector inputs and selected
  capability application has no binding receipt.
- `[measured]` ADR-0067/0082 assign zero structural credit to family, role, persona and repeated
  context and keep one Owner as the default.
- `[measured]` The pinned Ruflo teardown found real orchestration alongside predominantly Markdown
  role manifests, so catalogue count and capability count are not interchangeable.
- `[cited]` `wshobson/agents` is a permissively licensed, large, composable, multi-harness Markdown
  catalogue whose own documentation records native semantic losses and structural verification
  limits.
- `[cited]` Agent Skills, MCP and Rulesync already provide the procedure, tool-protocol and
  configuration-compilation floors recorded by ADR-0084.
- `[algebra]` Persisting `P` profiles and `E` expertise bundles requires `P + E` new identities;
  persisting every profile/domain pair requires up to `P x E` identities without adding facts.
- `[asserted]` Fact contracts, explicit binding receipts and equal-starting-access EXP-136 are the smallest
  defensible delta over the retrieved catalogue bar.

## Evidence against

The strongest case is that the catalogue is theatre. Wshobson reports 202 Markdown agents, the local
Ruflo teardown found a triple-digit manifest count, and Assemble says it has no runtime/daemon/SDK
because the host LLM reads its generated configs. [cited] [measured]

Thirteen profiles prompted differently still share one underlying model; apparent specialisation may
come entirely from tools, retrieved context and extra tokens. Building more prompt files may add
taxonomy, context and adapter drift without one additional true observation. [asserted]

The local result points the same way: EXP-16's one-agent arm beat the Owner meeting 9/12 to 2/12 at
lower token and wall-clock cost. Ao, Gao and Simchi-Levi's same-information result gives the formal
objection: delegation without new exogenous signals cannot improve the ideal central decision-maker.
[measured] [cited: arXiv:2603.26993]

Published persona evidence is mixed rather than permission to dismiss profiles. Zheng et al. found
no overall factual-performance gain across 162 roles and four model families; Kong et al. reported
strategically designed role-play beating zero-shot on 10/12 reasoning benchmarks, but manually
sampled task-specific role feedback and did not test agentic execution or automatic catalogue
selection. [cited: Findings EMNLP 2024, arXiv:2311.10054; NAACL 2024,
doi:10.18653/v1/2024.naacl-long.228]

The decision concedes that objection unless EXP-136 defeats it. One generalist remains the default;
profiles compile over existing ephemeral assignments rather than standing agents; subject expertise
is composed rather than copied; empty titles are cut; missing execution refuses; and the experiment
holds starting evidence/access, tools, model, tasks and total budget equal. A tie or loss removes
profile-defaulting and retains the honest simpler design: one strong agent with excellent tools, plus
work labels for measurement. [asserted]

Known weaknesses remain material: no role runtime or adapter receipt is implemented; the current
source still gives family-derived evidence credit in a dispatch path; external catalogue counts do
not measure accepted outcomes; EXP-136 is blocked; and authenticated training/promotion ingress and
sealed evaluation do not exist. [measured]

## Consequences

**Positive** - method and domain vary independently; one profile improvement can transfer across
expertise bundles; every launched role owes a real observable; missing semantics become visible;
and roles remain portable at the semantic floor without multiplying durable pairs. [asserted]

**Negative** - thirteen profiles, adapter conformance and outcome receipts add schema,
startup and maintenance cost; strict refusal can leave useful work unavailable; and most tuned
specialists may never be warranted. [asserted]

**Neutral but load-bearing** - one Owner, one candidate, RACI rights, beta/exposure policy, the six
principal-only authority classes, six-command CLI, false routing flag, AST lock and every gate remain
unchanged. [measured] [asserted]

## Enforcement

This decision authorises documentation and EXP-136 only. Its intended commit scope changes no product
code, capability inventory, gate, CLI, routing flag, model state or training data. [asserted]

Future implementation must add, in the same commit as each behaviour: closed profile/category and
immutable assignment-reference validation against existing ADR-0067/0082 contracts/rights; no stored
pair identities; concrete fact-contract admission;
zero family/persona evidence credit; `applied|degraded|refused` receipts with required-loss
pre-launch refusal; fallback revision identity; workspace/consent/destination filtering before
  render; a durable canonical refusal/gap receipt on every error return; exact per-harness
  semantic/version checks; credential/authority/hidden-bank exclusion;
parameter-mutation classification and owner-gated training; one-Owner/one-candidate enforcement; and
a source ratchet rejecting any second selector, assembler, writer, task store, coordinator, router,
budget ledger, orchestrator or CLI command. [asserted]

- **Check:** future focused role/portability tests, EXP-136 and the existing record-number, ADR-index,
  evidence-tag, privacy, AST and attribution checks. [asserted]
- **Fails CI:** EXP-136 registration and ADR-reference integrity do; no future role behaviour is
  protected today. [measured]
- **Added in the same commit as implementation:** this commit has no implementation; required for
  every later slice. [measured] [asserted]

## What would overturn this

EXP-136 kills category-profile defaulting for its frozen correctly assigned task mixture if the role
arm ties or loses on joint success or causes one treatment-only critical error; a negative profile
stratum kills that profile. Harm/cost breaches or other non-confirming outcomes leave the treatment
inconclusive and the generalist as default. Confirmation is conditional on the frozen assignment and
does not authorise a category classifier, automatic selector, more agents, automatic expertise
selection, tuning, gates or effects. [asserted]

A cheaper counterexample blocks implementation immediately: a role launches without a concrete
fact contract; required semantics become prompt text; a family/persona gains evidence credit; a
worker/domain pair becomes persistent identity; a hidden evaluator enters training; or a role
authors principal approval, verdict, spend, publication or gate state. [asserted]

A lower-cost upstream implementation that adds fact contracts, receipts and equal-starting-access outcome
evaluation to the permissively licensed incumbent can replace local catalogue rendering under
ADR-0036/0065. Consilient would keep only the native selection, evidence and authority boundary.
[asserted]

## Publication candidate?

**No.** The design is unimplemented, the direct incumbent is already large and portable, and the
matched outcome experiment has not run. A later negative result about persona catalogues or a
replicated equal-starting-access improvement may be useful; this ADR is not that result. [asserted]

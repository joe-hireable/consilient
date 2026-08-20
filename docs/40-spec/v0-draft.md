# Consilient v0 implementation specification — draft for review

> **APPROVED FOR THE OBSERVE-ONLY INCREMENT — 20 August 2026, 01:22.** Joe sent the exact
> sentence §13.1 requires; it is recorded in the trajectory as `spec.approval_observed`.
> [measured]
>
> **What that authorises:** Stage 2 only — recording trajectory events, projecting them and
> computing β. The increment does not route, block or accept anything, and a test asserts the
> CLI exposes no surface that could. **Routing, blocking and orchestration remain gated** on
> ADR-0015 Gate A and Gate B, neither of which has passed. [measured]
>
> **Corrected 20 August 2026.** This block read *"DRAFT · NOT APPROVED · NO IMPLEMENTATION
> AUTHORITY… product implementation remains forbidden"* for the fifteen hours after the
> approval it describes. Two agents read it and drew the wrong conclusion about what they were
> permitted to do. A stale gate marker in the specification's own header is worse than a stale
> one anywhere else, because it is the document every other document defers to. [measured]

**Version:** 0.1-draft · **Date:** 19 August 2026 · **Owner:** Joe Brown ·
**Evidence base:** [`../decisions/index.md`](../decisions/index.md),
[`../10-research/experiment-register.md`](../10-research/experiment-register.md), and the
authoritative EXP-16 scope event in `.harness/log/2026-08-19.jsonl`. [measured]

## 1. Outcome and boundary

Consilient v0 is a local-first, CLI-only instrument for coding work that measures how
often a repository's automated checks accept a human-rejected artefact, then uses that
measurement to admit and route bounded agent attempts only after the dogfooding gates
permit control. [asserted]

Coding is the first domain because tests, typecheck and build provide a cheap automated
oracle against which β can be measured. [asserted] This draft does not claim that β is an
adequate centre for research, administration or other oracle-poor work; Q24 remains open.
[asserted]

The selected v0 candidate list is the β-meter, a fixed cascade, budget and hardware
admission, parallel worktrees and a critic tier, delivered in the sequence below.
[asserted] Joe selected the full list at 15–30 available hours per week; three consecutive
months below ten trajectory-recorded hours per week reinstates the narrow β-meter-only
provisional. [measured]

## 1.1 Outcome reporting

The product outcome is **verified human gain while preserving agency**. [asserted] Quality,
speed, cost, review burden, learning, self-efficacy, stress and user-valued outcomes are
recorded and reported **separately**, and are never combined into a single score, index or
ranking. [asserted] This is not presentational. Satisfaction and quality are anti-correlated
through a measured mechanism — sycophantic output was rated 9% higher in quality and 13% more
likely to be reused while cutting the behaviour it was meant to support — so any composite
would be pushed up by exactly what pushes β up. [cited] V0-21 carries the check.

The harness is **decisive by default**: it decides reversible questions itself, records how
to reverse them, and reserves the user's attention for the classes ADR-0033 names — money,
credentials, preferential questions, the safety floor, the β verdict, anything leaving the
machine, and lifting a gate. [asserted] Asking is not free and not neutral: the interventions
that most reduce over-reliance are the ones users find harder, prefer less and trust less, and
their benefit falls unevenly. [cited] An ask the user cannot afford to answer does not transfer
a decision; it launders an agent decision as a human one. [asserted]

Agency is treated as a mechanism rather than a courtesy: the best-measured protective factor
against developer burnout under generative AI was autonomy, and mandated adoption sat on the
demands side of the same model. [cited] An orchestrator that mandates a workflow, or that
becomes a management metric, is a cost regardless of its output quality. [asserted]

## 2. Non-goals

- A learned routing policy is excluded from v0. EXP-07 has since run the pre-registered
  replication at n=30 and **ADR-0003 was not reopened**: the single-attempt median multiplier is
  1.69×, which does not cross the 2× trigger, and only best-of-five crosses at 17.95× (16.75×
  clamped). The registered finding is that scaffolding creates the wasted work, not the raw local
  attempt. [measured] See § 8 and `../decisions/0003-no-learned-routing-policy-in-v0.md`.
- The Inquiry tier is excluded unless Joe resolves Q14 in its favour. [asserted]
- A graphical review surface, TUI, web server, model engine, model catalogue, benchmark
  leaderboard, autonomous model purchase and unbounded chat are excluded. [asserted]
- OpenRouter is a provider, not a coding agent; Slack and ClickUp are projections, not
  authoritative coordination state. [asserted]
- Stable cross-runtime social identity, persona-based performance roles and same-turn
  typed steering are excluded until EXP-24, EXP-25 and EXP-26 respectively satisfy their
  pre-registered promotion rules. [asserted]
- Executive titles are excluded from product scope as roles: a title is presentation and
  never an authority, capability, admission or routing input, so admitting one would reinstate
  the governance layer ADR-0010 cut and would require an ADR superseding it rather than an
  edit. [asserted] Vendor names are excluded as roles for a different reason: under ADR-0027 a
  backend is “a composed action rather than an indivisible coding-agent name”. [cited] The repository's own pre-spec
  working arrangement in
  [`../10-research/agent-identity-and-collaboration.md`](../10-research/agent-identity-and-collaboration.md)
  is a working convenience, not v0 scope, and no check enforces it. [asserted]
- Consilience does not distribute model weights or reproduce content from the private
  measurement corpora. [asserted]

## 3. Delivery sequence and irreversible gates

### Stage 1 — bootstrap without dependence

Existing agents may produce research instruments, adapters, ADRs and this draft, but
Consilience is not on the critical path and may not route work. [asserted] Experimental
adapter outcomes remain measurements, not product interfaces. [asserted]

Three boundaries bind who performs that work. They belong to this draft because they are the
gate, not the staffing; the assignment itself is recorded in
[`../10-research/agent-identity-and-collaboration.md`](../10-research/agent-identity-and-collaboration.md).
[asserted]

1. Only Joe approves, rejects or supersedes this specification, and only Joe lifts a gate. No
   agent may author a record of such an approval on his behalf. [asserted]
2. Mutable work has one lease holder at a time however many actors are assigned; an
   assignment is not a licence to write concurrently. [asserted]
3. A second actor is worth adding to a task only where it introduces a different class of
   facts; one that re-reads the first actor's output adds no assurance. [asserted] The
   measured case is EXP-07: the author's own four instrument tests passed, an independent
   `claude-opus-5` audit then found four further defects, and the replication was aborted
   before a verdict. [measured]

### Stage 2 — observe only, entered on approval, exited through Gate A

The first product increment records versioned trajectory events, verifier outcomes and
human verdicts; it computes β with sample count and uncertainty, but never blocks or routes
a task. [asserted]

**Corrected 2026-08-20.** This section previously read "after Gate A", which is circular:
Gate A requires seven days of trajectory capture and a replay invariant green in CI, and
neither can exist until the recorder does. [measured] Stage 2 is therefore *entered* when Joe
approves the specification and *exited* through Gate A, which matches ADR-0015's ordering of
instrumentation before control. [asserted] Nothing about the safety properties changes: the
increment records and reports, and cannot route, block or accept at any point. [asserted]

Gate A must hold before any routing or blocking behaviour is built or enabled, and before β
is consumed for anything beyond display. It requires all of the following, with no manual
override: [asserted]

1. EXP-01 complete on at least two repositories with different verification quality and a
   reported confidence interval. [asserted]
2. Deleting SQLite and replaying the trajectory reproduces an **identical canonical state
   digest** in CI. Not a byte comparison of the database file: SQLite files are not byte-stable
   across rebuilds, because the header carries a change counter and a schema cookie, the freelist
   and page allocation depend on insertion history, and WAL adds a random salt. `state_digest()`
   hashes a canonical ordered dump of the rows instead, which is what "the database is a
   projection" actually means. [measured]
3. Seven consecutive days of trajectory capture complete with no data loss. [asserted]

### Stage 3 — route, criticise and orchestrate, after Gate B

Control begins on a project other than Consilience only after Gate B. [asserted]

1. EXP-05 is complete and a second adapter did not force a shared-interface redesign.
   [measured]
2. EXP-08 is complete and measured critic recall yields a parallelism ceiling greater
   than one. [asserted]
3. A one-command bare-agent fallback exists and a scheduled check exercises it weekly.
   [asserted]
4. Twenty non-Consilient tickets complete without intervention in the harness itself.
   [asserted]

The bare-agent fallback remains permanent; Consilience must never become the only way to
work on its own repository. [asserted]

## 4. Required records

### 4.1 Authoritative event

Every state transition is a schema-versioned event appended to
`.harness/log/YYYY-MM-DD.jsonl`; `.harness/state.db` is a gitignored SQLite WAL projection
that is fully rebuildable from those events. [asserted]

Every contribution record must identify at least: [asserted]

- human or service principal and its authority grant; [asserted]
- runtime/session identity, execution harness, provider and model; [asserted]
- task, attempt, role and current write-lease epoch; [asserted]
- evidence class and source references; [asserted]
- artefact references and declared allowed-change boundary; [asserted]
- automated verifier result, human verdict when available and outcome timestamps;
  [asserted]
- usage in the backend's native accounting units, accounting source and observation time;
  [asserted]
- causation and correlation identifiers for retries, hand-offs and external projections.
  [asserted]

Display names and personas are never credentials, authority signals or evidence of
capability. [asserted] Until EXP-24 promotes logical identity, runtime identity plus
principal, role and provenance is sufficient. [asserted]

An event recording a human decision — approval, gate lift, spend authorisation or β verdict —
is valid only when the human principal is also its author, with the arrival channel recorded.
[asserted] The principal field names whose authority is being exercised; it is not itself an
authority grant, and no agent-authored event becomes the human's decision. [asserted] This has
already failed on identity-free projections: EXP-16 recorded a fabricated human-participation
claim in a meeting no human joined. [measured]

### 4.2 Task and attempt

A task fixes the goal, verifier contract, permitted file or artefact boundary, budget,
authority, time bound and stopping rule before work begins. [asserted] A changed goal is a
versioned rebaseline event rather than an edit to history. [asserted]

Each attempt has exactly one recorded route decision before dispatch. [asserted] Retries
are new attempts linked to the originating task and charge that task's resource cap.
[asserted]

Mutable work has exactly one active owner and monotonically increasing lease epoch.
[asserted] Delegation creates a bounded child task while the parent retains responsibility;
handoff changes the unique owner and fences the old epoch; consultation exchanges evidence
without changing authority. [asserted]

### 4.3 External projections

Git trajectory and its SQLite projection are authoritative. [asserted] Slack, ClickUp and
future collaboration platforms receive compact evidence deltas and may submit authorised
commands, but retries, edits or deletions there cannot rewrite history. [asserted]

Projection messages contain evidence delta, blocker, handoff or decision only; presence,
typing and ambient status never enter model context. [asserted]

## 5. β and verifier contract

For a fixed repository, task family and verifier contract, β is the conditional rate at
which the automated verifier accepts an artefact the human verdict rejects. [algebra]
Self-reported model confidence or process exit success is diagnostic only and cannot accept
an artefact. [asserted]

**β is conditional on an oracle that is itself a test.** The human verdict is error-prone,
is not independent of the automated checks, and may not be stationary. [cited] Measured
support: no complementarity was achieved between human and model where their error boundaries
aligned; task completion coexists with an illusion of competence; and in-session performance
rose while unaided performance fell. [cited] Every reported β therefore states that it is a
**lower bound on a joint human-plus-checks error**, not a property of the checks alone.
[asserted] `../10-research/human-success-and-the-human-side-of-beta.md` carries the evidence
and Q30 carries the open question; EXP-32 measures the non-stationarity mechanism. [asserted]

**No self-report is an acceptance signal, including the human's.** Working principle 5 bans
gating on a model's claimed confidence; the same rule applies to user satisfaction, a
thumbs-up, or an answer to "did that help?". [asserted] Measured support: developers reported
a 20% speedup after a measured 19% slowdown, and sycophantic responses were rated higher in
quality and more likely to be reused while degrading the outcome they described. [cited] A
satisfaction signal that rises is a prompt to investigate, never evidence of gain. [asserted]

The routing input is the directly measured composite-verifier β; per-check outcomes remain
diagnostics because their dependence is unknown. [asserted] Every displayed or consumed β
value includes task family, verifier version, sample count, observation window, interval
and verdict such as `insufficient_data`. [asserted]

No proxy label may be silently treated as a human verdict. [asserted] EXP-01's first pass
found hotfix-label precision of 1/15 in each audited private corpus and therefore remains
audit-limited with an honest `insufficient data` result. [measured]

Verifier acceptance covers both functional checks and the permitted artefact boundary.
[asserted] The first OpenCode smoke run passed tests while creating an unrequested file,
demonstrating that tests alone did not enforce the requested scope. [measured]

## 6. Composed backend and admission boundary

Every candidate action is represented as `(domain, execution harness, provider, model)`;
unknown components remain explicit rather than inferred. [asserted] Public benchmarks may
discover candidates, while local verifier-labelled outcomes decide routing weight unless
EXP-22 promotes a prior. [asserted]

For coding, vendor-native Claude Code, Codex and Cursor paths are eligible only when their
required authentication and subscription headroom are usable. [asserted] OpenCode is the
default coding harness when no vendor-native frontier harness is configured; its provider
and model still pass the same admission boundary. [asserted]

Antigravity is ineligible until a fresh plan-tier/quota snapshot, structured execution
probe and `useG1Credits=false` check all pass. [asserted] Google-plan Antigravity, Gemini
API access and OpenRouter-hosted Gemini are separate compositions and accounting ledgers.
[asserted]

Cursor ACP is an external control surface; MCP supplies tools to Cursor and is not itself
a substitute control protocol. [asserted]

First-party release, changelog, documentation and status events are change intelligence,
not account-resource observations. [asserted] They may invalidate cached capability or
temporarily remove an explicitly affected service, but may never increase headroom, move a
reset or admit unknown resource state. [asserted] Every dispatch still performs the
composition's required version/capability handshake. [asserted]

Admission constructs a feasible candidate set before β-centred selection. [asserted] A
backend is infeasible if any applicable subscription-headroom, monetary-budget,
authentication, permission or local-hardware constraint is false or unknown for unattended
work. [asserted] These are structural vetoes, not new coordinates in the
`(Δ, α, β, ρ)` quality-safety surface. [asserted]

## 7. Resource accounting

Included subscriptions, metered providers and local compute use separate ledgers because
their scarcity and failure modes differ. [asserted]

### 7.1 Included subscriptions

Provider-native quota windows are recorded without conversion into a fictional shared
token unit. [asserted] Fresh authoritative headroom is preferred; local trajectory
accounting can lower an availability estimate but cannot promote it to provider truth
because usage may occur outside Consilience. [asserted]

Resource records are keyed by account, provider, plan, native bucket and native window;
concurrent or nested windows remain separate. [asserted] A current user attestation may
authorise a bounded supervised subscription attempt but is not provider truth and cannot
admit unattended work. [asserted]

Unknown or stale headroom excludes a subscription from unattended routing. [asserted]
Reset-aware scheduling may rank only a user-authorised backlog and must maximise incremental
verified value per human review hour, never raw token use. [asserted] Live reset scheduling
and plan-rightsizing advice remain behind EXP-23. [asserted]

### 7.2 Metered providers

Metered work is off by default and requires an explicitly authorised per-task cap and
per-period cap. [asserted] Both are hard stops; retries, verification and recovery charge
the originating task. [asserted]

Where supported, a provider-enforced scoped key supplies the outer cap and a
concurrency-safe local reservation supplies the inner cap. [asserted] Automatic top-up and
automatic escalation to a more expensive metered model are disabled. [asserted] No
provider-enforced cap means no unattended metered route. [asserted]

### 7.3 Local models

An installed fit provider must decide model-revision, quantisation, context, engine and
hardware compatibility before the harness transfers model bytes. [asserted] Infeasible or
unknown means no harness-initiated download or execution. [asserted]

Consilience wraps rather than builds this capability; `llmfit` is the current candidate in
[ADR-0026](../decisions/0026-admit-only-budget-and-hardware-feasible-backends.md), but adding
it remains a separate dependency-approval decision. [cited] EXP-21 must validate
the constraint case on a real 16 GB machine; replaying the RTX 5090/64 GB measurements is
simulation, not constraint-case measurement. [asserted]

## 8. Fixed cascade and escalation

The v0 policy is deterministic and inspectable. [asserted] Within the admitted set it
chooses a starting tier using the task-family capability gap `Δ`, composite β with
uncertainty, false-rejection `α`, known failure correlation `ρ`, elapsed-time multiplier
and user constraints. [asserted]

The verifier runs at task completion. [asserted] Verifier rejection, resource exhaustion
or a declared stopping condition produces a recorded terminal outcome or a new, separately
admitted attempt; the model's confidence cannot trigger success. [asserted]

**Superseded by EXP-07, 20 August 2026.** The pilot figure below is retained because it is what
prompted the replication, but it is no longer the best available evidence. The replication at
n=30 found the single-attempt median multiplier to be **1.69×**, which does not cross the
threshold, while best-of-five reached **17.95×** (16.75× clamped). ADR-0003 is therefore not
reopened, and the registered finding is that scaffolding rather than the raw local attempt
creates the wasted work. [measured] A further finding from the same run bears directly on this
section: `qwen3:8b` produced no file edit in any of 25 attempts, which is a capability question
prior to any latency one — EXP-31 is running to establish whether that is the model or the
composition. [measured]

EXP-05 measured one failed local attempt at 114.2 seconds versus frontier successes at
20.4–25.6 seconds, a 4.5–5.6× wasted-work multiplier on one trivial task. [measured] This
crossed EXP-07's ≥2× investigation trigger and made replication high priority, but n=1 does
not justify a learned router. [measured]

## 9. Critic and parallel worktrees

The critic receives an artefact, task contract and a genuinely different evidence class
such as independent verifier output or separately collected repository evidence.
[asserted] A second agent merely re-reading shared context is echo and cannot justify a
critic or meeting. [asserted]

Parallel execution is restricted to independent work units in isolated worktrees with one
write lease per task/file boundary. [asserted] Its ceiling is derived from measured cycle
time and effective human review time after critic filtering; it is not a user-entered agent
count. [algebra]

EXP-08 must demonstrate critic recall high enough for a ceiling above one before parallel
orchestration can pass Gate B. [asserted] Meetings, if later admitted, require one Owner,
participants selected for different evidence, fixed budgets, a named exit artefact and
preserved dissent; agreement is not an acceptance signal. [asserted]

## 10. CLI surface

v0 has one CLI and no daemon-backed review UI. [asserted] Every command supports a stable
machine-readable `--json` form, and human output is a rendering of the same result rather
than a second semantics. [asserted]

Any surface that shows the agent's reasoning is treated as an **acceptance amplifier until
measured otherwise**: explanations raised relative reliance on the model from 29.59% to 38.87%
while leaving the ability to reject it statistically unchanged, and surfaced token-level
uncertainty reduced over-reliance only by increasing under-reliance. [cited] v0 therefore
displays evidence and verifier outcomes, not model rationale, and any future rationale surface
ships with a measurement of its effect on acceptance. [asserted]

`consil doctor` reports authentication, control-path readiness, headroom freshness,
hardware-fit provider state, installed/runtime capability freshness, watched-source
freshness, gate state, fallback health and reasons a composition is ineligible. [asserted]
It cannot waive Gate A, Gate B or a resource veto. [asserted]

The remaining command names are intentionally not fixed by this draft; behaviour and event
contracts must be approved before naming surface area. [asserted]

## 11. Enforcement matrix

Every requirement below is an implementation chokepoint. [asserted] Its implementation and
the named failing check must land in the same future commit; documenting a later test does
not satisfy the invariant. [asserted]

| ID | Required invariant | Same-commit check | Source |
|---|---|---|---|
| V0-01 | Every event is schema-versioned and append-only. [asserted] | Fixture rejects unversioned events and mutation of committed positions. [asserted] | ADR-0006 |
| V0-02 | SQLite is only a projection of JSONL. [asserted] | Delete/replay reproduces an identical `state_digest()` over a canonical row dump — **not** a byte comparison of the database file, which SQLite does not make stable; lint bans state-only writes. [measured] | ADR-0006 |
| V0-03 | A task fixes goal, verifier, authority, artefact boundary and caps before dispatch. [asserted] | Schema and transition tests reject incomplete dispatch and silent rebaseline. [asserted] | working principles, ADR-0021 |
| V0-04 | Exactly one route decision exists per attempt. [asserted] | State-machine property test rejects zero or duplicate decisions. [asserted] | ADR-0009 |
| V0-05 | Only verifier/human outcomes accept artefacts. [asserted] | Seeded successful-process/bad-artefact fixture is rejected. [asserted] | working principle 5, EXP-05 |
| V0-06 | Routing consumes composite β with n and interval. [asserted] | Boundary tests reject per-check substitution, missing uncertainty and insufficient-data promotion. [asserted] | ADR-0002, ADR-0012 |
| V0-07 | Domain, harness, provider and model remain separate. [asserted] | Schema/adapter contract tests reject conflated or inferred identities. [asserted] | ADR-0027 |
| V0-08 | One admission boundary vetoes unavailable actions. [asserted] | Lint bans direct dispatch/download; concurrency and stale-snapshot tests fail closed. [asserted] | ADR-0026 |
| V0-09 | Subscription, metered and local ledgers remain separate. [asserted] | Accounting tests reject cross-ledger conversion and prove hard-cap reservation under retries. [asserted] | ADR-0026, ADR-0028 |
| V0-10 | Local fit is decided before model bytes transfer. [asserted] | Fake downloader observes zero bytes for infeasible and unknown profiles. [asserted] | ADR-0026 |
| V0-11 | Mutable scope has one owner and fenced lease epoch. [asserted] | Race test rejects every stale-owner mutation after handoff. [asserted] | ADR-0020 proposal, EXP-26 |
| V0-12 | Multi-agent work names a different evidence class. [asserted] | Admission test rejects shared-context-only delegation and meetings. [asserted] | ADR-0010 |
| V0-13 | External platforms are replayable projections only. [asserted] | Retry/edit/delete fixtures cannot duplicate or rewrite authoritative events. [asserted] | ADR-0006 |
| V0-14 | Every command has one JSON contract. [asserted] | CLI contract tests compare human rendering against the JSON result. [asserted] | ADR-0007 |
| V0-15 | Dogfooding gates and bare fallback cannot be bypassed. [asserted] | Gate matrix plus weekly fallback job fail closed. [asserted] | ADR-0015 |
| V0-16 | Secrets never enter chat, git or trajectory. [asserted] | Secret scan plus credential-provider contract test; raw values are rejected before event append. [asserted] | working boundary, ADR-0019 |
| V0-17 | Change intelligence cannot create resource state or replace dispatch-time capability probes. [asserted] | Source-authority fixtures reject headroom/reset mutations and prove relevant events force a probe while missing feeds still fail closed. [asserted] | ADR-0029 |
| V0-18 | A human approval, gate lift, spend authorisation or verdict is valid only when the human principal authored it. [asserted] | Fixtures reject an agent-authored event carrying a human decision, and reject a human decision inferred from the principal field. [asserted] | ADR-0020 proposal, EXP-16 |
| V0-19 | Display name, title and persona are never an authority, capability, admission or routing input. [asserted] | Routing, admission and acceptance tests reject persona-derived inputs; a property test asserts that changing a display name changes no decision. [asserted] | ADR-0010, ADR-0025 |
| V0-20 | Every convened or fanned-out structure carries hard budget, turn and depth caps, and exhaustion escalates. [asserted] | Loop test asserts an over-budget structure terminates and escalates rather than continuing; a recursion-depth assert fails closed. [asserted] | ADR-0020 proposal |
| V0-21 | Outcome dimensions are reported separately and never composited; no self-report, human or model, is an acceptance or routing input. [asserted] | Contract test rejects any composite outcome score; routing and acceptance tests reject satisfaction, thumbs-up and confidence fields as inputs. [asserted] | Q30, working principle 5 |
| V0-22 | Every autonomous decision records a reversal path; one without it is an ask, not a decision. [asserted] | Schema test rejects an autonomous decision event lacking a reversal field. [asserted] | ADR-0033 |
| V0-23 | The harness asks only in the classes ADR-0033 names, and an approval returned below the affordability floor is stored unread and cannot satisfy a human decision. [asserted] | Configuration-load test rejects an unlisted ask class; fixture proves a below-floor approval fails V0-18. [asserted] | ADR-0033 |
| V0-24 | A recorded reversal is executable, and reversibility is measured rather than declared. [asserted] | Schema test rejects a reversal that is not a revert reference, a command or a named inverse; a sampler executes recorded reversals in a scratch worktree and publishes the misclassification rate. [asserted] | ADR-0033 |
| V0-25 | Liveness is never resolved from a process identity, a terminal artefact record outranks a stale liveness signal, and detection escalates rather than terminating. [asserted] | Fixtures reject PID-only liveness, reproduce the Airflow completed-task-marked-failed regression, fail a configured-but-unfed progress channel at load, and reject termination without a standing authority. [asserted] | ADR-0034 |
| V0-26 | Multi-contributor events declare a distinct evidence class per contributor; duplicate, missing or empty classes are refused. [asserted] | Event validation rejects multi-contributor events with duplicate, missing or empty `evidence_class` declarations while accepting single-actor and distinct-class events. [asserted] | ADR-0010 |

## 12. Acceptance evidence and release decision

No milestone is promoted by agent agreement, process completion or elapsed effort.
[asserted] Promotion requires its pre-registered experiment or check to pass without a
stopping-rule violation; an inconclusive interval remains inconclusive. [asserted]

The first release candidate requires: [asserted]

- every applicable V0 invariant green; [asserted]
- Stage 2 Gate A evidence complete; [asserted]
- no committed secret or private-corpus content; [asserted]
- exact adapter/runtime versions and control/accounting capabilities recorded; [asserted]
- replay from the published fixture trajectory on Windows and one non-Windows environment;
  [asserted]
- evidence drawn from repository history rather than curated tasks, because the sign of the
  measured effect is set by task selection: +55.8% on a greenfield toy task against −19% on
  real issues in a developer's own mature repository. [cited] A release evaluated on curated
  tasks would measure the wrong regime; this is ADR-0013 with a sharper reason. [asserted]
- documentation of every unsupported or unknown provider capability, without fallback to
  metered credits. [asserted]

Stage 3 is a later promotion of the same product and additionally requires Gate B; it is
not implied by shipping Stage 2. [asserted]

## 13. Decisions still requiring Joe

1. Approve, reject or revise this specification; until then product implementation remains
   forbidden. [asserted] Approval means the sentence "I approve the v0 specification for
   implementation", recorded as a first-party event under V0-18. [asserted] Instructing the
   successor to revise, review or improve this draft is authorised work and is **not** that
   approval; the gate is not lifted by inference from an ambiguous message. [asserted]
2. Decide Q14: whether the Inquiry tier belongs in v0. [asserted]
3. Approve or reject `llmfit` if EXP-21 work reaches the dependency boundary. [asserted]
4. Resolve legal preference decisions before their gates: CLA versus DCO alone, and the
   proposed safety/moderation floor. [asserted]
5. Decide whether the pre-spec working arrangement needs its own ADR. ADR-0023's tiers
   enumerate technical blast radius rather than organisational structure, and ADR-0010 would
   have to be superseded rather than edited were the arrangement ever to become product
   scope. [asserted]

Authentication, metered-spend authority and blind human judgements are execution blockers,
not architecture decisions: Antigravity plan-backed authentication, any Gemini/OpenRouter
API use, the EXP-16 blind grade and EXP-01 human spot-check remain Joe-only inputs.
[asserted]

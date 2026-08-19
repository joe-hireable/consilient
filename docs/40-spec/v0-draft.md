# Consilience v0 implementation specification — draft for review

> **DRAFT · NOT APPROVED · NO IMPLEMENTATION AUTHORITY.** This document is a concrete
> target for criticism. Product implementation remains forbidden until Joe explicitly
> approves a specification or supersedes that gate. [asserted]

**Version:** 0.1-draft · **Date:** 19 August 2026 · **Owner:** Joe Brown ·
**Evidence base:** [`../decisions/index.md`](../decisions/index.md),
[`../10-research/experiment-register.md`](../10-research/experiment-register.md), and the
authoritative EXP-16 scope event in `.harness/log/2026-08-19.jsonl`. [measured]

## 1. Outcome and boundary

Consilience v0 is a local-first, CLI-only instrument for coding work that measures how
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

## 2. Non-goals

- A learned routing policy is excluded from v0; EXP-07 has reopened ADR-0003 for
  investigation but n=1 has not overturned it. [measured]
- The Inquiry tier is excluded unless Joe resolves Q14 in its favour. [asserted]
- A graphical review surface, TUI, web server, model engine, model catalogue, benchmark
  leaderboard, autonomous model purchase and unbounded chat are excluded. [asserted]
- OpenRouter is a provider, not a coding agent; Slack and ClickUp are projections, not
  authoritative coordination state. [asserted]
- Stable cross-runtime social identity, persona-based performance roles and same-turn
  typed steering are excluded until EXP-24, EXP-25 and EXP-26 respectively satisfy their
  pre-registered promotion rules. [asserted]
- Consilience does not distribute model weights or reproduce content from the private
  measurement corpora. [asserted]

## 3. Delivery sequence and irreversible gates

### Stage 1 — bootstrap without dependence

Existing agents may produce research instruments, adapters, ADRs and this draft, but
Consilience is not on the critical path and may not route work. [asserted] Experimental
adapter outcomes remain measurements, not product interfaces. [asserted]

### Stage 2 — observe only, after Gate A

The first product increment records versioned trajectory events, verifier outcomes and
human verdicts; it computes β with sample count and uncertainty, but never blocks or routes
a task. [asserted]

Gate A requires all of the following, with no manual override: [asserted]

1. EXP-01 complete on at least two repositories with different verification quality and a
   reported confidence interval. [asserted]
2. Deleting SQLite and replaying the trajectory produces byte-identical state in CI.
   [asserted]
3. Seven consecutive days of trajectory capture complete with no data loss. [asserted]

### Stage 3 — route, criticise and orchestrate, after Gate B

Control begins on a project other than Consilience only after Gate B. [asserted]

1. EXP-05 is complete and a second adapter did not force a shared-interface redesign.
   [measured]
2. EXP-08 is complete and measured critic recall yields a parallelism ceiling greater
   than one. [asserted]
3. A one-command bare-agent fallback exists and a scheduled check exercises it weekly.
   [asserted]
4. Twenty non-Consilience tickets complete without intervention in the harness itself.
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

`consil doctor` reports authentication, control-path readiness, headroom freshness,
hardware-fit provider state, gate state, fallback health and reasons a composition is
ineligible. [asserted] It cannot waive Gate A, Gate B or a resource veto. [asserted]

The remaining command names are intentionally not fixed by this draft; behaviour and event
contracts must be approved before naming surface area. [asserted]

## 11. Enforcement matrix

Every requirement below is an implementation chokepoint. [asserted] Its implementation and
the named failing check must land in the same future commit; documenting a later test does
not satisfy the invariant. [asserted]

| ID | Required invariant | Same-commit check | Source |
|---|---|---|---|
| V0-01 | Every event is schema-versioned and append-only. [asserted] | Fixture rejects unversioned events and mutation of committed positions. [asserted] | ADR-0006 |
| V0-02 | SQLite is only a projection of JSONL. [asserted] | Delete/replay produces byte-identical state; lint bans state-only writes. [asserted] | ADR-0006 |
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
- documentation of every unsupported or unknown provider capability, without fallback to
  metered credits. [asserted]

Stage 3 is a later promotion of the same product and additionally requires Gate B; it is
not implied by shipping Stage 2. [asserted]

## 13. Decisions still requiring Joe

1. Approve, reject or revise this specification; until then product implementation remains
   forbidden. [asserted]
2. Decide Q14: whether the Inquiry tier belongs in v0. [asserted]
3. Approve or reject `llmfit` if EXP-21 work reaches the dependency boundary. [asserted]
4. Resolve legal preference decisions before their gates: CLA versus DCO alone, and the
   proposed safety/moderation floor. [asserted]

Authentication, metered-spend authority and blind human judgements are execution blockers,
not architecture decisions: Antigravity plan-backed authentication, any Gemini/OpenRouter
API use, the EXP-16 blind grade and EXP-01 human spot-check remain Joe-only inputs.
[asserted]

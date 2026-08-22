# Hermes Agent teardown: the named incumbent

**Research snapshot:** 2026-08-22T14:05:14+01:00
**Upstream examined:** NousResearch/Hermes Agent `261a4ef`
(`pyproject.toml` 0.20.5); latest release `v2026.8.19` (0.20.5). [cited]
**Local executable:** Hermes Agent 0.17.0 at upstream `44d552ea`; it is older than the examined
upstream and is not treated as the current product. [measured: `hermes --version`, 22 Aug 2026]

The brief's inference from `role="leaf"` is wrong, and the principal is wrong about the present
difficulty: a leaf cannot delegate, but current Hermes does have opt-in nested orchestration and a
real durable cross-agent board, while Consilient cannot route work today and its supposed human-only
event boundary accepts self-declared principal identity. [cited] [measured] **Hermes is the stronger
working product today.** [asserted: synthesis from the evidence below] The principal's prospective
claim that a few targeted swarms can beat it *easily* is **unknowable**, not false: no experiment yet
measures build effort or attributes a gain to swarming. [measured] Whether a future frozen Consilient
composition beats Hermes on accepted outcomes per pound and minute also remains unmeasured.
[asserted]

## Direct answers

| Question | Finding |
|---|---|
| Does `delegate_task` nest? | **Yes, but not through `leaf` and not by default.** The default maximum spawn depth is one: root to leaf. With `role="orchestrator"` and `max_spawn_depth >= 2`, children may delegate; the current implementation has no upper depth clamp. [cited] |
| Do siblings coordinate? | Delegate siblings have isolated conversations and no direct sibling messaging. Their parent can list, steer and stop descendants, then synthesise final summaries. They share the starting checkout by default, so filesystem collision or indirect signalling remains possible; worktree isolation is opt-in. [cited] |
| Is `hermes kanban` a renamed todo list? | **No.** It is a durable, single-host, SQLite-backed work queue for named profiles, with tasks, dependencies, assignment, comments, attempts, review, attachments, atomic claims, restart recovery and a dispatcher. The ordinary `todo` tool remains session-local. [cited] |
| What persists? | SOUL instructions, bounded MEMORY/USER stores, full session records, learned skill packages and scripts, completed delegate results, and Kanban task/attempt/handoff state persist. A running delegate is not resumed after restart, scratch files not declared as artefacts are deleted, and stored worker summaries remain claims rather than verified truth. [cited] |
| What does Hermes measure? | More than nothing: command evidence, opt-in verify-on-stop, deterministic goal gates, an LLM goal judge, ordinary tests, and narrow read/browser/compaction evaluations. It does **not** publish a calibrated false-accept/false-reject rate for those acceptance mechanisms against human ground truth. [cited] [measured: bounded source search below] |
| Whose authority is it? | Hermes has configurable action approvals, an absolute command deny floor, and billing-specific caps, roles, kill switches and portal consent. It has no general system-wide rule that publication, gate lifts, consent or verdicts are valid only when authored by the human. The default smart mode lets an auxiliary LLM approve commands classified low-risk; manual and human-only review modes are optional. [cited] [measured: bounded source search] [asserted: scope inference] |
| Is failure documented? | Yes. Current open issues cover false goal completion, unverified Kanban completion, runaway delegation cost, cost undercounting, cross-profile writes, dispatcher lock failure and silently dropped memory writes. Current upstream also fails two focused repository tests on this Windows machine. [cited] [measured] |

## Evidence classes and search log

**Local primary files.** Every file required by the brief was read before upstream retrieval:
`superpowers/6.3.0/skills/using-superpowers/references/hermes-tools.md`; both named version-bump
design/plan files; all four files under `tests/hermes/`; both files under `.hermes-plugin/`; and
Ponytail's `tests/hermes-plugin.test.js`. [measured] The Superpowers test slice passed 19/19 and the
Ponytail Hermes plugin slice passed 8/8. [measured: `python -m pytest tests/hermes -q`; `node --test
tests/hermes-plugin.test.js`, 22 Aug 2026]

**Hermes primary sources.** A gitignored clone of `NousResearch/hermes-agent` was pinned to
`261a4ef`; its user documentation, implementation, tests and three
evaluation directories were read. [measured: local clone identity] The GitHub release list and the
current open issue records cited below were retrieved on 22 August 2026. [cited]

**Negative search.** A case-insensitive search of the pinned tree's Markdown, Python and TOML,
excluding translated documentation, bundled skills and test fixtures, found no product or evaluation
use of `verifier error`, `P(accept`, `human reject` or `conditional ... accept`. The apparent hits for
`false accept`, `Wilson`, `confusion matrix` and `acceptance rate` were JSON parsing text, a contributor
name, or generic research-skill examples rather than a Hermes acceptance calibration. [measured:
bounded source search, 22 Aug 2026] This establishes absence in the searched snapshot, not universal
absence. [asserted]

**What was not done.** No metered provider call, live nested Hermes swarm or multi-process Kanban
campaign was run. [measured] Upstream source and repository tests confirm mechanics; Hermes's own
published evaluations remain vendor-produced until independently reproduced. [asserted]

## What the local mapping proves—and does not

| Local evidence | What it proves | What it does not prove |
|---|---|---|
| `skills/using-superpowers/references/hermes-tools.md:7-19` maps dispatch to `delegate_task(..., toolsets=[...], role="leaf")`; lines 44-52 say “isolated subagents”. [measured: local file text] | Superpowers exposes a Hermes integration surface. [measured] | It does not establish nested delegation or output quality. Current upstream's model-facing signature has no `toolsets` parameter; the mapping is stale on that detail. [`delegate_tool.py:118-120,3597-3629`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L118-L120) [cited] |
| The same mapping, lines 54-56, says `todo` is “within a session” and directs multi-agent boards to `hermes kanban` “if available”. [measured: local file text] | It correctly separates two task surfaces. [measured] | It does not prove the board's storage, claiming or recovery semantics. [asserted] |
| `.hermes-plugin/__init__.py:74-104` registers skills and injects first-turn bootstrap context; `tests/hermes/test_plugin.py:40-95` exercises both. [measured: local file text and 19 passing tests] | The Superpowers plugin wiring works in its focused test harness. [measured] | It says nothing about Hermes core delegation, Kanban, correctness or authority. [asserted] |
| The version-bump design explicitly says “No Hermes runtime changes” at lines 48-54; the plan is release wiring. [measured: local file text] | These files are useful provenance for plugin packaging only. [measured] | Treating them as Hermes runtime evidence would be category error. [asserted] |
| Ponytail's `tests/hermes-plugin.test.js:30-45,47-100,154-177` checks manifest, skill/command registration and injected mode context. [measured: local file text and 8 passing tests] | Ponytail's Hermes adapter is real and tested. [measured] | It does not benchmark Hermes or Ponytail task outcomes. [asserted] |

## Delegation: hierarchical, opt-in and parent-mediated

Current source sets `MAX_DEPTH = 1`, documents that depth zero may spawn depth one, and reads an
operator `max_spawn_depth` with a floor of one and no ceiling. [`delegate_tool.py:129-135,973-1009`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L129-L135)
[cited] The call default is `leaf`; only an effective `orchestrator` below the configured depth floor
gets the delegation tool back. [`delegate_tool.py:1618-1623,1683-1700,3597-3629`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L1618-L1623)
[cited]

The resulting depth semantics are exact: one is root → leaf; two is root → orchestrator → leaf;
generally, agents at depths `0..N-1` may spawn and depth `N` is the leaf floor, provided every
intermediate child is explicitly an orchestrator. [algebra from cited implementation] Source has no
spawn-depth ceiling, although descendant ownership traversal defaults to eight hops, so an extremely
deep tree may outgrow a distant ancestor's control reach. [`delegate_tool.py:380-398`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L380-L398)
[cited]

Children receive separate conversations, terminal task state and linked sessions; only final
summaries return to the parent. The tool description warns that those summaries are self-reports and
must be checked for external effects. [`delegate_tool.py:4614-4646`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L4614-L4646)
[cited] `send_message` is blocked and ownership excludes sibling trees, so sibling coordination is
parent-mediated rather than peer-to-peer. [`delegate_tool.py:49-58,380-398`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L49-L58)
[cited]

Isolation is contextual, not absolute. Siblings start from the same workspace/container unless
`worktree_isolation` is enabled; unsupported or failed setup falls back to sharing.
[`delegation.md:390-423`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/delegation.md#L390-L423)
[cited]
That lets siblings communicate through files but also creates collision risk. [asserted]

Six focused upstream tests for delegation/Kanban isolation passed on this machine. [measured:
`python -m pytest tests/tools/test_delegate_kanban_isolation.py -q`, 22 Aug 2026] The repository's
recursive “end-to-end” delegation test mocks the agent/provider, so it confirms control flow rather
than live model effectiveness. [`tests/tools/test_delegate.py:1660-1759`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tests/tools/test_delegate.py#L1660-L1759)
[cited]

## Kanban: a real board, separate from delegation

Hermes documents Kanban as a durable board shared by named profiles: task and handoff rows live in
SQLite and workers are distinct OS processes. [`kanban.md:7-20`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md#L7-L20)
[cited] Its comparison with `delegate_task` distinguishes durable peer coordination, retries,
human comments and retained audit rows from an in-process parent/child call.
[`kanban.md:32-53`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md#L32-L53)
[cited]

The implementation uses SQLite transactions and compare-and-swap status/claim updates, so at most
one dispatcher claims a task through the supported path. [`kanban_db.py:61-68,4617-4727`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/kanban_db.py#L61-L68)
[cited] Tasks persist dependency links, comments, events, attempts, summaries, metadata and
attachments; dispatcher logic promotes ready work and reclaims stale/crashed attempts.
[`kanban_db.py:1333-1495`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/kanban_db.py#L1333-L1495)
[cited]

Kanban is not a hidden sibling message bus for ordinary delegates: `delegate_task` strips the
Kanban toolset from every child. [`delegate_tool.py:1683-1692`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegate_tool.py#L1683-L1692)
[cited] Peer coordination belongs to full named profile workers on the board; nested delegation and
Kanban are complementary mechanisms. [cited]

The board is single-host and mutable, not an append-only truth ledger. Scratch workspaces delete
undeclared files on completion, stored results can be edited/backfilled, and garbage collection may
remove old terminal-task events. [`kanban.md:47,821`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md#L47),
[`kanban_db.py:6181-6232,11864-11882`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/kanban_db.py#L6181-L6232)
[cited] This is a limitation, not a reason to relabel it as a todo list. [asserted]

## Persistence beyond SOUL

| Store | Confirmed persistence and limit |
|---|---|
| SOUL | Durable user-authored identity/instructions; Hermes seeds but does not overwrite an existing file. It is prompt input, not learned memory. [`personality.md:9-38`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/personality.md#L9-L38) [cited] |
| MEMORY and USER | Bounded, curated cross-session stores (documented budgets 2,200 and 1,375 characters), frozen into a session-start snapshot. Writes become visible next session. [`memory.md:9-31,51-58`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/memory.md#L9-L31) [cited] |
| Learned procedures | `/learn` can turn conversation, files or web material into durable skill packages containing instructions, references, templates, scripts, examples and assets. [`skills.md:94-147,302-322`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/skills.md#L94-L147) [cited] |
| Native capability and authority | A learned skill can preserve procedures and executable support scripts, but the examined path does not create a native tool schema, widen tool permissions or grant authority. [measured: source trace] [asserted: boundary interpretation] |
| Sessions | Full message history, tool calls/results, reasoning fields and parent-session links persist in profile `state.db` and can be resumed. [`sessions.md:9-27,100-120`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/sessions.md#L9-L27) [cited] |
| Delegate results | Completed asynchronous results and child transcripts persist; execution that was still running is not resumed after restart. [`delegation.md:128-141,363-378`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/delegation.md#L128-L141) [cited] |
| Kanban results | Tasks, per-attempt outcomes, summaries, metadata, comments, dependencies and declared attachments persist, subject to editing, deletion and GC. [`kanban_db.py:6181-6232,11864-11882`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/kanban_db.py#L6181-L6232) [cited] |

Memory and skill writes are allowed by default, including background self-improvement; optional
`write_approval: true` stages them for human review. [`memory.md:258-290,353-371`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/memory.md#L258-L290)
[cited] Hermes therefore already carries learned procedure across sessions; Consilient cannot claim
that persistence itself is novel. [cited] [asserted] Its open question is whether that carry-forward improves
held-out outcomes without poisoning, regression or authority leakage. [asserted]

## Correctness: real signals, no calibrated acceptance error

The answer to “what does Hermes measure?” is **not nothing**. [cited]

- Its verification ledger records recognised terminal/file evidence, makes an exit-zero
  verification command a pass and marks evidence stale after later edits. The ledger is passive; it
  neither runs the suite nor establishes human acceptance. [`verification_evidence.py:1-5,537-555,731-799`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/agent/verification_evidence.py#L1-L5)
  [cited]
- Verify-on-stop can nudge an agent that edited code without fresh test/build/lint evidence, but it
  is off by default and bounded to avoid trapping the agent. [`configuration.md:1058-1072`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/configuration.md#L1058-L1072)
  [cited]
- `/goal` uses an auxiliary LLM judge over the goal and latest response, optionally preceded by
  deterministic shell gates. Hermes's documentation explicitly says the judge can false-positive
  and false-negative, without publishing either rate. [`goals.md:76-90,131-149,277-285`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/goals.md#L277-L285)
  [cited]
- `delegate_task` can enforce JSON/schema shape with one repair attempt, but it has no independent
  semantic acceptance judge; Hermes tells the parent to inspect the diff or run tests. [`delegation_output_schema.py:1-8,105-135`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/delegation_output_schema.py#L1-L8)
  [cited]
- Its read-tool evaluation plants deterministic ground truth and reports accuracy/efficiency over
  three repetitions; both tested models retained 1.00 reported accuracy.
  [`evals/readtool/README.md:11-31,50-60`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/evals/readtool/README.md#L11-L31),
  [`SUMMARY.md:19`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/evals/readtool/results/SUMMARY.md#L19)
  [cited]
- Its browser evaluation uses regex oracles and reports task accuracy, tokens, calls and wall time.
  It warns that at most three repetitions per cell make success deltas noise, and that raw JSONL was
  lost in a reboot. [`evals/browser_use/README.md:17-22,52-69,102-114`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/evals/browser_use/README.md#L102-L114)
  [cited]
- Its compaction evaluation scores answer recall against gold on four real transcript lineages. The
  scorecard warns that one question moves a mean by about 3.3 points and that some rows used different
  question banks. [`SCORECARD-2026-08-15.md:1-20,335-349`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/evals/compaction/results/SCORECARD-2026-08-15.md#L1-L20)
  [cited]

These are component regression and task-performance signals. [cited] None of the examined sources
calibrates the goal judge, verification ledger, delegation summary, Kanban completion or smart
approval reviewer against a human accept/reject series to estimate
`P(machine accepts | human rejects)`. [measured: bounded source search] That is Hermes's clearest
epistemic gap and Consilient's only plausible category-level advantage here. [asserted]

The pinned upstream was also exercised locally without a provider call. Six delegation-isolation
tests and 13 verify-on-stop tests passed (one skipped). [measured] Two focused current tests failed
reproducibly on Windows: the goal-gate test expected a POSIX-style failing command to reject but
`run_gate` returned pass; and the Kanban protocol-violation budget test blocked after the first
violation following a crash instead of preserving the independent retry budgets. [measured:
`tests/hermes_cli/test_goal_gates.py::test_run_gate_fail_captures_output` and
`tests/hermes_cli/test_kanban_core_functionality.py::test_protocol_violation_budget_not_consumed_by_other_failures`, rerun separately 22 Aug 2026]
The latter run also reported that linked SQLite 3.50.4 was vulnerable to the WAL-reset bug and used
DELETE journalling. [measured: test warning] These are snapshot/runtime findings, not an estimate of
Hermes-wide failure frequency. [asserted]

## Authority: safety controls are not authorship

Hermes checks dangerous commands and has an absolute hardline blocklist. In default `smart` mode an
auxiliary LLM auto-approves commands it calls low-risk, auto-denies dangerous ones and escalates
uncertain cases; `manual` always prompts for flagged commands and `off`/Yolo bypasses approval prompts
above the hardline floor. [`security.md:24-60,94-114`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/security.md#L24-L60)
[cited]

Kanban likewise defaults `review_dispatch: true`, spawning an assigned profile with a review skill;
operators may set it false for human-only review boards. [`kanban.md:224-232`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md#L224-L232)
[cited] Agents may complete work, request review and return reviewer change verdicts through board
tools. [`kanban.md:291-310`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md#L291-L310)
[cited]

Hermes also has a domain-specific spending boundary: billing state exposes monthly caps, restricts
actions to owner/admin/finance-admin roles, supports an organisation kill switch and remote-spending
revocation, and routes one-time consent through the portal.
[`billing-lifecycle.md:30-38,47-58,134-147`](https://github.com/NousResearch/hermes-agent/blob/261a4ef/docs/billing-lifecycle.md#L30-L38)
[cited] This is meaningful authority machinery for billing; it does not establish a general
first-party authorship type across publication, gates, consent and verdicts. [asserted]

Those are configurable execution and workflow policies. [asserted] A bounded search found no
systemic Hermes equivalent of the *intended* V0-18 rule: publication, spend, credentials, consent,
gate lifts and verdicts are invalid unless a first-party human authored them. [measured: bounded
source search] Saying the auxiliary model “approves on the user's behalf” would overstate identity:
the operator chose a policy that permits machine approval, but the machine does not become the human
author. [asserted]

Consilient does not yet enforce that intended boundary either. [measured] `events.validate()` checks
only that declared `actor == principal` and declared `via == "cli"`; `consil record --event` accepts
caller-supplied JSON. A payload self-declaring `actor="joe-brown"`, `principal="joe-brown"` and
`via="cli"` validated successfully as `FORGED_DECLARATION_ACCEPTED`. [measured: direct
`events.validate()` reproduction, 22 Aug 2026; `events.py:957-978`; `cli.py:178-185,987-991`] Seven
focused V0-18/work-item fixtures pass, but they establish declaration consistency, not authenticated
authorship. [measured] A trusted human ingress that supplies unforgeable provenance is therefore a
precondition for any authority comparison; current Consilient has a design intention, not a working
authority advantage. [asserted]

## Documented failures and release record

The following are project issue reports, not independently reproduced outcomes unless the local-test
column above says otherwise. [cited]

| Primary record, open when retrieved | Reported failure or gap |
|---|---|
| [#18421](https://github.com/NousResearch/hermes-agent/issues/18421) | A historical `/goal` false positive: the response claimed a file existed, the write had failed, and the judge declared completion. Current contracts/gates mitigate but do not calibrate that judge. [cited] |
| [#70806](https://github.com/NousResearch/hermes-agent/issues/70806) | Kanban completion is not bound to verification evidence; verified completion remains a feature request. [cited] |
| [#91040](https://github.com/NousResearch/hermes-agent/issues/91040) | A delegation incident report records 35 child sessions, 1,268 child calls, exhausted weekly allowance and unreliable stop behaviour. [cited] |
| [#92004](https://github.com/NousResearch/hermes-agent/issues/92004) | Delegation cost/usage views read the root session and reportedly undercounted real spend by about 2.3 times in the supplied case. [cited] |
| [#91996](https://github.com/NousResearch/hermes-agent/issues/91996) | Live delegation transcripts can resolve profile home after a thread hop and write under another profile. [cited] |
| [#87609](https://github.com/NousResearch/hermes-agent/issues/87609) | On Windows, the Kanban singleton lock is reported to fail open, creating double-dispatch and WAL-corruption risk; the issue does not establish that corruption occurred. [cited] |
| [#92219](https://github.com/NousResearch/hermes-agent/issues/92219) | External memory-provider write failures can be invisible and silently drop data. [cited] |

No top-level `CHANGELOG` or consolidated known-limitations file exists in the pinned tree. [measured:
recursive filename search] The latest [v2026.8.19 release](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.8.19)
describes a patch roll-up of roughly 323 merged pull requests and defers curated notes to v0.21.0;
the compare link and issue tracker are therefore needed to reconstruct current failures. [cited]

## Stress-test of the bar

| Axis | Hermes strength | Hermes bottleneck exposed by primary evidence |
|---|---|---|
| Computational | It already combines live tools, nested calls, durable peer work, resumable sessions and learned procedures. [cited] | Delegation can multiply cost, current usage views can omit descendants, and no outcome-per-cost comparison demonstrates that a swarm beats one capable owner. [cited] |
| Mechanical | SQLite claiming, dependency promotion, per-attempt history and crash reclamation are implemented. [cited] | It is single-host; delegates share workspaces by default; current Windows tests expose gate and retry-budget failures. [cited] [measured] |
| Cognitive | Context isolation and persistent skills reduce parent-context load and repeated instruction. [cited] | Final summaries are self-reports; model-curated memory/skill writes are ungated by default; automated review can compound the same model's assumptions. [cited] [asserted] |
| Epistemological | Hermes does run deterministic checks and narrow oracle-backed evaluations. [cited] | It does not report how often its own acceptance mechanisms accept outcomes an independent human rejects. [measured] |
| Authority | It has user-configurable prompts, deny rules and a non-overridable catastrophic-command floor. [cited] | Machine approval is a normal configured path, and no general first-party-authorship type was found for decisions reserved to a principal. [measured] [asserted] |

The cross-disciplinary mechanism worth importing is diagnostic-test calibration: treat every
automated acceptance as a fallible test, compare it with a separately sourced verdict, and retain the
full confusion table rather than calling a pass “correct”. [asserted] Pair that with separation of
duties at the event boundary: a model may propose a protected decision but cannot emit the human
event that makes it valid. [asserted] This is a narrower and more defensible differentiator than
building another Kanban, memory store or hierarchy. [asserted]

## Head-to-head criteria

Every causal criterion below uses the same frozen public-repository task or artefact in both arms, a
pinned Hermes revision, an exactly matched underlying model/provider, and blinded human presentation;
otherwise it is blocked rather than called a system comparison. [asserted: proposed protocol]

| Criterion | Task and measurement | Result that beats Hermes | Leader today |
|---|---|---|---|
| Reachable product | Submit, interrupt, resume and complete 20 versioned coding tasks through each product's normal operator surface; count accepted artefacts and terminal adverse outcomes. [asserted] | More human-accepted artefacts with no extra missing/refused/timeout denominator. [asserted] | **Hermes.** It has CLI, desktop and messaging surfaces; Consilient routing is disabled and has no chat surface. [measured] |
| Accepted task outcome | Eighty paired coding tasks across four frozen strata; joint success requires the external deterministic verifier and blinded human acceptance without edits. [asserted] | Consilient's paired success-rate advantage has a 95% interval lower bound above `0.05`. [asserted] | **Hermes operationally; comparative quality unknown.** [asserted] |
| Acceptance error | The same frozen human-labelled acceptance bank, containing at least 30 rejected and 30 accepted artefacts, is judged by predeclared terminal sinks; measure the full 2×2 and report seeded faults separately from natural rejections. [asserted] | An exact one-sided paired-binomial/McNemar test rejects equal beta at `p < 0.05` in Consilient's favour; abstentions and missing verdicts withhold confirmation. [asserted] | **Unknown.** Hermes publishes no calibration; Consilient has only 1/30 required human rejections. [measured] |
| Human authority | After trusted human ingress exists, use the EXP-103 inert manifests to measure false machine-authored protected transitions and false refusals. [asserted] | Zero protected false authorisations and a lower ordinary false-refusal rate; one protected breach loses. [asserted] | **Neither.** Hermes makes human-only review optional; Consilient currently trusts self-declared event identity. [measured] [cited] |
| Durable coordination | Kill a worker at each frozen claim/checkpoint boundary, restart, then count recovered accepted completions, duplicates and lost handoffs. [asserted] | Higher recovery with zero duplicate external effect and no lost evidence. [asserted] | **Hermes.** Its board/recovery product exists; Consilient has components but Gate B remains shut. [measured] [cited] |
| Learning without regression | Add one learned procedure from a training bank, then run unseen matched tasks and poisoned near-misses; measure accepted outcome gain and regressions. [asserted] | Positive held-out accepted-outcome interval, no authority leak, and regression upper bound no worse than Hermes. [asserted] | **Unknown.** Hermes persists skills; neither examined product has the required comparative measurement. [cited] [measured] |
| Extra cost | Per joint human-accepted task: reported tokens, provider-equivalent GBP, tool calls, wall time, summed worker-minutes and blinded operator/review-minutes; descendants and setup/calibration are captured separately, and missing usage is adverse. [asserted] | Quality passes and both provider GBP and human minutes per joint success are at most `1.25×` Hermes; zero successes cost infinity. The dimensions are not collapsed. [asserted] | **Hermes by availability; efficiency unknown.** Its own open issue reports incomplete descendant accounting. [cited] |

## The comparison and the mechanism

**Correction — 22 August 2026:** When this teardown was written, the comparison had been proposed as
**EXP-118** and the identifier had been collision-checked, but no entry existed in
`docs/10-research/experiment-register.md`. The earlier `[measured]` claim that it was pre-registered
was false. The authoritative register entry was added after the specification audit and before any
EXP-118 run or outcome inspection. [measured: register heading; `spec-audit-2026-08-22.md`, D1]

The identifier had been chosen only after exact, case-insensitive searches across tracked and
untracked `docs/`, `src/`, `tests/`, `scripts/`, `.github/`, live dispatch briefs/recall packs and
other dispatch outputs found no prior `EXP-118` or `exp118`; EXP-104 was already reserved and was
rejected. [measured: allocation search, 22 Aug 2026]

EXP-118 does not build a second orchestrator. [asserted] Its Consilient arm must reuse
`dispatch.py`, `coordination.py`, `recall.py`, `work_items.py`, `routing.py`, `budget.py`,
`instructions.py` and the single `events.py` writer. [asserted] Every added evidence role must bring a
named different class of facts—execution output, a retrieved primary source, an independent model
family or a first-party human verdict—or be cut as echo. [asserted]

The brief also conflates evidence-role count with candidate exposure. [algebra] [asserted] The current fusion
specification separates review capacity from `n_attempt_max`, assigns one accountable Owner and emits
one candidate through the verifier; more evidence readers do not buy another attempt.
[`2026-08-22-evidence-fusion.md:131-133,248-249`](../superpowers/specs/2026-08-22-evidence-fusion.md)
[measured] [algebra] EXP-118 therefore freezes exactly one submitted candidate and one verifier
exposure per arm. Its Consilient composition must first qualify through EXP-80, or through a disjoint
configuration bank applying EXP-80's comparator; otherwise EXP-118 is `blocked`. [asserted] This
experiment then decides only held-out joint success, acceptance error and resource cost for the two
frozen product compositions. [asserted] Its disjoint configuration, evaluation and human-labelled
acceptance banks are sealed before comparison. [asserted] Both arms require the exact same pinned
provider/model, evidence and capability permissions, plus componentwise token, tool and summed
worker-minute ceilings; a mismatch is `blocked`, not adjusted after outcomes. [asserted] Recovery,
procedure learning and the protected-authority campaign remain with EXP-98, EXP-101 and EXP-103
respectively. [measured] EXP-118 remains blocked until trusted human ingress makes protected
authorship more than a self-declared string check; after that, one protected breach kills the
treatment without becoming another sub-experiment. [asserted] Because there is no third single-Owner
Consilient arm, any win belongs to the frozen product bundle; EXP-118 alone cannot say swarming caused
it. [asserted]

Acceptance is not allowed to float among Hermes mechanisms. [asserted] Arm H freezes one terminal
sink: `/goal` reports `done` under a predeclared completion contract after every registered quality
gate passes, with `agent.verify_on_stop=true`, the exact judge model/configuration and the turn budget
sealed. [cited] Arm C freezes one composite `verification.outcome`; only `status="completed"` carries
its Boolean verdict. [measured] Gate/turn exhaustion without `done` is rejection; provider, tool,
schema or timeout failure is abstention. Passive evidence, verify-on-stop nudges, delegation summaries
and Kanban review are reported separately and never pooled into a more favourable native result.
[asserted] Calibration artefacts are read-only and bound to a frozen canonical digest; an arm that
mutates or repairs one is reported separately and cannot enter the original artefact's acceptance
2×2. [asserted]

The analysis resamples the paired task, not each arm separately: 20,000 within-stratum paired
bootstrap resamples with seed `1180061` produce the two-sided joint-success interval. [asserted]
Safety uses the exact one-sided paired-binomial/McNemar test over discordant native acceptances on the
human-rejected bank; a zero-discordance sample is inconclusive. [asserted] Bootstrap safety intervals
are descriptive only: at the 30-rejection floor, three discordances can yield a falsely decisive
percentile bound. [measured: protocol falsifier, 22 Aug 2026] The outcome-blind sensitivity artefact
must be sealed before either evaluation bank is opened. [asserted]

**It cannot run today.** [measured] `consil doctor` at the snapshot reports Gate A FAIL, Gate B FAIL
and `routing/orchestration enabled: no`; `consil beta` reports one human rejection against the minimum
30. [measured: commands run 22 Aug 2026] There is no authorised routable Consilient squad to put in
the treatment arm. [measured] The claimed advantage is therefore **presently unfalsifiable**, even
though EXP-118 specifies the artefacts that can make it falsifiable later. [asserted] Registration
changes no gate, routing flag, CLI surface or product code. [measured]

The greater-than-five-point claim is confirmed only when the paired 95% lower bound exceeds `+0.05`,
falsified when the upper bound is at most `+0.05`, and otherwise remains inconclusive. [asserted]
The proposal also loses if either provider-equivalent GBP or human minutes per joint success exceeds
`1.25×` Hermes; zero successes make that arm's per-success cost infinite. [asserted] One
protected-authority breach or deliberate suppression of an outcome or usage record kills the
treatment immediately. [asserted] Fewer than 30 blinded human rejections per arm makes the
acceptance-error comparison `insufficient_safety_evidence`; it is not a favourable zero and not
itself a kill. [asserted] Likely failure modes are that extra roles repeat the same facts, Hermes's
broader product surface dominates, Consilient buys quality with extra budget, human review becomes
the bottleneck, or the two systems cannot share an exact model/runtime and the comparison is blocked.
[asserted]

## Plain answer and delta

The plain answer has two parts. **Hermes is stronger today: true.** [asserted] It already has the
hierarchy and cross-agent task management the brief treated as possible gaps, plus a much broader
working surface. [cited] **The prospective claim that a few swarms can beat it easily: unknowable.**
[asserted: no deciding experiment] EXP-118 can compare two frozen product bundles, but without a
Consilient single-Owner arm or an engineering-effort ceiling it cannot attribute a win to swarming or
call the work easy. [measured: registered scope] [asserted]

Consilient's plausible advantage is narrower: externally calibrated acceptance error and
evidence-class admission. [asserted] Authenticated nondelegable human authority is still a design
target, not a present differentiator, and none is yet a measured head-to-head win. [measured] The
teardown changes the next move from “build a few swarms” to “earn the second agent, then run
EXP-118”. [asserted] A result satisfying the fixed quality, beta, authority and cost thresholds would
beat Hermes for the frozen task mixture; anything less leaves Hermes as the bar. [asserted]

**Correction:** at the 2026-08-22 16:53 UTC valid-event snapshot, the trajectory contained 46 outcomes whose status was `timeout`, not 27; it contained four enumerated zero-byte Grok outcomes on 22 August, not five; Grok remained registered, not removed; and the observed reliability decline does not identify arm count as its cause. [measured]

# Hermes Agent as a dispatch arm: neither arm nor adopted component

## Decision

**Do not add Hermes as a fifth dispatch arm and do not adopt one of its components now.** Its CLI mechanically fits the subprocess boundary, but under the available subscription paths it supplies no new model family, evidence class, independently measured quota pool or verified authorised task capability that the current arms lack. Its useful board claim protocol is prior art for a native Consilient fix, not a reason to import a second orchestrator. [measured] [asserted]

No ADR is warranted; ADR-0088 was free when checked and remains unused. [measured]

This decision is revision-bounded to Consilient at the current worktree and Hermes Agent revision `261a4efb90d7` (version 0.20.5). Hermes was inspected from source only: it was not installed, configured, run or authenticated. [measured]

## Method and corrected failure census

The census used `consilient.events.read_all(Path(".harness/log"))`, counted only accepted `dispatch.outcome` events, and froze the result at 16:53 UTC. It found 120 outcomes and six quarantined log lines. [measured]

| Status | Count |
|---|---:|
| `ok` | 46 [measured] |
| `timeout` | 46 [measured] |
| `refused` | 20 [measured] |
| `killed` | 4 [measured] |
| `silent` | 3 [measured] |
| `failed` | 1 [measured] |

There were 47 events with `timed_out=true`: one event was classified `silent` while also carrying that boolean. The count of 27 status-timeouts is correct only for the 21 August log; 22 August added 19 before this snapshot. [measured]

The four valid Grok outcomes on 22 August were two zero-byte timeouts and two zero-byte operator kills. Two kill records each contain the operator-authored reason “Fifth zero-byte grok result today”, but the accepted event sequence contains no fifth Grok outcome that day; the reason is an assertion, not an enumerated count. [measured]

Grok was rerouted away after repeated failures, but it remains registered in [`harness.py`](../../src/consilient/harness.py#L117-L127) and probed by [`dispatch.py`](../../scripts/dispatch.py#L434-L435). A tracked earlier summary of the same trajectory records 29 Grok outcomes in total — five `ok`, 19 `timeout`, three `refused`, two `killed` — with its latest success on 21 August. [measured] ([source](subscription-reach-2026-08-22.md#L93-L102))

## The CLI contract: mechanically yes

Hermes exposes the console entry point `hermes = hermes_cli.main:main`. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/pyproject.toml#L372-L375))

The candidate non-interactive surface is `hermes chat --query-file BRIEF -Q --in CWD --provider PROVIDER --model MODEL --toolsets TOOLSETS --max-turns N --run-budget SECONDS`. `--query-file` preserves arbitrary text without shell interpretation; `-Q` suppresses presentation output; `--in` selects the directory. [measured] ([query flags](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L298-L315), [other flags](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L378-L474))

`--max-turns` and `--run-budget` are not hard bounds on the Codex app-server path: Hermes enters that path before its normal iteration loop and the app-server session receives neither value. In the normal loop, `--run-budget` gives an 80% wrap-up notice and caps implicit stale-call timeouts; it does not itself terminate the run at 100%. [measured] ([budget behaviour](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/conversation_loop.py#L121-L165), [app-server branch](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/conversation_loop.py#L1950-L1957), [session construction](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/codex_runtime.py#L742-L750))

The enforceable wall-clock contract would therefore come from Consilient's existing parent timeout and process-tree kill, not from those Hermes flags. [measured] ([dispatch enforcement](../../scripts/dispatch_workspace.py#L133-L163))

Provider, model and toolset flags are available on the same `chat` subcommand. They are invocation inputs, not proof of the provider, model or bill that actually handled every main and auxiliary call. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L320-L370))

Do not use the superficially cleaner `-z/--oneshot` integration. That mode explicitly auto-bypasses approvals; it is also the only mode exposing the structured `--usage-file`, so the safer `chat -q` route lacks equivalent spend evidence. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L101-L125))

Hermes' general approval default is `smart`, in which an auxiliary model can approve commands it judges low-risk. Its distinct non-interactive `single_query_mode` default is deterministic `deny`, which is safer, but it remains user-configurable and does not confine the host process. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/config_defaults.py#L2319-L2347))

Therefore Hermes passes only the mechanical non-interactive-entry test. `dispatch.py` could launch it, impose its own parent wall-clock bound, claim paths and record an outcome without a new `consil` subcommand. That is necessary and insufficient for admission. [measured] [asserted]

## What a fifth arm would add: no independent induction

Consilient's arm identity is static: each `Harness` has one `family` and one subscription `pool`, while fan-out treats `family:<family>` as the evidence class. [measured] ([registry](../../src/consilient/harness.py#L68-L76), [fan-out](../../src/consilient/harness_models.py#L196-L210), [recorded evidence class](../../src/consilient/harness_selection.py#L297-L375))

Hermes selects its effective provider and model dynamically. Registering it as `family="hermes"` would therefore turn a wrapper name into a false independence claim. Binding it to Codex, Claude or xAI authentication would consume an existing family and pool; it would add neither exogenous evidence nor separately measured headroom. [measured] [asserted] ([provider resolution](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/runtime_provider.py#L618-L634))

The Codex app-server path is opt-in and uses the user's ChatGPT subscription and Codex sandbox. In that mode Hermes becomes a shell around Codex, and `delegate_task`, Hermes memory, session search and Hermes todo are unavailable; the purportedly differentiating inner delegation is absent from the turn runtime. [cited] ([revision-pinned Hermes documentation](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L8-L22), [unavailable tools](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L71-L78))

The app-server transport starts Codex threads and turns without carrying Hermes' selected provider or model in those requests. On static evidence, `--provider` and `--model` therefore do not guarantee the effective Codex app-server model; that would need a runtime identity assertion before admission. [measured] ([session construction](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/transports/codex_app_server_session.py#L274-L346), [turn start](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/transports/codex_app_server_session.py#L519-L527))

If a future Hermes-supported provider genuinely supplies a new family or quota pool, Consilient should admit that provider through the existing adapter contract and name the underlying family and pool directly. Nesting it under a Hermes family would make provenance worse. [asserted]

## Cost, provider and account

There is no single truthful answer to “what would Hermes spend” without a sealed invocation profile and post-run provider evidence. An unpinned provider can resolve through user configuration or environment credentials, while auxiliary tasks and fallback configuration may use routes different from the main turn. [measured] ([provider resolution](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/runtime_provider.py#L618-L634), [auxiliary fallback order](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/configuring-models.md#L70-L92))

With the opt-in Codex app-server runtime and `openai-codex`, main turns use the host user's existing Codex CLI/ChatGPT authentication rather than an API key. Hermes documents that auxiliary title generation, compression, vision and self-improvement also use that subscription by default, but per-task overrides may redirect them to OpenRouter or another provider. [cited] ([revision-pinned Hermes documentation](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L262-L286))

That route spends the same Codex subscription pool as the existing Codex arm. Hermes classifies `openai-codex` as subscription-included and returns zero estimated US-dollar cost for that class, but zero in Hermes' estimate is not proof of zero marginal liability: optional Codex flexible credits may follow included allowance. [measured] [cited] ([route classification](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/usage_pricing.py#L1070-L1073), [zero estimate](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/usage_pricing.py#L1433-L1443), [project source record](../10-research/bibliography.md#L177))

ADR-0044's subscription-first rule remains binding after ADR-0064; an unknown, redirected or unaccounted metered route is a refusal, not a fallback. [cited] ([ADR-0044](../decisions/0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md#L25-L47), [ADR-0064](../decisions/0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md#L93-L96))

## Safety asymmetry and required enforcement

Hermes' ordinary terminal backend executes locally as the OS user; changing its working directory is not a filesystem boundary. Its Codex runtime improves write isolation, but defaults to `:workspace` and can expose native Codex plugins plus Hermes MCP callbacks with browser, search, image and speech effects. [cited] ([terminal source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/tools/terminal_tool.py#L10-L12), [Codex permissions](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L247-L260), [callback surface](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L364-L381))

Hermes does not supply a V0-18-equivalent default. Its board auto-dispatches reviewer agents by default and permits a reviewer to approve a review task into `done`; a human-only board is an optional configuration. [measured] ([review dispatch](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/kanban_db.py#L10299-L10311), [review completion](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/kanban_db.py#L5363-L5369))

V0-18 states that a human approval, consent, gate lift, spend authorisation or verdict is valid only when the principal authored it. [asserted] ([V0-18](../40-spec/v0-draft.md#L419-L419))

Current Consilient enforcement validates only caller-declared actor, principal and channel fields and expressly records the absence of a signature verifier. The intended rule and present enforcement are not equivalent. [measured] ([event ingress](../../src/consilient/events_durability.py#L122-L133))

A future Hermes arm would be forbidden to publish, push, send, approve, lift a gate, author a verdict, incur metered spend, access any unclaimed or non-allowlisted root, read host credentials, accept another agent's work, or persist a learned skill or memory as trusted policy. Agents could only propose those effects for separately authenticated principal action. [asserted]

Those prohibitions would require code, not a dispatch prompt: [asserted]

1. derive and record the actual provider, model, runtime and billing pool; never record `hermes` as an evidence family; [asserted]
2. reject `auto`, fallbacks, auxiliary-provider drift, identity mismatch, unknown headroom and every unapproved credential discovered in the environment; [asserted]
3. use `chat --query-file` with deterministic denial; ban `--oneshot`, `--yolo`, `--accept-hooks`, goals, cron, delegation and review automation; [measured] [asserted]
4. run under an OS-enforced profile whose only writable roots are the claimed paths, whose private sibling roots and host credential stores are unreadable, and whose network is disabled unless an exact capability authorises it; [asserted]
5. authenticate human ingress for every V0-18 action, with an agent proposal structurally unable to populate the principal-authored field; [asserted]
6. make the invocation profile immutable and digest-recorded, scrub the inherited environment, and verify the artefact, provider identity and spend record after termination; [asserted]
7. add refusal tests for provider drift, metered or flexible-credit use, private-root access, unclaimed writes, external effects, empty success, timeout descendants and missing attribution. [asserted]

Implementing those controls would reduce Hermes to a more complicated wrapper around an existing provider. Until a measured capability survives that reduction, the safety work has no compensating induction. [asserted]

## Component adoption: also no

Hermes' supported Kanban claim path is stronger than the unlocked read-modify-write defect found in Ruflo: it enables SQLite WAL mode, enters `BEGIN IMMEDIATE`, and uses a conditional `UPDATE` with `rowcount == 1` so only one claimant wins; the run and event are created in the same write transaction. No unlocked claim read-modify-write was found in that path. [measured] ([transaction](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/kanban_db.py#L61-L68), [claim protocol](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/kanban_db.py#L4617-L4727))

Consilient's current claim opening is weaker: `dispatch.py` checks for a conflict and later appends the claim as separate operations, while the append writer has no cross-process lock. [measured] ([check](../../scripts/dispatch_launch.py#L274-L361), [later open](../../scripts/dispatch_preflight.py#L219-L298), [append](../../src/consilient/events_fields.py#L148-L158))

Two dispatchers can therefore both observe no conflict and open overlapping claims. This race follows from the static interleaving; it was not reproduced in this review. [asserted]

That is a defect to fix once in Consilient's native coordination path, using an atomic lock/CAS around conflict-check plus append. ADR-0065 places coordination, trajectory, budget and routing in the native judgement tier, so importing Hermes' mutable SQLite board would duplicate authority and create a second task substrate. [measured] [cited] ([ADR-0065](../decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md#L38-L56))

The Kanban schema is useful prior art, but its goals, comments, hand-offs, review, attachments and mutable state are not missing evidence classes. The skill-learning format likewise resembles this repository's existing `SKILL.md` convention, while persistent promotion remains owner-gated. Neither component clears the adoption bar. [measured]

Hermes' Codex callback does expose browser automation, search, vision, image generation and speech, while Consilient has no demonstrated task-scoped connector pass-through today. That is a potential capability-tier addition, not a new evidence class. [cited] [measured] ([Hermes callback](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L58-L69), [current Consilient gap](subscription-reach-2026-08-22.md#L118-L126))

Do not adopt that callback bridge now: it routes Codex back through Hermes' configured tools, providers and credentials, and this review established no task-scoped admission, isolated credential set, exact spend path or named unmet task for it. Evaluate each underlying connector or MCP server directly under ADR-0065 when a concrete task needs it; importing the Hermes bridge wholesale would import the unsealed runtime this decision rejects. [measured] [asserted]

For this bounded decision, Hermes' atomic claim is the directly inspected comparator bar that Consilient's native claim path does not yet meet; no claim that it is the market's best board is made. The smallest better result is to repair that one native invariant without importing Hermes' orchestration surface. [measured] [asserted]

## Evidence against a fifth arm

The first 35 valid outcomes contained 24 successes (68.6%); the first 84 contained 36 (42.9%); the 120-outcome snapshot contained 46 (38.3%). This sequence measures deteriorating realised reliability, not that adding arms caused it; workload, harness mix, quota and time are confounded. [measured]

EXP-16 provides the narrower adverse result: model graders preferred the single-agent artefact in 9 of 12 comparisons and the Owner-meeting artefact in 2 of 12, while the meeting used 4.8 times the tokens and 3.7 times the wall time. Its publication audit notes unmatched budgets, six tasks, one replication and no decision-level significance, so the honest conclusion is only that this costlier group arm did not beat the single arm in that experiment. [measured] ([grading result](../10-research/experiments/exp16/grading-result-2026-08-20.md#L9-L75), [limits](../50-publications/P3-echo.md#L871-L888))

The current trajectory is already dominated by adverse outcomes: 46 timeouts, 20 refusals, four kills, three silences and one failure against 46 successes at the snapshot. Adding a wrapper with no new family or pool increases integration, probing and failure surface without increasing consilience. [measured] [asserted]

The provenance objection is stronger than the reliability objection. A dynamically routed harness that cannot prove the underlying model, account and auxiliary calls would make same-family work look independent; a safety model that permits agent-approved or host-user effects would weaken V0-18 at the boundary where authorship matters. In a system whose test depends on different classes and attributable evidence, that is a correctness defect. [measured] [asserted]

`python -m consilient.cli doctor --json` exited 1 in this worktree: Gate B conditions B1 and B3 passed, B2 and B4 failed, and `routing_orchestration_enabled` was `false`. This report changes no gate and authorises no external repository. [measured]

## Reversal condition and late-registered test

Reverse this decision only after the safety and attribution rules above exist and a fixed, blinded comparison shows that Hermes either completes a class of authorised work the direct underlying arm cannot, or supplies a separately measured family or quota pool, without worse adverse-outcome rate, wall time, verified quality or marginal spend. [asserted]

EXP-118 is the existing killing experiment: 80 paired tasks compare frozen Hermes and Consilient compositions under matched provider/model, permissions and componentwise ceilings, with blinded verdicts and adverse treatment of missing usage or runtime mismatch. It is explicitly recorded as a **late registration**, added before any EXP-118 run or outcome inspection; it is not a pre-registration. This dispatch neither wrote nor modified that entry. [measured] ([EXP-118](../10-research/experiment-register.md#L4975-L5005))

## Search and limits

The review traced the live Consilient registry, dispatch, coordination, event and gate paths; the local trajectory; tracked EXP-16 evidence; and the pinned Hermes entry point, parser, approval defaults, Codex runtime, usage classification and Kanban transaction. A bounded search of the project bibliography found no Hermes entry, so Hermes claims link to the revision-pinned primary source; its licence file grants the MIT terms. [measured] ([licence](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/LICENSE#L1-L20))

The aggregate census was reproduced at the stated cutoff, but no separate frozen-input digest or generated result artefact was created; the raw source remains the local trajectory. [measured]

Two different-family, read-only Claude audit attempts returned no artefact and were stopped; the completed adversarial audit was single-family and its decision-bearing findings were then checked against source. This is not a full independent audit. [measured]

No live Hermes behaviour, billing, Windows isolation or recovery claim was tested. Source inspection can reject admission gaps; it cannot establish that a future sealed integration works. [measured]

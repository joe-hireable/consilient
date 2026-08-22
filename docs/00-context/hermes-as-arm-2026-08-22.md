**Correction:** at the 2026-08-22 16:53 UTC valid-event snapshot, the trajectory contained 46 outcomes whose status was `timeout`, not 27; it contained four enumerated zero-byte Grok outcomes on 22 August, not five; Grok remained registered, not removed; and the observed reliability decline does not identify arm count as its cause. [measured]

# Hermes Agent as a dispatch arm: neither arm nor adopted component

## Decision

**Do not add Hermes as a fifth dispatch arm and do not adopt one of its components now.** Its CLI mechanically fits the subprocess boundary, but under the available subscription paths it supplies no new model family, evidence class, capability or independent quota pool. Its useful board claim protocol is prior art for a native Consilient fix, not a reason to import a second orchestrator. [measured]

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

Grok was rerouted away after repeated failures, but it remains registered in [`harness.py`](../../src/consilient/harness.py#L117-L127) and probed by [`dispatch.py`](../../scripts/dispatch.py#L434-L435). The tracked subscription census independently records 29 Grok outcomes in total — five `ok`, 19 `timeout`, three `refused`, two `killed` — with its latest success on 21 August. [measured] ([source](subscription-reach-2026-08-22.md#L93-L102))

## The CLI contract: mechanically yes

Hermes exposes the console entry point `hermes = hermes_cli.main:main`. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/pyproject.toml#L372-L375))

The safe candidate surface is `hermes chat --query-file BRIEF -Q --in CWD --provider PROVIDER --model MODEL --toolsets TOOLSETS --max-turns N --run-budget SECONDS`. `--query-file` is non-interactive and preserves arbitrary text without shell interpretation; `-Q` suppresses presentation output; `--in`, `--max-turns` and `--run-budget` provide the directory and native bounds. [measured] ([query flags](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L298-L315), [bounds](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L378-L474))

Provider, model and toolset flags are available on the same `chat` subcommand. They are invocation inputs, not proof of the provider, model or bill that actually handled every main and auxiliary call. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L320-L370))

Do not use the superficially cleaner `-z/--oneshot` integration. That mode explicitly auto-bypasses approvals; it is also the only mode exposing the structured `--usage-file`, so the safer `chat -q` route lacks equivalent spend evidence. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/_parser.py#L101-L125))

Hermes' general approval default is `smart`, in which an auxiliary model can approve commands it judges low-risk. Its distinct non-interactive `single_query_mode` default is deterministic `deny`, which is safer, but it remains user-configurable and does not confine the host process. [measured] ([revision-pinned source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/hermes_cli/config_defaults.py#L2319-L2347))

Therefore Hermes passes only the mechanical CLI test. `dispatch.py` could launch it, impose a parent wall-clock timeout, claim paths and record an outcome without a new `consil` subcommand. That is necessary and insufficient for admission. [measured]

## What a fifth arm would add: no independent induction

Consilient's arm identity is static: each `Harness` has one `family` and one subscription `pool`, while fan-out treats `family:<family>` as the evidence class. [measured] ([registry](../../src/consilient/harness.py#L68-L76), [fan-out](../../src/consilient/harness.py#L662-L740))

Hermes selects its effective provider and model dynamically. Registering it as `family="hermes"` would therefore turn a wrapper name into a false independence claim. Binding it to Codex, Claude or xAI authentication would consume an existing family and pool; it would add neither exogenous evidence nor headroom. [measured]

The Codex app-server path is opt-in and uses the user's ChatGPT subscription and Codex sandbox. In that mode Hermes becomes a shell around Codex, and `delegate_task`, Hermes memory, session search and Hermes todo are unavailable; the purportedly differentiating inner delegation is absent from the turn runtime. [cited] ([revision-pinned Hermes documentation](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L8-L22), [unavailable tools](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L71-L78))

The app-server transport starts Codex threads and turns without carrying Hermes' selected provider or model in those requests. On static evidence, `--provider` and `--model` therefore do not guarantee the effective Codex app-server model; that would need a runtime identity assertion before admission. [measured] ([session construction](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/transports/codex_app_server_session.py#L274-L346), [turn start](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/transports/codex_app_server_session.py#L519-L527))

If a future Hermes-supported provider genuinely supplies a new family or quota pool, Consilient should admit that provider through the existing adapter contract and name the underlying family and pool directly. Nesting it under a Hermes family would make provenance worse. [asserted]

## Cost, provider and account

There is no single truthful answer to “what would Hermes spend” without a sealed invocation profile and post-run provider evidence. An unpinned provider can resolve through user configuration or environment credentials, while auxiliary tasks and fallback configuration may use routes different from the main turn. [measured]

With the opt-in Codex app-server runtime and `openai-codex`, main turns use the host user's existing Codex CLI/ChatGPT authentication rather than an API key. Hermes documents that auxiliary title generation, compression, vision and self-improvement also use that subscription by default, but per-task overrides may redirect them to OpenRouter or another provider. [cited] ([revision-pinned Hermes documentation](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L262-L286))

That route spends the same Codex subscription pool as the existing Codex arm. Hermes records `openai-codex` as subscription-included and zero estimated US-dollar cost, but zero in Hermes' estimate is not proof of zero marginal liability: optional Codex flexible credits may follow included allowance. [measured] [cited] ([Hermes classification](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/agent/usage_pricing.py#L1048-L1062), [project source record](../10-research/bibliography.md#L177))

ADR-0044's subscription-first rule remains binding after ADR-0064; an unknown, redirected or unaccounted metered route is a refusal, not a fallback. [cited] ([ADR-0044](../decisions/0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md#L25-L47), [ADR-0064](../decisions/0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md#L93-L96))

## Safety asymmetry and required enforcement

Hermes' ordinary terminal backend executes locally as the OS user; changing its working directory is not a filesystem boundary. Its Codex runtime improves write isolation, but defaults to `:workspace` and can expose native Codex plugins plus Hermes MCP callbacks with browser, search, image and speech effects. [cited] ([terminal source](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/tools/terminal_tool.py#L10-L12), [Codex permissions](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L247-L260), [callback surface](https://github.com/NousResearch/hermes-agent/blob/261a4efb90d7/website/docs/user-guide/features/codex-app-server-runtime.md#L364-L381))

Consilient's V0-18 reserves verdicts, approvals, gate lifts and spend to authenticated human ingress, but the current event writer accepts caller-declared actor and principal fields without a cryptographic human-authorship check. The intended rule and present enforcement are not equivalent. [measured] ([V0-18](../40-spec/v0-draft.md#L419-L419), [event ingress](../../src/consilient/events.py#L890-L978))

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

Consilient's current claim opening is weaker: `dispatch.py` checks for a conflict and later appends the claim as separate operations, while the append writer has no cross-process lock. Two dispatchers can therefore both observe no conflict and open overlapping claims. [measured] ([check](../../scripts/dispatch.py#L1423-L1445), [later open](../../scripts/dispatch.py#L1579-L1601), [append](../../src/consilient/events.py#L1031-L1058))

That is a defect to fix once in Consilient's native coordination path, using an atomic lock/CAS around conflict-check plus append. ADR-0065 places coordination, trajectory, budget and routing in the native judgement tier, so importing Hermes' mutable SQLite board would duplicate authority and create a second task substrate. [measured] [cited] ([ADR-0065](../decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md#L38-L56))

The Kanban schema is useful prior art, but its goals, comments, hand-offs, review, attachments and mutable state are not missing evidence classes. The skill-learning format likewise resembles this repository's existing `SKILL.md` convention, while persistent promotion remains owner-gated. Neither component clears the adoption bar. [measured]

Hermes itself is the relevant open-source incumbent for a durable agent board and nested workflow, and its atomic claim is the concrete bar Consilient's native claim path does not yet meet. The smallest better result is to repair that one native invariant without importing Hermes' orchestration surface. [measured] [asserted]

## Evidence against a fifth arm

The first 35 valid outcomes contained 24 successes (68.6%); the first 84 contained 36 (42.9%); the 120-outcome snapshot contained 46 (38.3%). This sequence measures deteriorating realised reliability, not that adding arms caused it; workload, harness mix, quota and time are confounded. [measured]

EXP-16 provides the narrower adverse result: model graders preferred the single-agent artefact in 9 of 12 comparisons and the Owner-meeting artefact in 2 of 12, while the meeting used 4.8 times the tokens and 3.7 times the wall time. Its publication audit notes unmatched budgets, six tasks, one replication and no decision-level significance, so the honest conclusion is only that this costlier group arm did not beat the single arm in that experiment. [measured] ([grading result](../10-research/experiments/exp16/grading-result-2026-08-20.md#L9-L75), [limits](../50-publications/P3-echo.md#L871-L888))

The current trajectory is already dominated by adverse outcomes: 46 timeouts, 20 refusals, four kills, three silences and one failure against 46 successes at the snapshot. Adding a wrapper with no new family or pool increases integration, probing and failure surface without increasing consilience. [measured] [asserted]

The provenance objection is stronger than the reliability objection. A dynamically routed harness that cannot prove the underlying model, account and auxiliary calls would make same-family work look independent; a safety model that permits agent-approved or host-user effects would weaken V0-18 at the boundary where authorship matters. In a system whose test depends on different classes and attributable evidence, that is a correctness defect. [measured] [asserted]

`python -m consilient.cli doctor --json` exited 1 in this worktree: Gate B conditions B1 and B3 passed, B2 and B4 failed, and `routing_orchestration_enabled` was `false`. This report changes no gate and authorises no external repository. [measured]

## Reversal condition and unwritten test

Reverse this decision only after the safety and attribution rules above exist and a fixed, blinded comparison shows that Hermes either completes a class of authorised work the direct underlying arm cannot, or supplies a separately measured family or quota pool, without worse adverse-outcome rate, wall time, verified quality or marginal spend. [asserted]

The proposed comparison would use the same tasks, underlying provider, model, reasoning, tools, context and subscription state for direct and Hermes-wrapped arms; it would stop on any provider/model mismatch, unaccounted auxiliary call, metered or flexible-credit debit, protected-root access, external effect, empty success or escaped descendant. It is stated here only: no experiment-register entry or pre-registration was written. [asserted]

## Search and limits

The review traced the live Consilient registry, dispatch, coordination, event and gate paths; the local trajectory; tracked EXP-16 evidence; and the pinned Hermes entry point, parser, approval defaults, Codex runtime, usage classification and Kanban transaction. A bounded search of the project bibliography found no Hermes entry, so Hermes claims link to the pinned MIT-licensed primary source rather than an uncited secondary description. [measured]

No live Hermes behaviour, billing, Windows isolation or recovery claim was tested. Source inspection can reject admission gaps; it cannot establish that a future sealed integration works. [measured]

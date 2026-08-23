# Capability atlas: product claims and current instance probes

**Correction — [cited] this atlas can establish what PRODUCT documentation claims and [measured] what zero-cost INSTANCE probes expose, not that every advertised capability is usable here; [algebra] the robust candidate ceiling is `n_attempt_max = floor(epsilon / beta_upper)` when candidate badness is unknown, not the brief's iid logarithmic formula; and [asserted] a different model family alone does not establish a different class of facts.**

Date: 2026-08-23

Status: survey and specification; no routing authority

Extends: [harness-capabilities.md](harness-capabilities.md), [ADR-0027](../decisions/0027-compose-domain-harness-provider-and-model.md), [ADR-0042](../decisions/0042-admit-connectors-by-capability-probing-credential-isolation-and-fail-closed-boundaries.md), [ADR-0054](../decisions/0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md), [ADR-0067](../decisions/0067-front-one-chat-with-one-owner-evidence-squads.md), [ADR-0082](../decisions/0082-project-raci-onto-per-work-item-rights-and-require-structural-consultation.md), [ADR-0084](../decisions/0084-compile-portable-capabilities-per-harness-and-refuse-semantic-loss.md), and [ADR-0088](../decisions/0088-make-zero-cost-a-native-fail-closed-routing-ladder.md)

## Direct answer

[asserted] Keep a small, shipped PRODUCT taxonomy, but never route from it. Generate a secret-free INSTANCE observation for the exact harness/provider/model/surface composition at dispatch time, then join it to ADR-0054's measured capability row and verifier contract. A stale, unprobed or merely vendor-claimed positive is unavailable.

[measured] The present worktree already has the right pieces but not the closed loop: `capabilities.py` validates and selects `kind`/`name` requests, `dispatch.py` appends the selection as JSON to the task, `instructions.py` assembles the resulting brief, and `routing.py` holds the robust beta ceiling while explicitly remaining unwired. [measured] The selection currently proves neither native binding nor a served tool surface, and `dispatch.py` invokes CLIs rather than their SDK, ACP or app-server control surfaces.

[asserted] No new ADR is warranted. The PRODUCT/INSTANCE boundary is ADR-0054, portable compilation is ADR-0084, one Owner and RACI are ADR-0067/ADR-0082, and pool admission is ADR-0088. This document proposes a reversible schema and cache layout but commits no event schema, gate change, CLI command or source path; an implementation that changes an append-only event contract must be checked against those ADRs then.

[asserted] Adapter priority is SDK or native control protocol, then structured headless CLI, then API, then an attended app. Browser tools follow structured tools; raw mouse-and-screen computer use is last because it adds visual ambiguity, timing sensitivity, prompt-injection exposure and human hand-backs.

## Evidence boundary and vocabulary

[measured] PRODUCT rows below were checked against first-party vendor documentation retrieved on 2026-08-23. [measured] INSTANCE rows came from version/help, executable-presence, package-presence and configuration-key-name probes; no model prompt, account creation, credential read, secret value, paid API request or private commercial repository was used.

[asserted] The atlas uses these reach codes:

| Code | Meaning |
|---|---|
| `SDK` | [asserted] A supported software library or bidirectional control protocol can invoke it. |
| `CLI` | [asserted] A supported non-interactive command can invoke it. |
| `API` | [asserted] A supported HTTP or comparable interface can invoke it. |
| `APP` | [asserted] A person can invoke it in a first-party application, but no general scripted entry was established. |
| `CU` | [asserted] Reach requires browser or computer actuation rather than a structured operation. |
| `?` | [asserted] The reviewed primary sources did not establish reach; this is unknown, not absent. |

[asserted] Pool labels are ADR-0088's `Z0_LOCAL`, `Z1_FREE_KEY`, `S_SUBSCRIPTION` and `M_METERED`. PRODUCT documentation can describe payment paths; only an INSTANCE probe can classify the selected path. A subscription surface with possible credits, overage or on-demand billing is `M_METERED` unless the probe proves that debit path disabled and proves current headroom.

## PRODUCT: invocation and script reach

[cited] “ChatGPT Work / Codex” and “Grok CLI / Grok Bot” are not single products: each pair shares a vendor but exposes different invocation, state and security boundaries ([Work](https://learn.chatgpt.com/docs/get-started-with-work), [Codex CLI](https://learn.chatgpt.com/docs/codex/cli), [Grok Build](https://docs.x.ai/build/overview), [Grok Bot](https://docs.x.ai/grok-bot/overview), accessed 2026-08-23).

| Product surface | Script-reachable entry | Human or computer-use boundary | Preferred Consilient entry |
|---|---|---|---|
| Claude Code | [cited] `CLI`: `claude -p` supports stdin, sessions and machine-readable output; `SDK`: the Python and TypeScript Agent SDK controls agent loops; cloud routines add scheduled, GitHub and HTTP triggers ([headless](https://code.claude.com/docs/en/headless), [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview), [routines](https://code.claude.com/docs/en/routines), accessed 2026-08-23). | [cited] `APP` desktop, web, IDE and mobile surfaces exist; Chrome and computer-use paths can cross into attended browser or desktop control ([platforms](https://code.claude.com/docs/en/platforms), [Chrome](https://code.claude.com/docs/en/chrome), [computer use](https://code.claude.com/docs/en/computer-use), accessed 2026-08-23). | [asserted] Agent SDK first; structured `-p` when a process boundary is preferable. |
| Claude Cowork | [cited] `APP` web, desktop, mobile and Chrome are documented; Dispatch and saved schedules launch cloud work ([surfaces](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile), [Dispatch](https://support.claude.com/en/articles/13947068-assign-tasks-from-anywhere-in-claude-cowork), [schedules](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork), accessed 2026-08-23). | [asserted] No general Cowork CLI, SDK, JSON-schema result API or arbitrary-conversation API was found in the reviewed first-party Cowork navigation; browser/computer operation is `CU`. | [asserted] No unattended adapter; use an explicit human hand-off until a supported control surface is published and probed. |
| ChatGPT Work | [cited] `APP` hosted Work runs in ChatGPT and desktop Work can use local files, apps and browser; hosted work can continue with the local machine off ([Work](https://learn.chatgpt.com/docs/get-started-with-work), [desktop app](https://learn.chatgpt.com/docs/app), accessed 2026-08-23). [cited] `API` can trigger an already-published Workspace Agent, but that contract does not expose arbitrary Work conversations ([Workspace Agents API](https://learn.chatgpt.com/workspace-agents/trigger-runs), accessed 2026-08-23). | [cited] Local browser and computer use are `CU`; scheduled-task management is web/desktop rather than CLI or IDE ([computer use](https://learn.chatgpt.com/docs/computer-use), [automations](https://learn.chatgpt.com/docs/automations), accessed 2026-08-23). | [asserted] Published Workspace Agent API only when its fixed agent is the required composition; otherwise attended Work. |
| OpenAI Codex | [cited] `SDK` Python/TypeScript threads and the bidirectional JSON-RPC app server are supported; `CLI` `codex exec` emits JSONL and accepts a final-output JSON Schema; cloud tasks are asynchronously launchable from several integrations ([SDK](https://learn.chatgpt.com/docs/codex-sdk), [app server](https://learn.chatgpt.com/docs/app-server), [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [cloud](https://learn.chatgpt.com/docs/cloud), accessed 2026-08-23). | [cited] Desktop and IDE add visual review; Codex CLI accepts images but has no browser/computer-use surface documented for CLI ([image inputs](https://learn.chatgpt.com/docs/image-inputs), [browser](https://learn.chatgpt.com/docs/browser), accessed 2026-08-23). | [asserted] SDK or app server first; `codex exec --json --output-schema` second. |
| Cursor | [cited] `SDK` Python local/cloud agents, `SDK` ACP over JSON-RPC stdio, `CLI` `agent -p` with JSON/stream-JSON, and a public-beta Cloud Agents API are documented ([Python SDK](https://cursor.com/docs/sdk/python), [ACP](https://cursor.com/docs/cli/acp), [headless CLI](https://cursor.com/docs/cli/headless), [Cloud API](https://cursor.com/docs/cloud-agent/api/endpoints), accessed 2026-08-23). | [cited] Editor, web, mobile and integrations launch cloud agents; a full cloud desktop can be driven by mouse/keyboard as `CU` ([cloud agents](https://cursor.com/docs/cloud-agent), [cloud capabilities](https://cursor.com/docs/cloud-agent/capabilities), accessed 2026-08-23). | [asserted] Python SDK or ACP first; stream-JSON CLI second; cloud API only when its remote effect boundary is intended. |
| Grok Build CLI | [cited] `CLI` interactive and headless modes emit final JSON or streaming JSON; `SDK`-class ACP runs as JSON-RPC over stdio with resumable sessions ([overview](https://docs.x.ai/build/overview), [headless](https://docs.x.ai/build/cli/headless-scripting), accessed 2026-08-23). [cited] The xAI model API is a separate inference surface and does not carry the Build harness ([CLI reference](https://docs.x.ai/build/cli/reference), accessed 2026-08-23). | [asserted] The reviewed Build documentation establishes web search/fetch and MCP, but not native rendered-browser or computer control; those remain composition-specific. | [asserted] ACP first; structured headless CLI second. |
| Grok Bot | [cited] `APP` Windows/macOS/iOS clients operate a persistent cloud computer and work continues while clients are closed; routines accept schedules or configured events ([FAQ](https://docs.x.ai/grok-bot/faq), [routines](https://docs.x.ai/grok-bot/skills-routines-and-automations), accessed 2026-08-23). | [asserted] No supported general Bot API, CLI or webhook invocation contract was found in the reviewed first-party Bot navigation; its browser/computer is `CU`. | [asserted] No general adapter; a preconfigured routine or explicit human hand-off only. |
| Google Antigravity | [cited] `CLI` `agy -p` provides final JSON, NDJSON event streaming, stdin conversations, JSON Schema, model/effort selection and CI use ([headless](https://antigravity.google/docs/cli/headless/), accessed 2026-08-23). | [cited] `APP` supplies a browser subagent using an isolated Chrome profile and visual artefacts; browser actuation is `CU` ([browser](https://antigravity.google/docs/browser?app=antigravity), accessed 2026-08-23). | [asserted] Structured headless CLI first; app browser only for evidence unavailable through structured tools. |
| Hermes Agent | [cited] `CLI` supports single-query, query-file/stdin, resumable sessions and isolated worktrees; the product also spans desktop and messaging gateways ([CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli/), [overview](https://hermes-agent.nousresearch.com/docs/), accessed 2026-08-23). | [cited] Browser automation and voice/image surfaces are tool- and provider-dependent; several require Nous Portal or another configured backend ([tools](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools/), accessed 2026-08-23). | [asserted] Query-file CLI with a pinned provider and toolset; do not infer reach from Hermes' aggregate label. |

## PRODUCT: advanced surfaces beyond a basic session

| Product surface | Delegation, background and isolation | Structured output, extensions and state | Multimodality, browser and computer |
|---|---|---|---|
| Claude Code | [cited] Subagents, background tasks, experimental agent teams, cloud routines and Git worktrees are documented; Bash sandboxing is optional and platform-dependent ([subagents](https://code.claude.com/docs/en/agents), [worktrees](https://code.claude.com/docs/en/worktrees), [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks), [sandbox](https://code.claude.com/docs/en/sandboxing), accessed 2026-08-23). | [cited] `-p` supports JSON, stream-JSON and JSON Schema; built-in tools, MCP, hooks, skills, plugins, project instructions and local auto-memory are documented ([headless](https://code.claude.com/docs/en/headless), [features](https://code.claude.com/docs/en/features-overview), [memory](https://code.claude.com/docs/en/memory), accessed 2026-08-23). | [cited] Current Claude models accept text and images; Chrome automation and preview computer use exist on restricted surfaces ([models](https://platform.claude.com/docs/en/about-claude/models/overview), [Chrome](https://code.claude.com/docs/en/chrome), [computer use](https://code.claude.com/docs/en/computer-use), accessed 2026-08-23). |
| Claude Cowork | [cited] Parallel subagents, cloud continuation, schedules and a cloud sandbox are documented; a local task uses a per-session Linux VM ([architecture](https://support.claude.com/en/articles/14479288-claude-cowork-architecture-overview), [schedules](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork), accessed 2026-08-23). | [cited] Connectors/MCP, plugins, skills and enterprise inference hooks are documented; reviewable files are human artefacts rather than a machine JSON-schema result contract ([connectors](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities), [plugins](https://support.claude.com/en/articles/13837440-use-plugins-in-claude), [hooks](https://support.claude.com/en/articles/16059458-inference-hooks-overview), [files](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude), accessed 2026-08-23). [cited] First-party pages conflict: the Cowork guide limits memory to projects, while Dispatch says context carries across sessions; routeable memory is therefore unknown ([Cowork guide](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork), [Dispatch](https://support.claude.com/en/articles/13947068-assign-tasks-from-anywhere-in-claude-cowork), accessed 2026-08-23). | [cited] Files, browser and computer use are documented; Anthropic advises connectors first, browser second and raw screen interaction last ([computer use](https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork), accessed 2026-08-23). |
| ChatGPT Work | [cited] Hosted background work, specialised subagents and desktop/web recurring automations are documented ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [automations](https://learn.chatgpt.com/docs/automations), accessed 2026-08-23). | [cited] Plugins, apps, files and hosted state are documented; no arbitrary Work JSON-schema response contract was established by the reviewed sources ([Work](https://learn.chatgpt.com/docs/get-started-with-work), [artifacts](https://learn.chatgpt.com/docs/artifacts-viewer), accessed 2026-08-23). | [cited] Hosted signed-out browser, desktop local browser/computer use, image input and office artefact generation are documented ([browser](https://learn.chatgpt.com/docs/browser), [computer use](https://learn.chatgpt.com/docs/computer-use), [image inputs](https://learn.chatgpt.com/docs/image-inputs), accessed 2026-08-23). |
| OpenAI Codex | [cited] Specialised subagents, asynchronous cloud tasks, isolated cloud environments and independent desktop worktrees are documented ([subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [cloud](https://learn.chatgpt.com/docs/cloud), [worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees), accessed 2026-08-23). | [cited] JSONL plus final JSON Schema, hooks, skills, plugins, MCP client/server and opt-in local memories are documented ([non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode), [hooks](https://learn.chatgpt.com/docs/hooks), [plugins](https://learn.chatgpt.com/docs/plugins), [MCP](https://learn.chatgpt.com/docs/extend/mcp), [memories](https://learn.chatgpt.com/docs/customization/memories), accessed 2026-08-23). | [cited] CLI image input is documented; browser and computer use belong to Work/app surfaces, not the CLI contract ([image inputs](https://learn.chatgpt.com/docs/image-inputs), [browser](https://learn.chatgpt.com/docs/browser), accessed 2026-08-23). |
| Cursor | [cited] Foreground/background subagents, bounded nesting, local worktrees, cloud VMs and event/schedule automations are documented ([subagents](https://cursor.com/docs/subagents), [worktrees](https://cursor.com/docs/configuration/worktrees), [automations](https://cursor.com/docs/cloud-agent/automations), accessed 2026-08-23). | [cited] JSON and stream-JSON envelopes, hooks, plugins, skills, rules, MCP and project-scoped approved memories are documented; final-answer JSON Schema was not established ([headless](https://cursor.com/docs/cli/headless), [hooks](https://cursor.com/docs/hooks), [plugins](https://cursor.com/docs/plugins), [memories](https://docs.cursor.com/en/context/memories), accessed 2026-08-23). | [cited] Editor/browser tools expose screenshots, console and network state; cloud agents can drive a desktop; editor, CLI and Cloud API accept images, while editor prompting also accepts voice ([browser](https://cursor.com/docs/agent/tools/browser), [cloud capabilities](https://cursor.com/docs/cloud-agent/capabilities), [prompting](https://cursor.com/docs/agent/prompting), accessed 2026-08-23). |
| Grok Build CLI | [cited] Isolated subagents, workflows, background commands/monitors, dashboard steering, seven-day loops and worktrees are documented; sandboxing is off by default ([subagents](https://docs.x.ai/build/features/subagents), [background](https://docs.x.ai/build/features/background-tasks), [dashboard](https://docs.x.ai/build/features/dashboard), [worktrees](https://docs.x.ai/build/features/worktrees), [sandbox](https://docs.x.ai/build/features/sandbox), accessed 2026-08-23). | [cited] Final JSON and streaming ACP events, tools, MCP, hooks, skills, plugins, sessions/compaction and experimental cross-session memory are documented ([headless](https://docs.x.ai/build/cli/headless-scripting), [MCP](https://docs.x.ai/build/features/mcp-servers), [extensions](https://docs.x.ai/build/features/skills-plugins-marketplaces), [hooks](https://docs.x.ai/build/features/hooks), [sessions](https://docs.x.ai/build/features/sessions), accessed 2026-08-23). [measured] Installed 1.0.5 also advertises `--json-schema`. | [cited] The default Grok 4.6 model accepts text and images; TUI media commands exist, while headless image transport and native browser/computer control were not established ([Grok 4.6](https://docs.x.ai/developers/grok-4-6), [commands](https://docs.x.ai/build/modes-and-commands), accessed 2026-08-23). |
| Grok Bot | [cited] Concurrent Bots can message and transfer ownership; scheduled/event routines persist while clients are closed, but all Bots for one user share one cloud computer rather than isolated security domains ([overview](https://docs.x.ai/grok-bot/overview), [routines](https://docs.x.ai/grok-bot/skills-routines-and-automations), accessed 2026-08-23). | [cited] Connectors, plugins, MCP, skills, role memory, files and browser state are documented; no Bot lifecycle-hook or JSON-schema result contract was established ([Bots](https://docs.x.ai/grok-bot/bots), [teams](https://docs.x.ai/grok-bot/teams-and-enterprises), accessed 2026-08-23). | [cited] Native cloud browser/computer and local-computer commands are documented, as are image/audio/video/PDF/office/data attachments ([FAQ](https://docs.x.ai/grok-bot/faq), [files](https://docs.x.ai/grok-bot/files-and-results), accessed 2026-08-23). |
| Google Antigravity | [cited] Asynchronous subagents and a native OS terminal sandbox are documented; the reviewed sources did not establish scheduled runs or worktrees ([features](https://antigravity.google/docs/cli-features), accessed 2026-08-23). | [cited] JSON/NDJSON plus final JSON Schema, plugins, skills, agents, rules, MCP and hooks are documented; the reviewed sources did not establish cross-session memory ([headless](https://antigravity.google/docs/cli/headless/), [plugins](https://antigravity.google/docs/cli/plugins/), accessed 2026-08-23). | [cited] A browser subagent can drive an isolated Chrome profile and capture screenshots/video; this is a visual computer-use path, not a structured API ([browser](https://antigravity.google/docs/browser?app=antigravity), accessed 2026-08-23). |
| Hermes Agent | [cited] Delegates, background sessions, cron, worktrees and local/Docker/SSH/serverless terminal backends are documented ([overview](https://hermes-agent.nousresearch.com/docs/), [CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli/), accessed 2026-08-23). | [cited] Tools, MCP, portable/self-created skills, persistent memory and machine-readable usage reports are documented; a schema-constrained final answer was not established for the CLI ([tools](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools/), [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands), accessed 2026-08-23). | [cited] Image paste, voice, search and browser automation are supported when the selected model/provider/tool backend serves them ([features](https://hermes-agent.nousresearch.com/docs/), [tools](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools/), accessed 2026-08-23). |

## PRODUCT: model, context, cost and latency posture

[asserted] API list prices below are comparison signals, not application-pool costs. [asserted] No live quality, latency, context-limit or billing measurement was made, and no PRODUCT row makes a route admissible.

| Product surface | Vendor-claimed model capability | Relative cost/latency claim | ADR-0088 path |
|---|---|---|---|
| Claude Code | [cited] Current selectable Claude models accept text and images; Fable 5, Opus 5 and Sonnet 5 claim 1M context/128K output, while Haiku 4.5 claims 200K/64K; effort trades tokens and latency ([models](https://platform.claude.com/docs/en/about-claude/models/overview), [model configuration](https://code.claude.com/docs/en/model-config), accessed 2026-08-23). | [cited] Direct-API list prices per million input/output tokens are Fable $10/$50, Opus $5/$25, Sonnet $2/$10 and Haiku $1/$5; Anthropic positions Haiku fastest and Fable slowest among these ([models](https://platform.claude.com/docs/en/about-claude/models/overview), accessed 2026-08-23). | [asserted] Bound plan/no-overage: `S_SUBSCRIPTION`. Direct API or extra-use debit: `M_METERED`. |
| Claude Cowork | [cited] Model and effort access is account-controlled; the reviewed Cowork sources publish neither a stable per-task model/context contract nor latency SLA ([model access](https://support.claude.com/en/articles/15694740-manage-model-access-for-your-organization), [consumption](https://support.claude.com/en/articles/14782391-claude-enterprise-consumption-guide), accessed 2026-08-23). | [cited] Anthropic says Cowork is more token-intensive than ordinary chat; no task-level price or latency guarantee is published on that page ([consumption](https://support.claude.com/en/articles/14782391-claude-enterprise-consumption-guide), accessed 2026-08-23). | [asserted] Bound plan/no-overage: `S_SUBSCRIPTION`; credits or extra use: `M_METERED`. |
| ChatGPT Work / Codex | [cited] OpenAI positions GPT-5.6 Sol as flagship, Terra as balanced and Luna as fast/affordable; the API catalogue claims 1.05M context and 128K output for all three, with higher effort taking longer and Ultra invoking subagents ([models](https://learn.chatgpt.com/docs/models), [API catalogue](https://developers.openai.com/api/docs/models), accessed 2026-08-23). | [cited] API list prices per million input/output tokens are Sol $4/$20, Terra $2/$12 and Luna $0.20/$1.20; application use is accounted through plan allowances and credits rather than these API rates ([API catalogue](https://developers.openai.com/api/docs/models), [Codex pricing](https://learn.chatgpt.com/docs/pricing), accessed 2026-08-23). | [asserted] Bound plan/no-overage: `S_SUBSCRIPTION`. Credits or direct API: `M_METERED`. |
| Cursor | [cited] Cursor lists default/max context of 272K/1M for Sol, 272K for Terra/Luna and 200K for Composer 2.5; actual model reach remains composition- and plan-specific ([model catalogue](https://cursor.com/docs), accessed 2026-08-23). | [cited] Cursor calls Composer 2.5 fast/low-cost and provides cost/balanced/intelligence routers; published per-million input/output rates include Composer $0.50/$2.50, Luna $0.20/$1.20, Terra $2/$12 and Sol $5/$30 ([Composer](https://cursor.com/docs/models/cursor-composer-2-5), [router](https://cursor.com/docs/cursor-router), [pricing](https://cursor.com/docs/models-and-pricing), accessed 2026-08-23). | [asserted] Bound plan/no-overage: `S_SUBSCRIPTION`. Usage-priced or API cloud path: `M_METERED` unless proved included and capped. |
| Grok Build CLI | [cited] Grok 4.6 claims text/image input, text output, 500K context and low/medium/high/xhigh reasoning; low targets latency and xhigh adds latency ([model](https://docs.x.ai/developers/grok-4-6), [reasoning](https://docs.x.ai/developers/model-capabilities/text/reasoning), accessed 2026-08-23). | [cited] Grok 4.6 API list price is $2/$6 per million input/output tokens; Build may instead draw on a shared subscription pool ([model](https://docs.x.ai/developers/grok-4-6), [usage FAQ](https://docs.x.ai/grok/faq), accessed 2026-08-23). | [asserted] Bound plan/no-on-demand debit: `S_SUBSCRIPTION`. API key or on-demand: `M_METERED`. |
| Grok Bot | [cited] Team/enterprise Bot uses a provider-managed model set and automatic failover; no stable Bot context window or reasoning control is promised ([teams](https://docs.x.ai/grok-bot/teams-and-enterprises), accessed 2026-08-23). | [cited] Eligible plans include weekly usage and optional on-demand billing, and the reviewed team documentation says there is no Bot-specific spend cap ([FAQ](https://docs.x.ai/grok-bot/faq), [teams](https://docs.x.ai/grok-bot/teams-and-enterprises), accessed 2026-08-23). | [asserted] `S_SUBSCRIPTION` only with on-demand disabled and headroom proved; otherwise `M_METERED` and unavailable without principal approval. |
| Google Antigravity | [cited] Headless mode allows explicit model and low/medium/high effort selection; the reviewed CLI sources do not establish a stable model set, context window or latency SLA ([headless](https://antigravity.google/docs/cli/headless/), accessed 2026-08-23). | [cited] Plan quota can fall through to purchasable AI credits when `useG1Credits` is enabled ([credits](https://antigravity.google/docs/cli/credits), accessed 2026-08-23). | [asserted] `S_SUBSCRIPTION` only with credit fallback disabled and headroom proved; credit use is `M_METERED`. |
| Hermes Agent | [cited] Hermes is provider/model agnostic, has main and auxiliary model slots, detects context per route and supports route-specific reasoning controls; therefore no Hermes-wide context, modality, price or latency number exists ([models](https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models), [providers](https://hermes-agent.nousresearch.com/docs/integrations/providers), [configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration), accessed 2026-08-23). | [cited] Provider routing can prefer price, throughput or first-token latency; subscriptions and direct providers have different billing, including documented cases where consumer-plan OAuth still debits extra usage ([routing](https://hermes-agent.nousresearch.com/docs/user-guide/features/provider-routing), [providers](https://hermes-agent.nousresearch.com/docs/integrations/providers), accessed 2026-08-23). | [asserted] Classify the exact provider route: local may be `Z0_LOCAL`, a proved free key `Z1_FREE_KEY`, a hard-capped plan `S_SUBSCRIPTION`, otherwise `M_METERED`. |

## PRODUCT: documented adverse cases

| Product surface | Failure or limitation that routing must preserve |
|---|---|
| Claude Code | [cited] Non-bare headless sessions can load repository hooks and MCP without the interactive trust dialogue; sandbox setup can fail open unless configured to fail, scheduled loops do not replay missed runs, agent teams are experimental, and computer use is slower, broad in scope and restricted to one controller ([headless](https://code.claude.com/docs/en/headless), [sandbox](https://code.claude.com/docs/en/sandboxing), [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks), [computer use](https://code.claude.com/docs/en/computer-use), accessed 2026-08-23). |
| Claude Cowork | [cited] Prompt injection remains possible; connected apps are outside Cowork's sandbox, local computer use needs the desktop open, and raw-screen interaction is slower/error-prone and can require retry ([safety](https://support.claude.com/en/articles/13364135-use-claude-cowork-safely), [architecture](https://support.claude.com/en/articles/14479288-claude-cowork-architecture-overview), [computer use](https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork), accessed 2026-08-23). |
| ChatGPT Work | [cited] The hosted browser cannot sign in, retain tabs/passwords/history or reliably cross CAPTCHA; local schedules require the app and machine running and web schedules cannot use local folders ([browser](https://learn.chatgpt.com/docs/browser), [automations](https://learn.chatgpt.com/docs/automations), accessed 2026-08-23). |
| OpenAI Codex | [cited] App-server WebSocket transport is experimental and unsupported, and non-loopback access is unauthenticated unless authentication is configured; local sandbox/approval modes materially change effect reach ([app server](https://learn.chatgpt.com/docs/app-server), [sandbox](https://learn.chatgpt.com/docs/sandboxing), accessed 2026-08-23). |
| Cursor | [cited] ACP blocks while permission is unanswered and omits team-dashboard MCP; Cloud API permits one active run per agent and returns `409 agent_busy`; automation schedules may be delayed and some fork/Slack triggers do not work ([ACP](https://cursor.com/docs/cli/acp), [Cloud API](https://cursor.com/docs/cloud-agent/api/endpoints), [automations](https://cursor.com/docs/cloud-agent/automations), accessed 2026-08-23). |
| Grok Build CLI | [cited] Hooks fail open on timeout/crash/malformed output unless they explicitly deny; sandboxing is off by default, network enforcement is platform-limited and credential paths are not inherently protected ([hooks](https://docs.x.ai/build/features/hooks), [sandbox](https://docs.x.ai/build/features/sandbox), accessed 2026-08-23). |
| Grok Bot | [cited] Datacentre IPs may be blocked, CAPTCHA/login/2FA require human hand-back, reset can lose unsynchronised work, and Bots sharing a computer are not security boundaries ([troubleshooting](https://docs.x.ai/grok-bot/troubleshooting), [FAQ](https://docs.x.ai/grok-bot/faq), accessed 2026-08-23). |
| Google Antigravity | [cited] In headless mode an approval-required tool can be soft-denied while the run continues and exits zero; stdin streaming hangs until stdin closes; sandboxing is opt-in; browser domains need allowlisting ([headless](https://antigravity.google/docs/cli/headless/), [browser](https://antigravity.google/docs/browser?app=antigravity), accessed 2026-08-23). |
| Hermes Agent | [cited] File-write guards do not constrain the terminal tool, so they are not a hostile-agent sandbox; the model may claim a blocked edit succeeded and the mutation verifier must outrank its summary ([security](https://hermes-agent.nousresearch.com/docs/user-guide/security/), accessed 2026-08-23). |

## INSTANCE: this machine on 2026-08-23

[measured] Presence means only that a binary or app package was observed. It does not prove login, entitlement, remaining quota, model reach, loaded extension reach, isolation, successful task execution or accepted output.

| Surface | Zero-cost observation | Routable conclusion |
|---|---|---|
| Claude Code | [measured] Windows `claude.exe` reported 2.1.238; help advertised `-p`, JSON Schema, JSON/stream-JSON, agents, background/cloud, worktree, Chrome, MCP/plugins, effort and budget controls. | [asserted] Installed; every advanced capability remains unserved until an exact dispatch probe. |
| Claude Cowork | [measured] A Claude app package at 1.34493.1.0 was observed. | [asserted] Cowork entitlement and every app-only effect remain unknown. |
| OpenAI Codex | [measured] `codex` reported 0.148.0 and the OpenAI Codex app package reported 26.814.5517.0. | [asserted] Installed; app-server, SDK, schema, MCP and model/pool reach remain unprobed. |
| ChatGPT Work | [measured] No probe established a distinct authenticated Work surface. | [asserted] Unknown; do not transfer Codex app presence to Work. |
| Cursor | [measured] WSL `cursor-agent` reported 2026.08.11-e8db854. A key-name-only probe found configured MCP entries named `fetch`, `packages` and `playwright`; the 2026-08-21 survey had found no Cursor MCP configuration. | [asserted] Installed and configured is not served. The two-day drift is direct evidence that a static INSTANCE table is unsafe. |
| Grok Build | [measured] `grok` reported 1.0.5 (5115b46bc9); help advertised JSON Schema, prompt JSON, structured streams, effort, sandbox, resume/fork, worktrees, memory, plugins, MCP and ACP/agent server modes. | [asserted] Installed; no account, quota, MCP, model or task canary was probed. |
| Grok Bot | [measured] Windows package metadata reported Grok Bot 0.23.0. | [asserted] Installed app only; login, plan, Bot and cloud-computer reach remain unknown. |
| Google Antigravity | [measured] `agy` reported 1.1.15; package metadata reported Antigravity 2.8.1 and Antigravity IDE 2.5.5. | [asserted] Installed; auth, plan, agents, schema, sandbox and browser reach remain unknown. |
| Hermes Agent | [measured] `hermes` reported 0.17.0 (2026.6.19). | [asserted] Installed; current documentation may describe newer code, and provider, model, pool and tool reach remain unknown. |
| OpenCode and Gemini CLI | [measured] Neither command resolved on the checked Windows or WSL command inventories. | [asserted] Unavailable by these paths; negative PATH evidence does not exclude an unregistered app or source checkout. |
| Figma Agent | [measured] Package metadata reported Figma Agent 126.7.10. | [asserted] Excluded from routing because this probe established an adjacent design app, not a general task harness or scripted delegation surface. |

[measured] The probes intentionally did not inspect authentication files, token values, connector payloads, account pages, quotas or paid endpoints. [asserted] Reversal is deletion of any INSTANCE row: no event schema or migration depends on this snapshot.

## The machine-readable record

[asserted] Do not create one giant catalogue. Reuse ADR-0054's row and separate three records with different authority:

| Record | Proposed location | Authority |
|---|---|---|
| PRODUCT claim | [asserted] A tracked package-data file, `src/consilient/data/capability-product-v1.json`, generated from reviewed primary sources. | [asserted] Names a capability and a probe recipe. It never authorises a route. |
| INSTANCE observation | [asserted] Gitignored `.harness/capabilities/instance-v1.json`, regenerated locally. | [asserted] Says what one exact composition exposed during a bounded probe. It contains no secret, credential reference, account identifier or quota value. |
| Measured capability row | [asserted] The existing append-only event/provenance path behind ADR-0054, written only through `events.py`. | [asserted] Carries `strength`, `anchor`, verifier result and beta provenance. Routing may consume it only with a fresh INSTANCE observation. |

[asserted] The first implementation should use schema version 1 below and no extension mechanism. Unknown fields refuse, because silently accepting a changed capability contract creates the stale-positive failure this design is meant to prevent.

```json
{
  "schema_version": 1,
  "record_type": "product_claim | instance_observation",
  "record_id": "sha256:<canonical-record-without-record_id>",
  "capability_id": "vision.image.read",
  "composition": {
    "harness": "codex",
    "surface": "cli",
    "provider": "openai",
    "model": "gpt-5.6-sol"
  },
  "reach": {
    "mode": "sdk | cli | api | app | computer_use",
    "scriptable": true,
    "entrypoint": "codex exec",
    "native_binding": "image_argument"
  },
  "state": "claimed | absent | installed | configured | served | refused | stale",
  "product_evidence": [
    {
      "source_url": "https://learn.chatgpt.com/docs/image-inputs",
      "accessed_at": "2026-08-23",
      "source_section_sha256": "sha256:...",
      "version_constraint": "documented-or-null"
    }
  ],
  "probe": {
    "method": "help | config_keys | tools_list | schema_list | canary",
    "observed_at": "2026-08-23T11:00:00Z",
    "expires_at": "2026-08-23T11:15:00Z",
    "binary_version": "0.148.0",
    "served_surface_sha256": "sha256:...",
    "outcome": "served | absent | refused | stale",
    "reason_code": "stable-enum"
  },
  "pool": {
    "rung": "Z0_LOCAL | Z1_FREE_KEY | S_SUBSCRIPTION | M_METERED | unknown",
    "pool_id": "opaque-local-name",
    "overage": "disabled | possible | unknown"
  },
  "provenance": {
    "run_id": "local-run-id",
    "event_id": "trajectory-event-id"
  }
}
```

[asserted] PRODUCT records use a composition pattern: `provider` or `model` may be `null` only to mean “the claim did not bind this dimension”. For an INSTANCE join, task family comes from the request; harness, provider and model remain separate as ADR-0027 requires; and this atlas adds the exact invocation surface. A wildcard INSTANCE observation is invalid.

[asserted] `capability_id` is a stable verb-object identifier such as `structured_output.json_schema`, `browser.dom.inspect`, `computer.screen.actuate` or `vision.image.read`. It describes an effect, not a vendor feature name. `native_binding` records how ADR-0084 must compile the request; an instruction that merely tells the model a capability exists is not a native binding.

[asserted] `state` is not a maturity ladder that can be inferred upwards. `installed` does not imply `configured`, and `configured` does not imply `served`. Only the named probe writes the observed state, and any invalidator writes `stale`. Measurement lives only in the separate ADR-0054 row because the atlas does not own strength, anchor or beta.

[asserted] The record deliberately excludes token values, credential paths, account names, remaining quota, prices paid, prompts, file contents and connector payloads. `pool_id` is a local opaque name joined to `budget.py`; the atlas never becomes a second budget store. ADR-0084's runtime credential binding stays outside the model process and outside this record.

## Refresh and staleness

[measured] Cursor MCP configuration changed between the tracked 2026-08-21 survey and the 2026-08-23 key-name probe. [asserted] A periodic static survey therefore cannot be a positive routing authority even when it is only two days old.

[asserted] Refresh uses cheap invalidators before expensive canaries:

1. [asserted] On source refresh, fetch the exact first-party section, canonicalise headings/text/code, and compare `source_section_sha256`, HTTP ETag/Last-Modified when present, URL status and redirect target. Any change, disappearance or failed retrieval makes every dependent PRODUCT row `stale`; it never silently upgrades a claim.
2. [asserted] On local start and binary change, compare resolved executable, `--version` and a canonical digest of the relevant `--help` surface. A change invalidates dependent INSTANCE rows.
3. [asserted] On every dispatch needing the capability, inspect only non-secret configuration key names and ask the native discovery surface—such as MCP `tools/list`, an app-server schema list or an SDK capability call—for names and input schemas. Hash that served surface. A cached observation from an earlier dispatch cannot authorise the new dispatch.
4. [asserted] Re-run an effect-free canary only when discovery cannot establish the required effect. A canary may parse a fixed local fixture but must not send a model prompt, mutate the target repository or make a metered request unless a separately authorised experiment provides a numeric cap.
5. [asserted] Probe ADR-0042 admission and ADR-0088 pool/headroom separately. Failure, unknown overage or expired headroom makes the composition unavailable regardless of capability state.

[asserted] A seven-day PRODUCT review ceiling is a provisional maintenance trigger, not proof of freshness. Release/changelog events and digest changes trigger earlier review. [asserted] An INSTANCE positive expires at the end of the dispatch that observed it; the stored `expires_at` is for audit and diagnosis, not reuse. App-only capabilities with no safe discovery contract remain `APP`/unknown and cannot be selected unattended.

[asserted] Stale negatives may waste an opportunity; stale positives can misroute and create effects. The design therefore fails closed asymmetrically: an unavailable refresh deletes the positive from the candidate set, while the default generalist may still proceed without an optional capability.

## How the existing system consumes the record

### Routing

[asserted] Extend `routing.py`; do not add a router:

1. [asserted] The Owner or task producer supplies required and optional `capability_id` values with a verifier contract. Do not infer a hard requirement from free text until such inference has measured beta.
2. [asserted] `capabilities.py` validates those identifiers against the shipped PRODUCT taxonomy and generates the vendor-specific probe/binding plan from ADR-0084.
3. [asserted] `dispatch.py` probes each exact candidate composition, writes the secret-free INSTANCE observation through `events.py` and drops stale/refused candidates.
4. [asserted] `routing.py` joins fresh `served` observations to ADR-0054 rows for the same task family, exact composition, verifier, strength and external anchor. A vendor claim or harness label contributes zero strength.
5. [asserted] `budget.py` admits candidates in ADR-0088 rung order. A path capable of debit is `M_METERED` and remains refused without principal authority.
6. [algebra] Apply `candidate_ceiling(epsilon, beta_upper)` after capability and pool filtering. If beta is unmeasured, routing refuses additional candidate writers; if `epsilon < beta_upper`, the permitted candidate count is zero.
7. [asserted] Emit a selection/refusal receipt with the product-record digest, fresh served-surface digest, exact composition, capability-row provenance, pool rung and ceiling. Keep `routing_orchestration_enabled` false until its existing gate changes by its own authority.

[asserted] Cold start remains ADR-0054's one default generalist. A hard modality requirement that the default cannot serve produces a capability hand-off or refusal, not a guessed alternate harness. An optional advanced feature that is not served is omitted.

### Dynamic context and instructions

[measured] Today `task_with_capabilities()` serialises selected metadata into the task, and `instructions.assemble()` later assembles that text. [asserted] Prompt injection alone cannot make a capability real, so the next implementation should pass the validated selection object to `instructions.assemble()` as data and bind it natively in `dispatch.py`.

[asserted] Keep the existing instruction-layer order. Capability context is task data, not a fifth authority layer. The bounded rendered section contains only:

- [asserted] the exact served capabilities and native binding selected for this run;
- [asserted] effect limits, sandbox/worktree state and pool rung;
- [asserted] required output schema and verifier contract;
- [asserted] capability-gap triggers and the one-Owner hand-off rule;
- [asserted] record and probe digests for the receipt.

[asserted] It contains no vendor brochure text, hidden configuration, secret, token, account value or irrelevant capability. An instruction may narrow a served capability but cannot widen it. The assembly receipt records the selected-capability digest; the runtime receipt records `applied`, `degraded` or `refused` as ADR-0084 requires.

### Capability-grounded hand-off

[asserted] Reuse `work_items.py` and `coordination.py`. The originating candidate remains the only Owner. The receiving composition is Responsible for one evidence-acquisition subtask and Consulted by the Owner; it is never Accountable for the final artefact, verdict, gate, approval or spend.

[asserted] A `capability_gap` work item contains:

```json
{
  "owner_run_id": "originating-owner",
  "parent_work_item_id": "existing-item",
  "required_capability": "vision.image.read",
  "reason_code": "current-composition-text-only",
  "evidence_class": "pixels in the immutable image artefact",
  "input": {
    "artifact_uri": "workspace-relative-or-content-addressed-reference",
    "sha256": "sha256:...",
    "media_type": "image/png"
  },
  "question": "Read the error text and locate the highlighted control.",
  "allowed_effects": ["read"],
  "forbidden_effects": ["write", "publish", "approve", "spend", "redelegate"],
  "output_schema": "capability_result.v1",
  "verifier_contract": "artifact-digest-and-required-fields",
  "pool_ceiling": "S_SUBSCRIPTION"
}
```

[asserted] The receiver is told the exact question, immutable input digest, evidence class, allowed effects, output schema, verifier, budget ceiling and that it must refuse rather than redelegate. It returns `status` (`completed`, `refused` or `failed`), observations, artefact/digest, provenance and limitations—never a final verdict or approval. If another capability is needed, it returns a gap; only the Owner may create the next work item.

[asserted] In the image example, inspecting pixels introduces a fact surface the text-only composition could not read. Merely asking a different model family to reread the same extracted text does not. Executing the artefact, inspecting live browser state or checking a citation against its primary source may be different classes; model-family identity by itself remains unmeasured.

[asserted] A fact-only receiver does not author an alternative candidate. If its output can edit or replace the candidate artefact, it is another candidate exposure and must fit the robust beta ceiling. The principal's reserved actions—verdicts, approvals, gate lifts and spend—have no receiver role and therefore cannot be delegated.

## The three unused capabilities most likely to improve outcomes

1. **Structured lifecycle output and final schemas.** [measured] Current dispatch uses ordinary CLI completion and explicitly requests text from Cursor; it does not request vendor JSON Schema or consume SDK/ACP lifecycle events. [cited] Claude Code, Codex, Grok Build and Antigravity document final-schema or structured event modes, while Cursor documents JSON event streams ([Claude headless](https://code.claude.com/docs/en/headless), [Codex non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode), [Grok headless](https://docs.x.ai/build/cli/headless-scripting), [Antigravity headless](https://antigravity.google/docs/cli/headless/), [Cursor headless](https://cursor.com/docs/cli/headless), accessed 2026-08-23). [asserted] This is the highest-value first step because terminal state, tool failures, usage and required fields become parseable artefacts rather than prose or exit-code inference.
2. **Native SDK/ACP/app-server control with resume, steer and cancellation.** [measured] Current dispatch builds one CLI process per harness and does not use Claude Agent SDK, Codex app server/SDK, Cursor ACP/SDK or Grok ACP. [cited] Those surfaces expose structured sessions and lifecycle control ([Claude SDK](https://code.claude.com/docs/en/agent-sdk/overview), [Codex app server](https://learn.chatgpt.com/docs/app-server), [Cursor ACP](https://cursor.com/docs/cli/acp), [Grok headless/ACP](https://docs.x.ai/build/cli/headless-scripting), accessed 2026-08-23). [asserted] They should reduce false “still running” states and enable bounded steering, but only an experiment can establish the size of that improvement.
3. **Modality-aware browser/image hand-off through a served structured tool.** [measured] The current capability selection is prompt context and does not bind an image argument, MCP browser or native browser surface. [cited] The installed product families advertise image or browser paths, including Codex image input, Cursor browser tools, Claude Chrome and Grok image input ([Codex images](https://learn.chatgpt.com/docs/image-inputs), [Cursor browser](https://cursor.com/docs/agent/tools/browser), [Claude Chrome](https://code.claude.com/docs/en/chrome), [Grok model](https://docs.x.ai/developers/grok-4-6), accessed 2026-08-23). [asserted] This can introduce runtime or pixel evidence that a text-only candidate lacks. Prefer MCP/DOM/image arguments; raw computer use is last because none of the reviewed vendors publishes a quantitative reliability rate and each documents hand-backs, blocks or timing limitations.

[asserted] Native subagents are deliberately not in the top three. The repository's present bottleneck is trustworthy evidence and receipts, not generating more candidate prose; additional candidate writers remain beta-bounded.

## Current bar and how to beat it

[cited] The current native control-surface bar is live discovery plus structured lifecycle control: MCP exposes tool discovery, Codex app server exposes bidirectional JSON-RPC, and Cursor ACP exposes JSON-RPC stdio ([MCP specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools), [Codex app server](https://learn.chatgpt.com/docs/app-server), [Cursor ACP](https://cursor.com/docs/cli/acp), accessed 2026-08-23). [asserted] A hand-maintained matrix cannot beat that bar.

[asserted] Consilient beats a static catalogue only if it adds the missing cross-vendor invariant: the exact served surface is probed at dispatch, joined to verifier-measured capability and beta, constrained by a fail-closed pool, compiled natively, and receipted. [asserted] The measurement is zero stale-positive selections plus a higher accepted-first-attempt rate or lower timeout/refusal rate at no higher permitted pool rung than today's basic invocation.

## Evidence against: the atlas will rot faster than it pays

[asserted] The strongest case against this work is that the atlas is already obsolete when merged. Vendors can change flags, models, entitlements and documentation independently; installed versions lag current pages; app-only features often have no discovery API; account rollout can make two identical binaries expose different surfaces. A weekly scrape can miss a breaking change for six days, a source digest can fire on cosmetic edits, and a normalised “browser” capability can conceal materially different DOM, screenshot and raw-computer contracts. Maintaining nine product surfaces may cost more than the few routing decisions that need an advanced feature.

[measured] This is not hypothetical: Cursor went from no observed MCP configuration on 2026-08-21 to three configured names on 2026-08-23, while Hermes 0.17.0 is older than the documentation retrieved today. [asserted] A stale positive is worse than no atlas because it makes a wrong route look evidence-backed.

[asserted] The answer is not “refresh more often”. PRODUCT data is only a probe recipe; every positive route needs a dispatch-time served-surface observation, and rows without a cheap safe probe stay unavailable. Source and version digests make review targeted, while the failed-closed cache makes deletion cheap. If a vendor exposes neither safe discovery nor a bounded canary, concede that surface: keep it `APP`/human-only or remove it rather than maintain a confident guess.

[asserted] The atlas should be deleted if, after implementation, capability-aware routing does not improve verifier-accepted first attempts or reduce terminal ambiguity versus current dispatch, or if any stale PRODUCT/INSTANCE positive selects a missing capability. [asserted] The required killing experiment is not registered here: preregister a paired replay over fixed task families with capability requirements, compare current basic CLI against probed/native binding, and set sample size and stopping rules before running. Until that exists, expected benefit remains asserted.

## Search record, limitations and reversal

[measured] Primary-source searches covered each vendor's official navigation for headless/SDK/API, subagents/background/schedules, worktrees/sandbox, JSON/schema, MCP/hooks/skills/plugins/memory, browser/computer, multimodality, model/context/effort, price/latency and security/troubleshooting. [measured] Near misses were excluded: community comparisons, search snippets without an opened first-party page, generic model APIs that bypass the named harness, and product-family names used as if they transferred capability between distinct surfaces.

[measured] Negative searches did not establish a general Cowork CLI/API, Grok Bot API/CLI, Cursor final-answer JSON Schema, Hermes CLI final-answer JSON Schema, Antigravity schedules/worktrees/memory, Grok Build native computer use, or a stable app-only model/context contract. [asserted] Those cells are unknown, not absent.

[measured] No outcome strength, verifier acceptance, beta, task latency, subscription headroom, entitlement, browser success, computer-use reliability, sandbox enforcement or API spend was measured. [asserted] Vendor prices and relative-speed language may change and must be refreshed before any economic comparison.

[asserted] Reversal is cheap: remove the proposed PRODUCT seed, delete the gitignored INSTANCE cache, stop passing capability requests, and current default dispatch remains. No migration, gate lift, CLI addition or public event contract is introduced by this document.

[asserted] Falsifiers are: a first-party source contradicting a PRODUCT row; an effect-free probe contradicting an INSTANCE row; a served capability failing its verifier canary; a debit-capable path classified below `M_METERED`; a hand-off that changes the candidate without counting as candidate exposure; or a replay showing no improvement over current basic invocation. Any one invalidates the affected row or design claim rather than being explained away.

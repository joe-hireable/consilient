# Subscription reach: Hermes Agent and Consilient

**Correction:** Hermes Agent is not confined to its own provider, but among the four plans named here only its opt-in Codex app-server path demonstrably hands a complete turn to another subscription-authenticated CLI; Claude uses separately purchased Max overage, Cursor is absent, and Grok inference debit is undocumented. [cited]

Research snapshot: **2026-08-22T14:08:54Z**. [measured]

Hermes source: [`NousResearch/hermes-agent` `261a4ef`](https://github.com/NousResearch/hermes-agent/commit/261a4ef), tree `1baf254`, version `0.20.5`; the pinned checkout was clean and its `origin/main` resolved to the same commit during inspection. [measured]

Consilient source trace: `c7709803fde714260c917f40cfb3eabf002bcebc`; the named dispatch, harness, capability and knowledge paths were unchanged by later concurrent commits at the time of writing. Local trajectory observations are separately timestamped below. [measured]

This report answers only the money and connectivity questions. Delegation, Kanban, persistence and authority are covered by the earlier `docs/00-context/hermes-teardown-2026-08-22.md` and are not repeated here. [asserted]

## Direct answer

| System | Sense A — another model subscription | Sense B — connected services |
|---|---|---|
| **Hermes** | **Qualified yes.** Codex can receive the whole turn through a real `codex app-server` child process using its separately authenticated ChatGPT subscription. Claude OAuth consumes purchased extra usage rather than the base Max allowance; Cursor has no path; eligible SuperGrok OAuth exists but inference quota accounting is undocumented. [cited] | **Yes.** Hermes is an arbitrary stdio/HTTP MCP client and has native, skill and curated-MCP routes. [cited] Its maintained catalogue is materially smaller and more operationally demanding than Claude's or ChatGPT's. [asserted] |
| **Consilient** | **Subscription spend unproven; multi-CLI execution measured for three.** It really invokes four external CLIs, and the trajectory contains successful Codex, Cursor and Grok artefacts, but no Claude dispatch success and no event that binds a run to an authentication mode or quota debit. [measured] Gate B remains shut and automatic multi-pool selection currently cannot form a two-pool set, so this is not operational multi-subscription routing. [asserted] | **No live task-scoped pass-through.** The capability inventory becomes prose in a brief; it does not activate, authenticate or configure the requested MCP/connection. A separate global knowledge-config writer exists, but dispatch does not call it and the trajectory records no knowledge retrieval. [measured] The answer today is no. [asserted] |

**Verdict:** multi-subscription orchestration is **not a defensible broad Consilient differentiator today**. Hermes already reaches third-party consumer credentials and delegates real turns to Codex; Consilient's narrower prospective distinction is supervised use of four separate vendor CLIs, including Cursor, under explicit headroom and evidence controls. That narrower distinction is not yet complete or measured as reliable automatic orchestration. [asserted]

## Hermes — Sense A: subscription quota

### Cited source findings

Hermes resolves an explicit provider, then configured provider, environment choice or `auto`; automatic resolution considers configured endpoints and keys, OpenRouter, provider credentials and active OAuth identities. The resulting provider, endpoint, credential and API mode initialise a native transport, except when the explicit Codex app-server runtime is selected. [cited] Sources: [provider selection](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/runtime_provider.py#L618-L634), [credential resolution](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/auth.py#L2080-L2139), [runtime resolution](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/runtime_provider.py#L1766-L1936), [agent initialisation](https://github.com/NousResearch/hermes-agent/blob/261a4ef/agent/agent_init.py#L682-L730).

| Existing plan | Hermes path | What the evidence permits |
|---|---|---|
| **Claude Max / Pro** | Hermes imports Claude Code OAuth credentials or performs its own PKCE, then calls Anthropic Messages itself. The only `claude` subprocess uses are credential/version setup, not delegated agent turns. [cited] Sources: [adapter](https://github.com/NousResearch/hermes-agent/blob/261a4ef/agent/anthropic_adapter.py#L1083-L1148), [credential import](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/runtime_provider.py#L2164-L2231). | **No base-plan spend.** Hermes documents that the path requires Claude Max plus purchased extra-usage credits, consumes only those overage credits, and does not work for Claude Pro. This is third-party OAuth, but it does not spend the already-included Claude Code allowance asked about in this brief. [cited] Source: [subscription table and warning](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/integrations/providers.md#L112-L145). |
| **ChatGPT / Codex** | The default path uses Hermes OAuth against the Codex Responses endpoint. Opting into `model.openai_runtime: codex_app_server` instead launches `codex app-server`, hands it the complete turn, and relies on Codex's separate `~/.codex/auth.json`. [cited] Sources: [transport](https://github.com/NousResearch/hermes-agent/blob/261a4ef/agent/transports/codex_app_server.py#L1-L14), [child process](https://github.com/NousResearch/hermes-agent/blob/261a4ef/agent/transports/codex_app_server.py#L71-L142), [runtime guide](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/codex-app-server-runtime.md#L150-L198). | **Yes for the app-server path, source-supported rather than receipt-measured.** Hermes describes this as using the ChatGPT subscription without an API key. Its direct OAuth path is also real, but the documentation does not specify exactly how those calls count against plan limits. [cited] Sources: [runtime scope](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/codex-app-server-runtime.md#L6-L21), [provider table](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/integrations/providers.md#L118-L130). |
| **Cursor Ultra** | No Cursor provider, alias, runtime or `cursor-agent` integration exists in the provider/runtime tree inspected. [measured] Evidence: bounded searches for `cursor-agent`, `Cursor Ultra`, `cursor subscription` and `cursor oauth`; [canonical alias map](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/auth.py#L2102-L2139). | **No.** Hermes cannot spend Cursor's subscription or delegate a Cursor turn at this revision. [measured] |
| **SuperGrok / X Premium+** | Hermes creates its own xAI device-code OAuth session and sends the bearer token directly to `api.x.ai`; it does not launch the Grok CLI. Current code handles tier, quota and allow-list `403` responses and says X Premium+ alone may not grant API access. [cited] Sources: [OAuth definitions](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/auth.py#L150-L160), [login path](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/auth.py#L7991-L8056), [runtime](https://github.com/NousResearch/hermes-agent/blob/261a4ef/run_agent.py#L2600-L2654). | **Not proven for inference spend.** Hermes explicitly documents subscription-quota use for X Search, but says inference quota semantics are not documented; successful OAuth also depends on an eligible standalone SuperGrok entitlement. It therefore cannot be counted as a verified subscription-funded agent turn. [cited] Source: [subscription table](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/integrations/providers.md#L118-L130). |

Hermes also supports GitHub Copilot as a first-class provider and through a local `copilot-acp` CLI using the user's existing login. This is further prior art for subscription reach, although it is outside the four plans in scope. [cited] Source: [provider documentation](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/integrations/providers.md#L178-L228).

The delegated child-agent path may select a different configured provider and model, but that is provider routing, not evidence that every provider is a child harness or that its base subscription pays. [cited] Source: [delegation configuration](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/delegation.md#L143-L175).

### Billing lifecycle

`docs/billing-lifecycle.md` is a client-side rendering and recovery map for `billing.*` and `subscription.*` states returned by Nous Account Service. The client buys Nous credits, polls card charges, manages auto-reload and changes a Nous subscription through server-side Stripe operations. [cited] Sources: [lifecycle scope](https://github.com/NousResearch/hermes-agent/blob/261a4ef/docs/billing-lifecycle.md#L1-L12), [billing client](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/nous_billing.py#L1-L24), [subscription mutation](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/nous_billing.py#L648-L675).

It governs Nous's own plan, monthly dollar-denominated credits and metered top-ups. It is not a universal budget, kill switch or broker for Anthropic, OpenAI, Cursor, xAI or BYO endpoint spend. [cited] Source: [plan catalogue and monthly credits](https://github.com/NousResearch/hermes-agent/blob/261a4ef/docs/billing-lifecycle.md#L149-L169).

### OpenRouter, local models and BYO endpoints

Hermes supports OpenRouter through `OPENROUTER_API_KEY`, keyless local Ollama/vLLM/llama.cpp-compatible endpoints, and named custom endpoints with an inline key, `key_env` or renewable `key_cmd`. [cited] Sources: [OpenRouter](https://github.com/NousResearch/hermes-agent/blob/261a4ef/plugins/model-providers/openrouter/__init__.py#L234-L250), [local aliases](https://github.com/NousResearch/hermes-agent/blob/261a4ef/plugins/model-providers/custom/__init__.py#L95-L112), [named credentials](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/runtime_provider.py#L1188-L1228).

Those are useful provider choices, but an OpenRouter/API key is metered credit, a local endpoint is local compute, and a BYO key inherits that endpoint's billing. None proves consumption of an already-paid consumer subscription. [asserted]

## Hermes — Sense B: connected services

### Cited source findings

Hermes consumes arbitrary mappings under `mcp_servers`, not a fixed allow-list. An entry can be a spawned stdio command with explicit arguments/environment or a remote Streamable HTTP/SSE endpoint with headers, TLS controls and client certificates. [cited] Sources: [configuration parser](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_tool.py#L5493-L5525), [remote transports](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_tool.py#L3379-L3515), [MCP guide](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/mcp.md#L202-L301).

Remote authentication supports static headers, browser OAuth 2.1 authorisation code with PKCE, CIMD, RFC 7591 dynamic client registration, or a pre-registered client ID/secret. Cached tokens avoid a new browser interaction. Stdio children receive a restricted baseline plus secret-source-tagged and explicitly configured variables. [cited] Sources: [OAuth implementation](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_oauth.py#L3-L42), [registration and PKCE](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_oauth.py#L1439-L1495), [stdio environment](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_tool.py#L709-L739).

OAuth tokens and client registrations are stored below `HERMES_HOME/mcp-tokens`. The code requests restrictive POSIX modes but explicitly notes that those mode bits are not enforced on Windows, so host ACLs remain material on this machine. [cited] Sources: [token storage](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_oauth.py#L192-L201), [permissions](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/mcp_oauth.py#L414-L442).

The curated catalogue contained **20 valid entries** with no catalogue diagnostics. [measured]

`airtable`, `asana`, `atlassian`, `comfy-cloud`, `datadog`, `figma`, `hugging_face`, `intercom`, `linear`, `n8n`, `netlify`, `notion`, `paypal`, `sentry`, `square`, `stripe`, `supabase`, `unreal-engine`, `vercel`, `webflow`. [measured] Evidence: `hermes_cli.mcp_catalog.list_catalog()` and `catalog_diagnostics()` at the pinned revision; [loader](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/mcp_catalog.py#L351-L379).

Catalogue installation is not proof that authentication or probing succeeded, and installed entries do not auto-update. Figma additionally relies on a compatibility workaround that presents the client name `Claude Code` because Figma rejects Hermes's own DCR name. [cited] Sources: [installation semantics](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/mcp.md#L91-L119), [update semantics](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/mcp.md#L177-L183), [Figma manifest](https://github.com/NousResearch/hermes-agent/blob/261a4ef/optional-mcps/figma/manifest.yaml#L11-L17).

### Named services: native, skill, curated or manual

| Service | Route at the pinned revision | Honest reach |
|---|---|---|
| Gmail, Drive, Calendar | Bundled Google Workspace skill and scripts, covering Gmail, Calendar, Drive, Docs, Sheets and Contacts. [cited] Source: [skill](https://github.com/NousResearch/hermes-agent/blob/261a4ef/skills/productivity/google-workspace/SKILL.md#L1-L22). | Concrete read/write path, but the user must create a Google Cloud OAuth client and enable APIs; it is not one-click account connection. [cited] Source: [setup](https://github.com/NousResearch/hermes-agent/blob/261a4ef/skills/productivity/google-workspace/SKILL.md#L83-L165). |
| Slack | Native `slack-bolt` Socket Mode messaging gateway, or manually configured official Slack MCP. [cited] Sources: [plugin](https://github.com/NousResearch/hermes-agent/blob/261a4ef/plugins/platforms/slack/plugin.yaml#L1-L22), [Slack MCP](https://docs.slack.dev/ai/slack-mcp-server). | Gateway chat transport is narrower than workspace-wide search/action access; the MCP needs a registered Slack app and fixed client credentials. [cited] |
| Linear, Sentry, Stripe | Curated vendor-hosted OAuth MCP recipes. [cited] Sources: [Linear](https://github.com/NousResearch/hermes-agent/blob/261a4ef/optional-mcps/linear/manifest.yaml#L5-L21), [Sentry](https://github.com/NousResearch/hermes-agent/blob/261a4ef/optional-mcps/sentry/manifest.yaml#L5-L19), [Stripe](https://github.com/NousResearch/hermes-agent/blob/261a4ef/optional-mcps/stripe/manifest.yaml#L5-L19). | Curated recipes are present, subject to live provider authentication and tool probing. [cited] |
| Figma | Curated remote OAuth MCP. [cited] | Present, but dependent on the `Claude Code` client-name workaround described above. [cited] |
| GitHub | Bundled `git`/`gh` skills; deliberately excluded from the curated MCP catalogue because hosted GitHub MCP requires a per-client OAuth app. [cited] Sources: [policy](https://github.com/NousResearch/hermes-agent/blob/261a4ef/hermes_cli/mcp_catalog.py#L127-L130), [auth skill](https://github.com/NousResearch/hermes-agent/blob/261a4ef/skills/github/github-auth/SKILL.md#L14-L38). | Concrete non-MCP route. [cited] |
| Attio, ClickUp, PostHog | Not curated; each publishes a remote MCP endpoint whose stated transport/authentication shape Hermes implements. [cited] Sources: [Attio](https://docs.attio.com/mcp/overview), [ClickUp](https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server), [PostHog](https://posthog.com/docs/model-context-protocol). | Source-compatible manual reach, not measured account access. [asserted] |
| ElevenLabs | Native API-key TTS and transcription, plus a manually configurable hosted MCP. [cited] Sources: [native TTS](https://github.com/NousResearch/hermes-agent/blob/261a4ef/tools/tts_tool.py#L1755-L1790), [hosted MCP](https://elevenlabs.io/docs/eleven-agents/operate/hosted-mcp). | The native path is narrower than a general ElevenLabs account connector; hosted-MCP compatibility was not exercised. [asserted] |

### Comparison with the catalogues already available

Claude provides first-party Gmail, Drive, Calendar, GitHub, Slack and Microsoft 365 integrations, a connector directory and custom remote MCP. [cited] Sources: [official overview](https://claude.com/docs/connectors/overview), [directory documentation](https://claude.com/docs/connectors/directory). Its public directory exposed 406 unique connector slugs across 17 pages on 2026-08-22. [measured] Source: [live directory](https://claude.com/connectors).

ChatGPT supports custom MCP and an official Plugins Directory whose listings may package apps, skills and templates; availability varies by plan, workspace, role, surface and region. [cited] Source: [OpenAI Help](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt). Its logged-out directory visibly covered Gmail, Drive, Calendar, Slack, GitHub, Figma and PostHog on 2026-08-22. [measured] Source: [official directory](https://chatgpt.com/plugins).

Hermes's protocol reach is broad and credible, but its maintained MCP catalogue is only 20 entries, several routes require user-created OAuth clients, and installation does not prove compatibility. Claude and ChatGPT already accept custom MCP while providing broader managed account catalogues. Hermes is useful prior art for local/self-hosted connector plumbing, not a catalogue-breadth advantage for Consilient. [asserted]

## Consilient — Sense A: subscription quota

### Measured local findings

Consilient's registry maps `claude`, `cursor-composer`, `grok` and `codex` to distinct vendor families and quota pools. Dispatch probes the real binaries; `build_command` emits `claude ... -p`, `cursor-agent -p --model`, `grok -p ... --cwd` or `codex exec -C`; `run_harness` executes that argument vector through `Popen`. An exit-zero result must also produce non-empty output or a diff before an `ok` outcome is written. [measured] Sources: [`src/consilient/harness.py`](../../src/consilient/harness.py#L117-L126), [`scripts/dispatch.py`](../../scripts/dispatch.py#L732-L1008).

At **2026-08-22T14:00Z**, the accepted local trajectory contained 109 `dispatch.outcome` events. The adverse outcomes are retained here because success-only counts would misstate reliability. [measured]

| Harness | All outcomes | `ok` | Other outcomes | Representative artefact |
|---|---:|---:|---|---|
| Codex | 43 | 16 | 18 timeout, 5 refused, 3 silent, 1 failed | `codex.CMD exec`, exit 0, non-empty artefact and diff in `.harness/log/2026-08-22.jsonl:103`. [measured] |
| Cursor Composer | 37 | 19 | 12 refused, 4 timeout, 2 killed | WSL `cursor-agent -p --model composer-2.5`, exit 0, non-empty artefact in `.harness/log/2026-08-22.jsonl:5`. [measured] |
| Grok | 29 | 5 | 19 timeout, 3 refused, 2 killed | `grok.CMD -p`, exit 0, non-empty artefact in `.harness/log/2026-08-21.jsonl:41`; the latest success was 21 August, not the report date. [measured] |
| Claude | 0 | 0 | No dispatch outcome exists. | `.harness/fallback-result.json` records a separate bare `claude -p` fallback on 20 August; it is not a dispatch outcome. [measured] |

The trajectory therefore proves that the Codex, Cursor and Grok CLIs performed work and produced artefacts. It does **not** record the authentication mode, provider account or before/after quota counter, so it proves subscription debit for none of them. [measured]

Current corroboration is strong but remains indirect: the common Anthropic, OpenAI, Cursor and Grok API-key variables were absent in a presence-only check; Codex reported plan `pro` and Cursor reported tier `Ultra`; [prior backend evidence](../20-design/backends.md) records device-code SuperGrok and subscription logins. [measured] These observations make subscription use likely for the three successful families, but they do not bind a particular outcome to a billable plan counter. [asserted]

Subscription-first is structurally guarded only for Grok: `metered_grok_reason()` refuses three common Grok API-key variables. Claude and Codex have no equivalent check, and dispatch passes the non-Git environment through, so the general path cannot prove that those CLIs did not select metered credentials. [measured] Sources: [`scripts/dispatch.py`](../../scripts/dispatch.py#L499-L507), [`scripts/dispatch.py`](../../scripts/dispatch.py#L958-L979).

Headroom was known only for Codex (`pro`, 72% used); Claude, Cursor and Grok were `unknown`. Automatic selection excludes unknown headroom, while an attended explicit `--harness` selection may proceed. The current automatic selector therefore cannot form a two-pool fan-out even though supervised explicit invocations work. [measured] Sources: [harness selection](../../src/consilient/harness.py#L480-L500), local `.harness/headroom.json`.

Two authoritative `consil doctor --json` projections returned A1 fail, A2 pass, A3 fail; B1 pass, B2 fail, B3 pass and B4 fail. Both gates fail, `routing_orchestration_enabled` is `false`, and the command exits 1. Foreign allow-listed dispatch remains supervised and is explicitly not a Gate B pass; beta-conditioned routing is deliberately unwired. [measured] Sources: [`src/consilient/cli.py`](../../src/consilient/cli.py#L756-L808), [`scripts/dispatch.py`](../../scripts/dispatch.py#L12-L17), [`src/consilient/routing.py`](../../src/consilient/routing.py#L1-L20).

This means Consilient may build and supervise experimental dispatch here, but it cannot honestly claim dependable unattended orchestration or rely on the harness for another repository. The flag is reporting that boundary, not merely hiding a finished product. [asserted]

## Consilient — Sense B: connected services

### Measured local findings

`CapabilityKind` recognises `tool`, `mcp`, `skill`, `plugin` and `connection`, but inventory items contain only kind, name, availability and provenance; requests add only a reason; selected output contains kind, name, provenance and reason. There is no endpoint, transport, authentication material or executable configuration in the schema. [measured] Sources: [`src/consilient/capabilities.py`](../../src/consilient/capabilities.py#L8-L45), [`src/consilient/capabilities.py`](../../src/consilient/capabilities.py#L171-L194).

The live dispatch caller runs `scripts/capability_context.py`, captures its JSON, and appends a fenced `Selected capability context` block to the task. `run_harness` writes that task into the brief; the child command is only told to read the brief. No MCP or connection argument/configuration is emitted. The focused tests assert this text injection, not a connection. [measured] Sources: [`scripts/dispatch.py`](../../scripts/dispatch.py#L1248-L1272), [`scripts/capability_context.py`](../../scripts/capability_context.py#L27-L38), [`tests/test_dispatch.py`](../../tests/test_dispatch.py#L1198-L1278).

Separately, `scripts/knowledge.py` can materialise five declared knowledge MCP sources into global Cursor, Grok and Codex configuration, but not Claude. Dispatch does not call it and the operation is not task-selective. Local configuration names show those entries installed, but installation does not prove authentication or retrieval. [measured] Sources: [`scripts/knowledge.py`](../../scripts/knowledge.py#L206-L251), local `.harness/knowledge/sources.json`.

The accepted trajectory contained **zero** `knowledge.retrieved` events and zero outbound connector events; it contained three `computer.use` events. The local connector package covers SMTP email, Twilio SMS and Playwright computer use, not the broad named SaaS catalogue evaluated above. [measured]

Consilient therefore has fail-closed capability vocabulary and optional host-level MCP configuration, but no demonstrated task-scoped connector pass-through. Sense B is **no today**. [asserted]

## What would change the verdict

A minimum killing measurement for Sense A is a fixed harmless task run under an environment with metered keys absent, with the selected account/authentication mode and the vendor plan counter captured immediately before and after. The outcome event should bind those facts to the artefact. Repeat for all four families, including a successful Claude dispatch; then demonstrate automatic selection across at least two known-headroom pools without bypassing Gate B. [asserted]

A minimum killing measurement for Sense B is a task that requests one named connection, proves dispatch emitted its endpoint/configuration without secrets, retrieves a known canary record through the child harness, and records `knowledge.retrieved` with source provenance. Inventory text or globally installed names do not satisfy it. [asserted]

Until those measurements exist, the honest product claim is: **Consilient has supervised experimental multi-CLI dispatch, with successful local evidence for three families; Hermes has broader implemented third-party credential and connector reach; neither result establishes Consilient as a reliable multi-subscription orchestrator.** [asserted]

## Reproduction and limits

- The Hermes checkout was pinned before inspection; source, provider manifests and official documentation were used instead of model-provider calls. No OAuth login, SaaS tool call, paid inference or quota debit was performed. [measured]
- `uv run --frozen --extra dev python -m pytest -q --tb=no tests/run_agent/test_codex_app_server_integration.py tests/hermes_cli/test_runtime_provider_resolution.py tests/hermes_cli/test_mcp_catalog.py tests/tools/test_mcp_oauth.py` produced **172 passed, 1 skipped**. A preliminary bare-interpreter run was discarded because missing pinned extras and MCP SDK mismatch made it an invalid environment, not a product finding. [measured]
- `python -m pytest tests/test_dispatch.py tests/test_capabilities.py tests/test_knowledge.py -q` produced **107 passed, 1 skipped** in Consilient. [measured]
- An isolated A/B suite at pinned Consilient revision `fc929d4` produced the exact same **878 passed, 3 skipped, 7 failed** before and after adding this report; the seven failures belonged to the pre-existing committed tree. The report's initially detected foreign identifiers were shortened to the pinned unique revision, after which the foreign-identifier gate and its focused invariant passed. The advertised clean 891-pass baseline could not be reproduced while unrelated claimed changes were in flight, but this report caused no test to fall. [measured]
- External SaaS and connector catalogue pages were retrieved on 2026-08-22. Counts and availability can drift; the pinned Hermes code findings do not. [measured]
- No claim above upgrades source-compatible routing into a measured charge, account access or SaaS action. [asserted]

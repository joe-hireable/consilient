# The external product bar, frozen 22 August 2026

**Correction:** the brief's request to assess ChatGPT agent as something a person can use today is
already stale: OpenAI's current help page says that ChatGPT agent is no longer available and directs
users to ChatGPT Work. [cited] ([OpenAI Help, accessed
2026-08-22](https://help.openai.com/en/articles/11752874-chatgpt-agent))

**Freeze:** this external yardstick was frozen at `2026-08-22T13:22:19Z`. [measured] It was written
without reading any file under `docs/superpowers/specs/`, and it does not evaluate Consilient or use
its proposed design as a source. [asserted] Every external source linked below was retrieved on 22
August 2026; current product documentation and papers take precedence over recollection and launch
copy. [asserted]

## Decision, ranked by consequence

**The single strongest existing product for general delegated work is ChatGPT Work.** [asserted]
Confidence in this ranking is medium because no independent product-level comparison exists and the
surface changed during this freeze. [asserted] It is the hardest whole-product bar because one
generally available surface spans
multi-hour work, browser and computer use, connected apps, local and cloud files, finished documents,
spreadsheets, presentations and sites, scheduled or event-driven work, approvals, and continuity
across web, mobile and desktop. [cited] ([OpenAI operational documentation, accessed
2026-08-22](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex); [OpenAI launch record,
accessed 2026-08-22](https://openai.com/index/chatgpt-for-your-most-ambitious-work/))

That conclusion is deliberately uncomfortable but narrow. [asserted] Microsoft Copilot Cowork is
harder to beat inside a governed Microsoft 365 tenant; Cursor is harder on always-on software work;
OpenClaw is the stronger open and inspectable always-on architecture; and none of those specialist
losses is erased by naming one overall winner. [asserted] Google Workspace Studio is the stronger
no-code Google-native workflow surface, while OpenHands Agent Canvas and GitHub Agent HQ are direct
multi-agent command-post rivals whose scope remains software-development-centred. [cited] The
strongest product objection to ChatGPT Work is that its cloud browser cannot sign in, accept
credentials or make payments, so many consequential web tasks stop for the user. [cited] The
strongest evidence objection is that OpenAI publishes no product-level, independently labelled
reliability result or verifier false-accept rate for it in the sources reviewed. [measured] Thus
ChatGPT Work is the
strongest *usable product* bar, not the strongest *public measurement* bar. [asserted]

## Method and evidence boundary

The bar is the product a person can use, not the best model score, a framework feature list or a
vendor's self-selected demonstration. [asserted] For each incumbent, this review asked four questions:
what work can it actually perform; what outcome does its maker publicly measure; what the user pays;
and what primary documentation, a paper, or a reproducible issue says fails. [asserted]

“No public evidence found” below means that the reviewed official documentation, papers, changelogs,
public evaluations and issue evidence did not demonstrate the property by the freeze time. [measured]
It does **not** mean that a closed product's unpublished implementation lacks the property. [asserted]
Feature presence, vendor measurement and independently established performance are kept separate
because they are different claims. [asserted]

## Products a person can use now

| Incumbent | What it actually does | What is publicly measured | Cost at the freeze | Documented failure or limit |
|---|---|---|---|---|
| **ChatGPT Work / Workspace Agents** | Work performs longer multi-step research and produces documents, sheets, slides, reports and sites through cloud tasks, permitted local desktop access, browser/computer use, apps, schedules and cross-device continuation. [cited] Workspace Agents add repeatable shared configurations, memory, apps/custom MCP, schedules, API and Slack deployment, with role controls. [cited] | No controlled product-level general-work result or verifier confusion matrix was found; the help pages describe usage, not accepted-outcome reliability. [measured] | Plus is US$20/month, Pro is US$100 or US$200/month, and Business Standard is US$20/user/month annually or US$25 monthly; Work eligibility and allowances are plan-controlled, and task credit use varies. [cited] | Cloud browser is limited to public pages and cannot sign in, accept credentials or make payments; sites may block it and consequential actions require confirmation. [cited] The Workspace Agent API returns HTTP 202 without a run identifier or retrievable response, and shared authentication can expose data or actions beyond an end user's own authority. [cited] |
| **Claude Code and Claude Cowork** | Claude Code operates repositories, terminals, browsers, skills and subagents, with project instructions and auto-memory; Cowork adds long-running general tasks, plans, finished office artefacts, connected services, project memory, schedules and remote or local execution. [cited] | No independently labelled Cowork outcome benchmark or verifier false-accept result was found; Anthropic documents controls and limitations rather than a product success rate. [measured] | Pro is US$20/month or US$200/year; Max 5× is US$100/month and Max 20× US$200/month; usage is shared and Cowork consumes more compute. [cited] | Chat memory does not transfer except through Cowork projects, sessions cannot be shared, local-resource work requires the desktop app to remain connected, and Cowork consumes more allocation than chat. [cited] Mobile/web Cowork is captured by the Compliance API and Team/Enterprise administrators can monitor it through OpenTelemetry, so lack of enterprise telemetry is not a current limitation. [cited] Claude Code's sandbox does not inspect TLS, native Windows sandboxing is unavailable, and some configurations fail open unless explicitly prohibited. [cited] |
| **Microsoft Copilot Cowork** | General work inside Microsoft 365: documents, spreadsheets, slides, PDFs, email, calendar, files, research, browser use and scheduled work, with pause/resume/cancel and tenant administration. [cited] | Microsoft's public launch gives vendor-run productivity/cost comparisons, not an independent accepted-outcome benchmark or verifier false-accept estimate. [cited] | A Microsoft 365 Copilot licence plus usage-based Copilot Credits; pay-as-you-go is US$0.01 per credit and task consumption varies. [cited] | It requires explicit approval before writing or taking sensitive actions involving money, personal data, other people, accounts, deletion, subscriptions, health, government or security; that is useful friction, but also means unattended completion is intentionally bounded. [cited] |
| **Google Workspace Studio** | Builds, shares and schedules Gemini-powered flows across Gmail, Calendar, Chat, Drive, Docs, Forms, Sheets and Tasks, with event, schedule or manual triggers and selected third-party actions. [cited] | Test runs and activity logs expose execution, but no independent product-level accepted-outcome result or verifier false-accept matrix was found. [measured] | Included in eligible Workspace Business and Enterprise plans; annual list prices for Business Starter, Standard and Plus are US$7, US$14 and US$22 per user/month, with Enterprise quoted and temporary promotions separate. [cited] | Flows fail on Shared Drives, shared folders and `IMPORTRANGE` sheets because files must be private to the user; test runs take real actions, third-party steps can share account data, and broader DLP for third-party services was not a current commitment. [cited] |
| **Cursor** | Coding agents in local or isolated cloud environments, with tests, browser/MCP access, repository events, PR/Slack subscriptions, schedules, isolated subagents, automation memory and a long-lived `/goal`. [cited] | CursorBench 3.2 measures ambiguous multi-file tasks from real Cursor sessions plus cost, tokens and steps; its live top score was 70.8%, with an explicit warning that small differences may be noise. [cited] It is vendor-run coding evidence, not general-product reliability or verifier β. [asserted] | Individual plans are US$20, US$60 and US$200 per month; team plans are US$40 or US$120 per user per month, with model/cloud-agent usage and spend limits layered on top. [cited] | Cloud agents have internet access and automatically run commands, creating prompt-injection and exfiltration exposure; Cursor itself introduced long-lived goals after documenting that ordinary agents could forget the objective or stop partially complete. [cited] |
| **Devin** | Cloud software work, isolated sessions, browser/computer use, parallel managed Devins, recorded resumable workflows, full event timelines, schedules, reusable playbooks and organisation knowledge derived from past sessions. [cited] | Session analytics and internal diagnosis are exposed, but no independent general-work evaluation or own-verifier false-accept matrix was found. [measured] | Free, Pro at US$20/month, Max at US$200/month, and Teams with a US$80 minimum or US$40 full seat, plus quota/on-demand consumption. [cited] | Devin's own guidance says to split complex edits into smaller isolated tasks and approve knowledge; playbooks require skill and trial-and-error, and session cost rises with complexity. [cited] |
| **Manus** | Cloud browser, files, coding and website work, persistent projects/threads, schedules, integrations and optional access to a user's computer. [cited] | No independently labelled product benchmark or verifier false-accept result was found. [measured] | Free supplies 300 daily credits; Pro starts at US$20/month for 4,000 credits or US$40 for 8,000; Team starts at US$20/seat/month, while actual task consumption varies. [cited] | Manus says it cannot predict a task's credit cost in advance; at the freeze it was also warning affected accounts of a migration that would permanently remove cloud tasks, artefacts and connector data unless users backed them up before the stated deadline. [cited] |
| **OpenHands / Agent Canvas** | Open-source software-agent platform and command-post surface over OpenHands, Claude Code, Codex, Gemini and ACP agents, with local/remote/cloud backends, concurrent sessions, schedules/webhooks and Slack/GitHub/Linear integration. [cited] | This is the incumbent that disproves the easy claim that nobody evaluates its verifier: its critic reports AUC, Best@8 selection and early stopping, later supplemented by precision/recall against merge/diff proxies. [cited] | MIT local software is US$0; hosted individual access permits ten daily conversations with provider usage charged at cost, while Enterprise is custom-priced. [cited] | The critic's production labels are sparse proxies—merge and code-survival behaviour—not independently human-labelled bad artefacts; individual sessions time out and lack persistent state, interactive breakpoints and reliable visual verification. [cited] |
| **GitHub Agent HQ / Copilot agents** | Runs Copilot, Claude and Codex asynchronously from GitHub, VS Code and mobile, preserving issue, session, pull-request, review and audit context in one coding command surface. [cited] | CodeQL, secret scanning and dependency checks validate generated changes, but no independent Agent-HQ outcome benchmark or verifier β was found. [measured] | Individual plans are US$10 Pro, US$39 Pro+ and US$100 Max monthly; Business is US$19 and Enterprise US$39 per seat/month, with AI credits and Actions minutes consumed by agent runs. [cited] | Third-party agents are preview; the cloud agent is GitHub-only, limited to one repository, branch and pull request per task, and hard-stops after 59 minutes. GitHub warns that generated code can be wrong or insecure and requires human review before merge. [cited] |

### Product sources and failure evidence

- **OpenAI:** [Work and Codex operational guide](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex), [cloud-browser limits](https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt), [scheduled-task limits](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt), [retired agent guide and risk record](https://help.openai.com/en/articles/11752874-chatgpt-agent), [Workspace Agents](https://help.openai.com/en/articles/20001143), [apps and actions](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt), [Plus pricing](https://help.openai.com/en/articles/6950777-chatgpt-plus), [Pro pricing](https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro), and [Business pricing](https://help.openai.com/en/articles/8792828-what-is-chatgpt-business) were accessed 2026-08-22. [cited]
- **Anthropic:** [Cowork guide](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork), [Claude Code operation](https://code.claude.com/docs/en/how-claude-code-works), [security](https://code.claude.com/docs/en/security), [sandbox limits](https://code.claude.com/docs/en/sandboxing), [cloud limits](https://code.claude.com/docs/en/claude-code-on-the-web), and [plan prices](https://support.claude.com/en/articles/11049762-choose-a-claude-plan) were accessed 2026-08-22. [cited]
- **Microsoft:** [Copilot Cowork user guide](https://support.microsoft.com/en-us/microsoft-365-copilot/get-started-with-cowork), [GA record](https://www.microsoft.com/en-us/microsoft-365/blog/2026/06/16/copilot-cowork-is-now-generally-available/), and [usage-based billing](https://learn.microsoft.com/en-us/microsoft-365/copilot/usage-based-billing-overview-copilot-credits) were accessed 2026-08-22. [cited]
- **Google:** [Workspace Studio operational guide](https://support.google.com/workspace-studio/answer/16444479?hl=en), [agent data-access controls](https://knowledge.workspace.google.com/admin/studio/manage-work-agent-access-to-data), and [Workspace pricing](https://workspace.google.com/pricing?hl=en-UK) were accessed 2026-08-22. [cited]
- **Cursor:** [current changelog](https://cursor.com/changelog), [CursorBench 3.2](https://cursor.com/cursorbench), [cloud-agent documentation](https://prod.cursor.com/docs/cloud-agent), [current secrets and network boundary](https://cursor.com/docs/cloud-agent/security-network), and [pricing](https://cursor.com/docs/models-and-pricing) were accessed 2026-08-22. [cited]
- **Devin:** [advanced capabilities](https://docs.devin.ai/work-with-devin/advanced-capabilities), [scheduled sessions](https://docs.devin.ai/product-guides/scheduled-sessions), [when to use Devin](https://docs.devin.ai/essential-guidelines/when-to-use-devin), [playbooks](https://docs.devin.ai/product-guides/creating-playbooks), and [self-serve billing](https://docs.devin.ai/admin/billing/self-serve) were accessed 2026-08-22. [cited]
- **Manus:** [current plan prices](https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus), [credit rules](https://help.manus.im/en/articles/11711097-what-are-the-rules-for-credits-consumption-and-how-can-i-obtain-them), [unpredictable task cost](https://help.manus.im/en/articles/13185575-is-there-a-way-to-check-how-many-credits-a-task-will-cost-before-i-begin), [computer access](https://help.manus.im/en/articles/14178443-what-is-the-my-computer-feature-capable-of), and [the live service-change notice](https://help.manus.im/en/articles/16147831-service-change-overview-what-s-happening-and-am-i-affected) were accessed 2026-08-22. [cited]
- **OpenHands:** [Agent Canvas, core repository and licence](https://github.com/All-Hands-AI/OpenHands), [pricing](https://www.openhands.dev/pricing), [usage limits](https://docs.openhands.dev/openhands/usage/essential-guidelines/when-to-use-openhands), [critic evaluation](https://www.openhands.dev/blog/20260305-learning-to-verify-ai-generated-code), [verification stack](https://www.openhands.dev/blog/20260506-the-verification-stack), [critic guide](https://docs.openhands.dev/sdk/guides/critic), and [public benchmark harnesses](https://github.com/OpenHands/benchmarks) were accessed 2026-08-22. [cited]
- **GitHub:** [third-party coding agents](https://docs.github.com/en/copilot/concepts/agents/about-third-party-coding-agents), [cloud-agent limits](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent), [risks and mitigations](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations), [responsible-use limits](https://docs.github.com/en/copilot/responsible-use/agents), and [plans](https://docs.github.com/en/enterprise-cloud@latest/copilot/get-started/plans) were accessed 2026-08-22. [cited]

## Frameworks and always-on assistants

These are real incumbents for builders, but a framework feature is not itself an end-user outcome.
[asserted] Framework scores below therefore attach to one assembled system and model stack, never to
the framework in the abstract. [asserted]

| Incumbent | Usable capability and measurement | Cost | Documented failure or limit |
|---|---|---|---|
| **AutoGen / Magentic-One** | AutoGen supplies message-passing agents, code execution, group conversations, runtimes and persistence; Magentic-One assembled a five-agent ledger-and-worker system and reported 38.0% GAIA, 32.8% WebArena and 27.7% AssistantBench for that configuration. [cited] | MIT software at US$0, excluding model and infrastructure cost. [cited] | AutoGen is now maintenance-only and directs new users to Microsoft Agent Framework; the Magentic-One paper reports inefficient actions, weak verification/navigation and model refusals that prevented fair scoring on parts of WebArena. [cited] |
| **Microsoft Agent Framework** | The active successor provides Python/.NET agents, graph workflows, checkpoints, human approval, observability, MCP/A2A and an Agent Harness with planning, todos, persistence and skills. [cited] | MIT software at US$0, excluding provider/Azure/hosting cost. [cited] | Background agents, file access and looping are experimental; a current persisted-history/handoff issue can hang or print tool arguments, and parallel approval resume can execute only the first approved call. [cited] |
| **CrewAI** | Crews provide role-based collaboration; Flows provide deterministic state, persistence, guardrails and human input. No official result isolating framework lift was found. [measured] | MIT core at US$0; hosted Basic permits 50 executions/month and two automations, while Enterprise is quoted and model/hosting costs remain separate. [cited] | Its telemetry and test scores are instrumentation rather than calibrated external truth; agents require iteration/time caps, and built-in code execution was removed in favour of external sandboxes. [cited] |
| **LangGraph / Deep Agents / Fleet** | LangGraph supplies graph state, checkpoints, interrupts and cross-thread memory; Deep Agents adds filesystem, shell, subagents, plans and writable cross-session skills; Fleet adds persistent scheduled agents, identity, credentials, permissions and approvals. [cited] | MIT core at US$0; LangSmith Developer is US$0 plus usage, Plus US$39/seat/month plus usage, and Enterprise is quoted; models cost separately. [cited] | Durable replay requires idempotent side effects and has a documented duplicate-side-effect issue after crashes; writable shared memory is explicitly a prompt-injection surface. [cited] Deep Agents' published v0.7 deltas have reward intervals spanning zero, and no Fleet quality benchmark was found. [measured] |
| **Nous Hermes Agent** | Open-source local assistant across messaging and CLI, with tools, delegation, cron, checkpoints, persistent goals, memory and automatic creation or revision of procedural skills. [cited] | MIT software at US$0, excluding chosen model/API/host cost. [cited] | Its open evaluation issue says it still relies on self-assessment and manual review; goal completion judges admit false positives without a measured rate. [cited] The default terminal backend runs as the host user, and in-process approvals/scanners are not a security boundary. [cited] |
| **OpenClaw** | Open-source local-first assistant across channels, browser, shell and tools, with cron, detached work, subagents, durable goals and default-auto scanner-gated learning from corrections and successful work. [cited] | MIT software at US$0; model, search, media, embeddings and hosting cost separately. [cited] | A durable goal is state, not a background task; sandboxing is off by default and the project defines a one-trusted-operator rather than adversarial multi-tenant boundary. [cited] Automatic learning retains bad-advice risk, and a migration caused isolated cron runs to fail in a shipped version. [cited] An independent live-deployment study observed non-owner compliance, secret disclosure, destructive action, denial of service, identity spoofing and false completion under permissive shell configurations; that establishes concrete failures, not a default-product rate. [cited] |

### Framework and always-on sources

- **AutoGen and Magentic-One:** [AutoGen repository](https://github.com/microsoft/autogen), [AutoGenBench status](https://github.com/microsoft/autogen/blob/main/python/packages/agbench/README.md), and [Magentic-One paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/Magentic-One.pdf) were accessed 2026-08-22. [cited]
- **Microsoft Agent Framework:** [repository](https://github.com/microsoft/agent-framework), [Agent Harness](https://learn.microsoft.com/en-us/agent-framework/concepts/harness), [persisted-history handoff defect](https://github.com/microsoft/agent-framework/issues/7384), and [parallel approval defect](https://github.com/microsoft/agent-framework/issues/7569) were accessed 2026-08-22. [cited]
- **CrewAI:** [repository](https://github.com/crewAIInc/crewAI), [processes](https://docs.crewai.com/en/concepts/processes), [Flows](https://docs.crewai.com/en/concepts/flows), [testing](https://docs.crewai.com/en/concepts/testing), and [pricing](https://crewai.com/pricing) were accessed 2026-08-22. [cited]
- **LangGraph family:** [LangGraph repository](https://github.com/langchain-ai/langgraph), [multi-agent guide](https://docs.langchain.com/oss/python/langchain/multi-agent), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview), [writable memory warning](https://docs.langchain.com/oss/python/deepagents/memory), [Fleet](https://docs.langchain.com/langsmith/fleet), [v0.7 evaluation](https://www.langchain.com/blog/deep-agents-v0-7), [duplicate-side-effect report](https://github.com/langchain-ai/langgraph/issues/8039), and [pricing](https://www.langchain.com/pricing) were accessed 2026-08-22. [cited]
- **Hermes:** [repository](https://github.com/NousResearch/hermes-agent), [memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/), [goals](https://hermes-agent.nousresearch.com/docs/user-guide/features/goals), [evaluation gap](https://github.com/NousResearch/hermes-agent/issues/44000), and [security boundary](https://github.com/NousResearch/hermes-agent/security) were accessed 2026-08-22. [cited]
- **OpenClaw:** [repository](https://github.com/openclaw/openclaw), [durable goals](https://docs.openclaw.ai/tools/goal), [self-learning](https://docs.openclaw.ai/tools/self-learning), [operator scopes](https://docs.openclaw.ai/gateway/operator-scopes), [cost catalogue](https://docs.openclaw.ai/reference/api-usage-costs), [security policy](https://github.com/openclaw/openclaw/blob/main/SECURITY.md), [cron migration failure](https://github.com/openclaw/openclaw/issues/108642), and the independent [*Agents of Chaos* deployment study](https://arxiv.org/abs/2602.20021) were accessed 2026-08-22. [cited]

## What public evaluations actually measure

There is no defensible single “agentic-system score”. [asserted] The strongest current public bar is
a portfolio of different fact classes: privately held expert work for ecological validity,
version-pinned computer operation for long-horizon state, and fresh domain diagnostics for coding,
research and human-facing tool use. [asserted] Public-task-only leaderboards are development
diagnostics, not sufficient evidence for a global product claim. [asserted]

### Closest to general delegated work

| Evaluation | Scope and oracle | What it establishes | What prevents it being the whole bar |
|---|---|---|---|
| **Agents' Last Exam (ALE, 2026)** | 960 expert-authored workflows and 1,490 instances across 55 digital-industry subdomains in 13 clusters, executed through GUI, CLI and files; 150 instances are public, 1,017 are private and 323 were pending verification. [cited] Private instances are 68.3% of all 1,490, or 87.1% of the 1,167 public-plus-private usable inventory; pending does not mean runnable or rolling. [algebra] Outputs receive a `[0,1]` score and strict full-pass result, with 93.2% deterministic judges and 6.8% narrow model judges. [cited] | This is the broadest reproducible public protocol found for professional, multi-tool delegated work, and its 1,017 private instances give it a materially better contamination posture than fixed public tasks. [asserted] | Runs are capped at five hours even though source work spans hours to weeks; only deterministically checkable or tightly rubricable artefacts are admitted, the 323 pending instances cannot be counted as evaluation inventory, and a June 2026 benchmark has little longitudinal drift evidence. [cited] |
| **Remote Labor Index (RLI)** | 240 real Upwork projects from 358 verified freelancers in 23 domains; three independent domain reviewers compare the AI artefact with the professionally accepted human artefact. [cited] | Private tasks and market transactions make this the strongest ecological and human-acceptance check found; current public results remain low enough to discriminate systems. [asserted] | It excludes direct client interaction, physical work and long-term consequences; manual grading is slow and costly, its US$30 generation budget shapes results, and the current leaderboard publishes no confidence interval. [cited] |
| **Workspace-Bench 1.0 (2026)** | 388 tasks across five worker profiles, 74 file types and 20,476 interdependent files, with 7,399 rubric criteria over workspaces as large as 20 GB. [cited] | It directly measures file-dependent workspace understanding and production; its reported best agent scored 68.7% against a human 80.7%, while the agent average was 47.4%. [cited] | Tasks and rubrics are public, rubric grading is not independent human acceptance, and it tests bounded workspace deliverables rather than long-term authority or real external consequences. [asserted] |
| **OSWorld 2.0 (2026)** | 108 end-to-end workflows over 31 self-hosted sites, median skilled-human time about 1.6 hours, with strict binary completion and an average 27.25 checkpoints under a 500-step cap. [cited] | It is the strongest current version-pinnable measurement of long, stateful computer operation; the owner paper's best configuration reached 20.6% strict completion and 54.8% partial score. [cited] | It remains a 108-task controlled desktop whose mix and stochasticity matter; model-based checks still contribute 11.53% of all checks, and agents can learn the self-hosted environment. [cited] |
| **GAIA2 (2026)** | 800 dynamic scenarios across ten simulated universes and eleven core apps, covering execution, search, adaptation, time and ambiguity, with state-changing tools and three runs per scenario. [cited] | It tests asynchronous events and write actions that static question-answer benchmarks omit. [asserted] | Its public leaderboard uses validation data, submission is voluntary and uncontrolled, and an official-repository issue records an unresolved reproduction problem for one reported result. [cited] |
| **AutomationBench (2026)** | 600 scored tasks across sales, marketing, operations, support, finance and HR using 47 simulated SaaS tools; deterministic final-state assertions require every assertion for a strict pass. [cited] | It gives a clean, held-out diagnostic for business API workflow execution. [asserted] | It omits user dialogue, GUI work and long-term effects, while a final-state oracle can miss harmful or wasteful trajectories. [asserted] |
| **APEX-Agents (2026)** | 480 professional-services tasks across investment banking, consulting and law, eight runs per task, binary rubric criteria and Pass@1, Pass@8 and Pass^8 with bootstrap intervals. [cited] | Its repeatability reporting exposes instability that a single pass rate hides; the paper's top Pass@8 was 40% while top Pass^8 was 13.4%. [cited] | All tasks, rubrics and gold files are public; 422 of 480 outputs are console messages rather than file deliverables, and a model family also appears as judge and contestant. [cited] |
| **TheAgentCompany** | 175 tasks in a simulated software company using GitLab, OwnCloud, Plane, RocketChat, terminal and browser, scored by checkpoints, state and some model grading. [cited] | It remains a useful cross-application workplace predecessor. [asserted] | The tasks are fixed and public, the paper used one run per task with no confidence intervals or human baseline, and automatically evaluable software-company work dominates. [cited] |
| **GDPval / GDPval-AA v2** | GDPval uses 1,320 expert tasks from 44 occupations and blind peer comparison; GDPval-AA wraps 220 public tasks in a shell/web loop and reports model-judged pairwise Elo. [cited] | Original GDPval is a strong artefact-quality oracle; the agentic wrapper diagnoses production of professional artefacts. [asserted] | Original GDPval is one-shot rather than interactive agency; the agentic prompts and gold artefacts are public, its judge is a model rather than the original occupation experts, and Elo moves with the pool. [cited] |

### Narrow diagnostics that must not be presented as general work

| Evaluation | What it measures | Known contamination, saturation or validity problem |
|---|---|---|
| **SWE-bench / Verified / Pro** | Resolving repository issues under fail-to-pass and regression tests; this is narrow software maintenance. [cited] | OpenAI audited 138 repeatedly failed Verified tasks and found 59.4% had material problem/test issues, while tested models reproduced gold information; it stopped reporting Verified. [cited] A later audit estimates about 30% of 731 public SWE-bench Pro tasks are broken and records a score rise from 23.3% to 80.3% in eight months. [cited] |
| **SWE-bench Live / SWE-rebench / MirrorCode** | Live and rebench continuously collect fresher repository issues; MirrorCode tests whole-program black-box reimplementation against visible and hidden end-to-end tests. [cited] | Freshness reduces temporal leakage but automated collection still needs task-validity audits; MirrorCode is precisely specified CLI cloning rather than messy general work and can take days and billions of tokens. [cited] |
| **Terminal-Bench 2.1** | 89 containerised terminal tasks with human solutions and tests; a strong coding, sysadmin and scientific-CLI diagnostic. [cited] | Version 2.1 repaired 28 of 89 tasks, and maintainers document timeout modification, encrypted solutions, tests smuggled into setup and agents fetching online solutions; the current bar is also approaching saturation. [cited] |
| **τ-bench / τ² / τ³** | Customer-service dialogue, policy and state-changing tool use; later versions add dual-control users, banking and linked policy documents. [cited] | An official audit fixed 53 of the original 164 tasks for wrong actions, ambiguity, impossibility and loopholes, moving airline pass rates by 14–20 points; revision and simulator model are load-bearing. [cited] |
| **WebArena / VisualWebArena / Online-Mind2Web** | Browser action on self-hosted sites, with the live successor using 300 tasks over 136 real sites and human evaluation. [cited] | Static replicas and open tasks reward site-specific optimisation; rule-based evaluation can disagree with humans, while live sites drift and human judging costs more. [cited] |
| **BrowseComp / BrowseComp-Plus** | Obscure multi-hop web research and, in Plus, retrieval over a fixed 100,000-document corpus with evidence scoring. [cited] | BrowseComp is near saturation and Anthropic found public answer leakage plus agents recognising and decrypting the evaluation; Plus is more reproducible but its fixed public corpus no longer measures live-web resilience. [cited] |
| **GAIA v1** | 466 multi-tool research questions with short normalised answers; it excludes posting, booking, uploading and other consequential write actions. [cited] | Static questions can be memorised and web evidence drifts; GAIA2, not GAIA v1, is the relevant state-changing successor. [cited] |
| **ShellBench (formerly ClawBench, 2026)** | Nineteen general-work tasks selected from a 40-task pool after an eight-model, 1,080-run audit; each task runs three times with deterministic completion, trace and behaviour scoring. [cited] | Maintainers found 47.3% of raw score variance was seed noise, 21 of 40 candidate tasks had signal-to-noise below one, and model scores moved materially within hours or after harness releases. [cited] It names reward hacking and false completion, but publishes no independent human-labelled verifier confusion matrix. [cited] |

### Benchmark sources

- **General work:** [ALE paper](https://arxiv.org/abs/2606.05405), [ALE protocol](https://github.com/rdi-berkeley/agents-last-exam), [RLI method and leaderboard](https://labs.scale.com/leaderboard/rli), [RLI paper](https://arxiv.org/abs/2510.26787), [Workspace-Bench paper](https://arxiv.org/abs/2605.03596), [Workspace-Bench protocol](https://workspace-bench.github.io/), [OSWorld 2.0 method](https://osworld-v2.xlang.ai/), [OSWorld 2.0 paper](https://arxiv.org/abs/2606.29537), [GAIA2 paper](https://arxiv.org/abs/2602.11964), [GAIA2 environment and evaluation](https://github.com/facebookresearch/meta-agents-research-environments), [AutomationBench paper](https://arxiv.org/abs/2604.18934), [AutomationBench protocol](https://github.com/zapier/AutomationBench), [APEX-Agents paper](https://arxiv.org/abs/2601.14242), [TheAgentCompany paper](https://arxiv.org/abs/2412.14161), [GDPval](https://openai.com/index/gdpval/), and [GDPval-AA method](https://artificialanalysis.ai/evaluations/gdpval-aa) were accessed 2026-08-22. [cited]
- **Coding and terminal:** [original SWE-bench paper](https://arxiv.org/abs/2310.06770), [Verified retirement audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), [Pro audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/), [SWE-bench Live](https://arxiv.org/abs/2505.23419), [SWE-rebench v2](https://arxiv.org/abs/2602.23866), [MirrorCode](https://arxiv.org/abs/2606.30182), [Terminal-Bench 2.1 paper](https://arxiv.org/abs/2601.11868), [task repair record](https://www.tbench.ai/news/terminal-bench-2-1), and [integrity incident record](https://www.tbench.ai/news/leaderboard-integrity-update) were accessed 2026-08-22. [cited]
- **Interaction, browser and research:** [τ-bench](https://arxiv.org/abs/2406.12045), [τ²-bench](https://arxiv.org/abs/2506.07982), [τ³/τ-Knowledge](https://arxiv.org/abs/2603.04370), [official τ task audit](https://taubench.com/blog/tau3-task-fixes.html), [WebArena](https://arxiv.org/abs/2307.13854), [Online-Mind2Web](https://arxiv.org/abs/2504.01382), [BrowseComp](https://openai.com/index/browsecomp/), [BrowseComp contamination audit](https://www.anthropic.com/engineering/eval-awareness-browsecomp), [BrowseComp-Plus](https://arxiv.org/abs/2508.06600), and [GAIA](https://arxiv.org/abs/2311.12983) were accessed 2026-08-22. [cited]
- **Always-on evaluation:** [ShellBench repository and protocol](https://github.com/openclaw/shellbench) was accessed 2026-08-22; the old [ClawBench URL](https://github.com/openclaw/clawbench) redirects there. [cited]

## The candidate gaps, tested rather than assumed

| Candidate claim | Verdict at the freeze | Evidence that defeats the broad claim | The narrower finding that survives |
|---|---|---|---|
| **No incumbent evaluates its own verifier.** | **False.** [measured] | OpenHands reports critic AUC, Best@8 selection, early stopping, review precision/recall and incorporation proxies, including weak and corrected results. [cited] | No sampled product publishes `P(verifier accepts | artefact independently labelled bad)` by task class, with the bad-artefact denominator, sampling method and uncertainty exposed. [measured] For closed products this is **undocumented**, not proved absent from the implementation; the public demonstration is absent. [asserted] |
| **No incumbent carries capability forward between sessions.** | **False.** [measured] | Claude project/auto-memory, ChatGPT project and Workspace-Agent memory, Cursor Automation memory, Devin knowledge/playbooks, Manus projects, Hermes skill learning, OpenClaw self-learning and writable Deep-Agent skills all carry context or procedure forward. [cited] | Independent evidence that automatic carry-forward improves held-out outcomes without regressions, poisoning or authority leakage is missing from the reviewed product evidence. [measured] This effect is undocumented in the public record, not proved absent from any implementation. [asserted] OpenHands individual-session continuity is weaker than this field. [cited] |
| **No incumbent commits to duration and returns finished work.** | **False as a capability claim.** [measured] | Work and Cowork advertise multi-hour finished artefacts; Cursor holds goals and watches PRs; Devin, Manus, Hermes, OpenClaw and Fleet schedule or resume work. [cited] | No sampled product publishes a completion-by-deadline service level tied to independently accepted output, including restarts, usage exhaustion, refusal and quarantine in the denominator. [measured] Whether closed operators enforce private guarantees is undocumented. [asserted] |
| **No incumbent makes a non-technical principal's authority undelegable.** | **Partly false and otherwise undocumented.** [measured] | Microsoft Cowork reserves listed sensitive actions for user approval; OpenAI exposes role controls and write confirmations; Claude has permission modes and permanent-delete approval; OpenClaw reserves goal mutation to its operator and exposes scoped identities. [cited] | No sampled documentation defines one authenticated human principal whose authorship an agent cannot forge across final verdicts, spend, publication and irreversible actions, then adversarially demonstrates that boundary. [measured] This is a documentation and public-proof gap, not proof that every private implementation lacks such a control. [asserted] |

The genuinely unclosed public gap is therefore not a missing feature. [asserted] It is a missing
*joined proof*: no sampled product publishes a version-pinned, independently labelled general-work
evaluation that simultaneously accounts for accepted outcomes, verifier false accepts, refusals and
quarantines, deadline reliability, cross-session learning effects, principal-authority violations,
cost and human review time. [measured] OpenHands is the transparency leader in the sample, ALE/RLI
are the strongest general outcome protocols, OpenClaw exposes the clearest durable-goal and learning
mechanics, and Microsoft exposes the clearest protected-action list; no one result joins those
classes. [asserted]

This negative finding is bounded to the named products and retrieved public record at the freeze.
[asserted] A private evaluation, a changed product or an omitted incumbent could falsify it
immediately. [asserted]

## Testable criteria for a credible “best” claim

A candidate clears this bar only if it passes every gate below; averaging a catastrophic specialist
loss into a high overall score does not count. [asserted]

1. **General accepted outcome.** [asserted] On a post-freeze private task bank spanning professional
   artefacts, software, browser/desktop work, research, business actions and recurring cross-session
   work, blinded independent judges must accept a greater proportion of candidate outputs than
   ChatGPT Work outputs under the same tool, time and money budget. [asserted] Report paired outcomes,
   exact McNemar confidence/testing for binary acceptance, bootstrap intervals for partial scores,
   and all task-level records. [asserted]

2. **No hidden domain loss.** [asserted] The candidate's multiplicity-adjusted 95% interval must
   exclude a loss greater than five percentage points in every predeclared domain against one frozen
   comparator: ChatGPT Work for professional artefacts, browser/desktop work and research; Cursor for
   software; Copilot Cowork for governed business actions; and OpenClaw for recurring cross-session
   work. [asserted] Treat task as the clustered analysis unit, aggregate three product-task runs to
   one binary result by predeclared majority, and place the overall superiority hypothesis and six
   paired domain hypotheses in one Holm family at `α = 0.05`. [asserted] The confirmatory task count
   must be fixed using a separate pilot's arm-blinded discordance rate and a published calculation or
   simulation that gives at least 90% power to the *entire conjunctive win rule* after multiplicity,
   not 90% to each test separately. [asserted] An unaffordable required count makes the claim
   inconclusive, not passed. [asserted] Five points is a decision threshold, not an empirical
   constant. [asserted]

3. **Independent verifier calibration.** [asserted] Independently label at least 300 deliberately
   flawed candidate artefacts before showing them to the system's verifier; publish the full
   confusion matrix, provenance and disagreements, and estimate `β = P(accept | genuinely bad)` by
   task class with an exact one-sided 95% interval. [asserted] Zero false accepts among 300 bad
   artefacts gives an upper bound of `1 - 0.05^(1/300) = 0.994%`; it does not prove β is zero.
   [algebra] The pass threshold is an upper bound below 1%, so a sample of 300 passes only with zero
   false accepts; any non-zero count fails unless a larger sample was fixed before labels were seen.
   [asserted]

4. **Reliable completion, not mere persistence.** [asserted] Before each run, record the promised
   deadline, success oracle and maximum spend; report accepted-and-on-time rate, p50/p95 elapsed time,
   restarts, interventions, usage exhaustion, timeouts, refusals and quarantines. [asserted] The
   candidate must beat ChatGPT Work's accepted-and-on-time rate with a 95% paired interval excluding
   zero. [asserted]

5. **Beneficial carry-forward.** [asserted] Randomise new held-out task variants between memory-on
   and memory-off arms after identical past experience, then require a positive lower 95% bound on
   accepted-outcome lift and no increase in verifier β or authority violations. [asserted]
   [PAST-Bench](https://arxiv.org/abs/2608.04003), accessed 2026-08-22, supplies a public procedural
   memory diagnostic but does not replace product-level held-out work. [cited]

6. **Principal authority as an enforced boundary.** [asserted] Use authenticated, separately held
   principal credentials and attempt at least 300 prompt-injection, non-owner, replay and confused-
   deputy attacks against each reserved action class: final truth verdict, spend, publication and
   irreversible change. [asserted] Require zero agent-authored principal events and an exact one-sided
   95% bypass-rate upper bound below 1% per class. [asserted] A prompt saying “ask first” is not the
   control being tested. [asserted]

7. **Review and economic burden.** [asserted] Publish total and accepted-outcome-normalised money,
   tokens, wall time, tool calls and principal review minutes. [asserted] The candidate must improve
   accepted outcomes while the upper 95% paired-bootstrap interval is no greater than `1.05×` the
   incumbent separately for spend per accepted outcome and principal review minutes per accepted
   outcome. [asserted] Five per cent is a decision margin, not an empirical constant. [asserted]

8. **Reproducibility and drift.** [asserted] Freeze product/model versions, prompts, tools, network
   policy, effort, budgets, task revisions and judge versions; use at least three runs per stochastic
   task or publish a predeclared reliability sample; release traces where privacy permits; and repeat
   the external bar quarterly. [asserted] Every output must expose invalid, refused, timed-out,
   quarantined and safety-stopped trials rather than deleting them from the denominator. [asserted]

The minimum public benchmark portfolio is ALE's verified private set and RLI private for delegated
outcome, Workspace-Bench for file-dependent work, OSWorld 2.0 for long stateful work, a fresh
SWE-bench Live slice plus MirrorCode for code, τ³ for human-facing policy/tool use, and
Online-Mind2Web plus BrowseComp-Plus for browser/research diagnosis. [asserted] Winning
Terminal-Bench, BrowseComp or SWE-bench alone cannot support a general-product claim because each is
narrow, public, substantially saturated, gameable or all four. [cited]

## Proposed pre-registration; no register change made

**`EXP-100 — Does the candidate beat ChatGPT Work on independently accepted general delegated work
without buying the result with review burden, unsafe authority or an uncalibrated verifier?`**
[asserted] At `2026-08-22T12:54:36Z`, a repository search excluding the prohibited product-spec
directory found no `EXP-100`; the experiment register was inside the searched set, so this id was
verified free there without reading the specs. [measured]

- **Arms:** frozen candidate and ChatGPT Work versions on every task; for the six domain floors, use
  Work for professional artefacts, browser/desktop and research, Cursor for software, Copilot Cowork
  for governed business actions, and OpenClaw for recurring cross-session work. [asserted]
- **Bank and unit:** first run a separate 120-task planning pilot, twenty tasks in each domain, and
  exclude it from confirmation. [asserted] Use its arm-blinded discordance rate to run and publish a
  calculation or simulation that gives at least 90% power to the complete Holm-adjusted conjunctive
  win rule, then freeze that required count of new private tasks per domain before any confirmatory
  output is unblinded. [asserted] Task
  is the analysis unit; three independently randomised runs per product-task pair become one binary
  accepted-and-on-time result by majority, with ties impossible. [asserted]
- **Truth:** deterministic end-state checks where they measure the real requirement; otherwise three
  blinded domain reviewers, with adjudication and all disagreement retained. [asserted]
- **Audits:** a separately labelled pool of 300 bad artefacts for verifier calibration and at least
  300 adversarial attempts per reserved-action class. [asserted]
- **Primary endpoint:** independently accepted and on-time completion; verifier β, authority bypass,
  review minutes, spend and refusal/quarantine rates are co-primary safety and burden endpoints, not
  optional diagnostics. [asserted]
- **Analysis and win rule fixed before launch:** use task-cluster majority outcomes and place the
  overall two-sided exact McNemar superiority test plus six paired non-inferiority tests in one Holm
  family at `α = 0.05`; publish all estimates and simultaneous or multiplicity-adjusted intervals.
  [asserted] Pass all eight criteria, reject every hypothesis required by the conjunctive rule, and
  suffer no safety stop. [asserted]
- **Stopping rule fixed before launch:** stop the planning stage after exactly 120 pilot tasks; if the
  published power calculation cannot fit the confirmatory task count under a proposed £5,000
  external-spend cap, stop inconclusive before confirmation. [asserted] That cap requires the
  principal's explicit approval before launch and is not approved by this proposal. [asserted]
  Otherwise execute
  every powered confirmatory run and audit attempt, stopping only on the first unauthorised reserved
  action, disclosure of a secret/private corpus, or that hard spend cap. [asserted] A safety stop is a
  failure; a spend stop is inconclusive; timeouts, refusals, quarantines and missing outputs remain in
  their assigned arm's denominator. [asserted] There is no efficacy early stop. [asserted]

## Search record, exclusions and falsifiers

The search covered every named incumbent in the brief; product documentation, security and pricing;
2026 changelogs and successors; open-source repositories, licences and current issues; public
benchmark papers and owner protocols; benchmark audits for contamination, task repair, reward
hacking and saturation; and explicit negative searches for verifier false-accept measurement,
cross-session learning, deadlines and principal authority. [asserted]

Current official help and documentation were preferred. [asserted] Launch pages were used only to
establish a launch/date or a capability corroborated by operational documentation; opaque vendor
benchmarks were labelled as such rather than treated as independent evidence. [asserted] Issue
reports establish a documented occurrence, not a universal failure rate. [asserted] Model benchmark
scores were not silently transferred to the product surface that happened to use the model.
[asserted]

The principal exclusions were physical-world agents, consumer chat without action tools, pure model
leaderboards, unretrievable claims, and products whose relevance could not exceed one of the named
incumbents. [asserted] Google Workspace Studio, GitHub Agent HQ, OpenHands Agent Canvas, OpenClaw,
Microsoft Agent Framework, Microsoft Copilot Cowork, Agents' Last Exam, RLI, Workspace-Bench,
OSWorld 2.0, GAIA2, AutomationBench, APEX-Agents and ShellBench were added because their 2026
evidence materially moved the bar. [asserted]

The strongest falsifier is straightforward: a retrievable incumbent report that joins independent
general-task truth, task-class verifier β, deadline accounting, controlled cross-session lift,
principal-bound authority, cost and review burden for a versioned product. [asserted] Finding one
would require replacing the “joined proof” gap and re-running the strongest-product decision rather
than defending this freeze. [asserted]

## Plain answer

ChatGPT Work is the single existing general-work product that would be hardest to beat at this
freeze. [asserted] It wins the breadth and usability decision; OpenHands wins the
sample's transparency decision, OpenClaw wins the open always-on architecture decision, and Copilot
Cowork wins the governed-Microsoft-365 decision. [asserted] A future “best globally” claim is not
credible until it beats Work on independently accepted private work, does not lose the specialist
floors, and passes the verifier, time, learning, authority and burden gates above. [asserted]

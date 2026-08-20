# Orchestration dependencies: what would decide adoption

**Date:** 20 August 2026
**Status:** assessment only; no dependency was added and no candidate was run. [measured]
**Governs:** dependency experiments under ADR-0036; it does not authorise adoption. [asserted]

The brief names ADR-0048, but no `0048*.md` decision file exists in this clone at
`f65d96d`. [measured] This assessment therefore applies the rule quoted in the brief — a
capability must be fully usable for free, locally and without contacting a server we operate —
without claiming to have read the absent ADR. [asserted]

## Decision

**Adopt none of these today.** [asserted] LangSmith fails the free, local and account-free
filter on its own documentation; Microsoft AutoGen is in maintenance mode and tells new users
to migrate elsewhere. [cited] Those are documentary disqualifiers, not uncertain performance
claims, so experiments would not make either eligible. [asserted]

The first experiment worth running is durable execution, against Temporal and Prefect and the
current trajectory-only baseline. [asserted] The trajectory is durable evidence, not durable
execution: it can rebuild a SQLite projection, but it has no persisted runnable-work queue,
activity heartbeat, retry ownership or resumption protocol. [measured] A process can die after an
external side effect and before its outcome event, and the current record alone cannot decide
whether to repeat that side effect. [asserted]

OpenTelemetry is the most plausible low-coupling adoption, but only as a projection of the
trajectory. [asserted] MCP and ACP are protocols for different directions — tools into an agent
and a client controlling an agent respectively — and neither is an orchestration engine.
[cited] Pydantic AI and DSPy have no present product seam to replace because Consilient currently
delegates model interaction to whole coding agents. [measured]

The broad agent frameworks are the trap the brief warned about. LangGraph, Google ADK, CrewAI,
AG2 and Microsoft Agent Framework each bring an execution loop and state model; adopting one as
the coordinator would replace the authority boundary, trajectory semantics and adapter composition
on which the β claim rests. [cited] EXP-58 gives them a way to disprove that judgement by composing
*below* those boundaries and removing enough code to pay for the dependency. [asserted]

## Filters and maturity snapshot

Licence text was read from each repository's licence file, not a badge. [cited] Release dates and
open-issue counts below were read from issue-only repository queries on 20 August 2026; the
LangSmith and Prefect counts were refreshed at 23:17 BST. [cited] Open issues are a volatile
workload indicator, not a quality score, and counts are not comparable across projects' triage
policies. [asserted] “Offline” means the assessed core can complete its role with local models and
local storage, no hosted account, and outbound telemetry disabled where applicable. [asserted]

| Candidate | Licence and offline filter | Control posture and what it would replace here | Maturity observed 20 Aug 2026 | Disposition |
|---|---|---|---|---|
| **LangGraph** | MIT for the open-source graph runtime. Local execution and checkpointers need no LangSmith account. The production standalone Agent Server is separately licensed, requires `LANGGRAPH_CLOUD_LICENSE_KEY`, and normally reports licence/usage data to `beacon.langchain.com`. [cited] | Framework: owns graph execution, graph state and checkpoints. It would replace the scheduler/retry state and could become a second trajectory authority. [cited][asserted] | 461 open issues; `1.2.6`–`1.2.11` shipped from 18 Jun to 11 Aug, with further checkpoint/SDK releases through 19 Aug. v1 dropped Python 3.9 and deprecated prebuilt agent/state APIs. [cited] | EXP-58 for boundary fit and EXP-59 for crash recovery. [asserted] |
| **LangSmith** | MIT client SDK; hosted product is proprietary. Self-hosting requires an Enterprise plan and licence key, and ordinary self-hosting requires licence/billing egress. [cited] | Hosted observability, evaluation and deployment platform. It would replace local observability and, if Deployment were used, own the agent runtime. [cited][asserted] | SDK: 113 open issues; `v0.10.13`–`v0.11.1` shipped from 30 Jul to 19 Aug. The proprietary platform has no equivalent public issue/release record. [cited] | **Reject without experiment:** fails the free local-core rule. [asserted] |
| **Google ADK** | Apache-2.0. It runs locally with Ollama/LiteLLM and local session stores; the LiteLLM path must exclude compromised PyPI versions `1.82.7` and `1.82.8`. [cited] | Framework: `Agent`, workflow, runner, events and sessions own the agent and orchestration loop. It would replace the coordinator and adapter-owned model loop. [cited][asserted] | 298 open issues; parallel 1.x and 2.x trains shipped weekly or faster in Jul–Aug. ADK 2.0 replaced the executor with a workflow runtime and changed events, sessions and custom-execution behaviour. [cited] | EXP-58. The supply-chain incident raises the adoption bar but is not a permanent rejection. [asserted] |
| **CrewAI** | MIT. Local Ollama use needs no AMP account, but anonymous telemetry is enabled unless `CREWAI_DISABLE_TELEMETRY=true`. [cited] | Framework: Crews and Flows own agents, tasks, delegation, routing, mutable state and checkpoints. It would replace the coordinator; role collaboration adds no consilience unless evidence classes differ. [cited][asserted] | 115 open issues; `1.15.13`–`1.15.17` shipped 7–20 Aug. Its migration guide records moved imports, changed parameters, manager requirements and changed resume/fork semantics. [cited] | EXP-58, with outbound networking denied. [asserted] |
| **Microsoft AutoGen** | Code is MIT; documentation and other repository material are CC-BY-4.0. Local model clients exist. [cited] | Framework: Core and AgentChat own messaging, runtimes, teams and tool loops. It would replace the layer ADR-0001 says Consilient must sit above. [cited][asserted] | 558 open issues; last release `python-v0.7.5` on 30 Sep 2025. Upstream says maintenance mode and directs new users to Microsoft Agent Framework; v0.2→v0.4 was already a replacement API. [cited] | **Reject without experiment:** execution cannot reverse upstream's maintenance decision. [asserted] |
| **AG2** | AG2 additions are Apache-2.0; inherited AutoGen v0.2.35 code remains MIT, so NOTICE and file history determine obligations. Local providers are supported. [cited] | Framework: v1 `Agent` owns model/tool execution and `Network` owns a hub, channels, write-ahead log and audit trail. It duplicates the coordinator and trajectory. [cited][asserted] | 14 open issues; `v0.14.0`–`v1.0.2` shipped 26 Jun–15 Aug. v1 moved Classic to another repository and changed imports, agents and orchestration. [cited] | EXP-58; copied files would also need per-file licence checks. [asserted] |
| **Microsoft Agent Framework** | MIT. Its official Python provider supports local Ollama without authentication. [cited] | Framework: combines AutoGen-style agents with graph workflows, sessions, checkpointing and multi-agent orchestration. It would replace the coordinator, workflow state and parts of adapter control. [cited][asserted] | 489 open issues; Python reached `1.0.0` on 2 Apr and `1.14.0` on 14 Aug. Core is stable, while several connectors and APIs remain preview/experimental. [cited] | EXP-58. This is the supported successor that an AutoGen-only survey would miss. [asserted] |
| **Pydantic AI** | MIT. Local Ollama and test models need no account. Logfire is optional and sends nothing unless installed, configured and instrumented. [cited] | Agent framework, not merely validation: `Agent.run` owns model calls, tools, retries and output. It could replace a future native model-I/O loop; Pydantic Core is the narrower comparator. [cited][asserted] | 519 open issues; latest `v2.32.1` shipped 20 Aug, the fifth release in seven published days. v2 changed default tool side effects, provider selection, persistence, events and instrumentation. [cited] | EXP-60; no current product job. [asserted] |
| **DSPy** | MIT. Local Ollama/SGLang use needs no account; the ordinary 3.3 provider path still uses LiteLLM. [cited] | Programming/optimisation framework: owns LM calls, signatures, modules, caches and optimiser-generated prompts. It would replace future prompt/model-I/O code, not coding-agent adapters. [cited][asserted] | 316 open issues; `3.1.3`–`3.3.0` shipped Feb–Aug. v3 removed retrievers, aliases and deprecated clients; 3.3's typed LM boundary remains opt-in and experimental. [cited] | EXP-61; typed output alone is not enough to justify an optimiser framework. [asserted] |
| **Temporal** | Server and Python SDK are MIT and self-host locally without an account. [cited] | Durable execution runtime: its event history is the execution authority and replays deterministic workflows; external agents must run as activities. It could replace scheduling, retries and recovery, but cannot be a transparent second authority beside JSONL. [cited][asserted] | Server: 550 open issues; Python SDK: 83. SDK `1.28.0`–`1.31.0` shipped Jun–Jul; server upgrades and workflow-code changes have explicit compatibility constraints. [cited] | EXP-59. Strongest functional fit; adoption requires resolving which history is authoritative. [asserted] |
| **Prefect** | Apache-2.0. Local SQLite/PostgreSQL server and UI need no Prefect account. [cited] | Workflow framework/control plane: owns flow/task scheduling, retries and state. It can restart at task boundaries using persisted results, but does not reconstruct arbitrary Python execution through deterministic history replay. [cited][asserted] | 785 open issues; stable `3.8.0`–`3.8.3` shipped 23 Jul–13 Aug amid nightly releases. The 2→3 migration changed async execution, final states, caching, futures and server compatibility. [cited] | EXP-59. It must beat both Temporal and the no-dependency baseline, not merely work. [asserted] |
| **OpenTelemetry GenAI semantic conventions** | Apache-2.0; definitions and local collectors require no account. [cited] | Specification, not runtime. It should project committed events and must never replace or feed decisions into the trajectory. [cited][asserted] | 137 open issues; no tag, release or schema URL. Status is **Development**, which OTel defines as unsuitable for production. Current MCP fields still describe session/initialisation concepts removed by MCP `2026-07-28`. [cited] | EXP-62. Pinning can test fit; adoption waits for a tagged, aligned schema. [asserted] |
| **MCP** | New code/spec contributions are Apache-2.0, unconsented older work remains MIT, and non-spec documentation is CC-BY-4.0. Local stdio needs no account. [cited] | Protocol for exposing tools/resources/prompts *to* an agent. It must remain below coordinator validation and `append()`; it does not control an external coding agent. [cited][asserted] | 93 open issues; stable specifications shipped from Nov 2024 to Jul 2026. `2026-07-28` removed sessions/initialisation and moved Tasks to an extension; Python SDK 2.0 has not implemented that extension. [cited] | EXP-63 for an authority-preserving tool boundary. [asserted] |
| **Agent Client Protocol** | Apache-2.0; local newline-framed JSON-RPC over stdio needs no account unless the chosen agent does. [cited] | Protocol for a client controlling a coding agent while that agent retains its internal loop. It can replace vendor-specific transport code, not `Ticket`, `Outcome` or policy. [cited][asserted] | Core: 9 open issues; v1/schema releases shipped monthly in Jul–Aug while v2 remained draft. Python SDK `0.12.1` shipped 16 Aug and had 3 open issues, but its last explicit schema bump was v1.19 while core reached v1.21 on 20 Aug. [cited] | EXP-64. The existing 233-line Cursor ACP adapter proves feasibility; the SDK must prove parity and code deletion. [measured][asserted] |

### Downstream user-repository check

A bounded GitHub code search over the brief's named candidates excluded each candidate's own
repository, sampled the five best-matching exact imports and then read the matching files at
pinned commits. [cited] This is presence evidence, not a dependent count, production-quality
claim or representative sample. [asserted]

- The strongest execution evidence was
  [Julep's Temporal worker](https://github.com/julep-ai/julep/blob/fc74d079a18c8124b2627ca4717f5a9c269267db/julep/execution/worker.py):
  it registers deterministic workflows and a substantial activity set in the product's execution
  package. [cited] [MLflow ships an AG2 tracing integration](https://github.com/mlflow/mlflow/blob/d37342a6987db4c13b9337aeb192fb2afaee5046/mlflow/ag2/__init__.py),
  and [gptme ships an ACP agent implementation](https://github.com/gptme/gptme/blob/b36c05f418670df38ca1b956f4d041bb333cd2cf/gptme/acp/agent.py)
  with session, permission, tool and protocol handling. [cited] These are reusable integration
  modules in established projects, stronger evidence than an example application. [asserted]
- Public application evidence exists for
  [LangGraph in Tavily Chat](https://github.com/tavily-ai/tavily-chat/blob/5e7e4ac63738fef8ed2ecd4d51873b64dd82620d/backend/agent.py),
  [Prefect in Data For Good's ODIS pipeline](https://github.com/dataforgoodfr/13_odis/blob/494ac5726bbc5b4e7586e168a1c358fb77a131a2/prefect_flow/flow.py), and
  [Pydantic AI in a MongoDB RAG agent](https://github.com/coleam00/MongoDB-RAG-Agent/blob/b048eeab220e43b2b8f8c97508e4d6d2c134a468/src/agent.py).
  [cited] They exercise graphs/checkpoints, flow/task orchestration and typed agent/tool state
  respectively, but one repository each cannot establish migration safety. [cited][asserted]
- The sampled
  [ADK payment agent](https://github.com/Zen7-Labs/Zen7-Payment-Agent/blob/a1546be076c14d1f270b1109c1e055fd53b685c8/a2a_server/agent.py),
  [local CrewAI example](https://github.com/heaversm/crew-llamafile/blob/c70270aaa62f453978608cd21da425f8f5f13056/ollama-app.py) and
  [DSPy knowledge-graph script](https://github.com/chrisammon3000/dspy-neo4j-knowledge-graph/blob/2856b2dfe81fc801601c2a9c4b439429a4562a98/run.py)
  are single-purpose applications rather than evidence of a maintained integration boundary.
  [cited][asserted] The sampled
  [OpenTelemetry consumer](https://github.com/traceloop/opentelemetry-mcp-server/blob/92ff4caf5302e3779c2050a3857b240dfc16324b/src/opentelemetry_mcp/models.py)
  contains compatibility aliases across changing GenAI attribute names, which supports treating
  the Development conventions as migration risk rather than a stable product schema. [cited][asserted]

Microsoft Agent Framework was outside that downstream sample because it was not named in the
brief; its maturity case here remains upstream release history. [asserted] LangSmith and AutoGen's
documentary rejections do not depend on downstream popularity. [asserted]

## The three plausible gains

### 1. Durable execution

The JSONL trajectory survives a crash and the SQLite state can be deleted and rebuilt from it.
[measured] That proves provenance and replay; it does not resume an activity that was in flight,
detect a dead worker, fence a retry or prevent a duplicated external side effect. [measured]

Temporal directly addresses that gap through durable event history and deterministic workflow
replay. [cited] That is also its architectural cost: Temporal history would become execution
authority. JSONL can remain an audit projection, or Consilient can retain JSONL authority and reject
Temporal; pretending both independently drive recovery creates a dual-write problem. [asserted]

Prefect supplies scheduling, retries and persisted task results but not the same crash-replay
guarantee. [cited] LangGraph checkpoints graph supersteps only after the coordinator is expressed as
a LangGraph graph. [cited] EXP-59 tests all three against the exact side-effect window rather than
accepting a “durable” label. [asserted]

### 2. Observability

OpenTelemetry has common GenAI names for providers, models, agents, workflows, tools and errors.
[cited] It does not standardise Consilient's authority grant, evidence class, lease epoch, human
verdict, verifier version, β denominator, canonical event digest or append position. [measured]
Making it canonical would discard the provenance the project exists to preserve. [asserted]

The viable direction is one-way: canonical event → OTel span, using standard attributes where they
fit and a `consilient.*` event reference for project-only facts. [asserted] EXP-62 requires
deletion/regeneration, content-off export and fixed local queries. Current Development status and
MCP-version drift remain documentary co-gates even if the mapping works. [cited][asserted]

LangSmith is not the open-source shortcut to that result. Its SDK is open; the platform that stores,
queries and displays traces is hosted or Enterprise-licensed. [cited]

### 3. Typed model I/O

`events.py` validates `dict[str, Any]` through explicit field checks, and adapters normalise
terminal outcomes manually. [measured] That is data validation, not model I/O: coding agents own
their model/tool loops and Consilient consumes outcomes. [measured]

Pydantic AI would therefore add an agent loop before the project has shown it needs one.
[asserted] Pydantic Core may eventually replace hand-written structural validation more narrowly;
EXP-60 makes Pydantic AI beat both explicit validation and Core at a provisional native-model seam.
[asserted]

DSPy's genuine proposition is optimisation against a metric, not typed decoding in isolation.
[cited] EXP-61 tests held-out β and α. DSPy introduces no different class of facts by itself; any
gain must survive a mechanically disjoint held-out set. [asserted]

## Protocol direction and authority

MCP's current protocol is stateless and loses in-flight stdio requests when a server dies. [cited]
It is a candidate for bounded tool access, not long-running adapter orchestration. EXP-63 treats
route choice, dispatch, verdict submission and direct trajectory writes as hostile calls.
[asserted]

ACP already controls Cursor in EXP-05 through
`docs/10-research/experiments/exp05/adapter_cursor_acp.py`. [measured] The adoption question is
narrow: can the official Python SDK replace enough custom JSON-RPC/session code while preserving
the measured `Outcome`, permission and fail-closed behaviour? [asserted] EXP-64 tests stable v1;
v2 remains draft and the Python SDK's schema lag is measured rather than assumed harmless.
[cited][asserted]

## Registered decision path

| Experiment | Candidates | Different class of facts introduced | Adoption decision |
|---|---|---|---|
| EXP-58 | LangGraph, ADK, CrewAI, AG2, Microsoft Agent Framework | Candidate code under denied networking and hostile authority fixtures. [asserted] | Can a framework remain subordinate to the coordinator and remove material code? [asserted] |
| EXP-59 | Temporal, Prefect, conditionally LangGraph | Killed processes plus independently scored side-effect artefacts. [asserted] | Does an engine supply recovery the trajectory lacks without an unresolved second authority? [asserted] |
| EXP-60 | Pydantic AI, Pydantic Core, explicit validation | Frozen valid/invalid provider responses. [asserted] | Does the agent framework beat narrower validation at a future native seam? [asserted] |
| EXP-61 | DSPy | Held-out verifier outcomes on a disjoint mutant/control corpus. [asserted] | Does optimisation reduce β without buying it through α, cost or leakage? [asserted] |
| EXP-62 | OpenTelemetry GenAI | Real event projections, deletion/regeneration and fixed local queries. [asserted] | Is the standard a useful, disposable projection? [asserted] |
| EXP-63 | MCP | Malformed and hostile protocol calls plus resulting authoritative artefacts. [asserted] | Can MCP expose tools without becoming a bypass? [asserted] |
| EXP-64 | ACP | Protocol fixtures plus matched existing/custom-SDK Cursor artefacts. [asserted] | Should the official SDK replace the measured custom client? [asserted] |

LangSmith and AutoGen are rejected for fixed documentary reasons and do not receive experiments.
[asserted] Ruflo is not repeated: consensus is already EXP-52 and signed trajectory identity is
EXP-53. [measured]

Run order should be EXP-59, EXP-64, EXP-62, EXP-63, EXP-60, EXP-61, then EXP-58. [asserted]
This puts the measured product gap first, follows with narrow component seams, and leaves wholesale
framework substitution until those seams have had a chance to win. [asserted]

Every experiment uses only this repository, deterministic fixtures where possible, a throwaway
environment, pinned versions, and an outbound-network-denied phase after installation. [asserted]
No experiment authorises a permanent dependency, an external repository, a secret, a hosted
account or a change to routing gates. [asserted]

## Primary sources read

- Candidate repositories, licences, releases and issue-only API queries:
  [LangGraph](https://github.com/langchain-ai/langgraph),
  [LangSmith SDK](https://github.com/langchain-ai/langsmith-sdk),
  [ADK](https://github.com/google/adk-python),
  [CrewAI](https://github.com/crewAIInc/crewAI),
  [AutoGen](https://github.com/microsoft/autogen),
  [AG2](https://github.com/ag2ai/ag2),
  [Microsoft Agent Framework](https://github.com/microsoft/agent-framework),
  [Pydantic AI](https://github.com/pydantic/pydantic-ai),
  [DSPy](https://github.com/stanfordnlp/dspy),
  [Temporal server](https://github.com/temporalio/temporal),
  [Temporal Python SDK](https://github.com/temporalio/sdk-python),
  [Prefect](https://github.com/PrefectHQ/prefect),
  [OTel GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai),
  [MCP](https://github.com/modelcontextprotocol/modelcontextprotocol),
  [ACP](https://github.com/agentclientprotocol/agent-client-protocol), and
  [ACP Python SDK](https://github.com/agentclientprotocol/python-sdk). [cited]
- Control, offline, stability and migration documentation:
  [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview),
  [LangGraph standalone server](https://docs.langchain.com/langsmith/deploy-standalone-server),
  [LangSmith self-hosting](https://docs.langchain.com/langsmith/self-hosted),
  [ADK local models](https://google.github.io/adk-docs/agents/models/litellm/),
  [CrewAI telemetry](https://docs.crewai.com/en/telemetry),
  [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/),
  [Pydantic AI version policy](https://pydantic.dev/docs/ai/project/version-policy/),
  [Pydantic AI Logfire](https://pydantic.dev/docs/ai/integrations/logfire/),
  [DSPy local models](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md),
  [Temporal workflow history](https://docs.temporal.io/workflow-execution/event),
  [Temporal local server](https://docs.temporal.io/develop/run-a-development-server),
  [Prefect crash detection](https://docs.prefect.io/v3/advanced/detect-zombie-flows),
  [OTel GenAI status](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/README.md),
  [OTel document status](https://opentelemetry.io/docs/specs/otel/document-status/),
  [MCP `2026-07-28` changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog),
  [ACP Python library](https://agentclientprotocol.com/libraries/python), and
  [ACP v2 migration](https://agentclientprotocol.com/protocol/v2/migration). [cited]
- Supply-chain fact:
  [LiteLLM's incident notice](https://docs.litellm.ai/blog/security-update-march-2026). [cited]

## Reasoning, reversal and falsifiers

**Reasoning.** Selecting the broadest or most mature-looking framework from documentation would
test feature breadth and popularity, not whether the dependency preserves the authority/evidence
boundary or removes more code than it adds. [asserted] The experiments make those boundaries
executable before any dependency request. [asserted]

**Reversal:** revert this assessment commit and its experiment registrations; no runtime or
dependency state needs undoing. [asserted]

**Falsifiers:** a candidate passes its stopping rule; an applicable licence/offline fact is
superseded; the local baseline proves every crash cut with no duplicate or lost side effect; or the
OTel conventions stabilise with a tagged schema and native fields for the missing provenance.
[asserted] Each falsifies only its corresponding conclusion; none upgrades another candidate by
analogy or multi-agent agreement. [asserted]

# Orchestration dependencies: what would decide adoption

**Date:** 20 August 2026  
**Status:** assessment only; no candidate was installed or run. [measured]  
**Decision:** adopt none before the registered stopping rule for its actual role fires. [asserted]

## Evidence boundary

This assessment reads the candidates as possible dependencies under ADR-0036, not as products to
imitate. [asserted] The brief names ADR-0048, but no `0048*.md` decision file exists in this clone
at `f65d96d`. [measured] I therefore apply the rule quoted in the brief — a capability must be
fully usable for free, locally and without contacting an operated service — without claiming to
have read the absent ADR. [asserted]

The task permits changes only to this file and the experiment register, so the newly read primary
sources could not be added to `bibliography.md`. [measured] External observations below are
therefore conservatively `[asserted]`, with direct source links for reproduction, rather than
being promoted to `[cited]`. [asserted] MCP and ACP directionality is already backed by `[FULL]`
entries in the repository bibliography. [cited]

GitHub issue counts, releases and downstream code-search samples are a 20 August snapshot.
[asserted] Issue counts are workload indicators, not quality scores; rapid releases may indicate
maintenance or churn. [asserted] The downstream search sampled five best-match repositories per
import and proves public use only, not production reliability or representativeness. [asserted]

## Outcome

**Run durable execution first.** [asserted] The JSONL trajectory is durable evidence and can
rebuild SQLite, but it is not a work queue: it has no activity heartbeat, retry fencing or fact
that distinguishes “the adapter never ran” from “it performed an external side effect and died
before recording the outcome”. [measured][asserted] EXP-58 tests exactly that crash window against
LangGraph, Temporal, Prefect and a dependency-free baseline. [asserted]

**Do not adopt a broad agent framework merely to obtain scheduling.** [asserted] LangGraph,
Google ADK, CrewAI and AG2 each own an execution loop and state model. [asserted] There is no
existing product orchestration loop to replace yet; the repository has research runners and
adapters, while Stage 3 has only authorised the product loop to be built. [measured] Using one of
these frameworks as coordinator would replace the *planned* authority boundary and duplicate the
trajectory unless EXP-59 proves it can remain subordinate and delete at least 30% of local
coordinator code. [asserted]

**Treat OpenTelemetry as a disposable projection, MCP as tool ingress and ACP as agent control.**
[cited][asserted] None is an orchestration engine. [asserted] Pydantic AI and DSPy have no present
product seam because Consilient delegates model/tool loops to whole coding agents; EXP-60 and
EXP-64 become relevant only to a native model path. [measured][asserted]

## Candidate screen

“Offline” here means that the assessed core role completes with local storage and local models or
deterministic fixtures, requires no hosted account, and emits no outbound telemetry after documented
opt-outs are applied. [asserted]

| Candidate | Licence and offline screen | What controls the loop/state; what it would replace | Maturity evidence observed | Disposition |
|---|---|---|---|---|
| **LangGraph** | Standard MIT. The open-source graph, SQLite checkpointer and local execution do not require LangSmith. [asserted] | Framework: graph runtime, graph state and checkpoints. Used as coordinator, it would replace the planned scheduler/retry state and risk becoming a second trajectory authority. [asserted] | 461 open issues; `1.2.6`–`1.2.11` shipped from 18 Jun–11 Aug, with more checkpoint/SDK releases through 19 Aug. v1 dropped Python 3.9 and deprecated prebuilt agent/state APIs. Public import samples include `tavily-ai/tavily-chat`, but the best matches were mostly agent demos. [asserted] | EXP-59 for containment; EXP-58 for durability. [asserted] |
| **LangSmith** | SDK is MIT, but the free product is hosted; self-hosting requires an Enterprise plan and licence key. [asserted] | Hosted observability/evaluation/deployment platform. It would replace local observability and, if Deployment were used, own the agent runtime. [asserted] | SDK had 115 open issues and twelve releases from `v0.10.9` on 20 Jul to `v0.11.1` on 19 Aug. Public import samples existed, but they do not make the platform open-source or account-free. [asserted] | **Reject without experiment:** fails the documentary offline/free filter. [asserted] |
| **Google ADK** | Apache-2.0. Local/self-hosted models are available through LiteLLM; that path inherits LiteLLM, whose `1.82.7` and `1.82.8` packages were compromised in March 2026. [asserted] | Framework: `Agent`, Workflow, Runner, events and sessions own the agent and orchestration loop. It would replace the planned coordinator and adapter-owned model loop. [asserted] | 298 open issues; concurrent 1.x and 2.x releases shipped through Jul–Aug. The 2.0 guide declares breaking agent, event and session changes, including session incompatibility with older 1.x before 1.28. Best-match downstream samples were mostly ADK/MCP demos. [asserted] | EXP-59. The supply-chain incident raises the bar but is not a permanent rejection. [asserted] |
| **CrewAI** | Standard MIT. Local models work; anonymous telemetry is enabled unless `OTEL_SDK_DISABLED=true`, while detailed prompt sharing requires explicit `share_crew`. [asserted] | Framework: Crews and Flows own agents, tasks, delegation and flow state. It would replace the planned coordinator; role collaboration adds no consilience unless evidence classes differ. [asserted] | 115 open issues; eleven stable `1.15.x` releases shipped 26 Jul–20 Aug after 1.0 in Oct 2025. Downstream samples such as `heaversm/crew-llamafile` demonstrate local use, but the top samples were small applications. [asserted] | EXP-59 with outbound networking denied. [asserted] |
| **Microsoft AutoGen** | Code is MIT; documentation and other repository material are CC-BY-4.0. Local model clients exist. [asserted] | Framework: Core and AgentChat own messaging, runtimes, group chat and tool loops. It would replace the layer ADR-0001 says Consilient must sit above. [asserted] | 558 open issues; last release `python-v0.7.5` on 30 Sep 2025. Upstream says maintenance mode, accepts no new features and directs new users to Microsoft Agent Framework; migration from v0.2 was already non-trivial. Azure public samples still use it. [asserted] | **Reject without experiment:** execution cannot reverse upstream's maintenance decision. [asserted] |
| **AG2** | Mixed provenance: inherited AutoGen portions remain MIT; AG2 additions are Apache-2.0; file history determines terms. Local providers are supported. [asserted] | Framework: v1 `Agent` owns model/tool execution and `Network` owns the hub, channels, write-ahead log and audit trail. It duplicates the planned coordinator and trajectory. [asserted] | 14 open issues; `v0.13.2`–`v1.0.2` shipped 29 May–15 Aug. v1 is not a drop-in Classic upgrade. Imports appear in `mlflow/mlflow`, `assafelovic/gpt-researcher` and `ag-ui-protocol/ag-ui`, stronger downstream evidence than most agent-framework samples. [asserted] | EXP-59; adopted files would also need per-file licence checks. [asserted] |
| **Pydantic AI** | Standard MIT. Local OpenAI-compatible and Ollama endpoints are supported. Logfire is optional and sends nothing unless installed, configured and instrumented. [asserted] | Agent framework, not merely validation: `Agent.run` owns model calls, tools, retries and output. It could replace a future native model-I/O loop; Pydantic Core is the narrower library comparator. [asserted] | 519 open issues; eight v1/v2 releases landed 12–20 Aug. v2 became stable 23 Jun with explicit persistence removal and changed tool side-effect order. Downstream samples were real small applications rather than major infrastructure. [asserted] | EXP-60; no current product job. [asserted] |
| **DSPy** | Standard MIT. Local models work, ordinarily through LiteLLM. [asserted] | Programming/optimisation framework: owns LM calls, signatures, modules, caches and optimiser-generated prompts. It would replace future prompt/model-I/O code, not coding-agent adapters. [asserted] | 316 open issues; stable versions moved from `3.1.0` in Jan to `3.3.0` on 3 Aug. v3 removed retrievers, aliases and deprecated clients and dropped Python 3.9. Best-match downstream samples were small DSPy projects. [asserted] | EXP-60 for typed transport; EXP-64 for the optimiser's actual β/α value. [asserted] |
| **Temporal** | Server and Python SDK are standard MIT and self-host locally. [asserted] | Durable workflow engine plus SDK: owns workflow history, scheduling and retries while external agents can remain adapter activities. It would replace hand-built recovery, not the evidence trajectory. [asserted] | Server had 550 open issues; Python SDK 83 and six minor lines Apr–Jul, reaching `1.31.0`. Workflow code must remain deterministic and old histories must replay. Downstream samples include `julep-ai/julep` as well as Temporal's community agents. [asserted] | EXP-58; strongest candidate for the strongest missing capability. [asserted] |
| **Prefect** | Apache-2.0. Local server/UI are self-hosted; Prefect Cloud is optional. [asserted] | Workflow framework/control plane: owns flow/task scheduling, retries and state. Agent calls can remain tasks, but Prefect's database becomes another operational store. [asserted] | 786 open issues; stable `3.8.2` and `3.8.3` shipped 7 and 13 Aug amid daily development releases. The project crossed the breaking 2→3 boundary in Sep 2024. Downstream samples include civic-data flows but gave weaker production evidence than Temporal's Julep use. [asserted] | EXP-58; it must beat the no-dependency baseline. [asserted] |
| **OpenTelemetry GenAI semantic conventions** | Apache-2.0; collectors/exporters run locally. [asserted] | Standard plus libraries, not a runtime. It should project committed events, never replace or feed decisions into the trajectory. [asserted] | GenAI conventions moved to a new repository, had 137 open issues, no tagged release and declared agent/MCP conventions `Development`; schema URL remained `TODO`. Public constant-use samples were sparse and included TraceLoop's MCP server. [asserted] | EXP-61; compatible is not adoptable until a tagged schema exists. [asserted] |
| **MCP** | New code/spec contributions are Apache-2.0, unconsented older contributions remain MIT, and non-spec docs are CC-BY-4.0. Local stdio is supported. [asserted] | Protocol/library for exposing tools, resources and prompts *to* an agent. It must remain below coordinator validation and `append()`. [cited][asserted] | 93 open issues; dated stable specifications shipped Mar, Jun and Nov 2025 and Jul 2026. Public samples were plentiful but mostly small MCP servers; file-level licence provenance matters during transition. [asserted] | EXP-62 for an authority-preserving tool boundary. [asserted] |
| **ACP** | Apache-2.0; local JSON-RPC over stdio. [asserted] | Protocol/library for a client controlling a coding agent while the agent retains its internal loop. It can replace vendor-specific transport code, not `Ticket`, `Outcome` or policy. [cited][asserted] | 9 open issues; v1/schema releases shipped roughly monthly in Jul–Aug while v2 remained alpha. Downstream imports appear in AG2, `gptme/gptme` and `modelscope/ms-agent`; this is meaningful cross-project implementation evidence. [asserted] | EXP-63; the existing hand-written Cursor ACP adapter proves feasibility only. [measured][asserted] |

## What each dependency class could actually buy

### Durable execution

The current trajectory proves provenance and replay; it does not automatically resume an activity,
detect a dead worker or prevent a duplicated external effect across the unrecorded crash window.
[measured][asserted] Temporal and Prefect address that execution problem. [asserted] LangGraph
checkpoints graph supersteps, but only after the coordinator has been expressed as a LangGraph
graph. [asserted]

The rejected alternative is to call JSONL replay “durable execution” and add ad hoc retries.
[asserted] That conflates a record with a scheduler. [asserted] EXP-58 can instead show either
that the baseline is enough or that one engine earns its stores, processes and packages.
[asserted]

### Observability

OpenTelemetry has common GenAI names for providers, models, agents, workflows, tools and errors.
[asserted] It does not currently express Consilient's authority grant, evidence class, lease epoch,
human verdict, verifier version, β denominator, canonical event digest or append position.
[measured] Making it canonical would discard the provenance the project exists to preserve.
[asserted]

The viable direction is one-way: canonical event → OTel span, using standard attributes where they
fit and a `consilient.*` event reference for project-only facts. [asserted] EXP-61 requires deletion
and regeneration, content-off export and eight fixed queries before adoption. [asserted]

### Typed model I/O

`events.py` validates `dict[str, Any]` through explicit field checks, and adapters normalise
terminal outcomes manually. [measured] That is data validation, not model I/O: coding agents own
their model/tool loops and Consilient consumes outcomes. [measured]

Pydantic AI would therefore add an agent loop before the project has shown it needs one.
[asserted] EXP-60 makes the candidate beat explicit validation on 120 pinned valid, streamed and
invalid responses. [asserted] DSPy's distinctive claim is optimisation against a metric, so
EXP-64 separately tests held-out β and α; typed signatures alone cannot justify it. [asserted]

## Decision map

| Experiment | Candidates | Different class of facts | Fixed adoption question |
|---|---|---|---|
| **EXP-58** | LangGraph, Temporal, Prefect, trajectory-only baseline | Killed process groups plus an independent side-effect oracle. [asserted] | Does an engine survive all crash windows without displacing JSONL, and remove at least 30% of recovery code if the baseline also passes? [asserted] |
| **EXP-59** | LangGraph, ADK, CrewAI, AG2; Microsoft Agent Framework as an extra successor control | Candidate code under hostile authority fixtures and denied networking. [asserted] | Can a framework match all canonical events and delete 30% of coordinator code without adding authority? [asserted] |
| **EXP-60** | Pydantic AI, DSPy typed path, explicit-validation baseline | 120 frozen provider responses rather than framework examples. [asserted] | Does either correct a validation defect without a false reject, authority transfer or trajectory mismatch? [asserted] |
| **EXP-61** | OpenTelemetry GenAI | Real event projections, deletion/regeneration and fixed local queries. [asserted] | Is the standard a useful content-off projection, with a tagged schema as a documentary co-gate? [asserted] |
| **EXP-62** | MCP SDK, minimal JSON-RPC baseline | Malformed and hostile protocol calls observed through canonical events. [asserted] | Does MCP remove at least 30% of protocol code without creating a coordinator bypass? [asserted] |
| **EXP-63** | ACP SDK, hand-written ACP baseline | Frozen transcripts plus one admitted real local ACP backend. [asserted] | Does the SDK remove 30% of parser/session code while preserving outcomes and fail-closed behaviour? [asserted] |
| **EXP-64** | DSPy optimiser, frozen-prompt baseline | Held-out mutant/control verifier outcomes. [asserted] | Does optimisation lower β by ≥10 points without raising α by >5 points or leaking the hold-out? [asserted] |

Ruflo is not repeated: consensus is already tested by EXP-52 and signed trajectory identity by
EXP-53. [measured]

## Rejections that legitimately need no run

**LangSmith:** the SDK's MIT licence does not make the hosted product open source; the documented
self-hosted path requires Enterprise and a licence key. [asserted] The offline/free condition is
binary and documentary, so a benchmark would only waste a run. [asserted]

**Microsoft AutoGen:** its maintainer-declared maintenance mode and successor direction are support
facts, not uncertain runtime behaviour. [asserted] A local test cannot make it an appropriate new
long-lived dependency. [asserted]

No other candidate is rejected solely for popularity, issue count, release velocity or the
quality of its downstream sample. [asserted] Those observations set migration and maintenance
risk; the registered experiments decide technical adoption. [asserted]

## Primary sources read

Licence files, release pages, migration notes and GitHub issue/search APIs were read for:
[LangGraph](https://github.com/langchain-ai/langgraph),
[LangSmith SDK](https://github.com/langchain-ai/langsmith-sdk),
[Google ADK](https://github.com/google/adk-python),
[CrewAI](https://github.com/crewAIInc/crewAI),
[AutoGen](https://github.com/microsoft/autogen),
[AG2](https://github.com/ag2ai/ag2),
[Pydantic AI](https://github.com/pydantic/pydantic-ai),
[DSPy](https://github.com/stanfordnlp/dspy),
[Temporal server](https://github.com/temporalio/temporal),
[Temporal Python SDK](https://github.com/temporalio/sdk-python),
[Prefect](https://github.com/PrefectHQ/prefect),
[OTel GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai),
[MCP](https://github.com/modelcontextprotocol/modelcontextprotocol), and
[ACP](https://github.com/agentclientprotocol/agent-client-protocol). [asserted]

Role, offline and breakage details were checked against:
[LangGraph persistence](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint),
[LangGraph v1 migration](https://docs.langchain.com/oss/python/migrate/langgraph-v1),
[LangSmith self-hosting](https://docs.langchain.com/langsmith/self-hosted),
[LangSmith pricing](https://docs.langchain.com/langsmith/pricing-faq),
[ADK local models](https://google.github.io/adk-docs/agents/models/litellm/),
[Pydantic AI output](https://ai.pydantic.dev/output/),
[Pydantic AI Logfire](https://ai.pydantic.dev/logfire/),
[Pydantic AI changelog](https://ai.pydantic.dev/changelog/),
[DSPy setup](https://dspy.ai/getting-started/installation/),
[Temporal documentation](https://docs.temporal.io/),
[OTel GenAI status](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/README.md),
[MCP specification](https://modelcontextprotocol.io/specification/2026-07-28), and
[ACP versioning](https://github.com/agentclientprotocol/agent-client-protocol#versioning).
[asserted]

Downstream samples named above came from exact-import GitHub code searches with candidate
repositories excluded. [asserted] They are examples, not endorsement or an adoption count.
[asserted]

## Reasoning, reversal and falsifiers

**Reasoning.** The option not taken was to select the broadest or most mature-looking framework
from documentation and integrate it. [asserted] That would measure feature breadth and marketing,
not whether the dependency preserves the authority/evidence boundary or removes more code than it
adds. [asserted] The experiments make the boundary and the deletion threshold executable before
any dependency request. [asserted]

**Reversal:** `git revert <commit-that-added-this-assessment>` removes this assessment and the
registrations; no runtime or dependency state needs undoing. [asserted]

**Falsifiers:** a candidate passes its stopping rule; an applicable licence/offline fact above is
superseded; the local baseline proves every EXP-58 crash cut with no duplicate or lost side effect;
or the OTel conventions stabilise with a tagged schema and native fields for the project-only
provenance now missing. [asserted] Each falsifies only its corresponding conclusion; none upgrades
another candidate by analogy or multi-agent agreement. [asserted]
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
open-issue counts below were read from issue-only repository queries on 20 August 2026. [cited]
Open issues are a volatile workload indicator, not a quality score, and counts are not comparable
across projects' triage policies. [asserted] “Offline” means the assessed core can complete its
role with local models and local storage, no hosted account, and outbound telemetry disabled where
applicable. [asserted]

| Candidate | Licence and offline filter | Control posture and what it would replace here | Maturity observed 20 Aug 2026 | Disposition |
|---|---|---|---|---|
| **LangGraph** | Standard MIT; the open-source graph and checkpointers run without LangSmith. [cited] | Framework: owns graph execution, graph state and checkpoints. It would replace the planned scheduler/retry state and could become a second trajectory authority. [cited][asserted] | 461 open issues; `1.2.6`–`1.2.11` shipped from 18 Jun to 11 Aug, with further checkpoint/SDK releases through 19 Aug. v1 was largely backwards-compatible but dropped Python 3.9 and deprecated prebuilt agent/state APIs. [cited] | EXP-58 for boundary fit and EXP-59 for crash recovery. [asserted] |
| **LangSmith** | The SDK is MIT, but the product's free tier is hosted; self-hosting requires an Enterprise plan and licence key. [cited] | Hosted observability, evaluation and deployment platform. It would replace local observability with a licensed platform and, if Deployment were used, own the agent runtime. [cited][asserted] | SDK: 115 open issues and twelve releases from `v0.10.9` on 20 Jul to `v0.11.1` on 19 Aug. The platform itself has no public source/release history equivalent to inspect. [cited] | **Reject without experiment:** fails the free local-core rule. [asserted] |
| **Google ADK** | Apache-2.0, no rider. It runs locally and can use local/self-hosted models through LiteLLM; that path adds LiteLLM, whose `1.82.7` and `1.82.8` PyPI packages were compromised in March 2026. [cited] | Framework: its `Agent`, workflow, runner, event model and session schema own the agent and orchestration loop. It would replace both the coordinator and adapter-owned model loop. [cited][asserted] | 298 open issues; concurrent 1.x and 2.x release trains shipped repeatedly in Jul–Aug. The 2.0 README declares breaking agent API, event-model and session-schema changes, with new sessions incompatible with 1.x before 1.28. [cited] | EXP-58. The supply-chain incident raises the adoption bar but is not a permanent rejection. [asserted] |
| **CrewAI** | Standard MIT. Local models are supported; anonymous telemetry is enabled unless explicitly disabled. [cited] | Framework: Crews and Flows own agents, tasks, flow state, delegation and orchestration. It would replace the coordinator; role-based collaboration also conflicts with the different-class rule unless evidence differs. [cited][asserted] | 115 open issues; eleven stable releases from `1.15.7` on 26 Jul to `1.15.17` on 20 Aug. Its migration guide records changed imports, defaults and structured-output behaviour. [cited] | EXP-58, with outbound network denied so “offline” is tested rather than inferred. [asserted] |
| **Microsoft AutoGen** | Code is MIT; documentation and other repository content are CC-BY-4.0. [cited] It can use local model clients, but that does not cure its support status. [asserted] | Framework: Core and AgentChat own message passing, runtimes, group chat and tool loops. It would replace the layer ADR-0001 says Consilient must sit above. [cited][asserted] | 558 open issues; last release `python-v0.7.5` on 30 Sep 2025. The project is maintenance-only, accepts no new features and directs new users to Microsoft Agent Framework; migration from v0.2 was already non-trivial. [cited] | **Reject without experiment:** a local benchmark cannot turn a maintenance-only project into a supported new dependency. [asserted] |
| **AG2** | Mixed provenance: inherited AutoGen portions remain MIT and AG2 additions are Apache-2.0; NOTICE and file history determine the applicable terms. [cited] Fully local providers are available. [cited] | Framework: v1 `Agent` owns the model/tool loop and `Network` owns a hub, typed channels, write-ahead log and audit trail. That duplicates the coordinator and trajectory. [cited][asserted] | 14 open issues; `v0.13.2`–`v1.0.2` shipped from 29 May to 15 Aug. v1 is not a drop-in upgrade from AG2 Classic: imports, agent model and orchestration changed. [cited] | EXP-58. Any copied component would also require a per-file licence check. [asserted] |
| **Microsoft Agent Framework** | Standard MIT. Its official Python provider supports local Ollama without authentication. [cited] | Framework: explicitly combines AutoGen-style agents with graph workflows, sessions, checkpointing and multi-agent orchestration. It would replace the coordinator, workflow state and parts of adapter control. [cited][asserted] | 489 open issues; Python reached `1.0.0` on 2 Apr and `1.14.0` on 14 Aug. Core is stable, but several connectors remain preview and release notes still contain breaking changes for experimental APIs. [cited] | EXP-58. This is the supported successor that an AutoGen-only survey would miss. [asserted] |
| **Pydantic AI** | Standard MIT. Local OpenAI-compatible and Ollama endpoints are supported. Logfire is optional; nothing is sent unless it is installed, configured and instrumentation is enabled. [cited] | Agent framework, not merely a validator: `Agent.run` owns model calls, tools, validation retries and output. It could replace a future native model-I/O loop; Pydantic Core alone is the lower-level alternative. [cited][asserted] | 519 open issues; eight v1/v2 releases landed from 12–20 Aug. v2 became stable on 23 Jun and contains explicit breaking and behavioural changes; the project supplies a detailed upgrade guide. [cited] | EXP-60, blocked until a native model-I/O seam exists. [asserted] |
| **DSPy** | Standard MIT. It can use local models, but its ordinary provider layer is LiteLLM. [cited] | Programming/optimisation framework: owns LM calls, signatures, modules, caches and optimiser-generated prompts. It would replace future prompt/model-I/O code, not current coding-agent adapters. [cited][asserted] | 316 open issues; stable releases moved from `3.1.0` in Jan to `3.3.0` on 3 Aug. v3 removed retrievers, old aliases and deprecated clients and dropped Python 3.9; the 3.3 typed LM path remains experimental. [cited] | EXP-61; typed output alone is not enough to justify an optimiser framework. [asserted] |
| **Temporal** | Server and Python SDK are standard MIT and self-host locally. [cited] | Durable workflow engine plus SDK: owns workflow history, retries and scheduling while external agent calls can remain activities behind the adapter contract. It would replace hand-built recovery, not the evidence trajectory. [cited][asserted] | Server: 550 open issues; Python SDK: 83. The SDK shipped six minor lines from Apr–Jul and reached `1.31.0`; workflow code must remain deterministic and old histories must replay, making versioning a real maintenance obligation. [cited] | EXP-59. Strongest candidate for the strongest missing capability. [asserted] |
| **Prefect** | Apache-2.0, no rider. A local server and UI are fully self-hosted; Prefect Cloud is optional. [cited] | Workflow framework/control plane: owns flow/task scheduling, retries and state. Agent calls could remain ordinary tasks, but Prefect's database would become another operational state store. [cited][asserted] | 786 open issues; stable `3.8.2` and `3.8.3` shipped 7 and 13 Aug amid daily development releases. The 2→3 migration changed async execution, caching, futures and same-major server compatibility. [cited] | EXP-59. It must beat both Temporal and the no-dependency baseline, not merely work. [asserted] |
| **OpenTelemetry GenAI semantic conventions** | Apache-2.0, no rider, local collectors/exporters. [cited] | Standard plus libraries: gives control and should project spans/metrics from the trajectory, not replace it. [asserted] | The GenAI conventions moved to a new repository, have 137 open issues, no tagged releases and a `TODO` schema URL; prior core GenAI fields were deprecated during the move. [cited] | EXP-62. Eligible only as a pinned projection once a tagged schema exists. [asserted] |
| **MCP** | In transition: new code/specification contributions are Apache-2.0, unconsented older contributions remain MIT, and non-specification docs are CC-BY-4.0. [cited] Fully local stdio is supported. [cited] | Protocol/library boundary for exposing tools, resources and prompts *to* an agent. It does not control the coding agent and must not bypass the coordinator or `append()`. [cited][asserted] | 93 open protocol issues; dated stable specifications shipped in Mar, Jun and Nov 2025 and Jul 2026. Python SDK 2.0 is a breaking rewrite and does not yet implement the tasks extension. [cited] | EXP-63 for an authority-preserving façade. It is not an alternative to ACP. [asserted] |
| **Agent Client Protocol** | Apache-2.0, no rider, local JSON-RPC over stdio. [cited] | Protocol/library boundary: the client controls a coding agent while the agent retains its internal loop. It can replace vendor-specific direct CLI control where an agent implements ACP. [cited][asserted] | 9 open protocol issues; stable v1/schema releases shipped roughly monthly in Jul–Aug, with `v1.7.0` and schema `v1.21.0` on 20 Aug while v2 remained draft/alpha. The Python SDK is still 0.x. [cited] | EXP-64. The existing 233-line Cursor ACP adapter proves feasibility, not lower maintenance cost. [measured][asserted] |

## The three plausible gains

### 1. Durable execution

The JSONL trajectory survives a crash and the SQLite state can be deleted and rebuilt from it.
[measured] That proves provenance and replay; it does not resume an activity that was in flight,
detect a dead worker, fence a retry or prevent a duplicated external side effect. [measured]
Temporal and Prefect solve those execution concerns; LangGraph checkpoints graph supersteps, but
only after the coordinator is expressed as a LangGraph graph. [cited]

The rejected alternative is to call the trajectory “durable execution” and build retries around
it without testing the side-effect window. [asserted] EXP-59 can show that the baseline is enough,
or that a workflow engine earns its operational cost. [asserted]

### 2. Observability

OpenTelemetry has useful common names for provider, requested model, agent, workflow, tool and
error spans. [cited] It does not standardise Consilient's decision-critical fields: evidence
class, authority grant, lease epoch, human verdict, verifier version, β denominator, append
position or canonical event digest. [measured] Making OpenTelemetry the canonical schema would
discard the provenance the project exists to preserve. [asserted]

The viable shape is one-way: canonical event → OTel span carrying standard attributes where they
fit and a digest/reference back to the event for everything else. [asserted] EXP-62 measures
whether enough of the schema maps to make that interoperability useful without creating a second
authority. [asserted]

LangSmith is not the open-source shortcut to that result. Its SDK is open; the platform that stores,
queries and displays the traces is hosted or Enterprise-licensed. [cited]

### 3. Typed model I/O

`events.py` currently validates `dict[str, Any]` through hand-written field checks, and adapter
outcomes are normalised manually. [measured] That is typed data validation, but it is not model
I/O: coding agents own their model/tool loops and Consilient consumes terminal outcomes. [measured]

Pydantic AI would therefore add an agent loop where none is currently missing. [asserted]
Pydantic Core may eventually replace hand-written structural validation more narrowly; EXP-60
includes it as the honest baseline so Pydantic AI must beat the library rather than manual code
alone. [asserted]

DSPy's genuine proposition is optimisation against a metric, not typed decoding in isolation.
[cited] EXP-61 therefore tests held-out β and α. If optimisation does not improve verifier outcomes
without worsening false rejection or leaking the evaluation set, the framework has no current job.
[asserted]

## Protocol direction and authority

MCP's 2026-07-28 protocol is stateless and removes server-initiated sampling, elicitation and roots
requests on new-protocol connections; the Python SDK serves old and new clients, but its tasks
extension is not in 2.0. [cited] That makes it a candidate for bounded tools, not long-running
adapter orchestration. EXP-63 treats route choice, dispatch, verdict submission and direct
trajectory writes as hostile calls. [asserted]

ACP already controls Cursor in EXP-05 through
`docs/10-research/experiments/exp05/adapter_cursor_acp.py`. [measured] The adoption question is now
narrow: can the official Python SDK replace enough custom JSON-RPC/session code while preserving
the measured `Outcome`, permission and fail-closed behaviour? [asserted] ACP v2 is still draft and
recommends dual v1/v2 support, so EXP-64 tests stable v1 only. [cited]

## Registered decision path

| Experiment | Candidates | Different class of facts introduced | Adoption decision |
|---|---|---|---|
| EXP-58 | LangGraph, ADK, CrewAI, AG2, Microsoft Agent Framework | Candidate code running under denied network and authority probes, rather than vendor architecture claims. [asserted] | Can any framework remain subordinate to the coordinator and remove material code? [asserted] |
| EXP-59 | Temporal, Prefect, conditionally LangGraph | Killed/restarted processes plus independently scored side-effect artefacts. [asserted] | Does a workflow engine supply recovery the trajectory lacks? [asserted] |
| EXP-60 | Pydantic AI, Pydantic Core baseline | Mutated valid/invalid outputs and observed retry/validation behaviour. [asserted] | Does the agent framework beat a validation library at a future native seam? [asserted] |
| EXP-61 | DSPy | Held-out verifier outcomes on the existing mutant/control corpus. [asserted] | Does optimisation reduce β without buying it through α, cost or leakage? [asserted] |
| EXP-62 | OpenTelemetry GenAI | A loss audit over real trajectory events and local exported spans. [asserted] | Is a standard projection useful and disposable? [asserted] |
| EXP-63 | MCP | Malformed and hostile protocol calls plus resulting authoritative artefacts. [asserted] | Can MCP expose tools without becoming a bypass? [asserted] |
| EXP-64 | ACP | Protocol-state fixtures plus matched existing/custom-SDK Cursor artefacts. [asserted] | Should the official SDK replace the experimental custom client? [asserted] |

LangSmith and AutoGen are rejected for fixed documentary reasons and do not receive experiments.
[asserted] Ruflo is not repeated here: its consensus mechanism is already EXP-52 and its valuable
signed-identity idea is already EXP-53. [measured]

Run order should be EXP-59, EXP-64, EXP-62, EXP-63, EXP-60, EXP-61, then EXP-58. [asserted]
This puts the measured product gap first, follows with the narrowest likely code deletion, and
leaves wholesale framework substitution until component seams have had a chance to win. [asserted]

Every experiment uses only this repository, deterministic fixtures where possible, a throwaway
environment, pinned versions, and an outbound-network-denied phase after installation. [asserted]
No experiment authorises a permanent dependency, an external repository, a secret, a hosted
account or a change to routing gates. [asserted]

## Primary sources read

- Candidate licence files and repository release/issue pages:
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
  [MCP](https://github.com/modelcontextprotocol/modelcontextprotocol), and
  [ACP](https://github.com/agentclientprotocol/agent-client-protocol). [cited]
- Control, offline and migration documentation:
  [LangGraph data and telemetry](https://docs.langchain.com/langsmith/data-storage-and-privacy),
  [LangSmith self-hosting](https://docs.langchain.com/langsmith/self-hosted),
  [ADK local models](https://adk.dev/agents/models/ollama/),
  [CrewAI telemetry](https://docs.crewai.com/en/telemetry),
  [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/),
  [Microsoft Agent Framework Ollama provider](https://learn.microsoft.com/en-us/agent-framework/agents/providers/ollama),
  [Pydantic AI version policy](https://pydantic.dev/docs/ai/project/version-policy/),
  [Pydantic AI Logfire](https://pydantic.dev/docs/ai/integrations/logfire/),
  [DSPy local models](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md),
  [Temporal local server](https://docs.temporal.io/develop/run-a-development-server),
  [Prefect self-hosted networking](https://docs.prefect.io/v3/advanced/configure-network-access),
  [OTel GenAI repository](https://github.com/open-telemetry/semantic-conventions-genai),
  [MCP Python SDK v2](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0),
  [ACP v2 draft](https://agentclientprotocol.com/announcements/acp-v2-draft), and
  [ACP v2 migration](https://agentclientprotocol.com/protocol/v2/migration). [cited]
- Supply-chain fact:
  [LiteLLM's incident notice](https://docs.litellm.ai/blog/security-update-march-2026). [cited]

## Reasoning, reversal and falsifiers

**Reasoning.** The option not taken was to select the most mature-looking framework from
documentation and integrate it. [asserted] That would test popularity and feature breadth, not
whether the dependency preserves the project's authority and evidence boundaries or removes more
code than it adds. [asserted] The registered experiments make those boundaries executable before
any product dependency is requested. [asserted]

**Reversal:** `git revert <commit-that-added-this-assessment>` removes this assessment and the
seven registrations; no runtime or dependency state needs undoing. [asserted]

**Falsifiers:** a candidate passes its stopping rule; a licence or offline reading above is
superseded by the applicable component's actual terms; the current orchestrator gains and proves
crash resumption with no duplicate side effects; or the OTel conventions stabilise with native
fields for decision provenance now missing. [asserted] Any one changes the corresponding decision;
none licenses upgrading the others by analogy. [asserted]

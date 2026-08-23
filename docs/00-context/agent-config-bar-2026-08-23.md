# Agent configurations, skills and MCPs: external bar frozen before catalogue adaptation

**Correction to the dispatch brief.** Superpowers 6.3.0 is installed in the principal's per-user
Codex plugin cache, not vendored in this repository: the tracked `.agents/skills/` tree contains only
Consilient-native skills. The brief also misapplies a stale iid beta formula to squad size: beta
bounds independently shippable candidate exposure, not worker headcount. ADR-0077 defines a future
wired router's dependence-robust `n_max = floor(epsilon / beta_upper)` policy; the logarithmic
expression is only an iid diagnostic, and the current unwired helper refuses because human-labelled
beta is unestimated. At EXP-47's mutation `beta_upper = 0.334582` and `epsilon <= 0.40`, the
conditional robust ceiling is **at most** one, not exactly one for every such ceiling; a tighter
ceiling can admit zero. [measured] [algebra]

**Frozen:** 2026-08-23T11:07:58Z. This is a source survey and design yardstick, not an adoption
decision. No package was installed, no account was opened, no credential was used, and no metered
API was called. [measured]

**Scope assumption:** "no account" means that the component and its qualifying function can be
obtained and run locally without signup. A public repository does not qualify merely because its
source is visible if the relevant execution path still requires a hosted account, API key or
metered call. A browser driver remains account-free even though a particular target website may
independently require login; credentials for such a target are outside this bar. [asserted]

## Decision this bar makes

**The single best existing agent configuration is Superpowers 6.3.0.** It is the hardest coherent
workflow baseline to beat because one permissively licensed, cross-harness collection joins
requirements clarification, planning, test-first implementation, systematic debugging, worktree
isolation, review and verification. Its prose is not an independent fact source: it becomes
capability-bearing only when the host actually produces tests, builds, diffs or review artefacts.
[cited] [asserted]

OpenHands Extensions is the stronger catalogue and selector prior art; Microsoft Playwright MCP is
the strongest qualifying MCP capability; and direct harness use of the already available NumPy and
SciPy, plus bounded keyless retrieval from primary data services, is the strongest scientific/data
path. None belongs in Consilient's native judgement layer, and no whole upstream catalogue clears
the licence, credential, provenance and fail-closed requirements unchanged. [measured] [asserted]

## 1. Agent role and skill collections

Every linked source in this section was retrieved on **2026-08-23**. Source identities are shortened
to twelve hexadecimal characters where shown. Pinned repository identities freeze inspected code;
web documentation and issue states are dated observations rather than archived copies and must be
rechecked before adoption. [measured]

| Candidate | Licence and account boundary | What it really does | Documented failure boundary | Consilient consequence and adoption work |
|---|---|---|---|---|
| [Superpowers 6.3.0](https://github.com/obra/superpowers/tree/v6.3.0) | [MIT](https://github.com/obra/superpowers/blob/v6.3.0/LICENSE). The skills make no provider call; the chosen host may use a local model or its own separately governed provider. [cited] | A composable development workflow covering brainstorming, plans, TDD, debugging, worktrees, review and verification. It is **procedurally capability-bearing through host tools**, not an executor or fact source by itself. [cited] | The README records Hermes losing bootstrap instructions after context compaction, and [Junie can install the plugin yet expose no skills](https://github.com/obra/superpowers/issues/1822). Those failures show that discovery and retained activation cannot be inferred from installation. [cited] | Strongest configuration baseline. Pin and content-review only the required skills; map every tool to the existing local capability allowlist; disable optional remote visual telemetry; preserve test/build/diff output as `[measured]`. Do not import its parallel-agent default without a named different fact class, bounded scope and comparative test. [asserted] |
| [Anthropic Agent Skills](https://github.com/anthropics/skills) | There is no qualifying repository-wide licence: examples such as [webapp-testing are Apache-2.0](https://github.com/anthropics/skills/blob/3b3fad96af16/skills/webapp-testing/LICENSE.txt), while document skills such as [DOCX carry restrictive source-available terms](https://github.com/anthropics/skills/blob/3b3fad96af16/skills/docx/LICENSE.txt). Files are publicly cloneable; using Claude-hosted execution requires a separate Anthropic account. [cited] | `SKILL.md` plus scripts and resources. Script-backed subsets such as local Playwright testing are **capability-bearing**; guidance-only skills are prompts. [cited] | The [repository disclaimer](https://github.com/anthropics/skills/blob/3b3fad96af16/README.md) calls the skills demonstrations, says production behaviour can differ and requires independent testing for critical use. Mixed licence and dependency terms make wholesale adoption unsafe. [cited] | Never vendor the tree. Review licence, scripts, dependencies, network and credentials per skill; admit only a pinned permissive, credential-free subset. Keep the adopted-component refusal of restrictively licensed document skills. [asserted] |
| [Claude Code plugin ecosystem](https://github.com/anthropics/claude-code/tree/45bdfa96ca41/.claude-plugin) | The containing repository is [All Rights Reserved](https://github.com/anthropics/claude-code/blob/45bdfa96ca41/LICENSE.md), and Claude Code execution requires an Anthropic or third-party cloud-provider account. It therefore fails both the permissive-licence and no-account boundaries as a whole. [cited] | Plugins can bundle skills, agents, hooks, MCP and LSP servers. Individual components may be capability-bearing, but the marketplace is a distribution mechanism, not evidence. [cited] | Official guidance says plugins can execute arbitrary code with the user's privileges and Anthropic cannot verify bundled software; it also documents an offline update failure that can erase the cached clone unless retention is enabled. Sources: [plugin guidance](https://code.claude.com/docs/en/discover-plugins) and [offline failure](https://code.claude.com/docs/en/plugin-marketplaces). [cited] | Exclude the ecosystem as an adoption unit. Its schema is prior art only; any independently licensed public plugin starts a fresh per-component licence, dependency, credential and behaviour review. [asserted] |
| [Ruflo / claude-flow](https://github.com/ruvnet/ruflo/tree/3c99b1c84a25) | [MIT](https://github.com/ruvnet/ruflo/blob/3c99b1c84a25/LICENSE). Manifests are account-free source material; provider-backed execution paths that request a key do not qualify for this bar. [cited] | A large set of Markdown roles, declared capabilities, hooks and topology/configuration machinery. Sampled agent manifests are principally **prompts in costume**: a capability name in front matter is not proof that a child ran or produced an artefact. [cited] | [`coordination_orchestrate` records work without executing it](https://github.com/ruvnet/ruflo/issues/2140); [Windows headless workers have returned success with empty output](https://github.com/ruvnet/ruflo/issues/1446); and [`agent_execute` can require a second provider credential](https://github.com/ruvnet/ruflo/issues/2356). [cited] | Reference only. Do not import personas, topology or capability declarations. A role qualifies only when a named local tool or source produces an independently checkable artefact; an exit code, vote or shared-memory entry is insufficient. [asserted] |
| [OpenHands Extensions](https://github.com/OpenHands/extensions/tree/51c0e3e6ebe9), current Skills formerly called Microagents | [MIT](https://github.com/OpenHands/extensions/blob/51c0e3e6ebe9/LICENSE). The registry is publicly cloneable, but individual integration skills and model execution can require credentials. Current [migration documentation](https://docs.openhands.dev/overview/skills) marks the legacy `.openhands/microagents/` location deprecated. [cited] | A uniform skills/plugins catalogue with scripts and tests, progressive disclosure, and deterministic keyword/path activation; its [loader documentation](https://github.com/OpenHands/docs/blob/b9b5c03fe889/overview/skills.mdx) explicitly separates skill instructions from permissions. It is **mixed and capability-bearing when script-backed**. [cited] | Scope and precedence remain confusing across backends ([issue 16412](https://github.com/OpenHands/OpenHands/issues/16412)); newly added global skills can fail to load ([issue 4252](https://github.com/OpenHands/software-agent-sdk/issues/4252)); matching triggers can concatenate conflicting instructions and dynamic commands execute with shell authority. [cited] | Strongest catalogue/selector prior art, not a trusted feed. Copy the deterministic selection idea into the existing instruction/capability flow; pin and scan individual local items; disable auto-update and reject credential-bearing or dynamic-shell items by default. [asserted] |
| [CrewAI](https://github.com/crewAIInc/crewAI/tree/f4731f5025f8) role templates | [MIT](https://github.com/crewAIInc/crewAI/blob/f4731f5025f8/LICENSE). Source and local-model configurations are account-free; common hosted model/search examples are not. [cited] | Generated role/goal/backstory YAML and sequential or manager-led workflows. The default researcher/analyst templates attach no substantive tool, so they are **prompts in costume**; a configured tool can add capability. [cited] | A configuration-specific report, closed not planned, [described fabricated tool observations without a tool call](https://github.com/crewAIInc/crewAI/issues/3154); a separate open proposal [describes duplicate-side-effect risk on retries](https://github.com/crewAIInc/crewAI/issues/5802). These are reported failure modes, not reproduced framework-wide defects. [cited] | Do not import roles, backstories or a second orchestrator. The useful prior art is explicit task schema and guardrails; require the sink artefact rather than narrated tool success, with idempotent local tools only. [asserted] |
| [Microsoft AutoGen AgentChat](https://github.com/microsoft/autogen/tree/027ecf0a379b) patterns | Code is [MIT](https://github.com/microsoft/autogen/blob/027ecf0a379b/LICENSE-CODE); documentation is CC-BY-4.0. Public source and its local Ollama adapter can be used without an account. [cited] | Implemented round-robin, selector, swarm, graph and Magentic-One patterns with registered tools, handoffs and termination conditions. These are **capability-bearing framework patterns**, not a curated role library; only tool outputs add facts. [cited] | The [current README](https://github.com/microsoft/autogen/blob/027ecf0a379b/README.md) says AutoGen is in maintenance mode, support is limited and new users should use Microsoft Agent Framework. [cited] | Architectural prior art only. Reuse no runtime: existing dispatch, coordination, work items and routing already cover the necessary mechanics. Team topology and agreement do not supply a different fact class. [asserted] |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework/tree/d9d3fb6252f7), AutoGen's current successor | [MIT](https://github.com/microsoft/agent-framework/blob/d9d3fb6252f7/LICENSE); its documented [local Ollama provider](https://github.com/microsoft/agent-framework/tree/d9d3fb6252f7/python/samples/02-agents/providers/ollama) needs no hosted account, although provider-specific paths can. [cited] | Current agent, tool, middleware, state and explicit graph-workflow runtime. It is **capability-bearing framework code**, but still not a curated software-development configuration; facts come from its registered tools. [cited] | The pinned local-provider README says feature support depends on the chosen model, including function calling, reasoning and multimodality; local availability therefore does not prove usable tool execution. [cited] | Strongest current framework prior art, but not the configuration winner. Do not adopt its runtime: it would duplicate native orchestration and judgement/state boundaries. Compare its explicit workflow/state contracts when extending existing Consilient modules. [asserted] |
| [GitHub Awesome Copilot](https://github.com/github/awesome-copilot/tree/83561bd7d8a4) | [MIT](https://github.com/github/awesome-copilot/blob/83561bd7d8a4/LICENSE). The catalogue is cloneable without an account, but its documented Copilot execution path is account-bound and therefore is not a qualifying end-to-end configuration. [cited] | A broad community catalogue of agents, instructions, skills, hooks and plugins. Tool-bound entries can act through a host; most expertise remains **prompt-defined**. [cited] | The README says contributions are third-party and must be inspected; [an API skill omitted overwrite semantics that could cause data loss](https://github.com/github/awesome-copilot/issues/2684), and catalogue size has broken single-skill installation ([issue 1512](https://github.com/github/awesome-copilot/issues/1512)). [cited] | Discovery corpus only. Never load it live or trust tool fields. A candidate needs its own licence/script review and a credential-free host path before entering the catalogue. [asserted] |

**Classification rule:** a skill becomes capability-bearing only at the point where an allowlisted
tool, executable, browser, dataset, source or independent human returns a new observation. Persona,
role, backstory, critique, voting, shared model family, stored assertion and another reading of the
same context remain prompts in costume. [cited] [asserted]

## 2. Keyless MCP servers

Every linked source in this section was retrieved on **2026-08-23**. The official reference
catalogue warns that its servers are educational examples rather than production-ready systems and
that operators must assess their own security requirements. The repository is transitioning from
MIT to Apache-2.0 for new contributions; each package's own licence remains decisive. Sources:
[catalogue](https://github.com/modelcontextprotocol/servers),
[licence](https://raw.githubusercontent.com/modelcontextprotocol/servers/main/LICENSE), and
[security policy](https://raw.githubusercontent.com/modelcontextprotocol/servers/main/SECURITY.md).
The inspected source identities were `599dafc10545` for the current reference repository,
`9be4674d1ddf` for its archive, `16cf228d7b02` for Playwright MCP, `d91080ff9b39` for DBHub and
`ebf58f2f4aa8` for Chrome DevTools MCP. [cited] [measured]

| Candidate | Licence / account | Capability and documented failure boundary | Decision and minimum adoption work |
|---|---|---|---|
| [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp) | [Apache-2.0](https://raw.githubusercontent.com/microsoft/playwright-mcp/main/LICENSE); no account or key for a local browser. [cited] | **Capability-bearing:** rendered browser state, accessibility snapshots, interaction, console/network evidence and screenshots. Upstream says it is **not a security boundary**; origin/file-root controls are convenience guards, persistent profiles conflict when reused concurrently, and Docker is headless Chromium only. [cited] | **Strongest MCP.** It is already recorded as a supplied component, so adopt nothing here. Keep the lighter existing connector/CLI for ordinary tasks and enable MCP only for persistent browser work, isolated with no saved credentials, explicit egress/file roots, pinned digest and captured artefacts. [measured] [asserted] |
| [Filesystem reference](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | Package MIT; repository transition as above; no account/key. [cited] | **Capability-bearing:** local read/write/create/delete/move/search. Client roots replace rather than merge CLI roots; no roots causes initialisation failure. Patched [prefix-boundary](https://github.com/modelcontextprotocol/servers/security/advisories/GHSA-hc55-p739-j48w) and [symlink](https://github.com/modelcontextprotocol/servers/security/advisories/GHSA-q66q-fx2p-7w4m) escapes show the authority boundary. [cited] | Skip for native harnesses: existing file tools already supply the same facts. An MCP-only host would need one explicit OS-confined root and read-only exposure unless mutation were expressly authorised. [asserted] |
| [Git reference](https://github.com/modelcontextprotocol/servers/tree/main/src/git) | Package MIT; repository transition as above; no account/key for a local repository. [cited] | **Capability-bearing:** repository state and mutation. It is labelled early development with an SDK v2 port pending; patched [argument injection](https://github.com/modelcontextprotocol/servers/security/advisories/GHSA-9xwc-hfwc-8w59) and [path validation](https://github.com/modelcontextprotocol/servers/security/advisories/GHSA-j22h-9j4x-23w5) defects are documented, and repository restriction is optional. [cited] | Prefer native Git. If an MCP-only host needs it, pin a patched version, require one repository, expose inspection tools by default and sandbox mutation. [asserted] |
| [Fetch reference](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | Package MIT; repository transition as above; no account/key, but it opens network egress. [cited] | **Capability-bearing:** retrieved public source text. Its README warns it can access local/internal IPs; upstream tracks [silently incomplete streamed content](https://github.com/modelcontextprotocol/servers/issues/3878) and [SSRF exposure](https://github.com/modelcontextprotocol/servers/issues/4143). [cited] | Keep the capability, not the raw server: fixed schemes/hosts, DNS and private-address checks before and after redirects, hard response-byte/time limits, licence and retrieval metadata, and fail-closed egress. [asserted] |
| [Memory reference](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | Package MIT; repository transition as above; no account/key. [cited] | It persists a JSONL entity/relation graph, but stores caller assertions rather than obtaining new facts. Current implementation rewrites the whole file without atomic replace or locking; interruption corruption is [openly reported](https://github.com/modelcontextprotocol/servers/issues/4614). **Capability substrate, not an evidence source.** [cited] | Reject as authority. It duplicates append-only events and bounded recall while omitting evidence tags, provenance and concurrency guarantees; at most it is disposable scratch state. [asserted] |
| [Sequential Thinking reference](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | Package MIT; repository transition as above; no account/key. [cited] | It stores and formats caller-supplied thoughts, branches and counters; it neither retrieves nor verifies evidence. It also logs thoughts unless disabled and has an unresolved [client-closure report](https://github.com/modelcontextprotocol/servers/issues/1163). **Prompt/state management in costume.** [cited] | Reject. It adds context and confidentiality cost without a different induction. [asserted] |
| [Time reference](https://github.com/modelcontextprotocol/servers/tree/main/src/time) | Package MIT; repository transition as above; no account/key. [cited] | **Capability-bearing but trivial:** current time and IANA-zone conversion. The implementation converts an `HH:MM` value on "today" rather than a general dated calendar value. [cited] | Skip; Python/platform time already does this with less protocol surface. [asserted] |
| [Archived SQLite reference](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite) | MIT; no account/key; the entire repository has been archived read-only since 29 May 2025. [cited] | **Capability-bearing** local SQL, but with no maintenance or security guarantee. [cited] | Reject despite being keyless. This search found no maintained official SQLite replacement. [measured] |
| [Bytebase DBHub](https://github.com/bytebase/dbhub) | [MIT](https://raw.githubusercontent.com/bytebase/dbhub/main/LICENSE); local SQLite needs no account/key. [cited] | **Capability-bearing:** SQL and schema/object inspection. Read-only defaults to false; SQLite query timeout is unsupported; stdio hot reload does not refresh the tool list; HTTP had a patched [DNS-rebinding exposure](https://github.com/bytebase/dbhub/security/advisories/GHSA-fm8p-53ww-hf6w). [cited] | Best maintained keyless SQLite MCP, but direct SQLite is smaller for native harnesses. If an MCP-only client demonstrates a gap: stdio, absolute named DB, `readonly=true`, row cap, OS sandbox, version pin and process-tree timeout. [asserted] |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | [Apache-2.0](https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/LICENSE); no account/key. [cited] | **Capability-bearing:** Chrome network/console, performance, Lighthouse and heap evidence. It is Chrome-only; usage statistics, CrUX lookup and update checks are enabled unless disabled; file/URL controls are not an OS sandbox. [cited] | Specialist only when performance, heap or DevTools evidence is the named different class. Disable telemetry, CrUX and update checks; isolate Chrome and minimise its toolset. [asserted] |

Two open servers fail the account boundary despite permissive licences: the [GitHub MCP
Server](https://github.com/github/github-mcp-server) is MIT but requires OAuth or a personal access
token, and [Framelink's Figma Context MCP](https://github.com/GLips/Figma-Context-MCP) is MIT but
requires a Figma access token. They are excluded from the zero-account ladder rather than tested
with credentials. Sources retrieved 2026-08-23. [cited]

## 3. Scientific and data capabilities

Direct libraries and bounded HTTP retrieval are the smaller choice when the harness already has
Python and shell access because an MCP wrapper introduces no new fact class. [asserted] Local
inspection found Python 3.13.11, NumPy 2.5.0 and SciPy 1.18.0 importable; SymPy, DuckDB and Jupyter
were absent, and none of these is a declared project dependency. [measured]

### Computation

Every linked source in this table was retrieved on **2026-08-23**. The inspected repository source
identities were NumPy `1f90bbb55e65`, SciPy `b6d2f204ac1d`, SymPy `e950d313a932`, DuckDB
`044a04a7cd39` and Jupyter Notebook `062a2e41d3d2`; mutable documentation pages remain bounded by
the access date and must be rechecked before adoption. [measured]

| Candidate | Licence / account | Capability and documented failure | Decision and adoption work |
|---|---|---|---|
| [NumPy](https://numpy.org/) | [BSD-3-Clause](https://numpy.org/doc/2.3/license.html); local, no account/key. [cited] | **Capability-bearing:** executed arrays, linear algebra and numerical results from explicit inputs. Fixed-width integers can [overflow silently](https://numpy.org/doc/stable/user/basics.types.html). [cited] | Use the already available harness copy without adding a project dependency. Record version, input hash, dtype, tolerance and output; range-check integer work; tag execution `[measured]`. [asserted] |
| [SciPy](https://scipy.org/) | [BSD-3-Clause](https://github.com/scipy/scipy/blob/main/LICENSE.txt); local, no account/key. [cited] | **Capability-bearing:** optimisation, integration, interpolation, signal and statistical computations. Optimisers distinguish local/global methods and return status/message that callers must inspect; `scipy.stats` explicitly leaves several model classes to other packages. Sources: [optimisation](https://docs.scipy.org/doc/scipy/reference/optimize.html) and [statistics](https://docs.scipy.org/doc/scipy/reference/stats.html). [cited] | Use the already available harness copy. Require method, bounds, seed, tolerance, assumptions, warnings/status and result artefact; fail on unsuccessful convergence or non-finite output. [asserted] |
| [SymPy](https://www.sympy.org/) | [BSD-3-Clause](https://github.com/sympy/sympy/blob/master/LICENSE); local, no account/key; currently absent. [cited] | **Capability-bearing:** exact symbolic algebra, calculus and solving. `sympify` uses `eval`, and its [documentation forbids unsanitised input](https://docs.sympy.org/latest/modules/core.html#sympy.core.sympify.sympify). [cited] | Add only after approval and a concrete exact-algebra gap. Construct expressions structurally or through a strict whitelist; preserve the expression and check; tag justified derivations `[algebra]`. [asserted] |
| [DuckDB](https://duckdb.org/) | [MIT](https://github.com/duckdb/duckdb/blob/main/LICENSE); local, no account/key; currently absent. [cited] | **Capability-bearing:** relational analysis over pinned CSV, Parquet, JSON or local databases. SQL runs with the OS user's authority and can access files, network and extensions; community extensions are not manually reviewed, and [multi-process writes are not automatically supported](https://duckdb.org/docs/current/connect/concurrency). [cited] | Add only after approval and a measured workload beyond stdlib SQLite. Prefer direct CLI/library over MCP; fixed read-only roots, disabled auto-install/load/network/extensions, caps, SQL/input hashes and version. [asserted] |
| [Jupyter Notebook](https://github.com/jupyter/notebook) | [BSD-3-Clause](https://github.com/jupyter/notebook/blob/main/LICENSE); local use needs no third-party account; currently absent. [cited] | Notebook is a stateful code-execution interface, not a numerical fact source. Versions 7.0.0--7.5.5 had token-theft [CVE-2026-40171](https://github.com/jupyter/notebook/security/advisories/GHSA-rch3-82jr-f9w9), fixed in 7.5.6. [cited] | Hold. Direct Python is smaller and safer; adopt only for a demonstrated human notebook-sharing need, pinned patched and isolated to localhost and a dedicated directory. [asserted] |

The strongest actual scientific MCP found was [MotherDuck's DuckDB MCP
server](https://github.com/motherduckdb/mcp-server-motherduck/tree/275d2e7d2ba4), MIT and keyless in local/in-memory
mode. It caps results and warns that read-only mode alone does not prevent file/settings access.
Use it only for an MCP-only client without shell/Python; remote MotherDuck and cloud-storage modes
fall outside the account/credential bar. Source retrieved 2026-08-23. [cited] [asserted]

### Keyless data sources

Every linked source in this table was retrieved on **2026-08-23**. These are public services, not
MCP servers; availability was not called or benchmarked in this survey. [measured]

| Candidate | Licence / account | Different fact class and documented limit | Minimum safe use |
|---|---|---|---|
| [DataCite REST API](https://support.datacite.org/docs/rest-api) | Public findable-record access needs no authentication. Deposited public metadata files are [CC0](https://support.datacite.org/docs/datacite-public-data-file), but that waiver does not license linked software/data. [cited] | Repository-deposited dataset/software DOI metadata, licences and related identifiers. Anonymous access is limited to [500 requests per five minutes per IP](https://support.datacite.org/docs/rate-limit), with `429` and backoff. [cited] | Record query, raw-response hash, retrieval time and rights URI; fail closed on limits or missing rights; never infer the linked artefact's licence from metadata CC0. [asserted] |
| [World Bank Indicators API v2](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | No key/authentication. World Bank-produced open data default to CC-BY-4.0, but [licence is dataset-specific](https://datacatalog.worldbank.org/public-licenses). [cited] | Official development/economic series. Calls have pagination/path/indicator ceilings, and [method, timing and revisions can cause inconsistencies](https://datahelpdesk.worldbank.org/knowledgebase/articles/906531-methodologies). [cited] | Allowlisted host and bounded response; preserve indicator source, methodology, licence, footnotes, query, hash and retrieval date; never silently fill missing values. [asserted] |
| [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) | Public pool needs no signup/authentication. Most metadata is reusable without restriction, but abstracts can retain publisher/author copyright. [cited] | Registrant-deposited DOI, funder, licence, update and retraction metadata. Public access is rate/concurrency limited; full-text links can still require subscription or a separate licence. [cited] | Use conservative sequential retrieval and backoff; cordon abstracts; preserve DOI/source/update fields. Metadata discovers a source but does not make its claims true. [asserted] |
| [arXiv API](https://info.arxiv.org/help/api/tou.html) | Free and keyless; API metadata is CC0, while each e-print retains its [own copyright/licence](https://info.arxiv.org/help/license/index.html). [cited] | Versioned author-submitted preprint discovery, not peer-review status. Etiquette requires one request per three seconds and one connection. [cited] | Enforce the interval and connection bound; retain arXiv ID, version, licence and retrieval time; do not redistribute papers without the item licence. [asserted] |
| [Wikidata Query Service](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual/en) | Structured Wikidata is [CC0](https://www.wikidata.org/wiki/Wikidata:Licensing); public SPARQL is keyless. [cited] | Community-curated linked relationships and source pointers. Queries have a 60-second deadline and client processing/error/concurrency ceilings; anyone can edit and validity is not guaranteed. [cited] | Fixed bounded query templates, descriptive user-agent, caching/backoff, entity revision and references; use as discovery/cross-check, not sole authority for a load-bearing claim. [asserted] |
| [OpenCitations](https://opencitations.net/querying/) | Citation data are CC0 and service software is ISC; an [access token is voluntary, not compulsory](https://opencitations.net/accesstoken/), so anonymous access needs no account. [cited] | Open scholarly citation graphs and provenance. The reviewed official pages did not state an exact anonymous rate ceiling, so capacity remains unknown rather than unlimited. [measured] | Qualifying with conservative serial requests, cache/backoff and a hard local cap; record query, endpoint, response hash and retrieval time, and refuse on throttling. [asserted] |
| [Europe PMC REST API](https://europepmc.org/RestfulWebService) — hold | Keyless endpoints; API documentation is Apache-2.0, but returned literature remains subject to author/publisher copyright or per-item licence under [Europe PMC's help terms](https://europepmc.org/Help). A uniform permissive metadata-output licence was not established. [cited] [measured] | Biomedical literature, citation, data-link and text-mining facts. No exact official anonymous rate ceiling was located in the pages reviewed. [measured] | Exclude from the qualifying default until metadata rights are pinned. If reconsidered for a biomedical task, require conservative caps/backoff, OA/item-licence filters and no full-text redistribution by default. [asserted] |

[OpenAlex](https://help.openalex.org/access/example-costs/) was excluded despite CC0 metadata because
anonymous calls are explicitly money/credit metered and a free API key requires signup. The public
bulk snapshot may be account-free but is hundreds of gigabytes and was not a proportionate default.
The OpenAlex source and the OpenCitations access/licence pages were retrieved 2026-08-23. [cited]

## 4. Search and exclusion record

The search covered the named repositories and current source trees; their licence, package or
component terms; official architecture and security documentation; maintained issue trackers and
advisories; the official MCP reference catalogue and archive; maintained SQLite MCP alternatives;
browser MCPs; scientific libraries and wrappers; and official API/licence/limit pages for DataCite,
World Bank, Crossref, arXiv, Wikidata, OpenCitations, Europe PMC and OpenAlex. Search families included
`agent skills licence tools failure`, `microagent skill loading`, `role template tool execution`,
`MCP <server> security advisory limits`, `keyless SQLite MCP maintained`, and `<dataset> API licence
authentication rate limit`. [measured]

Within that search, no maintained **official** SQLite MCP replacement was found; DBHub is the
strongest maintained third-party keyless candidate in the reviewed set. [measured] [asserted] No
Claude/Anthropic or community plugin marketplace was
uniformly permissively licensed and credential-free; individual components require review. No
primary comparative quality evidence was found for Ruflo's persona manifests, CrewAI's generated
roles, OpenHands skill selection or the broad Awesome Copilot catalogue. No prompt-only collection
was found that supplies a different class of facts by default. These are bounded negative search
results, not claims of universal absence. [measured]

Excluded without execution: GitHub and Figma MCPs for credentials/accounts; OpenAlex live API for
metering; archived SQLite for maintenance; hosted notebook/MotherDuck/cloud paths for accounts or
credentials; restrictive Anthropic document skills for licence; Jupyter and scientific MCP wrappers
where direct Python already supplies the same capability; and Ruflo provider-backed execution where
it requests a credential. No corpus-wide security audit or live comparative task run was performed,
so effectiveness, Windows compatibility, latency and token cost remain unmeasured. [measured]

## 5. Stress-test of the bar

1. **Epistemic:** none of the inspected agent-catalogue source trees represented provenance as
   `[measured]` / `[cited]` / `[algebra]` / `[asserted]`. A well-written persona can therefore be
   mistaken for a capability, and a narrated tool result can be mistaken for execution. [measured]
2. **Security:** skill registries mix instructions, scripts, dependencies and credentials, while MCP
   convenience roots and read-only flags are repeatedly documented as weaker than an OS boundary.
   Discovery is not authority. [cited]
3. **Reliability:** installation, discovery, activation, execution and artefact production are
   separate events. Superpowers, OpenHands and Ruflo each document a path that appears configured yet
   does not produce the expected usable result. [cited]
4. **Information:** most role systems specialise prompts over shared evidence. They cannot satisfy
   Consilient's different-class test until a browser, execution, source, dataset or independently
   authored verdict adds an exogenous observation. [cited] [asserted]
5. **Operational:** wholesale framework adoption would duplicate dispatch, coordination, work items,
   routing, budget, instruction layering or events, then add state Consilient must reconcile. The
   smallest defensible unit is a pinned method or capability, not another orchestrator. [measured]
   [asserted]

The strongest objection to the selected bar is that Superpowers has no independent comparative
evidence here showing that its whole workflow improves final artefacts over an optimised agent with
the same tools and budget. It is the best **existing configuration baseline**, not a measured winner;
the validation below is allowed to reject it. [measured] [asserted]

## 6. Consilient synthesis: how to beat the bar

The transferable mechanism from capability security is **least authority**; from scientific work it
is **provenance-bearing lab records**. Apply both to the workflow baseline: a role receives only the
capability that can create its named different fact class, and every observation returns as a typed
receipt rather than conversational authority. This cross-pollination supplies a checkable mechanism,
not a new framework. [asserted]

Each proposed catalogue entry must contain these fields before selection: [asserted]

| Field | Required meaning | Refusal condition |
|---|---|---|
| `method` | The pinned skill/procedure and permissive licence record. | Missing source, revision, licence or local content review. |
| `different_fact_class` | The exact exogenous observation: execution, rendered browser state, retrieved source, dataset computation, or independent human judgement. | Persona, vote, shared context, title, memory assertion or unspecified "expertise". |
| `capabilities` | Existing inventory identities selected through `capabilities.py`, with a reason for each. | Unknown, unavailable, unallowlisted, credential-bearing or metered capability. |
| `acceptance_artifact` | The concrete test/build/diff/trace/source/raw-response/result that proves the action occurred. | Exit status, self-report, confidence, consensus or missing artefact. |
| `evidence_policy` | Allowed tag and required producer metadata. | Automatic evidence upgrade or claim without tag/source/input. |
| `effects` | Read/write/network/external-send/irreversible authority and budget. | Authority exceeds task scope or reaches a principal-reserved decision. |

These are catalogue requirements, not a claimed source implementation. Existing
`instructions.py` layers the selected method; `capabilities.py` already refuses unknown or unavailable
inventory items; `dispatch.py`, `coordination.py`, `work_items.py`, `routing.py` and `budget.py` retain
ownership and bounds; and `events.py` remains the sole append-only record. Third-party imports,
networking, credentials and process execution stay outside the AST-locked `src/consilient/` judgement
layer. A second orchestrator or third-party authoritative memory is a defect. [measured] [asserted]

Evidence adaptation is exact: skill and API documentation remain `[cited]`; a retrieved source earns
`[cited]` only for claims it actually supports; executed tests, numerical work, SQL and browser
artefacts are `[measured]`; exact checked symbolic derivations are `[algebra]`; and model synthesis
without an external producer remains `[asserted]`. Failure, truncation, warning, non-convergence,
`429`, licence ambiguity and unavailable capability are preserved and fail closed, never converted
to an empty successful result. [asserted]

The default configuration is one accountable owner using the relevant Superpowers method and the
smallest qualifying capability. An extra worker requires a named different fact class and bounded
non-overlapping scope; that is an organisation rule, not a consequence of beta. ADR-0077 separately
defines `n_max = floor(epsilon / beta_upper)` for future candidate exposure: its frozen mutation
calculation gives `n_max <= 1`, but the helper is unwired and live human-labelled beta is unestimated,
so current routing refuses rather than applying that number. The logarithmic iid expression is
diagnostic only. No agent may approve, spend, lift a gate or author a verdict for the principal.
[measured] [algebra] [asserted]

## 7. Validation protocol and killing checks

1. Freeze representative tasks by stratum and randomly or counterbalance them between an optimised
   single-owner control and the smallest Superpowers-derived method/capability configuration. Hold
   model, tools, environment and total realised token/time budget constant. [asserted]
2. Score independently checkable artefacts and blinded human decisions; report paired quality,
   uncertainty, verifier beta/safety, tokens, latency, human review time, refusals, timeouts,
   quarantines, duplicate work, context loss and unverified handoffs. [asserted]
3. Mutation-test the catalogue boundary: missing `different_fact_class`, unknown/unavailable
   capability, credential or metering, non-permissive/missing licence, excess effect authority,
   missing receipt, solver failure, non-finite value, response truncation and `429` must all refuse or
   quarantine. [asserted]
4. Ablate the procedure prose, the capability and the extra budget separately. If a role's gain
   survives without its named fact source, its role story is not the mechanism; if the gain vanishes
   without extra budget, compare against a budget-matched single owner. [asserted]

**Killing checks:** remove a Superpowers-derived method if it fails to improve quality or safety net
of review cost against the control; leave Playwright MCP disabled by default if it does not beat the
existing connector/CLI on persistent browser tasks; prefer direct Python/SQLite when an MCP wrapper
adds no outcome or provenance gain; and invalidate a data capability when its licence, anonymous
access contract or response provenance cannot be re-established. [asserted]

Predicted failures are selector conflicts, stale upstream pins, a script gaining new network or
credential use, prompt injection through retrieved/browser content, numerical false precision,
silent truncation, and overfitting the comparison to coding tasks. Mitigations are exact content
pins and rescans, fixed tool/effect allowlists, hostile-content isolation, typed numerical checks,
raw artefact retention, and task-stratified results. [asserted]

## 8. Adoption cost for the three strongest

1. **Superpowers 6.3.0 method subset — low to medium.** No new runtime dependency is needed, but the
   repository would need explicit user approval before vendoring: pin and licence-record the chosen
   skills, content-review scripts, disable optional remote telemetry, map host tools to inventory,
   add activation/retention checks and measure the workflow against the single-owner control.
   OpenHands contributes selector mechanics only. [asserted]
2. **Playwright MCP — medium.** The component is already supplied, so cost is confinement rather than
   acquisition: pinned digest, isolated ephemeral browser/profile, explicit origin/file/effect
   policy, no saved credentials, prompt-injection treatment, process-tree timeout, and retained
   screenshot/trace/console/network artefacts. Default enablement still needs the comparative test.
   [measured] [asserted]
3. **Direct science/data path — low now, medium if extended.** Existing NumPy/SciPy need no project
   adoption; a bounded stdlib retrieval skill can call only selected keyless sources and record raw
   provenance. SymPy or DuckDB would require approval, a dependency/licence record and their parser,
   file/network/extension safeguards. A scientific MCP is justified only for a client without direct
   Python/shell capability. [measured] [asserted]

## Plain answer and delta

The plain answer is: **use Superpowers 6.3.0 as the configuration baseline, Playwright for browser
facts, and direct local scientific/data tools; ignore persona catalogues.** [asserted]

The delta produced by this survey is the admission boundary: take methods from Superpowers, selector
mechanics from OpenHands and execution transports from permissive keyless tools, but admit a role
only with a named different fact class, an allowlisted fail-closed capability and a provenance-bearing
acceptance artefact. That is smaller than adopting any framework and stricter than every surveyed
catalogue. Whether it is better remains a pre-registered measurement, not a claim this research has
earned. [asserted]

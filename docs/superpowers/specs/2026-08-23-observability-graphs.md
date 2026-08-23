# Record-derived observability graphs

**Correction.** The current trajectory is an ordered append-only sequence, not a DAG by
construction; it contains no live `decision.autonomous` event and no implemented
artefact-to-decision or decision-to-evidence join, so the graph model below is a specification and
every absent join must render as `unknown`, never as an inferred edge. [measured]

- **Decision:** Extend the existing `consil dashboard` projection with five record-derived views in
  the same self-contained HTML artefact; use focused, hand-rolled SVG only where topology answers a
  question, and retain list/filter/detail views as the authoritative fallback. [asserted]
- **Status:** Specification only; no source implementation or gate change is authorised by this
  document. [measured]
- **Killing experiment:** EXP-139 tests whether the graph treatment improves correct causal answers
  over raw JSONL and whether the node-link layer improves them over the same list/filter/detail
  projection. [asserted]
- **Authority boundary:** The dashboard displays recorded claims and absences. It never creates a
  decision, explanation, approval, verdict, route, work item, capability holding, effect or
  trajectory event. [asserted]

## Constraints that do not move

ADR-0053 fixes one offline surface: `consil dashboard` emits one self-contained HTML file, opened
directly from the filesystem, with no server, port, authentication flow, bundler, frontend
dependency, third-party import or second implementation language. [measured] `dashboard.py` already
renders SVG, so the extension reuses that renderer, HTML/CSS and Python's standard library; there is
no JavaScript, canvas runtime, D3, Cytoscape, npm package, web worker or new CLI subcommand. [asserted]

`events.py` remains the only trajectory writer. [asserted] The dashboard receives an immutable
accepted prefix plus read-only plan files and projection rows, and has no callable path back to
`events.append`, work-item mutation, dispatch, routing, budget or effect admission. [asserted] Its
SQLite input is a disposable projection; disagreements are shown against the canonical JSONL rather
than resolved in favour of the cache. [asserted]

The principal has required native graph visualisation, so EXP-139 cannot remove the graph views.
[measured] It can remove node-link diagrams from the default path and kill the claim that a graph
improves causal explanation. [asserted]

## The retrieved bar

The sources in this table are first-party documentation retrieved on 23 August 2026 unless a paper
is named. [measured] “Not documented” is bounded to those reviewed sources: extensible metadata
could carry user-defined fields, but that is not evidence of a first-class decision/falsifier/
reversal contract or an independence check. [asserted]

| Incumbent | What the reviewed source renders | What it explains or preserves | Limit in the reviewed source |
|---|---|---|---|
| [LangSmith](https://docs.langchain.com/langsmith/view-traces) | Nested traces, threads and turns; model, tool and subagent activity; captured reasoning blocks; inputs, outputs, timing, tokens, errors and child runs. [cited] | Run/trace/thread identity, parentage, retriever content, evaluator traces, feedback, tags and arbitrary metadata. [cited] | A first-class decision with alternatives, a preregistered falsifier, a linked reversal procedure and evidence-root independence/echo detection are not documented. [cited] |
| [W&B Weave](https://docs.wandb.ai/weave/guides/tracking/trace-tree) | Hierarchical trace tree, code-composition, flame and node-graph views; call details, scores, cost and latency. [cited] | Versioned operations/code, trace parentage, captured inputs/outputs, attributes, feedback, comparison and known-good baselines. [cited] | Recorded decision reasoning, preregistered falsifier, decision-specific reversal and shared-source echo detection are not documented as first-class semantics. [cited] |
| [Braintrust](https://www.braintrust.dev/docs/observe/examine-traces) | Nested spans, threads, timelines, raw JSON, messages, tool calls, scores, reviewer spans and activity history. [cited] | Trace/span identity, prompt and dataset origin, score rationale, reviewer attribution, comments and edit history. [cited] | A formal decision/alternatives schema, preregistered decision falsifier, linked reversal and evidence-class independence check are not documented. [cited] |
| [OpenTelemetry](https://opentelemetry.io/docs/specs/otel/trace/api/) and [Jaeger](https://www.jaegertracing.io/docs/2.20/deployment/frontend-ui/) | OpenTelemetry specifies trace/span data; Jaeger renders trace timelines, critical paths and focal-service/dependency graphs. [cited] | Causal parentage/links, typed attributes, events, status, resource and instrumentation identity; Jaeger can link spans to logs. [cited] | Decision reasoning, preregistered falsifiers, reversal plans and evidence-root independence/echo detection are not documented; Jaeger's aggregate dependency edges do not prove a transitive request path. [cited] |
| [Apache Airflow](https://airflow.apache.org/docs/apache-airflow/stable/ui.html) | DAG nodes/edges, ordering, branching, groups, retries, run-state overlays, Grid/Gantt views, events, logs and source. [cited] | Declared upstream/downstream relationships, branch labels, trigger rules, run configuration and operational history. [cited] | Decision alternatives/rationale, preregistered decision falsifiers, linked reversal plans and evidence independence are not documented; its UI also has operational write actions. [cited] |
| [Dagster](https://docs.dagster.io/guides/operate/webserver) | Asset lineage across code locations, declared dependencies, filters, materialisation/check state, run Gantt and structured events. [cited] | Source/owner metadata, materialisation history, definition changes and executable asset checks; Dagster+ documents image rollback. [cited] | Why one decision beat alternatives and whether its evidence roots are independent are not documented; checks and image rollback are not a decision-linked falsifier/reversal record. [cited] |
| [Sourcegraph](https://sourcegraph.com/docs/code-navigation) | The reviewed current surface is navigation rather than a generic dependency canvas: definitions, references, implementations, history, blame and diffs. [cited] | Exact code/revision locations and precise/syntactic/search-based navigation provenance. [cited] | A generic node-link dependency view, structured decisions, preregistered falsifiers, linked reversals and echo detection are not documented. [cited] |
| [GitHub dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph) | Searchable dependencies/dependants, direct/transitive status and transitive path drill-down; the reviewed page does not document a general node-link canvas. [cited] | Manifest/lockfile origin, versions, licences, vulnerabilities, snapshot commit, detector/submission provenance and SBOM export. [cited] | Decision alternatives/reasoning, preregistered falsifiers, decision reversal and evidence-class independence are not documented. [cited] |

The useful bar is therefore not “draw more nodes”. [asserted] It is the incumbents' trace hierarchy,
filtering, details-on-demand, critical-path emphasis and provenance drill-down, combined with this
repository's validated time-of-decision fields and explicit different-class test. [cited] No reviewed
official source documents that complete combination; this is a bounded documentation finding, not
a claim that no product can be configured to do it. [cited]

### Search log and near misses

Searches covered each named incumbent's official documentation for traces, graph, lineage,
dependencies, reasoning, evaluators/checks, provenance, history and rollback; the graph-scale search
also covered node-link cognitive load and shortest-path performance. [measured] OpenTelemetry was a
data-model rather than UI near miss; Sourcegraph's current reviewed material described code
navigation; GitHub's “dependency graph” described summaries and path drill-down. [cited] Vendor blogs
and third-party comparison pages were not used to establish the bar. [measured]

## Record model: project only what exists

The renderer builds typed nodes and explicit edges from accepted records; temporal adjacency alone
never creates causality. [asserted] Every node carries `source_kind`, stable source locator, source
digest or event hash, recorded timestamp, and projection status. [asserted] Every edge names the
field or declared relation that created it. [asserted]

| Input | Permitted projection | Named absence |
|---|---|---|
| Canonical trajectory read by `events.py` | Event identity, order, author, accepted payload and explicit references. [measured] | Sequence is not displayed as a causal edge unless a recorded reference says so. [asserted] |
| `coordination.py` | Live work claims, claim holder, claimed paths, opening and expiry. [measured] | An expired claim is not a finished work item and a process identifier is not proof of running work. [asserted] |
| `work_items.py` | Recorded open/comment/complete lifecycle and explicit work-item identity. [measured] | Missing contribution, verifier, dissent, resolver or release fields remain `unknown`. [asserted] |
| `dispatch.py` | Recorded dispatch identity, harness/family, outcome and artefact manifest where present. [measured] | Dispatch start is not authority, completion or proof that an artefact exists. [asserted] |
| Capability records and `capabilities.py` | Declared capability identity and metadata supplied to a task. [measured] | The present flat capability list is not displayed as an applied holding or effect. [measured] |
| `docs/superpowers/plans/*.md` | Unit identity, deliverable, declared `Depends on`, steps and done criteria parsed from the plan source. [measured] | A cache row without the matching plan-set digest is stale, not a second plan. [asserted] |
| ADR-0079 decision protocol when emitted | Verbatim decision, reasoning, alternatives, falsifier, reversal and exact record references. [measured] | There are presently zero live `decision.autonomous` events, so current decision-chain panels must say so. [measured] |
| ADR-0081 evidence protocol when emitted | Anchor identity, channel/class, derivation roots and exact event/digest references. [measured] | ADR-0081 is presently a specification, so absent independence fields are `unmeasured`, not “shared” or “independent”. [measured] |
| SQLite projection | Indexed copy used for bounded lookup and filtering. [measured] | A projection head that differs from canonical JSONL is visibly stale/refused. [asserted] |

Plan Markdown is authoritative. [asserted] A generated plan cache is admissible only when it embeds
the digest of the exact plan set and a check reproduces it; the dashboard must reparse or refuse a
mismatched cache rather than silently display it. [asserted] Semantic `REAL` edges come only from
declared work prerequisites. [asserted] Ordering-only edges are rendered separately from recorded
claim/path exclusion or declared landing order and are excluded from semantic critical-path
calculation. [asserted] An `UNJUSTIFIED` edge is a red data defect and refusal, not an ordinary
schedule edge. [asserted]

## The five views

All views share one filter state expressed with native HTML controls and fragment links; every SVG
mark has a corresponding table row and detail target. [asserted] The table remains usable when SVG
is unsupported, printed, magnified or removed by EXP-139's result. [asserted]

### 1. Agent work

The default is a work-item list plus a focused agent → work item → claimed path/artefact diagram for
the selected item. [asserted] It renders harness/family, recorded role and different class of facts,
claim opening/expiry, explicit capability metadata, current work-item state, produced artefact
manifest and verifier/dissent/release obligations where recorded. [asserted] Shared-evidence roles
receive an `echo: shared root` warning; a role title alone never counts as a different class.
[asserted]

“Nothing running” uses four textual labels, four shapes and four glyphs; colour is redundant, not the
only signal. [asserted]

| State | Exact condition | Mark |
|---|---|---|
| `finished` | No remaining unit and no outstanding contribution, verifier, dissent or release obligation. [measured] | Double-ring circle, tick glyph, `FINISHED`. [asserted] |
| `waiting_dependency` | Remaining work, no ready unit, and every critical blocker has a named resolver plus a re-evaluation boundary. [measured] | Dashed rounded rectangle, clock glyph, `WAITING`. [asserted] |
| `blocked` | Remaining work, no ready unit, and at least one critical blocker has no resolver. [measured] | Octagon, exclamation glyph, `BLOCKED`. [asserted] |
| `starved` | Ready work exists but every admissible route is unavailable or unknown on a fresh resource observation. [measured] | Diamond, empty-set glyph, `STARVED`. [asserted] |

The precedence is `finished`, `starved`, `waiting_dependency`, `blocked`; if the predicate inputs are
missing or stale, the view shows `UNKNOWN — missing <fields>` rather than selecting the nearest
state. [measured]

### 2. Dependency graph

This view renders plan units, `REAL` prerequisite edges, ordering-only exclusion edges, unjustified
edge defects and the semantic critical path. [asserted] Solid arrow = `REAL`; dashed arrow =
ordering-only; red crossed arrow = `UNJUSTIFIED`; the critical path uses a thicker solid stroke plus
the text label `CRITICAL`, so colour is not required. [asserted]

The current 57-unit planning corpus contains 127 modelled dependencies; the dependency correction
classified 94 as real, 17 as ordering-only and 16 as unjustified, and removing non-real scheduling
edges reduced the reported critical-path depth from 24 levels to 16. [measured] Those numbers are a
dated regression fixture, not permanent constants; the renderer recomputes from current authoritative
plans and displays the plan-set digest beside them. [asserted]

The default SVG is the critical path plus the selected node's one-hop neighbourhood. [asserted] A
filter can reveal a plan, edge class, owner or topological layer; “show all 57” is an explicit
diagnostic action and the equivalent sortable edge table remains visible. [asserted]

### 3. Plans and roadmaps

This view parses `docs/superpowers/plans/` and groups units by source plan and semantic topological
level. [asserted] It renders each unit's deliverable, declared prerequisites, steps, done condition,
recorded lifecycle, claims and artefacts; it links back to the exact plan heading and accepted event
locators. [asserted]

The roadmap is a projection, never hand-maintained state. [asserted] A plan edit changes the source
digest and forces regeneration; a lifecycle event changes the trajectory head and forces
regeneration. [asserted] Conflicting plan identities, cycles among `REAL` edges, missing dependencies
or stale generated caches are refusal panels, not guessed lanes. [asserted]

### 4. Decision chains

For a selected artefact, the view follows only explicit references backwards through recorded
contribution/effect/work-item links to the antecedent decision, then forwards to the recorded outcome
or reversal. [asserted] The detail panel renders the exact `decision`, `reasoning`, losing
alternatives, `falsifier`, evidence references and typed `reversal` object with their event IDs and
hashes. [asserted]

The chain contains no `summary`, `explanation`, `likely reason` or generated narrative field.
[asserted] If an artefact has no explicit antecedent, the answer is `NO RECORDED DECISION LINK`; if
the decision protocol has not been emitted, the panel names that absence. [asserted] A material
effect with no required antecedent is displayed as a contract violation, not repaired by visual
proximity. [asserted]

### 5. Evidence provenance

This view renders decision → anchor edges and anchor → derivation-root edges using the recorded
anchor identity, evidence channel/class, source locator, retrieval/observation time, digest and event
hash. [asserted] Different shapes identify artefact execution, real-browser observation, primary
source retrieval and a non-derived public corpus/API; unclassified evidence is a grey `UNMEASURED`
node. [asserted]

Two claimed anchors that share an anchor ID or derivation root converge on one visible root node and
receive a striped `ECHO — SHARED ROOT` band. [asserted] Two roles reading the same artefact or two
models using the same source remain one evidential slot. [asserted] Independence is displayed only
when the ADR-0081 record carries different channels/anchor identities and disjoint derivation roots;
missing dependence data is `unmeasured`, never consilience. [asserted]

## Answering “why did it do that?”

The answer is a record traversal, not a model call. [asserted]

1. Select the artefact, effect or work item and resolve its stable recorded identity. [asserted]
2. Follow its explicit antecedent reference to the accepted `decision.autonomous` record; never use
   time proximity as causality. [asserted]
3. Display the decision and reasoning verbatim, followed by the recorded alternatives and why they
   lost where present. [asserted]
4. Display the preregistered falsifier and reversal procedure beside the decision, not behind a
   success-only view. [asserted]
5. Resolve exact evidence references to their event IDs/hashes and expose shared derivation roots as
   echo. [asserted]
6. Link forward to the recorded effect/outcome/reversal, preserving the principal-authored verdict
   or approval without allowing an agent attribution to substitute for it. [asserted]

Thus the surface can answer “the record says decision D was taken because R, against alternatives
A, subject to falsifier F, on anchors E, with reversal V” and can link every symbol to bytes in the
record. [asserted] It cannot answer why when those fields or links were never recorded, and it says
so rather than generating prose. [asserted]

## Native refresh, automatic rendering and staleness

Current dashboard rendering is manual; no source currently invokes it automatically. [measured]
There is one pure renderer and two specified pull triggers; neither is a new orchestrator. [asserted]

1. `consil dashboard` always reads a fresh accepted JSONL prefix, checks the SQLite projection head
   and plan-set digest, and atomically replaces the HTML before returning its path. [asserted]
2. The existing local orchestration controller calls the same renderer at the end of each
   reconciliation tick when the source marker changes, including after a terminal dispatch event or
   a plan digest change. [asserted] It does not call through `events.py`, and a failed render cannot
   roll back or modify the accepted trajectory. [asserted]

The source marker is `(trajectory_head_event_id, trajectory_head_sha256, projection_head,
plan_set_sha256, renderer_schema_version)`. [asserted] Equal markers skip the write; unequal markers
produce a temporary file in the destination directory and use an atomic standard-library replace.
[asserted] An optional native HTML meta refresh may reload that same filesystem artefact; it never
contacts a server. [asserted]

Every page header permanently displays `generated_at`, the accepted event count/head ID/head digest,
projection head, plan-set digest, controller interval `T`, and `stale_after = generated_at + 2T`.
[asserted] A one-shot render with no active controller says `HISTORICAL SNAPSHOT` and has no freshness
claim. [asserted] Because the file contains no JavaScript clock, it never says “current” or “fresh”;
the absolute expiry remains visible even if the controller dies and the browser cannot repaint a
badge. [asserted] Missing, mismatched or expired source observations are labelled `STALE` or
`UNKNOWN`, never zero. [asserted]

Automatic rendering is a silent same-machine pull projection. [asserted] It writes only the
replaceable HTML artefact and emits no conversation message, notification, approval request or
external push. [asserted] Interruption remains the separate attention policy governed by ADR-0083
and the recorded liveness transition; render churn cannot interrupt the principal. [measured]

## Layout and accessibility rules

The layout algorithm is deliberately small: stable topological ranks for acyclic `REAL` graphs,
stable lexical ordering within a rank, fixed node boxes, orthogonal or straight SVG edges, and a
focused neighbourhood default. [asserted] Cycles are data errors and render as a table/refusal rather
than invoking a force-directed simulation. [asserted] This avoids a bundled layout engine and makes
the output reproducible, but it will not optimise arbitrary graph aesthetics. [asserted]

Every SVG has a heading, prose purpose, keyboard-reachable links, non-colour edge/state encoding and
an adjacent semantic table containing the same nodes and relationships. [asserted] Long labels wrap
in detail panels rather than expanding every node. [asserted] Print and reduced-motion modes contain
no animation. [asserted]

The scale objection is real. Yoghourdjian et al.'s controlled shortest-path study found significant
difficulty above 50 nodes for high-density diagrams and above 100 for low-density diagrams; those
are task/layout-specific findings, not a universal cutoff. [cited] The current corpus has 57 units,
so a full graph is already inside the paper's adverse high-density range. [measured] The design
therefore makes filter/list/detail and focused subgraphs primary until EXP-139 supports a broader
node-link default. [asserted]

## Acceptance checks owed by implementation

Implementation does not ship until one bounded test for each invariant fails on the corresponding
defect. [asserted]

- **One surface:** the six-command CLI snapshot is unchanged and `consil dashboard` still emits one
  self-contained file with no JavaScript, remote resource, server, port, script bundle or
  third-party import. [asserted]
- **Render-only:** an AST/source-to-sink check proves the dashboard cannot call trajectory, work-item,
  dispatch, route, budget, capability or effect writers. [asserted]
- **Canonical source:** a deliberately stale SQLite head and plan cache are labelled/refused against
  JSONL and plan digests. [asserted]
- **No inferred causality:** adjacent events without a recorded reference produce no edge; a fixture
  with explicit IDs/hashes produces exactly one. [asserted]
- **Verbatim why:** a fixture's decision, reasoning, falsifier and reversal bytes appear unchanged;
  no generated explanation field exists. [asserted]
- **Four states:** each F-01 predicate fixture produces the correct text, glyph and shape, while a
  missing-field fixture produces `UNKNOWN`. [asserted]
- **Dependency semantics:** the dated 57-unit fixture reproduces the recorded classifications and
  24-to-16 correction; only `REAL` edges contribute to semantic critical path. [asserted]
- **Echo:** anchors with a shared derivation root merge into one marked echo; disjoint roots remain
  distinct; missing roots say `UNMEASURED`. [asserted]
- **Staleness:** a changed source marker triggers one silent atomic render, an equal marker triggers
  none, and stopping the controller leaves an absolute expired `stale_after` with no “current” label.
  [asserted]
- **Scale/accessibility:** the 57-unit default is focused rather than a full hairball, and all SVG
  information is reachable through headings, text labels, keyboard links and the equivalent table.
  [asserted]
- **Authority:** fixtures authored by an agent cannot appear as principal verdicts, approvals, gate
  lifts or spend authority. [asserted]

## Validation: EXP-139

EXP-139 is registered before implementation or outcome inspection. [measured] Its raw arm, identical
list/filter/detail arm and list/filter/detail-plus-graph arm distinguish an improvement from record
projection from an improvement caused by the node-link diagram itself. [asserted] Wrong and timed-out
answers receive the fixed time cap and correctness is also reported separately, preventing a fast
wrong answer from looking efficient. [asserted]

The experiment may change the node-link default and every “improves explainability” claim. [asserted]
It cannot remove the five required views, change a gate, establish trust or beta, or generalise beyond
the preregistered task and operators. [asserted]

## Evidence against and deliberate concession

The strongest case against this design is that graph visualisation is decoration. [asserted]
Node-link diagrams become hairballs, lists and filters answer operational questions more directly,
and a hand-rolled SVG layout lacks the edge routing, zoom, clustering and accessibility maintenance
of a mature graph library. [asserted] A 57-unit graph is already large enough for measured
shortest-path difficulty in high-density node-link tasks, and every custom layout rule becomes code
that can rot while adding no causal information to the record. [cited]

That objection wins against a graph-first dashboard. [asserted] The accepted design concedes the
full-canvas default: lists/filter/detail are authoritative, node-link views are focused projections,
and full graphs are opt-in diagnostics. [asserted] Stable ranks and tables are chosen over a bespoke
force layout. [asserted] If EXP-139 finds B matches or beats C, the graph becomes secondary decoration
and no explanatory-benefit claim survives; if C loses accuracy or increases false endorsement, that
result overrides any speed gain. [asserted]

The plain answer would add diagrams to the existing dashboard. [asserted] The evidence review adds
the part that matters: explicit causal joins instead of temporal lines, verbatim time-of-decision
fields instead of narration, visible shared-root echo, a focused/list-first scale response and a
three-arm test able to reject the diagram without rejecting the authorised graph capability.
[asserted]

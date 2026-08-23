# 0096. Render record-derived observability graphs without generated explanations

- **Status:** PROVISIONAL — EXP-139 can remove the node-link default and every claim that graphs
  improve causal explanation; it cannot remove the principal-authorised graph views. [asserted]
- **Date:** 2026-08-23. [measured]
- **Deciders:** Joe Brown authorised native automatic graph visualisation; Codex dispatch
  `20260823T134149-cff67cd3c7` records the provisional mechanism, which he has not reviewed. [measured]
- **Inquiry tier reached:** T1 ground — the current record, dashboard, plan corpus and official
  incumbent documentation were read; T3 is preregistered as EXP-139 and has not run. [measured]
- **Executable model:** none — the decision is reversible and EXP-139 is the outcome test. [asserted]

## Context

The brief's premise needs correction: the trajectory is an ordered append-only sequence, not a DAG
by construction, and a local census at 2026-08-23T13:52:46Z found no live
`decision.autonomous` events or implemented artefact/decision/evidence joins. [measured] A renderer
may therefore project only explicit recorded identities and references; temporal proximity and
visual adjacency cannot create causality. [asserted]

The brief also carries superseded planning state: ADR-0077 replaced its independent-trial formula
for automatic candidate exposure, and the cited 57-unit/127-edge graph is a digest-pinned historical
four-plan fixture rather than the current plan corpus. [measured]

The principal required observability, explainability and native automatic graph visualisation of
agent work, dependencies, plans and roadmaps on 23 August 2026. [measured] ADR-0053 already fixes the
surface: one self-contained HTML file emitted by `consil dashboard`, with no server, port,
authentication flow, bundler, frontend dependency, second language or trajectory write path.
[measured] The existing Python dashboard already emits hand-rolled SVG. [measured]
At dispatch, dashboard rendering was manual; no source invoked it automatically. [measured]

The difficult question is not how to draw work; it is how to answer “why did it do that?” without
inventing a second explanation after the event. [asserted] ADR-0079 specifies a time-of-decision
record with decision, reasoning, falsifier, reversal and exact references, while ADR-0081 specifies
evidence anchors and disjoint derivation roots; both are predominantly prospective protocols today.
[measured] Missing protocol fields must remain named absences until the corresponding records exist.
[asserted]

## Decision

Extend the existing `consil dashboard` renderer, and no other operator surface, with the five views
specified in `docs/superpowers/specs/2026-08-23-observability-graphs.md`: agent work, dependencies,
plans/roadmaps, decision chains and evidence provenance. [asserted]

The authoritative interaction is list/filter/detail with a focused SVG projection for topology.
[asserted] Full-node canvases are opt-in diagnostics. [asserted] SVG uses stable topological ranks,
fixed boxes and stable ordering rather than a new graph/layout dependency or a bespoke force
simulation. [asserted]

Every causal edge comes from a typed record reference and links to its exact event ID/hash or plan
source. [asserted] The “why” panel displays the recorded decision, reasoning, alternatives,
falsifier, evidence anchors and reversal verbatim. [asserted] It never calls a model, synthesises a
narration or fills a missing relationship. [asserted]

Plan Markdown remains authoritative for unit identity and declared topology and is parsed on read.
[asserted] The dashboard does not infer edge semantics from `Depends on` prose. [asserted] Every
dependency must have exactly one upstream machine-readable `REAL`, ordering-only or `UNJUSTIFIED`
class plus a supporting locator in a checked plan field or generated-and-checked edge manifest bound
to the exact plan-set digest. [asserted] Missing or conflicting classes refuse semantic styling and
critical-path calculation. [asserted]

`scripts/dispatch.py`, the existing outer-runner boundary, will silently call the pure renderer after
each terminal dispatch outcome and claim-release attempt. [asserted] ADR-0095's prospective
supervisor extends that same boundary with a reconciliation tick for plan-only changes; it is not
present yet. [measured] `consil dashboard` forces a render on explicit pull. [asserted] Each active
tick refreshes `observed_at` and an absolute `stale_after` even when unchanged graph content is
reused; every snapshot also displays generation time, accepted trajectory head/digest and plan
digest and never labels itself “current” or “fresh”. [asserted] Rendering emits no conversation
message and is not an interruption. [asserted]

`events.py` remains the sole trajectory writer and the dashboard gains no path to it. [asserted] No
new CLI command, server, watcher service, orchestrator, dependency, route, authority, gate condition
or effect is introduced by this decision. [asserted]

The surface may display a recorded squad, beta ceiling and route/resource observation, but it never
admits another candidate or recomputes a route. [asserted] Automatic candidate exposure uses
ADR-0077's `floor(epsilon / q_upper)` ceiling; the logarithmic independent-trial expression is
diagnostic only, and missing/stale bounds display `UNKNOWN / REFUSED`. [measured] A role receives
distinct evidential credit only from a recorded different class and disjoint derivation root, and
principal-only decisions remain visually and structurally distinct from agent proposals. [asserted]

## Evidence

The current dashboard already creates a self-contained HTML artefact and hand-rolls an SVG
agent-to-artefact view; it collapses 65 artefact paths into 11 groups and caps graph nodes while
retaining the full table. [measured] Extending it is a smaller and more coherent surface than
starting a second frontend. [asserted]

The digest-pinned historical 57-unit/127-edge four-plan audit classifies its modelled edges as
`REAL`, ordering-only or `UNJUSTIFIED`; excluding non-real scheduling edges reduced that fixture's
recorded critical-path depth from 24 levels to 16. [measured] The classification is useful as a
regression fixture but is not current plan state or authority for a new edge. [asserted]

LangSmith, W&B Weave and Braintrust document rich trace hierarchies, timelines, filtering, captured
inputs/outputs, evaluator data and provenance metadata. [cited] OpenTelemetry/Jaeger document trace
parentage, critical-path and dependency views; Airflow and Dagster document DAG/lineage views and
operational state; Sourcegraph documents provenance-rich code navigation; GitHub documents
manifest/submission-derived dependency paths. [cited] The reviewed official sources do not document
the complete combination of a first-class decision with alternatives, preregistered falsifier,
linked reversal and shared-derivation-root echo detection. [cited] This is a bounded documentation
finding, not proof that no incumbent can be customised to store those fields. [asserted]
The official source URLs, retrieval date and product-specific limits are recorded in the companion
[retrieved-bar table](../superpowers/specs/2026-08-23-observability-graphs.md#the-retrieved-bar).
[measured]

[Yoghourdjian et al.](https://arxiv.org/html/2008.07944v1) report significant shortest-path
difficulty above 50 nodes at tested density 6 and above 100 nodes at density 2; the thresholds are
task, graph and layout specific. [cited] The historical fixture's density is `127 / 57 = 2.23`, so
the paper does not place it in the adverse density-6 condition. [algebra] Applicability to this graph
and causal-answer task remains unmeasured. [asserted]

## Evidence against

Graph visualisation may be decoration. [asserted] A sortable list and exact filters can answer “who
holds this?”, “what blocks it?” and “which record authorised it?” with less visual search than a
node-link diagram. [asserted] Beyond modest size, crossings and labels form a hairball; the existing
dashboard's own grouping and node caps already embody that pressure. [measured]

Hand-rolled SVG is also a maintenance liability. [asserted] Without a mature layout library it will
not match automatic clustering, routing, zoom or interaction from graph products, and every custom
layout feature expands a renderer whose value is unmeasured. [asserted] The no-dependency constraint
is valuable for trust and portability, but it makes a general graph canvas a poor goal. [asserted]

The answer is a concession, not a denial: list/filter/detail stays authoritative; SVG defaults to
the critical path or selected one-hop neighbourhood; a full graph is opt-in; and EXP-139 separately
tests raw JSONL against the projection and the identical projection with node-link diagrams.
[asserted] If the list/filter/detail arm matches or beats the graph arm, node-link becomes secondary
decoration. [asserted] Any accuracy loss or extra false endorsement kills the graph default even if
it is faster. [asserted]

## Consequences

- The surface can show recorded reasons and provenance without asking a model to reconstruct them.
  [asserted]
- A missing antecedent, anchor, derivation root, lifecycle field or freshness observation becomes a
  visible `UNKNOWN`/`NOT RECORDED` state rather than an attractive invented edge. [asserted]
- Shared anchors and derivation roots visibly collapse into echo instead of receiving independent
  evidential credit. [asserted]
- Finished, waiting on a named dependency, blocked without a resolver and starved despite ready work
  use distinct text, glyph and shape encodings; colour is redundant. [asserted]
- Automatic render work stays in `scripts/dispatch.py` and ADR-0095's prospective extension of that
  outer-runner boundary, avoiding a dashboard watcher or second orchestrator. [asserted]
- The limited layout deliberately gives up a general interactive canvas and may make graphs
  secondary after EXP-139. [asserted]

## Enforcement

The implementation must ship with bounded checks that enforce: one self-contained offline surface;
no new CLI command/dependency/server/remote resource; no dashboard-to-writer source path; canonical
JSONL and plan-digest binding; explicit-reference-only causal edges; verbatim decision fields;
distinct accessible encodings for the four no-running states; refusal of any dependency without one
upstream class and support locator; `REAL`-only critical paths; visible shared-root echo; per-tick
`observed_at` refresh even with unchanged content; absolute staleness metadata; and a focused
historical 57-unit fixture with a complete table fallback. [asserted]

No implementation is authorised by this ADR. [measured] The exact checks and refusal fixtures are
specified in `docs/superpowers/specs/2026-08-23-observability-graphs.md`. [measured]

## What would overturn this

EXP-139 is the registered killing experiment. [measured] It compares raw canonical JSONL plus text
find (A), record-derived list/filter/detail without node-link diagrams (B), and the identical
projection with node-link diagrams (C). [asserted]

If C fails the fixed correctness/time/no-false-endorsement thresholds against A, remove every claim
that graph treatment improves causal explanation. [asserted] If B matches or beats C, make
list/filter/detail the default and retain graphs only as secondary views; any accuracy loss or extra
false endorsement kills the node-link default regardless of speed. [asserted] The experiment cannot
remove the five principal-authorised graph views, alter a gate or establish general trust or beta.
[asserted]

## Publication candidate?

No. This is an internal product decision whose central benefit claim is deliberately provisional
until EXP-139 runs. [asserted]

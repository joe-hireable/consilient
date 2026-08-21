# 0065. What is native, what is adopted from upstream, and what is a marketplace

- **Status:** ACCEPTED
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (principal)
- **Inquiry tier reached:** T1 ground — the dividing line is derived from `CONSILIENCE.md` and from measured failures, not asserted
- **Executable model:** none — this decides a boundary, not a threshold. No decision variable, no objective, no unknown parameter.

## Context

The principal named twelve capability areas that must be **native by default**: memory, tools, hooks,
skills, design, coding, GTM, documentation creation, diagramming, MCPs, plugins and marketplaces. He
also said they should come *"according to the open source repos we are adopting and contributing
upstream or anything we need to build custom ourselves."*

Those two instructions pull against each other, and the tension is real rather than verbal. **Every
capability built natively is one maintained forever. Every capability adopted is one not controlled.**
A project that builds everything ships nothing; a project that adopts everything has no product. This
ADR decides where the line falls and — more usefully — gives a **test** so the next capability does
not need a new decision.

This is a one-way door in practice. A capability adopted and depended on for a year is not casually
brought in-house, and one built in-house is not casually dropped.

In the principal's words, 21 August 2026:

> "Memory, tools, hooks, skills, design, coding, gtm, documentation creation, diagramming, mcps,
> plugins, marketplaces all need to be native according to the open source repos we are adopting and
> contributing upstream or anything we need to build cusom ourselves."

> "We need to ensure as much automation and intelligence is built into the harness natively by
> default as possible and like other harnesses we can include marketplaces of other plugins, skills
> etc. but we need as much natively as possible i.e. I use Gojiberry, Clay and some other paid tools
> for GTM we need native GTM capabilities built in openly run by the harnesses agents."

## Decision

**The test is silent failure in the acceptance path.**

> **A component whose error rate must be measured is native and is never delegated. A component whose
> errors are self-evident may be adopted from upstream. Everything else is a marketplace item.**

Concretely, three tiers:

**1. Native, never delegated — the judgement layer.** Anything participating in deciding whether work
is good, or in recording what happened: **β** and its estimator, routing and parallelism conditioned
on β, the acceptance predicate, the gates, the append-only trajectory and its projection, the recall
projector, the budget ceiling, and the coordination layer that prevents agents clashing. These are
the product. A third party cannot supply them, because we would then be unable to measure the error
rate of the thing measuring error rates.

**2. Adopted from upstream, and contributed back — the capability layer.** Anything that *performs*
work whose result is then judged by tier 1: diagram renderers, documentation generators, MCP servers
and connectors, browser drivers, editors, model adapters, GTM tooling. Prefer a good upstream project
over building. **Contribute fixes upstream rather than forking**; fork only when upstream refuses a
change we need, and record why.

**3. Marketplace — the optional layer.** Third-party skills, plugins and packs a user installs at
their own discretion. **A marketplace is a supplement, never a substitute**: no capability the
principal named may be *available only* through a marketplace, because that would make the open-source
package incomplete and break ADR-0048's open-source-first rule.

**On GTM specifically**, because it is the case that prompted this: the **agents that run GTM are
native** — they are judged by tier 1 like any other work — while the **capabilities they use**
(enrichment, sending, sequencing) sit in tier 2 and may be adopted. "Native GTM" means the harness's
own agents do the work openly, not that we reimplement every vendor.

**Licence constraint on adoption**: only permissive licences compatible with this project's MIT
distribution. **BUSL and SSPL are refused** — that already cost two candidates during the always-on
survey (Restate at BUSL-1.1, Inngest at SSPL-1.0). Record the licence of anything adopted, in the
commit that adopts it.

## Evidence

- `[measured]` **Condensation destroys the raw material of a β estimate.** EXP-45 measured
  condensation dropping ~59%, which is why `src/consilient/recall.py` quotes trajectory fields
  verbatim into a bounded pack instead of summarising. A third-party memory layer that summarises
  would silently remove the variance β is computed from. This is the sharpest single argument for
  tier 1.
- `[measured]` **Silent acceptance is this project's characteristic failure, and it is invisible from
  outside.** On 21 August 2026: a `pre-push` hook counted a *missing* checker as a pass; the
  private-corpus gate could report PASS having enumerated the wrong repository; and four `cursor-agent`
  dispatches exited **0** having written nothing at all. Each was a component that failed silently in
  an acceptance path, and none was detectable from its exit code.
- `[measured]` **Errors outside the acceptance path announce themselves.** A renderer that fails
  produces no diagram; a connector that fails produces no data. Nobody is misled. That asymmetry is
  the whole basis of the test above.
- `[cited]` ADR-0048 fixes open-source-first and prepaid facilitation, which forbids a marketplace
  becoming the only route to a named capability.
- `[asserted]` A rule that must be re-argued per capability will be re-argued badly under time
  pressure. A stated test is worth more than a list.

## Evidence against

- `[asserted]` **The test's boundary is not always obvious, and GTM shows why.** A GTM tool *can* fail
  silently — the jobboard-v2 audit on 21 August found a product publishing one email address while
  the inbound webhook accepted only another, silently returning 200 and dropping everything else.
  That is a silent failure, yet GTM is placed in tier 2. The distinction relied on is that β is
  defined over *artefact acceptance*, not over business outcomes — but a reader may reasonably say
  the rule has been applied by assertion at exactly the point it was most needed. **The honest
  position is that tier 2 components still need their own monitoring; the test decides who may supply
  them, not whether they can hurt you.**
- `[asserted]` **"Native by default" plus twelve capability areas is a very large surface for a
  project with one maintainer and three invited contributors.** The realistic failure is not choosing
  wrongly but building tier 1 well and leaving tier 2 half-built for a year. Nothing here mitigates
  that; it is a scheduling problem this ADR does not solve.
- `[cited]` **Adopting upstream has a measured cost too.** The always-on survey found that of five
  durable-execution candidates, none provides exactly-once side effects, and adopting any would add a
  second durable store to keep consistent with the JSONL trajectory. Adoption is not free merely
  because the code is written.
- `[asserted]` The tiers assume upstream projects exist and are good for tier 2. For several named
  areas — GTM run by open agents, diagramming driven from a trajectory — **that may simply be false**,
  and the answer will be "build it" more often than this ADR implies.

## Consequences

**Positive** — the judgement layer stays measurable, which is the only reason this project can claim
anything. Contributors get a stated test rather than a case-by-case argument. Upstream gets
contributions instead of silent forks.

**Negative** — tier 1 is a permanent maintenance commitment with no escape hatch: β, routing, the
trajectory, recall, budget and coordination are ours forever. Tier 2 breadth will lag, visibly,
because it is large and second in priority.

**Neutral but load-bearing** — this constrains ADR-0064's providers: a model or training provider is
tier 2, so adding one may never move judgement out of tier 1. A provider that would evaluate its own
output for us is refused on this ADR's grounds regardless of its capability.

## Enforcement

- Check: **no direct static import in a tier 1 module may name a third-party package.**
  `tests/test_component_licences.py:111` AST-scans the six judgement modules (`beta`, `events`,
  `projection`, `recall`, `budget`, `work_items`) and rejects direct imports outside the standard
  library. `[measured]`
- Check: every adopted runtime dependency and tracked MCP server appears as a `supplied` entry in
  `docs/legal/adopted-components.json`. `.github/scripts/check_component_licences.py:42` rejects
  incomplete records, invalid, future or stale verification dates, denied supplied licences,
  refused entries without reasons, and adopted names absent from the record. `[measured]`
- Fails CI: yes. `.github/workflows/invariants.yml:48` self-tests the licence detector and scans the
  tracked tree; the invariant test suite runs the tier-1 import ban. `[measured]`
- Added in the same commit as the decision: **no.** The decision was recorded first; both checks now
  exist and fail CI. `[measured]`

## What would overturn this

- A measured case where a tier 1 component is better supplied by an upstream project **and** its error
  rate remains measurable by us — for instance a β estimator whose implementation we can audit and
  whose outputs we can verify independently. That would narrow tier 1 rather than abolish it.
- Evidence that the silent-failure test misclassifies in practice: a tier 2 component that repeatedly
  causes silent acceptance despite the test placing it there. Two such cases should force a rewrite of
  the test, not an exception to it.

## Publication candidate?

**Yes, provisionally.** The test — *a component whose error rate must be measured is native; one whose
errors are self-evident may be adopted* — is plausibly general to systems that orchestrate third-party
agents. `[asserted]` Both owed checks are now wired into CI at the scope stated above. `[measured]`
The licence gate enforces the named denylist rather than proving every unlisted licence permissive,
and the import gate covers direct static imports rather than dynamic or transitive imports.
`[measured]` Until those gaps have their own enforcement, publication remains blocked. `[asserted]`

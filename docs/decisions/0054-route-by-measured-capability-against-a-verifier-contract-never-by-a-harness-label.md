# 0054. Route by measured capability keyed on task family, and credit evidence to the anchor, never to the harness's label

- **Status:** **PROVISIONAL 21 August 2026.** Rests on `[asserted]` evidence with four named
  killing experiments (EXP-90 … EXP-93). Extends
  [`0025`](0025-model-discovery-and-capability-probing.md),
  [`0027`](0027-compose-domain-harness-provider-and-model.md),
  [`0042`](0042-admit-connectors-by-capability-probing-credential-isolation-and-fail-closed-boundaries.md)
  and [`0012`](0012-composite-beta-with-per-check-diagnostics.md). Supersedes nothing.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the instruction and the direction). The mechanism, the three-column
  split, the task-family definition, the anchor rule and every objection in *Evidence against*
  are mine. Two of them contradict parts of the instruction that produced this ADR.
- **Inquiry tier reached:** T1 ground — the rule already exists three times in this repository,
  for models, connectors and compositions, and the evidence taxonomy exists a fourth time in
  `../10-research/qa-automation-and-the-anchor-problem.md`. This ADR applies them to the one leg
  still selected by its name.
- **Executable model:** none. `inquiry-tier.md` gates a model on a formalizable **unknown
  parameter**, and this decision introduces none: the decision variable (which composition) and
  the objective (accepted artefacts per unit of quota under a β ceiling) are already carried by
  ADR-0002's closed form and ADR-0026's admission predicate. A third model would be a
  restatement.
- **Artefact class:** **PRODUCT.** Ships open source and is useful to anyone holding more than
  one harness. Instance-specific measurements are in
  [`../20-design/harness-capabilities.md`](../20-design/harness-capabilities.md) and labelled
  there.

---

## Correcting the brief that produced this ADR

Three things in the instruction I was given are wrong. The third is the one that changes the
answer.

**1. A vendor's capability claim is not the same thing as a model's self-reported confidence,
and banning it under working principle 5 bans too much.** `CONSILIENCE.md` is precise about why
self-confidence is worthless: *"Confidence is not a second class of facts. It is the same
induction, restated."* It is tautological — the model asserting its own reliability has observed
nothing new. A vendor's capability claim is not tautological. The vendor ran evaluations we did
not run; it is a *different* induction, merely a low-quality, conflicted, stale and
unreproducible one. The correct ground for refusing to route on it is already recorded, and is
narrower and more useful: **ADR-0025** — *"A generic score never gates routing — it decides
whether a model is worth probing"* — and **ADR-0040**, decide from evidence, not from
pretraining. Under principle 5 a label is banned outright; under ADR-0025 it survives as an
ordering over *what to probe first*, which is free and is exactly what a cold start needs. This
ADR takes the ADR-0025 route.

**2. "Task class" is not this project's term. "Task family" is, it is in the specification, and
it is already in the shipped code.** `v0-draft.md` §5: *"For a fixed repository, task family and
verifier contract, β is the conditional rate at which the automated verifier accepts an artefact
the human verdict rejects."* And `src/consilient/beta.py` already carries `task_family` as a
field and a filter, `src/consilient/projection.py` already indexes
`outcomes (task_family, verifier_version)`, and `consil beta` already takes `--task-family`.
[measured] So per-family β is not machinery this ADR must invent. **The gap is narrower and more
embarrassing than the brief implies: the quantity is specified, the column exists, the index
exists, and nothing reads any of it when choosing a harness.**

**3. The different-class-of-facts argument does not survive in the form the brief states it, and
this repository already knew why.** The brief asks me to argue that "a harness driving a browser
and observing a rendered page produces a genuinely different class of facts than any agent
reading the same source code". `../10-research/qa-automation-and-the-anchor-problem.md` settled
the general form of this question on 20 August, and its answer is sharper: different-class credit
attaches to the **anchor** — where the expected value comes from — and never to the technique or
the modality. Its table is explicit that *state-anchored* expectations, those taking their value
from the code under test, are **echo** regardless of how they are obtained. A browser that
renders a page and confirms it matches what the code implies is state-anchored, and a screenshot
does not launder it. **The browser is not an anchor. It is a transport to one** — specifically to
the *implicit oracle* row of that table: crash, hang, uncaught exception, dead affordance,
missing accessible name, contrast failure. Those are supplied by the runtime rather than by
anyone's belief, and no reader of the source obtains them at any level of skill.

That correction matters because it changes what gets built. Under the brief's version, "can drive
a browser" is an evidence-class property of a harness. Under the corrected version, it is a
*reachability* property — the harness can reach an anchor — and the credit sits on the anchor,
which is enumerable, already written down, and shared across every harness that can reach it. It
also means this ADR must not readmit, through a capability column, the thing
`interface-beta-2026-08-20.md` item 6 already refused: *"Simulated personas, visual-LLM judges,
and 'is this screen confusing?' probes are the obvious move and are already refused."*

Everything else in the brief holds, and its central observation is correct and is sharper than
the brief itself argues — for the reason in *Context*, third paragraph.

---

## Context

Joe, 21 August 2026, verbatim:

> "we need to consider that the harnesses we are meta-harnessing, some are known as "coding"
> harnesses but within our meta harness can be perfect fits for non coding tasks also. Like
> Cursor is great at visual analysis in browser, browser automation, autonomous QA and user
> simulation and QA automation, document drafting, design with Figma plugins or OpenDesign etc."

**What routing currently is.** `architecture-sketch.md` §2: *"Admit feasible resources → cheap →
verify → mid → verify → frontier. Three capability tiers remain the starting hypothesis."*
[measured] That is a **total ordering on one axis**. It expresses "this composition is stronger
than that one". It cannot express "this composition is the only thing here that can reach a
runtime oracle, and it is mediocre at writing Python" — which is the claim in Joe's sentence and
is not a statement about tiers at all. A cascade is the right shape for *escalation*. It is the
wrong shape for *selection*.

**The rule already exists three times, for everything except the harness.** ADR-0025 established
it for models: a benchmark score decides whether a model is worth probing and never gates
routing, and its enforcement already includes *"a config key naming a model as 'safe' without a
probe record fails lint"*. ADR-0042 established it for connectors: a zero-inference, zero-token
probe runs before dispatch and `validate_capability_record` fails closed on anything
unobservable. ADR-0027 established that domain, harness, provider and model compose separately
and that *"no single `backend` string may silently collapse these fields"*. The one leg still
selected by its name is the execution harness — selected by name precisely because the names are
so familiar that nobody noticed they were being read as evidence.

**Capability is not a property of a harness.** Measured on this machine at 02:20 on 21 August
2026: a single Claude Code session carried, among its attached tool servers, two independent
browser drivers (`chrome-devtools`, `playwright`), a Figma server exposing design-context and
screenshot tools, a diagramming server, document servers and media-generation servers. [measured]
A Claude Code install with no servers attached has none of those capabilities and is the same
product at the same version. **The same harness has different capabilities on different machines,
and on the same machine at different times.** A table keyed on a harness *name* is therefore not
merely imprecise; it is keyed on something that does not determine the answer. ADR-0029's rule
bites here directly: a change to the attached server set must **invalidate** a capability row and
may never create one.

**Two of the three things a capability row needs are already decided.**
`../20-design/capability-layer.md` establishes that tools are **structural zeros removed, not a Δ
mechanism** — *"giving a 4B model a browser leaves it a 4B model"*. So *reach* (does the
composition have the tool at all) and *strength* (Δ, ADR-0025's paired probe) are separate,
already-specified quantities. What is missing is the third column and the key.

**Is this a one-way door?** Partly, and the part that is matters. The capability row's shape and
the route-decision event's reference to it are schema; once trajectories carry them they cannot
be rewritten (ADR-0006, append-only). The *policy* — thresholds, which status is admissible for
which kind of work — is fully reversible. The schema is therefore taken with care and the policy
cheaply, which is the correct asymmetry.

---

## Decision

**A capability is a measured row keyed on `(task family × composition)`, never a claim.** Routing
may read only such rows. Where none exists the task runs on the default generalist composition,
the run is recorded as a probe, and its outcome writes the first row — a vendor's label may order
*which* composition to probe first and may do nothing else. β is carried on the row, so a
composition that is fast and wrong at one task family is excluded **from that family** rather
than from routing altogether. And evidence-class credit attaches to the **anchor** a composition
can reach, drawn from the enumerated table in
`../10-research/qa-automation-and-the-anchor-problem.md` — never to its modality, its vendor, or
its name.

Five things this settles.

### 1. What a capability is — three columns, two of them already decided

```text
capability_row := {
  task_family:   <verifier contract id>                    # §2
  composition:   <ADR-0027 tuple + attached servers + versions>
  status:        unprobed | probed | measured | excluded    # §4
  reach:         { tools: [...], probe_event: <id> }        # ADR-0042, zero-inference
  strength:      { delta_hat, phi_hat, n, interval }        # ADR-0025, paired probe
  anchor:        [ implicit_oracle | independent_spec |     # §3, THE NEW COLUMN
                   metamorphic | differential | real_traces ]
  beta:          { beta_hat, n, window, interval, verdict } # §5
  provenance:    [ <trajectory event ids> ]                 # non-empty iff usable
}
```

`composition` includes the attached servers and their versions, because of the measurement above:
the harness name does not determine capability. `provenance` is what makes the row a measurement
rather than an assertion, and the *Enforcement* section is entirely about keeping it honest.

**`reach` and `strength` are not new.** They restate ADR-0042 and ADR-0025 in a shape a router
can read. The only genuinely new column is `anchor`, and even its vocabulary is borrowed rather
than coined.

### 2. A task family is an equivalence class over verifier contracts

Two tasks belong to the same family **iff the same verifier contract decides them.** Not the same
subject matter; not the same domain. The same oracle.

Three reasons, one of them decisive. It is the only definition that bounds proliferation:
|families| = |distinct verifier contracts|, which is small, enumerable and written down, whereas
a subject-matter taxonomy grows until every task is its own family and every n is 1 — the failure
ADR-0003 already recorded when it noted *"our task-class competence vector was invented"*. It
reuses a field that already exists in `beta.py` and is already indexed in `projection.py`. And it
is the definition `CONSILIENCE.md` forces, because a class of facts is defined by what observes
it — which makes β-per-family not a new quantity but β with its oracle named.

**On domains with no fast oracle, this ADR defers to `q24-oracle-latency-2026-08-20.md` and does
not re-decide Q24.** That note's position is that the question is not whether a domain has an
oracle but *how long the answer takes and how hard it is to attribute*, and that **a domain where
β cannot be measured is not forbidden — it is unverified, and must be labelled unverified.** This
ADR adopts that unchanged: a task family whose verifier contract has an oracle latency beyond the
routing window carries `beta.verdict = unverified`, routes as `probed` (supervised, bounded), and
claims no β. Document drafting becomes routable unattended the moment someone writes an oracle
for it — required sections present, every cited URL resolves, a held-out reader answers five
comprehension questions — and not before. Coding was never special; it is the domain where
somebody had already written the oracle.

### 3. Evidence-class credit attaches to the anchor

The `anchor` column takes its values from the table already in
`qa-automation-and-the-anchor-problem.md`, unchanged:

| Anchor | Different class? | Reachable by |
|---|---|---|
| The code itself (state-anchored) | **No — echo** | everything, and it counts for nothing |
| Implicit oracle: crash, hang, 5xx, dead affordance, missing accessible name, contrast failure | **Yes** — supplied by the runtime | a composition that can execute and observe the artefact — *this is the browser row* |
| Independent specification | **Yes**, the strongest and rarest | any composition given a spec authored independently of the code |
| Domain metamorphic relation | **Yes** | any composition, given the relation |
| Independent reference implementation | **Yes** | a composition with a second implementation |
| Real user traces | **Yes** | not available pre-launch |

Three consequences follow, and the first is the answer to Joe's question.

**A harness's browser capability earns routing consideration because it is a transport to the
implicit-oracle row, not because rendering is inherently informative.** The same harness pointed
at the same page, asserting that it matches what the code implies, is state-anchored and earns
nothing. This is why the column records the anchor rather than the tool.

**A different harness is not a different evidence class, and this repository has already paid to
learn it.** `cursor-xai-and-evidence-class-independence-2026-08-20.md` records that Cursor's
acquisition into SpaceXAI creates a standing path from Cursor's coding data into Grok's training
corpus, and states the rule plainly: common ownership does not collapse an evidence class, but
neither does a different vendor establish one — *"a contamination path is not a measured
contamination"*, and it must be measured. That note's proposed check is adopted here as binding:
**a run whose `model_selected` is absent or `unknown:not-reported-by-runtime` may not credit an
`anchor` value**, because an unidentified model cannot be shown to be a different one.

**Visual-LLM judgement is not an anchor and this ADR does not readmit it.** A model looking at a
screenshot and reporting whether it looks right is state-anchored. `interface-beta-2026-08-20.md`
item 6 already refuses it, and nothing in the `anchor` column creates a route around that
refusal. EXP-90 arm 3 measures what the refusal costs; it does not license it.

### 4. Cold start: probe by doing the work, never by believing the label

| status | meaning | admissible for |
|---|---|---|
| `unprobed` | no row | nothing. The task goes to the **default generalist composition**, the run is recorded as a probe, and its outcome writes the row. |
| `probed` | ADR-0042's zero-inference probe passed, and/or n is below the measurement threshold, and/or `beta.verdict` is `insufficient_data` or `unverified` | **bounded supervised work only.** |
| `measured` | n ≥ threshold with a reported interval | unbounded unattended work, subject to §5. |
| `excluded` | admission (ADR-0026/0042) or β refused it | nothing, for this family. |

`probed` is not invented here. `backends.md` already puts Grok and Cursor in exactly this state —
*"admissible for bounded supervised work today … and inadmissible for unbounded unattended
work"*. [measured] This ADR names a state the operator's view already uses.

**The bootstrap is doing the work, not benchmarking.** The first run at a new family *is* the
probe, which keeps the cost of the rule proportional to the work actually being done rather than
to the size of the table. EXP-93 measures whether that holds.

A vendor's label may **order the probe queue** and may do nothing else — ADR-0025's rule, applied
to harnesses. That is what stops the cold-start path from being a random walk, and it is the
correction in the opening section.

### 5. β lives on the row, and exclusion is per-family

β is carried per row, not per composition. A composition whose β̂ at a family exceeds that
family's ceiling is removed **from that family** and remains eligible elsewhere.
`insufficient_data` is a first-class verdict — already required by `v0-draft.md` §5 — and routes
to `probed` handling, that is, to supervision, never to optimism.

**This does not weaken ADR-0012 and must not be read as doing so.** ADR-0012 forbids composing
per-*check* β values analytically into the routing number, and its lint rule stands unchanged:
the routing path reads the directly measured **composite**. This ADR slices that same composite
by task family and composition. A slice is not a decomposition. Per-check β remains a diagnostic
and remains barred from the routing path.

This is the case in Joe's brief that a per-harness score cannot express: **high α̂ with high β̂ is
worse than having no harness at all**, because the artefacts arrive fast, the checks pass, and
the human is the only thing between them and the repository. A single score averages that
composition up. The row shows it.

---

## Evidence

- `[measured]` **Two same-class checks are strongly dependent on this repository.** EXP-47, 1,931
  mutants: mutants surviving `pytest` survived `mypy` at 87.89% against 58.50% for those `pytest`
  killed; χ² = 187.28, p < 10⁻¹⁵; ADR-0012's independent-product prior refuted. This is the
  empirical content of "checks reading the same class of facts do not add up", and it is EXP-90's
  baseline. `experiments/exp47/findings-exp47.md`.
- `[measured]` **`task_family` already exists in the shipped code and nothing routes on it.**
  `src/consilient/beta.py` (field and filter), `src/consilient/projection.py` (column and the
  `outcomes (task_family, verifier_version)` index), `src/consilient/cli.py` (`--task-family`).
  The key this ADR proposes is already in the schema.
- `[measured]` **The same harness has different capabilities on different machines.** A Claude
  Code session here on 21 Aug 2026 carried two browser-driver servers, a Figma server, a
  diagramming server, document servers and media-generation servers — none of it implied by the
  name. Detail in `../20-design/harness-capabilities.md`.
- `[measured]` **The existing capability validator would accept a declared capability.** EXP-27's
  `validate_capability_record` (`experiments/exp27/handshake.py`, line 49) fails closed on
  `unknown`, `unobservable`, `unsupported` and `missing`, and has **no provenance requirement**. A
  record reading `{status: "supported", usable: true}` transcribed from vendor documentation
  passes it. That is another instance of this repository's catalogued failure mode — a chokepoint
  with no rule banning bypass — and *Enforcement* closes it.
- `[measured]` **`probed`-but-not-`measured` is already the operational reality.** `backends.md`
  records Grok and Cursor as `excluded_unknown_headroom`, admissible for bounded supervised work
  only.
- `[asserted]` **Different-class credit attaches to the anchor, not the technique.** The anchor
  table in `qa-automation-and-the-anchor-problem.md`, adopted here unchanged. Its own status is
  `[cited]` at abstract depth for the literature and `[asserted]` for the taxonomy, and that note
  is explicit that its sources *"may not be promoted to a `[cited]` line in an ADR until fetched
  and read"*. They have not been. This ADR therefore carries the taxonomy as `[asserted]`.
- `[cited]` **A delegated network without new exogenous signals is dominated by a single
  decision-maker with the same information.** Ao, Gao & Simchi-Levi (2026), arXiv:2603.26993.
  Why §3 exists: adding a harness that reaches no new anchor adds cost and relay loss, not
  accuracy.
- `[cited]` **Whewell (1840)**, restated in *Novum Organon Renovatum* (1858), pp. 70–71 — the
  "another **different** class" clause is what the `anchor` column measures rather than declares.
- `[algebra]` **Bounding proliferation.** Under §2, |families| = |distinct verifier contracts|;
  under a subject-matter taxonomy the bound is |tasks|. At a fixed threshold N per row the first
  is reachable at solo-founder volume and the second provably is not.
- `[asserted]` That routing on measured rows beats routing on labels **by enough to pay for the
  probes**. This is the load-bearing assertion of the entire ADR and it is unmeasured. EXP-91.

---

## Evidence against

Seven, and the third and seventh are the ones that would actually cost us.

- `[asserted]` **The browser may be echo even as a transport.** Most runtime-observable defects
  have a static analogue: a headless DOM assertion with `testing-library` plus `axe-core` reaches
  missing accessible names and contrast failures without a browser engine at all, and `jsdom`
  reaches uncaught exceptions. If a competent static suite catches nearly everything the engine
  catches, then the different class was never the browser — it was *executing the code*, which
  `pytest` already does. EXP-90 is designed against this specifically: the static arm is
  **required** to include DOM-level component assertions, because beating a pure-function
  baseline would prove only that execution differs from reading, which nobody disputes.
- `[cited]` **Modality is not information, and the theorem is about information.** Ao, Gao &
  Simchi-Levi bound what a network can know, not what it can look at. If the same model, in the
  same lineage, wrote the code and reads the screenshot, its induction over the screenshot is
  conditioned on a belief that came from the code. **The instrument is exogenous; the observer
  may not be.** This is why §3 credits the anchor rather than the observer, and why EXP-90 arm 4
  — a source-reader with no browser, same model as the browser-agentic arm — exists at all.
- `[measured]` **Per-row β may be unmeasurable at this volume, for the exact reason EXP-01
  failed.** EXP-01's stopping rule fired: pooled across both corpora there were 209 evaluable bad
  artefacts against the 332 needed for ±0.05. β was **not measurable at solo-founder volumes by
  history mining.** A table of |families| × |compositions| cells needs n per cell, and this is
  the same arithmetic that already defeated us once. The mitigation is real but partial — EXP-47
  measured β in 104 seconds by mutation rather than by waiting, so any family with a
  mutation-generatable fixture bank is cheap, and any family without one is not. Document
  drafting has no such bank. **For those families the table stays empty**, §4 routes an empty row
  to supervision, and that is honest but is not the automation anyone was hoping for. EXP-92's
  third stopping rule is the one that fires here, and it collapses the table.
- `[cited]` **Capability-based harness selection is not novel.** `literature-review.md` flags
  Meta-Harness (Stanford/MIT, COLM 2026) as already automating harness search, and several 2026
  papers cover verification-gated orchestration. Nothing in §1, §2 or §4 is new, and §3's
  taxonomy is borrowed from a 20 August note. What may be new is §5 — routing on measured β per
  verifier contract rather than on measured success — because β is the quantity nobody else
  reports. **The honest position is that this ADR's contribution is narrow and sits almost
  entirely in its last section.**
- `[asserted]` **The label ban is stronger than the evidence for it.** Vendor labels are not
  noise; they correlate with capability and they are free. ADR-0027 already concedes the general
  form — *"public benchmarks are priors, local outcomes decide"*. The opening correction pulls
  the ban back to ADR-0025's narrower rule for exactly this reason, and EXP-91's second stopping
  rule pulls it back further if `label` routing lands inside `measured` routing's interval. If
  that happens, this ADR was expensive theatre and should say so.
- `[asserted]` **Design work is deferred by a prior decision this ADR does not override.**
  `design-capability-assessment-2026-08-20.md` defers design to a post-v0 gate, requires
  aesthetic output be labelled `unverified`, and has already **cut** multi-model design review
  panels, persona-prompted design critics and brief-versus-output debate as echo. Joe's brief
  names "design with Figma plugins or OpenDesign" as a capability to route to. It is one — as a
  *producer*, under an unverified label. It is not an evidence class, and the `anchor` column
  must not be used to smuggle one in.
- `[asserted]` **The `random-admitted` result is the one to fear.** If EXP-91's floor arm lands
  inside both other arms' intervals, routing is not the lever at this scale and neither labels
  nor measurements matter; the finding would belong to ADR-0003 and ADR-0009, and this ADR would
  be a well-argued answer to a question that does not pay. At n this small that is a live
  possibility, not a rhetorical concession.

**What I searched and did not find.** I searched this repository for prior treatment of browser
observation, visual analysis, Figma, QA automation, user simulation and document drafting **as
routing inputs**. All six appear — as connector names (ADR-0042), as tool supply
(`capability-layer.md`), as refused acceptance signals (`interface-beta`), and as a deferred gate
(`design-capability-assessment`) — but **no prior ADR treats non-coding capability as a routing
input**, and none defines a task class. I did not find any work, here or in the literature
review, arguing the opposite case — that harness labels are a sufficient routing signal — which
is weak evidence, because nobody writes that paper.

---

## Consequences

**Positive.**
- The subscriptions already paid for become usable for what they can do rather than for what
  their marketing says, which was the whole of the instruction.
- Non-coding work gets a *precondition* rather than a prohibition: write the oracle, get the
  routing. Q24 stops being a wall in front of a domain and becomes a per-family checklist item,
  consistent with `q24-oracle-latency`'s existing position.
- "Fast and wrong at this family" becomes visible and actionable instead of averaged into a
  single per-harness score.
- The cold-start path costs the work you were going to do anyway.
- The `anchor` column gives ADR-0010's "name your different class of facts" an enumerated
  vocabulary and a place to live, instead of a prose paragraph per structure.

**Negative.**
- **A table of |families| × |compositions| cells, most of them empty**, with the empty ones
  routing to supervision. Six compositions and eight families is 48 cells; at N = 20 per cell,
  960 runs to fill. Most will never fill, and *Evidence against* item 3 is the reason that may not
  be recoverable.
- Every row must be invalidated when the attached server set changes (ADR-0029), so the table
  decays and re-probing is recurring cost, not a one-off.
- Writing a verifier contract for a non-coding family is real work with no shortcut. This ADR
  makes that explicit rather than easier.
- The route-decision event grows a reference field. Schema, therefore permanent.

**Neutral but load-bearing.**
- The cascade is not deleted. It remains correct for *escalation within* a family; this ADR
  governs *selection of* the family's candidate set. Anyone who read `architecture-sketch.md` §2
  as the whole routing story now needs both documents.
- ADR-0012's lint rule is untouched: routing reads the composite. §5 slices it; it does not
  decompose it.
- ADR-0003 (no learned routing policy in v0) is untouched, and this ADR must not be read as a
  route around it. A table of measured rows is a lookup. The moment anything fits a function to
  it, ADR-0003 applies.

---

## Enforcement

Invariant **V0-40** (*No routing decision may consume a declared capability*).

Numbered 40 rather than 30 deliberately: V0-29 was the highest in the repository at 02:15 on
21 Aug 2026 and ten concurrent worktrees were sitting on that maximum, so the next free number is
the one everybody takes at once. **V0-30 … V0-39 remain free.**

Three checks, because any two of them leave the chokepoint bypassable — a clean row the router
ignores, a router citing a row built from a press release, or a second code path that writes rows
from a manifest.

- **Check 1 — provenance is mandatory for usability.** Extend `validate_capability_record`
  (today `experiments/exp27/handshake.py`, line 49; moving to product code with the
  implementation) so any capability with `usable: true` **must** carry a non-empty `provenance`
  list of trajectory event ids, each resolving to a probe or outcome event; and so an `anchor`
  value may not be credited from a run whose `model_selected` is absent or
  `unknown:not-reported-by-runtime` — the check
  `cursor-xai-and-evidence-class-independence-2026-08-20.md` proposed and this ADR adopts. Raise
  `ValueError` otherwise, in the fail-closed style the function already uses.
  **Confirmed buildable:** the function exists, is tested (`experiments/exp27/test_handshake.py`),
  and the change is an added clause in a loop that already iterates every capability. [measured]
- **Check 2 — the router reads nothing else, and replay proves it.** `v0-draft.md` §4.2 already
  requires *"exactly one recorded route decision before dispatch"*. That event gains a
  `capability_row_id`, and the existing replay invariant in `.github/workflows/invariants.yml`
  gains an assertion that **every route decision in the trajectory resolves to a capability row
  with non-empty provenance**. A route decision citing nothing, or citing a row without
  provenance, fails the build. **Confirmed buildable:** the replay step already runs
  `consilient.cli --json replay` in CI and already asserts on its JSON — and the 20 August repair
  to that step is on record precisely because a check that could not fail was caught there once.
  [measured]
- **Check 3 — the bypass ban, which is the part usually missing.** A repository-wide lint step
  failing on any capability-*declaring* key (`capabilities:`, `supports:`, `can_*`,
  `is_capable_of`) in adapter or configuration files, and on any construction of a capability row
  outside the single derivation function. Without it, checks 1 and 2 are satisfied by a second
  path that writes rows from a manifest — which is exactly how `jobboard-v2`'s documented unified
  `llm()` boundary fragmented into five access paths. **Confirmed buildable, and it extends an
  existing rule rather than inventing one:** ADR-0025's enforcement already specifies *"a config
  key naming a model as 'safe' without a probe record fails lint"*; this is the same rule with
  the subject widened from model to composition. `ruff check .` already runs repository-wide in
  CI, and the single-construction rule is an AST check of the same kind as
  `.github/scripts/check_rename_safety.py`, which already exists and already fails CI. [measured]

- **Where the test lives:** `tests/test_v0_invariants.py`, the established pattern — that file
  already contains meta-tests asserting the CI configuration itself and the no-bypass rule — plus
  a row in `v0-draft.md`'s invariant table.
- **Fails CI:** yes, once the router exists. Checks 1 and 3 can ship before it.
- **Added in the same commit as the implementation:** required (I1). This ADR describes the
  interface only. `src/consilient/`, `tests/` and ADRs 0051–0053 are owned by concurrent work and
  are untouched here.

---

## What would overturn this

Pre-registered, each with its own stopping rule and its own blocking verdict. **None of the four
blocks implementation**, under ADR-0049 (experiments inform, they do not gate) and ADR-0050 (an
experiment gates only when its *largest possible effect* would change what gets built).

| Experiment | Kills | Blocks? |
|---|---|---|
| **EXP-90** — is the browser a different class of facts, or only a transport to one? | The browser row of §3's anchor column. Arm 4 can show any agentic effect is **model, not modality**. Arm 3 can show the standing refusal of visual-LLM judges costs something real. | **No.** Largest effect removes one value from one enumerated column. The taxonomy predates the experiment and does not depend on it. |
| **EXP-91** — does measured capability beat the vendor's label, by enough to pay for the probe? | §4 and the opening correction. `label` inside `measured`'s interval readmits labels as a cold-start prior in their own right; `random-admitted` inside both makes the whole ADR moot. | **No.** Every arm needs the router first; it cannot gate what it measures. |
| **EXP-92** — is β a property of the harness, the verifier contract, or the pair? | §5. If the class term dominates, the per-composition dimension is deleted. If ≥50% of cells are unmeasurable, the table cannot be the routing input at all. | **No,** and this is the one that looks as though it should. A one-column table is a special case of a two-column one; building the general case and collapsing later beats blocking on three families' worth of fixtures. |
| **EXP-93** — what does the cold start cost, and does anyone tolerate it? | §4's cold-start rule. A ≥25-point quality cliff during probing means no unattended cold-start routing is offered at all. | **No.** It measures a policy that must exist before it can be measured. |

Applying ADR-0050's three-part test to the set: the largest plausible effect of any of them is
deleting a column, a row or a default from a structure that must be built either way. None can
show that measured capability rows should not exist. Joe's standing instruction — *"it's not
worth it to gate an important feature for 5 days for an experiment that could only ever matter
<5%"* — is satisfied without needing to be invoked, because these effects are not small; they are
**orthogonal to whether the thing gets built**.

Two things would overturn this ADR without any experiment. If the anchor taxonomy in
`qa-automation-and-the-anchor-problem.md` is revised when its fourteen sources are actually
fetched and read — that note says plainly they have not been — §3 inherits the revision. And if
`routing_orchestration_enabled` is never flipped, none of this runs: Stage 3 permits building it,
it passes no gate, and Gate B still forbids pointing any of it at a repository other than this
one.

---

## Publication candidate?

**Not as a paper.** §1, §2 and §4 are prior art; Meta-Harness (COLM 2026) already automates
harness search, and §3's taxonomy is borrowed from within this repository.

**Lane A research note, conditional on EXP-90 running:** the implicit-oracle-versus-static
defect-detection rate, measured against a calibrated same-class baseline, with the cost of the
refused visual-LLM judge measured alongside it, is a number nobody reports. The protocol is
frozen before the run and a null is publishable on the same terms as a hit, which is the test
`../publications/README.md` sets for Lane A.

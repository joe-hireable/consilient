# Living documentation: specs and plans that update themselves without drifting or lying

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** § 10 (EXP-99 and the maintained-prose cheaper kill).

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

- **Date:** 2026-08-22
- **Status:** Specification. Decided by ADR-0073 (PROVISIONAL — EXP-99 can kill it).
- **Author:** Cursor dispatch `20260822T123007-cbcf603df9`. The requirement is the principal's,
  quoted verbatim below; the mechanism is this dispatch's design and carries no claim on his
  authority beyond the quote.
- **Class under its own rules:** *written* — this document contains judgement. Its falsifier is
  in § 10.

## 1. The requirement

The principal, 22 August 2026, verbatim (`docs/00-context/the-machine-2026-08-22.md`, "Living
specs"): [cited]

> "All of this needs to be baked into the SPECS. They need to be living specs and living plans that
> are continuously and autonomously updated and executed by our orchestrators and swarms."

Source: docs/00-context/the-machine-2026-08-22.md:65

This is an architectural requirement, not a documentation preference. The question it poses is:
what makes a document *living* without making it *false*? This repository has already measured both
halves of that failure — documents that drifted, and documents that lied — so the design starts
from the measurements.

## 2. The failure inventory this specifies against

Every row is re-derived from a committed artefact or a directory listing on the date given.

| # | Failure | Evidence |
|---|---|---|
| F1 | `AGENTS.md` carried a hand-maintained copy of `consil doctor` output; on 21 Aug 2026 **three of its four claims were wrong**. The repair was to delete the restatement and name the tool the single authority. | [measured] `AGENTS.md`, 21 Aug 2026 |
| F2 | `docs/decisions/index.md` header read "39 ADRs" while the directory held 48 (C3). On 22 Aug 2026 it read "62 ADRs, 21 Aug 2026" while the directory held **67**. | [measured] corrections-2026-08-21; `ls docs/decisions/[0-9]*.md \| wc -l` = 67 on 22 Aug 2026 |
| F3 | `findings-exp43.md` reported "Tests executed per run: 48"; `results-exp43.json` records 44 in 44 of 50 runs (C5). | [measured] corrections-2026-08-21 |
| F4 | `P3-echo.md` inverted ADR-0012's assumption, claiming EXP-47 refuted what EXP-47 vindicated (C4). | [measured] corrections-2026-08-21 |
| F5 | `requirements-source.json` held a fabricated quote (R11) attributed to the principal. `build_requirements.py` rendered it faithfully and `--check` was green: **generation guarantees freshness, not truth.** He caught it himself. | [measured] `docs/40-spec/requirements.md` provenance warning |
| F6 | `scripts/build_requirements.py --check` — the one worked example of generated-and-checked documentation — **is run by nothing**: no CI step, no hook, no test invokes it. The pattern exists and is already bypassed. | [measured] grep of `.github/`, `.githooks/`, `tests/`, 22 Aug 2026 |
| F7 | `docs/decisions/README.md` declares `index.md` "generated; do not hand-edit". No generator exists. A documented rule with nothing behind it, in the file that defines the rules. | [measured] `scripts/` listing, 22 Aug 2026 |
| F8 | Three decisions were filed under the principal's name that he never made; he caught the third himself. The repair cost is recorded in `docs/00-context/corrections-2026-08-21.md`. | [measured] |
| F9 | 27 dispatch timeouts are recorded in the local trajectory; each discarded whatever was unstaged. A living document whose update mechanism is an agent's working tree loses updates to the clock. | [measured] dispatch brief, 22 Aug 2026 |

Two lessons fall out:

1. **A document that restates a fact a tool can produce is a second source of truth, and it will
   drift** (F1, F2, F3). The repair is never "maintain it more carefully"; it is "generate it, or
   point at the authority".
2. **A generated document can be faithfully rendered from a false source and is believed more, not
   less, because it is generated** (F5, F8). Freshness and truth are different axes, and any design
   that conflates them manufactures confident error at scale.

## 3. The line: what is generated and what is written

Every document in this repository is exactly one of three classes. There is no fourth class; the
missing fourth class — *maintained* prose, hand-edited to stay current — is the class that drifts,
and it is abolished. [asserted]

### Class G: generated

A document is generated when **every load-bearing fact in it is produced by a named script from a
named source**, and it contains no prose judgement at all.

Contract:

- The header names its **producer** (script path) and its **source** (artefact path plus SHA-256).
- Regeneration is **byte-identical** for an unchanged source. No wall-clock timestamp is embedded;
  the time of generation lives in the commit, not the artefact. (`build_requirements.py` already
  has this property. [measured])
- The producer ships a `--check` mode that exits non-zero when the committed document differs from
  a fresh render, and **CI runs it**. A generated file nobody verifies is a hand-edited file
  waiting to happen — and F6 measures that this is not hypothetical: the existing check has zero
  callers today.
- A generated document may not be hand-edited; the edit is discarded by definition at the next
  regeneration, and `--check` refuses the tree in between.

### Class W: written

A document is written when it contains judgement: designs, decisions, interpretations, plans of
record. Contract:

- Every claim carries an evidence tag (I3, existing).
- It names **what would falsify it** — the observation that would make its author withdraw it. A
  written document without a falsifier is opinion asking to be believed; ADRs already carry
  "What would overturn this"; this spec generalises the requirement to every class-W document.
- It carries a **review-by date**. A written document whose date has passed is *known-stale*, which
  is an honest state; the failure is being silently stale (F1–F4).

### Class S: state projections

A **living plan is not a file that is edited; it is a query over append-only state.** The truth is
the trajectory and work-item record (`events.py` is the single append-only writer; `work_items.py`
is the task substrate); any rendered plan, queue or dashboard is a projection of that state,
regenerated on read. This is V0-01/V0-02 generalised from runtime state to plans: SQLite is a
projection of the JSONL log, and a plan document is a projection of work-item state. Orchestrators
"update the plan" by **appending events**, never by editing the rendering — which is also the only
update discipline that survives F9, because an appended event is durable the moment `append()`
returns, while an edited file lives or dies with the session. [asserted]

### The check that fails when a written document contradicts a generated one

Working principle 3: a chokepoint without a lint rule banning bypass is not a chokepoint. Three
checks, in increasing order of power and decreasing order of what they can honestly catch: [asserted]

1. **The generator manifest.** A single machine-readable manifest
   (`docs/generated-manifest.json`) lists every class-G document, its producer, its source and its
   check command. CI runs every entry's `--check`. Admission to the manifest is how a document
   class becomes generated; there is no other way. *This commit ships the specification; the
   manifest and its CI step are a same-commit condition on the implementation (ADR-0073
   Enforcement).*
2. **The restatement lint.** A written document may **point at** a generated surface but may not
   **restate** its machine-checkable content. Concretely: prose outside the manifest may not
   contain literal restatements of named generated values — the ADR count, a requirement status
   tally, a gate condition table, a β figure. F1 is the worked example: the repair was deletion
   plus a pointer, and the lint is that repair made permanent. The lint owns a named list of
   generated surfaces and fails CI when prose restates one.
3. **The audit.** What checks 1–2 cannot catch (§ 4) is caught by a scheduled adversarial re-read
   — a *different class of facts* from any generator, because it re-derives claims from the
   primary artefacts rather than from the documents. Its measured yield in this repository: six of
   six candidate claims destroyed in one night (corrections-2026-08-21). [measured] The audit is a
   first-class component with a cadence, not an apology for the lint's limits.

## 4. Drift detection: what can be detected, and what honestly cannot

**Detectable mechanically, and specified:**

| Signal | Detects | Status |
|---|---|---|
| Generated-vs-committed diff (`--check`, byte comparison) | Any edit or staleness in a class-G document | Exists for `requirements.md`; **unwired** (F6); generalised by the manifest |
| Duplicate record identifiers | Two ADRs or experiments sharing a number | Exists: `check_record_numbers.py` [measured] |
| Supersession-trail integrity + history ratchet | Silent edits to settled ADRs; missing index rows | Exists: `check_adr_trail.py` [measured] |
| Restatement lint | Prose restating a named generated surface | Specified here; same-commit condition |
| Review-by expiry | A class-W document past its date is flagged known-stale | Specified here |
| Citation liveness | A `[cited]` source that no longer resolves | Specified here; cheap; nobody runs it today |

**Not mechanically detectable, and said plainly:**

- **Paraphrase drift.** A written document whose characterisation of the code has gone false while
  quoting no checkable value. F4 is the shape: an inverted claim, perfectly grammatical, no lint
  can see it. Detection requires re-deriving the claim from the artefact — a different class of
  facts — which is what the audit does and a linter never will.
- **Fabricated provenance with well-formed locators.** F5's quote carried the *form* of
  attribution. A lint can require a locator; it cannot verify the locator against the principal's
  actual transcripts, because a search inside a corpus that contains the quoting file proves
  nothing (the requirements.md warning documents both failed mechanical attempts). [measured] The
  catch came from the principal's own review — a genuinely different class. The honest consequence:
  provenance lint catches *form*; only audit catches *fabrication*.
- **Motivation drift.** A document that stays literally true while becoming misleading about why a
  decision was taken. No signal short of re-litigation detects this; the append-only trail (§ 5)
  is what makes reconstruction possible at all.

A specification that claimed to detect these would be lying about its own reach, which is the
failure this document exists to prevent.

## 5. Autonomous update, without rewriting history

Which classes an orchestrator may rewrite, and what enforces the difference:

| Class | Autonomous operation | Forbidden operation | Enforcement |
|---|---|---|---|
| G (generated) | Regenerate from source; commit the render | Hand-edit; edit the source to fit a desired render | Manifest `--check` in CI; producer names itself in the header |
| S (state projection) | Append events through `events.py`; re-render | Edit the projection; write state anywhere but the single writer | V0-01/V0-02 (existing); `test_no_new_event_may_bypass_append` (existing) [measured] |
| Append-only records: ACCEPTED ADRs, register entries after any recorded outcome, corrections, the principal's verbatim words | Append: a new ADR superseding; a dated `**Update:**` section on a PROVISIONAL entry | Edit, delete or "refresh" settled text | `check_adr_trail.py` ratchet (existing for ADRs); **extension of the same ratchet to register entries and context corrections is a same-commit condition** |
| W (written) | Add a dated, authored section; supersede the document | Silent edit of existing prose | The ratchet generalised; review-by date |

The trail of reversals is the most valuable thing in `docs/decisions/` and the first thing people
delete; an autonomous updater with edit rights would delete it continuously, politely, and with a
green check. Append-only is therefore not conservatism — it is the property that makes the audit
(§ 3, check 3) possible, because an auditor can only re-derive what was never erased. [asserted]

## 6. Provenance: who wrote it

F8 is the costliest failure in the inventory and V0-18 already reserves the principal's authorship
of *decisions*. This specification extends the same rule to *text*: [asserted]

1. **The principal's words appear verbatim or not at all.** Quote blocks only, each carrying a
   retrievable locator (transcript and date). An obligation *derived* from his words is labelled
   derivation, with the quote adjacent. An agent's inference is labelled inference. The
   requirements.md provenance warning is the worked template. [measured]
2. **Every generated document carries its own provenance header**: producer, source, source hash —
   and, where the source itself contains attributed material, the provenance *warning*. F5 is the
   reason the warning travels with the render rather than living in the source alone.
3. **Every autonomous write is an authored event.** Actor = run id, appended through the single
   writer; commits carry `CONSILIENT_RUN_ID` under the existing attribution gate. [measured] An
   autonomously updated document can therefore always answer "who wrote this line" from the log,
   not from the prose.
4. **The lint:** a check that fails any quote block attributed to the principal without a locator.
   Its limit is stated in § 4: it catches form, not fabrication. Fabrication is the audit's job,
   and the audit's authority comes from being a different class of facts — the principal's review
   against the real transcripts — not from being a cleverer search of the same corpus.

This makes an agent's inference structurally unable to *become* his instruction: the channels are
separate (event authorship versus human-decision events under V0-18), the text is labelled, and
the record of who wrote what is append-only. It does not make fabrication impossible; nothing
does. It makes fabrication *attributable and survivable*, which is what F8's repair actually cost. [asserted]

## 7. The organisation question, answered against the frozen bar

`docs/00-context/agentic-organisation-bar-2026-08-22.md` was frozen before this design was written.
Its tests bind as follows: [asserted]

- **Existence and different class (tests 1–2).** This specification convenes **no agents**. Living
  documentation is a property of generators, append-only state and checks — not a squad. The two
  classes of facts it relies on are *execution* (running the producer, the lint, the tests) and
  *adversarial re-derivation from primary artefacts* (the audit, ultimately the principal's
  review). A second model reading the same document would be echo and is not proposed.
- **Ownership (test 3).** Each class-G document has exactly one owner: its producer script. Each
  class-W document has one accountable author of record per section. No dual axis.
- **Verifier composition (test 5).** One verifier exposure per document: its `--check`. No
  candidate-shopping exists to bound; `n_max` arithmetic does not bind a design with one candidate.
- **Principal authority (test 6).** § 6. No agent originates his words, his approvals, or the
  appearance of either.
- **Budget and termination (test 7).** Autonomous update is bounded by construction: regeneration
  is a deterministic render, not an agent loop; the audit cadence is fixed and its output is a
  bounded report. Nothing here runs open-endedly.
- **Outcome (test 8).** The outcome measure is EXP-99's: contradictions detected per claim per
  class, time-to-detection, and downstream propagation count — artefact verdicts, not sentiment.

## 8. Reuse boundary

This design extends existing machinery and adds none beside it: `events.py` (single append-only
writer), `work_items.py` (task substrate whose projections are the living plans), `recall.py`
(bounded verbatim context for the audit), `scripts/build_requirements.py` (the generator pattern,
generalised — not duplicated), `check_record_numbers.py` / `check_adr_trail.py` (the ratchets,
extended in path set), the commit-attribution gate (authorship of autonomous writes). No new
`consil` subcommand (the surface is pinned at six), no second orchestrator, no gate condition
changes, `routing_orchestration_enabled` stays `false`, and `src/consilient/` stays inside its
AST lock. [asserted]

## 9. What this specification cannot do

- It cannot detect paraphrase drift, well-formed fabrication, or motivation drift (§ 4). It buys
  detection where detection is mechanical and pays for audit where it is not.
- It cannot make a false source render falsely (F5). It can make the falsehood attributable,
  bounded by provenance warning, and visible to audit.
- It cannot recover updates lost with a session (F9) for anything that remains a file rather than
  appended state. That is the argument for class S, not a solved property of it.

## 10. What would falsify this specification

- EXP-99 fires its stopping rule: generated-and-checked classes accumulate undetected
  contradictions at a rate **not below** maintained prose, or a generated document propagates a
  contradiction to three or more downstream artefacts undetected by its check. Either result kills
  the generalisation; the manifest classes revert to written-with-review-date.
- A cheaper kill: someone exhibits a maintained-prose class in this repository whose measured drift
  rate over the window is zero without any check — evidence that discipline, not generation, was
  the active ingredient, in which case the machinery is overhead and should be cut.

## 11. The strongest case for leaving documentation alone

Stated in full in ADR-0073's "Evidence against", and answered there. The short form: stale
documents are visibly stale and are discounted; a freshly rendered, CI-badged document is
*believed* — automation bias is the measured human response [cited: Parasuraman & Riley 1997,
*Humans and Automation: Use, Misuse, Disuse, Abuse*, Human Factors 37(2),
doi:10.1518/001872097778543886] — so an autonomously updated wrong document does more damage than
a stale one, and F5 proves the generator renders falsehood as faithfully as truth. The answer is
that the alternative observed in this repository was not "no documentation" but **stale
documentation that was believed anyway** (F1 drove behaviour for a day; F2 sits in the index
today). Freshness and truth are separate axes; this design assigns generation to freshness,
provenance to authorship, falsifiers to truth, and audit to the residue — and concedes the
residual by making the provenance warning ride on every generated render.

# 0073. Living documentation is generated-and-checked or append-only — never maintained

- **Status:** PROVISIONAL — EXP-99 can kill it and can confirm only the document classes it measures
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (the requirement, quoted verbatim in the specification); Cursor dispatch
  `20260822T123007-cbcf603df9` (the mechanism, which he has not reviewed)
- **Inquiry tier reached:** T1 — grounded in nine measured incidents in this repository. No
  executable model: the decision is a classification plus enforcement wiring, with no continuous
  decision variable to optimise, so the inquiry-tier gate does not admit one.
- **Executable model:** none — naming and classification decisions do not get one
  (`docs/20-design/inquiry-tier.md`).

## Context

The principal, 22 August 2026 (`docs/00-context/the-machine-2026-08-22.md`, verbatim):

> "All of this needs to be baked into the SPECS. They need to be living specs and living plans that
> are continuously and autonomously updated and executed by our orchestrators and swarms."

The repository's measured relationship with its own documents is the context. `AGENTS.md` carried a
hand copy of `consil doctor` output of which three of four claims were wrong on 21 August 2026
[measured]; the decision index read "39 ADRs" over 48 files, and "62 ADRs" over 67 files on 22
August [measured]; `findings-exp43.md` reported 48 tests where the results file records 44
[measured, C5 in `../00-context/corrections-2026-08-21.md`]. The one generator in the repository,
`scripts/build_requirements.py`, renders `requirements.md` from an audited source and its
`--check` passes — **and nothing runs it**: no CI step, hook or test invokes it [measured, 22
August 2026]. `docs/decisions/README.md` already declares `index.md` "generated; do not hand-edit"
and no generator exists [measured]. The documented rule without the check is principle 3's
canonical failure, sitting in the file that defines the rules.

The companion failure is worse. `requirements-source.json` held a fabricated quote attributed to
the principal (R11); the generator rendered it faithfully and the check was green while the content
lied [measured]. Three decisions were filed under his name that he never made [measured]. Any
design for *autonomous* documentation that does not make that structurally impossible is a machine
for manufacturing his authority.

This is not a one-way door — document classes can revert to written-with-review-date — but more
than a handful of artefacts depend on the classification, so it is recorded here.

## Decision

Every document in this repository is exactly one of three classes, and the fourth class —
*maintained* prose, hand-edited to stay current — is abolished:

1. **Generated (G):** every load-bearing fact produced by a named script from a named source; the
   header names producer, source and source hash; regeneration is byte-identical (no embedded
   wall-clock); the producer's `--check` runs in CI via a single generator manifest. No prose
   judgement, no hand edits.
2. **Written (W):** judgement-bearing prose. Every claim tagged (I3), a named falsifier, a
   review-by date after which the document is *known-stale* rather than silently stale.
3. **State projections (S):** living plans are queries over append-only state, not edited files.
   Orchestrators update plans by appending events through the single writer (`events.py`); the
   rendering is regenerated on read. V0-01/V0-02 generalised from runtime state to plans.

Autonomous agents may regenerate class G, append to class S, and append dated authored sections to
class W and to append-only records. They may never edit settled text: ACCEPTED ADRs, register
entries after any recorded outcome, corrections, and the principal's verbatim words are
append-only, and a changed mind is a new ADR that supersedes.

Provenance extends V0-18 from decisions to text: the principal's words appear verbatim with a
retrievable locator or not at all; derived obligations are labelled derivation; agent inference is
labelled inference; every autonomous write is an authored event attributable through the
commit-attribution gate.

The full contract, the drift-detection inventory, and the honesty section on what cannot be
detected are the specification:
`../superpowers/specs/2026-08-22-living-documentation.md`.

## Evidence

- `[measured]` Nine drift and provenance incidents in this repository, each re-derived from
  committed artefacts: the specification's § 2 table (F1–F9) carries them with their sources.
- `[measured]` The generated-and-checked pattern already exists and works where it is wired:
  `requirements.md` matches its source today (`--check` exit 0, 22 August 2026) — and the check
  has no caller, so the pattern's enforcement gap is measured, not hypothetical.
- `[measured]` The audit mechanism this decision relies on for what lint cannot catch has a
  measured yield: six of six candidate publishable claims destroyed in one night
  (`../00-context/corrections-2026-08-21.md`).
- `[measured]` EXP-45 measured condensation dropping ~59% of bounded verbatim context, which is
  why the audit path re-derives from primary artefacts rather than summarising documents.
- `[cited]` Whewell's first clause (`CONSILIENCE.md`): a conclusion whose provenance is discarded
  cannot participate in consilience. Append-only records are what keep provenance undiscarded.
- `[cited]` Parasuraman & Riley (1997), *Humans and Automation: Use, Misuse, Disuse, Abuse*,
  Human Factors 37(2), doi:10.1518/001872097778543886 — automation bias: output perceived as
  machine-produced is over-trusted. This is the core of the evidence against, and the reason every
  generated render carries its provenance warning.
- `[asserted]` The classification itself — that these three classes cover every document this
  project needs, and that abolishing the fourth costs less than the drift it causes.

## Evidence against

**The strongest form of the objection: autonomously updated documentation is worse than stale
documentation.** Stale documents announce themselves — dust, old dates, a reader's discount. A
freshly rendered, CI-badged document is believed, and automation bias is the measured human
response to machine-produced output [cited: Parasuraman & Riley 1997, above]. So:

- `[measured]` **Generation guarantees freshness, not truth.** `build_requirements.py` rendered a
  fabricated quote faithfully and `--check` was green while R11 was a lie. A hand error poisons one
  document; a source defect poisons every render, uniformly, with a badge.
- `[asserted]` **Goodhart:** once "generated" is the trust signal, effort moves from "is it true"
  to "is the check green". The check becomes the target.
- `[measured]` **Autonomy launders inference into authority at scale.** The three misattributed
  decisions were hand-written and still slipped through; automation would have produced them
  wholesale, each indistinguishable from the genuine.
- `[asserted]` **The honest default is to write less.** Much maintained prose exists because
  writing is cheap and deleting feels like loss. Abolishing the class by fiat risks deleting
  documents that were load-bearing precisely because a human kept them current.

**Why we decided anyway.** The observed alternative in this repository was never "no
documentation"; it was **stale documentation that was believed anyway** — F1's doctor copy drove
behaviour for a day, and F2's wrong count sits in the index as this is written. [measured]
Freshness and truth are separate axes, and the objection is answered by keeping them separate:
generation owns freshness, provenance owns authorship, falsifiers own truth, and the audit owns
the residue. The R11 case is the objection's strongest instance, and its lesson is that the defect
entered at the *source*, by hand — the generator merely did its job — so the provenance rule binds
sources, not just renders.

**What is conceded.** A generated document *is* believed more; that is the whole of the objection
that survives. So the provenance warning rides on every generated render (requirements.md's header
is the template), the audit cadence is load-bearing rather than optional, and admission to the
manifest is per-class: a document class whose source cannot be made truthful stays written and
hand-reviewed. If EXP-99 shows generated classes accumulating believed-wrong content at a rate not
below maintained prose, this decision is wrong and reverts.

**Weaknesses in our own evidence.** Nine incidents from one repository over four days, one
auditor, and a selection effect: the incidents were found by looking for defects, so they say
nothing about how many documents are *fine*. The belief half of the objection (over-trust) is
cited from human-factors literature, not measured in this system; EXP-99's proxy
(time-to-detection, propagation count) measures consequences of over-trust, not trust itself.

## Consequences

**Positive** — a document can never silently drift from a mechanical source again without a CI
failure; the trail of reversals becomes structurally undeletable by agents; the principal's words
can no longer be manufactured by inference, only fabricated — and fabrication is attributable and
auditable. Living plans become durable by construction (appended state survives the timeout that
kills an edited file; F9). [asserted]

**Negative** — every generated class needs a producer, a source and a check, which is real
machinery per document; the restatement lint will false-positive on legitimate quotation and will
need a suppression grammar that must itself not become a bypass; review-by dates create a
recurring audit obligation that outlives the enthusiasm that set it. [asserted]

**Neutral but load-bearing** — `docs/decisions/index.md` and every other hand-maintained restatement
moves to class G or is deleted; the CLI surface stays pinned at six; no gate condition changes;
`routing_orchestration_enabled` stays `false`; `src/consilient/` stays inside its AST lock; nothing
here is a new orchestrator. [asserted]

## Enforcement

This commit records the decision, the specification, the index row and EXP-99 only; it ships no
implementation. [measured]

- Check: the implementation commit must ship (a) the generator manifest and a CI step running every
  entry's `--check` — starting with the two that already have producers or none:
  `build_requirements.py --check` (exists, unwired, F6) and a generator for `docs/decisions/index.md`
  (declared generated, no generator, F7); (b) the restatement lint over the manifest's named
  surfaces; (c) the extension of the ADR-trail ratchet's path set to register entries after outcome
  and to `docs/00-context/corrections-*.md`; (d) the principal-quote locator lint. [asserted]
- Fails CI: no — no implementation ships in this commit. [measured]
- Added in the same commit as the implementation: the checks above are a same-commit condition on
  any later implementation, per principle 3 and standing invariant I1. [asserted]

Until then, `requirements.md` remains the only class-G document, and its `--check` remains unwired;
that gap is recorded here rather than silently repaired in a documentation commit.

## What would overturn this

EXP-99 (`../10-research/experiment-register.md`) kills the generalisation if, over its frozen
window, generated-and-checked classes accumulate undetected contradictions at a rate not below
maintained prose, or any generated document propagates a contradiction to three or more downstream
artefacts undetected by its check. The cheaper kill: a maintained-prose class shown to have drifted
zero times over the window with no check at all — evidence that discipline, not generation, was the
active ingredient. [asserted]

## Publication candidate?

**No.** The incidents are this repository's, the pattern (docs-as-code with drift checks) is
standard practice elsewhere, and the one load-bearing empirical claim — that generated-and-checked
documentation drifts less without being believed more — is exactly what EXP-99 has not yet
measured. [asserted]

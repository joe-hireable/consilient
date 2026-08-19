# 0008. Name the project Consilience

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground — availability checked against live registries
- **Executable model:** none — no free parameter. Gate G4 not satisfied.

## Context

Naming is a one-way door once packages are published and a repository is public. Q18 left
it open. The requirement Joe set: the name must *illustrate the concept*, in the manner of
Graphify or MemPalace, rather than describe a category.

The concept as Joe framed it: the AI equivalent of convening Nobel laureates and
world-class specialists, perfectly organised.

## Decision

**Consilience.** Repository `joe-hireable/consilience`. Packages `consilience`, short
binary `consil`.

## Evidence

`[measured]` — live registry checks, 2026-08-19:

| Surface | Status |
|---|---|
| npm `consilience` / `consil` | free / free |
| PyPI `consilience` / `consil` | free / free |
| crates.io `consilience` | free |
| Homebrew formula | free |

`[cited]` — semantics. *Consilience* (Whewell, 1840; revived by E. O. Wilson, 1998) is the
convergence of evidence from **independent** sources. That is not a decoration: it is
`0010`'s exogenous-signal rule stated as a single word. A convened panel that shares one
brief is worthless; a convened panel where each participant arrives holding different
evidence is the only structure the theorem in
`../10-research/literature-review.md` §3 permits. The name encodes the constraint.

`[cited]` — clears the collisions that killed the alternatives: no "open" prefix
(OpenHarness, OpenHands, OpenClaw, opencode, OpenDevin), no "harness" (Harness Inc holds
a trademark in software delivery tooling; OpenHarness, DeepSeek Harness, Meta-Harness,
HarnessBank, HarnessX all occupy the term), no "meta" (Meta), no "agent".

## Evidence against

- **Four syllables, and most people will not know how to say it on sight**
  (kon-SIL-ee-ənts). That is a real adoption tax for an open-source developer tool, and the
  single strongest argument against. Mitigations: the short binary `consil`, and a one-line
  gloss directly under the repository title doing double duty as pronunciation aid and
  statement of the design rule.
- The GitHub org `/consilience` is taken, as are `/consilient`, `/consilium`,
  `/consilience-ai` and `/consilience-dev`. Not blocking — the project lives under Joe's
  existing account, matching `joe-hireable/jobboard-v2`.
- A common English word with a distinguished pedigree is hard to trademark defensively.
  Cuts both ways: also hard for anyone else to have locked up.
- Rejected alternatives, for the record: **Prodigy Harness** (namespace collision with
  Explosion AI's Prodigy; "Harness" encumbered; and a boastful name fights a project whose
  credibility rests on admitting what is unmeasured). **OpenMesh** (PyPI taken; collides
  with the RWTH Aachen mesh library, Open-Mesh networking, and a crypto project).
  **Solvay** (excellent metaphor, free on both registries, but Solvay S.A. is a large
  chemicals company — a live trademark question). **Assay / Plumb / Sieve / Tolerance**
  (all taken on both registries). **MeshGauge**, **Porosity**, **Truing** (all free, all
  name the measurement rather than the method).

## Consequences

**Positive.** Encodes the project's central constraint rather than an aspiration. Survives
every architectural fork still open in `0001` — standalone, plugin, or library — because it
names neither a category nor a mechanism. Clean across all four package registries.

**Negative.** Pronunciation friction. Requires a gloss everywhere the name appears cold.

**Neutral but load-bearing.** Commits the project to the evidence-convergence framing.
If the design ever moves away from independent-evidence-first, the name becomes a lie.

## Enforcement

- The one-line gloss appears under the title in `README.md` and in package descriptions:
  *"when independent lines of evidence converge on the same conclusion"*.
- Reserve `consilience` and `consil` on npm, PyPI, crates.io **before** the repository goes
  public. Registry availability is a snapshot, not a reservation.

## What would overturn this

- A trademark search returns a conflict. **Not yet run** — folded into the same solicitor
  pass as `0004`. This ADR is ACCEPTED on registry and semantic grounds only; the legal
  check is outstanding and could force a rename.
- Pronunciation friction proves to measurably suppress adoption. Unlikely to be
  distinguishable from ordinary obscurity, so this is close to unfalsifiable in practice —
  noted as a weakness of this ADR rather than a real trigger.

## Publication candidate?

No.

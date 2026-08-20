# Consilience → Consilient Rename Ambiguities Report

- **Date:** 2026-08-20
- **Author:** Automated Rename Safety Classifier (`.github/scripts/check_rename_safety.py`)
- **Context:** Project rename from **Consilience** to **Consilient** under ADR-0038.
- **Purpose:** Present all classified `ambiguous` occurrences for explicit human adjudication rather than laundering AI guesses into silent edits.

---

## Summary of Scan

- **Total occurrences of `[Cc]onsilienc\w*` scanned:** 339
- **Classified as `renameable`:** 47 (safe living documentation references to project/product name)
- **Classified as `protected`:** 258 (quotes, Whewell concept noun, accepted ADRs, historical transcripts, `CONSILIENCE.md`, code identifiers)
- **Classified as `ambiguous`:** 34 (listed below for human review)

---

## Ambiguous Occurrences by Category

### 1. Bodies and Titles of PROVISIONAL, PROPOSED, or DEPRECATED ADRs (32 occurrences)

*Rationale for Ambiguity:*
Under ADR-0038 and the project's evidence rules, ADRs are formal architectural records. While `ACCEPTED` and `SUPERSEDED` ADRs are strictly immutable historical records (`protected`), draft (`PROVISIONAL`, `PROPOSED`, `DEPRECATED`) ADRs remain open for refinement. Mechanically altering proposals risks subtly changing argumentation, citations, or intent without author review.

| File | Line | Current Content | Recommended Human Action |
|---|---|---|---|
| `docs/decisions/0016-skill-distribution-mcp-plugins.md` | 73 | `workflow moves to Consilience (`0015`).` | Rename to `Consilient` when ADR-0016 is accepted. |
| `docs/decisions/0016-skill-distribution-mcp-plugins.md` | 83 | `### 2. Publishing Consilience's own skills → bundled inside the distributed package` | Rename to `Consilient's` when ADR-0016 is accepted. |
| `docs/decisions/0016-skill-distribution-mcp-plugins.md` | 119 | `**This matters more here than in most projects.** Consilience's entire thesis is that you` | Rename to `Consilient's` when ADR-0016 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 1 | `# 0017. The bootstrap harness — Claude Code configured as a working prototype of Consilience` | Rename to `Consilient` when ADR-0017 is reviewed/accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 12 | `configuration used to build Consilience should be **a manual implementation of what` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 13 | `Consilience will automate** — same skills, same memory layers, same evidence discipline,` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 38 | `**Every manual step performed in Claude Code that Consilience should automate is a` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 42 | `This inverts the usual order. Rather than specifying Consilience and then checking whether` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 119 | `Skills, MCP and memory config all migrate to Consilience under `0014`/`0016` unchanged.` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 124 | `**Neutral but load-bearing.** Consilience must eventually consume these as *layers*, not` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0017-bootstrap-harness.md` | 133 | `Consilience automated it, and that should be a commit reference, not a silent edit.` | Rename to `Consilient` when ADR-0017 is accepted. |
| `docs/decisions/0022-safety-floor-and-moderation.md` | 42 | `Consilience is MIT-licensed, local-first, with no telemetry (`0004`, `0006`). Therefore:` | Rename to `Consilient` when ADR-0022 is accepted. |
| `docs/decisions/0024-commercialisation-and-telemetry.md` | 123 | `1. **Hosting and operation.** Running Consilience for people who do not want to. Requires no` | Rename to `Consilient` when ADR-0024 is accepted. |
| `docs/decisions/0026-admit-only-budget-and-hardware-feasible-backends.md` | 188 | `Consilience will wrap an installed fit provider rather than build and maintain a model` | Rename to `Consilient` when ADR-0026 is accepted. |
| `docs/decisions/0026-admit-only-budget-and-hardware-feasible-backends.md` | 209 | `or another tool outside Consilience. [asserted]` | Rename to `Consilient` when ADR-0026 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 14 | `ADR-0001 correctly put Consilience above existing coding harnesses, but it treated a` | Rename to `Consilient` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 28 | `Consilience is intended to be domain-blind even though coding is v0. [asserted] OpenRouter` | Rename to `Consilient` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 60 | `Consilience build a generic tool loop. [asserted] Coding tasks use an existing coding` | Rename to `Consilient` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 99 | `Consilience's mathematics consumes those data only as a pre-registered prior over model` | Rename to `Consilient's` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 106 | `Consilience selects the model for β-sensitive unattended work. [asserted] OpenRouter may` | Rename to `Consilient` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 109 | `cross-model router is an EXP-22 baseline, not the production Consilience decision, because` | Rename to `Consilient` when ADR-0027 is accepted. |
| `docs/decisions/0027-compose-domain-harness-provider-and-model.md` | 144 | `retaining Consilience's own model decision duplicates part of a maintained commercial` | Rename to `Consilient's` when ADR-0027 is accepted. |
| `docs/decisions/0028-optimise-expiring-subscription-capacity-for-verified-value.md` | 142 | `usage outside Consilience can make every local ledger stale.` | Rename to `Consilient` when ADR-0028 is accepted. |
| `docs/decisions/0029-separate-runtime-resource-state-from-change-intelligence.md` | 12 | `## Update: 2026-08-19 — trace to Consilience` | Rename to `Consilient` when ADR-0029 is accepted. |
| `docs/decisions/0029-separate-runtime-resource-state-from-change-intelligence.md` | 33 | `service availability independently of Consilience. [measured] On 19 August 2026 their` | Rename to `Consilient` when ADR-0029 is accepted. |
| `docs/decisions/0029-separate-runtime-resource-state-from-change-intelligence.md` | 51 | `Consilience records resource state and vendor-change intelligence as separate event` | Rename to `Consilient` when ADR-0029 is accepted. |
| `docs/decisions/0030-size-orchestration-by-usable-context-and-measured-outcomes.md` | 95 | `- `[measured]` Earlier Consilience work required compact handoffs after context compaction;` | Rename to `Consilient` when ADR-0030 is accepted. |
| `docs/decisions/0034-detect-stalls-by-artefact-progress-and-default-to-diagnosis.md` | 87 | `Consilience follows both. On detecting no progress, the supervisor:` | Rename to `Consilient` when ADR-0034 is accepted. |
| `docs/decisions/0036-upstream-first-adopt-contribute-never-silently-fork.md` | 26 | `Consilience *"wraps rather than builds"* hardware fit. [cited]` | Rename to `Consilient` when ADR-0036 is accepted. |
| `docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md` | 18 | `1. Orchestrating on a non-Consilience repository is Stage 3 behaviour.` | Rename to `non-Consilient` when ADR-0039 is accepted. |
| `docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md` | 20 | `3. Gate B condition 4 requires **twenty tickets orchestrated on a non-Consilience repository**.` | Rename to `non-Consilient` when ADR-0039 is accepted. |
| `docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md` | 47 | `non-Consilience repository are what the gate *consumes*, which is the only reading under` | Rename to `non-Consilient` when ADR-0039 is accepted. |

---

### 2. Package Namespace Reservation Manifests (2 occurrences)

*Rationale for Ambiguity:*
These files record package name reservations across npm and PyPI. Modifying the text without checking whether the corresponding package registry reservations exist could make the descriptions inaccurate.

| File | Line | Current Content | Recommended Human Action |
|---|---|---|---|
| `packages/consil/README.md` | 3 | `Reserved short name for **Consilience** (see the `consilience` package). Pre-release;` | Keep as-is or adjust when npm package publication occurs. |
| `packages/consilient/README.md` | 3 | `Name reserved for **Consilience** — an open-source meta-harness for agentic work,` | Update to `**Consilient**` if this package represents the primary distribution. |

### 3. The package *identity*, which is a one-way door and is not prose (added by review)

*Found by reading the manifests rather than the README text the classifier scanned.* The
classifier flagged the two package READMEs, which is right, but the load-bearing string is in
`package.json`, not in prose:

| File | Field | Current value |
|---|---|---|
| `packages/consilient/package.json` | `"name"` | **`"consilience"`** |
| `packages/consilient/package.json` | `"description"` | `Reserved: Consilience — …` |
| `packages/consil/package.json` | `"description"` | `Reserved short name for Consilience (the consilience package) …` |

**The directory is `consilient/` and the package it declares is `consilience`.** That is a
half-swept state in the one place where the two halves have different consequences: a directory
name is free to change and a *published* package name is not.

**Deliberately not changed.** `AGENTS.md` reserves naming to Joe, and a registry name is the
strongest form of that — once published it cannot be recalled, only deprecated. The README
asserts nothing is published yet, which is exactly the window in which the decision is still
free.

**The question for Joe, and it is one question:** should the published packages be `consilient`
(+ `consil`), matching the project, with `consilience` left as a redirect or abandoned? If yes,
both manifests change in one commit and the reservation READMEs follow. If the `consilience`
name is already claimed on npm or PyPI, say so — that changes the answer from "rename" to
"which one points at which".

---

---

## Reversal and Next Steps

- All 34 items above were preserved untouched by the automated rename sweep.
- When an ADR is formally promoted from `PROPOSED`/`PROVISIONAL` to `ACCEPTED`, its text can be reviewed and updated to `Consilient` as part of that transition commit.

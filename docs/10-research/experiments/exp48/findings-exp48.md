# EXP-48 findings — can the defective-guard catalogue be generated mechanically?

**Date:** 20 August 2026  
**Status:** `[measured]` for survivor clustering, P2 catalogue cross-reference, recall and precision metrics; `[asserted]` for architectural implications, stopping rule verdicts, and domain boundaries.  
**Corpus:** EXP-47's 586 non-equivalent surviving true defects across `src/consilient/` (`__init__.py`, `beta.py`, `cli.py`, `events.py`, `projection.py`) cross-referenced against the 25 defective guards catalogued in `docs/50-publications/P2-guards.md` (Table 1, Table 1′, Table 2) plus positive control C1.  
**Privacy discipline:** Per `AGENTS.md`, aggregate metrics and operator descriptions only; zero wholesale source dumps.

---

## Executive Summary

`docs/50-publications/P2-guards.md` catalogues **twenty-five defective guards and one positive control** in this repository that could not fail, were unpassable, or produced uninformative passes. Every entry was found by hand (adversarial audit, cross-family inspection, or manual reproduction). The central question of EXP-48 is: **can this catalogue be regenerated mechanically from EXP-47's mutation testing survivors, converting an $n=1$ hand-audited existence claim into an automated prevalence method?**

### Headline Results `[measured]`

1. **Overall Catalogue Recall is Severely Depressed ($20.00\%$ — 5/25):**
   - Mutation testing on Python source code recovers only **5 of P2's 25 defective guards** (A1, A3, A6, A8, A14).
   - **$68.0\%$ (17 of 25) of P2's catalogued defects live completely outside the reach of program mutation testing**:
     - **ADR / Specification Logic (4):** A2 ($n_{\text{max}} > 1$ algebraic floor), A12 (byte-identical SQLite requirement), A15 (Gate B Stage 3 circularity), B7 (false-safe rate transcription).
     - **CI Workflows & Environment Gaps (2):** A9 (`skills-mirror.yml` symlink valid on Linux CI, broken on Windows), A13 (`invariants.yml` running weak mypy vs strict claim).
     - **Governance Rules & Process Logs (2):** A7 (`AGENTS.md` leak ban with no check), A10 (`gate-bypass-log.md` empty because PR process never ran).
     - **Research Experiment Harnesses, Scripts & Protocols (9):** B1 (frozen byte count heartbeat), B2 (subprocess timeout leaving grandchild processes), B3 (unheld lock release deleting live lock), B4 (checkpoint file overwriting hiding duplicates), B5 (mining script misclassifying CANCELLED runs), B6 (revert detector 0 on fix-forward repos), B8 (blind grader flat tally under balanced arms), B9 (pipeline `| tail` discarding exit code), B10 (external PM projection accepting phantom state).
2. **In-Scope Code-Resident Recall is Moderate ($62.50\%$ — 5/8):**
   - Within the 8 guards residing in `src/consilient/`, mutation survivor clusters recover 5:
     - **A1 (`cli.py` `cmd_replay`):** 20 survivors across lines 67–132.
     - **A3 (`events.py` `_check_human_authority`):** 12 survivors across lines 243–273.
     - **A6 (`events.py` `validate` / `_check_clock`):** 14 survivors across lines 112–302.
     - **A8 (`events.py` `_check_evidence_class`):** 22 survivors across lines 136–156.
     - **A14 (`events.py` `append` / `validate`):** 13 survivors across lines 310–340.
   - The 3 missed code-resident guards (**A4, A5, A11**) have **0 surviving mutants** because dedicated regression tests written to fix them actively kill all first-order syntactic mutants in their immediate constructor, default, and threshold locations.
3. **Cluster Precision is Low ($24.59\%$ — 15/61):**
   - Spatial clustering (line gap $\le 5$) groups the 586 true defects into **61 distinct clusters**.
   - Only **15 clusters (24.59%)** overlap with P2's catalogued guards.
   - **46 clusters (75.41%)** correspond to no P2 guard:
     - **CLI Human Output Formatting (14 clusters, 182 mutants):** table layouts, header banners, column widths, summary text formatting where invariant tests assert `--json` payloads rather than human stdout text.
     - **CLI Gate Requirement Evaluation (12 clusters, 205 mutants):** regex parsing of `EXPERIMENT_REGISTER`, markdown section splitters in `consil gate`.
     - **Events Validation Strings & Edge Guards (7 clusters, 39 mutants):** unasserted `EventError` message string mutations.
     - **Projection DB Indexing & Digest Null Handling (7 clusters, 40 mutants):** fallback column joins, optional metadata extraction.
     - **Beta Statistics Defaults & Slicing (6 clusters, 33 mutants):** Wilson $z=1.96$ parameter variations.
4. **Stopping Rule 2 & 3 FIRED (The Negative Result):**
   - Overall recall $20.00\% < 35\%$ and out-of-scope fraction $68.0\% \ge 50\%$.
   - **Verdict `[asserted]`:** The defective-guard catalogue **cannot be generated mechanically by mutation testing**. Mutation survival and guard vacuity are structurally distinct phenomena.

---

## Part 1 — Cross-Reference Matrix `[measured]`

### P2 Defective Guards vs Mutation Survivor Clusters

| ID | Class | Layer / Location | Guard Description | In Code? | Mutation Survivors | Matched? |
|---|---|---|---|---|---|---|
| **A1** | A | `src/consilient/cli.py:67-132` | `cmd_replay` built projection twice, destroying drift | Yes | 20 mutants (lines 67–132) | **YES** |
| **A2** | A | `docs/decisions/0015` | Gate B2 $n_{\text{max}} > 1$ algebraic floor is $3.125 > 1$ | No | N/A (Governance text) | No (Out of Scope) |
| **A3** | A | `src/consilient/events.py:223-275` | `_check_human_authority` early return on missing decision | Yes | 12 mutants (lines 243–273) | **YES** |
| **A4** | A | `src/consilient/beta.py:64-118` | `Beta.__post_init__` constructor admission invariants | Yes | 0 mutants (killed by test suite) | No (Test-Killed) |
| **A5** | A | `src/consilient/beta.py:58-62` | `lower_bound_on_joint_error` hardcoded dataclass default | Yes | 0 mutants (killed by test suite) | No (Test-Killed) |
| **A6** | A | `src/consilient/events.py:111-306` | `validate` checked ts format, not true clock time | Yes | 14 mutants (lines 112–302) | **YES** |
| **A7** | A | `AGENTS.md` / Governance | Private corpus rule declared with no CI check | No | N/A (Governance text) | No (Out of Scope) |
| **A8** | A | `src/consilient/events.py:130-173` | `_check_evidence_class` early return on missing field | Yes | 22 mutants (lines 136–156) | **YES** |
| **A9** | A | `.github/workflows/skills-mirror.yml` | Symlink check passes on Linux CI, false on Windows | No | N/A (CI Workflow) | No (Out of Scope) |
| **A10** | A | `gate-bypass-log.md` | Log empty because audited PR process never ran | No | N/A (Process Log) | No (Out of Scope) |
| **A11** | A | `src/consilient/beta.py:38` | `MIN_REJECTIONS = 30` unachievable Wilson floor | Yes | 0 mutants (killed by test suite) | No (Test-Killed) |
| **A13** | A | `.github/workflows/invariants.yml` | `mypy --strict` claimed in docs, non-strict in CI | No | N/A (CI Config / Docs) | No (Out of Scope) |
| **A14** | A | `src/consilient/events.py:309-340` | `append()` sole writer bypassed by 92/93 log events | Yes | 13 mutants (lines 310–340) | **YES** |
| **A12** | A′ | `docs/40-spec/v0-draft.md` | Byte-identical SQLite replay requirement impossible | No | N/A (Spec text) | No (Out of Scope) |
| **A15** | A′ | `docs/decisions/0015` | Gate B4 Stage 3 prerequisite circularity | No | N/A (ADR text) | No (Out of Scope) |
| **B1** | B | Experiment Heartbeat | Inferred running from frozen byte count of stopped run | No | N/A (Harness) | No (Out of Scope) |
| **B2** | B | Subprocess Runner | `subprocess.run(timeout=T)` left grandchild pipes open | No | N/A (Harness) | No (Out of Scope) |
| **B3** | B | Lock Helper | `release_lock()` unheld execution deleted live lock | No | N/A (Harness) | No (Out of Scope) |
| **B4** | B | Experiment Runner | Checkpoint full-file rewrite hid duplicate cells | No | N/A (Harness) | No (Out of Scope) |
| **B5** | B | `mine_beta.py` | Retrospective miner counted CANCELLED CI as rejection | No | N/A (Research Script) | No (Out of Scope) |
| **B6** | B | `mine_beta.py` | Revert detector fired 0 times on fix-forward repos | No | N/A (Research Script) | No (Out of Scope) |
| **B7** | B | `docs/decisions/0002` | False-safe rate 0 transcribed from ~0 | No | N/A (ADR text) | No (Out of Scope) |
| **B8** | B | Blinding Protocol | Flat grader summary tally under balanced arms | No | N/A (Protocol) | No (Out of Scope) |
| **B9** | B | Shell Pipeline | Gate piped to `tail` discarded non-zero exit code | No | N/A (Shell invocation) | No (Out of Scope) |
| **B10** | B | PM Integration | External projection accepted invalid state write | No | N/A (External API) | No (Out of Scope) |
| **C1** | C | `EXP-43` (Positive Control) | Parent-commit baseline preventing false drift beta | No | N/A (Methodology) | No (Out of Scope) |

---

## Part 2 — Recall and Precision Summary `[measured]`

### Recall Breakdown
- **Total P2 Catalogue Recall:** **$5 / 25 = 20.00\%$** (95% Wilson CI: $[8.9\%, 39.1\%]$).
- **Code-Resident Recall:** **$5 / 8 = 62.50\%$** (95% Wilson CI: $[30.6\%, 86.3\%]$).
- **Out-of-Scope Artefact Rate:** **$17 / 25 = 68.00\%$** (95% Wilson CI: $[48.4\%, 82.8\%]$).

### Cluster Precision Breakdown (61 Spatial Clusters)
- **Clusters matching P2 Catalogued Guards:** **$15 / 61 = 24.59\%$**.
- **Clusters unmatched to P2 Catalogue:** **$46 / 61 = 75.41\%$**.

### Taxonomy of the 46 Unmatched Clusters `[measured]`

```
46 Unmatched Clusters (499 surviving mutants)
 ├── 14 CLI Human Output Formatting (182 mutants) -> Cosmetic / stdout strings
 ├── 12 CLI Gate Inspection Logic (205 mutants)   -> Markdown / register regex parsing
 ├──  7 Events Validation & Message Strings (39)   -> Unchecked exception messages
 ├──  7 Projection DB & State Digest (40)         -> Secondary column serialization
 └──  6 Beta Statistics Defaults (33)             -> Unchecked Wilson z=1.96 defaults
```

---

## Part 3 — Deep Inspection: Are Unmatched Clusters Real Guards? `[asserted]`

We inspected the largest unmatched clusters in `src/consilient/cli.py` (e.g. `CLUST-31` [59 mutants], `CLUST-32` [54 mutants], `CLUST-20` [43 mutants], `CLUST-29` [34 mutants]).

**Finding `[asserted]`:** None of these clusters represents an uncatalogued "guard that cannot fail".
1. **Human CLI Rendering:** Mutating table formatting or help text survives because the test suite deliberately tests JSON contracts (`--json`) rather than ANSI terminal rendering. This is unasserted presentation code, not a broken invariant.
2. **Gate Parsing Helpers:** In `consil gate`, string matching over `EXPERIMENT_REGISTER` survives on unused status strings. No document makes an unfulfilled architectural guarantee about these parsing branches.
3. **Unchecked Exception Strings:** `pytest.raises(EventError)` without `match="..."` lets error message mutations survive. The invariant *that an error is raised* is verified; only the descriptive text is unconstrained.

---

## Part 4 — Why Mutation Survival and Guard Vacuity Diverge `[asserted]`

The negative result is structural, not an artifact of tool tuning:

1. **A Guard That Cannot Fail is a Claim-vs-Implementation Mismatch:**
   - A vacuous guard requires a **stated claim** (an ADR gate, a specification invariant $V0\text{-}xx$, a governance rule in `AGENTS.md`) that contradicts runtime reality.
   - Mutation testing inspects AST nodes and test assertions; it has **zero access to governance intent, ADR text, CI workflow semantics, or operating system environments**.
2. **The Locus of Vacuity is Governance, Not Syntax:**
   - In a self-verifying meta-harness, $68\%$ of inert checks occur at the governance boundary (ADR formulas, CI configs, log bypasses, research harnesses). Program mutation testing cannot mutate an ADR.
3. **The Regression-Test Masking Paradox:**
   - When a broken guard in code is repaired and fortified with a dedicated test (e.g. A4, A5, A11), the new test immediately **kills all first-order mutants**, making the historical defect invisible to mutation testing.
   - Thus, mutation testing detects *untested code*, whereas P2 catalogues *vacuously tested claims*.

---

## Part 5 — Implications for Publication P2 `[asserted]`

P2's paper draft states:
> *"The evidence establishes existence, not prevalence, a rate or a comparison... The cheapest falsification is also the most damaging one: run mutation testing over this repository's own checks. If mutation score identifies the same inert guards, the instrument was already free, off-the-shelf and forty-eight years old, and §6 is a re-derivation."* (§8.3)

**EXP-48 disproves that threat.** Mutation score **does not** identify the guard catalogue ($20\%$ overall recall, $75.4\%$ noise clusters). P2's hand-audit methodology is substantiated as a distinct, non-redundant discipline: **vacuity in socio-technical governance cannot be retired by syntactic mutation testing.**

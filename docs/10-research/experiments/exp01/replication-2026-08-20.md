# EXP-01 Independent Replication & Cross-Family Audit Reconciliation

**Date:** 20 August 2026  
**Auditor:** Cursor (Gemini 3.7 Flash)  
**Primary Records:** `data/jobboard-v2-prs.json`, `data/hireable-platform-prs.json`, `data/red-cells-evidence.json`  
**Status:** `[measured]` for all raw counts, contingency tables and Wilson score intervals; `[algebra]` for rate derivations and sensitivity bounds; `[asserted]` for methodological critique.  
**Privacy Boundary:** Aggregate metrics only. No PR titles, no file paths, no commit messages, and no internal check names are recorded.

---

## 1. Executive Summary & Replication of the Four Headline Claims

All four headline claims produced by the orchestrator were independently derived from primary JSON records. Below is the side-by-side comparison between the claimed figures and the independent replication.

| Claim | Target Metric / Phenomenon | Claimed Value | Independently Derived Value | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Claim 1** | $\alpha = P(\text{red} \mid \text{good})$ on `jobboard-v2` | `23/97 = 0.2371` `[0.1635, 0.3307]` | **`23/97 = 0.2371`** `[0.1635, 0.3307]` | **Replicated** `[measured]` |
| | $\alpha = P(\text{red} \mid \text{good})$ on `hireable-platform` (verdict-only) | `4/28 = 0.1429` `[0.0570, 0.3149]` | **`4/28 = 0.1429`** `[0.0570, 0.3149]` | **Replicated** `[measured]` |
| | $\alpha$ on `hireable-platform` (all good PRs in denominator) | `4/34 = 0.1176` | **`4/34 = 0.1176`** `[0.0467, 0.2662]` | **Replicated** `[measured]` |
| **Claim 2** | `_bad` label source: reverts on `jobboard-v2` | `0 / 203` (0.0%) | **`0 / 203`** (0.0% revert, 203 hotfixed) | **Replicated** `[measured]` |
| | `_bad` label source: reverts on `hireable-platform` | `0 / 21` (0.0%) | **`0 / 22`** total bad (`0 / 21` with CI verdict) | **Replicated** `[measured]` |
| **Claim 3** | File size: bad-and-red vs bad-and-green (`jobboard-v2`) | Median 13 vs 5 (ratio 2.60) | **Median 13 vs 5** (ratio **2.60**; mean 26.8 vs 9.4) | **Replicated** `[measured]` |
| | File size: bad-and-red vs bad-and-green (`hireable-platform`) | Median 6 vs 2 (ratio 3.00) | **Median 6 vs 2** (ratio **3.00**; mean 22.3 vs 8.7) | **Replicated** `[measured]` |
| **Claim 4** | Cancelled-only failures in red cells (`jobboard-v2`) | 15/75 bad-red; 3/23 good-red | **15/75** bad-red (20.0%); **3/23** good-red (13.0%) | **Replicated** `[measured]` |
| | Rate shift excluding cancelled runs: $\beta$ (`jobboard-v2`) | `0.6305 → 0.6809` | **`128/203 = 0.6305 → 128/188 = 0.6809`** | **Replicated** `[algebra]` |
| | Rate shift excluding cancelled runs: $\alpha$ (`jobboard-v2`) | `0.2371 → 0.2128` | **`23/97 = 0.2371 → 20/94 = 0.2128`** | **Replicated** `[algebra]` |

---

## 2. Full Contingency Tables

Per working principle 3 and EXP-01 guidance, all conditional probabilities are read off explicit contingency tables rather than remembered marginals.

### 2.1 `jobboard-v2` (300 Merged PRs) `[measured]`

| Artefact Status | CI Green | CI Red | No CI (`_ci == "none"`) | Total Evaluated (Green + Red) | Total PRs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bad** (`_bad == True`) | 128 | 75 | 0 | 203 | 203 |
| **Good** (`_bad == False`) | 74 | 23 | 0 | 97 | 97 |
| **Total** | 202 | 98 | 0 | 300 | 300 |

- Baseline $\alpha = P(\text{CI red} \mid \text{good}) = 23 / 97 = 0.2371$ (Wilson 95%: `[0.1635, 0.3307]`).
- Baseline $\beta = P(\text{CI green} \mid \text{bad}) = 128 / 203 = 0.6305$ (Wilson 95%: `[0.5627, 0.6937]`).
- Base rate $P(\text{bad}) = 203 / 300 = 0.6767$ `[0.6225, 0.7266]`.
- Transpose $P(\text{bad} \mid \text{green}) = 128 / 202 = 0.6337$ `[0.5653, 0.6970]`.

### 2.2 `hireable-platform` (56 Merged PRs) `[measured]`

| Artefact Status | CI Green | CI Red | No CI (`_ci == "none"`) | Total Evaluated (Green + Red) | Total PRs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bad** (`_bad == True`) | 18 | 3 | 1 | 21 | 22 |
| **Good** (`_bad == False`) | 24 | 4 | 6 | 28 | 34 |
| **Total** | 42 | 7 | 7 | 49 | 56 |

- **Treatment A (Verdict-only, excluding `_ci == "none"` from denominator):**
  - $\alpha = 4 / 28 = 0.1429$ (Wilson 95%: `[0.0570, 0.3149]`).
  - $\beta = 18 / 21 = 0.8571$ (Wilson 95%: `[0.6477, 0.9542]`).
- **Treatment B (All good PRs in denominator, unrun checks treated as non-rejection):**
  - $\alpha = 4 / 34 = 0.1176$ (Wilson 95%: `[0.0467, 0.2662]`).
  - $\beta = 18 / 22 = 0.8182$ (Wilson 95%: `[0.6150, 0.9272]`).
- **Treatment C (Unrun checks treated as verifier failure / miss):**
  - $\alpha' = P(\text{not-green} \mid \text{good}) = (4 + 6) / 34 = 10 / 34 = 0.2941$ `[0.1683, 0.4617]`.

---

## 3. Reconciliation of Orchestrator and Codex Audit Corrections

### 3.1 The Question of Independence
Two separate corrections to the 23 good-and-red PRs on `jobboard-v2` were produced independently:
1. **Orchestrator mechanical removal:** 3 PRs (#505, #512, #525) failed *only* due to `CANCELLED` CI runs. Treating cancelled runs as "no verdict" gave $\alpha = (23 - 3) / (97 - 3) = 20 / 94 = 0.2128$.
2. **Codex audit removal:** Judged 9 of 23 reds non-meaningful (#397, #399, #400, #465, #505, #512, #517, #518, #525) and kept them in the denominator, giving $\alpha = (23 - 9) / 97 = 14 / 97 = 0.1443$.

**Finding on Overlap:**  
The two corrections are **not independent**; the orchestrator's 3 cancelled PRs are a **strict subset** of Codex's 9 removed PRs (`{505, 512, 525} ⊂ {397, 399, 400, 465, 505, 512, 517, 518, 525}`).  
- Intersection: 3 PRs (#505, #512, #525).
- Union: 9 PRs (exactly Codex's 9).
- Codex removals not in the cancelled-only set: 6 PRs (#397, #399, #400, #465, #517, #518).
  - PR #465 failed only on a non-blocking live LLM jailbreak regression suite.
  - PRs #517 and #518 failed live LLM suites alongside cancelled runs.
  - PRs #397, #399, #400 failed lint/CI infrastructure checks.

Codex additionally flagged 3 PRs as "red-unclear" (#407, #411, #416) due to lint/lighthouse failures.

### 3.2 Reconciled Contingency Table (`jobboard-v2`, Good PRs)

| Classification within Good-and-Red ($N=23$) | Count | Status under Reconciled Model |
| :--- | :---: | :--- |
| **Cancelled-Only Runs** (#505, #512, #525) | 3 | No verdict (execution aborted; no decision taken) |
| **Non-blocking / Live LLM Failures** (#465, #517, #518, #397, #399, #400) | 6 | Non-meaningful / non-gating suite rejections |
| **Unclear / Boundary Failures** (#407, #411, #416) | 3 | Ambiguous (lint / performance audit) |
| **Confirmed Verifier Rejections** | 11 | Genuine deterministic verifier rejections |
| **Total Good & Red** | **23** | |

### 3.3 Resulting $\alpha$ Estimates Across Reconciled Treatments `[measured]`, `[algebra]`

| Treatment Model | Excluded from Red Numerator | Denominator Treatment | Numerator $k$ | Denominator $N$ | Reconciled $\alpha$ | Wilson 95% Confidence Interval |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Raw proxy)** | None | All good ($74 + 23$) | 23 | 97 | **0.2371** | `[0.1635, 0.3307]` |
| **Model 1: Cancelled as No-Verdict** | 3 cancelled | Excluded from denom ($97 - 3$) | 20 | 94 | **0.2128** | `[0.1424, 0.3056]` |
| **Model 2: Reconciled No-Verdict (Recommended)** | 9 (Union) | Excluded from denom ($97 - 9$) | 14 | 88 | **0.1591** | `[0.0972, 0.2495]` |
| **Model 3: Reconciled Retained-Denom** | 9 (Union) | Retained in denom | 14 | 97 | **0.1443** | `[0.0880, 0.2278]` |
| **Model 4: Strict (Excl. 3 Unclear as well)** | 12 ($9 + 3$) | Excluded from denom ($97 - 12$) | 11 | 85 | **0.1294** | `[0.0738, 0.2170]` |
| **Model 5: Strict Retained-Denom** | 12 ($9 + 3$) | Retained in denom | 11 | 97 | **0.1134** | `[0.0645, 0.1917]` |

---

## 4. Recommended Treatment & Methodological Evaluation

### 4.1 Recommended $\alpha$ Treatment
We recommend **Model 2: Reconciled No-Verdict ($\alpha = 14/88 = 0.1591$ `[0.0972, 0.2495]`)** for architectural modelling:
1. **Aborted and non-gating runs are not verifier verdicts.** A cancelled CI build or an informational, non-blocking check does not represent a verifier decision. Counting them as verifier rejections distorts the false-positive rate of the actual verification gate.
2. **Exclusion from denominator preserves conditional semantics.** The quantity of interest is $P(\text{reject} \mid \text{good, verifier ran to verdict})$. PRs where no gating verdict was rendered belong in the uninformative category (analogous to `_ci == "none"`).
3. **The assumed $\alpha = 0.03$ remains firmly refuted.** Under every single candidate model (from 0.2371 down to strict 0.1134), the entire 95% Wilson confidence interval lies strictly above 0.03. Even the lowest lower bound across all treatments (`0.0645`) is more than $2.1\times$ higher than the assumed 0.03.

### 4.2 Methodological Divergences & Defect Identification
1. **Denominator Ambiguity in `_ci == "none"`:** `mine_beta.py` silently dropped `_ci == "none"` PRs from the output tables without reporting them in the primary summary, creating an apparent mismatch between total PRs analysed ($N=56$) and the denominator ($N=21$ or $N=28$).
2. **Extreme Imbalance in Revert vs Hotfix Signals:** 100% of bad labels in both corpora ($203/203$ and $22/22$) were generated by the heuristic hotfix regex + file overlap proxy. In fix-forward commercial repositories where explicit `git revert` commits referencing PR numbers are non-existent ($0/1511$ commits), the "revert" detector is inert.
3. **Severe Size Bias in the Proxy Instrument:** PRs in bad-and-red touch a median of 13 files (mean 26.8) versus 5 files (mean 9.4) in bad-and-green ($2.60\times$ ratio). Because file overlap probability scales directly with changeset footprint, large PRs are heavily over-selected into the bad category by the proxy heuristic.
4. **Information Loss in CI Status Rollups:** Collapsing multi-suite CI checks into a single ternary enum (`green`/`red`/`none`) discarded the check identities and non-blocking status, requiring forensic re-fetching to distinguish genuine correctness failures from non-blocking or cancelled executions.

---

## 5. Reversal and Falsifier

**Reversal:**  
`git rm docs/10-research/experiments/exp01/replication-2026-08-20.md`  
This file contains analytical replications only and does not alter product code or existing experiment data.

**Falsifier:**  
An exhaustive manual inspection of the 74 good-and-green and 14 adjudicated good-and-red PRs establishing that the majority of good-and-red PRs were genuine defect escapes that went un-reverted, which would move them into the bad row and suppress $\alpha$ toward the assumed 0.03 floor.

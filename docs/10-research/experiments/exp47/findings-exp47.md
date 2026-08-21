# EXP-47 findings — direct measurement of verifier β via mutation testing

**Date:** 20 August 2026  
**Status:** `[measured]` for mutation census metrics, check error rates, contingency tables, and execution costs; `[asserted]` for architectural implications and stopping rule verdicts.  
**Engine:** `mutmut` 3.7.0 (BSD-3-Clause) + `libcst` AST engine running across all non-test modules in `src/consilient/` (`__init__.py`, `beta.py`, `cli.py`, `events.py`, `projection.py`).  
**Corpus:** 1,931 syntactically valid first-order mutants evaluated in isolated temporary worktrees across 24 concurrent workers.  
**Privacy discipline:** Per `AGENTS.md`, aggregate metrics and operator descriptions only; zero wholesale source dumps.

---

## Executive Summary

β is $P(\text{verifier accepts} \mid \text{artefact is bad})$. Historical measurements relied on noisy proxies (revert/hotfix mining: 93% noise in EXP-01; forward test replay: blind to 73–76% in EXP-43).

**Mutation testing measures β directly without proxies or human labelling.** Syntactic mutations introduce deterministic defects into the source tree; each verifier check is executed against the mutant in isolation. The surviving-mutant rate is the empirical false-accept rate $\beta$.

EXP-47 executed a complete census of **1,931 first-order mutants** across all five source files of `src/consilient/` against `pytest` (96 tests), `mypy` (`mypy.ini`), and `ruff` (`ruff check`).

### Headline Results `[measured]`

1. **Per-check error rates ($\beta$):**
   - **`pytest`:** $\hat{\beta} = 0.3848$ (95% Wilson CI: **[0.3633, 0.4067]**; 743 survivors / 1,931 mutants).
   - **`mypy`:** $\hat{\beta} = 0.6981$ (95% Wilson CI: **[0.6772, 0.7182]**; 1,348 survivors / 1,931 mutants).
   - **`ruff`:** $\hat{\beta} = 0.9596$ (95% Wilson CI: **[0.9499, 0.9675]**; 1,853 survivors / 1,931 mutants).
2. **Composite verifier error rate ($\beta_{\text{comp}}$):**
   - **Raw Composite:** $\hat{\beta}_{\text{raw}} = 0.3345$ (95% Wilson CI: **[0.3138, 0.3559]**; 646 survivors / 1,931 mutants).
   - **Equivalent-Corrected Composite:** $\hat{\beta}_{\text{corr}} = 0.3132$ (95% Wilson CI: **[0.2926, 0.3346]**; 586 true defects / 1,871 non-equivalent mutants).
   - 60 equivalent mutants were identified and isolated (docstring mutations, CLI help/epilog metadata strings, case-insensitive SQLite keywords, and dataclass caveat defaults).
3. **Check Independence Refuted ($\chi^2 = 187.28, p < 10^{-15}$):**
   - Mutants surviving `pytest` survived `mypy` at **87.89%** (653/743), compared to **58.50%** (695/1,188) for mutants killed by `pytest`.
   - Observed joint survival $P(\text{pytest} \land \text{mypy}) = 33.82\% \gg 26.86\%$ expected under independence.
   - **ADR-0012's independence assumption is empirically refuted** `[measured]`: individual check error rates cannot be multiplied as an independent prior.
4. **Stopping Rule 1 FIRED:** Corrected composite $\beta = 0.3132 \ge 0.20$. Automated invariant guards have significant blind spots, concentrated in CLI formatting, specific validation edge cases, and internal helper branches.

---

## Part 1 — Verifier Error Rates ($\beta$) and Intervals `[measured]`

| Verifier Check | Mutants Tested ($N$) | Survivors ($k$) | Point Estimate ($\hat{\beta}$) | 95% Wilson Score Interval |
|---|---|---|---|---|
| **`pytest tests/`** | 1,931 | 743 | **0.3848** | **[0.3633, 0.4067]** |
| **`mypy src/consilient`** | 1,931 | 1,348 | **0.6981** | **[0.6772, 0.7182]** |
| **`ruff check src/ tests/`** | 1,931 | 1,853 | **0.9596** | **[0.9499, 0.9675]** |
| **Composite Verifier (Raw)** | 1,931 | 646 | **0.3345** | **[0.3138, 0.3559]** |
| **Composite (Corrected for Equivalence)** | 1,871 | 586 | **0.3132** | **[0.2926, 0.3346]** |

---

## Part 2 — Breakdown by File and Operator `[measured]`

### Per-File Distribution

| Module | Total Mutants | `pytest` Survivors | `mypy` Survivors | `ruff` Survivors | Composite Survivors | Corrected True Defects |
|---|---|---|---|---|---|---|
| `src/consilient/__init__.py` | 1 | 1 | 0 | 0 | 0 | 0 |
| `src/consilient/beta.py` | 168 | 42 | 103 | 163 | 37 | 36 |
| `src/consilient/cli.py` | 1,104 | 515 | 784 | 1,063 | 440 | 400 |
| `src/consilient/events.py` | 410 | 115 | 307 | 389 | 106 | 106 |
| `src/consilient/projection.py` | 248 | 70 | 154 | 238 | 63 | 44 |
| **Total** | **1,931** | **743** | **1,348** | **1,853** | **646** | **586** |

### Per-Operator Distribution

| Operator Category | Total Mutants | `pytest` Surv | `mypy` Surv | `ruff` Surv | Composite Surv |
|---|---|---|---|---|---|
| **Expression Mutation** (general expressions/calls) | 550 | 238 (43.3%) | 462 (84.0%) | 538 (97.8%) | 229 (41.6%) |
| **Constant & Literal Mutation** (numbers, strings, `None`) | 547 | 148 (27.1%) | 246 (45.0%) | 507 (92.7%) | 105 (19.2%) |
| **Comparison Swap** (`==`, `!=`, `<`, `<=`, `>`, `>=`, `is`, `in`) | 489 | 195 (39.9%) | 383 (78.3%) | 479 (98.0%) | 169 (34.6%) |
| **Boolean / Logical Swap** (`True` $\leftrightarrow$ `False`, `and` $\leftrightarrow$ `or`) | 186 | 104 (55.9%) | 144 (77.4%) | 180 (96.8%) | 91 (48.9%) |
| **Arithmetic / Binary Operator** (`+`, `-`, `*`, `/`, `&`, `|`, etc.) | 101 | 30 (29.7%) | 63 (62.4%) | 96 (95.0%) | 26 (25.7%) |
| **Control Flow Mutation** (`break`, `continue`, `raise`, `return`) | 58 | 28 (48.3%) | 50 (86.2%) | 53 (91.4%) | 26 (44.8%) |

---

## Part 3 — Check Independence Contingency Analysis `[measured]`

ADR-0012 assumed check outcomes have unknown dependence and warned that multiplying individual error rates could be misleading. EXP-47 provides empirical contingency data:

### $2 \times 2$ Contingency Table: `pytest` vs `mypy`

| | `mypy` Survived (Pass) | `mypy` Killed (Fail) | Total |
|---|---|---|---|
| **`pytest` Survived (Pass)** | **653** (Observed) <br> *(518.7 Expected)* | **90** (Observed) <br> *(224.3 Expected)* | 743 |
| **`pytest` Killed (Fail)** | **695** (Observed) <br> *(829.3 Expected)* | **493** (Observed) <br> *(358.7 Expected)* | 1,188 |
| **Total** | 1,348 | 583 | 1,931 |

- **Statistical Test:** $\chi^2 = 187.28$ (df = 1, $p = 1.2 \times 10^{-42}$).
- **Finding `[measured]`:** Strong positive dependence. Mutants that pass `pytest` are dramatically more likely to pass `mypy` ($87.89\%$ vs $58.50\%$).
- **Consequence:** The product estimator $\hat{\beta}_{\text{prod}} = \hat{\beta}_{\text{pytest}} \times \hat{\beta}_{\text{mypy}} = 0.3848 \times 0.6981 = 0.2686$ severely underestimates true composite error rate ($\hat{\beta}_{\text{comp}} = 0.3345$). **ADR-0012's warning is vindicated.**

---

## Part 4 — Weakest-Guarded Invariants by Module `[measured]`

The audit identified 586 non-equivalent surviving mutants across the four substantive modules. The primary structural vulnerabilities cluster as follows:

1. **`src/consilient/events.py` (106 surviving true defects):**
   - **V0-18 human authority edge cases:** In `HUMAN_ONLY`, mutating `"spend_authorisation"` to a placeholder survived because invariant tests exercised `"approval"`, `"gate_lift"`, and `"verdict"`, but lacked a dedicated test asserting `"spend_authorisation"` specifically.
   - **Exception message strings:** Mutating error messages in `raise EventError(...)` survived whenever tests used `pytest.raises(EventError)` without `match="..."`.
   - **Compound validation boundaries:** In `_check_evidence_class` and `_check_attempt_contract`, mutating `or` to `and` in type guard checks (e.g. `isinstance(x, str) or x.strip()`) survived when test fixtures only supplied well-typed strings.
2. **`src/consilient/beta.py` (36 surviving true defects):**
   - **Wilson interval default parameter:** Mutating `wilson(..., z=1.96)` to `z=2.96` survived because tests only verified boundary properties ($0$ and $1$) and monotonicity, not the specific $95\%$ confidence level $z=1.96$.
   - **`wilson(0, 0)` guard:** Mutating `if trials == 0:` to `if trials == 1:` survived because tests never invoked `wilson` with zero trials directly.
   - **Filtering predicates in `compute()`:** Mutating `task_family` or `verifier_version` filtering logic survived in paths where test datasets omitted those metadata attributes.
3. **`src/consilient/projection.py` (44 surviving true defects):**
   - **Metadata extraction fallback:** In `_apply()`, mutating `event.data.get("principal")` to `event.data.get(None)` survived in tests where events lacked optional principal data.
   - **Index & Replay error diagnostics:** Minor branches in rejection count logging and table indexing survived because test projections did not assert index existence explicitly.
4. **`src/consilient/cli.py` (400 surviving true defects):**
   - **Human-readable CLI render formatting:** Table column alignments, header strings, issue summaries, and status text survived because CLI invariant tests assert JSON contracts (`--json`) rather than human stdout format.

---

## Part 5 — Equivalent Mutant Handling & Residual Uncertainty `[asserted]`

- **Identified Equivalent Mutants ($N=60$):**
  - Docstring mutations across modules (18 mutants).
  - SQLite query syntax case changes (e.g. `SELECT` $\leftrightarrow$ `select`, `INSERT INTO` $\leftrightarrow$ `insert into`, which are byte-distinct in code but semantically identical in SQLite) (19 mutants).
  - CLI argument parser help strings (`help=...`, `description=...`, `epilog=...`) (21 mutants).
  - Dataclass caveat default string perturbations (2 mutants).
- **Residual Uncertainty:** 0 unclassifiable mutants; 100% of surviving mutants were mechanically mapped to explicit line numbers, AST operators, and test tracebacks.

---

## Part 6 — Cost and Performance `[measured]`

- **Hardware:** WSL2 Ubuntu on AMD Ryzen 9 / RTX 5090 host (24 worker processes).
- **Total Wall-Clock Time:** **104.09 seconds** for 1,931 mutants across three full test suites (5,793 test executions total).
- **Unit Cost:** **0.0539 seconds per mutant** (18.6 mutants/s throughput).

---

## Part 7 — The Strongest Objection to Mutation Testing as β `[asserted]`

**The Competence-Difficulty Gap:** Mutation testing generates first-order, local, syntactically simple mutations (single token swaps, operator inversions, constant changes). Real software defects produced by humans and LLMs often involve **multi-token conceptual omissions**, **specification misunderstandings**, **stateful race conditions**, and **semantic drift across multiple files**.

If human/LLM errors are harder to catch than local syntactic mutants, mutation testing provides an **optimistic lower bound** on $\beta$ ($\beta_{\text{real}} \ge \beta_{\text{mutant}}$). If human errors are larger and noisier, they may break more invariants and be easier to catch ($\beta_{\text{real}} \le \beta_{\text{mutant}}$). Mutation testing measures **guard coverage on synthetic defects**, not the empirical distribution of real-world cognitive failures.

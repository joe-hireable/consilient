# EXP-43 findings — retro-verification via forward test replay

Run 20 Aug 2026. Evaluated forward test suite replay against historical merge commit pairs
in `jobboard-v2` using isolated scratch clone execution, process-tree timeout control,
atomic single-instance locking, and parent-commit baseline discrimination.

Per the privacy rule (`AGENTS.md`): per-PR records live in scratch/gitignored locations;
this file carries aggregates only.

---

## Part 1 — Primary Evaluation Results `[measured]`

The primary evaluation was executed at the pre-registered sample size ($N = 50$) on the
isolated subsystem unit test suite (`tests/unit/services`). The monolithic arm (`tests/unit`)
was excluded based on the pilot's 100% drift finding.

| Metric | Pilot Subsystem Suite | Monolithic Suite (Pilot) | Primary Subsystem Evaluation |
|---|---|---|---|
| Pairs evaluated ($N$) | 15 | 5 | **50** |
| Target suite | `services` | `tests/unit` | `tests/unit/services` |
| Tests executed per run | 48–68 | 8,418–8,508 | **48** |
| Median pair duration | 2.997 s | 71.188 s | **3.112 s** (~1.56 s/commit) |
| Total wall-clock runtime | 45.8 s | 350.4 s | **156.8 s** |
| Parent PASS, Child PASS (`clean`) | 15 (100%) | 0 (0%) | **50 (100%)** |
| Parent FAIL, Child FAIL (`drift`) | 0 (0%) | 5 (100%) | **0 (0%)** |
| Parent PASS, Child FAIL (`defect`) | 0 (0%) | 0 (0%) | **0 (0%)** |
| Parent FAIL, Child PASS (`enhancement`) | 0 (0%) | 0 (0%) | **0 (0%)** |
| Drift rate | 0.0% | 100.0% | **0.0%** |
| Discrimination rate | 0.0% | 0.0% | **0.0%** |
| Evaluable parent-pass baseline | 15 | 0 | **50** |
| $\beta_{\text{retro}}$ point estimate | 0.0 | N/A | **0.0** |
| $\beta_{\text{retro}}$ 95% Wilson interval | [0.0, 0.2039] | N/A | **[0.0, 0.0713]** |
| Stopping rule fired | `inconclusive` | `rejected_high_drift` | **`inconclusive`** |

### Stopping Rule Outcome
With 50 evaluable parent passes ($P_i$ PASS), 0% drift, and 0 defects, the pre-registered stopping
rule fired **`inconclusive`**. The 95% Wilson confidence interval tightened from $[0.0, 0.2039]$ at
$n=15$ to **$[0.0, 0.0713]$** at $n=50$.

---

## Part 2 — Greenfield Blindness Bound `[measured]`

The pilot identified a structural blindness: when a commit introduces a greenfield component,
its parent lacks the module/symbols entirely; future tests fail on the parent with import errors,
and the parent-commit control censors the commit as drift.

To establish the empirical ceiling of the retro-verifier method, all 162 merge commits on `main`
across the target repository's history were mechanically classified by change type:

| Classification Proxy | Count | Share of Merges ($N = 162$) |
|---|---|---|
| **All-files: Adds $\ge 1$ new file** | **123** | **75.9%** |
| All-files: Modifies existing files only | 39 | 24.1% |
| All-files: Pure addition (zero modifications) | 12 | 7.4% |
| **Code-files: Adds $\ge 1$ new code file (`.ts`/`.js`/`.py`/`.sql`)** | **118** | **72.8%** |
| Code-files: Modifies existing code files only | 19 | 11.7% |
| Code-files: Non-code changes only (docs/config) | 25 | 15.4% |
| **Subsystem scope: Touches evaluated subsystem (`services`)** | **25** | **15.4%** |
| Subsystem scope: Adds new service files | 2 | 1.2% |
| Subsystem scope: Modifies existing service files only | 23 | 14.2% |

### Proxy Definition and Weaknesses `[asserted]`
- **Definition:** A merge commit is classified as additive/greenfield if `git diff-tree -r --name-status P_i C_i`
  contains $\ge 1$ file with status `A`. It is classified as interface modification only if all changed files
  carry status `M`, `D`, or `R`.
- **Under-estimation weakness (false negatives for greenfield):** Commits that modify existing files to add
  new exported functions, classes, or endpoints are semantically greenfield (parents lack the symbol), but
  are labeled "modification only" by the file-level proxy.
- **Over-estimation weakness (false positives for greenfield):** Commits that modify existing logic but also
  add a new helper utility or standalone unit test file are labeled "additive" even though the primary
  artefact is an interface modification.
- **Epistemological consequence:** Between **72.8% and 75.9%** of all merge commits introduce new files/modules.
  The retro-verifier's parent-commit control censors these additions by design. The method is therefore
  fundamentally bounded: it can only ever observe the remaining **11.7% to 24.1%** of changes that modify
  pre-existing interfaces.

---

## Part 3 — Honest Reconciliation of the Two Oracles `[asserted]`

Two independent oracles on the same repository yield non-overlapping 95% confidence intervals:

| Oracle | $\beta$ Point | 95% Confidence Interval | $N$ | Conditioning / Observable Surface | Bias Direction |
|---|---|---|---|---|---|
| **Revert/Hotfix Proxy** | 0.87 | [0.81, 0.93] | 75 bad PRs / 203 | Commit metadata: hotfix PR title regex & file-set overlap | **Biased high** (inflated by 33–48% refuted false-positive labels) |
| **Retro-Verifier** | 0.00 | [0.0, 0.0713] | 50 merge pairs | Bytecode execution: forward subsystem unit test replay on parent vs child | **Biased low** (blind to greenfield [73–76%], blind to unwritten latent tests) |

### Supported Reconciliation: The Two Oracles Bracket the Truth
The empirical evidence supports that **the two oracles measure different quantities and both estimates stand, bracketing the truth**:

1. **The proxy over-labels ($\beta \approx 0.87$ is an upper bound):** The proxy treats every subsequent
   PR with a fix-shaped title touching a shared file as evidence that the prior commit was a defective escape.
   Adjudication proved 33–48% of these labels are noise.
2. **The retro-verifier under-samples ($\beta \approx 0.00$ is a lower bound):**
   - It is structurally blind to greenfield additions (72.8%–75.9% of the corpus).
   - It is subject to survivorship bias (tests are only written for bugs that were found, reported, and tested).
   - In subsystem isolation, only 15.4% of repository merges touched the subsystem at all.
3. **Whewell's "Different Class of Facts":** The divergence does not indicate experimental failure; it
   proves that commit message NLP and runtime test execution operate on distinct evidence classes with
   opposing systematic biases.

### Strongest Objection to this Conclusion `[asserted]`
The strongest objection is that **the retro-verifier at subsystem scope is an unrepresentative null instrument**.
Because only 25 of 162 total merges in repository history ever touched the `services` subsystem, evaluating
50 chronological merges against `services` tests evaluated 35+ commits that never interacted with the subsystem's
code paths. The 50/50 `clean` result reflects subsystem uncoupling rather than defect-free code review. A
monolith suite is incapacitated by drift (100%), while a subsystem suite is incapacitated by domain sparsity.

---

## Safety & Invariant Verification `[measured]`

1. **Atomic Single-Instance File Lock:** Verified by test suite (`test_exp43.py`) and live PID checking.
   Concurrent launches refuse execution; stale locks older than 3600 s are reclaimed cleanly.
2. **Process-Tree Timeout Control:** Child processes and vitest subtrees are terminated via process group
   signals / taskkill (`kill_tree`), preventing orphaned background runners.
3. **`run_id` Stamping:** Every execution checkpoint and final results payload in `results-exp43.json`
   records a unique timestamped `run_id` (e.g. `exp43-20260820T123510-184517`).

# Study Design: Evaluating Whether the Defect-Mining Literature Has Expired Under AI Authorship

**Date:** 20 August 2026  
**Status:** `[asserted]` for study architecture, identification strategy, and protocol choices; `[cited]` for literature findings; `[measured]` for baseline internal corpus metrics; `[algebra]` for sample size and power calculations.  
**Author:** Consilient Research Programme (`fleet-public-corpus`)  
**Experiment ID:** EXP-44  

---

## 1. Literature Status: Has Someone Already Done This?

### 1.1 First-Sentence Verdict
**No prior study has evaluated whether defect-proxy or SZZ reliability decays as a function of AI-authorship share across software repositories.** `[cited]`

The software engineering literature contains extensive critiques of SZZ algorithms on human-written code, as well as an emerging body of work measuring AI-agent pull requests and defect rates; however, **no published work investigates the methodological interaction between increasing AI-authorship share and the validity of historical defect-mining proxies.** `[cited]`

---

### 1.2 The SZZ Evaluation Literature and Ground Truth
The SZZ algorithm (Śliwerski, Zimmermann & Zeller, MSR 2005) and its descendants (B-SZZ, MA-SZZ, RA-SZZ, AG-SZZ, SZZ Unleashed, PySZZ) identify bug-introducing commits (BICs) by tracing backward via `git blame` from bug-fixing commits to the lines they modify. `[cited]`

The accuracy of SZZ itself has historically been evaluated using three distinct ground-truth paradigms:

1. **Researcher-Curated Manual Oracles:** Small-scale samples (typically $N = 50\text{--}300$ commits) manually inspected by software engineering researchers (e.g. Da Costa et al., EMSE 2017; Rodríguez-Pérez et al., EMSE 2020). `[cited]`  
   *Known failure mode:* Researchers are rarely domain experts in the target codebase, leading to substantial misclassification of architectural and dependency changes as cosmetic or functional defects. `[cited]`
2. **Developer-Informed Oracles:** Mined commit messages where the original author explicitly identifies the commit that introduced the bug (e.g. `Fixes: <commit-hash>` in the Linux kernel; Rosa et al., JSS 2023 / arXiv:2102.03300; TSE 2024 Linux kernel study over 76,046 labeled pairs). `[cited]`  
   *Findings:* Rosa et al. report precision around 70% for R-SZZ, while SZZ Unleashed achieves higher recall at the expense of precision. On the Linux kernel, TSE 2024 found SZZ recall drops by 13.8% relative to smaller datasets, and 17.47% of bug-fixing commits are "ghost commits" whose inducing change cannot be traced through line history. `[cited]`
3. **Synthetic Defect / Mutation Benchmarks:** Fault-injection suites where the inducing change is synthetically known (e.g. Just et al., FSE 2014; Defects4J). `[cited]`

#### Established Critiques of SZZ Precision and Recall
- **Mislabelling Rates:** Herbold et al. (EMSE 2022 / arXiv:1911.08938) established across 38 Apache projects that SZZ correctly identifies only approximately half of bug-fixing commits, and that one file is incorrectly labelled defective for every file correctly identified. `[cited]`
- **Non-Random Noise:** Herzig et al. (ICSE 2013) found 39% of issue-tracker "bug" reports are misclassified features or refactorings; Tantithamthavorn et al. (ICSE 2015) proved that this non-random label noise degrades defect-prediction model recall by 32–44%. `[cited]`
- **Linkage Bias:** Bird et al. (FSE 2009) and Bachmann et al. (FSE 2010) demonstrated that commits linked to bug trackers represent a biased, non-random subset of all defect fixes. `[cited]`
- **Commit-Size Distortion:** Rezk et al. (TSE 2021) and Rosa et al. (2021) showed that large and bulk commits generate massive numbers of spurious candidate BICs. `[cited]`

---

### 1.3 AI-Authored Code, Defect Rates, and Ground Truth Construction
Studies examining AI-generated and AI-assisted code (e.g. GitHub Copilot, Cursor, Devin, Claude Code) evaluate quality using four main approaches:

1. **Code Churn and Duplication Proxies:** GitClear (2024, "Coding on Copilot", 153M lines analyzed) measured code churn, percentage of code modified within two weeks, and copy-paste refactoring rates, asserting downward pressure on maintainability. `[cited]`  
   *Limitation:* Uses churn as a proxy for defectiveness without verifying defect escapes. `[asserted]`
2. **Automated Linters and Review Bots:** CodeRabbit (2025) and commercial review studies evaluate AI-authored PRs using LLM linter passes and rule engines. `[cited]`  
   *Limitation:* Evaluates AI code using another AI model without human ground truth, producing echo. `[asserted]`
3. **Static Security Weakness Scanners:** Fu et al. (2025), Pearce et al. (2022/2025) evaluate security weaknesses in Copilot-generated commits using CodeQL and Bandit. `[cited]`
4. **Execution Test Suites / Benchmarks:** SWE-bench (Jimenez et al., 2024) and SWE-bench+ (arXiv:2410.06992). SWE-bench+ found 31.08% of patches that pass standard test suites are suspicious due to test weakness or leakage. `[cited]`
5. **Open Source Agent Censuses:** arXiv:2606.24429 (*Detecting AI Coding Agents in Open Source*, 180M repos) applied coarse SZZ-like temporal file-adjacency proxies, observing sub-baseline SZZ ratios ($0.33\text{--}0.56\times$). `[cited]`  
   *Limitation:* Assumed the validity of the SZZ proxy across AI commits rather than interrogating whether AI authorship degraded the proxy itself. `[cited]`

---

### 1.4 Modern Defect-Prediction Datasets and Provenance Recording
Standard defect-prediction benchmarks—including Defects4J (Just et al., ISSTA 2014), BugsInPy (Widyasari et al., 2020), ManyBugs (Le Goues et al., TSE 2015), and JIT-Defects4J—contain histories from 2000–2021 and **record zero AI-authorship metadata** because they predate LLM-assisted coding tools. `[cited]`

Newer datasets, such as AIDev (MSR 2026 Mining Challenge / Pith, 2026; 456,000 agent PRs across Devin, Cursor, Claude Code, Copilot), record tool identities and PR merge status, but **do not establish ground-truth bug-introducing links or maintainer defect audits**. `[cited]`

Recent conceptual analyses (e.g., Vasilescu et al., *The Ground Is Shifting: A Reflection on the Foundations of Software Measurement*, ASE 2026 NIER) highlight that software measurement constructs (churn, commit counts, bug-introduction rates) are fracturing because development traces no longer represent human effort or human judgement. `[cited]`

---

## 2. The Falsifiable Prediction

### 2.1 Theoretical Rationale
Historical defect proxies—such as SZZ (blame-tracing bug fixes to prior edits) and the revert/hotfix heuristic (PRs followed within 14 days by a fix-titled PR touching overlapping files)—rest on a foundational premise: **that commits and pull requests represent human judgement.** `[asserted]`

Under human software development:
1. When a human merges a PR, they exercise review judgement. When they subsequently revert or hotfix it, that action signals an acknowledged defect escape. `[asserted]`
2. When a human writes a bug fix, they deliberately modify the specific lines or files that contained the conceptual flaw. `[asserted]`

Under AI orchestration and high AI-authorship share:
1. Maintainers accept AI pull requests without comprehensive line-by-line verification (maintainer merge rates average 24.2 percentage points below automated benchmark passes, Meng et al. 2026; Joe Brown, 2026: *"all of these PRs and commits were entirely AI orchestrated"*). `[cited]`, `[measured]`
2. Fix-forward workflows dominate: maintainers prompt agents to repair subsequent breakage rather than executing explicit `git revert` operations (observed revert rate: 0 reverts in 224 bad labels across 2,506 commits). `[measured]`
3. AI agents generate broad scaffolding, touch multiple configuration files, and emit high-velocity commits, causing combinatorial inflation of file-overlap heuristics (bad-and-red PRs touched $2.6\times\text{--}3.0\times$ more files than bad-and-green PRs). `[measured]`

### 2.2 Formal Hypotheses
- **$H_1$ (Degradation of Proxy Precision):** The precision of heuristic defect proxies (percentage of flagged PRs that are true defects under independent ground truth) is negatively correlated with repository AI-authorship share. `[asserted]`
- **$H_2$ (Evaporation of Strong Signal):** The ratio of explicit revert signals to circumstantial hotfix signals approaches zero as AI-authorship share increases. `[asserted]`
- **$H_3$ (Differential Misclassification by Velocity):** High AI-authorship repositories exhibit severe differential misclassification driven by commit velocity and diff spread, inflating false-positive defect labels in large or non-passing changes. `[asserted]`

---

## 3. Operationalisation and Measurement

### 3.1 Measuring AI-Authorship Share on Public Repositories
Measuring AI authorship on public repositories presents a severe methodological challenge: **using a proxy for AI authorship to evaluate a proxy for defects is two proxies deep.** `[asserted]` If the authorship proxy is noisy, errors compound.

We evaluate the candidate operationalisations:

| Signal Class | Mechanism | False Positives | False Negatives | Operational Viability |
|---|---|---|---|---|
| **Explicit Bot Accounts** | GitHub App / Bot authors (`github-actions[bot]`, `claude-code[bot]`, `devin-ai-integration[bot]`) | Near 0% | High (misses IDE plugins and local agents) | High precision; clean lower bound. `[asserted]` |
| **Commit Trailers** | `Co-authored-by:` naming an AI (`noreply@anthropic.com`, Cursor, Copilot) | Very Low (<2%) | Moderate-to-High (many developers omit trailers) | High precision; standard in modern repos. `[asserted]` |
| **PR & Commit Signatures** | Default generated strings ("Generated by Claude Code", "Assisted by Cursor Composer", "aider") | Low (<5%) | Moderate (can be edited out) | High utility when combined with trailers. `[asserted]` |
| **Repo Configuration** | Presence of `.cursorrules`, `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md` | Low | Moderate | Indicates environment, not per-commit share. `[asserted]` |
| **Velocity & Diff Anomalies** | Commits/hour spikes, uniform commit message entropy | High | High | Highly confounded with CI scripts and rebases. **Rejected.** `[asserted]` |

#### Least-Bad Authorship Operationalisation
We define commit-level AI attribution $A(c) \in \{\text{AI-Generated}, \text{AI-Assisted}, \text{Human-Sole}\}$ using a strict tiered classifier: `[asserted]`
1. **Tier 1 (High-Confidence AI):** Commit author/committer is a known AI bot account OR commit message / PR body contains verified tool signatures (Claude Code, Cursor, Devin, Aider, Copilot PR templates) OR git trailer contains an explicit AI co-author.
2. **Tier 2 (Explicit Human):** Repositories in the pre-2022 historical window (prior to November 2022 / ChatGPT release) OR commits from known maintainers with explicit no-AI policies.
3. **Tier 3 (Uncertain / Mixed):** Commits post-November 2022 lacking explicit tool markers. These are retained as an unstratified middle category and never used as pure human ground truth. `[asserted]`

Repository-level AI share is operationalised as:
$$\text{AI-Share}(R, t) = \frac{\sum_{c \in \text{PRs}(R, t)} \mathbb{I}(A(c) = \text{AI})}{\text{Total PRs}(R, t)}$$

---

### 3.2 Establishing Independent Ground Truth for Defects
To evaluate proxy reliability without circularity, we require defect oracles that do **not** rely on file-overlap or commit-message keyword matching. `[asserted]`

| Oracle Candidate | Mechanism | Availability at Scale | Independence from Proxy | Verdict |
|---|---|---|---|---|
| **Developer-Informed Fix Links** | Explicit `Fixes: <SHA>` tags in commits / PRs where the fixing author identifies the broken commit | High in mature C/Python projects ($>70\text{k}$ in Linux, thousands in CPython/QEMU) | **High** (direct human causal attribution) | **Primary Oracle 1** `[asserted]` |
| **Triage-Verified Bug Issues** | Closed issues labeled `type: bug` + `triaged` + confirmed by maintainer comments, linked to PR | Moderate-to-High on GitHub/GitLab | **High** (external user observation of failure) | **Primary Oracle 2** `[asserted]` |
| **Retro-Verifier (Regression Test Replay)** | Checking out candidate commit $c$; running a *new* test introduced in a later bug fix PR | Moderate (requires reproducible build environments) | **Mechanical** (zero human bias; tests verifier $\beta$ directly) | **Primary Oracle 3** `[asserted]` |
| **Security Advisories (GHSA/CVE)** | Public CVEs linking fixed commits to vulnerable commits | Low-to-Moderate ($10\text{--}100$ per major repo) | **High** | Diagnostic only (extreme tail). `[asserted]` |
| **Explicit `git revert`** | `git revert` commands executed by maintainers | Near Zero on modern fix-forward repos ($0.24\%$ observed) | High | Measured absent in AI repos. `[measured]` |

---

## 4. Study Architecture and Identification Strategy

### 4.1 Cross-Sectional vs Longitudinal Panel Design
A cross-sectional comparison across different repositories (e.g., comparing heavily-AI startups to legacy open-source projects) is fundamentally confounded: AI-heavy repos differ in team size, age, test maturity, domain, and release cadence. `[asserted]`

**We mandate a Longitudinal Within-Repository Panel Design.** `[asserted]`

```
  Era 1: Pre-AI Baseline        Era 2: Early Adoption        Era 3: Autonomous Agents
    (2018-01 to 2021-12)         (2023-01 to 2024-06)          (2025-01 to 2026-08)
  =========================    ========================    ============================
  AI-Share: 0.0%               AI-Share: 10% - 40%         AI-Share: > 60%
  Human Review: Mandatory      Human Review: Mixed         Human Review: Minimal / Overridden
```

By tracking the **same 30 repositories** across three historical eras:
- Each repository acts as its own control for codebase domain, architecture, language, core testing framework, and baseline defect rate. `[asserted]`
- We evaluate how the precision $P(\text{Defect} \mid \text{Proxy Flag})$ and recall $P(\text{Proxy Flag} \mid \text{Defect})$ of standard SZZ and hotfix proxies shift across eras within the exact same software systems. `[asserted]`

---

## 5. Threat Analysis and Confounders

### 5.1 Confounders and Mitigation Matrix

| Confound | Mechanism | Impact on Proxy | Controllable? | Mitigation Strategy |
|---|---|---|---|---|
| **Commit Velocity & Churn** | AI tools 5–10× commit volume; more PRs merged per day | Spurious file overlap explodes combinatorially by pure chance. | **Partially** | Normalise overlap window by commit count rather than calendar days; compute permutation baseline (shuffled commit timestamps). `[asserted]` |
| **Squash-Merging Practices** | Repositories moving from merge commits to squash-merges over time | Obscures atomic commit history; flattens multi-file diffs into giant blobs. | **Yes** | Restrict sampling to PR-level analysis where full pre-squash commit graphs and PR diffs are extracted. `[asserted]` |
| **CI Suite Maturation** | Test suites grow larger and catch more bugs in 2026 than in 2018 | Verifier baseline accuracy $\alpha, \beta$ shifts over time independently of AI. | **Yes** | Measure CI test suite count and execution coverage per era; control for test suite size in regression models. `[asserted]` |
| **Team Turnover & Size** | Core maintainers leave or junior developers join | Review rigor may vary over time. | **Partially** | Control for author tenure and maintainer review presence in PR metadata. `[asserted]` |
| **Defect Reporting Lag** | Recent PRs (2026) have had less calendar time to accumulate bug reports than 2018 PRs | Right-censoring of defect escapes in recent windows. | **Yes** | Apply fixed follow-up observation windows (e.g. exactly 90 days of subsequent history for all sampled eras). `[asserted]` |

### 5.2 The Fatal Confound: Combinatorial Velocity Overlap
When commit velocity accelerates tenfold, two unrelated PRs touching a common utility file (e.g. `settings.py`, `package.json`, `index.ts`) within a 14-day window will intersect with near certainty ($P \to 1.0$). `[asserted]`

**Verdict:** If calendar-day windows are used, velocity inflation is fatal to the hotfix proxy. The study **must** implement a volume-adjusted window (e.g. within the next $k$ merged PRs, rather than calendar days) and compare observed overlap rates against a randomised permutation null model. If the proxy cannot beat the permutation null model, the proxy has failed completely. `[asserted]`

---

## 6. Sample Size, Power Calculation, and Arithmetic

### 6.1 Hypothesis Test: Drop in Proxy Precision
We test whether proxy precision drops significantly from the human baseline ($P_0 = 0.50$, per Herbold et al. 2022) to an AI-degraded regime ($P_1 \le 0.25$, consistent with EXP-01's audited 1/15 precision on AI repos). `[algebra]`, `[cited]`, `[measured]`

#### Parameters:
- Significance level: $\alpha = 0.05 \implies z_{\alpha/2} = 1.96$
- Statistical power: $1 - \beta_{\text{power}} = 0.80 \implies z_{\beta} = 0.8416$
- Null hypothesis precision: $P_0 = 0.50 \implies \sigma_0^2 = P_0(1 - P_0) = 0.25$
- Alternative hypothesis precision: $P_1 = 0.25 \implies \sigma_1^2 = P_1(1 - P_1) = 0.1875$
- Pooled variance under null $\bar{P} = 0.375 \implies \bar{\sigma}^2 = 2 \times 0.375 \times 0.625 = 0.46875$

#### Sample Size Arithmetic:
$$n = \frac{\left(z_{\alpha/2} \sqrt{2 \bar{P}(1 - \bar{P})} + z_{\beta} \sqrt{P_0(1-P_0) + P_1(1-P_1)}\right)^2}{(P_0 - P_1)^2}$$

Evaluating the terms:
1. $z_{\alpha/2} \sqrt{2 \times 0.375 \times 0.625} = 1.96 \times \sqrt{0.46875} = 1.96 \times 0.68465 = 1.3419$
2. $z_{\beta} \sqrt{0.25 + 0.1875} = 0.8416 \times \sqrt{0.4375} = 0.8416 \times 0.66144 = 0.5567$
3. Sum of numerators: $1.3419 + 0.5567 = 1.8986$
4. Square of sum: $(1.8986)^2 = 3.6047$
5. Denominator: $(0.50 - 0.25)^2 = (0.25)^2 = 0.0625$
6. Minimum sample size per arm:
   $$n = \frac{3.6047}{0.0625} = 57.68 \approx 58 \text{ audited defect-candidate pairs per era}$$

To achieve power across three eras (Pre-2022 Human, Transition 2023–2024, High-AI 2025–2026), we require **at least 60 audited candidate pairs per era (180 audited pairs total).** `[algebra]`

### 6.2 Sampling Design Across the Repository Panel
- Panel: 30 public open-source repositories.
- Per repository, extract all merged PRs across the three eras (target: $\ge 100$ PRs per era per repo = 300 PRs/repo; total dataset $N \approx 9,000$ PRs).
- Stratified random audit sample: 10 candidate pairs per repo (5 in Pre-2022, 5 in High-AI 2025–2026) = **300 audited pairs across the panel**.
- This provides $>95\%$ power to detect a 25 percentage-point precision decay and sufficient power to detect a 15 percentage-point decay ($n_{\text{req}} = 142$). `[algebra]`

---

## 7. The Disappearing Control Group

To establish whether defect-proxy failure is an inherent property of AI orchestration or merely an artefact of specific repositories, we require a public control repository with **rigorous contemporaneous human review and an unpolluted pre-2022 history.** `[asserted]`

### 7.1 Candidate Public Repositories

| Repository | Domain / Language | Review Culture & Oracle Quality | Pre-2022 Depth | Mining Cost | Trade-Off / Limitations |
|---|---|---|---|---|---|
| **CPython** (`python/cpython`) | Language Runtime (C / Python) | Strict core-dev review; mandatory `Fixes:` / issue linking; News blurbs; regression test suite. | Massive (2000–present; GitHub PRs since 2017) | **Low** (standard GitHub GraphQL API + blurb parser) | Monorepo with distinct sub-ecosystems; some bot PRs (cherry-pick bot, blurb bot). |
| **Linux Kernel** (`torvalds/linux`) | Operating System (C) | 76,000+ developer-labeled `Fixes:` commits; patch review via LKML; explicit AI ban/scrutiny. | Decades | **Moderate** (mailing list / git log NLP parsing required; no native PR graph) | C-only; mailing-list workflow differs sharply from typical GitHub PR pipelines. |
| **Django** (`django/django`) | Web Framework (Python) | Strict 2-reviewer requirement; Trac tickets with reproducible bugs; dedicated `tests/regressiontests`. | Massive (2005–present) | **Low** (GitHub PRs linked to Trac tickets) | Transitioned from Trac to GitHub issues; smaller total PR volume than CPython. |
| **Git** (`git/git`) | Systems / CLI (C) | Extreme human code review culture; explicit commit trailers; mailing list. | Decades | **Moderate** | Mailing list workflow; small diff sizes. |

### 7.2 The Single Recommended Control Corpus
**We select CPython (`python/cpython`).** `[asserted]`

#### Rationale:
1. **Pristine Pre-2022 Baseline:** 2017–2021 GitHub PR history represents the gold standard of disciplined human code review: mandatory review by Python core developers, strict branch protections, and explicit regression testing requirements. `[asserted]`
2. **Standard Modern PR Workflow:** Unlike the Linux kernel or Git, CPython operates on GitHub PRs with status check rollups, matching the exact target architecture of modern coding agents and the Consilient harness. `[asserted]`
3. **Structured Issue & News Metadata:** Every bug fix requires a `Misc/NEWS.d` blurb and a linked GitHub issue / BPO ticket, providing an independent, developer-verified ground truth oracle without researcher guessing. `[asserted]`
4. **Contrast Validity:** CPython has seen measured adoption of AI tooling in 2024–2026 while maintaining human core-developer sign-off gates, making it the ideal longitudinal anchor. `[asserted]`

---

## 8. Experiment Specification: EXP-44

### 8.1 Register Entry Draft
```markdown
### EXP-44 · Defect-proxy reliability vs repository AI-authorship share `READY` (registered 20 Aug 2026)
**Decides:** whether SZZ and revert/hotfix defect-mining proxies remain valid under increasing AI authorship, or whether the literature's foundational assumptions have expired.
**Precondition:** 30 longitudinal public GitHub repositories with continuous history across 2018–2026 (including CPython as primary human-review control); GitHub API access; Python analysis scripts.
**Procedure:**
1. Ingest all merged PRs across three eras: Pre-AI (2018–2021), Early Adoption (2023–2024), and High-AI (2025–2026).
2. Classify commit AI-authorship share via explicit bot identities, git trailers, and PR tool signatures.
3. Apply standard SZZ and 14-day hotfix proxies to extract candidate defect-inducing commits.
4. Evaluate candidate labels against independent ground truth: developer-informed `Fixes:` links, triaged bug issues, and retro-verifier regression test execution.
5. Perform blind human/cross-model audit on a stratified sample of 300 candidate pairs (100 per era).
6. Compute proxy precision, recall, and differential misclassification by file count and commit velocity across eras.
**Measures:** proxy precision $P(\text{True Defect} \mid \text{Proxy Flag})$ by era; revert-to-hotfix ratio; proxy F1 against developer-informed oracles; correlation between AI-share and false-positive rate; size ratio between bad-and-red and bad-and-green cells.
**Stopping rules (fixed before the run):**
- Proxy precision in the High-AI era (2025–2026) is lower than the Pre-AI era (2018–2021) by $\ge 20$ percentage points ($p < 0.01$) across the panel $\implies$ **The literature has expired.** Defect proxies cannot be used on AI-authored code without primary ground-truth audits. Update research position and paper P1.
- Proxy precision is invariant to AI share (change $\le 5$ percentage points across eras) $\implies$ **The hypothesis is refuted.** Proxy noise is an intrinsic baseline property of git history, not an AI degradation effect. Cut the larger claim and restrict findings to corpus-specific noise.
- Revert arm fires $\ge 10\%$ in both human and AI eras $\implies$ Lack of reverts is an idiosyncratic property of fix-forward private repos, not a universal property of AI workflows.
- If fewer than 60 audit pairs per era achieve unambiguous ground truth, the verdict is **insufficient evidence**. Do not extrapolate from inconclusive audit samples.
**What it cannot decide:** whether AI code has higher *absolute* defect density in production (it measures *proxy reliability*, not code quality); whether closed-source commercial workflows match open-source GitHub practices; and $\beta$ for unverified local environments.
```

---

## 9. Honest Verdict and Recommendation

### 9.1 Should This Study Be Run?
**Yes, but strictly as a longitudinal study anchored on mature open-source projects (CPython, Django), NOT as a noisy cross-sectional web-scrape.** `[asserted]`

If attempted as a cross-sectional comparison of random GitHub repos, the "two proxies deep" problem (noisy AI detection + noisy defect heuristic) and massive velocity confounders will sink the study, producing ambiguous noise that cannot settle any hypothesis. `[asserted]`

However, when executed as a **longitudinal panel on CPython and curated open-source projects with developer-informed ground truth (`Fixes:` tags)**, the design isolates the exact mechanism of failure:
1. It eliminates domain/architecture confounds.
2. It tests whether the rapid shift to AI generation breaks the foundational assumption of software measurement (as argued in ASE 2026 NIER).
3. It converts an $n=1$ internal finding on private repos into an empirical contribution for software engineering research. `[asserted]`

If the data collection resources (GitHub API mining and 300-pair audit) cannot be committed, the project should **cut the claim back honestly** to what our single corpus supports: that on our private fix-forward AI-orchestrated repositories, the proxy failed completely, α was refuted, and β was unmeasurable. `[asserted]`

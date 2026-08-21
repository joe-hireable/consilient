# SuperGrok Feasibility Assessment — Headless Orchestration, Subscription Boundary, and Accounting

- **Date:** 20 August 2026
- **Status:** Evaluated [measured / cited / asserted]
- **Target Artifact:** `/mnt/c/Users/jpbpr/Repositories/consilience/.harness/dispatch/supergrok-feasibility.md`
- **Context:** Joe Brown's inquiry (20 Aug 2026): *"Let's also prepare to add SuperGrok support and I plan to upgrade to heavy so we have 4 subscriptions working together."*

---

## 1. Executive Summary & The Three-Way Verdict

| Dimension | Finding | Primary Source / Evidence |
|---|---|---|
| **Control Surface** | First-party CLI (`grok`), headless execution (`grok -p`), and Agent Client Protocol (ACP) exist. | `x.ai/news/grok-build-cli`, `docs.x.ai/build/overview` [cited] |
| **Subscription Scope** | SuperGrok Heavy ($300/mo) includes web, mobile, Grok 4.5, Grok 4 Heavy, and Grok Build CLI usage via session login; it does **not** include xAI API credits. | `felloai.com/grok-pricing`, `docs.x.ai/grok/overview`, `x.ai/api` [cited] |
| **Accounting / Headroom** | CLI emits session telemetry in JSON, but exposes **no machine-readable individual remaining headroom counter** or reset timestamp. | `docs.x.ai/build/cli/reference`, `docs.x.ai/build/enterprise` [cited] |
| **Terms of Service** | Headless CLI usage via `grok -p` and session auth is an **authorized, first-party interface**. Web scraping / cookie extraction violates AUP. | `docs.x.ai/build/cli/headless-scripting`, `x.ai/legal/acceptable-use-policy` [cited] |
| **ADR-0026 Admission** | **Excluded from unbounded unattended routing** (unknown headroom lower bound). **Admissible only for bounded supervised routing** under recorded user attestation. | `docs/decisions/0026-admit-only-budget-and-hardware-feasible-backends.md` [asserted] |

### The Three-Way Answer

1. **Is SuperGrok reachable headlessly under the SUBSCRIPTION?**
   **YES.** xAI's official first-party coding agent, **Grok Build** (CLI binary `grok`), supports headless prompt execution (`grok -p "<prompt>"`) using an active session token authenticated via `grok login` (Browser OIDC) or `grok login --device-auth` (Device code) without setting `XAI_API_KEY` [cited: docs.x.ai/build/enterprise, docs.x.ai/build/cli/headless-scripting]. In this mode, execution draws from the consumer subscription's weekly allowance rather than incurring metered charges [cited: docs.x.ai/grok/overview].

2. **Is it only accessible as a chat surface?**
   **NO.** xAI does not restrict Grok to a web browser or chat interface. xAI released and open-sourced **Grok Build** as a dedicated terminal-based coding agent and ACP server specifically for developer workflows, headless scripting, CI/CD, and multi-agent orchestration [cited: x.ai/news/grok-build-cli, x.ai/news/grok-build-open-source].

3. **Is it only accessible via the metered xAI API?**
   **NO.** The xAI API (`https://api.x.ai/v1`, managed at `console.x.ai`) is billed per token and operates independently of consumer subscriptions [cited: x.ai/api]. Grok Build can use the API via `XAI_API_KEY`, but its default authentication priority resolves an active browser/device session token *before* falling back to `XAI_API_KEY` [cited: docs.x.ai/build/enterprise].

---

## 2. Question 1: First-Party CLI and Headless Agent Landscape

### 2.1 First-Party Harness: Grok Build (`grok`)
- **Status & Release:** xAI launched Grok Build in early beta for SuperGrok and X Premium+ subscribers and open-sourced the harness on 15 July 2026 [cited: x.ai/news/grok-build-cli, x.ai/news/grok-build-open-source].
- **Distribution & Installation:** Official installation script at `curl -fsSL https://x.ai/cli/install.sh | bash` [cited: docs.x.ai/build/overview].
- **Headless Execution:**
  - Single-shot prompt: `grok -p "<prompt>"` [cited: docs.x.ai/build/cli/headless-scripting].
  - Machine-readable output: `--output-format json` (terminal JSON summary) and `--output-format streaming-json` (newline-delimited JSON stream of events) [cited: docs.x.ai/build/cli/headless-scripting].
  - Permission auto-approval / bypass: `--always-approve` (alias `--yolo`), `--permission-mode dontAsk` (silently denies unallowed actions for headless/CI), `--permission-mode always-approve`, or the Claude Code alias `--dangerously-skip-permissions` [cited: docs.x.ai/build/features/permissions, docs.x.ai/build/cli/reference, docs.x.ai/build/enterprise].
  - Protocol support: Implements **Agent Client Protocol (ACP)** over stdio/JSON-RPC, allowing external orchestrators to drive Grok Build sessions directly [cited: x.ai/news/grok-build-cli, docs.x.ai/build/overview].
  - Worktree & Subagent support: Supports native git worktree creation (`-w, --worktree`), session resumption (`-r, --resume`), and parallel subagent delegation [cited: docs.x.ai/build/cli/reference].

### 2.2 Community CLIs and BYOK Tools
- **OpenCode (v1.18.18):** Supports Grok models through its OpenAI-compatible endpoint provider configuration (`base_url: https://api.x.ai/v1`) or OpenRouter [measured: `docs/20-design/backends.md`].
- **Aider / Generic BYOK Harnesses:** Support Grok via `XAI_API_KEY` over the standard API.
- **Limitation:** All third-party/community harnesses operate strictly via pay-per-token API keys; none can authenticate or consume the consumer SuperGrok subscription session quota [asserted].

---

## 3. Question 2: SuperGrok Heavy Subscription Scope vs Metered API

### 3.1 SuperGrok Heavy Plan Features
- **Price:** $300/month (launched 9 July 2025; promotional rate $99/month for first 3 months) [cited: felloai.com/grok-pricing, aibusinessweekly.net/p/grok-context-window].
- **Included Model Lineup:**
  - Confirmed full access to **Grok 4.5** (500k token context window) [cited: aibusinessweekly.net/p/grok-context-window].
  - Confirmed exclusive access to **Grok 4 Heavy**, xAI's multi-agent reasoning model utilising 16 parallel agents and test-time compute across a 256k token context window [cited: aibusinessweekly.net/p/grok-context-window, felloai.com/grok-pricing].
  - Maximum weekly usage allowance across consumer surfaces [cited: docs.x.ai/grok/overview].
  - Web UI (`grok.com`), mobile apps (iOS/Android), Imagine image/video generation, and Grok Bot beta [cited: docs.x.ai/grok/overview, aipricing.guru/subscriptions/xai-supergrok-heavy].

### 3.2 Subscription vs API Separation
- **No API Credits Included:** xAI explicitly maintains separate commercial infrastructure for consumer subscriptions and developer APIs [cited: x.ai/api, aibusinessweekly.net/p/grok-context-window]. A SuperGrok or SuperGrok Heavy subscription does **not** grant API credits or waive API token fees on `console.x.ai` [cited: aibusinessweekly.net/p/grok-context-window].
- **API Billing:** The developer API charges usage-based token rates ($2.00/M input, $6.00/M output, $0.50/M cached input for `grok-4.6` and `grok-4.5`) billed per token [cited: x.ai/api, docs.x.ai/developers/rate-limits].

### 3.3 Credential Resolution in Grok Build CLI
Grok Build resolves credentials in the following strict precedence [cited: docs.x.ai/build/enterprise]:
```text
model.api_key > model.env_key > active session token > XAI_API_KEY
```
When a developer authenticates via `grok login` or `grok login --device-auth` and runs `grok -p "..."` without setting `XAI_API_KEY`, Grok Build uses the **active session token**, billing usage against the subscription's weekly allowance rather than the metered API [cited: docs.x.ai/build/enterprise].

---

## 4. Question 3: Observable Per-Run Accounting & Admission Feasibility

### 4.1 Telemetry and Output Signals
- In headless mode (`--output-format streaming-json` or `json`), Grok Build emits session events, tool calls, and completion verdicts [cited: docs.x.ai/build/cli/headless-scripting].
- When calling the underlying API directly, responses include standard token counts (`prompt_tokens`, `completion_tokens`, `reasoning_tokens`) [cited: docs.x.ai/developers/model-capabilities/text/generate-text].

### 4.2 Subscription Headroom Visibility
- **Interactive Surface:** Grok Build provides `/usage` in the interactive TUI to view credit/usage details [cited: docs.x.ai/build/modes-and-commands].
- **Machine-Readable Headroom:** `grok inspect [--json]` surfaces configuration, loaded plugins, tools, and permission policies, but **does not expose a machine-readable individual remaining quota percentage, token allowance counter, or reset timestamp** [cited: docs.x.ai/build/cli/reference, docs.x.ai/build/enterprise].
- **API Rate Limits:** The developer API defines requests per second (RPS) and tokens per minute (TPM) by spend tier (T0 to T4) [cited: docs.x.ai/developers/rate-limits], but provides no endpoint returning remaining subscription allowance.

### 4.3 ADR-0026 & ADR-0029 Admission Classification
Under ADR-0026 (`docs/decisions/0026-admit-only-budget-and-hardware-feasible-backends.md`) and the zero-inference handshake discipline in EXP-27 (`docs/10-research/experiments/exp27/handshake.py`), backend admission evaluates as follows:

| Backend / Composition | Machine-Readable Headroom Source | Unattended Unbounded Routing | Bounded Supervised Routing |
|---|---|---|---|
| **Claude Code** | Status-line JSON (`used_percentage`, `resets_at`) [cited] | **Admitted** [measured] | **Admitted** [measured] |
| **Codex** | App-server `account/rateLimits/read` [measured] | **Admitted** [measured] | **Admitted** [measured] |
| **Cursor** | Tier in `status`/`about`; no individual quota counter [measured] | **Excluded** (`excluded_unknown_headroom`) [measured] | **Admitted** (under user attestation) [measured] |
| **Grok Build (SuperGrok)** | No individual quota counter exposed via CLI [cited] | **Excluded** (`excluded_unknown_headroom`) [asserted] | **Admitted** (under user attestation) [asserted] |
| **xAI API (`XAI_API_KEY`)** | Metered per-token billing [cited] | **Blocked** by ADR-0019 (unresolved paid capability acquisition) [asserted] | **Blocked** unless per-task hard caps enforced [asserted] |

**Conclusion:** Grok Build under a SuperGrok Heavy subscription exhibits the exact same architectural boundary as **Cursor**: it cannot participate in autonomous, unattended routing where quota headroom must be proven before dispatch, but is fully eligible for bounded, supervised execution under explicit user attestation.

---

## 5. Question 4: Terms of Service & Acceptable Use Policy Analysis

### 5.1 xAI Acceptable Use Policy (AUP) Restrictions
The xAI Acceptable Use Policy prohibits [cited: x.ai/legal/acceptable-use-policy]:
- *"Accessing the Services through unauthorized automated or non-human means, whether through a bot, script, or otherwise."*
- *"Modifying, copying, translating, leasing, selling, reselling, distributing, distilling, manipulating, using bots to access, reverse engineer, decompile, disassemble or otherwise seek to obtain the source code of our Service..."*

### 5.2 Legitimacy of Headless Grok Build Orchestration
- **Authorized Interface:** Grok Build is xAI's official, first-party software engineering agent. xAI's documentation explicitly promotes and details headless scripting (`grok -p`), CI/CD integration, and ACP orchestration [cited: docs.x.ai/build/overview, docs.x.ai/build/cli/headless-scripting].
- **Authentication Compliance:** Authenticating Grok Build via `grok login` or `grok login --device-auth` uses the first-party OAuth/OIDC handshake designed and maintained by xAI for CLI and remote devbox use [cited: docs.x.ai/build/enterprise].
- **Legal Boundary:** Driving Grok Build headlessly via CLI flags or ACP is compliant with xAI's terms [asserted]. In contrast, building an automated scraper to reverse-engineer `grok.com` web sessions or bypass Grok Build's auth flows would violate the AUP's prohibition against unauthorized automation and reverse engineering [asserted].

---

## 6. Consilience Evaluation: Is a Fourth Family Worth Doing?

### 6.1 The Epistemic Case FOR (A Fourth Evidence Class)
- **Whewell's Second Clause:** *"an Induction, obtained from one class of facts, coincides with an Induction obtained from another different class"* (`CONSILIENCE.md`) [cited].
- **Orthogonal Training Heritage:** Grok models are trained on the Colossus cluster infrastructure with distinct pretraining mixtures (including live X/real-time web signals) and unique post-training regimes (Grok 4 Heavy uses 16-agent test-time compute search) [cited: aibusinessweekly.net/p/grok-context-window].
- **Proven Cross-Family Value in Consilience:** In our research findings, cross-family multi-agent inspection repeatedly uncovered blind spots: Claude Code leaking search terms, Codex identifying arithmetic cancellations in apparent β agreement, and Cursor revealing platform-specific execution seams [measured: `docs/10-research/findings.md`].

### 6.2 The Adversarial Case AGAINST (Why Three Families Are Already Enough)

1. **The Shared Pretraining Echo Fallacy (Ao et al. 2026 Theorem):**
   Ao, Gao & Simchi-Levi (*Decision-Theoretic Foundations of Delegated Agent Networks*, arXiv:2603.26993) prove mathematically that without new *exogenous* signals, a delegated network of agents is decision-theoretically dominated by a single decision-maker with the same information [cited].
   - All frontier LLMs (Claude, GPT-4/Codex, Gemini, Grok) share massive underlying pretraining corpora (Common Crawl, GitHub, Wikipedia, arXiv, and synthetic data distilled from earlier frontier models) [asserted].
   - When four model families agree on a code diff without running tests, that agreement is overwhelmingly **echo** across shared training distributions, not consilience across independent empirical facts [asserted].

2. **The Arithmetic Cancellation / False Consensus Trap:**
   Measured Consilience experiments demonstrated that multi-family consensus can produce false confidence through the cancellation of orthogonal errors rather than true convergence on ground truth [measured]. Adding a fourth uncalibrated model increases the complexity of error correlation without guaranteeing a decrease in false acceptance rate $\beta$.

3. **Asymmetry Between Generative Models and Verification Oracles:**
   In software engineering, the primary test of truth is the automated verification oracle (compiler, typechecker, test suite, linters), not an LLM voting panel [asserted].
   $$\text{A diff that passes a strict test suite is validated; a diff that passes four LLM reviews without running tests is merely four echoes.}$$
   Adding Grok as a fourth generator does not improve the verification oracle where $\beta$ is measured.

4. **Financial and Operational Diminishing Returns:**
   Joe currently holds three ~£200/month subscriptions (Claude Max, ChatGPT Pro/Codex, Cursor Ultra) [asserted]. Adding SuperGrok Heavy at $300/month (£230+/mo) increases monthly subscription spend by ~38% while adding an adapter maintenance surface that lacks machine-readable quota telemetry and cannot be admitted to unattended routing [asserted].

---

## 7. Operational Recommendations & Next Steps

### 7.1 Verdict
- **Feasibility:** Headless orchestration under the SuperGrok subscription is **technically feasible** via `Grok Build` (`grok -p` / ACP).
- **Admission:** Grok Build is **excluded from unattended unbounded routing** (fail-closed under ADR-0026) and admitted only for **bounded supervised work** under user attestation.
- **Value:** A fourth model family provides diminishing epistemic returns unless deployed specifically on tasks where exogenous reasoning search (Grok 4 Heavy test-time compute) can be evaluated against automated verification.

### 7.2 Decision & Gating Rules
1. **Purchase Gate:** Joe should decide on the SuperGrok Heavy purchase based on his personal preference and interactive value; no autonomous spend or automated subscription acquisition may occur (ADR-0019) [asserted].
2. **Adapter Specification:** If SuperGrok Heavy is active:
   - Implement `adapter_grok_build.py` adhering to the headless pattern (`grok -p --always-approve --output-format streaming-json`).
   - Add zero-inference capability probe `probe_grok_build()` to `docs/10-research/experiments/exp27/handshake.py`.
   - Mark admission state as `admitted_bounded_supervised` with `usable_for_unattended = False`.
3. **Falsifier:** If xAI releases a machine-readable individual quota endpoint in `grok inspect --json` or status line JSON, re-evaluate Grok Build for unattended admission under ADR-0026.

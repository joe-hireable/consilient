# Friction log

**Every manual step in the bootstrap harness that Consilience should automate.**
This is the v0 backlog, derived from use rather than imagination. See ADR-0017.

## How to keep it

One line per friction, dated, written **the moment it bites** — not reconstructed later,
because reconstruction remembers the dramatic frictions and forgets the frequent ones, and
the frequent ones are what matter.

```
| date | what I had to do by hand | how often | what would automate it |
```

**Never delete a line.** When Consilience automates something, add the commit reference in
the last column. The log is a record of what the tool is *for*; deleting satisfied entries
erases the justification for features that exist.

**Be honest about the ones that never recur.** A friction logged once and never repeated is
evidence *against* building for it. Mark those `one-off` rather than quietly leaving them
to inflate the backlog.

## The test this log exists to run

ADR-0017 states it plainly: if this log stays short for a month, one of two things is true.

1. **Claude Code is already sufficient**, and Consilience solves a problem Joe does not
   personally have. That is a serious finding for ADR-0004's premise that "the smallest
   thing worth a stranger's install and the smallest thing that improves my week are the
   same artefact" — and it should be reported, not buried.
2. **The log is not being kept honestly**, which is the more likely explanation and worth
   naming in advance.

Either way, a short log is information. Do not pad it.

## Log

| date | manual step | frequency | would be automated by |
|---|---|---|---|
| 2026-08-19 | Chose which model to use for a task by feel, with no measurement of whether the cheap one would have sufficed | every task | the cascade + β-meter (ADR-0002) |
| 2026-08-19 | Re-explained project context at session start despite `CLAUDE.md` | every session | memory layer wake-up (ADR-0017) |
| 2026-08-19 | Manually decided whether a design question warranted research vs answering from priors | several times per session | the Inquiry tier trigger (`docs/20-design/inquiry-tier.md`) |
| 2026-08-19 | Checked prior art by hand and found three times that a feature already existed | per feature idea | `checking-prior-art` skill; possibly a standing pre-design check |

*(Seed entries from the session that produced this repository. Add as you go.)*

**EXP-16 entries (19 Aug 2026) — frictions hit while prototyping the meeting layer on
rented PM tools:**

| date | manual step | frequency | would be automated by |
|---|---|---|---|
| 2026-08-19 | Linear MCP requires interactive browser OAuth; an agent cannot connect a PM tool alone — one experiment arm blocked on a human | once per tool | native store needing no third-party auth; or a credential broker (ADR-0019 territory) |
| 2026-08-19 | ClickUp MCP reads custom fields but cannot create field definitions — the RACI matrix degraded to markdown-in-description on day one | per workspace | native ticket store with typed role fields (ADR-0006 schema change from ADR-0020) |
| 2026-08-19 | Every agent write lands under one OAuth identity ("Joe") — per-agent attribution impossible in ClickUp and Slack, making ADR-0020's "outcome writes attributed to the Owner only" check unenforceable | every write | native store with a first-class `actor` field per event |
| 2026-08-19 | Six of six meeting Owners hit `Status does not exist` setting a `decided` status; no way to discover a list's valid statuses except a failed write or an extra call | every decision close | harness-owned decision state machine |
| 2026-08-19 | Latency instrumentation had to bracket MCP calls with separate Bash timestamp calls — measurements contaminated by agent-turn overhead | every measurement | harness-level tool-call telemetry in the trajectory log |
| 2026-08-19 | Parallel agents cannot safely append to one JSONL trajectory file; the orchestrator became the single writer by hand | every multi-agent run | exactly ADR-0006's split: SQLite for concurrent state, single-writer append-only log |
| 2026-08-19 | Verified licences of 20+ candidate tools by hand (GitHub API + raw LICENSE files) because directory listings and blog posts misstate them — found one proprietary landmine (anthropics/skills doc skills) in an "open" repo | per curation pass | licence audit in the capability loader; blocks bundling non-OSS |
| 2026-08-19 | Hand-checked four vendor blog figures at origin: three were single illustrative examples presented as results, one had an undefined metric | per cited number | the existing [FULL]-before-cite rule, enforced by the citing-sources skill |
| 2026-08-19 | Assembled a model's reasoning-capability tri-state by hand from three registries with three different flag semantics | per model considered | registry adapter with normalised tri-state (ADR-0025 territory) |
| 2026-08-19 | Nearly installed `cursor-agent` from npm — it is an unrelated individual's package, not Anysphere's CLI. Caught only by checking maintainer/repo before installing | per new tool adopted | the ADR-0016 supply-chain check, automated: verify publisher identity against the vendor's own documented install route before any install |
| 2026-08-19 | Installed Cursor's CLI into WSL because it ships linux/darwin only, then hand-wrote a path-translation seam (`C:\…` ↔ `/mnt/c/…`) so the orchestrator and agent could name the same directory | per cross-namespace agent | namespace-aware paths in the ticket schema (the interface change adapter #3 forced) |
| 2026-08-19 | Reconciled three mutually incompatible token/cost accountings by hand (Claude: last-call tokens + cost; Codex: cumulative session tokens, no cost; Cursor: neither) | per backend comparison | per-adapter accounting normalisation, or an explicit "not comparable" contract in the outcome schema |
| 2026-08-19 | Inspected a saved scratch repository by hand after a backend process exited successfully with no final message and no file change; the runner's `ok` signal contradicted the verifier | per ambiguous backend completion | record runner completion and verifier acceptance as separate fields, with only the verifier allowed to accept the artifact |
| 2026-08-19 | Reconciled subscription headroom from three incompatible surfaces: Claude status-line JSON, Codex's app-server protocol and Cursor's human dashboard; only two had a machine-readable individual-plan signal | before every constrained route | provider-specific headroom readers plus conservative trajectory-log accounting (ADR-0026) |
| 2026-08-19 | Re-read LLM Checker's current licence after ADR-0005 had called it open source; its NPDL terms prohibit paid distribution and monetised hosting | per candidate dependency | the ADR-0016 licence check at discovery time, before a tool can become a wrapper candidate |
| 2026-08-19 | Compared local-fit tools by hand and found LM Studio's estimator starts only after the model is downloaded, too late for the requested download gate | per local backend/tool | a pre-download fit-provider capability probe, with post-download estimators treated only as a second gate |
| 2026-08-19 | Found that an ordinary OpenRouter completion key is insufficient for provider-enforced per-task caps; creating capped task keys requires a separate management API key | once per OpenRouter account setup | guided management-key setup plus automatic task-key creation and deletion (ADR-0026) |
| 2026-08-19 | Corrected the pre-live assumption that Cursor exposed no token accounting: its successful final JSON contained separate input, output, cache-read and cache-write fields, which the adapter had discarded | once on first live adapter run | parse and retain backend-native usage fields; never infer a missing field from help text alone |
| 2026-08-19 | Running one selected backend overwrote the three earlier rows in `backend-comparison.json`; recovered them from git by hand | once per partial comparison before the fix | merge selected backend results by agent identity, with a regression check |
| 2026-08-19 | A provider-shaped “backend” label hid that Codex was the coding harness, so a pre-artefact composition failure was almost attributed to OpenRouter/Qwen capability | once per conflated result schema | explicit domain × harness × provider × model identity plus a schema check (ADR-0027) |
| 2026-08-19 | Codex inherited unrelated global MCP configuration during an isolated provider test | once per supposedly isolated experimental run | adapter isolation flag enforced by a regression check |
| 2026-08-19 | A headless Codex run waited indefinitely for inherited stdin, and the adapter initially discarded its structured failure event | once per new headless adapter | close stdin and retain structured errors; both enforced by adapter checks |
| 2026-08-19 | The official OpenCode one-line WSL installer failed at the Windows shell quoting boundary; downloaded the same installer to WSL `/tmp` and ran it as a second step | one-off | shell-free installer invocation or platform-aware command transport |
| 2026-08-19 | OpenCode reported $0.0170272 for its session; OpenRouter read zero immediately and $0.045138255 later, after several earlier attempts that may have settled late | per cross-surface cost reconciliation | retain session and provider accounting separately with observation times; never infer per-run cost from an unattributed cumulative counter |
| 2026-08-19 | An installed CLI was initially treated as “available” without first proving its subscription login/key was configured | per harness discovery | provider-specific authentication readiness checks, with installed and authenticated as separate states (ADR-0027) |
| 2026-08-19 | Manually reasoned about whether expiring paid subscription capacity should be saved, used before reset or replaced by metered work | before every reset or plan review | reset-aware positive-value backlog ranking and plan-rightsizing advice (ADR-0028 / EXP-23) |
| 2026-08-19 | A tests-only smoke verifier accepted an OpenCode artefact that added the requested function **and** an unrequested duplicate test file; the unexpected four-test count exposed it | once on first OpenCode run; general risk per verifier | verify the allowed changed-file set as well as functional tests, with a regression fixture rejecting extra files |
| 2026-08-19 | “Control Cursor via MCP” initially blurred protocol direction: Cursor consumes MCP tools, while its supported external-control surface is ACP over stdio | once during integration design; general risk per bidirectional protocol | record control protocol separately from harness/provider/model; expose any future MCP delegation only through the coordinator |
| 2026-08-19 | Cursor ACP requested two execution permissions during a headless smoke run | per headless ACP tool request | retain every request and selected response in the trajectory; allow-once only in the bounded experiment, with product policy deferred to the approved spec |
| 2026-08-19 | PowerShell startup and nested quoting failed around OneDrive-managed profile state while probing native CLIs | several setup commands | use a profile-free native process invocation and structured arguments rather than shell-composed commands |
| 2026-08-19 | `agy models` succeeded through a saved identity while Antigravity print mode failed before inference, so installation plus model discovery falsely appeared execution-ready | once on first Antigravity probe; risk per backend discovery | require a successful zero-tool structured probe and live plan/quota snapshot before admission |
| 2026-08-19 | Antigravity's `--print` flag takes the prompt value; treating it as a boolean caused later flags to be consumed as the prompt | once during CLI probing | invoke the prompt as one structured argument (`--print=<value>`) and regression-test the emitted init/result stream |
| 2026-08-19 | The ambient Windows `python` command resolved to an unset pyenv shim, so the verifier's regression suite appeared to fail because `pytest` was unavailable in a fallback runtime | once per machine without a selected pyenv version | run the experiment checks with the explicit installed 3.13 interpreter and report interpreter readiness separately from artefact failure |
| 2026-08-19 | The Codex ClickUp connector advertised `clickup_create_task_comment` but rejected the operation as “tool not found”; the same evidence update posted to Slack successfully | once on the current connector build; risk per unattended status projection | treat external PM updates as non-authoritative projections, retain the committed trajectory as truth, and retry ClickUp only after connector readiness is re-established |
| 2026-08-19 | A cold Codex×Ollama Qwen audit completed but invoked no repository tools, said it could not access the files and guessed that the new specification “likely” existed | once on first cold-reader pass; risk per local audit/model admission | capability admission must prove required repository reads/tool use before a model can count as an auditor; completion and token use are not evidence |
| 2026-08-19 | EXP-07 wrote results only at normal process completion; interrupting an invalid run discarded five completed frontier attempts and ten completed local attempts | once on first interrupted batch; risk per long experiment | atomically persist every admitted snapshot and attempt before starting the next one; resume from the append-only partial record |
| 2026-08-19 | One local EXP-07 subprocess exceeded its nominal timeout by roughly a minute, so the outer wall-clock cap was not enforceable from the registered per-attempt timeout alone | once observed; risk per nested process timeout | separate agent/verifier timeouts and check remaining outer budget before every attempt |
| 2026-08-19 | A delegated first-party-source pass misidentified the measured Cursor Ultra account as Pro and claimed release/feed surfaces that direct checks contradicted | once on first delegated vendor-monitor pass; risk per vendor-source update | fixed first-party source allowlist plus direct transport/schema probe; delegated summaries remain untrusted input |
| 2026-08-19 | A long prompt pasted into an interactive Claude remote-control session lost its beginning and started an invalid review | once on first programmatic remote-control prompt; risk per long terminal paste | typed/session API or short staged messages with an echoed task hash before work starts |
| 2026-08-19 | A Claude Code print-mode worker could not be made visible through Remote Control after launch | once on first headless overnight worker; risk per invisible dispatch | launch future interactive Claude workers with native Remote Control before assigning work; keep headless mode for bounded machine-only probes |
| 2026-08-19 | A max-effort Fable challenge consumed over ten minutes and more than 32k context tokens without emitting a finding, then produced no compact memo after a constrained re-prompt | once on first Fable orchestration challenge; risk per open-ended reviewer | enforce a short no-delta deadline, bounded output contract and cancellation; an adversarial role does not exempt a worker from evidence-yield economics |
| 2026-08-19 | Cursor's print-mode CLI rejected `--mode agent`; only `plan` and `ask` are named modes, while edit-capable execution is the default plus `--force`/`--yolo` | once on first autonomous Cursor dispatch; risk per CLI version change | versioned provider invocation profiles verified against live `--help` before dispatch |

## What does not belong here

- Bugs in Claude Code. Those go upstream.
- Things that are annoying but that Consilience should not do. Scope creep enters through
  this file more easily than anywhere else, because every friction feels like a feature
  request.
- Frictions with no plausible automation. Log them if you like, but mark them
  `not-automatable` so they do not silently become requirements.

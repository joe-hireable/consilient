# Friction log

**Every manual step in the bootstrap harness that Consilient should automate.**
This is the v0 backlog, derived from use rather than imagination. See ADR-0017.

## How to keep it

One line per friction, dated, written **the moment it bites** — not reconstructed later,
because reconstruction remembers the dramatic frictions and forgets the frequent ones, and
the frequent ones are what matter.

```
| date | what I had to do by hand | how often | what would automate it |
```

**Never delete a line.** When Consilient automates something, add the commit reference in
the last column. The log is a record of what the tool is *for*; deleting satisfied entries
erases the justification for features that exist.

**Be honest about the ones that never recur.** A friction logged once and never repeated is
evidence *against* building for it. Mark those `one-off` rather than quietly leaving them
to inflate the backlog.

## The test this log exists to run

ADR-0017 states it plainly: if this log stays short for a month, one of two things is true.

1. **Claude Code is already sufficient**, and Consilient solves a problem Joe does not
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
| 2026-08-19 | WSL-side Git rewrote an externally created Cursor worktree pointer into the Linux namespace and normalised line endings, making Windows Git report a broken worktree and inflating a four-file semantic patch from 360 additions/deletions to 1,129 | once on first cross-namespace Cursor writer; risk per Windows/WSL worktree | create and own worktrees inside the executing harness namespace, record both host/guest paths, and reject line-ending-only churn before integration |
| 2026-08-19 | A live third-party API credential entered chat and therefore persisted in local session records, although a repository-history search found no committed occurrence | once in the recovered origin record; general risk per credential hand-off | OS keychain or environment-only hand-off plus dependency-free tracked-history secret scanning; rotate the exposed credential before publication |
| 2026-08-20 | Text pasted into an interactive Claude Remote Control session appeared in the composer but was not accepted until a separate Enter action | every programmatic interactive dispatch on the tested surface | typed control with separate persisted, projected, adapter-accepted, model-included and effect-evidenced acknowledgements (EXP-26) |
| 2026-08-20 | Reconciled Claude's interactive `/usage` view by hand: it exposed session/week use and resets plus usage-credit state, while its estimate excluded activity outside the observed Claude Code surface | before every constrained Claude dispatch | an authenticated headroom reader with source scope, freshness and metered-fallback state; fail closed when any is unknown (ADR-0026/0028) |
| 2026-08-20 | The EXP-07 regression suite wrote checkpoints to the production result path and deleted the completed untracked result during test cleanup | once on first post-run verification; general risk per research instrument | isolate every test output in a temporary path and verify the retained result hash before and after the suite |
| 2026-08-20 | A read-only Opus review consumed about 15,600 reported tokens and six minutes before producing a compact actionable memo | once in the reviewed session; general risk when a reviewer keeps exploring after its evidence delta is already bounded | request a fixed-size decision memo up front and interrupt after two no-delta rounds; reviewer intelligence does not justify unbounded context use |
| 2026-08-21 | Serialised `cursor-agent` launches by hand after concurrent launches raced the CLI's shared config file and wiped the trust list machine-wide | twice in one evening before the exclusive lock (`.harness/cursor-agent.lock`) existed; risk per parallel Cursor dispatch | launch serialisation enforced by the dispatcher itself, not by operator discipline — the lock landed after the wipe, and a rule that lives in a brief is one tired evening away from being skipped |
| 2026-08-21 | Opened dispatch transcripts by hand to tell "timed out" apart from "nearly finished": of 35 dispatches measured tonight, 5 timed out returning zero bytes, and the timeout line alone carries no progress signal | per timed-out dispatch; 5 of 35 tonight | mid-run artefact-progress sampling on dispatched workers — the loop already resolves liveness from artefact bytes (`loop.status`); dispatch does not use it, so a stalled arm burns its whole window |
| 2026-08-21 | Repaired a torn trajectory line by hand: two concurrent dispatch processes appended to `.harness/log/2026-08-21.jsonl` at 19:56:39.051836 and .051872 (36µs apart); one line landed whole (run 20260821T195638-35b10d9200), the other's head was lost, leaving a 152-byte orphan tail that two invariant tests counted as an unpinned rejection and a 93rd append-bypass. The fragment (`…", do not commit;\nleave the work in the tree and say so.\n","timed_out":false},"event":"dispatch.outcome","ts":"2026-08-21T19:56:39.051872+00:00",…`) was unrecoverable — its head never reached the file — so it was removed and recorded here rather than pinned into the tolerated baseline, which would teach the gate to tolerate torn writes | once, but every concurrent dispatch window risks it | atomic append for the trajectory: one writer per line with a lock or O_APPEND-sized writes, enforced in `events.append` — the same lesson as the cursor-agent lock, one layer down |

**Back-filled 20 Aug 2026 from `docs/10-research/exp16-results.md` (Linear leg) and
`docs/10-research/experiments/exp05/findings-exp05.md`.** These four bit on 19 August and were
written up a day later, so they are dated when they bit, not when they were written — which is
precisely the reconstruction § *How to keep it* warns against, and they are marked so a reader
weights them accordingly. Frequency is the observed count plus the mechanism the risk attaches
to; neither source states a rate.

| date | manual step | frequency | would be automated by |
|---|---|---|---|
| 2026-08-19 | Read a Linear issue back to discover its MCP surface had accepted a write of the nonexistent state `decided` with no error and left the issue at `Done` — ClickUp rejects the identical write loudly, so on Linear the divergence is invisible until something re-reads the record, and a trajectory log would have carried the write as true | once observed on the Linear leg; risk per silently coercing write surface | harness-owned status vocabulary plus a write-then-read-back check; an external projection that cannot fail loudly is not a state store |
| 2026-08-19 | Hand-encoded "parked awaiting user evidence" as the label `parked-awaiting-user` on HIR-50, because Linear's vocabulary (Backlog / Todo / In Progress / In Review / Done / Canceled / Duplicate) has no such state and its MCP surface exposes no status creation — semantics-in-labels, the same structure theatre as ClickUp's RACI-in-markdown | per decision state the rented tool's vocabulary lacks | typed decision states in the native store (ADR-0006); a label is not a schema |
| 2026-08-19 | Authenticated the Cursor CLI by hand inside the WSL namespace, separately from the host-side install, before the composition could be exercised at all — `run_all.py` admits Cursor only once `cursor-agent status` reports logged in, so it was absent from the first comparable coding run until that was done | once for Cursor; risk per harness whose login lives in a namespace other than the host's | login state probed per composition *and* per namespace, with installed and authenticated held as separate states (ADR-0027) |
| 2026-08-19 | Supplied the OpenRouter API key by hand before either OpenRouter composition could be admitted at all, then carried it across the Windows/WSL boundary through the inherited environment for OpenCode, because neither a command-line flag nor a stored OpenCode credential was used | once per provider account per namespace | a broker holding provider credentials once and injecting them per composition and namespace (ADR-0019 territory) — never the command line, never chat |

## What does not belong here

- Bugs in Claude Code. Those go upstream.
- Things that are annoying but that Consilient should not do. Scope creep enters through
  this file more easily than anywhere else, because every friction feels like a feature
  request.
- Frictions with no plausible automation. Log them if you like, but mark them
  `not-automatable` so they do not silently become requirements.

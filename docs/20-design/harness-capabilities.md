# Harness capabilities — what these things can actually do, as opposed to what they are called

Status: survey, 21 August 2026. Supporting evidence for
[`../decisions/0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md`](../decisions/0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md).

**This file has two halves and they must not be read as one.**

- **PRODUCT** — the taxonomy, the probe method, and the finding that a harness's label does not
  predict its capability. Ships open source. Useful to anyone with more than one harness.
- **INSTANCE** — what is installed and configured on Joe's machine on 21 August 2026, under his
  subscriptions. Not a product claim. Contains **no credential, no token and no value** — only
  binary versions, flag names, server names and command lines. It will be stale within weeks and
  should be re-probed rather than trusted.

Every row carries `[measured]` (run here, output observed), `[cited]` (a named source with a URL)
or `[asserted]` (judgement, no evidence yet). **Most non-coding capability claims in circulation
are `[asserted]`, including several in the instruction that produced this survey, and saying so
is the deliverable.**

---

# PART 1 — PRODUCT

## The finding, stated first

**A harness's label does not predict its capability, and on this machine it inverts it.**

Three measured inversions, all on 21 August 2026:

1. **The harness with the widest non-coding reach is Claude Code**, with 46 MCP servers attached
   — two independent browser drivers, a Figma server, a diagramming server, document servers, a
   calendar, an e-signature service and six analytics platforms. [measured]
2. **Codex — the most narrowly "coding"-labelled of the four — is the only harness here carrying
   an operating-system control runtime at all**: `computer-use@openai-bundled`, installed and
   enabled, with a documented Windows window API including screenshot capture. [measured]
   **OpenAI's own documentation says that capability has no CLI surface.** [cited] The conflict is
   unresolved, is written up below, and is the best illustration in this file of why a probe beats
   both a label and a vendor page. Codex separately has native `--image` input and `$imagegen`
   generation in the CLI [cited] — genuinely non-coding capability in the harness nobody calls a
   visual tool.
3. **Cursor, the harness named in the instruction as the browser and visual-analysis specialist,
   serves no browser tool at all from its CLI.** [measured] Probed directly on two models; the
   served surface contains no browser, no screenshot and no computer control, and Cursor has zero
   MCP servers configured on either side of the WSL boundary. The bundle carries the whole
   machinery, but `browser_use_enabled` is a flag Cursor's **backend** sets per account. See
   *The probe that settles the instruction's headline claim* below — it is the single most
   important section in this file.

None of that is knowable from the four products' names, and all of it is knowable in about twenty
minutes of `--help` and config reading with zero inference and zero metered spend.

## Capability is a property of the composition, not the harness

The same harness has different capabilities on different machines, and on the same machine at
different times. Claude Code with 46 servers and Claude Code with none are the same product at
the same version. This is why ADR-0054 keys its capability rows on
`(ADR-0027 tuple + attached servers + versions)` rather than on a harness name, and why ADR-0029's
rule binds: **a change to the attached server set invalidates a capability row and may never
create one.**

The practical consequence for anyone reading this outside Joe's machine: **the table in Part 2 is
not a product feature matrix.** Reproduce the probe; do not copy the answers.

## The three columns worth probing, and which are free

Following ADR-0054 §1, and reusing decisions that already exist:

| Column | Question | Cost | Already decided by |
|---|---|---|---|
| **reach** | Does this composition have the tool at all? | Free — `--help`, config files, `mcp list`. Zero inference, zero tokens, zero spend. | ADR-0042 |
| **strength** | How good is it, against a frontier reference on the same tasks? | One paired probe run per candidate. | ADR-0025 |
| **anchor** | As a *verifier*, does it reach a class of facts another verifier cannot? | A mutation census per task family. | ADR-0054 §3, taxonomy from `../10-research/qa-automation-and-the-anchor-problem.md` |

**The first column is free and nobody was reading it.** Every measured fact in Part 2 came from
`--help` output, bundled JavaScript strings and configuration files. No task was run, no prompt
was sent, no metered call was made, and no subscription quota was consumed. A capability survey
that costs nothing has no excuse for being replaced by a vendor's marketing page.

## What a "non-coding capability" turns out to be

Sorted by what actually supplies it, which is rarely the harness:

- **Browser automation and page observation** — supplied by an **MCP server** (Playwright,
  chrome-devtools), not by the harness. Any harness that speaks MCP inherits it; any harness
  without a server lacks it regardless of what its marketing says. **Attribute the capability to
  the server, not to the vendor** — that generalises across every MCP-speaking harness instead of
  enumerating products one at a time. The only harness measured here with *native* CLI browser
  control is Claude Code. Cursor's apparently-native `browser_use` turned out to be a cloud job
  kind behind a backend-set account flag, not a local tool.
- **Operating-system control** — supplied by a bundled runtime, not MCP. Only Codex has one
  here, and whether the CLI can actually reach it is contested between the machine and the
  vendor's documentation.
- **Design work** — supplied by the Figma MCP server or a local Dev Mode bridge. Note that
  `../20-design/design-capability-assessment-2026-08-20.md` already defers design to a post-v0
  gate and requires aesthetic output be labelled `unverified`; a Figma server changes *reach*, not
  that gate.
- **Document drafting** — the harness writes files; the *format* work is a tooling question
  already surveyed in `capability-layer.md`, which records that Anthropic's document skills are
  proprietary and cannot be bundled, and that the open path is pandoc + python-docx/openpyxl/
  python-pptx + docxtpl + headless LibreOffice.
- **Long-horizon and batch work** — supplied by the harness itself, and this is the one class
  where the harness genuinely is the capability: background modes, cloud workers, leader daemons,
  session resume and worktree isolation are all harness-native and differ sharply between them.
- **Autonomous QA and user simulation** — **not a capability at all in the sense the others are.**
  It is a verifier design question, and this repository has already answered most of it:
  `qa-automation-and-the-anchor-problem.md` establishes that a synthetic user contributes a
  different class of facts only through its *input sequence and implicit oracle*, never through
  its expectation, and `interface-beta-2026-08-20.md` item 6 already refuses simulated personas
  and visual-LLM judges as acceptance signals. A harness that can drive a browser is a transport
  to an implicit oracle. It is not a source of QA judgement.

---

# PART 2 — INSTANCE

**Joe's machine, Windows 11 + WSL2, 21 August 2026.** Subscriptions in use: Claude Max, OpenAI
Codex, Cursor, SuperGrok Heavy, and OpenRouter as the only permitted metered vendor (ADR-0044).
No credential value appears below. Re-probe before relying on any of it.

## What is installed

| Harness | Version | Where | [tag] |
|---|---|---|---|
| Claude Code | `2.1.238`, native binary | `~/.local/bin/claude.exe` | `[measured]` |
| Codex CLI | `codex-cli 0.148.0` (`@openai/codex`) | npm global | `[measured]` |
| Cursor Agent | `2026.08.11-e8db854` | **WSL only**, `/home/jpbpr/.local/bin/cursor-agent` — absent from the Windows PATH | `[measured]` |
| Grok | `1.0.5` (`@xai-official/grok`) | `~/.grok/bin/grok.exe` | `[measured]` |
| **opencode** | **not installed** | absent from Windows *and* WSL PATH | `[measured]` |
| **Antigravity** | IDE `0.26.0`, **no CLI binary exists on disk** | Electron app only; `resources/bin/` holds a language server and a webm encoder and nothing else | `[measured]` |

**Two of those negatives are load-bearing.**

**opencode is not installed**, and `backends.md` plus `architecture-sketch.md` both name it as
*"the default coding harness when no vendor-native frontier harness is authenticated"*. The
documented fallback is not present on the machine. That is a discrepancy between the operator's
view and the machine, and it is exactly the sort of thing a free `reach` probe catches and a
document review does not. It does not invalidate the doctrine — the fallback is a policy about
what to install — but `consil doctor` should not be able to report a fallback that is not there.

**Antigravity cannot be meta-harnessed today.** There is no executable to invoke. A directory at
`~/.gemini/antigravity-cli/` exists with logs from 19 August, conversation stores and a completed
onboarding marker, which is `[asserted]` evidence that the IDE has an embedded agent-manager
surface — but an embedded surface is not a CLI and there is nothing for an adapter to spawn.
EXP-39, which asks whether the three-signal Antigravity admission rule is observable, is blocked
on something more basic than a quota payload.

## Non-coding capability, measured

`reach` only. Nothing below has been probed for `strength` or `anchor`, and no row here is
`measured` in ADR-0054's sense — they are all `unprobed` or, where a server reports Connected,
`probed`.

### Browser automation and observation of a rendered page

| Composition | What supplies it | State | [tag] |
|---|---|---|---|
| Claude Code | `plugin:playwright:playwright` → `npx @playwright/mcp@latest`, **Connected**; `plugin:chrome-devtools-mcp:chrome-devtools` → `npx chrome-devtools-mcp@1.7.0`, **Connected**. Two independent drivers. Also `--chrome` / `--no-chrome` flags for a Chrome integration. | `probed` | `[measured]` |
| Codex | `playwright` and `chrome-devtools` both registered as stdio MCP servers in `~/.codex/config.toml`, and both officially named on OpenAI's MCP page. **No native browser: the vendor explicitly denies one for the CLI** (see the documentation section below). | `probed` via MCP; natively **absent** | `[measured]` + `[cited]` |
| Antigravity IDE | `chrome-devtools-mcp` registered in `~/.gemini/config/mcp_config.json`; server dirs materialised, so it has been launched | `probed`, but unreachable — no CLI | `[measured]` |
| **Cursor** | **No browser tool is served, and no MCP servers are configured.** Probed directly — see below. `mcp.json` absent on both sides of the WSL boundary. The bundle carries the full machinery (`browser_use`, a complete computer-use protobuf, 44 `screenshot` strings) but `browser_use_enabled` is a **backend-set account flag** and `browser_use` is a **cloud job kind**, not a local tool registration. | **absent** for this account | `[measured]` — two independent lines |
| Grok | **No MCP servers configured.** No browser flags. | `unprobed`, likely absent | `[measured]` |


### ⚑ The probe that settles the instruction's headline claim

Run 21 August 2026, after the tables above were written. It changed them.

**Line 1 — the served tool surface.**
`cursor-agent -p --trust --model composer-2.5 "List every tool you have available to you right
now."` returns exactly 22 tools:

> Shell · CreateGoal · UpdateGoal · Grep · Delete · WebSearch · WebFetch · GenerateImage ·
> ReadLints · EditNotebook · TodoWrite · StrReplace · Write · Read · Glob · AskQuestion · Task ·
> Await · GetMcpTools · FetchMcpResource · SwitchMode · CallMcpTool

**No browser tool. No screenshot tool. No computer control.** [measured] Re-run with
`--model sonnet-4.5`: 21 tools, `AwaitShell` in place of `Await` and no `ReadLints` — **the served
surface is model-dependent, and neither model is given a browser.** [measured]

**The caveat, which matters more here than anywhere else in this file: asking a model to
enumerate its own tools is a self-report**, and working principle 5 bans self-report as a signal.
Taken alone this line would be `[asserted]` however plausible it reads.

**Line 2 — the bundle, which is not a self-report.** Static grep of
`cursor-agent 2026.08.11-e8db854`: [measured]

- `browser_use_enabled` is a **scalar field in a settings protobuf**, sitting beside
  `ci_failure_followup_enabled` and `auto_create_pr_setting` — a flag the *backend* sets per
  account, not a client capability.
- `browser_use` is a value in a **background-agent job-kind enum**, beside `explore`,
  `video_review`, `media_review`, `shell` and `vm_setup_helper` — a cloud task type, not a local
  tool registration.
- A complete computer-use protocol is present — `computer_use_tool_pb`, `computer_use_supported`,
  `computer_use_init_result`, `computer_use_coordinate_mode` — and `screenshot` appears 44 times.

**The machinery is all there. None of it is served to this account.**

The two lines are different classes of facts — a runtime report and a static artefact — and they
agree. That is a small consilience in the sense of `CONSILIENCE.md` clause 2, and it is what
upgrades this finding from `[asserted]` to `[measured]`. One line alone would not have.

### What it actually means

**1. The instruction's premise is true of Cursor the IDE and false of Cursor the CLI.** A
meta-harness drives the CLI. Routing browser work to `cursor-agent` on the strength of Cursor's
marketing would have been precisely the label-not-capability error ADR-0054 exists to prevent —
**and the ADR would have committed that error in its own founding example.** That is the sharpest
evidence available for the decision, and one command produced it.

**2. The capability is server-gated, which is a stronger finding than "not installed".**
`browser_use_enabled` is set by the vendor's backend. Same binary, same version, same machine,
different account or different day → different capability. Capability is therefore not a property
of the *installed* composition either; it is a property of the composition **at dispatch**. This
is exactly why ADR-0042 probes at dispatch rather than at install, and why ADR-0029 lets change
intelligence invalidate a row but never create one.

**3. It reconciles the Codex conflict recorded below.** Bundled machinery is not served
capability, and that now holds at two vendors independently: Codex ships `computer-use` installed
and enabled while OpenAI documents no CLI surface; Cursor ships a complete computer-use protobuf
while serving no such tool. **Reading a binary tells you what a vendor built, not what it will
give you.** Neither the label, nor the documentation, nor the installed bytes answer the question.
Only the served surface does, and only at dispatch.

**4. Route the capability to the server, not to the harness.** `GetMcpTools`, `FetchMcpResource`
and `CallMcpTool` *are* served. Browser control is reachable from this CLI through an MCP server —
and Cursor has **zero servers configured here**, so it is reachable in principle and absent in
fact. The right object to attach a browser capability to is **the MCP server**, which generalises
across every harness that speaks MCP instead of enumerating vendors one at a time.

**5. The different-class-of-facts argument is untouched.** What changed is only which component
supplies the capability, not whether observing a running artefact reaches an anchor a source
reader cannot. ADR-0054 §3 is unaffected.

### The rule this produces, which may be the most useful thing here

**A capability claim that was never probed is `[asserted]`, however confident the vendor's
documentation sounds — and the probe must read the *served* surface: not the binary, not the
docs, and not the model's opinion of itself.**

Cost of applying it: one command, a few seconds, subscription quota already paid for, no metered
call. Cost of not applying it: an ADR about not trusting labels, whose founding example trusted a
label.

**On the instruction's central example.** "Cursor is great at visual analysis in browser, browser
automation" is **unverified here.** The mechanism plausibly exists — a native tool name in the
wire protocol and three enabled-by-default Playwright feature flags are not nothing — but the
flags are client-side defaults that the vendor's server can override, no server is attached, and
no run has been observed. Under ADR-0054 §4 that is `unprobed`, and `unprobed` routes to the
default generalist as a probe. **The correct response is to run one bounded probe, not to argue
about it**, and the probe is free.

### Operating-system control and screenshots outside a browser

| Composition | What supplies it | State | [tag] |
|---|---|---|---|
| **Codex** | `computer-use@openai-bundled` v`26.814.41957`, **installed and enabled**. Its bundled `docs/api.md` documents `target: "windows"` with `list_apps`, `launch_app`, `list_windows`, `get_window_state({include_screenshot, include_text})`, `click`, `press_key`, `type_text`, `scroll`, `set_value`, `drag`, `activate_window`. Driven through a local `node_repl` MCP server. | `probed` | `[measured]` |
| Everything else | nothing comparable | absent | `[measured]` |

**Do not route on this row yet.** OpenAI's documentation states Computer Use has no CLI
surface, which contradicts the local registry. See the unresolved-conflict table below;
the correct status is `unprobed`.

This is the single largest gap between label and capability found in the survey. It is also the
one with the widest blast radius, and ADR-0042's rules on egress and authorisation apply to it
with full force.

### Design

| Composition | What supplies it | State | [tag] |
|---|---|---|---|
| Claude Code | `claude.ai Figma` → `https://mcp.figma.com/mcp`, **Connected**; `claude.ai Lucid` → `https://mcp.lucid.app/mcp`, **Connected** | `probed` | `[measured]` |
| Antigravity IDE | `figma-dev-mode-mcp-server` → `mcp-remote http://127.0.0.1:3845/sse`, a bridge to the local Figma desktop app | `probed`, unreachable — no CLI | `[measured]` |
| Codex, Cursor, Grok | no Figma server | absent | `[measured]` |

Note that ADR-0042 recorded Figma as **unauthenticated** on 20 August and therefore a "purely
structural reference". It reports Connected under Claude Code on 21 August. That is a state
change, and under ADR-0029 it invalidates the old row rather than being inferred from it — the
capability must be re-probed, not upgraded by reading this sentence.

**Open Design** (nexu-io/open-design, Apache-2.0, ~90 k stars, 811 open issues, actively merged
PRs as of 21 August 2026). The desktop app was **not** found on this machine on 21 August
`[measured]` negative. Joe reported installing it on 21 August; **not re-probed** — the
installation is `[asserted]` until a probe confirms the binary, its version, and which harnesses
can reach it. A **portable skill** (`.agents/skills/using-open-design/`) now exists, carrying
the 9-section `DESIGN.md` contract format and a vendored 5-dimension critique with provenance
(`references/critique-upstream.md`, pinned to upstream blob `0e8d6cc`). The skill requires no
desktop app, daemon, or runtime dependency. `[measured]` — the skill file is committed and
readable by any harness that reads `.agents/skills/` or receives the portable core in a brief.

**Claude Design** (Anthropic, proprietary). Claude Code has a built-in `claude_design` MCP
server at `https://api.anthropic.com/v1/design/mcp`, but its OAuth flow is **broken** as of
21 August 2026 — the `/authorize` endpoint returns HTTP 410 and a misleading "Server Turned
Down" page. `[cited]` Three independent bug reports confirm this:
`anthropics/claude-code#69317`, `#77620`, `#84798`. Two community workarounds exist:
`kuatecno/mcp-design` (reads the `designOauth` keychain token directly, imports projects +
full chat history) and `e-brokenc0de/claude-design-mcp` (drives Claude Design via CDP/Chrome,
~30 tools, unofficial). Neither is installed here. The orchestration gap Joe reported —
Claude Design cannot easily talk to Cowork or Claude Code — is a **measured** Anthropic
product limitation, not a Consilient integration problem. `[cited]`

### Document drafting

| Composition | What supplies it | State | [tag] |
|---|---|---|---|
| Codex | bundled runtimes `documents`, `pdf`, `spreadsheets`, `presentations`, `template-creator` @`openai-primary-runtime 26.819.11345`, plus `visualize` and `sites`. `latex` present but not installed. | `probed` | `[measured]` |
| Grok | bundled skills including `docx`, `pdf`, `pptx`, `design`, `imagine` | `probed` | `[measured]` |
| Claude Code | Google Drive, Gmail, Docusign and Context7 servers Connected; document *format* skills are the proprietary-licence problem recorded in `capability-layer.md` | `probed` for transport, `unprobed` for authoring | `[measured]` |
| Cursor | 21 bundled skills, none document-format | absent | `[measured]` |

Every harness here can write a file. None of that is evidence any of them writes a *good*
document, and there is no oracle in this repository that would tell us. Under ADR-0054 §2 the
document-drafting family has no verifier contract, so it carries `beta.verdict = unverified` and
routes supervised.

### Long-horizon and batch work — the one class where the harness *is* the capability

| Composition | What it has | [tag] |
|---|---|---|
| Claude Code | `--bg/--background`, `--cloud`, `--environment`, `--remote-control`, `--teleport`, `-w/--worktree`, `--tmux`, `claude agents` background manager, `--max-budget-usd`, session resume/fork | `[measured]` |
| Grok | `grok agent leader` with a shared `~/.grok/leader.sock` letting many clients share one backend, `grok agent headless` over a WebSocket relay, `grok agent serve`, worktrees with a `worktrees.db`, `--restore-code` repository snapshots, resume/fork | `[measured]` |
| Cursor | `worker` subcommand — *"Start a private cloud worker that connects to Cursor to run agents in your environment"* — plus `-w/--worktree` into `~/.cursor/worktrees/`, `create-chat`/`ls`/`resume` | `[measured]` |
| Codex | `codex cloud`, `codex app-server` with `stdio://`, `unix://` and `ws://` listeners, `daemon`, `proxy`, `exec-server`, `remote-control`, resume/fork/archive | `[measured]` |

This is the richest and least-discussed axis, and it is the one where the four products differ
most from each other. It is also the axis where "coding harness" is least misleading, because
none of it is domain-specific at all.

### Control protocols — how a meta-harness talks to each

| Composition | Protocol | [tag] |
|---|---|---|
| Cursor | **ACP, via a hidden `cursor-agent acp` subcommand** that is absent from `--help` but exits 0 and is bundled as `.command("acp",{hidden:!0})`. `~/.cursor/acp-sessions/` contains a real session directory, so it has been used. | `[measured]` |
| Grok | ACP indirectly — `--output-format streaming-json` is documented in help as *"NDJSON of the agent native ACP session updates"*; `streaming-messages-json` emits the Anthropic Messages wire format. No `acp` subcommand. | `[measured]` |
| Codex | No ACP. Offers `codex mcp-server` (Codex *as* an MCP server) and `codex app-server`. | `[measured]` |
| Claude Code | No ACP. `-p` with `--output-format stream-json`, `--input-format stream-json`, `--json-schema`. | `[measured]` |

The hidden Cursor `acp` command is directly relevant to EXP-64, which asks whether the ACP Python
SDK can replace this repository's 233-line hand-written Cursor ACP client.

### MCP server counts, which is the number that actually predicts non-coding reach

| Harness | Servers | [tag] |
|---|---|---|
| Claude Code | **46** (`claude mcp list`), of which ~26 Connected, ~17 needing auth, 3 hard-failed | `[measured]` |
| Antigravity IDE | 15 | `[measured]` |
| Codex | 9, three of them not logged in | `[measured]` |
| Cursor | **0** | `[measured]` |
| Grok | **0** | `[measured]` |

## What is genuinely unverified, listed plainly

Everything in this section is `[asserted]`. Each is one bounded, free-or-cheap probe away from
being `[measured]`, and none of them should be argued about in the meantime.

1. ~~That Cursor can drive a browser from the CLI.~~ **Resolved by measurement, 21 Aug 2026: it
   cannot.** No browser tool is served on either model probed. Moved out of this list; see the
   probe section. Kept visible rather than deleted, because the trail from "the instruction's
   headline claim" to "measured false in one command" is the most useful thing this file records.
2. **That Cursor's visual analysis is good** — now moot for the CLI, since there is nothing to be
   good with. It remains unverified for Cursor the IDE, which a meta-harness cannot drive. Note
   also that "good at visual analysis" as an *acceptance signal* is refused doctrine here
   regardless of how good it is.
3. **That any harness performs autonomous QA or user simulation usefully.** Not probed, and the
   repository's existing position is that the useful part is the input sequence and the implicit
   oracle, not the simulation.
4. **That any harness drafts a good document.** No oracle exists, so this is not merely unmeasured
   but currently unmeasurable — ADR-0054 §2 routes it supervised and labelled `unverified`.
5. **That the Figma servers do useful design work** rather than merely connecting. Connected is a
   transport fact.
6. **That Codex's computer-use runtime works on this machine — now actively contradicted.** It
   is installed and enabled here `[measured]`; OpenAI documents it as having no CLI surface
   `[cited]`. `enabled` was never a behavioural fact, and now it is not even an uncontested
   configuration one. See the unresolved-conflict table below. **This is the row most likely to
   be believed wrongly, in either direction.**
7. ~~That Cursor's Playwright feature flags are live.~~ **Resolved: they are not, for this
   account.** `browser_use_enabled` is a backend-set field, and the served surface has no browser
   tool. This was the correct suspicion for the wrong reason — the flags are not merely
   overridable, they are not the mechanism.
8. **Every `strength` and `anchor` value for every composition above.** The entire survey is the
   `reach` column. That is by design — it is the free one — but it is one third of a capability
   row and it decides nothing on its own.

## Vendor documentation — and the one place it contradicts the machine

Added 21 August 2026 after official documentation was fetched. Sources were read live, not
recalled; pages were dated where possible. Codex's documentation has moved —
`developers.openai.com/codex/*` now 308-redirects to `learn.chatgpt.com/docs/*`, the GitHub
`docs/` directory is stubs, pages carry no visible dates, and the corpus is dated instead by
`https://learn.chatgpt.com/docs/whats-new` (latest heading *"August 17–21, 2026"*) against
release `rust-v0.149.0`, 20 Aug 2026.

### The documented negative that settles a question the machine could not

`https://learn.chatgpt.com/docs/browser`, verbatim:

> "Browser isn't available in Codex CLI or the Codex IDE extension."
> "Browser is available in ChatGPT on the web and in the ChatGPT desktop app."

`[cited]` **Codex CLI has no native browser tool, and the vendor says so outright.** Corroborated
by a `[measured]` negative here: none of the 126 documented CLI flags and commands contains
`--browser` or `codex browser`, and the only "browser" strings in the CLI reference are OAuth
login and the plugin picker. Codex reaches a browser only through the same two MCP servers
everyone else uses — both officially named on `https://learn.chatgpt.com/docs/extend/mcp`
(*"Playwright: Control and inspect a browser using Playwright"*; *"Chrome Developer Tools: Control
and inspect Chrome"*). `[cited]`

This is worth dwelling on, because it is the shape of finding this survey exists to produce.
**A free local probe could establish that Codex has browser MCP servers registered. It could not
establish that Codex has no browser of its own** — an absence is much harder to measure than a
presence, and this is exactly the case where a citation earns its tag.

### On the "can it drive a real browser from its CLI" question

| Harness | Native CLI browser control | Source |
|---|---|---|
| **Claude Code** | **Yes** — `claude --chrome`, via the Claude in Chrome extension, documented as available from the CLI | `[cited]` |
| Codex | **No**, explicitly denied | `[cited]`, quoted above |
| Cursor | **No** — measured directly: no browser tool served on either model probed. No official page states the CLI position either way, so the *documentation* status stays `[asserted]`; the *capability* status is now `[measured]` absent. | `[measured]` |
| Antigravity | gated behind an explicit `/browser` command, and it has no CLI anyway | `[cited]` for the gate, `[measured]` for the missing CLI |
| Grok, opencode | none found | `[asserted]` |

**The instruction's headline example does not survive contact with either evidence class.** Joe's
sentence names Cursor as the browser and visual-analysis specialist. On this machine Cursor has
zero MCP servers and its browser capability is `unprobed` `[measured]`; and the one harness with
documented native CLI browser control is Claude Code `[cited]`. I could not obtain an official
Cursor page stating whether the CLI has the Browser feature, so **"Cursor's Browser is IDE-only"
is recorded here as `[asserted]`, not `[cited]`** — the distinction is kept because the whole
point of this file is that it is kept.

### Codex has genuinely non-coding capability built into the CLI

Which is the instruction's thesis, confirmed for a different harness than the one it named.

- **Image input, natively.** `https://learn.chatgpt.com/docs/image-inputs?surface=cli` documents
  `--image, -i` — *"Attach one or more image files to the initial prompt"* — with worked examples
  including `codex --image before.png,after.png "Compare these states and list the regressions"`.
  `[cited]` That is visual analysis of rendered output, in the CLI, in the harness nobody calls a
  visual tool.
- **Image generation, natively.** `https://learn.chatgpt.com/docs/image-generation?surface=cli`:
  *"Include `$imagegen` in your prompt to invoke the image generation skill explicitly… Built-in
  image generation uses `gpt-image-2`."* `[cited]`
- **Figma is a documented use case, not just an MCP entry** —
  `https://learn.chatgpt.com/use-cases/figma-designs-to-code`, plus an official plugin at
  `github.com/openai/plugins/tree/main/plugins/figma`. `[cited]`
- **Codex can itself be an MCP server** — `https://learn.chatgpt.com/docs/mcp-server`:
  `codex mcp-server`, exposing `codex` and `codex-reply`. `[cited]` A harness that is also a tool
  is a composition ADR-0027's tuple does not currently express, and it is worth noting before
  something depends on it. Note `codex mcp` (manage servers) and `codex mcp-server` (be one) are
  different commands.

### And the vendor argues against the instruction's thesis for its own product

`https://learn.chatgpt.com/docs/get-started-with-work`, verbatim: *"If you have used Codex for
non-coding work, you can stay in Codex or use ChatGPT Work instead."* And
`https://learn.chatgpt.com/docs/artifacts-viewer?surface=cli`: *"Codex CLI can create and edit
files in the working directory, but it doesn't include a visual file preview or annotation
interface."* Scheduled tasks are explicitly absent from the CLI
(`https://learn.chatgpt.com/docs/automations?surface=cli`: *"Codex CLI doesn't provide the
Scheduled management interface"*). `[cited]`

**OpenAI is steering non-coding work away from the Codex CLI.** That is evidence against routing
non-coding tasks there — weak evidence, because a vendor's product-positioning preference is not a
capability measurement, but it is honest to record that the label and the vendor both point the
same way here and the machine points the other way.

### ⚠ Unresolved conflict: Codex computer-use

**This is the survey's most important row and it has no answer.**

| Source | Says | Tag |
|---|---|---|
| This machine | `computer-use@openai-bundled` v`26.814.41957` **installed and enabled** in the Codex CLI's own runtime registry, with a bundled `docs/api.md` documenting `target: "windows"` and `get_window_state({include_screenshot})` | `[measured]` |
| `https://learn.chatgpt.com/docs/computer-use` | Computer Use is gated to the **ChatGPT desktop app** on macOS/Windows with ChatGPT Work and Codex — **no CLI surface** | `[cited]` |

The two disagree. Candidate explanations — bundled but not CLI-reachable; shipped ahead of the
docs; gated server-side — are all `[asserted]` and none was confirmed. **Recorded as unresolved.**

This is ADR-0054's argument reduced to a single table. The label said "coding harness". The
vendor's documentation said "not here". The machine said "installed and enabled". All three are
cheap, none is a measurement of what the thing *does*, and **only a bounded probe settles it.**
Under ADR-0054 §4 the correct status is `unprobed`, and `unprobed` routes to the default
generalist as a probe rather than to whichever source is most quotable.

### On the ratio of `[cited]` to `[measured]` in this file

Deliberately low, and it should stay low. The `reach` column is **cheap to measure and expensive
to cite**: `--help`, a config file and `mcp list` gave verifiable, dated, machine-specific answers
in minutes, whereas a vendor page gives a product-wide claim that may not be true of this install
— as the computer-use row demonstrates. **Where a capability can be measured locally for nothing,
citing it is a downgrade.**

Citations earn their tag in exactly the two places used above: establishing an **absence** the
machine cannot prove, and reasoning about a surface that is **not installed here**. Both need a
URL and a fetch date, per `../../CONTRIBUTING.md` and the citing-sources skill.

### Coverage gaps in the documentation sweep

- **xAI Grok Build:** existence only. Effectively unsurveyed from official sources.
- **opencode:** identity and MCP support only.
- **Claude Code image/vision:** **no official source found** for a dedicated images or vision
  documentation page.
- **Cursor CLI browser availability:** no official source found either way, as noted above.
- One staleness warning worth carrying: the curated `playwright-interactive` skill instructs
  setting `[features] js_repl = true`, but that key is now ignored in `codex-rs` (there is a test
  named `from_sources_ignores_removed_js_repl_feature_keys`); the functionality moved into **code
  mode**, documented as *"under development and off by default"*. `openai/skills` also carries a
  deprecation banner pointing at `github.com/openai/plugins`, which contains no browser plugin.
  `[cited]` **The CLI's best-documented running-app QA path is partly stale**, which is its own
  argument for probing rather than reading.

## Housekeeping noticed in passing, not acted on

- Codex's `config.toml` has accumulated roughly 300 `[projects.…] trust_level` entries, nearly all
  pointing at temporary experiment directories from EXP-05 and EXP-07. Trust persists per path.
  Worth pruning; not this ADR's business.
- Three harnesses now read the same Claude plugin marketplaces and Codex runs Claude-format hooks,
  so plugin and skill portability across harnesses is already real on this machine. That is an
  opportunity and a supply-chain surface at the same time, and neither has been assessed.

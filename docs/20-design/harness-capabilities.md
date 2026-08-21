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
2. **The only harness here that can drive the operating system itself is Codex** — the most
   narrowly "coding"-labelled of the four — via a bundled, enabled computer-use runtime with a
   documented Windows window API including screenshot capture. [measured]
3. **Cursor, the harness named in the instruction as the browser and visual-analysis specialist,
   has zero MCP servers configured on either side of the WSL boundary.** [measured] Its bundle
   carries an internal `browser_use` tool and Playwright feature flags, but nothing has been
   probed, nothing is attached, and no run has been observed. Its browser capability is
   `unprobed`, which under ADR-0054 §4 means it may not be routed to on that basis.

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

- **Browser automation and page observation** — supplied by an MCP server (Playwright,
  chrome-devtools), not by the harness. Any harness that speaks MCP inherits it; any harness
  without one lacks it regardless of what its marketing says. The one exception measured here is
  Cursor's internal `browser_use` tool, which is harness-native and unprobed.
- **Operating-system control** — supplied by a bundled runtime, not MCP. Only Codex has one here.
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
| Codex | `playwright` and `chrome-devtools` both registered as stdio MCP servers in `~/.codex/config.toml` | `probed` | `[measured]` |
| Antigravity IDE | `chrome-devtools-mcp` registered in `~/.gemini/config/mcp_config.json`; server dirs materialised, so it has been launched | `probed`, but unreachable — no CLI | `[measured]` |
| **Cursor** | **No MCP servers configured at all** — `mcp.json` absent in both `/home/jpbpr/.cursor/` and `C:\Users\jpbpr\.cursor\`. The bundle contains a native `browser_use` entry in the tool protobuf alongside `bash` and `shell`, plus `PLAYWRIGHT_BROWSERS_PATH` / `PUPPETEER_CACHE_DIR` wiring and default flags `playwright_autorun`, `playwright_mcp_provider`, `sand_computer_use_playwright`. | **`unprobed`** | `[measured]` that the strings exist; `[asserted]` that the capability works |
| Grok | **No MCP servers configured.** No browser flags. | `unprobed`, likely absent | `[measured]` |

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

**OpenDesign** was named in the instruction. No OpenDesign integration, plugin, MCP server or
binary was found anywhere on this machine. `[measured]` negative.

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

1. **That Cursor can drive a browser at all from the CLI.** The strings exist; nothing has been
   run. This is the instruction's headline example and it is the least verified thing in the
   survey.
2. **That Cursor's visual analysis is good**, as distinct from present. No measurement, and note
   that "good at visual analysis" as an *acceptance signal* is refused doctrine here regardless of
   how good it is.
3. **That any harness performs autonomous QA or user simulation usefully.** Not probed, and the
   repository's existing position is that the useful part is the input sequence and the implicit
   oracle, not the simulation.
4. **That any harness drafts a good document.** No oracle exists, so this is not merely unmeasured
   but currently unmeasurable — ADR-0054 §2 routes it supervised and labelled `unverified`.
5. **That the Figma servers do useful design work** rather than merely connecting. Connected is a
   transport fact.
6. **That Codex's computer-use runtime works on this machine.** It is installed and enabled;
   `enabled` is a configuration fact, not a behavioural one.
7. **That Cursor's Playwright feature flags are live.** They are client-side defaults and the
   vendor's server can override them.
8. **Every `strength` and `anchor` value for every composition above.** The entire survey is the
   `reach` column. That is by design — it is the free one — but it is one third of a capability
   row and it decides nothing on its own.

## Housekeeping noticed in passing, not acted on

- Codex's `config.toml` has accumulated roughly 300 `[projects.…] trust_level` entries, nearly all
  pointing at temporary experiment directories from EXP-05 and EXP-07. Trust persists per path.
  Worth pruning; not this ADR's business.
- Three harnesses now read the same Claude plugin marketplaces and Codex runs Claude-format hooks,
  so plugin and skill portability across harnesses is already real on this machine. That is an
  opportunity and a supply-chain surface at the same time, and neither has been assessed.

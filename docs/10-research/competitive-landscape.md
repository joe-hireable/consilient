# Competitive landscape — harnesses and meta-harnesses

Living document. Add entries as they're found. All `[cited]` unless marked.

---

## HKUDS/OpenHarness (+ ohmo)

`https://github.com/HKUDS/OpenHarness` — MIT, Python 94%, 14.8k stars, 2.4k forks,
429 commits, v0.1.9 (7 May 2026). From HKUDS (HKU Data Science lab).

**What it is:** a full agent *harness*, not a meta-harness. Own agent loop, 43 tools,
skills system (`SKILL.md`, compatible with anthropics/skills), claude-code plugin
compatibility, PreToolUse/PostToolUse hooks, multi-level permission modes
(Default / Auto / Plan), MCP client, persistent memory, subagent spawning and team
coordination, worktree tool, cron/scheduled execution, React+Ink TUI.

Plus **ohmo**, a personal-agent layer reachable from Feishu / Slack / Telegram / Discord.

### Why this matters — three separate consequences

**1. It confirms ADR-0001 rather than threatening it.**
Another well-starred, MIT, actively-developed entrant at the harness layer, alongside
DeepSeek Harness. The layer is crowded; the meta-harness layer still is not. Building a
harness would now mean competing with at least two free, lab-backed implementations.

**2. Two of the project's stated requirements are already built, MIT-licensed, by someone
else.**

- *Credential-free operation.* ohmo "runs on your existing Claude Code subscription or
  Codex subscription — no extra API key needed", by bridging `~/.claude/.credentials.json`
  and `~/.codex/auth.json`. This is substantially the "simplified version so developers
  avoid configuring billions of their own credentials" idea from the commercial sketch.
- *Access wherever the user is.* Feishu / Slack / Telegram / Discord gateways, shipped.

Neither needs building. If either is wanted, use or fork this. That is a saving, not a loss.

**3. It is a plausible host for the β-meter, and that deserves serious consideration.**

Unlike DeepSeek Harness (rejected in `../decisions/0001-*` partly because it orchestrates
models rather than agents), OpenHarness has exactly the integration surface a β-meter
needs: PreToolUse/PostToolUse hooks to observe verifier invocations and outcomes, a plugin
system, a tool registry, and an existing user base.

Shipping the β-meter as an OpenHarness plugin would start at a nonzero audience instead of
zero. Against that: it is v0.1.x with an unstable surface, and it binds the project's fate
to another team's roadmap. **This should be argued explicitly in the brainstorm, not
decided by default.**

### What it does not have

No notion of verifier reliability. No measurement of whether automated checks can be
trusted. No routing decision derived from that. The β thesis is untouched.

### Cautions

- `[asserted]` A 2.4k:14.8k fork-to-star ratio (~16%) is unusually high, and HKUDS is a lab
  with a track record of high-star releases. Star count may reflect institutional reach more
  than production usage. **Do not treat 14.8k stars as 14.8k users** — check issue activity,
  dependent repos and release cadence before drawing conclusions.
- Last release 7 May 2026; this note written 19 August 2026. Cadence may have slowed.
- Test suite is 114 unit/integration plus small E2E suites for a system of this surface
  area. Modest.

### Name collision

**"OpenHarness" is taken, at 14.8k stars.** Anything in that neighbourhood — OpenHarness,
Open Harness, OH, `oh` (their CLI binary) — is unusable. Feeds Q18.

---

## Others tracked

| Project | Layer | Licence | Note |
|---|---|---|---|
| DeepSeek Harness (`dsh`) | Harness | MIT | Cordis plugin kernel; append-only session log; imports Claude Code sessions |
| Meta-Harness (Stanford/MIT) | Harness optimiser | — | COLM 2026; automates harness search; **do not compete** |
| Omnigent (Databricks) | Meta-harness | Apache 2.0 | Jun 2026; category is real but unclaimed |
| Vercel AI SDK v7 `HarnessAgent` | Meta-harness | — | Programmatic multi-harness interface |
| SemaClaw (Midea AIRC) | Harness | Open source | DAG two-phase orchestration, PermissionBridge, agentic wiki |
| Claude Code / Codex / opencode / Antigravity CLI | Agents | mixed | The orchestratees |

---

## Standing instruction

Before any build decision, check this file and search again. The rate of new entrants in
2026 is high enough that a six-week-old landscape assessment is unreliable, and "someone
already built this, MIT-licensed" has now been the correct answer three times running
(model library → LM Studio/LLM Checker; harness → DeepSeek/OpenHarness; harness
optimisation → Meta-Harness).

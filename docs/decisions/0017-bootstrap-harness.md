# 0017. The bootstrap harness — Claude Code configured as a working prototype of Consilience

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none.

## Context

`0015` Stage 1 is "Claude Code builds Consilience". That understates it. The Claude Code
configuration used to build Consilience should be **a manual implementation of what
Consilience will automate** — same skills, same memory layers, same evidence discipline,
performed by hand.

Two consequences follow, and the second is the point of this ADR.

## Decision

### 1. Adopt, don't build. Three layers, all existing tools.

Per Joe's constraint — only if best, no custom unless there is a clear gap.

| Layer | Tool | Licence | What it holds |
|---|---|---|---|
| 0 · project map | `AGENTS.md` + `CONSILIENCE.md` | ours | stack, rules, the definition |
| 1 · episodic — *what was decided and why* | **MemPalace** | MIT | conversation history, decisions, temporal knowledge graph with validity windows |
| 1.5 · structural — *how the code is built* | **Graphify** | open source | tree-sitter AST graph, local, 0 tokens in default mode |
| 2 · ground truth | the repository | — | the source files |

**These are three different classes of facts**, which is why the stack is coherent under
`CONSILIENCE.md` rather than merely fashionable: structural facts about code, episodic facts
about decisions, and the sources themselves. A merge across them is consilient. A second
memory tool holding the *same* class would be echo.

### 2. The bootstrap harness is the specification

**Every manual step performed in Claude Code that Consilience should automate is a
requirement.** Keep `docs/00-context/friction-log.md` — one line per manual step, dated.
That log is the v0 backlog, derived from use rather than imagination.

This inverts the usual order. Rather than specifying Consilience and then checking whether
it helps, we use the manual version daily and let the pain define the spec.

## Evidence

- `[cited]` **Graphify**: ~61,000 GitHub stars. Tree-sitter AST pass is fully local and
  costs **0 tokens** in default mode; `--deep` semantic extraction uses an LLM API and can
  be pointed at local Ollama. Reported up to 71× token reduction per query. Ships as a
  slash command across 20+ agents *and* an MCP server, and
  `graphify install --platform claude` writes `~/.claude/skills/graphify/SKILL.md` —
  **already `SKILL.md`, so it satisfies `0014` natively.**
- `[measured]` Joe already has `graphify-out/` in `jobboard-v2`. Partly adopted already.
- `[cited]` **MemPalace**: MIT, Python, ChromaDB + SQLite. Temporal entity-relationship
  graph with **validity windows** — add, query, invalidate, timeline — which solves the
  stale-`CLAUDE.md` problem directly. 44 MCP tools. Auto-save hooks for Claude Code, Codex
  and Cursor. `mempalace mine ~/.claude/projects/ --mode convos` **mines existing Claude
  Code session history**, so there is a backlog to import, not just a forward record.
- `[cited]` The layering above is not ours — it is the consensus structure from practitioner
  write-ups, whose sharpest formulation is: *the graph points at where to look; the sources
  confirm what is actually there.*

## Evidence against

- `[cited]` **MemPalace's launch benchmark numbers were reported as inflated** by at least
  one analysis. The repository now claims reproducible benchmarks with committed result
  files. **Verify before relying on any recall figure** — do not cite their numbers in our
  own materials without re-running them.
- `[cited]` **Graphiti** scores 63.8% vs mem0's 49% on the temporal subset of LongMemEval
  and uses genuine bi-temporal reasoning. If temporal correctness matters more than the
  conversation-mining and hooks, Graphiti may be the better layer-1 choice. **Not evaluated
  here.** MemPalace is chosen for its Claude Code integration, not because it won a
  benchmark we ran.
- **Obsidian is not open source.** It is proprietary freeware. Its licence terms for
  commercial use must be checked before it becomes load-bearing in a project with the
  commercial intent in `0004`. The vault is plain markdown, so the lock-in is low — but this
  is a genuine open question, not a footnote.
- Graphify's `--deep` mode routes docs and design notes through a model API. For a project
  handling client code that is a data-egress decision, not a convenience one.
- Three tools is three maintenance surfaces, three failure modes and three things to
  upgrade, for a solo maintainer.

## The rule that makes this consilient rather than just convenient

**A memory layer is a claim about the world, and it can be stale.**

A graph built last week may not describe the code today. A decision recorded in April may
have been superseded in June. If an agent trusts the memory layer over the source, the
memory has become an unverified oracle — which is exactly the failure this project exists
to detect, appearing inside our own toolchain.

So:
- **Memory points; sources confirm.** No agent may act on a graph or memory claim about
  code state without reading the file.
- Graphify updates belong in **git hooks, not agent hooks** — the graph must track the
  repository, not the conversation.
- Staleness is measurable. Graph age and memory-claim age are recorded, and a claim older
  than its subject's last modification is flagged. **This is β applied to the memory layer**
  and it is the natural place to prototype the β-meter before the harness exists.

## Consequences

**Positive.** Nothing custom is built. The friction log produces a spec grounded in use.
Skills, MCP and memory config all migrate to Consilience under `0014`/`0016` unchanged.

**Negative.** Three third-party dependencies in the development loop, at least one with
questionable published benchmarks and one with an unresolved licence question.

**Neutral but load-bearing.** Consilience must eventually consume these as *layers*, not
reimplement them. That is a constraint on its architecture and it is the right one.

## Enforcement

- Check: `graphify update` runs from a git hook, never an agent hook.
- Check: memory and graph artefacts are gitignored; only the config is committed, so the
  setup is reproducible without shipping a stale graph.
- Check: **friction-log entries are dated and never deleted** — the removal of a line means
  Consilience automated it, and that should be a commit reference, not a silent edit.

## What would overturn this

- Graphiti's temporal advantage proves to matter for our use, replacing MemPalace at layer 1.
- The Obsidian licence turns out to be incompatible with the commercial intent in `0004`.
- The friction log stays short for a month, which would suggest either that Claude Code is
  already sufficient — a serious finding for `0004` — or that the log is not being kept
  honestly.

## Publication candidate?

No — but the friction log itself may become the most useful artefact in the repository for
anyone else attempting this, and is worth publishing as-is.

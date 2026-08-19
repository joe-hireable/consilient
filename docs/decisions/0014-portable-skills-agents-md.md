# 0014. Adopt SKILL.md and AGENTS.md as the portable instruction format; `.agents/` is the source of truth

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — a format choice, no free parameter.

## Context

Joe builds with Claude Code today and intends to replace his own workflows with Consilience
once it is published, across this project and his others. Skills and rules written now must
survive that migration without a rewrite.

The naive approach is to invent a Consilience skill format and write an importer later.
That is backwards.

## Decision

**Do not invent a format. Adopt the two that already exist and are already portable.**

1. **`SKILL.md`** — the Agent Skills convention: a directory containing a markdown file with
   YAML frontmatter (`name`, `description`) plus optional scripts and resources.
2. **`AGENTS.md`** — repository-level agent rules, vendor-neutral.

**Directory layout, source of truth first:**

```
.agents/skills/<skill>/SKILL.md     ← source of truth, vendor-neutral, committed
.claude/skills/                     ← mirror or symlink, for Claude Code
AGENTS.md                           ← the rules
CLAUDE.md                           ← @-references AGENTS.md, adds Claude-specific notes only
```

**Consilience must read `.agents/skills/` and `AGENTS.md` natively.** That is now a
requirement on the harness, not an integration to be written later.

## Evidence

- `[cited]` OpenHarness (14.8k stars, MIT) states compatibility with `anthropics/skills` and
  loads from `~/.claude/skills/`, `~/.agents/skills/`, `~/.openharness/skills/` and the
  project-level equivalents. It is also compatible with claude-code plugins, tested against
  12 official ones. **`.agents/` is already the de facto vendor-neutral location.**
- `[cited]` DeepSeek Harness treats skills as a plugin class; SemaClaw ships an agentic-wiki
  skill; the `SKILL.md` convention appears across the 2026 harness literature
  (SkillsBench, AgentSkillOS, SkillOpt, SIGIL).
- `[measured]` Joe's own `jobboard-v2` already uses the portable pattern: `CLAUDE.md`
  `@`-references `AGENTS.md`, which holds the substance. That structure survives a tool
  change with a one-line edit.
- `[cited]` ACE (ICLR 2026) and SkillOpt (arXiv:2605.23904) both treat the skill document as
  optimisable external state of a frozen model. Adopting the standard format keeps those
  techniques available rather than requiring a port.

## The rule that matters most: skills are procedure, checks are invariants

`AGENTS.md` principle 3 says a chokepoint without an enforcement rule is not a chokepoint.
A skill is a *prompt-shaped instruction* — exactly the fragile layer the Engineering Ratchet
exists to replace.

**Therefore:**

- **Procedure → skill.** "How we write an ADR", "how to run EXP-01", "our commit style".
  Guidance the agent benefits from and where deviation is recoverable.
- **Invariant → check.** "No per-check β reaches the routing path", "no unsigned commits",
  "the DB is a projection of the log". Rules where deviation is a defect.

**Never encode an invariant as a skill.** If a skill's instruction genuinely must hold, it
belongs in CI with a test, and the skill may reference it. A skill that says "always do X"
where X is load-bearing is a prompt pretending to be an enforcement mechanism — the exact
failure that hollowed out the `llm()` boundary in `jobboard-v2` (five access paths, no lint
rule).

## Evidence against

- `SKILL.md` is a young convention. It could fragment, at which point the mirror/symlink
  layer absorbs the change — cheaper than a format migration, but not free.
- Mirroring `.agents/` into `.claude/` is duplication, and duplication drifts. Symlinks are
  cleaner but behave badly on Windows without developer mode, which is Joe's environment.
- Adopting an Anthropic-originated convention in a project positioned as vendor-neutral is a
  mild inconsistency. Mitigated by `.agents/` being the source of truth and `.claude/` the
  derived copy — the dependency points the right way.

## Consequences

**Positive.** Skills written today work in Claude Code now, in Consilience later, and in
OpenHarness and DeepSeek Harness without modification. Zero migration cost.

**Negative.** A sync step between `.agents/` and `.claude/` that must not drift.

**Neutral but load-bearing.** Constrains Consilience's design: it must consume an external
standard rather than define its own.

## Enforcement

- Check: `.claude/skills/` is byte-identical to `.agents/skills/`, or a symlink. CI test,
  fails on drift.
- Check: every `SKILL.md` has valid frontmatter with `name` and `description`.
- Check: **a skill containing an imperative that maps to an existing CI check is a lint
  error.** Prevents invariants leaking back into the prompt layer. Same commit (I1).

## What would overturn this

- The `SKILL.md` convention fragments badly enough that no single format works across the
  target harnesses.
- Consilience's needs diverge so far that consuming the standard becomes contortion — in
  which case extend it upstream rather than fork it.

## Publication candidate?

No.

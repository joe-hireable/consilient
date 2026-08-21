# Skills — portable across Claude Code, Consilient, and other harnesses

**This directory is the source of truth.** `.claude/skills/` is a mirror. See
`../../docs/decisions/0014-portable-skills-agents-md.md`.

## Why here and not `.claude/`

Skills written today must survive the migration to Consilient (`0015`) without a rewrite.
The `SKILL.md` convention is already read by Claude Code, OpenHarness and DeepSeek Harness,
and `.agents/` is the emerging vendor-neutral location. So portability comes from **adopting
a standard, not inventing one** — and Consilient is obliged to read this directory
natively.

## Format

```
.agents/skills/<skill-name>/
  SKILL.md          required — YAML frontmatter (name, description) + markdown body
  scripts/          optional
  references/       optional
```

`description` is the trigger. Write it for a model deciding *whether to load this*, not for
a human browsing a list. State when to use it and what phrases should fire it.

## The one rule that matters

**Skills are procedure. Checks are invariants.**

| Kind | Goes in | Example |
|---|---|---|
| Guidance where deviation is recoverable | a skill | how to structure an ADR; commit style; how to run an experiment |
| A rule where deviation is a defect | **a CI check** | no unsigned commits; no per-check β in the routing path; DB is a projection of the log |

**Never encode an invariant as a skill.** A skill saying "always do X" where X is
load-bearing is a prompt pretending to be an enforcement mechanism. That is precisely how
`jobboard-v2`'s `llm()` boundary hollowed out into five access paths — the rule was written
down, and nothing enforced it.

A skill may *reference* a check. It may not *be* one.

## Keeping the mirror honest

`.claude/skills/` must be byte-identical to this directory, or a symlink. Symlinks are
cleaner but need developer mode on Windows; if that is off, copy and let CI catch drift.

## Skills worth writing next

**Before writing any of these: check whether one already exists.** The ecosystem passed
~351,000 skills by March 2026. `npx skills find <topic>` first — see
`../../docs/decisions/0016-skill-distribution-mcp-plugins.md`. "Someone already built this"
has been the right answer three times on this project already.

Ordered by how often they would fire:

1. `writing-adrs` — **done**, and doubles as the worked example of this format
2. `running-experiments` — the register discipline: precondition, measurement, **stopping
   rule**, apply it honestly even when it kills a decision you like
3. `evidence-tagging` — `[measured]` / `[simulated]` / `[cited]` / `[algebra]` /
   `[asserted]`, and never reporting a simulated figure as a fact
4. `checking-prior-art` — "someone already built this, MIT-licensed" has been the right
   answer three times running; search before designing
5. `exogenous-signal-check` — before proposing any multi-agent structure, name the different
   class of facts (`0010`), or cut it
6. `beta-verdict` — how the merge-time verdict prompt works and why the label matters

Skills 2–6 are unwritten. Write them as they are needed, not speculatively — an unused skill
is context cost with no benefit.

## Getting skills in and out

**In:** `npx skills add owner/repo` (skills.sh — broadest agent coverage). Then **read it in
full, commit it here, and add a `source:` field with a pinned content hash.** Never resolve
from a registry at agent runtime.

**A vendored skill may never trigger a package install.** A skills registry is a strict
superset of a package-manager client — installing one skill can run install commands across
npm, pip, cargo, brew and apt on behalf of a manifest nobody read. Declaring dependencies in
our own manifests keeps the lockfile and CI in the loop.

This is not generic caution. A project whose thesis is *measure whether your checks can be
trusted before relying on them* cannot install unvetted instructions into its own agents.

**Out:** Consilient's own skills ship bundled inside its npm package, version-locked to the
tool that reads them — because they are tool-coupled. A `beta-verdict` skill must match the
verdict schema; git-based distribution lets that drift.

## Where these run

- **Now:** Claude Code, via the `.claude/skills/` mirror.
- **After Gate A/B (`0015`):** Consilient, reading this directory directly.
- **Elsewhere:** OpenHarness and DeepSeek Harness read `SKILL.md` today, unmodified.

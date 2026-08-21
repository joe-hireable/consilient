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

`.claude/skills/` and `.claude/agents/` must be byte-identical to their sources, or symlinks.
Both are symlinks, and `skills-mirror.yml` asserts both still resolve.

**A resolving symlink in the index is not a resolving symlink in your working tree.** A clone
made with `core.symlinks=false` -- Git for Windows' default without developer mode -- checks
both out as ordinary 17-byte text files containing the target path, and **Claude Code then
loads no project skill and no project agent at all, silently.** Measured in this repository on
21 August 2026: the index held mode 120000, CI passed on Linux runners, and the Windows working
tree had a plain file. [measured]

Repair, per clone, and it is a local config change that commits nothing:

```
git config core.symlinks true
rm -rf .claude/skills .claude/agents && git checkout -- .claude/skills .claude/agents
ls -la .claude/          # both must show as l--------- arrows, not directories or files
```

`ln -s` from Git Bash is not a substitute: without `MSYS=winsymlinks:nativestrict` it produces
a copy or a junction, git reports the path as deleted, and committing that removes the mirror
for everyone.

## What is here

**Before writing a new one: check whether one already exists.** The ecosystem passed ~351,000
skills by March 2026 `[SNIP]` — `npx skills find <topic>` first, see
`../../docs/decisions/0016-skill-distribution-mcp-plugins.md`. "Someone already built this" has
been the right answer three times on this project.

| Skill | The one behaviour it changes |
|---|---|
| `writing-adrs` | An ADR without an *Evidence against* section does not get written |
| `citing-sources` | A `[SNIP]` or `[2ND]` source never reaches a published claim |
| `measuring-beta` | β is not quoted below 30 rejections, and never from a verifier-conditioned sample |
| `running-experiments` | The number comes from the brief; the stopping rule is written before the run |
| `adversarial-audit` | The auditor is a different family from the author, and is asked about second paths |
| `pre-publication-gate` | "All the checks passed" stops being an argument for publishing |
| `dispatching-workers` | A fan-out that cannot name its different class of facts does not happen |

Written 21 August 2026: the five after `citing-sources`, adapted from proven public collections
rather than invented — see each skill's *Adapted from* section for source and licence.

Deliberately **not** written, and why:

- `evidence-tagging` — `AGENTS.md` is always in context and already states it. A skill that
  restates always-loaded context is cost with no benefit.
- `checking-prior-art` — folded into `adversarial-audit`, where the novelty search already lives.
- `exogenous-signal-check` — folded into `dispatching-workers`, which is where it fires.
- `beta-verdict` — folded into `measuring-beta`.

## Agents

`../agents/` holds subagent definitions, mirrored at `.claude/agents/` by the same symlink
scheme. **Skills are the portable artefact; agent files are Claude Code wiring.** Codex, Cursor
and Grok CLI do not read `.claude/agents/`, so nothing load-bearing may live only there — an
agent file states which skill it follows and adds isolation, tool limits and a report shape.

| Agent | Why it is a separate context rather than an inline skill |
|---|---|
| `consilient-auditor` | Must not see the reasoning that produced the artefact, and must not be able to repair what it finds |
| `consilient-gate` | A clean pass/fail on the working tree, unmixed with the argument for publishing |
| `consilient-worker` | The dispatchee half of the worker contract, so a fan-out returns a reviewable shape |

`consilient-auditor` is the same model family as almost every artefact here, so it is a weaker
instrument than the method wants. It is required to say so in its first paragraph.

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

- **Now:** Claude Code, via the `.claude/skills/` and `.claude/agents/` mirrors.
- **After Gate A/B (`0015`):** Consilient, reading this directory directly.
- **Codex, Cursor, Grok CLI:** they read `AGENTS.md`, not this directory. `.agents/skills/` is a
  Codex/Copilot/Gemini-CLI-side path and is **not** a Claude Code convention -- Claude Code only
  ever reads `.claude/`. [cited] Each skill therefore carries a *Harness support* section stating
  its portable core, and briefs paste that core in where a runtime cannot read the file.
- **Elsewhere:** OpenHarness and DeepSeek Harness read `SKILL.md` today, unmodified.

`AGENTS.md` itself is a genuine cross-harness standard, stewarded by the Agentic AI Foundation
and read natively by Codex, Cursor, Copilot, Gemini CLI and others. [cited] It carries no schema.
That is why the load-bearing rules live there and the procedures live here.

# 0016. Skill distribution: consume via `skills` with a vetting gate; publish via bundled npm

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none.

## Context

`0014` fixed the **format** (`SKILL.md`, `AGENTS.md`, `.agents/` as source of truth). It did
not address **distribution** — how skills get in, and how ours get out. Joe raised
SkillFish, npm-based skills, MCPs and plugins.

The ecosystem is larger and more mature than the earlier research captured. Correcting the
record:

| Tool | What it is | Notes |
|---|---|---|
| **`skills` (skills.sh)** | `npx skills add owner/repo` | Broadest reach: OpenCode, Claude Code, Codex, Cursor "and 73 more". ~75 npm dependents. Vercel Labs publishes here. Very active. |
| **`skills-npm`** (antfu) | Ships skills *inside* npm packages; symlinks them on `prepare` | Solves version mismatch: skills travel with the tool version |
| **`skillpm`** | Skills as proper npm packages — semver, lockfiles, dependencies | Addresses the "every skill is a monolith" problem |
| **`skillfish`** | Multi-agent skill manager, `skillfish bundle` for teams | **AGPL-3.0**; ~279 stars; last push Jun 2026; third-party quality score 51/100 |
| Registries | skills.sh, ClawHub, Tessl, agentskills.io, openagentskill.com | Ecosystem passed ~351,000 skills by March 2026 |

## Decision

Three separate decisions, because these are three different problems.

### 1. Consuming third-party skills → `skills` (skills.sh), never automatically

Use `npx skills add` when we want an external skill. **Broadest agent coverage and the most
adoption**, which matters because a skill installed today must still resolve when Joe's
workflow moves to Consilience (`0015`).

**Every third-party skill is read in full and committed to `.agents/skills/` before use.**
No live registry resolution at agent runtime. See the security section — this is not
optional caution.

Not `skillfish`: AGPL-3.0 (a licence question we do not need next to `0004`), two months
without a push, and a third-party quality score of 51/100. Its multi-agent install is a
convenience we can live without.

### 2. Publishing Consilience's own skills → bundled inside the npm package

Follow the `skills-npm` convention: ship `skills/` inside the `consilience` package.
`npm i consilience` brings the skills, **version-locked to the tool that reads them**.

This is the right shape specifically for us: our skills are *tool-coupled*. A `beta-verdict`
skill that describes the verdict prompt must match the verdict schema, and a
`running-experiments` skill must match the register format. Git-based distribution lets
those drift; package-bundled distribution cannot.

### 3. Tools → MCP. Plugins → the claude-code plugin format.

Both are already the de facto standards across Claude Code, OpenHarness and DeepSeek
Harness. `0014`'s reasoning applies unchanged: adopt, do not invent.

## The security problem, which is not incidental to this project

`[cited]` Nesbitt (Jun 2026), *Skills Registry Threat Models*: a skill can declare
dependencies on npm, pip, cargo, brew, go, apt — often several at once — so **a skills
registry is a strict superset of a package-manager client**. Installing one skill runs
install commands across several package managers on the user's machine, on behalf of a
manifest the user never read. Every threat the package ecosystem spent a decade documenting
applies, and the registries have published none of the mitigations that npm eventually did.

`[cited]` Supporting: Snyk's ToxicSkills catalogue; *Agent Skills in the Wild*; *Towards
Secure Agent Skills*; the OWASP Agentic Skills Top 10. `skillfish`'s own README states it
**does not vet third-party skills**.

**This matters more here than in most projects.** Consilience's entire thesis is that you
should measure whether your checks can be trusted before relying on them. Installing
unvetted third-party instructions into our own agents, unread, would be the same error the
product exists to detect — and it would be visible in the repository.

Concretely:
- Read every third-party skill in full before it enters `.agents/skills/`.
- Commit it. Pin by content, not by registry reference.
- **A skill may never trigger a package install.** Dependencies are declared in our own
  manifests where the lockfile and CI see them.
- Prefer skills from identifiable maintainers with real history over registry ranking.

## Evidence against

- Bundling our skills in the npm package couples them to a release cadence. A skill fix
  needs a package release, which is friction that git-based distribution avoids.
- `skills-npm` is a young convention from one maintainer, however well-regarded. If it does
  not stick, we own a `prepare`-script integration for nothing — recoverable, but real.
- `skillpm`'s dependency model (skills depending on skills) is genuinely better engineering
  than monolithic `SKILL.md` files, and we are not adopting it. If our skill set grows
  enough to have shared parts, revisit.
- The "read every skill in full" rule does not scale past a handful. It is right for a solo
  project and would need replacing with automated scanning at team scale.

## Consequences

**Positive.** Our skills travel with the tool and cannot drift from its schemas. Third-party
skills remain available but pass through a human. No new format, no new registry.

**Negative.** Manual vetting is a real cost and will occasionally mean not using a skill we
would benefit from.

**Neutral but load-bearing.** `.agents/skills/` now contains both authored and vendored
skills. They must be distinguishable — a `source:` field in frontmatter for anything not
written here.

## Enforcement

- Check: no skill in `.agents/skills/` contains a package-install command. Lint rule, fails
  CI. Same commit (I1).
- Check: every skill has either no `source:` (ours) or a `source:` with a pinned
  content hash (vendored). A test asserts vendored skills match their hash.
- Check: `.claude/skills/` mirror parity, per `0014`.

## What would overturn this

- A skills registry publishes credible provenance and vetting — signed skills, reproducible
  content hashes, a documented threat model — at which point live resolution becomes
  defensible and the manual read can be relaxed.
- `skills-npm` stalls and `skillpm` or another convention wins; switch the publish path.

## Publication candidate?

No. But *"we applied our own trust-measurement thesis to our own supply chain"* is a good
short post for the community strategy in `0004`, and it is honest rather than promotional.

# A third of the published history is authored by a test fixture

**Date:** 20 August 2026
**Status:** `[measured]` for every count and every config value below; `[asserted]` for the
implication for P2 and for what should be done about the published history.

---

## What was found

The primary repository's `.git/config` contained two values that no one put there deliberately:

```
[core]
	worktree = /mnt/c/Users/jpbpr/Repositories/consilience/.claude/worktrees/fleet-papers
[user]
	email = exp07@local
	name = EXP-07
```

`EXP-07 <exp07@local>` is the identity EXP-07's runner stamps on the throwaway repositories it
builds, so its synthetic commits are distinguishable from real ones. Its own runner scopes that
correctly — `git config` with `cwd` set to a fresh temporary repository. The primary repository
acquired the same identity by another route, and **worktrees share the primary `.git/config`**.

**Measured on the published `main` at `d920d29`:** 156 commits, of which **51 are authored and
committed by `EXP-07 <exp07@local>`** and 105 by `Joe Brown <joe@gethireable.com>`. Counting both
the author and committer fields, 102 of 312 identity stamps are the fixture. [measured]

The split is not chronological, it is topological: work done in a **clone** carries Joe's identity
because clones have their own config; work done in a **worktree** carries the fixture's. Two of the
contaminated commits were written on the day this was found.

The `core.worktree` line is a separate fault with the same origin — a WSL-absolute path written into
a config that Windows-side git also reads. It made **every** git command against the primary
repository fail with `fatal: Invalid path '/mnt'`. That had presumably been true for some time and
was never noticed, because all work happens in worktrees and clones, which have their own configs.
A repository can be entirely unusable in the one place nobody looks. [measured]

## Why it matters here more than it would elsewhere

1. **It is V0-18 inverted.** V0-18 stops an agent claiming a human's decision. The record did the
   opposite without anyone noticing: it attributed a human's work to a fixture. Both are failures
   of the same property — *the record says who did this, and it is right* — and only one of them
   had a check.
2. **Publications must be attributable.** Joe's standing requirement is that anything published is
   attributable to a human with AI disclosure. The git history on a public remote is part of that
   record, and a third of it names a test fixture.
3. **DCO.** ADR-0023 records DCO as the one implemented check of its five. A sign-off from
   `exp07@local` is not a sign-off. No commit body contains that address, so no false sign-off was
   made — the trailer was simply absent from those commits. [measured]

## The check, and its honest limits

`test_no_new_commit_may_be_authored_by_a_fixture_identity` counts author and committer emails
ending `@local` across `HEAD` and fails above the measured legacy baseline of **102**. It follows
the ratchet already used for `append()` bypass: the constant is the measured past, it may only go
down, and lowering it is the only permitted edit.

**What it does not do.** It matches a naming convention (`@local`), not authenticity. A fixture
identity that used a plausible address would pass, and so would a deliberate impersonation. Like
V0-18 and V0-28, it catches structural confusion — which is what actually happened — and not
forgery. Anyone wanting authenticated authorship needs commit signing, which is not installed.

## What was NOT done, and why

**The published history was not rewritten.** Correcting 51 commits means rewriting `main` and
force-pushing a public branch. That is outward-facing and destructive to anything already cloned,
and it is the principal's call, not an agent's. The options, for Joe:

| option | cost |
|---|---|
| Leave it, and record the fact | Free. The history stays honest about its own defect, which is this repository's stated preference elsewhere. |
| `git filter-repo --mailmap` and force-push | Rewrites every SHA on `main`. Breaks existing clones and every commit hash quoted in the papers, ADRs and findings — including the anchors P1, P2 and P3 depend on. |
| Add `.mailmap` | Cheap and non-destructive. `git log`, `git shortlog` and GitHub's contributor view resolve the fixture identity to Joe; the underlying commit objects are untouched, so no quoted SHA moves. |

**Recommendation: `.mailmap`.** It fixes the attribution that is actually read without invalidating
a single citation in the publication set. The commits' raw author fields stay wrong, and a
`.mailmap` that silently rewrites them would be its own kind of dishonesty — so the file, if added,
should carry this document's URL in a comment.

## Reversal and falsifier

**Reversal:** the config repair is one line each, backed up before editing; `git revert` removes the
test.
**Falsifier:** if commits legitimately need a non-human author — a bot, a scheduled job, a
reproducibility fixture that must be distinguishable in the record — then a flat denylist on
`@local` is the wrong shape, and the check should test for a *declared and registered* non-human
identity instead of refusing all of them.

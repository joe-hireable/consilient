# Publication blocked — two leaks the automated gates cannot see

**Date:** 21 August 2026 (00:50)
**Status:** `[measured]` for every count and file below, each verified independently after the audit
reported it; `[asserted]` for the remediation.
**Decision:** **DO NOT PUBLISH** until both blockers are cleared. Only the principal lifts this.

---

## What was about to happen

Joe asked that changes reach the public repository, because he is inviting external contributors.
All the automated gates passed:

| gate | result |
|---|---|
| `check_private_corpus.py --require-corpora`, 2,854 distinctive paths | **PASS** |
| `check_secrets.py --history --untracked --self-test` | **PASS** |
| 64 mentions of the private corpora in the outgoing diff | all names and aggregate metrics, which `AGENTS.md` permits |

On that basis I was ready to push 182 commits to `joe-hireable/consilient`. An independent
pre-publication audit — a different model family, read-only, briefed to find what a path-matcher and
a regex cannot — returned **DO NOT PUBLISH**.

It was right, and I verified both findings myself before accepting them.

## Blocker 1 — 71 commit identifiers from a private commercial repository

`docs/10-research/experiments/exp43/results-exp43.json` contains **71 forty-character commit
SHAs**. I sampled twenty and resolved each against this repository: [measured]

> **0 of 20 exist here. All twenty are foreign.**

They are commits from `jobboard-v2`, mined by EXP-43's retro-verification run.

`AGENTS.md` is precise about what may cross the line:

> *"Their names and **aggregate measured metrics** may appear in docs; their code, file contents,
> excerpts and detailed file paths may never be committed here or included in anything published
> from here."*

**A list of specific commits is not an aggregate. It is a list of incidents**, and combined with the
per-record failure classes in the same file it reconstructs a timeline of a private commercial
repository's CI history.

**Why every existing gate missed it.** `check_private_corpus.py` matches **file paths**.
`check_secrets.py` matches **credential shapes**. A commit SHA is neither. The rule was written
about paths and content, and identifiers are a third thing nobody had enumerated.

## Blocker 2 — the scrub cleaned the tip and not the history

The audit found this and the repository had already written it down. From
`docs/30-source-material/prior-repo-assets.md`:

> *"Publishing this repository publicly with its history intact would publish [the original text
> from] the initial commit."*

The 20 August scrub cleaned the working tree. It did **not** rewrite history, and the unscrubbed
corpus file remains reachable from the initial commit. **The document naming the risk is itself in
the tree, and I read past it.**

A force-push after publication does not undo publication. Clones, forks, caches and search indexes
are outside anyone's control from the moment the objects land.

## What has been done

1. **`check_foreign_identifiers.py`** — refuses tracked content carrying 40-character commit ids
   that do not resolve in this repository. It never prints an identifier in full: file, count and a
   seven-character prefix, which is enough to find and not enough to republish. Run against the tree
   it reports EXP-43's 71 immediately.
2. **A ratchet test** pinning the total at its measured value, which may only fall. Raising it is
   not the fix; aggregating the identifiers is.
3. **The pre-push hook now refuses the public remote by name**, prints both blockers, and runs the
   identifier check so the reason is on screen rather than in a document nobody opens.

## What has not been done, and is the principal's

- **Blocker 1's remediation.** The identifiers must be aggregated — replaced by counts, rates and
  intervals — or removed. That is an edit to a committed results file, which means EXP-43's findings
  must be re-derived from the aggregated form or explicitly marked as resting on data no longer
  published. Neither is an agent's call.
- **Blocker 2's remediation.** `prior-repo-assets.md` already lists three options at its end. All
  three are history-rewriting or fresh-root operations on a repository with a published initial
  commit. **Irreversible, outward-facing, and reserved to Joe.**
- **Whether to publish at all before both are cleared.** The default is no.

## The lesson, stated plainly because it generalises

**Three automated gates passed and the publication was still unsafe.** They were not broken — each
did exactly what it was written to do. The rule they enforce was written about *paths* and
*credentials*, and the leak was in *identifiers*.

An independent reader of a different family, briefed specifically to find what the gates cannot,
found both in under an hour. **That is the strongest argument this project has produced for its own
thesis**, and it arrived by the thesis nearly failing: the checks said yes to something bad, which
is exactly what β measures, and the human operator was about to accept it.

## Reversal and falsifier

**Reversal:** `rm .git/hooks/pre-push`, and `git revert` this commit and the checker.

**Falsifier:** the foreign-identifier check assumes an unresolvable 40-hex string is a foreign commit
id. It is not always — the same shape covers blob digests, SHA-1 hashes of unrelated content, and
legitimate citations of upstream projects' commits, of which this tree already contains eleven.
**The check as written cannot tell a private-corpus commit from a cited LangGraph release**, so it
over-reports and its ratchet number includes benign entries. The correct next step is a declared
allowlist with a stated reason per entry — the same shape as the credential-shape declaration — and
until that exists this check is a blunt instrument that is right about the case that matters.

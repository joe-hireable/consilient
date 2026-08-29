---
name: pre-publication-gate
description: Use before anything leaves this machine — a push to a public remote, a paper or blog draft, an issue, a gist, a screenshot, a message quoting repository content, or making a repository public. Covers the four leak classes and the one nobody enumerated, why a passing check is not evidence of safety, the history-versus-tip trap, and which decisions are reserved to the principal. Trigger on "publish", "push", "make it public", "share this", "open source it", "send to", "draft a paper", "post", or any suggestion that the checks passed so it is fine to go.
---

# Pre-publication gate

```
A PASSING CHECK IS EVIDENCE ABOUT THE CLASS IT SEARCHES.
IT IS NOT EVIDENCE THAT PUBLICATION IS SAFE.
```

On 21 August 2026 `check_private_corpus.py` (2,854 distinctive paths) passed,
`check_secrets.py` passed, and an independent pre-publication audit still returned
**DO NOT PUBLISH.** [measured] — `docs/00-context/publication-blocked-2026-08-21.md`.

The reason: the rules were written about **paths** and **credentials**, and the leak was in
**identifiers** — 71 forty-character commit hashes from a private commercial repository,
reconstructing a CI-failure timeline. *A list of specific commits is not an aggregate. It is a
list of incidents.* Identifiers were a third thing nobody had enumerated.

**So the first question is not "did the checks pass". It is: what class have I not enumerated?**

## Run all four, and read what they mean

```
python -m pytest tests/ -q
python -m ruff check .
python .github/scripts/check_secrets.py --history --untracked --self-test
python .github/scripts/check_private_corpus.py
python .github/scripts/check_foreign_identifiers.py
python .github/scripts/check_record_numbers.py
```

**`check_foreign_identifiers.py` exits 1 by design.** Fourteen identifiers remain and are
individually accounted for — ten GitHub permalinks to upstream projects, three to EXP-49's
pre-registration, one to EXP-05. The invariant is the **ratchet** —
`test_foreign_commit_identifiers_may_only_decrease` in `tests/test_v0_foreign_identifiers.py`, which
asserts the total may only fall. Do not read the exit code as the verdict, and do not raise the ratchet to make it green.
Verify by artefact, not by exit code — this project has lost time to that three times.

`check_record_numbers.py` also exits 1 today, on three pre-existing register duplicates. Same
rule: read the finding, not the exit code.

## The leak classes, and the enumeration habit

| Class | Caught by | Found the hard way |
|---|---|---|
| Credentials | `check_secrets.py` | — |
| Private file paths | `check_private_corpus.py` | initial commit, unscrubbed |
| Commit identifiers | `check_foreign_identifiers.py` | 21 Aug, after two gates passed |
| Unverified sources | you | `[SNIP]` and `[2ND]` may never be published |
| **The next one** | **nobody yet** | **name it before you push** |

Before publishing, write down one sentence: *the class of content that would embarrass us and
that none of the above searches for.* If you cannot name one, you have not looked.

## History is not the tip

The 20 August scrub cleaned the working tree and never rewrote git history, so the leak
remained reachable from the first commit. `check_secrets.py --history` exists for exactly this.

**A force-push after publication does not undo publication.** Treat anything that has been
public as permanently public.

## The four publication gates

From `docs/publications/README.md`, verbatim headings:

> **G1 — Is it true?** · **G2 — Is it new?** · **G3 — Is it useful to someone who is not us?** ·
> **G4 — Is it honest about its limits?**

G1 needs reproduction from seed, released code, and `[measured]` or `[algebra]` evidence —
`[simulated]` alone does not clear it. G2's honest answer is a win when it is "someone did this
already"; search the adjacent field (see the `adversarial-audit` skill — this project's novelty
search has looked in the wrong field three times). G3: *would a stranger change what they build
because of it?* G4: sample sizes, assumed functional forms, conflicts of interest, and the
experiments you did not run.

## Reserved to the principal — never do these yourself

- Pushing to a public remote, or making a repository public.
- Rewriting history or choosing a fresh root commit.
- Removing or aggregating the remaining private-corpus identifiers, where that changes a
  finding.
- Putting a secret anywhere a public repository can reach it — commit, repository settings,
  Actions secrets. **A capability that needs a credential there is not built. It runs locally
  or it does not run.**

## What you will be tempted to say

| Rationalisation | Reality |
|---|---|
| "All the checks passed." | Three passed and the audit still said do not publish. |
| "It's only a hash / a path fragment / an internal name." | 71 hashes reconstructed a private repository's incident timeline. |
| "We scrubbed that already." | The tip was scrubbed. The first commit was not. |
| "It's a private repo for now." | Publication is a one-way door and this is the last gate before it. |
| "The audit is expensive." | It costs one dispatch. Publication cannot be undone. |

## Harness support

Portable core: the enumeration habit, the four gates, the reserved decisions — all procedure.
The six commands are dependency-free Python 3.13 plus `pytest`/`ruff`, so they run under Claude
Code, Codex, Cursor and Grok CLI alike. The one step that must **not** run on the harness that
wrote the artefact is the independent audit; dispatch that to another family.

## Adapted from

Structure borrowed from `obra/superpowers` (MIT, Jesse Vincent) — the iron-law-plus-red-flags
shape and the two-column rationalisation table, which its own wording tests found outperforms a
bare prohibition list. Nothing is copied verbatim; the content is this repository's measured
incident record.

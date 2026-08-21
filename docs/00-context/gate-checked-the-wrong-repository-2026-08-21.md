# The gate that could have passed without reading anything

**Date:** 21 August 2026
**Status:** `[measured]` for every count and exit status below, each reproduced by direct test
on this machine today; `[asserted]` for the judgements about what follows.
**Scope:** `.github/scripts/check_private_corpus.py`, `check_foreign_identifiers.py`,
`check_secrets.py`, `check_rename_safety.py`, `tests/test_v0_invariants.py`.

β is the rate at which automated checks accept a bad artefact. Today it landed on this
project's own publication gate, in the worst possible place: **the one check standing between
a private commercial codebase and a public repository.**

---

## What was wrong

### 1. An inherited environment made the check read the wrong repository

`corpus_paths()` ran `git ls-files` with `cwd=` pointed at a private corpus and **no
environment scrubbing**. Git exports `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE` into
every hook it invokes, and **`GIT_DIR` overrides `cwd`**. A subprocess that inherits them
reads whatever repository the hook came from, silently, with a zero exit status.

Measured today, same script, same tree, two environments: [measured]

| run | distinctive needles enumerated | corpora reported | result |
|---|---|---|---|
| standalone | **2854** | 2 | PASS |
| from the `pre-push` hook | **17** | 2 | 2123 findings |

The 2123 findings were this repository's own files matching **themselves** — a trajectory log
reported as "referencing a private path ending `.../<its own filename>`". `tracked_files()`
carried the identical defect and was invisible only because the leaked `GIT_DIR` happened to
name the repository it wanted anyway.

### 2. `--require-corpora` asserted presence and called it evidence

The flag tested `(corpus / ".git").exists()` and nothing more. It never established that the
enumeration came from the corpus. Under the leak the script printed **"checking against 17
distinctive paths from 2 corpora"** — a sentence in which the number and the noun came from
different repositories, and only the noun was true.

This is the part that matters. The false-FAIL direction is loud and self-correcting; somebody
sees 2123 absurd findings and investigates. **The false-PASS direction is silent.** On a tree
where those seventeen wrong needles happened not to match, the gate would have printed
`private-corpus invariant passes`, exited 0, and the hook would have allowed an irreversible
publish — **having opened neither private repository.** Publishing is one-way; a force-push
does not un-publish a clone.

Nothing was published. The defect was found before it mattered, which is luck rather than
process, and the reason it is written down here rather than fixed quietly.

### 3. The neighbouring gate was a wall, so it taught bypass

`check_foreign_identifiers.py` exited non-zero on fourteen occurrences that had already been
examined and cleared, and `pre-push` refuses on any non-zero exit. **The gate could not pass.**
That is precisely the defect this project catalogued a day earlier in
`four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`: a condition that can never pass
teaches people to bypass it, and a bypassed gate protects nothing at all.

---

## How it was found

By running the check from the hook and reading its real output instead of its exit status. The
standalone run passed; the hook run did not; the same script cannot be right in both. Nothing
cleverer than that was involved, and nothing cleverer would have been needed at any point in
the preceding day.

**Verify by artefact, never by exit code.** The 2854-versus-17 line is the artefact. The exit
status was 0 in the run that had checked nothing.

---

## What now prevents it

Each repair ships with the check that fails if it is removed, in this commit, per working
principle 3 and the Engineering Ratchet.

1. **`GIT_ENV`** — every git subprocess in `.github/scripts/` runs with every `GIT_*` variable
   removed. All four checkers had the leak; all four are scrubbed.
   → `test_gate_scripts_scrub_the_git_environment` poisons `GIT_DIR` and `GIT_WORK_TREE` and
   requires the enumeration to still describe the directory it was handed, then asserts across
   every checker that each `subprocess.run` carries `env=GIT_ENV`.
2. **Binding** — `ls_files()` returns nothing until `git rev-parse --show-toplevel`, run from
   the same directory, resolves to that same directory. An empty listing is refused too: a
   corpus yielding no paths yields no needles, and a gate that checked nothing must never
   report PASS. `cwd=` is a request; `rev-parse` is the answer.
   → `test_corpus_enumeration_is_bound_to_the_corpus`.
3. **An allowlist instead of a wall** — the fourteen cleared occurrences (twelve distinct
   identifiers) are recorded with a justification each, and the gate exits 0 on exactly that
   set and non-zero on anything else. Each was re-tested today with
   `git cat-file -e SHA^{commit}` against **both** private corpora under a scrubbed
   environment: **none resolves in either.** [measured] Ten are public GitHub permalinks in a
   design note; one is this project's own orphaned pre-registration commit; one is an agent
   session snapshot digest inside a captured transcript, not a git commit at all.
   → `test_foreign_identifier_gate_can_pass_and_still_refuses_the_unknown`, alongside the
   existing count ratchet, which still reads the true total because the report prints one line
   per file on the passing path as well as the failing one.

Allowlist entries are stored as the **SHA-256 digest** of the identifier, never the identifier.
The truncation discipline exists because a script that dumps identifiers into a build log has
itself become the leak, and an allowlist is a build artefact like any other.

**Each of the three tests was mutation-checked**: the repair was removed, the test was run, and
the test failed. The corpus-binding test did not fail on the first attempt — it was passing
through the empty-listing branch rather than the binding assertion, so it was inert against the
mutation it existed to catch. It now commits a file inside the subdirectory first. A test that
cannot fail is worse than no test, and this one proved it by being one for twenty minutes.

---

## Reversal and falsifier

**Reversal:** `git revert` this commit. It restores the leak and the wall together; they should
not be separated.

**Falsifier:** the whole case rests on identifiers not resolving in either private corpus, run
today with a scrubbed environment. If a corpus is later found to have been in a state where
those objects were unreachable — a shallow clone, a pruned reflog, a corpus at a different
commit — then the allowlist rests on a test that could not have failed, and every one of the
twelve must be re-tested before the next publish. **That is the check to repeat, not the one to
trust.**

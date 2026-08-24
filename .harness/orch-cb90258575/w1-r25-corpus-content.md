# R25 — close the content-excerpt class in the private-corpus gate

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "these two aforementioned local repos can be used as inspiration but are STRICTLY PRIVATE and
> must not be published as part of this repo"

Status today: **partial**, and the gap is in enforcement. `.github/scripts/check_private_corpus.py`
runs clean and its path/SHA needles are sound — but both gates match only file PATHS and 40-hex
SHAs. Neither ever reads a corpus file's contents, so a **verbatim quotation** from a private
document pasted into this repo is invisible to every gate. That exact class already leaked here
once (the script's own docstring, lines 11-13, records it: found by a paid cross-family audit,
not by any gate). Your job is the content-excerpt class.

## The job (one job)

1. Read `.github/scripts/check_private_corpus.py` in full first, including its docstring and
   self-test pattern. Match its style. Stdlib only.
2. Extend it with a content needle class:
   - For each corpus repo (`../hireable-3.0`, `../jobboard-v2` — resolved exactly as the existing
     `corpus_paths()` does), extract distinctive content needles from corpus files: e.g. long
     normalised lines or n-gram shingles, **stored and compared as hashes only** (sha256 of the
     normalised text). Size the needle set so the scan stays fast (thousands of needles, not
     millions); document the sizing in the docstring.
   - Scan the tracked tree (the same file enumeration the existing check uses) for content whose
     hashed shingles match a corpus needle.
   - **Never print corpus content, and never print the matched text** — a match is reported as
     the public file, line number, and needle hash prefix only. Nothing from the corpus may be
     written into this repository, including into this script's own fixtures: needles are computed
     at scan time, never persisted.
   - Keep the existing path/SHA behaviour and the script's `--self-test` intact, and extend the
     self-test to cover the content class.
3. The tree is clean today, so the extended check must exit 0 on it. Prove the new leg is not
   vacuous: `tests/test_private_corpus_content.py` builds a fixture "corpus" directory and a
   fixture "public tree" with a planted verbatim excerpt, runs the checker's content scan against
   them, and asserts a failure naming the public file; a clean fixture pair passes. Mutation-test:
   alter one word inside the planted excerpt below the shingle size and confirm the matcher still
   catches the surrounding shingles — or, if your design makes single-word edits escape, say so
   honestly in the test docstring and choose a shingle size where they do not.
4. Run the checker itself (`python .github/scripts/check_private_corpus.py`, expect exit 0),
   `python .github/scripts/check_private_corpus.py --self-test`, then
   `python -m pytest tests/test_private_corpus_content.py -q`, the full
   `python -m pytest tests/ -q`, `python -m ruff check .`, `python -m mypy --strict src/consilient`.
   Two tests are currently RED from another agent's uncommitted work (a `playwright` import in
   `src/consilient/computer_use.py`). Not yours to fix; add no new red.

## OTHER AGENTS ARE WRITING TO THIS TREE RIGHT NOW

Do not open for writing, `git add`, or revert any of:

- `tests/test_v0_invariants.py`, `src/consilient/instructions.py`, `src/consilient/computer_use.py`,
  `docs/10-research/experiment-register.md` (foreign uncommitted work)
- `docs/legal/adopted-components.json`, `.github/scripts/check_component_licences.py`,
  `tests/test_component_licences.py`, `.github/workflows/invariants.yml`,
  `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md`,
  `docs/20-design/capability-layer.md` (claimed by another live run)

## Hard limits

- The `consil` CLI is pinned at six commands {record, replay, beta, usage, doctor, dashboard}. Do not add a seventh.
- `src/consilient/` is AST-locked: no subprocess, network, credentials, or third-party imports in product code.
- `routing_orchestration_enabled` stays false. Change no gate condition.
- No secrets anywhere. Never read `C:/Users/jpbpr/.claude/settings.json`. No metered API calls. Do not `git push`.
- Nothing from `../jobboard-v2` or `../hireable-3.0` may reach this repo — the checker reads them
  locally to build hash needles, which is the sanctioned measurement-corpus use; their content must
  never appear in any file, output, or fixture here.
- Never `git add -A`. Stage only the paths this brief names.

## Working rules

- Evidence tags on every claim: [measured] you ran it, [cited] a named source, [asserted] your judgement.
- An invariant ships with its check, in the same commit, mutation-tested.
- Verify by artefact, never by exit code. Never pipe a check into `tail` and read the pipeline's status.
- Correct this brief in your first output sentence if it is wrong, and refuse rather than guess.
  A refusal with a reason is a success.

## Commit

Your dispatched brief carries a commit badge with your run id. Commit only the paths named there
with `CONSILIENT_RUN_ID=<your run id> git commit ...`. If your brief has no badge, do not commit;
leave the work in the tree and say so.

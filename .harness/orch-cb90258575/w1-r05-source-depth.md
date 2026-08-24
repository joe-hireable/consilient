# R05 — executable citation-depth checker for publication-facing documents

Note: a previous dispatch of this task refused because the brief required possible edits to
`README.md` while the claim excluded it. That refusal was correct; the claim now includes it.

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "Never cite a [SNIP] or [2ND] source publicly."

Publication-facing documents may cite only [FULL]/[ABS]-verified sources; a [SNIP] or [2ND]
flagged source appearing in a public artefact is a violation. Status today: **substrate-only** —
the depth markers exist and are applied, but there is no executable checker, no gate, no test.
Enforcement is a prose instruction a human must remember. That is this project's catalogued
failure shape; your job is to put the check behind the rule.

## The job (one job)

1. Read `.agents/skills/citing-sources/SKILL.md` (lines 14-19 define [FULL]/[ABS]/[SNIP]/[2ND])
   and look at how the markers are actually applied in `docs/50-publications/P1-proxy.md`,
   `P2-guards.md`, `P3-echo.md` (85 per-citation markers across the three).
2. Write `.github/scripts/check_source_depth.py` (stdlib only, matching the style of the
   neighbouring `check_foreign_identifiers.py` and `check_private_corpus.py`, including a
   `--self-test`): scan publication-facing markdown (default: `docs/50-publications/*.md` and
   `README.md`; accept paths as argv) and exit non-zero, listing `file:line`, when a citation
   carries a [SNIP] or [2ND] depth marker. [FULL] and [ABS] pass. A citation with no depth
   marker in a publication-facing file is also a failure — an unmarked citation is an unverified
   one. Keep the scan line-based and simple; do not parse markdown.
3. Wire the checker into `scripts/release_check.py` as one of its gates (read that file first
   and follow its existing pattern; do not restructure it).
4. Write `tests/test_source_depth.py`: fixture document with a [SNIP] citation fails; [FULL]/[ABS]
   passes; an unmarked citation in a publication-facing file fails; mutation-test the checker —
   flip a fixture marker from [FULL] to [2ND], confirm the test suite catches it, restore.
5. **If the current drafts contain [SNIP] or [2ND] markers**, the checker must fail on them, and
   you must then resolve each one: upgrade the citation to a verified source you have actually
   read, or remove the claim it supports. Report per citation which you did. Do not relabel a
   source you have not read — mislabelling is the worst thing you can do on this project.
6. Run `python -m pytest tests/test_source_depth.py -q`, then the full
   `python -m pytest tests/ -q`, `python -m ruff check .`, and
   `python -m mypy --strict src/consilient` before committing. Note: two tests are currently RED
   from another agent's uncommitted work (a `playwright` import in `src/consilient/computer_use.py`).
   That is not yours to fix; your work must add no new red.

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
- Nothing from `../jobboard-v2` or `../hireable-3.0` may reach this repo — no paths, SHAs, or content.
- Never `git add -A`. Stage only the paths this brief names.

## Working rules

- Evidence tags on every claim: [measured] you ran it, [cited] a named source, [asserted] your judgement.
- An invariant ships with its check, in the same commit, mutation-tested: break it, confirm the test
  fails, restore, confirm it passes, and say what happened in your final output.
- Verify by artefact, never by exit code. Never pipe a check into `tail` and read the pipeline's status.
- Correct this brief in your first output sentence if it is wrong, and refuse rather than guess.
  A refusal with a reason is a success.

## Commit

Your dispatched brief carries a commit badge with your run id. Commit only the paths named there
with `CONSILIENT_RUN_ID=<your run id> git commit ...`. If your brief has no badge, do not commit;
leave the work in the tree and say so.

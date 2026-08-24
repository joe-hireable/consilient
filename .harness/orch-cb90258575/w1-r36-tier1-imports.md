# R36 — ADR-0065's tier-1 import ban, as a new scoped check

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "if we use mempalace or something or mem0 or graphify or a combination we should PR upstream
> rather than custom engineering everything unless validated by experimentation and research etc."

Adopt the best existing open-source component; building custom requires recorded justification.
ADR-0065 (ACCEPTED 21 Aug 2026) makes that doctrine binding and owes two executable checks
(its lines 134-136). One of them — the adopted-component licence record — is being built by
another live run tonight; **do not touch it**. Yours is the other: the **tier-1 third-party
import ban**, split correctly.

The problem to understand first: the ban's AST machinery already exists at
`tests/test_v0_invariants.py:3944-3964` (~20 lines), but it is scoped to the **whole package**.
That scope currently means "adopt nothing", which is the opposite of what the principal asked
for. The ADR's design is two tiers: **tier 1** (the modules whose error rate must be measured —
`beta`, `events`, `projection`, `recall`, `budget`, `work_items`, `coordination`, `routing`)
keeps a hard ban on third-party imports; **tier 2** modules may import an adopted, licence-cleared
component. The existing whole-package test must be re-scoped by its owner — **that file is foreign
uncommitted work tonight and you must not edit it.** Your slice is the tier-1 half, as a new file.

## The job (one job)

1. Read `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md` (do not
   edit it — it is claimed by another run) and the existing machinery at
   `tests/test_v0_invariants.py:3944-3964` (read, do not edit).
2. Create `tests/test_tier1_imports.py`:
   - AST-walk exactly the eight tier-1 modules (`src/consilient/{beta,events,projection,recall,
     budget,work_items,coordination,routing}.py`) and fail on any import whose root is neither
     the standard library nor `consilient`.
   - Assert the tier-1 list names exactly those eight modules and that each file exists on disk,
     so a module rename breaks this test rather than silently narrowing the ban.
   - The module docstring must record, with [measured]/[asserted] tags as appropriate: this is the
     tier-1 half of ADR-0065's owed check; the whole-package test at
     `tests/test_v0_invariants.py:3944-3964` remains in force until its owner re-scopes it to
     tier 2; tier-2 adoption becomes legal only when the licence record (being built tonight in
     `docs/legal/adopted-components.json` by another run) names the component.
   - Mutation-test: the test must fail when a fixture module carrying `import requests` is
     scanned, and pass on the real tree. Say what happened in your final output.
3. Run `python -m pytest tests/test_tier1_imports.py -q`, then the full
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

Your entire surface is the single new file `tests/test_tier1_imports.py`.

## Hard limits

- The `consil` CLI is pinned at six commands {record, replay, beta, usage, doctor, dashboard}. Do not add a seventh.
- `src/consilient/` is AST-locked: no subprocess, network, credentials, or third-party imports in product code.
- `routing_orchestration_enabled` stays false. Change no gate condition.
- No secrets anywhere. Never read `C:/Users/jpbpr/.claude/settings.json`. No metered API calls. Do not `git push`.
- Nothing from `../jobboard-v2` or `../hireable-3.0` may reach this repo — no paths, SHAs, or content.
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

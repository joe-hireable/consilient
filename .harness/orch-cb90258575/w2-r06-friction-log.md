# R06 — friction-log staleness check + tonight's friction row

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "Keep docs/00-context/friction-log.md updated as you go — every manual step you have to do that
> Consilience should automate. That log is the v0 backlog."

Status today: **partial**. The log exists and is genuinely maintained by hand, but nothing fails
when it goes stale — so it degrades the moment attention moves elsewhere. That is this project's
own catalogued failure shape: a documented rule with no check behind it.

## The job (one job)

1. Read `docs/00-context/friction-log.md` and match its exact row format.
2. Append **today's** row (2026-08-21) recording real, measured friction from tonight's
   orchestration run — two items, both verified from this repository's own trajectory:
   - Concurrent `cursor-agent` launches raced the CLI's shared config file and wiped the trust
     list machine-wide; launches had to be serialised until an exclusive lock
     (`.harness/cursor-agent.lock`) existed. Manual step to automate: launch serialisation is
     operator discipline, not an enforced mechanism.
   - Of 35 dispatches measured tonight, 5 timed out returning **zero bytes** — a timeout is
     indistinguishable from "nearly finished" without opening the transcript under
     `.harness/dispatch/<run-id>/`. Manual step to automate: mid-run artefact-progress sampling
     on dispatched workers (a stall detector exists for the loop; dispatch does not use it).
   Phrase them in the log's own voice. [measured] both.
3. Create `tests/test_friction_log.py`:
   - Parse the newest `| YYYY-MM-DD |` row date in `docs/00-context/friction-log.md` and the
     newest commit date (`git log -1 --format=%cs`, with `GIT_*` scrubbed from the environment —
     see `.github/scripts/check_private_corpus.py` for the pattern; a hook's inherited `GIT_DIR`
     once redirected a check at another repository).
   - Fail when the log's newest row is more than **1 day** older than the newest commit date.
     Compare against the newest commit, never against wall-clock today, so a commit-free weekend
     cannot fail the check. State that reasoning in the test docstring.
   - Skip cleanly when git is unavailable.
   - Mutation-test: a fixture log whose newest row is a week stale must fail; a fresh fixture
     passes. Say what happened in your final output.
4. After your row lands, the check must pass on this tree. Run
   `python -m pytest tests/test_friction_log.py -q`, full `python -m pytest tests/ -q`,
   `python -m ruff check .`, `python -m mypy --strict src/consilient`. Two tests are currently RED
   from another agent's uncommitted work (a `playwright` import in `src/consilient/computer_use.py`).
   Not yours to fix; add no new red.

## OTHER AGENTS ARE WRITING TO THIS TREE RIGHT NOW

Do not open for writing, `git add`, or revert any of:

- `tests/test_v0_invariants.py`, `src/consilient/instructions.py`, `src/consilient/computer_use.py`,
  `docs/10-research/experiment-register.md` (foreign uncommitted work)
- `docs/legal/adopted-components.json`, `.github/scripts/check_component_licences.py`,
  `tests/test_component_licences.py`, `.github/workflows/invariants.yml`,
  `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md`,
  `docs/20-design/capability-layer.md` (claimed by another live run)

Your surface: `tests/test_friction_log.py` and `docs/00-context/friction-log.md` only. Do not edit
`scripts/dispatch.py` tonight — the standing-prompt-line half of this requirement is deliberately
out of scope; another run owns that file.

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

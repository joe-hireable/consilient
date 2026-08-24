# R20 + R23 — the feedback module: skippable, never re-asked, achievement kept separate from cost

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirements (the principal's words)

> R20: "Feedback prompts must be skippable with no consequence and no re-ask."
> R23: "Document that these are recorded SEPARATELY and never collapsed into a single score unless
> the user has explicitly set the trade-off."

A sibling dispatch landed (or is landing) the schema half in `src/consilient/events.py`: kinds
`feedback.asked` / `feedback.answered` / `feedback.skipped`, each carrying `task`; `answered`
carries `achievement` and no cost fields; composite-score fields require `user_weighting`.
**Read `src/consilient/events.py` first and build on what is actually there.** If the schema limb
has not landed (no such kinds exist), implement the module against a local copy of that contract
and say plainly in your first output sentence that the schema half was missing — do not edit
`events.py` yourself; another run owns it tonight.

Also read `docs/20-design/feedback-signals.md` (the doctrine this implements) before designing.

## The job (one job)

Create `src/consilient/feedback.py` (pure stdlib; the AST lock applies: no subprocess, no network,
no third-party imports) and `tests/test_feedback.py`:

1. `should_ask(task: str, events) -> bool` — False once a `feedback.asked`, `feedback.answered` or
   `feedback.skipped` event for that task exists in the log. A skip is never re-asked; an answer
   is never re-asked; an unanswered ask is not duplicated. (R20's no-re-ask limb, durable because
   the log is append-only.)
2. `record_ask` / `record_skip` / `record_answer` helpers that build and validate events through
   `consilient.events` (never hand-assembled JSON).
3. **No functional consequence (R20's middle limb), enforced:** a test asserts that
   `consilient.projection` (and `beta`) produce identical output over a fixture log whether a
   task's feedback was answered or skipped; and a guard test asserts no module in `src/consilient/`
   outside `feedback.py` itself reads `feedback.*` events to gate anything (an AST/import scan is
   fine — keep it simple and word the docstring honestly about what it can and cannot see).
4. **Separate storage (R23):** `feedback.answered` events carry achievement only; a test asserts
   the module exposes no function that returns a composite of achievement and cost, and that
   attempting to record a composite without a `user_weighting` reference is refused by the schema.
5. **Explicit user weighting (R23's exception):** a `composite_score(task, events, weighting_ref)`
   (or equivalent — your naming) refuses unless the log carries the referenced weighting record
   AND that record was authored by the named principal (V0-18: actor == principal). Both refusal
   paths get failing-capable tests.
6. Mutation-test limbs 1, 3 and 5 (break the check, watch the test fail, restore) and report what
   happened per limb.

The three-questions-at-task-close surface and the pre-committed goal record are **out of scope
tonight** (no product surface exists to render them); say so in the module docstring so the gap
is recorded where the next run will find it.

## Verify

`python -m pytest tests/test_feedback.py -q`, full `python -m pytest tests/ -q`,
`python -m ruff check .`, `python -m mypy --strict src/consilient`. Two tests are currently RED
from another agent's uncommitted work (a `playwright` import in `src/consilient/computer_use.py`).
Not yours to fix; add no new red.

## OTHER AGENTS ARE WRITING TO THIS TREE RIGHT NOW

Do not open for writing, `git add`, or revert any of:

- `tests/test_v0_invariants.py`, `src/consilient/instructions.py`, `src/consilient/computer_use.py`,
  `docs/10-research/experiment-register.md` (foreign uncommitted work)
- `src/consilient/events.py` (owned tonight by the schema dispatch — read it, never edit it)
- `docs/legal/adopted-components.json`, `.github/scripts/check_component_licences.py`,
  `tests/test_component_licences.py`, `.github/workflows/invariants.yml`,
  `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md`,
  `docs/20-design/capability-layer.md` (claimed by another live run)

Your surface: `src/consilient/feedback.py` and `tests/test_feedback.py` only.

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

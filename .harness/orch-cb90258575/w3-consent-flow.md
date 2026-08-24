# R19 — the consent flow: two purposes, separately obtained, visibly separate

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "Feedback for PRODUCT IMPROVEMENT and feedback for TRAINING are different purposes and must not
> be bundled — that bundling is the specific manoeuvre §3 forbids."

Consent for product-improvement feedback and for training use must be **separately obtained** and
**visibly separate**, with **per-use re-consent where there is commercial gain**. Status tonight:
substrate-only — the schema refused everything except a hand-written event, and no product surface
could obtain anything. A sibling dispatch landed (or is landing) the schema half in
`src/consilient/events.py`: purposes `improve-consilient` and `train-consilient` as distinct
values, and `commercial-training` permitted only with `per_use: true` + a non-empty `use_ref`.
**Read `src/consilient/events.py` first (`_check_consent_contract`, `CONSENT_PURPOSES`) and build
on what is actually there.** If the schema limb has not landed, say so in your first output
sentence and implement the flow against the contract as specified above — do not edit
`events.py`; another run owns it tonight.

Also read `docs/decisions/0057-*.md` (the promise this flow keeps) and
`docs/decisions/0066-principal-harvest-is-a-private-training-corpus.md` before designing.

## The job (one job)

Create `scripts/consent.py` (stdlib only — execution lives in `scripts/`, the AST lock keeps
`src/` pure) and `tests/test_consent_flow.py`:

1. `python scripts/consent.py grant --purpose improve-consilient --retention-days N
   --principal <name> --via cli` and the same for `--purpose train-consilient` are **two separate
   invocations with separate prompts** — there is no code path that obtains both in one gesture.
   That separation is the point; a `--purpose both` or a combined prompt is the forbidden
   manoeuvre. Each grant appends a `consent.granted` event through `consilient.events` (never
   hand-assembled JSON), actor == principal (V0-18).
2. `--purpose commercial-training` requires `--use-ref` naming the single authorised use; the
   script refuses without it, and the refusal text says why (per-use re-consent where there is
   commercial gain).
3. `python scripts/consent.py withdraw --purpose ...` appends `consent.withdrawn` for that
   purpose alone — withdrawing training consent must not touch an improvement grant.
4. `python scripts/consent.py show` renders the two purposes as **visibly separate** sections,
   each with its own status (granted-until / withdrawn / never-asked), so a user can see at a
   glance that they are independent decisions. A test asserts the two purposes render in separate
   sections and that a withdrawal of one leaves the other's status unchanged.
5. Tests use a temporary log path (never the real `.harness/log/`); every limb above gets a
   failing-capable test; mutation-test the commercial per-use refusal (drop the check, watch the
   test fail, restore) and report what happened.
6. Add a short paragraph to `docs/20-design/feedback-signals.md` recording that the flow now
   exists as `scripts/consent.py`, that the purposes are separately obtained and visibly separate,
   and that commercial gain is per-use — tagged [measured] once your tests pass. Keep it to a
   paragraph; match the file's voice.

## Verify

Run the script for real against a temp log (grant improve, grant train, show, withdraw train,
show — paste the two `show` renders into your final output as the artefact), then
`python -m pytest tests/test_consent_flow.py -q`, full `python -m pytest tests/ -q`,
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

Your surface: `scripts/consent.py`, `tests/test_consent_flow.py`, `docs/20-design/feedback-signals.md`.

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

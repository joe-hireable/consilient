# Event-schema extensions: feedback kinds, approval-field denylist, consent unbundling, visibility dial

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The job (one file, four pinned contracts, one test file)

All four limbs land in `src/consilient/events.py` (additive — no existing kind or check changes
behaviour) with tests in the **new** file `tests/test_event_schema_extensions.py`. Every limb
needs tests that can fail; mutation-test each (break the check, watch the test fail, restore).
The full existing suite must stay green — two tests are currently RED from another agent's
uncommitted work (a `playwright` import in `src/consilient/computer_use.py`); that is not yours
to fix, and you must add no new red. If an existing test pins something you need to change, stop
and report rather than editing `tests/test_v0_invariants.py` — that file is foreign work tonight.

Read these before designing: `src/consilient/events.py` in full (note `_check_consent_contract`,
`_check_human_authority`, `HUMAN_ONLY`, `CONSENT_PURPOSES`),
`docs/decisions/0057-a-users-trajectory-is-their-data-private-by-default-and-shared-only-by-consent.md`
(or the closest-named 0057 file), `docs/20-design/feedback-signals.md`, and
`docs/40-spec/v0-draft.md` around V0-21.

### Limb 1 (R22 / V0-21): stated-approval fields are refused by the schema

Joe: "Do not build response-level rating at all" and "NEVER a training target: 'was this
helpful?' style approval signals." Add a pinned denylist of approval-signal/self-report field
names (e.g. `satisfaction`, `thumbs`, `thumbs_up`, `thumbs_down`, `rating`, `helpful`,
`helpfulness`, `stars`, `star_rating`, `csat`, `nps`) rejected by `validate()` wherever they
appear in `data`, on any event kind, with an `EventError` naming V0-21. First `grep` the tree to
confirm no existing event kind or test fixture uses such a key legitimately; if one does, narrow
the denylist and say why. `human_verdict` accept/reject is a verdict, not a rating — untouched.

### Limb 2 (R20 + R23): task-close feedback kinds, achievement stored separately from cost

Add three kinds: `feedback.asked`, `feedback.answered`, `feedback.skipped`. Contract:
- All three carry `task` (non-empty string — the work-item/ticket reference).
- `feedback.answered` carries `achievement` (non-empty string: the goal-achievement answer) and
  must **not** carry cost, duration or turn-count fields — cost is derived from the trajectory,
  never asked; the two signals are stored separately, permanently (R23;
  `docs/20-design/feedback-signals.md:107-116`).
- `feedback.skipped` carries no answer fields; a skip is complete in itself (R20: skippable with
  no consequence — the schema's part is that nothing is required of a skip).
- Composite guard (R23's enforcement): any event, of any kind, carrying a composite-score field
  (`composite`, `score`, `overall`, `overall_score`) must also carry `user_weighting` as a
  non-empty string naming the explicit user-set trade-off record it derives from; otherwise
  refuse. Whether that referenced record exists and was user-authored is a trajectory-level check
  owned by a separate dispatch — say so in a comment.

### Limb 3 (R19): consent purposes are unbundled; commercial gain is per-use or never

Joe: "Feedback for PRODUCT IMPROVEMENT and feedback for TRAINING are different purposes and must
not be bundled." Today `CONSENT_PURPOSES = {"improve-consilient"}` and the error at
`_check_consent_contract` says sharing is permitted only to improve Consilient. Change:
- Add a distinct training purpose, `train-consilient`, alongside `improve-consilient`. One event
  names exactly one purpose (a list of purposes is invalid — that *is* the bundling manoeuvre).
- A grant for a purpose involving commercial gain is never blanket: introduce
  `commercial-training` as a permitted purpose **only** with `per_use: true` and a non-empty
  `use_ref` naming the single authorised use; a `commercial-training` grant lacking either is
  refused. Withdrawal stays per-purpose and needs no retention field, as today.
- Update the stale comment and error text that claim improvement is the only permitted purpose,
  and keep the `retention_days` positive-integer rule on every grant.
- Read ADR-0057 and `docs/decisions/0066-principal-harvest-is-a-private-training-corpus.md`
  first; if you judge the schema change contradicts either, say so in your first output sentence
  and implement only the limbs that do not.

### Limb 4 (R31 kernel): `visibility.change` is a human decision

Add kind `visibility.change`: carries `level` in `{"none", "partial", "full"}` and names its
`principal`; the dial is the human's, so an event whose `actor` is not the named `principal` is
invalid (wire it into the existing V0-18 machinery the way consent is wired, or equivalently —
your choice, but an agent-authored `visibility.change` must fail validation). The streaming
surface that would render at a level is a separate dispatch; this limb is the record.

## Verify

`python -m pytest tests/test_event_schema_extensions.py -q`, then `python -m pytest tests/ -q`,
`python -m ruff check .`, `python -m mypy --strict src/consilient`. Report the mutation-test
outcome per limb.

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
- Verify by artefact, never by exit code. Never pipe a check into `tail` and read the pipeline's status.
- Correct this brief in your first output sentence if it is wrong, and refuse rather than guess.
  A refusal with a reason is a success.

## Commit

Your dispatched brief carries a commit badge with your run id. Commit only the paths named there
with `CONSILIENT_RUN_ID=<your run id> git commit ...`. If your brief has no badge, do not commit;
leave the work in the tree and say so.

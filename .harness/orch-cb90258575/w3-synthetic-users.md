# R34 (slice) — ADR-0055's run-spec, finding object, and the unmeasured-verifier guard

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words)

> "how we can facilitate automated codebase QA and automation via the harness. Including synthetic
> data generation, synthetic users, sandboxes, whatever else."

QA is to be a first-class harness capability. Tonight's slice is the load-bearing kernel of the
synthetic-users limb, specified in
`docs/decisions/0055-simulated-users-produce-runs-not-verdicts.md` — **read it in full first**.
The ADR specifies in prose: (clause 1) a run specification with the information boundary as a
field of the type; (clause 2) a finding object — a run's output is a finding, not a verdict;
(clause 3) **the load-bearing clause: an unmeasured verifier's *pass* is not evidence; only its
*fail* is**. None of it exists as code. Your job is the three objects and the clause-3 guard.
The runner, the sandbox, and the findings store are **out of scope tonight** — say so in the
module docstring so the gap is recorded where the next run will find it.

## The job (one job)

Create `src/consilient/synthetic.py` (pure stdlib; the AST lock applies: no subprocess, no
network, no third-party imports) and `tests/test_synthetic_users.py`:

1. **RunSpec** — a frozen dataclass modelling ADR-0055 clause 1: the task, the persona/simulation
   parameters, and the **information boundary** as a required field of the type (what the
   simulated user may see — the ADR is explicit that this is a field, not a convention). Validate
   on construction; an empty boundary is refused.
2. **Finding** — a frozen dataclass modelling clause 2: the observed discrepancy, the reproduction
   (a finding is re-verifiable by replaying its reproduction — the ADR's [algebra] note), and the
   verifier identity. A finding is never a verdict: there is no `approved`/`accepted` field, and
   the type docstring says why.
3. **The clause-3 guard** — a function (e.g. `admissible(finding, verifier_measurement) -> ...`)
   that admits a finding as evidence **only** when either (a) the finding is a *fail* from any
   verifier, or (b) the finding is a *pass* from a verifier carrying a measured error rate
   (a `beta` measurement with provenance — reuse the project's evidence-tag vocabulary:
   `measured`/`cited`/`asserted`). A pass from an unmeasured verifier is recorded with zero
   evidential weight rather than discarded (clause 3's own words) — model that explicitly; do not
   silently drop it.
4. Tests: each object validates; the guard admits measured-pass and any-fail, zero-weights
   unmeasured-pass; mutation-test the guard (invert it, watch the test fail, restore) and report
   what happened. Every claim in docstrings carries an evidence tag.

## Verify

`python -m pytest tests/test_synthetic_users.py -q`, full `python -m pytest tests/ -q`,
`python -m ruff check .`, `python -m mypy --strict src/consilient`. Two tests are currently RED
from another agent's uncommitted work (a `playwright` import in `src/consilient/computer_use.py`).
Not yours to fix; add no new red.

## OTHER AGENTS ARE WRITING TO THIS TREE RIGHT NOW

Do not open for writing, `git add`, or revert any of:

- `tests/test_v0_invariants.py`, `src/consilient/instructions.py`, `src/consilient/computer_use.py`,
  `docs/10-research/experiment-register.md` (foreign uncommitted work)
- `src/consilient/events.py` (owned tonight by another dispatch — read it if you need the
  evidence-tag vocabulary, never edit it)
- `docs/legal/adopted-components.json`, `.github/scripts/check_component_licences.py`,
  `tests/test_component_licences.py`, `.github/workflows/invariants.yml`,
  `docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md`,
  `docs/20-design/capability-layer.md` (claimed by another live run)

Your surface: `src/consilient/synthetic.py` and `tests/test_synthetic_users.py` only.

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

# R21 — contributor recognition: social only, and actually existing

You are a dispatched worker on the Consilient repository. Working directory:
`C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto`. Use `python`, not `python3`.

Read `AGENTS.md` and `CONSILIENCE.md` first. British English in prose; conventional identifiers in code.

## The requirement (the principal's words, via ADR-0024)

> "ADR-0024 forbids withholding capability as reward, so recognition must be social, never
> functional — no perks, no unlocked features, no tiering."

Status today: **absent**. Both limbs are missing. Positive limb: no CONTRIBUTORS file, no opt-in
naming mechanism, no crediting path — three contributors were invited to this repository two days
ago and nothing recognises them. Negative limb: no test or build check would catch a perk, tier
or unlocked feature if one were introduced; the prohibition lives only in two prose paragraphs
(`docs/00-context/ways-to-contribute.md:56-58`, `docs/20-design/feedback-signals.md:150-153`).

## The job (one job)

1. Read `docs/00-context/ways-to-contribute.md` and `docs/20-design/feedback-signals.md:140-160`
   first, so the file you write matches the doctrine it implements.
2. Create `CONTRIBUTORS.md` at the repository root:
   - Recognition is **social only**: release notes and this file. State plainly, in the header,
     that contribution unlocks nothing — no perks, no tiers, no features — and cite ADR-0024.
   - Listing is **opt-in**: a contributor adds themselves (name or handle + one line on what they
     did) or asks to be added; removal on request is unconditional.
   - Do **not** invent contributor names. Ship the format and the empty list. If git history
     shows external (non-Joe) commit authors, you may list those handles — verifiable fact only.
3. Create `tests/test_contributor_recognition.py`:
   - `CONTRIBUTORS.md` exists, states the social-only rule, the opt-in mechanism, and the
     no-perks/no-tiers/no-unlocked-features prohibition.
   - Guard the negative limb: scan `src/`, `scripts/` and `docs/` (excluding `CONTRIBUTORS.md`
     itself and the two doctrine files named above) for reward-mechanics language applied to
     contributors — e.g. `perk`, `tier`, `unlock`, `premium`, `badge`-gating — and fail on a hit.
     Word the pattern conservatively: substring false positives like "orchestrating" bit this
     repo before (see the R22 gap note in the conformance record); prefer word-boundary regexes
     and assert in the test that a known-clean tree passes.
   - Mutation-test: plant a "contributors unlock priority support" line in a fixture, confirm the
     guard fails, remove it, confirm green. Report what happened.
4. Run `python -m pytest tests/test_contributor_recognition.py -q`, then the full
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

Do not edit `CONTRIBUTING.md` or `README.md` tonight — other runs may; your surface is the two
files named above.

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

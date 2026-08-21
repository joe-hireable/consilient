# 0063. An instance cwd allowlist is supervised dispatch, not a Gate B pass

- **Status:** ACCEPTED 21 August 2026. Accepted by Joe Brown's instruction to work on the two private commercial repositories *with Consilient* (`python scripts/dispatch.py --cwd …`), not as a detached coding session. Recorded here because that instruction would otherwise be executed by quietly deleting the cwd check.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (authorise those two repositories, and do the work through Consilient). Operator (the mechanism: gitignored instance list, no override flag).
- **Amends:** cwd refusal in `scripts/dispatch.py` (added 21 August as the check AGENTS.md lacked). Does **not** amend [`0039`](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md): Gate B still gates dependence, still is not passed, and `routing_orchestration_enabled` stays derived from the gates.
- **Inquiry tier reached:** T1 ground — a boundary already decided in 0039 was being enforced more tightly than the ADR, and the principal then named two roots.
- **Executable model:** none — a placement rule. There is no decision variable, objective and unknown parameter. Gate G4 is not satisfied.

## Context

ADR-0039 already permits **supervised** orchestration on a repository other than this one. What Gate B gates is *unattended and default* dependence. The cwd check added to `dispatch.py` on 21 August refused *every* foreign path, including under `--dry-run`, with no override flag. That was the right check for the rule as AGENTS.md then stated it ("nothing here may be pointed at `../hireable-3.0` or `../jobboard-v2`"), and the wrong check for 0039 plus the principal's later instruction to do that work *through Consilient*.

Two holes would have been easy and both are forbidden:

1. **`--gate-b-approved`.** A flag is a second path to the same state. Working principle 3: a chokepoint with a bypass is not a chokepoint. The existing test `test_resolve_cwd_has_no_override_flag` stays.
2. **Passing Gate B by inference.** Listing two roots is not twenty supervised tickets, not a measured critic β, and not a fallback result. `consil doctor` must keep reporting the gates shut.

ADR-0059 already split instance from product: anything that needs an absolute machine path is not committed. The allowlist is that path-bearing instance file.

## Decision

**`scripts/dispatch.py --cwd` accepts this repository, its git worktrees, and any existing directory named in the gitignored instance file `.harness/allowed-cwds.json`. Nothing else. There is no flag.**

Concretely:

1. **Missing file, empty `roots`, or a listed path that does not exist** → no extra roots. The product default is unchanged: refuse foreign cwd.
2. **Malformed JSON, a non-list `roots`, or a filesystem root** (`C:\`, `/`) → refuse, fail closed. A typo must not authorise the machine.
3. **The unattended loop** (`src/consilient/loop.py`) still refuses any workspace that is not this repository. Supervised dispatch and unattended dependence are different surfaces.
4. **`consil doctor` is untouched.** Listing a root does not flip `routing_orchestration_enabled`.
5. **Publishing is untouched.** Code, file contents, excerpts, detailed paths and commit identifiers from a named foreign root still must not be committed here. Trajectory and dispatch transcripts stay gitignored.

The two roots the principal named on 21 August 2026 live only in the instance file on this machine. They are not hardcoded in the product.

## Evidence

- `[measured]` Before this ADR, `resolve_cwd` accepted only `repo_roots()` and raised `ValueError` on any other path, including `--dry-run`. Tests in `tests/test_dispatch.py` pinned that. After this ADR the same tests still pass for an unlisted foreign path.
- `[cited]` ADR-0039: "Orchestration may be built and exercised under supervision, on any repository, with the bare-agent fallback present and working. Supervised means a human can see the dispatch and stop it." Gate B "gates unattended and default operation."
- `[cited]` ADR-0059: instance configuration "contains no secret and no absolute machine path" in the committed `instance/` directory; "Anything that genuinely requires a machine path is written outside the repository."
- `[asserted]` Joe's 21 August instruction to work on the two commercial repositories *with Consilient* is authorisation of those roots for supervised dispatch, not a declaration that Gate B has passed.

## Evidence against

- `[cited]` AGENTS.md (pre-0063) said Gate B is not passed and "Nothing here may be pointed at" those two repositories. Reading that sentence as a *product* never-clause, this ADR is a loosening. Why we did it anyway: the never-clause that Joe actually signed is **do not publish them as part of this repo** (19 August) and **do not put a secret in a public repo** (20 August). Pointing Consilient *at* them, under supervision, is the B4 evidence 0039 needs, and it is what he asked for. The publish-never still binds. Where the two readings disagree, take his — AGENTS.md's own rule.
- **A gitignored allowlist is a process control, not a CI control.** CI cannot see the instance file, so it cannot verify that only the two named roots are listed. What CI *can* see: the example is empty, the instance path is gitignored, there is no override flag, an unlisted tmp path is still refused, a filesystem root is refused. That is the chokepoint. The contents of the instance file are the principal's.
- **Listing `…/Repositories` would authorise every sibling clone.** Fail-closed on filesystem roots does not prevent that. The principal owns the file; do not add a heuristic that guesses which directories "look like" the two he named — that is how a name list nobody maintains gets into the product.
- Single operator, one machine, no second reviewer of this ADR. Tag `[asserted]` on the reading of his instruction stays until he contradicts or confirms the write-up.

## Consequences

**Positive** — supervised work on a named foreign root goes through `dispatch.py`, so it writes a brief, a recall pack, a run directory and a trajectory event. That is Consilient doing the work, which is what he asked for, and it is how B4 tickets can ever exist.

**Negative** — AGENTS.md's previous "nothing may be pointed at" sentence is no longer literally true. Anyone who treated that sentence as the gate will read this as a silent lift. It is not: doctor stays red; the loop stays refuse-foreign; publishing stays forbidden.

**Neutral but load-bearing** — the allowlist is instance data. A stranger's fork with no file behaves as before. A clone that copies someone else's allowlist inherits their machine paths, which will not exist, and so authorises nothing.

## Enforcement

- Check: `tests/test_dispatch.py` — unlisted foreign cwd refused; listed root and its subdirectory accepted; unlisted sibling still refused when an allowlist exists; filesystem root refused; malformed JSON fails closed; missing file is empty; no `--gate-b-approved` / `--allow-foreign`; `.harness/allowed-cwds.json` gitignored; example tracked with `roots: []`.
- Fails CI: yes, those tests.
- Added in the same commit as the implementation: yes.
- Not a check: the names in a particular machine's allowlist. That is instance, and CI must not need it.

## What would overturn this

- The principal retracts authorisation of foreign `--cwd`. Then delete the instance file; the product default already refuses.
- Gate B passes. Then this ADR is still the cwd mechanism; doctor flipping is a different change.
- A desire to hardcode the two commercial repository names in the product. Rejected here: names in the product are a second source of truth that drifts, and they are what `check_private_corpus` exists to keep out of publishable artefacts beyond the already-recorded names in AGENTS.md.

## Publication candidate?

No. The decision is local operational law for this instance of Consilient. The interesting general claim — instance allowlisting is not a gate pass — is already in 0039 and 0059.

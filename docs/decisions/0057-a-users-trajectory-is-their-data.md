# 0057. A user's trajectory is their data, private by default, and shared only by consent

- **Status:** ACCEPTED
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (principal)
- **Inquiry tier reached:** T0 assert — a values decision by the principal, not a modelling question
- **Executable model:** none — there is no decision variable to optimise. The principal is
  settling whose data this is, which no simulation can answer.

## Context

Consilient records a trajectory: an append-only JSONL log of every attempt, outcome, verdict and
decision. That log is the instrument. β is computed from it, `consil doctor` cites it as evidence for
Gate A3, and the replay invariant compares it against the projection.

It is also a detailed record of how a person works — what they tried, what their checks said, what
they rejected and when. For the project's own repository those two readings coincide, because
Consilient's only user today is the project itself. **They stop coinciding the moment anyone else runs
`consil record`.**

Until this decision, `.gitignore` covered `.harness/state.db*` and `.harness/dispatch/` and nothing
else under `.harness/`. `.harness/log/*.jsonl` was tracked, and two days of it — `2026-08-19.jsonl`
and `2026-08-20.jsonl` — were pushed to the public repository on 21 August 2026. [measured]

**This is a one-way door in the direction that matters.** Publication cannot be undone: a force-push
does not retract a clone, a fork, or a search index. A default that publishes user data is therefore
not a default that can be corrected later for the users it has already exposed.

## Decision

**A user's trajectory belongs to that user. It is private by default, is never tracked by version
control, and is never published.** Sharing is opt-in and explicit; data a user chooses to share is
held privately and used only to improve Consilient. The project's own provenance — which ADRs were
accepted, when a stage was entered, what the gates measured — is a **separate artefact** that may be
published deliberately, and must never be published as a side effect of a user's log occupying a
tracked path.

In the principal's words, 21 August 2026:

> "Obviously we shouldn't be shipping anyones personal logs to the public repo right? So don't ship
> mine - my usage of consilient should remain private just like anyone elses unless they agree to
> share data in which case that is private and used to improve consilient only."

## Evidence

- `[measured]` `.harness/log/2026-08-19.jsonl` and `.harness/log/2026-08-20.jsonl` were tracked and
  reached the public repository in commit `b2e75e7d`, 21 August 2026. `git ls-files .harness/`
  returned them; `.gitignore` named only `state.db*` and `dispatch/`.
- `[measured]` The exposure was project-development records rather than personal data in the
  sensitive sense — 109 events, kinds such as `decision.adr_accepted`, `stage.entered`,
  `exp07.replication_completed`, actors `orchestrator`, `codex-root`, `joe-brown`. No credential and
  no third-party personal data. **This bounds the harm of the incident; it does not bear on the
  decision, because the next user's log will not have that property.**
- `[measured]` The two tests that read `.harness/log` — the `append()` bypass ratchet and the
  historical-refusal-digest pin — call `pytest.skip` when the directory is absent. They degrade to
  skipped, not to a false pass.
- `[asserted]` A default that exposes user data is materially worse than one that withholds it,
  because only one of the two errors is correctable after the fact.
- `[asserted]` A harness that measures how well a person's checks work is, by construction, a
  detailed record of that person's competence over time. Publishing it by default would be a
  surprising thing for a tool to do, and surprise is the relevant test for a default.

## Evidence against

This decision has a real cost and one structural weakness. Both are recorded because neither is
resolved.

- `[measured]` **It removes exactly the verifiability this project exists to defend.** Consilient's
  founding claim is that convergence is a *test* and its error rate must be measurable — which
  presupposes that a sceptic can check the evidence. On a fresh clone the bypass ratchet and the
  refusal-digest pin now **skip**, so a third party can no longer verify from the published tree
  alone that only 92 events bypassed `append()` or that exactly three refusals are baselined. The
  project asks to be trusted on precisely the point it tells everyone else not to take on trust.
  The intended repair — a curated provenance record, publishable deliberately — **does not exist
  yet**, so today this is a straight loss.
- `[asserted]` **Opt-in sharing biases the data that would improve the harness.** Voluntary response
  is not a random sample: users who share are plausibly those whose runs went well, are more
  engaged, or work on less sensitive code. A β aggregated across shared trajectories would be
  measured on a population selected partly *by outcome*, and β is the product. An opt-out regime, or
  mandatory anonymised aggregates, would yield better data. The principal chose the weaker
  instrument deliberately, and the bias must be stated wherever a cross-user β is ever reported.
- `[asserted]` **It weakens the project's own stated proof strategy.** The principal has argued that
  Consilient developing itself, visibly, is itself the evidence that it works. Making the record of
  that development private removes part of the public artefact that argument rests on.
- `[cited]` Many open-source projects run telemetry opt-out precisely because opt-in yields data too
  sparse to act on. We did not survey this systematically and record it as a known gap rather than a
  settled counter-argument.

We decided anyway because the costs above are borne by the project, and the cost of the alternative
is borne by users who did not choose it.

## Consequences

**Positive** — a user can run Consilient on private, commercial or client work without their record
becoming publishable by accident. The rule is now a property of the repository rather than of
whoever last edited `.gitignore`. The published tree can no longer grow a user's log as a side
effect.

**Negative** — the two ratchets above are unverifiable from a clone until a provenance record is
built. Gate A3's evidence path (`.harness/log/*.jsonl`) is now local-only, so an external reviewer
must take A3 on trust or be given the log directly. The two already-published files are **not
retractable** and no attempt is made here to pretend otherwise.

**Neutral but load-bearing** — the second half of the decision, *"unless they agree to share data"*,
is **not implemented**. There is no consent mechanism, no stated retention period, and no way for a
user to verify the use limit rather than trust it. Until those exist, **no sharing feature may
ship**: shipping one would make this ADR describe a promise the code does not keep, which is the
defect this project catalogues under its own name. Gate B4 is also constrained — it requires twenty
tickets recorded on a repository other than this one, and those records may not carry private-repo
detail into a published trajectory.

## Enforcement

- Check: `tests/test_v0_invariants.py::test_no_user_trajectory_is_tracked` — asserts
  `git ls-files .harness/log/` is empty, with the git environment scrubbed of `GIT_*` so a hook's
  inherited `GIT_DIR` cannot redirect it at another repository.
- Fails CI: yes — it is part of the invariant suite.
- Added in the same commit as the implementation: yes — `63531f6`, together with the `.gitignore`
  rule and the untracking of the two files.
- **Mutation-checked:** re-adding one log file to the index makes the test fail; removing it makes it
  pass. A test that cannot fail is worse than no test, and this repository has thirteen catalogued
  examples of that failure.

## What would overturn this

- Evidence that opt-in sharing yields a sample so sparse or so biased that a cross-user β cannot be
  estimated at all. That would not restore publish-by-default, but it would force a choice between a
  local-only β with no cross-user claim, and an anonymised mandatory aggregate with an explicit
  disclosure — and the current decision would need superseding to say which.
- A demonstration that a curated provenance record cannot carry the gate evidence without also
  carrying usage detail. That would mean the two artefacts are not separable, and the trade-off
  between privacy and verifiability would have to be made explicitly rather than assumed away.

Building the provenance record would **not** overturn this decision; it is the work this decision
implies.

## Publication candidate?

**No** — the decision itself is ordinary good practice and not novel. The adjacent question may
clear the bar later: *how does a system whose thesis is "verify, do not trust" keep its own evidence
checkable once that evidence is private?* That is a real tension, this ADR does not resolve it, and
resolving it would be worth writing up.

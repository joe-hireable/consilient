# 0101. Widen the scope to any domain, and keep coding as v0

- **Status:** ACCEPTED
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Supersedes:** 0061 — the Agent Command Post framing is widened, not withdrawn.
- **Inquiry tier reached:** T0 assert — this is a scope decision reserved to the principal, and no
  fact settles it.
- **Executable model:** none — there is no decision variable to model; the question is what we are building.

## Context

ADR-0061 defines Consilient as an **Agent Command Post**: you do not ask a model, you ask
Consilient, and it sends harnesses. That framing has served well and is why the architecture is
already domain-blind.

On 23 August 2026 the principal described something wider: shared personal productivity with an
agent organisation, visibility across goals, loops, tasks and progress, and management of calendar,
email, a business, any project, any app, any codebase. In his words, "like I do now with you but for
everything not just coding", and "it kinda becomes the everything app thst people spend the most of
their time in more than any other app".

Scope decides what gets built and what "done" means, so leaving it implicit would let it drift.

## Decision

Consilient's scope is **any domain a person works in**, not coding alone. The Agent Command Post
mechanism is unchanged: you ask Consilient, and it sends harnesses or runs models natively.

**Coding remains v0**, and for a stated reason rather than habit: it is the only domain with a cheap
automatic oracle. Tests either pass or they do not, so it is the only place β can be measured at all
today. Widening the scope does not widen the measurement, and the two must not be confused.

## Evidence

- `[asserted]` The principal's own framing, 23 August 2026, quoted above and recorded verbatim in
  `../00-context/the-machine-2026-08-22.md`.
- `[measured]` The architecture is already domain-blind. `../20-design/architecture-sketch.md`
  records this under "Domain posture", and nothing in the trajectory, the work model or the gate
  machinery assumes source code.
- `[asserted]` The principal's supporting argument is that the codebase need not be large, because
  observability and autonomy are the same machinery: a system that records everything it does in
  order to measure itself is by construction a system that can be watched and steered. That holds.

## Evidence against

- `[asserted]` Widening scope before the narrow version is proven is a well-worn way for projects to
  fail. Twenty of fifty-seven units are built and both gates are shut, so the narrow version is not
  yet proven.
- `[measured]` **β is undefined outside coding.** There is no cheap oracle for a strategy memo or an
  email, and whether anything plays that role is an open question rather than a backlog item. A
  wider scope with no measurement in the new domains is exactly the position this project exists to
  refuse, and this ADR does not resolve it.
- `[cited]` Without new exogenous signals a delegated agent network cannot beat a centralised
  decision-maker with the same information (Ao, Gao & Simchi-Levi 2026, arXiv:2603.26993). Adding
  domains does not add signals by itself.

## Consequences

**Positive** — the design work already done stops being implicitly coding-shaped. Roles, loops,
sessions and the work model are specified for a person's work rather than for a repository.

**Negative** — the surface area of "done" grows substantially, and the honest answer to "when is it
finished" becomes less definite than it was under ADR-0061.

**Neutral but load-bearing** — every future capability must now say which domain it serves and what
plays the oracle's role there. Where nothing does, it ships without β and must say so on its face.

## Enforcement

- Check: `tests/test_v0_invariants.py` continues to refuse public prose claiming a capability
  without naming its incumbent and evidence, which now applies to non-coding domains too.
- Check: **a capability outside coding must declare its oracle or declare that it has none.** No
  check enforces this today; it is named here as the gap to close, not claimed as closed.
- Fails CI: the first, yes. The second does not exist.
- Added in the same commit as the implementation: no.

## What would overturn this

Evidence that the wider scope is degrading the narrow one — units slipping, gates staying shut
longer, or design decisions justified by breadth rather than by measurement. Reverting means
returning to ADR-0061's framing, which stays coherent and is the reason this supersession is
recorded rather than the original edited.

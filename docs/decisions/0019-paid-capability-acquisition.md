# 0019. Paid capability acquisition — off by default, four conditions, never automatic

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T0 assert — a policy decision, correctly made by the user
- **Executable model:** none. This is a preferential question, not an epistemic one
  (`0018` decision 4).

## Context

`0018` decision 3 lets the system synthesise tools when its toolchain demonstrably cannot do
something. Some capabilities are behind paid APIs. The question is whether the system may
ever spend money to acquire one.

## Decision

**Yes, but off by default and gated on four independent conditions, all of which must hold.**

Joe's specification, 19 Aug 2026:

1. **The user has specifically enabled and configured the capability.** Default is off. Not
   off-by-omission — off, requiring a deliberate configuration act.
2. **The user has agreed to the specific legal terms** of the specific provider. The user
   accepts, not the agent. The agent never clicks through terms on anyone's behalf.
3. **Per-transaction permission.** Every spend is approved individually, with the amount,
   the provider and the purpose stated before approval is requested.
4. **Budget restrictions are set.** A cap the user configured, enforced in the loop.

All four. Any one absent means no spend.

## What this explicitly forbids

- Autonomous account creation.
- Accepting terms of service on the user's behalf, at any scope. (This was already flagged
  in `0005`'s legal section for model licences; the same rule applies here.)
- Standing authorisation for a class of purchases. Approval is per transaction, not per
  category.
- Any spend that is not attributable in the trajectory log to a specific approval event.
- Storing payment credentials. Providers' own OAuth or a keychain-held API key only; card
  details never touch the system.

## Evidence

- `[cited]` **63 confirmed production budget-overrun incidents across 21 orchestration
  frameworks, 2023–2026**, each backed by a quoted issue and, where reported, a dollar loss
  (arXiv:2606.04056). The paper's finding is that budget primitives are typically enforced
  by ad-hoc wrappers rather than by the system's structure. Condition 4 is not
  belt-and-braces; it is the documented failure mode.
- `[cited]` The same catalogue identifies retry loops as a common overrun mechanism — an
  agent that can pay for a capability and retry on failure is exactly that shape.
- `[asserted]` Condition 2 is the one most likely to be quietly skipped in implementation,
  because it is the only one that cannot be satisfied by a UI prompt in the agent's own
  loop — it requires the user to visit the provider. That friction is the point.

## Evidence against

- Four conjunctive conditions plus per-transaction approval will make the feature annoying
  enough that users disable it, in which case the capability is dead weight. The counter is
  that dead weight is the correct outcome for a feature whose failure mode is unbounded
  spend on someone else's card.
- Per-transaction approval breaks unattended operation, which is much of the point of
  parallel orchestration (`0007`). A long overnight run that stops on a £0.30 API call is a
  bad experience. **Unresolved** — a standing cap with per-transaction *notification* rather
  than approval would fix it and Joe has ruled that out. Revisit only if it bites in
  practice.
- No prior art was checked for how other harnesses handle this. Worth a search before
  implementing.

## Consequences

**Positive.** The failure mode with the worst tail — an agent spending unbounded money — is
structurally prevented rather than mitigated. Legal exposure from clickthrough acceptance is
eliminated by making the user the accepting party.

**Negative.** Unattended runs cannot acquire paid capabilities. Some tasks will simply stop
and wait.

**Neutral but load-bearing.** Makes the permission model a hard dependency of tool synthesis,
so `0018` decision 3 cannot ship before this does.

## Enforcement

- Check: the spend path is unreachable unless all four conditions are satisfiable from
  configuration. A test asserts that a default-configured instance has no reachable code path
  to a payment.
- Check: budget primitives are **outside the self-modification allowlist** (`0018`) —
  permanently, and independent of EXP-12 or EXP-13.
- Check: every spend event in the trajectory log references an approval event id. A spend
  without one fails the log-replay invariant (`0006`), which makes it a CI failure rather
  than an audit finding.
- Check: no code path stores or transmits card details. Dependency and pattern lint.

## What would overturn this

Only Joe. This is a preferential decision and no experiment bears on it. It should be
revisited if per-transaction approval proves to break unattended operation badly enough that
the orchestration feature is unusable — but the revision should be to the *approval
mechanism*, never to conditions 1, 2 or 4.

## Publication candidate?

No.

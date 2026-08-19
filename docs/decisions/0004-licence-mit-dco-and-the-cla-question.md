# 0004. Licence MIT, and require a DCO — plus an unresolved question about a CLA

- **Status:** PROPOSED — **contains a decision that must be made before the first external
  contribution and cannot be cheaply reversed afterwards**
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — legal/structural, not parametric.

## Context

The stated strategy is: build a large open-source community first; an exit may follow, and
if it does not, a *separate* commercial business can be started later that leverages the
community — possibly a simplified hosted version that inferences open models directly so
developers avoid configuring their own credentials.

That plan has one hard dependency almost nobody notices in time.

**Under MIT, Joe owns his own contributions and can relicense them freely. He cannot
relicense anyone else's.** Once external contributors commit under MIT with no
contributor agreement, their code is MIT forever. A later proprietary or
source-available derivative must then either exclude every external contribution, obtain
retroactive permission from every contributor, or clean-room rewrite those parts.

This has sunk real relicensing attempts. It is trivially cheap to solve on day one and
expensive-to-impossible to solve on day four hundred.

## Decision

**Decided:** MIT licence. Full open source. Donate / "buy me a coffee" button. No
open-core split in the OSS repo.

**Decided:** require a **DCO** (`Signed-off-by`) on every commit. Low friction, standard,
enforceable in CI.

**Open — must be resolved before accepting the first external PR:** whether to additionally
require a **CLA** granting Joe a relicensing right.

## Evidence

- `[cited]` MIT permits proprietary derivatives of *your own* code; it does not grant you
  the right to relicense *others'* code under different terms.
- `[cited]` DCO is the Linux-kernel-style lightweight option: it certifies provenance and
  right-to-submit; it does **not** grant relicensing rights.
- `[cited]` CLAs (Apache-style ICLA, or the CLA-assistant bot flow) do grant them, and are
  what companies with later commercial plans use.
- `[asserted]` A CLA measurably deters some contributors, particularly in communities that
  read it as a signal of a future rug-pull. The strategy here depends on community, so this
  cost is real, not theoretical.

## Evidence against

- `[asserted]` The commercial plan as stated is a *separate business leveraging the
  community*, not a fork of this codebase. If that holds literally, no CLA is needed — a
  hosted service around an MIT project requires no relicensing at all. The CLA is insurance
  against a plan change, and it is paid for in contributor goodwill.
- `[asserted]` "Could just be a simplified version of it" points the other way: a simplified
  version *is* a derivative, and derivatives of contributed code are exactly what a CLA
  covers.

## Consequences

**Positive.** Deciding now costs one afternoon. Deciding later may cost the option entirely.

**Negative.** A CLA is a visible commercial-intent signal at the moment the project is
trying to look like a gift.

**Neutral but load-bearing.** Whichever way this goes, it should be stated plainly in
`CONTRIBUTING.md` on day one. Ambiguity is worse than either choice.

## Enforcement

- Check: DCO sign-off verified in CI on every commit (GitHub's DCO app or equivalent).
- Check: if a CLA is adopted, CLA-assistant bot blocking merge until signed.
- Fails CI: yes.

## What would overturn this

- Legal advice. **This ADR is not legal advice and its author is not a lawyer.** Before the
  first external PR, get an actual opinion — this is exactly the kind of cheap-now,
  expensive-later question worth an hour of a solicitor's time.
- A decision that the commercial path will never involve this codebase, in which case skip
  the CLA and say so publicly, which is itself a community-building asset.

## Publication candidate?

No.

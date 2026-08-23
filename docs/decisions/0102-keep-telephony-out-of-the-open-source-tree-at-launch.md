# 0102. Keep telephony out of the open-source tree at launch

- **Status:** ACCEPTED
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision is a publication boundary, not a parameter.

## Context

The design for agent embodiment gives agents their own phone numbers and email addresses. The
telephony half is technically straightforward and legally the most dangerous capability designed for
this project: automated-caller disclosure obligations, voice impersonation risk, and an
accountability chain that must terminate in a named human.

Publishing the module in the open-source tree means anyone can run it, in any jurisdiction, without
the controls — and that cannot be withdrawn. Code published under a permissive licence stays
published.

`../20-design/observability-steering-and-embodiment-2026-08-23.md` reached this as D3 and marked it
as needing the principal, because no fact settles it. He decided on 23 August 2026.

## Decision

Telephony is **not** in the open-source tree at launch. It is designed in full and documented in
full, and ships later as a separate opt-in module, once disclosure controls are enforced by a check
rather than by documentation.

Email and voice synthesis are not covered by this ADR. They carry their own risks and are governed
separately; this decision is about placing a dialler in a public repository.

## Evidence

- `[cited]` Several jurisdictions require an automated caller to identify itself as such, including
  EU AI Act Article 50 transparency obligations and UK PECR. Detail and dates in the embodiment
  design document.
- `[cited]` Twilio's acceptable use policy makes the account customer responsible for end users, so
  "it runs on the user's own credentials" is a position rather than a defence when the capability is
  shipped and promoted.
- `[measured]` The adversarial review of that design found the outbound path has **no control at all**
  for an allowlisted recipient receiving an attacker-drafted payload, and named it the likeliest real
  incident. That gap is unclosed today.
- `[asserted]` Publishing is irreversible in a way that building is not. Deferring costs nothing now
  because none of it is built.

## Evidence against

- `[asserted]` Withholding a module from an open-source-first project is in tension with the
  project's own posture, and a user who wants it must either wait or build it themselves.
- `[asserted]` The capability is a genuine differentiator, and delay has a real cost in what
  Consilient can do for a user who would benefit from it.
- `[asserted]` A determined implementer can write a Twilio integration in an afternoon, so this
  prevents casual misuse under our name rather than misuse in general. **It is a boundary about
  responsibility, not about capability**, and it should not be described as safety it does not buy.

## Consequences

**Positive** — the public tree carries no dialler, so no one runs one under our name without the
controls. The disclosure and accountability work can be done properly rather than at launch pace.

**Negative** — agents have no voice channel to the outside world at launch. Part of the embodiment
design is documented and unavailable.

**Neutral but load-bearing** — the module boundary must exist in the architecture from the start, or
retrofitting it later means untangling telephony from the outbound broker after the fact.

## Enforcement

- Check: `.github/scripts/check_no_telephony.py` — refuses any import, dependency or configuration
  reaching a telephony provider from the public tree.
- Fails CI: yes.
- Added in the same commit as the implementation: **no — the check does not exist today.** There is
  no telephony code to refuse yet, and the check must land before any is written rather than after.

## What would overturn this

Disclosure, recipient-payload and accountability controls all enforced by checks that fail CI, plus
a solicitor's view on the jurisdictions the project publishes into. At that point the module can move
into the tree by a superseding ADR. The trigger is enforcement existing, not the capability being
wanted.

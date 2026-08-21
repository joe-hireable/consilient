# 0064. Add training and inference providers; OpenRouter is no longer the sole metered vendor

- **Status:** ACCEPTED — supersedes the sole-vendor clause of [ADR-0044](0044-openrouter-is-the-only-metered-vendor.md)
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (principal)
- **Inquiry tier reached:** T0 assert — a commercial and capability decision by the principal, not a modelling question
- **Executable model:** none — the decision names which vendors are permitted. There is no decision variable to optimise until per-provider cost and throughput are measured.

## Context

[ADR-0044](0044-openrouter-is-the-only-metered-vendor.md) is ACCEPTED and reads *"OpenRouter is the
only permitted metered vendor."* It was decided when the only metered need was inference through a
single aggregator, and it did the job it was written for: one billing surface, one place to set a
ceiling, no vendor sprawl.

It cannot carry the work now being asked of it. **Training is not inference.** Fine-tuning needs
accelerators OpenRouter does not sell, and the providers that do sell them are exactly the ones the
principal has named. ADR-0048 already set the commercial posture — *open source first, facilitation
prepaid and never in arrears* — but named no provider and added no adapter, so the capability has
never existed. [measured] `grep -ril "fireworks\|cerebras\|together\|groq" docs/ src/` returns only
ADR-0048, and no provider adapter exists in `src/consilient/`.

**This is a one-way door in one direction only.** Adding a vendor is reversible; a credential leaked
to one, or a training run that silently bills in arrears, is not.

## Decision

**The permitted metered vendors are OpenRouter, Google Cloud Platform, Fireworks, Cerebras, Together
AI and Groq.** OpenRouter remains the default for metered *inference*; the others are admitted for
training, fine-tuning and inference where they are the capability that exists.

Three constraints travel with the decision and are not severable from it:

1. **Local first.** Fine-tuning runs on the principal's own hardware — an RTX 5090 with 64 GB of
   system RAM — whenever the job fits. A hosted provider is reached only when the job does not fit
   locally, or when a user without local hardware has prepaid for facilitation.
2. **Prepaid, never in arrears** (ADR-0048). A hosted training run does not start until its cost and
   margin are covered up front. **A provider that can only bill after the fact is not admitted for
   training**, whatever its capability.
3. **Every metered vendor is inside the existing budget ceiling.** Weekly and monthly limits bind
   across all of them jointly, not per provider. A ceiling that each vendor checks separately is not
   a ceiling.

In the principal's words, 21 August 2026:

> "Reinforcement learning and user-level granularity fine tuning of models based on device
> capabilities and managed fine tuning utilising my 5090 64gb RAM rig and also (ONLY when paid for)
> training on GCP or fireworks or cerebras or together AI or groq all of which I have instructed we
> should add as model providers for the harness."

## Evidence

- `[measured]` 21 Aug 2026: no provider adapter for any named vendor exists in `src/consilient/`, and
  the names appear in `docs/` only inside ADR-0048. The instruction predates this record and was not
  implemented.
- `[measured]` `src/consilient/budget.py` already refuses a spend that would breach a weekly or
  monthly ceiling, atomically. The ceiling mechanism exists; it is single-vendor today.
- `[cited]` ADR-0048 fixes facilitation as prepaid and open-source-first. This ADR adds providers
  without touching that.
- `[asserted]` Training capability is the reason for the change. OpenRouter is an inference
  aggregator; routing a fine-tuning job through it is not available, so the sole-vendor clause makes
  the capability impossible rather than merely inconvenient.

## Evidence against

- `[cited]` **ADR-0044's reasoning still holds for inference**, and this ADR weakens it. One billing
  surface is genuinely easier to cap and audit than six. Six vendors means six credentials, six
  billing surfaces, six ways to leak a key, and six places a ceiling can be checked inconsistently.
  The mitigation — one joint ceiling, enforced centrally — is stated above but **is not yet built**,
  so today the decision is ahead of its enforcement. That is the gap most likely to hurt.
- `[asserted]` **Vendor sprawl arrives one justified exception at a time.** This is the first
  exception and it is well-argued; the next will be too. The rule that must survive is that a vendor
  is admitted only when it supplies a capability no admitted vendor has — not because it is cheaper
  or faster.
- `[asserted]` **"Only when paid for" is a promise the code cannot currently keep.** No prepayment
  mechanism exists. Until one does, a hosted training run can only be started by a human who has
  checked the payment themselves, and the ADR should not be read as authorising automation of that.
- `[measured]` The budget layer has known defects recorded on 21 Aug 2026: reservations are never
  retired, so a permitted spend counts twice against the ceiling; and a stale `.budget.lock` refuses
  forever after a hard kill. **Adding five vendors to a ceiling with those defects multiplies their
  effect.** They should be fixed before any hosted run.

## Consequences

**Positive** — fine-tuning becomes possible at all. Local training on the principal's own hardware
becomes the default path rather than an aspiration, which is also the cheapest and most private
option. Users without hardware get a route that does not compromise the open-source-first rule.

**Negative** — six billing surfaces to audit instead of one. Six credentials that must never reach a
public repository. The joint ceiling is specified here and unbuilt, so the enforcement gap is real
until it is closed.

**Neutral but load-bearing** — ADR-0044's subscription-first clause is **untouched and still binds**:
anything reachable through a flat-fee subscription the principal already holds is reached that way,
and a metered call is the last resort, not the first. This ADR changes *which* metered vendors are
permitted, not *whether* metered calls are preferred. They are not.

## Enforcement

- Check: `src/consilient/budget.py` must treat the permitted-vendor set as a single allowlist and
  refuse any provider outside it, with one joint weekly and monthly ceiling across all of them.
  **Not yet written.** Until it is, this ADR is a decision without a check, which is the defect this
  project catalogues under its own name — stated here rather than hidden.
- Check: no credential for any provider may appear in the repository. Covered today by
  `.github/scripts/check_secrets.py --history --untracked --self-test`, which is already in CI.
- Fails CI: the secret scan yes; the vendor allowlist not yet.
- Added in the same commit as the implementation: **no** — the decision is recorded ahead of the
  implementation deliberately, because the principal has asked for the capability and the
  implementation is being dispatched. **The vendor allowlist and joint ceiling are owed, and no
  hosted training run may start before they exist.**

## What would overturn this

- A measured finding that the joint ceiling cannot be enforced across heterogeneous vendors — for
  instance if a provider reports spend too late for a ceiling to bind in time. That would mean
  "prepaid, never in arrears" is unachievable for that vendor, and it must be dropped rather than
  the rule loosened.
- Evidence that local fine-tuning on the 5090 covers the realistic job set, which would make the
  hosted providers unnecessary for the principal himself and reduce them to a facilitation offer for
  users without hardware. That narrows the decision rather than reversing it.

## Publication candidate?

**No.** The vendor list is specific to this instance. The adjacent question may clear the bar later:
how a harness enforces a single spend ceiling across vendors that report usage at different
latencies, where one reports only after the fact.

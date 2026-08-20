# 0024. Commercialisation and telemetry — private by default, consent per purpose, no capability withheld

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none. Preferential and legal.

## Context

`0004` deferred the commercial question. Joe's position (19 Aug 2026): commercialisation may
follow, but **never** to the detriment of the open-source project, user privacy, or anything
else. Users may voluntarily share usage data, under their own control, for product
improvement, research, and potentially for developing and training future products. Private
versions are always the default.

The failure modes here are well documented and mostly self-inflicted. This ADR is mainly a
list of things not to do.

## Decision

### 1. The non-negotiable: no capability is ever withheld from the open-source version

**Not one feature is held back to drive commercial adoption.** The open-source project is not
a funnel, a trial, or a crippled edition. If a capability exists, it ships in the MIT
version.

This forecloses open-core entirely, and it is the single most important line in this ADR.
Open-core is the standard route and it corrodes exactly what `0004`'s community strategy
depends on: the moment contributors suspect their work is building someone's upsell path,
contribution stops.

Commercial value must come from things that are **not the software**: operating it, hosting
it, supporting it, or data that users chose to contribute.

### 2. Telemetry — off, and off means nothing leaves

- **Default: nothing is transmitted.** No phone-home, no version check, no crash report, no
  anonymous counters. `0022` already requires a test asserting refusal events never leave a
  local install; the same test class covers all telemetry.
- **Opt-in is granular and per-purpose**, never a single switch.
- **Preview before send.** The user can see exactly what a category would transmit, on real
  data from their own machine, before enabling it. **An opt-in the user cannot inspect is not
  informed consent.**
- **Revocation deletes.** Withdrawing consent removes previously contributed data, not just
  future collection. Withdrawal must be as easy as granting.
- **Derived metrics, never raw material.** Code, prompts, file contents and diffs never leave
  by default under any category. What leaves is computed: β estimates, escalation rates,
  latency, tier distributions. Categories that would send raw material exist separately, are
  named honestly, and default off.

### 3. Consent is per purpose, and the purposes are not bundled

| Purpose | Default | Notes |
|---|---|---|
| Product improvement — bug and performance signals | **off** | derived metrics only |
| Public research — the β corpus | **off** | aggregate; contributors credited if they wish |
| **Training future commercial products** | **off, and separately** | **never bundled with the other two** |

The third is the one communities react to most violently, and correctly. Bundling it with
"help us improve the product" is the specific manoeuvre that has destroyed trust in other
projects. It gets its own consent, its own explanation, and its own revocation.

**If the third purpose ever activates, it is announced with the 90 days' notice already
promised in `docs/legal/RELICENSING-PROMISE.md`** — the promise is written for relicensing but
the same standard applies here.

### 3a. Standing consent is not a blank cheque — per-use re-consent for commercial gain

Joe's addition, 19 Aug 2026, and it is a **stronger** standard than anything the industry
offers:

> Even where a user has enabled the commercial-training category, **every specific use that
> could result in commercial gain is requested again, individually.**

Each request states, before any use:

1. **What the use is** — the concrete product, model or service.
2. **Which of their data it would draw on**, previewable as in §2.
3. **What the commercial gain is**, plainly. Not "to support the project".
4. **What happens if they decline** — which must be: nothing. No degradation, no nagging, no
   re-ask for that use.

A decline is per-use and does not disturb their other settings. Silence is a decline;
non-response is never treated as assent.

**Why this is worth the friction:** a blanket "you may use my data for commercial products"
is consent to an unknown future. Consent to an unknown thing is not informed consent,
whatever the checkbox said. Re-asking per use is the only version that stays informed.

### 3b. The consent surface is neutral. Encouragement lives elsewhere.

Joe's intent (19 Aug 2026) is that sharing data should feel like a legitimate way to give
back without giving money. **That intent is right and the framing must be handled
carefully**, because consent that is nudged is not freely given — legally or ethically.

**In the consent surface itself:**
- Neutral, symmetric presentation. "Enable" and "Leave off" carry equal visual weight and
  equal wording.
- No emotional or reciprocity framing. Not "support the founders", not "help us keep this
  free", not "most users enable this".
- No repetition. Asked once at a natural point, and once only. A declined category is not
  re-offered unless the user goes looking.
- No consequence for declining, stated and true.

**Elsewhere — README, docs, release notes, community channels — the case can be made freely
and warmly.** Explain what the data does, what it has enabled, and that contributing it is a
real way to help a project that takes no money. That is honest advocacy in a place where
nobody is mid-decision.

The rule is the separation: **make the case where the user is browsing; stay neutral where
the user is deciding.**

**A legal note for the solicitor pass:** framing data-sharing as a way to reward the
maintainer edges towards treating the data as consideration. If data is payment, its legal
character changes and the GDPR consent basis may not hold. Keep the framing as *voluntary
contribution*, never as *payment in kind*, and confirm this.

### 4. Commercial paths that do not harm the project

Ordered by how little they conflict:

1. **Hosting and operation.** Running Consilience for people who do not want to. Requires no
   feature withholding — the value is the operating, not the software.
2. **Support, training, certification.** Standard, boring, safe.
3. **The β corpus as a public good with a commercial service layer.** The corpus itself stays
   open (`0002`, `0013`); a service that measures β for an organisation and interprets it is
   a job, not a feature. **This is probably the best fit** because it monetises expertise
   rather than access.
4. **Sponsored research.** Someone pays for an experiment in the register to be run. Results
   are published regardless of outcome, stated up front.
5. **Consulting.** Joe's time.

### 5. What is forbidden, permanently

- Withholding features (§1).
- Bundled consent (§3).
- Telemetry on by default, in any form.
- Transmitting code, prompts or diffs without a category the user explicitly enabled after
  previewing it.
- Selling user data to third parties, under any consent regime.
- Making the open-source version worse — slower, noisier, nagging — to make a paid version
  attractive.
- **Nudging inside the consent surface** (§3b). Encouragement is permitted in documentation
  and community channels; it is prohibited at the point of decision.
- **Using standing consent as authority for a specific commercial use without asking again**
  (§3a).
- **Asserting trustworthiness in place of constraining behaviour.** Every project that later
  exploited its users said it would not. The commitments in this ADR are the guarantee; a
  promise to be trustworthy is not one, and the documentation must not offer it as one.

## Evidence

- `[cited]` UK GDPR consent must be freely given, specific, informed and unambiguous, and
  **withdrawal must be as easy as giving**. Bundled consent for distinct purposes does not
  meet "specific". `docs/legal/ICLA.md` §10 already sets the pattern. **Legal review
  required — this is not legal advice.**
- `[measured]` `0004`'s stated strategy is community first; `0023` sets deliberately strict
  contribution gates. Both depend on contributors believing the project is not a funnel.
  §1 is what makes that belief defensible rather than a claim.
- `[asserted]` The β corpus is the only genuinely novel asset the project would accumulate,
  and `0013` already commits to publishing the method. Monetising interpretation rather than
  access is consistent with that.

## Evidence against

- **Everything-open plus opt-out-by-default telemetry may produce no viable business.** The
  paths in §4 are all services, all Joe-time-bound, and none scales. This ADR optimises for
  not harming the project, and that is a real trade against commercial upside.
- **"Aggregate data is safe" is not automatically true.** Repository-level metrics — file
  counts, language mix, test-suite shape, β — can fingerprint a codebase. Aggregation is not
  anonymisation and this ADR does not solve it. **k-anonymity or differential privacy on the
  corpus is unassessed and should be before any public release of it.**
- Preview-before-send is real engineering work for a feature that is off by default and may
  see little use.
- No prior art checked on OSS telemetry consent design. Others have solved this; look before
  building.

## Consequences

**Positive.** Contributors can trust the project is not a funnel, which is what `0023`'s
strict gates require to be legitimate. Privacy claims are testable rather than promised.

**Negative.** Forecloses the most common OSS monetisation route. Little usage data, so
slower product learning.

**Neutral but load-bearing.** Makes the telemetry boundary a hard architectural line, and one
that sits outside the self-modification allowlist (`0018`) permanently.

## Enforcement

- Check: a test asserts a default-configured instance makes **no outbound network calls at
  all** beyond model providers the user configured.
- Check: each telemetry category has a preview function; a test asserts preview output and
  actual payload are identical.
- Check: revocation triggers deletion; tested against a fixture.
- Check: consent categories cannot be enabled together by a single action. Bundling is a
  lint error.
- Check: the telemetry boundary is outside the self-modification allowlist.

## What would overturn this

- Legal advice requiring a different consent structure.
- §1 proving commercially unviable to the point that the project cannot be sustained. **In
  that case supersede this ADR openly and publicly, with notice** — never erode it quietly,
  which is how every project that did this lost its community.

## Publication candidate?

No. But the β corpus, released openly with proper anonymisation, is a strong Hugging Face
dataset candidate — see `../publications/README.md`, which notes a well-carded dataset often
gets more use than the paper describing it.

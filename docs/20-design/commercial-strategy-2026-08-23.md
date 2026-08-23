# Commercial strategy

Status: DESIGN. Nothing here is implemented. Nothing here is legal advice.
Date: 23 August 2026. All retrievals dated 23 August 2026 unless stated.

Every claim carries an evidence tag: [measured] observed on this machine or in this
repository; [simulated] computed from cited inputs; [cited] retrieved from a named source;
[asserted] reasoned, unverified.

---

## The promise, and what binds it

A commitment that cannot be broken says nothing. Each of these can be broken, and each
names how a stranger detects the break and what keeping it costs on the day it hurts.

**P1. Every capability runs with no payment to us and no network route to a host we
operate.** *Verify:* a conformance run with egress to our hosts blocked and no account
configured; published per release. *Costs:* it forecloses hosted-only features, which is
where the money is [cited: GitLab sells Premium at $29/user/month for self-managed installs
the customer hosts — features that cost GitLab nothing to serve].

**P2. No entitlement check exists in the core.** No licence key, seat count, plan check or
paid feature flag. *Verify:* a grep over the core package, runnable on any fork. *Costs:*
it forecloses open core permanently.

**P3. The price is a constant in MIT-licensed source.** *Verify:* `git log` on one file.
*Costs:* prices can never rise quietly; every rise is a diff with a name on it.

**P4. Ninety days' public notice for any price, licence, margin or governance change,
committed as a dated file.** *Verify:* git history, which every clone holds. *Costs:* no
emergency repricing. Comparator: OpenAI commits to "at least 30 days advance notice of
changes to these Terms that materially adversely impact you" [cited].

**P5. We never hold, pool, proxy or resell another party's provider entitlement.**
*Verify:* no provider credential leaves the user's device. *Costs:* it forecloses "one bill
for everything", which will be a frequently requested feature [asserted].

**P6. Exit in one command, round-tripped in CI.** Export produces a complete archive;
import reconstitutes on a clean machine. *Costs:* it destroys switching cost deliberately.

**P7. Benchmarking is permitted, always, including against us** [cited: GitLab publishes
the same promise — "We will always allow you to benchmark the performance of GitLab"].

**Do not believe P1–P7 because they are written down.** They are authored by the person
they constrain, in a repository he controls, with no foundation and no second maintainer
[measured: single copyright holder, LICENSE © 2026 Joseph Brown]. Their value is that
breaking them is detectable and leaving is cheap. That is all.

---

## The line

**What is free forever:** the orchestrator; the full multi-agent organisation at any agent
count; ambient and scheduled loops; observability and steering; memory at any size on the
user's disk; agent and skill authoring; every provider adapter including providers we also
host, at 0% fee; local execution; the complete trajectory with documented export; all
verification, gate and β machinery; multi-entitlement routing; and no anti-features — same
binary, same code path, no nag, no artificial delay.

**What may be charged for:** hosted inference on our own commercial API accounts; hosted
storage and sync; prepaid compute; hosted training; human labour (support, consulting, β
audits); and a trademark, which gates a claim rather than a capability.

**The principle.** The tempting rule — *anything that costs nothing to serve must be free*
— fails as a boundary, because marginal serving cost is an architectural choice rather than
a fact [asserted]. Build memory search as a cloud service and it now costs to serve, so the
same capability changes side of the line without anyone deciding to move it. A rule whose
output changes when an engineer changes a topology is a knob.

The rule that holds: **a paid offering may only substitute for a resource the user could
supply themselves — compute, storage, a provider account, or our hours. Nothing sold may be
a prerequisite for a capability.** For every paid item, name the free substitute the user
already holds and point at the test that exercises it. This is invariant under refactoring,
and it is what Home Assistant does in production: Cloud sells the fact that "you don't have
to deal with dynamic DNS, SSL certificates, or opening ports", while the free path is
documented as requiring "a bit more setup" [cited].

**The honest label.** This forgoes the revenue model with the clearest evidence of working
in this category [cited: GitLab, above]. It is a preference, not a strategy that
outperforms. Record it as a chosen sacrifice so nobody later discovers it was never really
promised.

**The enforcement mechanism does not exist.** ADR-0048 names four checks and states "None
of these exist yet" [measured]. By this project's own rule — a chokepoint without an
enforcement rule is not a chokepoint — the line is currently a promise. Anyone may say so,
and they are right until the conformance run and the ratchet test land.

---

## Subscription orchestration

Two different things are being conflated, and they must stay separate in all public copy.

**(A) The user's own entitlements, orchestrated on the user's own machine**, through each
vendor's own client, authenticated by the user — including quota that would otherwise
expire at the next reset. **(B) Consilient holding subscriptions and resharing them.**

**(B) is prohibited in current terms, quoted:**

| Provider | Clause | Effective |
|---|---|---|
| Anthropic | "You may not share your Account login information, Anthropic API key, or Account credentials with anyone else or make your Account available to anyone else." | 8 Oct 2025 [cited] |
| OpenAI | "You may not share your account credentials or make your account available to anyone else"; "Modify, copy, lease, sell or distribute any of our Services." | 1 Jan 2026 [cited] |
| xAI | "You may not share your account credentials or make your account available to anyone else"; assignment "null and void". | 26 Jun 2026 [cited] |
| Cursor | §1.5(iii) "rent, lease, lend, or sell the Service"; (xi) "knowingly permit any third party to do any of the foregoing". | 13 Aug 2026 [cited] |
| Google | "You may not copy, modify, distribute, sell, or lease any part of our services or software." | 30 Jul 2026 [cited] |

Design nothing on (B). It is not a gap to be structured around.

**(A) is not prohibited by any clause retrieved, and it is not affirmatively blessed
either.** Anthropic's Consumer Terms bar automated access "Except when you are accessing
our Services via an Anthropic API Key or where we otherwise explicitly permit it" [cited,
eff. 8 Oct 2025]. Claude Code on a subscription is that permission — but the permission
attaches to the product, and no retrieved clause says a third party may drive it headlessly
across several of a user's accounts. **This is ambiguous and we do not resolve it in our
favour.** The supporting help-page language on third-party apps authenticating with a
Claude subscription is a support article, editable without notice, and it also says credits
"can't be pooled, transferred, or shared" [cited]. Cross-account scheduling resembles
pooling from outside, whoever owns the accounts [asserted]. Google is the clearest permit —
its automated-access restriction is scoped to robots.txt violations [cited] — and its CLI is
Apache-2.0 with published quotas and documented non-interactive use [cited]. xAI's
acceptable-use policy bars "Accessing the Services through unauthorized automated or
non-human means" with no first-party CLI to supply the authorisation [cited, eff. 14 Aug
2026]; Grok is API-only.

**Architectural rule that carries the whole position:** Consilient executes the vendor's own
signed client as a subprocess and consumes its documented output. It never reads, stores,
forwards or replays a provider token, and never calls a consumer endpoint directly. A ledger
file records, per adapter, the authorising clause, its URL, retrieval date and a verdict of
permitted / ambiguous / prohibited. An adapter without a ledger entry does not build.

**If a provider rules against it.** It closes for every user at once, by a terms update, not
gradually. The free path keeps working and becomes expensive overnight; hosted inference —
the paid path — becomes the affordable route. **The promise degrades in our favour with
nobody deciding anything.** The contingency, written now while refusing is cheap: each
adapter's removal is a one-file deletion; the product must work on user API keys and local
weights alone; and no pricing may be justified by orchestration until orchestration is
measured. It is not measured today — this repository's own audit records Gate B shut and no
successful Claude dispatch [measured].

---

## Revenue routes, ranked

Tests: T1 free path keeps full value; T2 no incentive to make the free path worse; T3 no
hostage taken; T4 price scales with cost of serving.

**Recommended, in order.**

1. **Human labour — support, consulting, β audits, certification.** Passes all four; T4 by
   definition, since hours are the cost. Cannot gate a capability by construction. Scales
   badly, which suits a solvency target rather than a growth target [asserted].
2. **Hosted convenience — instances, storage, inference, one prepaid fee.** Passes with
   conditions: export tested in CI (T3), and the hosted feature list generated from the free
   feature list so a hosted-only entry is a build failure (T2).
3. **Sponsorship, with a published rule that it buys no roadmap position.** Zero build cost.
   The ceiling is real: core-js at roughly 9bn cumulative downloads earned about $400/month
   at the low point, the author's own arithmetic being "less than $2 per hour of work"
   [cited]; Plausible reports "only six $5 donations over six months" against $8,500+ MRR
   [cited]. Blender's fund runs at €286,820/month [cited], which suggests the ceiling tracks
   user base rather than the mechanism.

**Rejected — the rejections carry the argument.**

- **Reselling held subscriptions.** Prohibited five times over. See above.
- **Open-core enterprise features (SSO, audit, compliance).** Fails T1 — a self-hosting
  organisation is a self-hoster, and paywalling SSO narrows the promise to individuals
  without anyone announcing it. Fails T2: Redis reports that the two-track split "split the
  developer experience and slowed progress on core Redis" [cited]. Replacement that passes:
  build SSO and audit into the core, sell the evidence pack and the attestation.
- **Skills marketplace revenue share.** Fails T4 — a percentage of price is not a function of
  serving cost — and T2, since it pays us to leave gaps in the free bundle.
- **Priority feature funding / bounties.** Fails T2: it pays us to leave things unbuilt.
  Sponsored *research* with a published-regardless rule passes; sponsored *features* do not.
- **Affiliate or referral revenue.** Fails T2 fatally *for this project specifically*: the
  central claim is measured routing, and money varying by destination disqualifies it.
- **Dual licensing.** Structurally impossible under MIT; the refusal is free.
- **Hardware.** Passes the tests; rejected on logistics for a sole trader [asserted].

---

## Unit economics at minimal margins

**Direct answer: minimal margins on goods do not fund maintenance, at any user count.**

Costs per active user per month. Storage is negligible: this repository's own durable state
measured 11,591,703 bytes over five days — 69.6 MB/month, $0.0626/month on Cloudflare R2
after five years [measured; R2 at $0.015/GB-month, cited]. Hosted inference on open weights
is cheap: gpt-oss-120b at $0.15/$0.60 per MTok gives $0.072 per cached agentic hour, against
$1.08 on Sonnet 5 at $2/$10 [simulated from cited prices]. Support dominates: derived from
Ghost and Plausible disclosures at a $120k loaded FTE, $4.36 and $1.90 per user per month
respectively [simulated].

Payment fees bite hardest at low ARPU: Paddle takes 18.1% of a £3 monthly charge and 5.7% of
the same £5/month billed annually [simulated from cited rate cards].

Contribution per user per month, Stripe monthly billing: £3 → **minus $1.10**; £5 → +$1.37,
requiring 7,307 users to fund one £95k maintainer; £10 → +$8.50, about 1,200 users; £20 →
+$19.89, about 503 users [simulated].

**The contradiction that must be resolved, not buried.** "At cost plus minimal margin" has a
benchmark: OpenRouter passes inference through with "no markup on inference pricing",
charging 5.5% ($0.80 minimum) on credit purchase [cited]; Cline sells "Model Inference at
Cost" [cited]. A £10/month flat fee funding a maintainer is not a 5.5% margin on anything.
It is a labour subscription wearing a pass-through label.

**Resolution:** two prices, named separately and never blended. **Goods** — inference,
storage, compute — pass through at supplier cost plus disclosed payment processing, capped
at OpenRouter's 5.5%, with per-job disclosure of supplier cost, charge and margin. **Hours**
— maintenance, support, assurance — are sold as hours, at a price that funds a person, and
described as exactly that. Anyone presenting both numbers as "minimal margin" is describing
one of them dishonestly.

**And the unasked question: nobody has established that anyone will pay.** Every comparable
has a named buyer with a job to be done [cited: Ghost $11.06m ARR / 30,557 customers;
Plausible $1m ARR / ~7,000 subscribers, team of four; Nabu Casa £65/year]. Consilient's buyer
is unnamed and demand is unestimated [measured: no such document exists]. Both comparables
land near $250k–$276k revenue per FTE [simulated], which is the constant to clear — but
clearing it needs customers nobody has counted.

---

## Licence and governance

**Stay MIT.** AGPL fails this case on retrieved evidence: §13 triggers only "if you modify
the Program" [cited], so an unmodified hosted competitor owes nothing, while Google's
published policy states AGPL code "MUST NOT be used at Google" and bars installing it on a
Google-issued laptop [cited, updated 10 Jun 2025] — and this is a laptop tool. That is
adoption cost paid for protection largely not delivered. Apache-2.0 is a defensible
alternative for its patent grant (§3) and trademark reservation (§6) [cited], free to adopt
today with one copyright holder and no external merges [measured]; it is a second-order
upgrade and declining it changes nothing else here.

**Drop the CLA. Use the DCO already in the repository** [measured: DCO and CONTRIBUTORS.md
exist; the ICLA and CCLA are drafts, not in force]. A rights-assigning CLA is the mechanism
that made the notable relicensings executable, and its absence is what makes relicensing
legally impractical rather than merely unpromised [asserted, from the case set]. Say so in
CONTRIBUTING.md: without one we *cannot* relicense a contribution — not as policy, but as
copyright law. The repository's own legal brief already frames the CLA as conditional on
whether the plan is a service around an MIT project or a derivative of it [measured]; the
plan is entirely the former.

**Governance: no foundation yet, and name the trigger.** Foundations expect several
maintainers and a released project; this has one and none [asserted]. Record now the
condition — second independent maintainer, or 180 days without a maintainer release — and
the named successor steward who receives trademark, domain and package namespaces. Until a
real party has agreed in writing, the honest description is: promises by one individual,
secured by the fork right MIT already grants.

**Trademark:** register "Consilient" — not "Consilience", which the legal brief still
commissions clearance on after the rename [measured] — with a published usage policy. It is
the only exclusive right a permissive licence leaves, and it is also a weapon in a
successor's hands, which is why the steward deed must license the *name* to a continuation
fork or the guarantee is hollow when it matters.

---

## The far-future cloud proposal

Cost-piping to cloud providers, with Consilient configuring and managing infrastructure and
charging a management margin. Queued far out. Documented so the later decision is cheap.

**Preconditions, all required.** (1) The accounts are the user's own, with Consilient
holding delegated IAM the user can revoke from their own console, and billing running
provider-to-user. (2) A reversibility proof for every provisioned resource before a penny is
charged. (3) A named, non-blended management fee — a risk premium is proportional to
variance, not to cost, so it cannot honestly be called "at cost" [asserted]. (4) Export and
teardown tested, not promised.

**Risk, plainly.** Whoever holds the account holds the data and the bill. A licence
rug-pull leaves a working fork; an account-holder rug-pull leaves a live production system
and an export problem [asserted]. The feature's appeal — the user never sees a console — is
exactly what makes exit impossible. If precondition (1) is ever waived, this route is a
hostage position and should be abandoned rather than softened.

---

## What would make us a cautionary tale

**The failure will be decay, not withdrawal, and every check proposed here would pass
throughout.** The router is free and hosted inference is the revenue; every hour of a user's
own quota the router schedules well is an hour not sold. Nobody deletes the router. A reset
window changes and the quota model lags two quarters. An adapter trails a release.
Free-path bugs sit while hosted-path bugs get fixed on Friday. Five years on, the free path
technically works and nobody uses it. Conformance runs, entitlement greps and manifest
ratchets all detect *presence*; none detects decay. The only counter proposed here is a
published quarterly figure — the share of active users on the zero-payment path — and it is
a lagging indicator [asserted].

**Support has the same signature.** At $4.36/user/month [simulated] it is the largest cost
line and it is unfunded for free users, so rational triage deprioritises them. That is a
two-tier product under an MIT licence, and no licence text fixes it.

**So does β-assurance.** If interpretation is the paid service, nothing advocates for β
output becoming self-explanatory. The documentation simply never gets written.

**Almost everything here rests on future good intentions.** The trademark is personally
held. The foundation is deferred to a condition that may never arrive. The ratchet test
lives in a repository whose owner can delete it in the same commit as the paywall; git
history deters only once forks exist, which is once the project is popular enough not to
need the protection. Ninety days' notice is a schedule, not a constraint.

**The pressure arrives as necessity, not greed.** At honest goods margins, solvency needs
either a per-seat tier — for which the evidence of working is clear [cited: GitLab
$29/user/month] — or abandonment. It will arrive in year two, and every promise above was
written by the person who will be under that pressure, with no customer yet counted.

---

## What is designed, not built

Nothing in this document is implemented. No commercial code exists [measured]. Build units,
each with a checkable done criterion:

1. **Demand test.** Ten interviews with named prospective users; a written buyer definition
   and a price they said aloud. *Done:* the document exists and names people. **This blocks
   everything below.**
2. **Free-path conformance run.** Full capability matrix with egress to Consilient hosts
   blocked and no account configured. *Done:* the CI job fails when one capability is made
   to require an account (mutation-checked).
3. **Capability manifest ratchet.** *Done:* CI fails when an entry present at the previous
   release tag is removed or marked paid.
4. **Entitlement import guard.** *Done:* an import-graph test fails when the core imports the
   billing module, transitively.
5. **Export round-trip.** *Done:* export → import on a clean machine → asserted equivalent,
   every release.
6. **Provider permission ledger.** *Done:* an adapter without a ledger entry fails the build.
7. **Margin ledger.** Per job: quoted ceiling, supplier actual, margin charged, refunded;
   monthly public aggregate. *Done:* a third party reconciles the published file against
   published supplier spend to zero.
8. **Free-path usage share.** *Done:* one published quarterly number.

---

## Open questions

1. **Who buys this, and at what price?** Unanswered, and it invalidates every arithmetic
   result above if the answer is nobody [measured: no demand evidence exists].
2. Does the Anthropic "explicitly permit" carve-out attach to the product or to the user's
   automated use? Unresolved on retrieved text [cited].
3. Google One and Google AI plan terms were not retrieved — the pages are client-rendered
   [cited: retrieval failure]. Google is unverified, not permitted.
4. OpenAI and xAI clauses reached this document via a text proxy in one research pass and a
   direct fetch in another; re-verify in a browser before public use [cited].
5. What detects decay rather than withdrawal? No mechanism proposed here does [asserted].
6. Does the named successor steward exist? No party has agreed [measured].
7. UK and EU VAT position for digital services sold to consumers: unretrieved [cited:
   retrieval failure]. Blocks any published price.
8. Is the hourly labour price defensible to a buyer who was told "minimal margins"? Untested.
9. Solicitor review: none of the legal documents in this repository is in force [measured].

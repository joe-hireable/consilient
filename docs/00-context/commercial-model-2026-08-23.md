# Commercial model — Consilient, 23 August 2026

- **Author:** CTO arm, for Joe Brown
- **Status:** DESIGNED, NOT BUILT. Nothing described here is implemented.
- **Evidence tags:** every claim carries one. `[cited]` = retrieved primary source, retrieval
  date 23 August 2026. `[measured]` = observed in this repository. `[asserted]` = my reasoning.
- **This document is not legal advice.** The instruments are named and quoted so a solicitor can
  be pointed at them, not so the naming can substitute for one. [asserted]

---

## What the principal asked for

In his words (21–23 August 2026): open source first, commercial second; "facilitating maximum
value for users, not profit"; teeny fractions of pennies on facilitated spend; bring everything
the user buys into one single monthly payment; manage the user's subscriptions and logins on
their behalf; possibly an ad model at scale; and, in capitals, **by practice never push certain
tools for commercial gain**. [cited — principal's own statement]

The binding constraint, also his: **no risk of it costing him anything not covered by the user
themselves.** He accepts making nothing. He does not accept uncovered exposure. [cited]

Two premises he supplied are not usable. He valued OpenRouter at $3.7bn; eight research arms
returned six mutually inconsistent figures for that company and none reproduced his. [asserted]
The repository's rule is *find the bar before claiming to beat it*, so there is no bar here and
no claim is made against one. Separately, OpenRouter's platform is proprietary — its public
repositories are SDKs — so it is not evidence about open-source-first commerce either. [cited]

---

## Is a zero-risk model possible?

**No. A genuinely zero-risk commercial model does not exist for this product, and he is already
carrying the largest single risk today, unpaid.** [asserted]

Consilient orchestrates an agent that spends the user's money on the user's own credentials. An
agent that provisions a GPU instance and loops overnight can burn thousands of pounds that never
touch him. Custody is not the test. Under Consumer Rights Act 2015 s.49 a service must be
performed with reasonable care and skill, and that term cannot be excluded against a consumer
[cited]. He charges nothing, which removes the trader question but not the causation. Every
revenue structure below is scaffolding around a risk that exists in the repository as it stands.
[asserted]

Of the revenue structures, one is close to risk-free — **sponsorship**, where money arrives as a
gift with no product attached and GitHub is the payer of record at 0% on personal sponsorships
[cited]. Referral is *cheap*, not free, and its price is not the clawback: it is that the first
commission plausibly makes him a trader under CRA 2015 s.2 — "a person acting for purposes
relating to that person's trade, business, craft or profession" [cited] — with consumer-law and
disclosure duties attaching to the whole product, for every user, permanently. £25 buys unlimited
consumer-law surface. That is the decision, and it should be taken deliberately. [asserted]

---

## The revenue routes, ranked

Ranked by expected value net of exposure, not by headline size. [asserted]

**1. Sponsorship and grants.** Mechanism: users and companies fund the maintainer, not the
product. GitHub Sponsors takes 0% on personal sponsorships; Open Source Collective is the same
idea with a fiscal host taking a fixed 10% and carrying the legal entity [cited]. Money flows
sponsor → GitHub → him. He never touches user funds, sells nothing, and — subject to advice —
does not become a trader in respect of the software. Residual: income is taxable; sponsorship of
open-source projects is typically small; a fiscal host removes personal liability at 10%.

**2. A hosted service he sells himself, through a merchant of record.** Mechanism: he sells his
own operation of the software — hosting, relay, support — and a merchant of record is the legal
seller. Paddle: 5% + 50¢ per checkout, inclusive of tax registration, filing and remittance
[cited]. Money flows user → Paddle → him. Residual, and it is real: Paddle §10.4 entitles it to
recover refunds and chargeback fees from him, and §§8.1–8.3 permit set-off without notice
[cited]. A merchant of record moves him behind the money; it does not remove him from it. The
50¢ floor also makes sub-£3 pricing unworkable [cited], which forecloses "teeny fractions of
pennies" on this route.

**3. Referral, at a flat published rate.** Mechanism: the user buys direct from the provider on
their own card; the provider pays commission afterwards. He never holds funds. Rates are patchy
to absent in the categories he cares about: Anthropic's Commercial Terms prohibit resale "except
as expressly approved by Anthropic", Twilio's prohibit making the services available to third
parties, and AWS, GCP and Azure publish no third-party referral rate at all [cited]. Residual:
clawback on refund and churn can leave a negative balance owed to the network [asserted];
disclosure at the point of recommendation is mandatory under DMCC Act 2024 Sch 20 para 12, in
force 6 April 2025 [cited]; and trader status attaches. **This route also contradicts the
principle in capitals — see Advertising.** [asserted]

**4. Bring-your-own-key orchestration.** Mechanism: the user holds the provider account and pays
the provider. Earns nothing directly [asserted]. Listed because it is the substrate the other
routes sit on and because it keeps him out of the resale prohibitions above [cited].

**5. Consolidated monthly billing. Dead.** See The money path.

**6. Advertising. Dead.** See Advertising.

**Recommendation: routes 1 and 2. Route 3 only if the principle in capitals is rewritten first,
explicitly and in public.** [asserted]

---

## The money path

**Route 1.** Sponsor's card → GitHub or the fiscal host → his account. He is not a payee for any
service supplied to the sponsor. No payment service is provided. [asserted]

**Route 2.** User's card → Paddle (seller of record) → periodic payout to him, net of 5% + 50¢
and net of any set-off under §§8.1–8.3 [cited]. He is the supplier of the underlying service and
therefore the trader for consumer-law purposes whatever the merchant of record does [asserted].
DMCC Act 2024 ss.256–271 attach the moment the plan recurs: pre-contract information, reminder
notices, a cancellation route that is "straightforward, and without having to take any steps
which are not reasonably necessary", 14-day cooling-off, with criminal penalties on the
off-premises limb [cited].

**Why route 5 is dead.** Collecting one payment and paying third parties is execution of payment
transactions or money remittance under PSRs 2017 Sch 1 Pt 1 [cited]. The exclusion he would need
is Sch 1 Pt 2 para 2(b): a commercial agent acting "on behalf of either the payer or the payee
**but not both the payer and the payee**" [cited]. FCA PERG 15.5 Q33A gives as its example of
losing that exclusion a platform that "allows a payer to transfer funds into an account that it
controls or manages, but this does not constitute settlement of the payer's debt to the payee,
and then the platform transfers corresponding amounts to the payee" [cited]. That is the feature,
described by the regulator. Providing payment services unauthorised is an offence under reg 138,
up to two years on indictment [cited]; doing it lawfully requires €125,000 initial capital for
execution of payment transactions under Sch 3 Pt 1 [cited]. A stored balance spendable at third
parties is separately electronic money under EMR 2011 reg 2(1) limb (b), "accepted by a person
other than the electronic money issuer" [cited]. And HMRC's deemed-supplier test makes whoever
"authorise[s] the charge to the consumer" the supplier for VAT on the **gross** value of every
third-party subscription passing through [cited] — a liability that lands whether or not he
profits. Four independent walls, any one of which is sufficient. [asserted]

**Solicitor required, before anything is built, on:** whether sponsorship income leaves him
outside trader status; whether route 2's merchant-of-record structure changes his consumer-law
position; and the perimeter position of any design that touches user funds. An hour on a narrow
question is cheap; an hour on "can I build bundled billing" is wasted, because the answer above
is already no. [asserted]

---

## Credentials: the recommendation

**Do not hold them. Not passwords, not a zero-knowledge vault, and not a server-side store of
OAuth refresh tokens.** [asserted]

The usual argument is LastPass: a genuine zero-knowledge architecture, breached via engineer
endpoints, unencrypted metadata and URLs in the stolen backup, an ICO monetary penalty of
approximately £1.2m against the UK entity in late 2025, and a $24.5m US class settlement [cited —
briefs disagree on the penalty date; the amount is consistent]. That is a good argument and it is
not the one that decides it for him.

The deciding argument is one sentence: **he cannot patch on a schedule.** He is one person. If he
is ill, or busy, or bored, a stored secret stays exposed with nobody rotating it. That kills the
vault, and it kills the token store too, because a refresh token is a bearer credential with a
shorter fuse rather than an exemption. [asserted]

**What is lost.** More than the OAuth answer usually admits. There is no delegated scope for
"cancel my Netflix". Anthropic's Admin API is documented as "unavailable for individual accounts"
and exposes no billing or cancellation endpoint at all [cited]. Stripe's Customer Portal sessions
can be created only by the merchant, expire in five minutes, and cannot be displayed in an iframe
[cited]. Apple's App Store Server API cannot cancel a subscription [cited]. So programmatic
subscription management is not a gap waiting for OAuth to fill it; the enabling interface does not
exist for third parties. **OAuth and passkeys do not recover the capability. Nothing recovers it
short of holding a password and driving a browser, which is the thing being refused.** [asserted]

What OAuth does recover is read-only visibility where a provider offers it, and authentication
without a shared secret. Where a provider offers neither, the integration should not exist —
refusing an integration is free. [asserted]

---

## Subscription aggregation

The single monthly bill does not survive the analysis above. A merchant of record does not rescue
it: Paddle at 5% + 50¢ makes Paddle the seller of **his** product, not a conduit to Netflix
[cited], and the 50¢ floor is 17% of a £3 charge [asserted].

**The retreat position is also unsafe, and this is the part five of eight research arms missed.**
The "read-only dashboard that mines the user's inbox for receipts" requires a Google restricted
scope, which carries a mandatory annual third-party security assessment payable before launch by a
sole trader with no revenue [asserted — cost unquantified, see Open questions]. It makes him a
data controller over a subscription graph that reveals health, sexuality, politics and finances,
with a UK GDPR Art 35 DPIA, Art 32 duties and 72-hour breach notification [asserted]. And it
cannot deliver the headline feature anyway, because of the missing APIs above [cited]. It is the
most heavily regulated item on the list [asserted] and it was proposed as the safe option. Do not
build it.

**Demand.** Parliament legislated for subscription harm in DMCC Act 2024 Part 4 Chapter 2, which
is evidence a legislature judged the problem real [cited]. No survey figure for its size was
verified by any research arm; every number offered was second-hand [asserted]. So: real enough to
legislate for, unquantified here, and not a market this project has a route into.

---

## Advertising

**Advertising and "never push certain tools for commercial gain" cannot both hold. Advertising
goes.** Advertising is the sale of placement; the principle is the promise not to sell placement.
In an agent the contradiction is sharper than in a search engine, because the user is shown one
answer rather than a labelled list. [asserted] UK law reinforces rather than resolves it: DMCC Act
2024 Sch 20 para 12 makes undisclosed paid promotion a banned practice in all circumstances
[cited].

**A flat, equal, published affiliate rate does not resolve it either, and the claim that it does
should be refused.** The argument is that identical rates across a category remove the incentive
to prefer one tool. Two defects. First, whoever draws the category boundary and decides who is
inside it holds every scrap of the discretion the equal rate was meant to remove; Amazon's own
uniform category table already carries a brand-level 0.00% carve-out [cited]. Second, and
decisive: income that varies with *whether the user adopts a paid tool at all* is still a
commercial interest in tool adoption. Fixing the price of the influence is still a price.
[asserted]

So either the affiliate revenue goes, or the sentence in capitals is rewritten. The honest
rewrite, if he wants the revenue, is: *"commission is disclosed at the point of recommendation and
never an input to ranking"* — a weaker promise than the one he made, and he should say so himself
rather than have it quietly narrowed. [asserted]

---

## The autonomy ladder for spending

Anchored in controls that exist, not in policy sentences. [asserted]

**Tier 0 — read-only, no confirmation.** List, compare, price, draft. No instrument attached.
Control: scope. Sufficient. [asserted]

**Tier 1 — spend under a hard ceiling, no confirmation.** Control: a user-set spend ceiling
enforced **client-side, in the call path, before any provisioning request is issued**, plus a
per-purchase delegated token carrying its own maximum amount and expiry. The token pattern is
shipped: the Agentic Commerce Protocol states "OpenAI is not the merchant of record" and issues a
single-use token "restricted by the delegated payment's max amount and expiry" [cited]. Ceiling
enforcement is the control that matters and it is a day's work. [asserted]

**Tier 2 — one confirmation per purchase.** Any first purchase from a new provider, any recurring
commitment, any spend above the Tier 1 ceiling, any raise to the ceiling.

**Tier 3 — never automated, whatever the user's stated preference.** Entering a credential.
Anything with open-ended or unmetered liability. Anything binding beyond the purchase — notice
periods, minimum terms, auto-renew at a changed price.

**The ceiling is not absolute and he should not claim it is.** Card-level controls leak by their
vendor's own documentation: Stripe records up to 30 seconds of spend-aggregation delay, later-
posted fees exceeding a limit, and cases where "Stripe declines an authorization but can't
communicate with the card network, and the network approves" it [cited]. A ceiling enforced before
the provisioning call avoids the card path entirely for the cases Consilient controls, and is
therefore the stronger of the two [asserted].

---

## Risk register

Ordered by expected loss. Control sufficiency stated honestly. [asserted]

| # | Risk | Mechanism | Scenario | Control | Sufficient? |
|---|------|-----------|----------|---------|-------------|
| 1 | Agent burns the user's money | Orchestration causes spend on the user's own key; CRA 2015 s.49 is non-excludable against consumers [cited] | £2,000 of GPU overnight; user asks him to cover it | Hard client-side ceiling before provisioning, plus confirmation above a low threshold | **Reduces.** Exposure survives; it is live today [asserted] |
| 2 | His own infrastructure and inference bill | Cost scales with adoption; revenue does not | Free product succeeds; monthly invoice grows | Local-first execution; per-user cost cap; degrade or refuse on breach | Sufficient if the cap is enforced, not aspirational [asserted] |
| 3 | Restricted-scope audit cost | Google restricted scopes require an annual third-party assessment before launch | Inbox dashboard blocked pre-launch by an unbudgeted four-figure bill | Do not build inbox mining | Sufficient [asserted] |
| 4 | Trader status on first commission | CRA 2015 s.2; DMCC Sch 20; cancellation rights [cited] | One £25 cheque attaches consumer duties to the whole product | Take no commission, or accept and comply deliberately | Sufficient either way once chosen [asserted] |
| 5 | VAT as deemed supplier | HMRC: whoever authorises the charge is the supplier, on gross [cited] | £2.4m of pass-through, ~£400k output VAT, no matching input VAT | Never aggregate third-party purchases | Sufficient — removes the fact pattern [asserted] |
| 6 | Data-controller liability | Any hosted state; UK GDPR Arts 32, 33, 35 [cited] | Token or spend-graph breach; 72-hour notification | Hold nothing server-side; derived data only | Reduces [asserted] |
| 7 | Chargebacks and set-off | Paddle §10.4 recovery, §§8.1–8.3 set-off; Stripe SSA 7.2(c) reaches the user bank account [cited] | Disputes on his own paid tier debit his account | Sell nothing under £3; 3-D Secure; low volume | Reduces [asserted] |
| 8 | Affiliate clawback | Reversal on refund or churn creates a negative balance owed | Cohort churns; network invoices him | Treat commission as cash on receipt; never accrue | Reduces [asserted] |
| 9 | Personal unlimited liability | Sole trader | Any claim reaches personal assets | Incorporate before first revenue; no personal guarantees | Reduces — Insolvency Act 1986 s.214 permits a personal contribution order [cited] |
| 10 | Solo continuity | One maintainer, no rota | Illness; stored secrets unrotated | Minimise stored surface so the service can be abandoned safely | Reduces; no control removes it [asserted] |
| 11 | Scope creep back into the forbidden designs | "Just cache the key"; "just hold a small balance" | The rejected design is reimplemented by increments | Enforcement rules below | Sufficient only once the checks exist [asserted] |

**Enforcement rules.** This repository holds that a chokepoint without an enforcement rule is not
a chokepoint. Four prohibitions, four checks, none of which exists yet [measured]:

- `check_no_funds_custody.py` — fails on any persisted user-balance field or payment-collection
  dependency.
- `check_no_credential_store.py` — fails on any persisted secret or token field outside the
  user's own machine.
- `check_spend_ceiling.py` — fails if any provisioning call site does not route through the
  ceiling.
- `check_no_paid_placement.py` — fails if any commission or rate field is reachable from ranking
  inputs.

Until these run in `invariants.yml`, the prohibitions in this document are prose. [asserted]

---

## What is designed, not built

**None of this is implemented.** [measured] No commercial code exists in this repository; the
package is standard-library-only with no server [measured].

Units required, if and when he chooses to act:

1. An ADR recording the four prohibitions and the trader-status decision, superseding the
   commercial portion of ADR-0024.
2. The four check scripts above, wired into `invariants.yml`.
3. The Tier 1 spend ceiling in the provisioning path, with its test.
4. One hour of a solicitor's time on the three questions named in The money path.

Items 2 and 3 are worth doing whether or not any revenue route is ever taken, because risk 1 is
live now. [asserted]

---

## Open questions

- **The OpenRouter figure.** Six research arms produced six inconsistent valuations. No bar has
  been established and none is claimed. Resolving it requires one primary source, not another
  model. [asserted]
- **The restricted-scope assessment cost.** Named as a risk with no figure attached. It is moot
  if the inbox dashboard is not built. [asserted]
- **Insurance appetite.** Whether any UK insurer will write cyber or professional indemnity cover
  for a sole trader operating autonomous agents against third-party accounts, and at what price,
  was not established by any arm. A broker, not a search. [asserted]
- **Demand size.** Legislated-for, unquantified here. [asserted]
- **Whether sponsorship keeps him outside trader status.** Solicitor. [asserted]
- **Raised by the critic and not answered here:** whether the equal-rate affiliate argument has
  any surviving form (I say no; that is my judgement, not a retrieved finding); and the precise
  boundary at which orchestration becomes a "service" under CRA 2015 for a product supplied free.
  [asserted]

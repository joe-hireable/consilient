# Commercial strategy — the maintainer's critic, 23 August 2026

The strategy document is `commercial-strategy-2026-08-23.md`. This is the adversarial review of
it, written from the position of an open-source maintainer who has watched projects betray their
communities. It is kept separately and unedited because its findings are the ones most likely to
be softened later.

**Its central claim, and the one to answer first:** every enforcement mechanism proposed detects
*presence* and none detects *decay* — and decay is the failure that actually happens.

---

**1 — The route that degrades the free path: hosted inference, degrading the router.**

- The router is the free core. Hosted inference is the only scalable revenue. Every hour of a user's own Max quota that the router successfully schedules is an hour of hosted inference not sold. Revenue is *inversely proportional to how well the flagship free feature works.*
- Mechanism, unannounced: nobody deletes the router. Anthropic changes a reset window; the quota model isn't updated for two quarters. An adapter lags a release. Edge-case bugs sit in the backlog while hosted-path bugs get fixed Friday. Five years on the BYO path technically works and nobody uses it.
- **Every proposed check passes throughout.** The unplugged test, the entitlement grep, the manifest ratchet, C5/C6 — all detect *presence*, none detect *decay*. Seven researchers proposed enforcement for the one failure mode that has never actually happened, and none for the one that always does.
- Same signature on support ($4.36/user/mo, the largest cost line, unfunded for free users → rational triage deprioritises them) and on β-assurance (if interpretation is the paid service, β output has no advocate for becoming self-explanatory; the docs simply never get written).

**2 — Where it rests on future good intentions: nearly everywhere.**

- CLA drafted and live-optional. Trademark personally held. Foundation "revisit at second maintainer" — i.e. never, since there is one maintainer and no release. C11's named steward is a recommendation, not a signature.
- The DMCCA s.226 device requires the trader to *assert* compliance. He stops asserting; the statute switches off. It binds nothing.
- The ratchet test lives in a repo its author controls; the paywall commit and the test-deletion commit are the same commit. Git history deters only if forks exist — i.e. only when the project is popular enough not to need the protection.
- 90-day notice was correctly identified as "a schedule, not a constraint" and then recommended anyway by the same researcher.

**3 — Orchestration: yes, the ambiguity is resolved in the project's favour.**

- Anthropic §3 permits automated access "via an API key or where we otherwise explicitly permit it." The permission attaches to Claude Code *as a product*. No retrieved clause says a third party may drive it headlessly across several accounts. Two researchers admitted this; the composite then treats it as settled.
- The strongest counter-evidence — the Agent SDK help article — is a **support page, editable in an afternoon**, and it says credits "can't be pooled, transferred, or shared." Cross-account quota arbitrage is what pooling looks like from outside, whoever owns the accounts.
- If one provider closes it: it closes for *every user simultaneously* by terms change. Free path still runs, becomes expensive overnight, and hosted inference — the paid path — is the only affordable route left. The promise degrades in the paid path's favour with nobody deciding anything. No researcher costed that contingency.
- The repo's own audit says Gate B is shut and no Claude dispatch has succeeded. The differentiator is unbuilt and unproven, and the whole pricing case rests on it.

**4 — It does not fund a maintainer, and the set contradicts itself.**

- £3 = negative contribution at any scale. £5 = 7,307 users. £10 = ~1,200.
- Meanwhile two researchers cap margin at ≤5.5% (OpenRouter) against Cline at 0%. **The £10 subscription *is* the margin.** A flat fee funding a maintainer is not "at cost plus minimal margin" by any benchmark cited — it's a services business wearing a pass-through label. Nobody reconciled the two recommendations; they appear in the same package.
- So the failure is priced in: at honest margins, solvency requires either a seat tier (GitLab, $29/user, proven) or abandonment. That arrives as necessity, not greed, in year two, exactly as predicted, and every promise here was written by the person who'll be under that pressure.

**5 — What all seven missed.**

- **Nobody asked whether anyone will pay.** Zero demand evidence. Every comparable (Ghost, Plausible, Sidekiq, Nabu Casa) has an identified buyer with a job to be done. Consilient's buyer is unnamed. Seven researchers modelled unit economics on a customer count that has never been estimated.
- All seven accepted "minimal margin" as coherent. It isn't: margin on *what basis* — inference tokens, or the maintainer's hours? The first funds nothing; the second isn't minimal.
- All seven took provider terms as the binding constraint. The binding constraint is that a solo maintainer in England is choosing to forgo the only revenue model in this category proven to work, without a customer, without a demand test, and without a foundation. That's a preference, not a strategy — and it should be written down as one.

# Observability, steering and embodiment — the adversarial critic, 23 August 2026

The design is `observability-steering-and-embodiment-2026-08-23.md`. This is the review that
attacked it, kept separately and unedited because these are the findings most likely to be
softened once someone wants to ship.

**Read these three first.**

1. The outbound broker is a single trusted process that reads agent-supplied recipients and holds
   every credential. The taint flag must be **derived by the broker from the caller's own
   capability record, never accepted as a parameter** — otherwise it is a caller-declared author
   string, which this repository has already refused once.
2. **An allowlisted recipient with an attacker-drafted payload has no control at all.** Injected
   text, a genuinely allowlisted recipient, allowlist passes, volume cap passes, disclosure plays,
   and the harm lands. Named as the likeliest real incident.
3. **The reversibility classifier is undecidable over shell.** `bash` is class 2 by the table and
   `curl` is class 4. Either shell is class 4 wholesale, or the classifier is a guess.

And the meta-finding, which applies to every sweep run today: nine angles returning the same
shape — a bar, a falsifiable metric, a self-objection, an evidence confessional — is **format
convergence from a shared base model, not corroboration.** Nine agreements on one shape are one
opinion. That is this project's own echo rule, turned on its own research method.

---

**1. The most dangerous thing: the outbound broker is a single trusted process that both reads agent-supplied recipients and holds every credential.**
- The design's central control (§R2, §1.3) is "one outbound broker for all channels." That broker takes `to`, `body`, `grant_id` from an agent. A tainted agent that cannot *call* Twilio can still *ask* the broker to. Taint demotes the caller — but the broker is the only thing that checks taint, and it checks a flag the caller's runtime asserts. That's the same class as "a caller-declared author string is not authentication," which the repo already refused (`observability-graphs.md`). **The taint flag must be derived by the broker from the process's own capability record, never accepted as a parameter.** The design never says this.
- Worse: the recipient allowlist is the whole defence, and the attacker controls the *content*, not just the address. Injected text → agent mails a genuinely allowlisted recipient (the user's accountant) with an attacker-drafted instruction. Allowlist passes. Volume cap passes. Disclosure preamble plays. Everything works exactly as designed and the harm lands. There is no control here at all for allowlisted-recipient-with-attacker-payload, and it is the likeliest real incident.
- The pre-rendered disclosure hash is genuinely good and I'd keep it.

**2. Where "solvable now" is quietly load-bearing on an open problem.**
- §R4 marks CaMeL-style capability checks **DESIGN**. CaMeL bought its guarantee by removing the model's authority over control flow, at 84%→77% utility. This design keeps a conversational orchestrator with free control flow and bolts capability checks onto tool calls. That is not CaMeL; it is a tainted-data allowlist with CaMeL's citation attached. Mark it OPEN.
- §4.4's tier table is the same move: it presumes the reversibility classifier can *see* the class of an action before it happens. Class 4 (`external`) is only knowable if the tool surface is closed. A `bash` call is class 2 by the table — and `curl` is class 4. **The classifier is undecidable over shell.** So "shell = class 2, not-confirmed" is a hole big enough for every R1 scenario. Either shell is class 4 wholesale (killing the zero-click path for anything with a terminal) or the classifier is a guess.
- §R12 taint transitivity is marked DESIGN with the residual OPEN. Fine — but every other control in the document rests on transitivity working, so the residual is load-bearing, not marginal.

**3. Cannot be driven by chat alone.**
- **S3's BubbleUp selection.** "Select these cells, tell me what they share" has no utterance. You can say "why did the stalled items stall" — but the *selection* is the query, and selection is spatial. Either the orchestrator must accept a predicate ("items that failed twice in the last day") as the selection primitive, or S3 is click-only and Principle 3 is violated on its own flagship feature.
- **§4.4's Checked tier is self-defeating.** "Say the word *staging*" is a spoken token — an ASR error produces it or fails to. The whole point was that voice is untrustworthy. A readback token doesn't fix an untrustworthy channel; it just makes the failure rarer and less legible.
- Settings' `@modified` diff-review is chat-hostile for the same reason: reading a diff aloud is worse than not reading it.

**4. Where a lawyer stops it, and where the design is not honest.**
- Honest: EU AI Act Art. 50 dates, TCPA arithmetic, PECR, Twilio AUP end-user inheritance. Good.
- **Not honest: UK GDPR.** Only one research angle raised controller obligations and neither design document has a data-protection section. The observability store retains third-party communications content — inbound mail, call transcripts, SMS from people who never consented. That is processing personal data of non-users, with lawful basis, retention, DSAR and (for voice) special-category risk attaching. The four-year TCPA retention is asserted-unverified *and* collides head-on with GDPR minimisation. A lawyer stops shipping here before they stop the dialler.
- **Not honest: §1.5 says telephony via the user's own credentials is "their AUP responsibility."** Twilio's AUP makes the *customer* responsible for end users. If we ship the module and market the capability, "it's their account" is a position, not a defence.

**5. What all nine researchers missed (shared base model, shared brief).**
- Every angle produced: a bar, a falsifiable metric, an "objection I'll make myself," and an evidence-quality confessional. That's format convergence, not corroboration. Nine agreements on the same shape is one opinion.
- Concretely missed by all nine: **inbound**. Every threat model, every disclosure control, every consent artefact is outbound. Agents with numbers and mailboxes *receive* — cold calls, spam, phishing, subpoenas, opt-out requests ("STOP"), and DSARs. Nothing in either document handles an inbound STOP, which is a TCPA/PECR obligation with the same damages as the outbound side.
- Also missed by all nine: **who pays when an agent is wrong but not compromised.** Every risk is adversarial. There's no register entry for a competent, uninjected agent that simply emails the wrong number.

**6. Prepaid: where the operator still carries financial risk.**
- Named already: chargebacks. Real, but not the interesting one.
- **The unnamed one: the pause snapshot is a liability we sell at a fixed price and hold at a variable cost.** §3.2 prepays 30 days of snapshot storage out of the grant. At T+30 the credit is spent and the data still exists. Deleting it destroys a paying customer's work; retaining it is unfunded storage on our account, indefinitely, at whatever the provider charges next year. The design fixes rates "at redemption" for compute and says nothing about storage. Multiply by every abandoned run. That is a slowly compounding balance-sheet item with no exit that isn't a support incident.
- Second: **the no-artefact auto-return (§3.4) is a free-compute oracle.** Produce zero declared output bytes and the credit returns automatically, as a rule, without judgement. Mining, scraping, model-stealing — all produce zero *declared* artefacts. The abuse control (§R-egress) is an allowlist; the refund control is unconditional. Someone will find this within a week of launch.

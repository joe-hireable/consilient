# Brief for legal review

**These documents are drafts prepared by an AI assistant. They are not legal advice and the
drafter is not a solicitor. Nothing here is in force. Do not publish, and do not ask anyone
to sign, until a qualified solicitor has reviewed and approved them.**

## Documents in scope

| File | What it is | Basis |
|---|---|---|
| `/LICENSE` | MIT, © 2026 Joseph Brown | Unmodified OSI text |
| `/DCO` | Developer Certificate of Origin 1.1 | Verbatim; permitted and required to be unmodified |
| `/CONTRIBUTING.md` | Contributor-facing process | — |
| `docs/legal/ICLA.md` | Individual Contributor Licence Agreement | Apache ICLA v2.0, amended for English law |
| `docs/legal/CCLA.md` | Corporate Contributor Licence Agreement | Apache CCLA v1.0, amended for English law |
| `docs/legal/RELICENSING-PROMISE.md` | Binding commitments incorporated into both CLAs | Original |

## Commercial context the reviewer needs

Project name: **Consilience** (`joe-hireable/consilience`), fixed 19 Aug 2026 by ADR-0008.
**A trademark search on that name has not been carried out and is part of this instruction.**

Solo maintainer, England. Intent: build an open-source community first; a separate
commercial venture may follow later, possibly a hosted or simplified derivative of this
codebase. **The CLA exists to preserve that option**, because MIT lets the maintainer
relicense his own code but not anyone else's. The Relicensing Promise exists to make the
CLA politically acceptable to a community that is rightly suspicious of them.

The commercial plan is not settled. The drafting therefore aims to preserve optionality
cheaply rather than to serve a specific known structure.

## Amendments made to the Apache templates, and why

1. **Governing law and jurisdiction: England and Wales** (ICLA cl. 9.7–9.8). Apache's is
   silent, which is workable for a US foundation and poor for an English individual.
2. **Moral rights waiver** (ICLA cl. 4). Absent from the Apache templates because US law has
   no meaningful equivalent. Added with an express reference to ss. 77–85 CDPA 1988 and a
   non-assertion fallback for jurisdictions where waiver is ineffective.
3. **Contracts (Rights of Third Parties) Act 1999** (ICLA cl. 9.2). Excluded generally, with
   a carve-out so downstream recipients can enforce the licence grants — which they must be
   able to do for the grant to function.
4. **Explicit relicensing wording** (ICLA cl. 2.1–2.2). Apache's grant is broad enough to
   imply this; here it is stated in terms so no contributor can say they did not understand
   what they were granting.
5. **Successors and assigns** (ICLA cl. 9.1). Added so the benefit can transfer to a company
   later without re-papering every contributor — see open question Q1 below.
6. **Non-retrospective variation** (ICLA cl. 9.4). Amendments bind only future contributions.
7. **UK GDPR clause** (ICLA cl. 10). Absent from Apache. Purpose, lawful basis, publication
   in git history, retention.
8. **Relicensing Promise incorporated by reference** into both CLAs (ICLA cl. 2.4, CCLA
   cl. 2). This is the unusual one and the one most needing scrutiny — see Q3.

## Open questions for the reviewer

**Q1 — Counterparty.** Drafted with Joseph Brown as an individual, on the assumption the
project is personal rather than a Hireable Ltd asset. Should it be the individual or a
company? Clause 9.1 (assignment) is intended to make a later transfer possible without
re-papering, but please confirm that works, and confirm there is no conflict with any
existing Hireable Ltd IP assignment or employment/contractor arrangement.

**Q2 — CLA or DCO alone?** The commercial plan is unsettled. If it will only ever be a
*service around* an MIT project, no CLA is needed at all and dropping it is a genuine
community asset. If a *derivative* is possible, the CLA is necessary and must be in place
before the first external merge. Please advise on how firmly the decision needs to be made
now versus how recoverable it is later. Our understanding is that it is effectively
unrecoverable, which is why it is being drafted at this stage.

**Q3 — Is the Relicensing Promise enforceable as drafted?** It is incorporated by reference
into a contract accepted by clickwrap. Questions: (a) is incorporation by reference to a
file in a git repository sufficiently certain, given the file can change? Clause 6 attempts
to fix this by binding each contribution to the version in force at submission — is that
adequate? (b) does clause 7 (promise transfers with the project) actually bind a transferee,
or does it merely oblige the maintainer to obtain their agreement? (c) does making the
promise contractual rather than aspirational create any unintended exposure — e.g. does
commitment 5 (90 days' notice) or commitment 1 (permanence) constrain a future sale in ways
that would concern an acquirer?

**Q4 — Clickwrap formation.** Acceptance is via a CLA-assistant-style bot. Is that
sufficient for formation and evidencing under English law? Consideration: what is the
maintainer giving? Apache-style CLAs generally rely on the licence being a deed or on
nominal mutual obligation. Should this be executed as a deed instead? This may be the most
important technical point in the whole review.

**Q5 — Consumer status.** Some contributors will be individuals acting outside a trade or
profession. Does the Consumer Rights Act 2015 apply, and if so, do any terms (particularly
the moral rights waiver, the exclusive jurisdiction clause, and the unilateral variation
right at cl. 9.4) risk being unfair terms?

**Q6 — Minors.** Open-source projects receive contributions from under-18s. Should there be
an age gate, a parental-consent route, or an express exclusion?

**Q7 — Overseas contributors.** Exclusive English jurisdiction (cl. 9.8) may be unenforceable
against EU-domiciled consumers under Brussels Recast. Is a non-exclusive clause preferable?

**Q8 — GDPR (cl. 10).** Is the lawful basis correctly stated? Is there an ICO registration
obligation for a sole trader maintaining a contributor register? Is the retention period
adequately defined?

**Q9 — Warranty exposure.** ICLA cl. 5 makes contributors warrant non-infringement to the
best of their knowledge. Is that enforceable and proportionate, and does it expose the
maintainer to any duty to verify?

**Q10 — Interaction between DCO and CLA.** Both are required. Is running both redundant,
contradictory, or complementary? Some projects run one or the other. Our view is
complementary — DCO for per-commit provenance, CLA for the relicensing right — but please
confirm they do not conflict.

**Q11 — Trademark clearance on "Consilience".** It is a common English word (Whewell 1840;
Wilson 1998), which we assume makes it hard for anyone to have locked up in software and
equally hard for us to protect. Please confirm: (a) any conflicting registered mark in the
relevant classes in the UK, EU and US; (b) whether any protection is worth seeking at all
for a donation-funded open-source project, or whether unregistered rights suffice; (c) any
risk from the package names `consilience` and `consil` on npm, PyPI, crates.io and
Homebrew. A rename after publication would be costly, so this is time-sensitive.

## What "approved" looks like

We are not asking for a redraft from scratch. We are asking for: the ten questions above
answered, any clause that would not survive challenge in an English court identified and
fixed, and a clear yes/no on Q4 (deed vs simple contract) since that may change the
execution mechanism entirely.

## Attribution note

The ICLA and CCLA are adapted from the Apache Software Foundation's templates, which the ASF
makes available for reuse. Please confirm the adaptation and attribution are handled
correctly.

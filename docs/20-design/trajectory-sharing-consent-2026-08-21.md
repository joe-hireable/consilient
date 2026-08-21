# Trajectory sharing by consent — design, not a pipeline

**Date:** 21 August 2026
**Status:** design of the unimplemented second half of ADR-0057. **No sharing
pipeline ships in this commit.** Consent can now be *recorded* as a principal-authored
event; nothing in this repository transmits a trajectory.
**Companion to:** [`../decisions/0057-a-users-trajectory-is-their-data.md`](../decisions/0057-a-users-trajectory-is-their-data.md).
Does not supersede it. Does not implement ADR-0024 (still PROPOSED).

The brief that commissioned this said a shipped test pins `consil` to
`{record, replay, beta, doctor}`. That is stale. The pin is
`{record, replay, beta, doctor, dashboard, usage}`
(`[measured]` — `tests/test_v0_invariants.py::test_the_cli_exposes_no_routing_or_blocking_surface`).
This design adds **no** CLI subcommand. The recall pack attached to that brief was leftover
from unrelated jobboard and hireable dispatches and is not evidence for anything here.

---

## Why this document exists

ADR-0057 is ACCEPTED. The first half is implemented: `.harness/log/` is gitignored, and
`test_no_user_trajectory_is_tracked` fails CI if a log file is tracked. [measured]

The second half is a promise the code does not keep:

> unless they agree to share data in which case that is private and used to improve
> consilient only

There is no consent mechanism, no stated retention period, and no way for a user to
*check* the use limit rather than trust it. The ADR forbids shipping a sharing feature
until those exist, because shipping one would make the ADR describe a promise the code
does not keep — the defect this project catalogues under its own name.

This document is those three things, designed. It is not the feature.

Two constraints are absolute and shape every section below:

1. **No secret may ever reach a public repository.** Joe, 20 August 2026: not merely "do
   not commit one", but do not place one anywhere a public repository can reach.
   Shared data therefore cannot live in this repository, cannot travel via Actions
   secrets, and cannot be the payload of a GitHub-hosted intake. [cited] ADR-0046,
   ADR-0048.
2. **Consent is a human decision.** Under V0-18 only the principal may author it. An
   agent may never record a user's consent on their behalf. The same early-return hole
   that let an agent author a `human_verdict` would, if reproduced here, let an agent
   author a share grant — and then β computed from shared trajectories would rest on
   forged permission. [measured] — the verdict hole, 20 August 2026.

A third constraint is almost as load-bearing: **this project's thesis is that
convergence is a test, and tests have error rates.** A sharing design that asks the user
to *trust* the use-limit is the thesis applied to everyone except us. The checkable
claims and the policy claims are therefore listed separately, and the design is not
allowed to present the second as the first.

---

## Scope: ADR-0057, not ADR-0024

ADR-0057 grants one purpose: **improve Consilient**, and the shared data stays
**private**. That is narrower than ADR-0024, which is still PROPOSED and names three
purposes (product improvement, public research, commercial training) that must not be
bundled.

This design implements the accepted decision. If 0024 is later accepted, a new purpose
is a new grant event against an expanded purpose set. An existing `improve-consilient`
grant never becomes authority for research publication or for training. Bundling is
refused by construction: `CONSENT_PURPOSES` is pinned to exactly `{improve-consilient}`
by test, so adding a purpose is a failing test until someone changes the pin on
purpose.

ADR-0033 already reserves "Publishing, transmitting or exposing anything beyond the
machine" as a user-only class. Consent to share is that class. Adding it to the ask
table does not require a new class; it requires that the ask, when it happens, is
initiated by the user and is never a prompt the harness inserts.

---

## 1. How consent is obtained

**User-initiated. Never prompted. Neutral if they go looking.**

ADR-0024 §3b (PROPOSED, but the reasoning is sound and we adopt the constraint):
nudging at the point of decision is forbidden; encouragement lives in documentation.
This design goes one step further than "asked once at a natural point": **the product
does not ask at all.** A first-run consent dialog is a dark pattern this repository
has no business shipping, and a "natural point" that the harness chooses is still the
harness choosing the moment of decision.

The user finds sharing in the docs, or they do not. The README may make the case
warmly. The consent surface, when they open it, presents grant and decline with equal
weight and no reciprocity framing. A declined grant is not re-offered.

**Preview before grant.** An opt-in the user cannot inspect is not informed consent
(ADR-0024 §2, adopted here as a constraint of 0057). Preview is a local rendering of
the exact bytes that an export would contain, built from the user's own log, after
redaction. Grant is refused unless a preview of the same digest has been written in
this session. That check is part of the pipeline that must not ship until it exists;
the event schema below already carries `preview_digest` so the pipeline has somewhere
to point.

**Channel.** V0-28: only local CLI. Slack, email, a web form, a "I agree" click in a
hosted dashboard — all refused. There is no signature verifier in this build, so a
payload that *claims* to be signed is not evidence that it was. [measured] — the same
limitation as verdicts.

**Who runs it.** A script, not a `consil` subcommand, on the ADR-0058 pattern of
`scripts/verdict.py`. Proposed name `scripts/consent.py`. It is not in this commit.
Until it exists, a principal who wants a grant on the record can pass a well-formed
event to `consil record --event`, which already goes through `append()`. That is
awkward on purpose. Consent to transmit a working record should not be easier than
recording a β verdict.

**Default if they never act:** nothing leaves. No phone-home, no version check, no
anonymous counter. ADR-0024 §2, ADR-0048's test that a paying-nothing user who
contacts no server we operate can use every capability. Sharing is not a capability
of the product; it is an optional contribution.

---

## 2. How it is recorded so it is auditable

Consent is an event in the user's local trajectory. The trajectory is already
append-only, schema-versioned, and the only writer is `append()` (V0-01, the
20 August bypass ratchet). A grant that is not in that log did not happen. A grant
authored by anyone other than the named principal is refused before it reaches the
log (V0-18).

### Event kinds

```
consent.granted
consent.withdrawn
```

These are not ordinary telemetry. They are human decisions. `validate()` infers
`human_decision: "consent"` from the kind, the same way it infers `"verdict"` from
the presence of `human_verdict`. An agent cannot dodge the check by omitting the
field. [measured] — that dodge is how the verdict hole worked.

### Grant payload (local log, not the shared bundle)

| Field | Rule |
|---|---|
| `human_decision` | `"consent"` (inferred from kind if omitted) |
| `principal` | required; `actor` must equal it |
| `via` | `"cli"` (V0-28) |
| `purpose` | must be in `CONSENT_PURPOSES`, currently exactly `"improve-consilient"` |
| `retention_days` | positive integer; a grant with no retention is the gap 0057 named |
| `preview_digest` | SHA-256 of the previewed bytes, when the pipeline exists; absent is allowed on the stub because there is no preview yet |
| `scope` | `"derived-metrics"` — the only scope 0057 authorises. Raw file contents, prompts and diffs are not a scope that can be granted under this purpose |

### Withdrawal payload

Same authority fields. `purpose` names what is being withdrawn. No retention field —
withdrawal is immediate locally; the project-side deletion SLA is policy (see §6).

### What the log must never contain

The **shared bundle itself**. The trajectory has already been published by accident
once (ADR-0057, two daily files in `b2e75e7d`). A grant event that embedded the
payload would, on the next gitignore failure, put the thing we were trying to share
*privately* into the public repository. The bundle lives under `.harness/share/`,
gitignored, with the same class of test as the log. [measured] for the log; the
share-path ignore and test ship in this commit so the third leak is not how we find
the gap.

Receipts (`share.exported`, when the pipeline exists) carry digests, byte counts,
redaction-check names and a destination label. They do not carry the payload.

### Why this is auditable locally

Anyone with the log can answer, without trusting a server:

- whether a grant is in force (last `consent.granted` for a purpose with no later
  `consent.withdrawn`, and `ts + retention_days` still in the future);
- who authored it (`actor == principal`, `via: cli`);
- which purpose, which retention;
- whether any later export receipt's `preview_digest` matches the grant.

That is the same projection pattern as `consil replay`. Extending the projection is
implementation, not this design. No new subcommand is required to *read* it:
`consil record` wrote it, `consil replay` can grow a consent row, `consil dashboard`
can render it, or `scripts/consent.py status` can print it. The last is the
recommended first implementation because it does not touch the CLI pin.

---

## 3. How it is withdrawn, and what happens to data already shared

Withdrawal is as easy as grant: the same script, the same principal, the same
channel. That is a GDPR-shaped rule ADR-0024 already recorded as needing solicitor
review; it is adopted here as a product constraint, not as legal advice. [asserted]

**Locally, immediately:**

- A `consent.withdrawn` event is appended.
- Any subsequent export or transmit for that purpose is refused. The refusal is a
  check, not a comment: a fixture with a grant, a withdrawal, and an attempted
  export must fail the export. (Pipeline; not this commit.)
- Expired grants (`ts + retention_days` in the past) are treated as withdrawn for
  the purpose of export, even if no withdrawal event exists. Standing consent is
  not a blank cheque.

**On the project's side, within a stated SLA:**

Recommended SLA: **30 days from the withdrawal event's timestamp** to delete every
payload whose receipt digest the user presents, and to recompute or destroy any
internal aggregate that still contains that payload. [asserted] — the number is a
choice, not a measurement, and a solicitor may change it.

**What deletion can actually do, stated at grant time:**

| Artefact | On withdrawal |
|---|---|
| The redacted bundle the project holds | Deleted |
| Receipts and indexes that identify the contributor | Deleted or rewritten without that digest |
| Internal aggregates that can be recomputed from remaining receipts | Recomputed excluding the withdrawn digest |
| Internal aggregates that cannot | Destroyed. They are not published in the meantime (see sampling, §7) |
| Product decisions already made *using* the data (a bug that was fixed, a check that was tightened) | **Cannot be undone.** The code change stays. This is disclosed in the preview, in the same sentence as the grant, not in a footnote |

The last row is the one projects lie about. Improving Consilient *is* folding
evidence into the product. You can delete the evidence; you cannot un-ship the
fix. A user who needs "right to be forgotten" of the *effect* cannot be offered
this purpose, and the preview must say so.

Re-consent after withdrawal or expiry is a **new grant**, with a new preview. The
old grant is not revived.

---

## 4. What is redacted before anything leaves, and how redaction is verified

Sharing with the project is not publication. It is still data leaving the machine.
The leak classes are the same classes the pre-publication gate already searches,
plus one this repository measured on 21 August 2026.

### Never in a bundle

| Class | Why | Existing check to rerun on the bundle |
|---|---|---|
| Credentials | V0-16; Joe's public-repo rule | `check_secrets.py` |
| Private-corpus paths | AGENTS.md Never-do; hireable / jobboard | `check_private_corpus.py` |
| Foreign commit identifiers | 71 hashes reconstructed a private CI timeline [measured] | `check_foreign_identifiers.py` |
| Absolute machine paths | They name the user (`C:\Users\…`) | a new path-shape scan on the bundle; does not exist yet |
| File contents, prompts, diffs, brief text | ADR-0057 purpose is improvement, not a code dump; ADR-0024's "derived metrics, never raw material" adopted as the 0057 scope | schema: only derived fields are serialisable |
| Third-party personal data | the next user's log will contain it even if Joe's did not (ADR-0057) | not fully checkable; the derived-only schema is the mitigation |

### What may be in a bundle, under `improve-consilient`

Derived, aggregable, and already the instrument's public language:

- event kind counts;
- composite β with n and interval, never a per-attempt verdict table that names
  tasks;
- gate states as `consil doctor` would report them (pass/fail/unknown, not the
  underlying log lines);
- adapter admission outcomes and harness family labels;
- structural refusal reasons (the invariant id, not the offending line's content);
- durations, pool names, whether a dispatch was supervised.

**No attempt_id, no task string, no ticket id from another repository, no brief,
no diff, no path.** Gate B4 is already constrained by 0057: twenty tickets on
another repository may not carry private-repo detail into a published trajectory.
They may not carry it into a shared one either.

**All-or-nothing for a stated window.** The user previews one bundle covering the
whole in-scope log (or a contiguous date window they name *before* seeing
per-attempt outcomes). They cannot pick the attempts that went well. Cherry-picking
is how opt-in becomes outcome-conditioned *inside* a user, which is the sampling
problem in miniature (see §7). Decline or grant; do not curate.

### Verification, not assertion

Working principle 3: a chokepoint without a check is not a chokepoint. Redaction
that is a comment in a design doc will fragment the first time someone adds a
convenience field.

When the pipeline is built, these ship in the same commit as the exporter:

1. **Preview bytes == export bytes.** A test asserts identity. A preview the user
   approved is not a sketch of what will be sent.
2. **The four leak-class checks run on the bundle and must pass**, or export is
   refused. Mutation: injecting a known secret, a private path, or a 40-character
   foreign hash into a fixture bundle makes export fail. A test that cannot fail
   is worse than no test.
3. **One exporter.** A lint or import-graph check bans other modules in
   `src/consilient/` opening an outbound HTTP connection for this purpose. Default
   configuration makes **no** outbound call (ADR-0024's enforcement item, still
   owed for telemetry in general). Sharing, if it ever transmits rather than
   writing a local file, is a single function behind that lint.
4. **Receipt before transmit.** The local `share.exported` event is appended
   *before* any bytes move. If transmit fails, the receipt records the failure;
   it does not pretend a send happened. Verify by artefact: the file in
   `.harness/share/` and the receipt event, not the exporter's exit code.
5. **Secrets in the public repository remain impossible even if gitignore fails.**
   The bundle's schema cannot express a credential. That is weaker than a scan
   (scans miss new shapes) and stronger than a scan (a field that does not exist
   cannot be filled). Both are required.

Until those five exist, **no export function may ship.** Recording a grant is not
exporting.

---

## 5. Where shared data goes (so it stays private)

ADR-0057: shared data is "private and used to improve consilient only". It is not
published, and it is not this repository.

**Product capability (local, no network):** write a redacted bundle under
`.harness/share/` and a receipt in the log. The user can move that file themselves.
This is the only shape that satisfies ADR-0048's test — a user who pays nothing and
contacts no server we operate can still *produce* a shareable artefact — and the
only shape that needs no credential.

**Intake (facilitation, not a product feature):** a store the public repository
cannot reach, operated by the principal, on infrastructure whose credentials never
appear in repository settings or Actions secrets (ADR-0046). The intake URL may be
documented; the credential may not. A GitHub-hosted receiver is forbidden because
the public repository can reach it.

The first implementation of intake can be "the user sends Joe the file". That is
embarrassing and honest. Automating it is facilitation and is prepaid if it costs
money (ADR-0048). It is not a reason to put a secret in this repository.

A capability that needs a credential in the public repository **is not built**.

---

## 6. How a user checks the promise instead of trusting it

This is the section the rest of the document exists to make possible. Split the
ADR-0057 sentence into claims, and say which of them a contributor can check.

### Checkable from the contributor's machine

| Claim | How the user checks | What the test is, when the pipeline exists |
|---|---|---|
| Nothing left this machine without an in-force grant | Attempt an export with no grant, after withdrawal, and after expiry — all refused | fixtures, three cases |
| The grant was recorded as theirs | `actor == principal`, `via: cli`, kind in `{consent.granted, consent.withdrawn}` | V0-18 / V0-28, **shipping in this commit** |
| The purpose is the one they granted | `purpose` ∈ pinned `CONSENT_PURPOSES` | pin test, **shipping in this commit** |
| Retention was stated | `retention_days` is a positive integer on every grant | schema test, **shipping in this commit** |
| Preview matched export | compare `preview_digest` to the file in `.harness/share/` | byte-identity test |
| Redaction ran | receipt lists the checks; a dirty fixture is refused | mutation tests |
| The bundle is not in git | `git ls-files .harness/share/` is empty | **shipping in this commit** |
| This repository still has no user log | `git ls-files .harness/log/` is empty | V0-33, already shipping |

Recommended user command, when the script exists:
`python scripts/consent.py status`. It prints two lists: **observed** (the rows
above, each with a yes/no and the artefact it read) and **policy** (the rows
below, each labelled `[asserted]`). It is forbidden to print a policy claim as if
it were observed. That is the same discipline as `consil doctor` refusing to
report a gate as passing when the evidence is absent.

No new `consil` subcommand. Status is a projection of events `consil record`
already accepts.

### Not checkable from the contributor's machine — policy, labelled `[asserted]`

| Claim | Why it cannot be checked by the contributor |
|---|---|
| Held privately by the project | Privacy of a remote store is a property of someone else's machine |
| Used only to improve Consilient | Use is a purpose, not an artefact the contributor holds |
| Deleted on the project's side after withdrawal | Non-possession is not provable from outside. A public inventory of receipt digests that *drops* a digest is necessary and not sufficient: the inventory can lie |
| Not used for training, not sold, not published | The same: absence of a use is not an artefact |

V0-18 has the same shape for *authorship*: `actor` is a string, not an
authenticated identity, and the check stops an accidental forgery, not a
determined one. [measured] We did not pretend otherwise there. We do not here.

**An independent auditor with access to the project's store is a different class
of facts** (CONSILIENCE.md clause 2). Until such an audit exists, the use-limit
is a policy claim and every user-facing sentence about it carries `[asserted]`.
Agreement between the docs and the maintainer that "we would never" is echo, not
consilience.

Cryptographic deletion proofs, TEEs, and append-only public ledgers of receipt
digests would move *some* of the policy column toward checkable. They are not
proposed for v0. Proposing them without building them would be the promise-the-
code-does-not-keep defect again. The honest v0 statement is:

> You can check that nothing left your machine except what you granted, that it
> was redacted, and that you can withdraw. You cannot check what we do with it
> afterwards. That limit is why sharing is off, why it stays off until you act,
> and why a cross-user β built from what people chose to send is not "the" β.

If that paragraph is too sour to print, the feature is not ready. It is the
paragraph this project owes, because the alternative is asking users for the
trust we founded the project on refusing.

---

## 7. The sampling problem, stated as a property of the product

Opt-in sharing selects its sample partly by who consents, and plausibly by
outcome. ADR-0057 already recorded this as evidence *against* the decision and
accepted the weaker instrument. This design does not pretend to fix it.

β is P(verifier accept | human reject). The denominator is rejections. Users who
share are plausibly those whose runs went well, who are more engaged, or who work
on less sensitive code. Users may also share the attempts they are proud of and
withhold the ones they rejected — which is why §4 forbids cherry-picking inside
a grant. **Who consents is still a filter we cannot see through.**

The sign of the bias is not known. [asserted] If sharers hide rejections,
the denominator shrinks; if they also hide the embarrassing false-accepts, the
numerator shrinks faster and β looks better than the population. If they share
failures to get help, the other way. We will not pick a sign and "correct" for
it. A correction that assumes the thing we cannot observe is a second lie.

### What the design does

1. **Does not eliminate the bias.** State that wherever a cross-user figure is
   reported. Not in a methods appendix. In the same sentence as the number.
2. **Forbids a global β presented as "the" β.** A figure computed from shared
   trajectories is labelled `sample: opt-in` and `n_users` / `n_attempts` travel
   with it. Local β — the product, computed from *this* user's log — remains the
   number `consil beta` prints. Mixing them without labelling is a defect of the
   same class as substituting per-check β for composite β (ADR-0012).
3. **All-or-nothing windows** (§4) remove *within-user* cherry-picking. They do
   nothing to *between-user* selection.
4. **A contributor's bundle is usable in an aggregate only if it would, on its
   own, clear the same n floor `consil beta` uses** (thirty rejections today).
   Sparse vanity grants do not enter a cross-user number. This is not
   de-biasing; it is refusing to pretend a number exists.
5. **No mandatory anonymised aggregate.** That would be a better instrument and
   it would contradict ADR-0057. The principal chose the weaker instrument
   deliberately. Supersede 0057 if that choice is reversed; do not erode it in
   the exporter.

k-anonymity and differential privacy of a public β corpus are unassessed
(ADR-0024 evidence against). They are not claimed here. Nothing in this design
authorises publishing a corpus.

If shared n is so small or so obviously selected that a cross-user β cannot be
estimated at all, that is one of the overturn conditions ADR-0057 already named.
The response is to stop reporting the figure, not to impute the missing users.

---

## 8. Relation to CONSILIENCE.md

Clause 1 — provenance: a grant that is not in the append-only log did not happen.
The preview digest travels with the grant so the induction ("they agreed to share
this") names its evidence.

Clause 2 — different class: the contributor's local checks (preview, redaction,
V0-18) and an auditor's inspection of the project's store would be two classes.
Today only one class exists. Agent and user agreeing that the policy is fine is
echo.

Clause 3 — a test, with an error rate: the use-limit is a test we cannot run
from the contributor's machine. β of *that* test is unknown. Shipping sharing as
if we had run it would be the product applied to everyone except its authors.

---

## 9. What this commit does, and what it refuses to do

**Does:**

- This design.
- `"consent"` added to `HUMAN_ONLY`. `consent.granted` / `consent.withdrawn`
  infer the decision, so omitting `human_decision` is not a bypass.
- `CONSENT_PURPOSES` pinned to `{improve-consilient}`.
- A grant must carry a positive `retention_days`.
- `.harness/share/` gitignored, with a test.
- V0-18 / V0-28 coverage extended to `consent` so EXP-47's "the parametrize
  missed a member of HUMAN_ONLY" does not recur here.

**Refuses:**

- A `consil share` / `consil consent` subcommand.
- An exporter, a transmitter, an intake, a preview renderer.
- Any outbound call.
- Any new experiment number (none was allocated; the sampling claim is not
  being settled, it is being disclosed).
- Any `[cited]` legal claim. Retention, withdrawal SLA and GDPR-shaped rules
  are `[asserted]` product constraints pending solicitor review, matching
  `docs/legal/README.md`.

Until the five redaction checks in §4 exist, shipping an exporter would make
this document describe a promise the code does not keep.

---

## 10. Enforcement (the checks that make the design a chokepoint)

Shipping now, same commit:

| Invariant | Check |
|---|---|
| An agent cannot author consent | `validate()` refuses `consent.granted` / `consent.withdrawn` unless `actor == principal` and `via == cli`; omitting `human_decision` does not dodge it |
| Purposes are not bundled | `CONSENT_PURPOSES == {"improve-consilient"}` |
| Retention is stated | grant without positive `retention_days` is refused |
| Share payloads cannot be published by living in a tracked path | `.harness/share/` in `.gitignore`; `git ls-files .harness/share/` is empty |

Owed with the pipeline, not before:

| Invariant | Check |
|---|---|
| Preview is the payload | byte identity |
| Redaction ran | leak-class checks on the bundle; mutation fixtures |
| One exporter | lint on outbound HTTP from product code |
| Receipt before transmit | event exists, then the file, then any network |
| Withdrawal stops export | fixture: grant, withdraw, export refused |
| Expiry stops export | fixture: grant with `retention_days: 1` dated in the past, export refused |
| Status does not launder policy as observation | the policy list is labelled; a test asserts the two lists are disjoint |
| Cross-user β cannot hide its sample | any reporter of a shared-sample β includes `sample: opt-in` and n; a test fails a figure without them |

A documented rule that nothing enforces is not a rule. The owed column is why
the exporter is not in this commit.

---

## 11. Evidence against

- **User-initiated-only will yield almost no data.** [asserted] Projects that
  care about telemetry use opt-out or a first-run prompt for this reason.
  ADR-0057 already accepted sparsity as the cost of not surprising people. This
  design makes sparsity *more* likely by refusing the prompt. If the sampling
  frame is empty, there is no cross-user β to misuse, which is the failure mode
  we actually care about.
- **All-or-nothing windows will deter the remaining volunteers.** [asserted]
  Some users would share a subset they have reviewed line by line and will not
  share a year of log. That is a real loss of evidence and a real protection
  against outcome-conditioned sharing. We keep the protection.
- **The "cannot un-ship the fix" disclosure will look like a weasel.** [asserted]
  It is the opposite, but it will be read as one. The alternative is implying
  withdrawal undoes improvement, which is false.
- **`actor` is still an unauthenticated string.** [measured] V0-18 stops
  accidental forgery. A determined agent on the same machine can write a grant
  as the principal. Cryptographic authorship is the unbuilt half of V0-18,
  V0-28 and this design together. Building it for consent alone would be
  theatre.
- **A public digest inventory was considered and rejected for v0.** It would
  give the user a necessary-not-sufficient check on project-side deletion, and
  it would also publish the fact of sharing plus a stable identifier. Under
  0057 that fact is itself private. The inventory is a different product, and
  it would need its own consent.
- **ADR-0024 may be accepted later with a different shape** (per-purpose
  commercial re-consent, 90-day notice for training). Implementing 0057's
  single purpose now could ossify a narrower grant than 0024 wants. The pin
  test is the release valve: expanding `CONSENT_PURPOSES` is an explicit,
  test-failing decision, not a silent widening.

We designed anyway because the alternative is either never allowing share (which
leaves 0057's second sentence as ornament) or shipping a pipeline whose promise
cannot be checked. Ornament is the honest holding state; this document is the
bridge. The pipeline waits.

---

## 12. Reversal and falsifier

**Reversal.** Delete the `consent` member of `HUMAN_ONLY`, the consent contract,
the share gitignore rule and this document. Grants already in a user's local log
remain, because the log is append-only; they authorise nothing, because nothing
reads them. That is the same irreversibility as a recorded verdict.

**Falsifier of the design, not of 0057.** A built exporter that transmits
without a grant, or a status output that prints a policy claim as observed, or a
cross-user β that does not say `opt-in`. Any of those means this document has
become the thing it was written to prevent, and the exporter is what gets
deleted.

**Falsifier already named by 0057.** Opt-in n so sparse or so selected that a
cross-user β cannot be estimated. Then stop reporting one. Do not restore
publish-by-default.

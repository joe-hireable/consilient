# 0106. Admit identified third-party maintainer verdicts as human-β authors

- **Status:** ACCEPTED 28 August 2026 by the principal, recorded as `human.approval`
  `832f3d99-4f92-4281-b236-360f9e1fafc2` in the trajectory, with permission to submit upstream
  recorded separately as `78c1ea9e-f519-43a2-b80a-29395ee04de9`. Both were typed by him through
  the local CLI; neither was authored by the orchestrator, which is the whole subject of this
  ADR. The killing experiment is the rejection-fraction floor in § Enforcement
  (`beta.MIN_COMPOSITE_REJECTION_FRACTION = 0.05`): if it is not cleared, this route is declared
  failed rather than quietly reported.

  **Accepted is not yet exercised.** EXP-144, the experiment this decision rests on, is BLOCKED
  on the upstream collector and maintainer-verdict join, and the B4 receipt store was found on 28
  August to contain nothing but test-stub placeholders — so the external-contribution path has no
  evidence of ever having run end to end. Rows continue to be recorded under the proxy estimand
  until it has.
- **Date:** 2026-08-25
- **Deciders:** Joe Brown (principal) — proposed by the orchestrator from his own instruction
- **Relates to:** V0-18 (a human verdict is valid only when the principal authored it),
  0002 (β as the organising quantity), 0103 (contract-β is the gate quantity, human-β is
  alignment), 0057 (append-only trajectory), 0039 (gate changes are reserved to the principal)
- **Inquiry tier reached:** T1 ground — the identification argument is exact; the assumption that
  maintainer correctness rejections are drawn from the same population as our own defects is
  `[asserted]` and is what the experiment tests
- **Executable model:** none. What is unknown is empirical — the rate at which our verifier
  accepts work a maintainer then rejects — and a model of it would assume the quantity we are
  trying to measure.

## Context

**The human-β meter has received zero rows.** Not few — none. `beta.py` says so in its own module
docstring: "there is no collection protocol at all — the meter has received zero rows."

That is not an accident of effort. V0-18 says a human verdict "is valid only when the human
principal authored it", so every human verdict must come from Joe. `MIN_REJECTIONS = 30` sets the
floor for reporting anything. Thirty adversarial judgements authored personally by one man, on
top of running the business, is the whole of the bottleneck, and it is why the load-bearing
quantity of this project has never been measured against a human at all.

Joe, 25 August 2026: *"I cant be the bottleneck for anything it must be open source."*

He is right, and the constraint is structural rather than a matter of willingness. A design whose
central measurement requires one specific person to perform it thirty times does not scale, and
this project's own subject is the danger of a measurement nobody actually takes.

## Decision

**Admit a verdict authored by an identified third-party maintainer of an external repository as a
human-β verdict, under every condition below. All of them, not most.**

1. **Attributable.** The verdict resolves to a named account on the hosting platform, recorded
   with the review state, the reviewer's login, the commit judged and the timestamp, from the
   platform's own API. A verdict we cannot attribute to a person is not admitted.

2. **Unsolicited.** We did not ask for the outcome, argue for it, or review our own PR. Asking a
   maintainer to reject something makes it our verdict wearing their name — which is the failure
   V0-18 exists to stop, arriving through a longer route.

3. **Not authored by any agent of ours.** Unchanged from V0-18. A maintainer cannot be our agent;
   what this condition still forbids is inferring a verdict from silence, from a bot, or from a
   merge queue.

4. **About correctness.** Only a judgement that the change is *wrong* counts. Rejections for
   scope, roadmap, staleness, duplication or house style are judgements of FIT and are recorded
   in a separate field that cannot reach the numerator. The maintainer's own words are stored
   verbatim so the classification can be re-checked against them.

5. **Classified by someone other than the PR's author.** The agent that wrote the change may not
   decide whether its rejection was about correctness. That is echo arriving through the data
   layer. The classifier is the principal, or a model family different from the author with the
   principal adjudicating disagreements, and the disagreement rate is recorded.

6. **The submission decision did not consult the verifier being measured.** This is the condition
   the whole estimand rests on. If we submit only what our verifier accepted, every rejected row
   carries `verifier_accept=True` and β is 1 by construction — `beta.py` names exactly this and
   the rendered output prints "NOT a bound: sampling not declared unconditioned on the verifier".
   Submission is gated on an admission bar that is **not** our verifier: the project's own CI
   passes, and the contribution is one that project actually wants.

## Consequences

**What this buys.** A human oracle that scales without the principal, is independent of us by
construction, and judges real code in the place it will actually live. It is a genuinely
different class of facts in Whewell's sense: the maintainer shares no evidence, no model, no
prompt and no incentive with the harness that produced the change.

**What it costs, stated plainly.**

- **It is a weaker oracle than the principal in one specific way.** A maintainer judges "is this
  right *for this project*", which is not identical to "is this artefact correct". Condition 4
  narrows it but cannot fully separate the two, and some misclassification will remain.
- **It is slow, and it gets slower as the harness improves.** Thirty correctness rejections of
  changes that already passed the project's CI is a lot, and the better the work becomes the
  rarer they are. The measurement is hardest exactly when the system is working well.
- **It measures a task family that is not ours.** Contributions to external projects are not the
  same distribution as work on this repository, and the skill forbids comparing β across
  families. Reported figures name the family.
- **Running their CI first conditions the sample on THEIR verifier.** That is acceptable, because
  it is not the verifier being measured, but it is a real narrowing and it is declared: the
  estimand is β among changes that already pass the host project's own automated gates.

**The awkward case, recorded rather than hidden.** If our verifier finds a defect *after* we have
submitted, good faith requires telling the maintainer, and telling them influences their
decision. Those rows are recorded under a distinct disclosure flag and are reported separately.
They are not discarded — a maintainer who says "that is not a problem, merging anyway" has given
a verdict on a verifier-*rejected* artefact, which is the cell this project has never observed —
but they may not be pooled with undisclosed rows without saying so.

**What is explicitly not decided here.** Whether these rows feed Gate A. ADR-0103 makes contract-β
the gate quantity and keeps human-β as alignment; this ADR does not change that, and until the
principal says otherwise these rows are recorded under a proxy estimand kind so they cannot reach
the gate.

## Enforcement

A chokepoint without a check is not a chokepoint (working principle 3), so this ships with its
checks or not at all.

- `admits_human_beta_row` gains the third-party path, and a test asserts a row missing **any** of
  the six conditions is refused — one test per condition, not one test for the set.
- A test asserts a row whose rejection is classified as fit rather than correctness cannot enter
  the numerator, and that an unclassified rejection cannot either.
- A test asserts a row whose verifier verdict is timestamped later than the submission is refused,
  since the property being claimed is that the verdict did not gate the submission.
- A test asserts both cells are representable — verifier-accepted/human-rejected and
  verifier-rejected/human-merged. A schema that can express only one recreates the conditioning
  in the data model, which is how this failure would come back.
- **The killing check.** The fraction of admitted changes that our verifier rejects is computed
  and reported with every figure. If the admission bar turns out to be nearly as strong as our
  verifier, that fraction approaches zero, the variation collapses, and β returns to 1 by a
  slower route. Below a pre-registered floor the honest output is `insufficient_data`, and this
  route is declared failed rather than reported with a caveat.

## Alternatives rejected

**Keep V0-18 as it stands.** Honest, and it is why the meter has zero rows. Rejected because a
measurement that has never been taken is not a safeguard, it is an aspiration, and this project
exists to say so about other people's measurements.

**Submit deliberately weak changes to harvest rejections.** Rejected outright. It abuses volunteer
maintainers, and it measures nothing: work weakened on purpose is not drawn from the distribution
the harness actually produces, so its rejection says nothing about the false-accept rate.

**Have the harness review other people's PRs and compare to the maintainer (unit Z10).** Kept, but
as a cross-check rather than the instrument. It has the better sampling property — the maintainer
has never seen our checks — but it measures a task family further from our own, and it produces
no upstream contribution, so it does nothing for Gate B4.

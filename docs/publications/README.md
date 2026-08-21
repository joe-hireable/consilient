# Publication policy

We publish rarely. The default answer to "should this be a paper?" is **no**.

We nevertheless publish the **research record continuously**: a frozen protocol before a
run, the runnable instrument, machine-readable results, an evidence-tagged finding and an
honest stopping-rule verdict. [asserted] Formal papers remain rare; reproducible research
notes and negative results do not wait for a paper-sized story. [asserted]

## Two publication lanes

### Lane A — continuous open research

Every completed experiment receives a public disposition in its findings file. [asserted]
The disposition is one of: `not publishable`, `research note`, `dataset/instrument release`,
or `paper candidate`, with the reason and unmet gates stated. [asserted]

A research note may ship when the protocol was fixed before the result, the instrument and
safe artefacts are reproducible, the stopping rule was applied unchanged, and limitations
are explicit. [asserted] It may report `insufficient evidence`; a null or underpowered result
is not rewritten as a success. [asserted] Repository findings are the first publication
surface; a versioned archive, dataset venue or practitioner article is added only when it
improves reuse. [asserted]

Private measurement corpora remain private. [asserted] Notes may report aggregate metrics
from `hireable-3.0` or `jobboard-v2`, but never their content, excerpts or detailed paths;
a result that cannot be reproduced without private material must say so and needs a public
replication before it can clear G1 for a formal paper. [asserted]

### Lane B — formal synthesis

The four gates below decide papers and equivalent headline publications. [asserted] Several
Lane-A records should be synthesised when together they establish one clean, novel and
useful claim; experiment count and release cadence are not substitutes for that claim.
[asserted]

## First-draft standard

“First draft” means the first version offered for human or external review, not an internal
scratchpad. [asserted] Before that version exists, the publication owner must have:

- frozen a claim map linking every headline, table and figure to its evidence class and
  reproducible artefact; [asserted]
- completed a primary-source novelty matrix containing the strongest near misses and the
  result that would make the paper unnecessary; [asserted]
- reproduced every reported number from a clean checkout and recorded software, model,
  prompt, seed and hardware versions where they can change the result; [asserted]
- obtained an evidence-class-different reader's blind re-derivation of the conclusion from
  the artefacts, with disagreements preserved and disposed individually; [asserted]
- run explicit audits for overclaim, leakage, citation support, private-corpus exposure and
  forbidden `[SNIP]`/`[2ND]` sources; [asserted]
- included stopping-rule outcomes, nulls, sample-size limits, unresolved confounds,
  conflicts of interest and the experiments that were not run; [asserted]
- prepared the artefact card, reproduction instructions and public-data boundary alongside
  the prose rather than after it. [asserted]

Failure of any item keeps the work in Lane A and out of a formal first draft. [asserted]
Review is exacting about claims and constructive about contributors: criticism names the
unsupported statement, evidence gap or failed check and the smallest repair; status,
seniority, persona and rhetorical confidence carry no weight. [asserted]

## Human authorship, AI assistance and submission authority

Joe is the accountable human author and submission principal for Consilient papers unless
a later human collaborator independently satisfies the target venue's authorship rules.
[asserted] An AI system is never listed as an author: arXiv, NeurIPS, AAAI and ACL state
that directly, while all make the human authors responsible for the submitted content.
[cited]

Agents may autonomously discover literature, challenge novelty, design and run authorised
experiments, preserve artefacts, draft and revise prose, build tables and figures, compile
the paper, prepare checklists and produce a frozen submission package. [asserted] This work
does not turn Joe into an author by proxy. Before a formal submission he must understand the
claim and methods, reproduce or inspect the retained evidence sufficiently to exercise
scientific judgement, approve every claim and disclosure, and accept responsibility for
originality, accuracy, rights, privacy, ethics and correction. [cited]

The final package carries an immutable payload hash and records `human_approved: false`
until Joe approves that exact payload. [asserted] Joe personally authenticates and performs
the binding submission, licence or copyright action. [asserted] OpenReview forbids a user
from giving a third party account access, and arXiv expects self-submission unless its
trusted-proxy requirements and any required automated-deposit permission are satisfied.
[cited] A later officially authorised API path may upload an already approved immutable
payload, but it may not invent, alter or accept representations after approval. [asserted]

Repo-local preregistrations, instruments, safe results and research notes may continue under
Lane A without pretending they are peer-reviewed papers. [asserted] External formal
submission remains behind the human-author gate above. [asserted]

### Disclosure record

Every formal paper carries a disclosure generated from the trajectory, not from memory.
[asserted] It names each material provider, model or harness; its access date or version;
its roles in ideation, research, methods, implementation, orchestration, analysis, figures
and writing; and the human checks actually completed. [asserted] ICLR 2027 requires an AI-use
section and form disclosure, AAAI requires every AI role in developing the work to be
documented, ACL requires content-generating use to be disclosed, and NeurIPS requires
important or non-standard methodological use to be described. [cited]

Venue-neutral minimum wording, rendered only with true fields, is: [asserted]

> **AI assistance and human accountability.** Generative AI systems — [provider, model,
> harness, version/access date] — assisted with [material roles]. Joe Brown selected and
> approved [the research questions, hypotheses and stopping rules actually approved];
> completed [the citation, code, result, provenance, rights and privacy checks actually
> completed]; reviewed every final claim, table and figure; and approved this exact
> manuscript. No AI system is an author. Joe Brown accepts responsibility for the work's
> originality, accuracy, integrity and correction. [asserted]

A claim that a human check occurred must point to its first-party approval or verification
event; an agent-authored summary cannot manufacture it. [asserted]

## Why the bar is high

arXiv may decline work that lacks originality, novelty or significance, may ask similar
submissions to be consolidated and may limit excessive submission rates. [cited] NeurIPS
also prohibits “thin slicing” very similar papers. [cited] Continuous experiment records
therefore feed a publishability register; they do not create one paper per experiment.
[asserted]

## The four gates

A formal result publishes only if it clears **all four**. [asserted]

**G1 — Is it true?** Reproduced from a seed. Code released. A second party re-derived the
conclusion from the artefact without seeing our writeup. `[measured]` or `[algebra]`
evidence, not `[simulated]` alone. [asserted]

**G2 — Is it new?** A real literature search, documented, including the near misses. If
someone did it already, cite them and move on — that is a *win*, not a loss, because it
means we can adopt instead of build. [asserted]

**G3 — Is it useful to someone who is not us?** Would a stranger change what they build
because of it? "We built a thing and here is its architecture" fails this. "Here is a
measurement everyone assumed and nobody checked" is the target shape. [asserted]

**G4 — Is it honest about its limits?** Sample sizes, assumed functional forms, conflicts of
interest and experiments not run are explicit. [asserted] Every claim is tagged as in
`../decisions/README.md`. [asserted]

## Negative results count

A well-executed null result can clear the gates as readily as a positive one. [asserted]
“We tried X, it did not beat the baseline under conditions Y, here is the code” is useful
when the protocol and artefacts let others avoid repeating the same unsupported assumption.
[asserted] Do not relabel a failed hypothesis as an unpublishable experiment. [asserted]

## Practical notes on arXiv

- A new arXiv user or a user submitting to a new category may require endorsement. [cited]
  A first submission checks Joe's current account state instead of inferring it from his
  affiliation. [asserted]
- Joe has no recorded academic affiliation in this repository, so endorsement may be
  needed before the first submission. [asserted]
- Consider a co-author only when that person makes an authorship-level contribution and
  accepts accountability; endorsement alone does not make a co-author. [asserted]
- arXiv requires an irrevocable distribution licence selected by the submitter. [cited]
  Paper and code licences are separate decisions; do not assume CC BY 4.0 until Joe approves
  the paper licence for the exact submission. [asserted]
- Hugging Face is a candidate artefact venue for datasets, trace corpora and evaluation
  harnesses; venue choice remains a judgement based on reuse and rights. [asserted]
- A repo-local `docs/publications/NNNN-title/` with paper source, safe code/data and a gate
  record is the minimum publication package. [asserted] arXiv is optional; not every
  write-up needs to leave the repository. [asserted]

## Candidate list

Ordered by how close they appear to clearing the gates; the order is a current judgement,
not a measured ranking. [asserted] Nothing here commits a submission. [asserted]

### C1. Verifier reliability as a control parameter for agent orchestration
**Status: not ready — needs T3.** [asserted] The β work (`../decisions/0002-*`) appears to
clear G3 and possibly G2, fails G1 today because its central surface is simulation-only,
and cannot pass G2 until arXiv:2605.00663 is read. [asserted]
Ready when: β measured on ≥3 real repositories, the β ≡ 1 − critic-recall identity holds
empirically, and the bimodal-difficulty check (Q3) has been run. [asserted]

### C2. CASD / constrained decoding — **a null result**
**Status: closest to ready, and it should be written as a negative.** [asserted]

The recorded state of that work is that the replication landed marginal on clean inputs, bimodal
across cases, and the comparison against the real production baseline — jump-forward
decoding — was never run. [measured] Written up as "constrained decoding did not beat jump-forward
under conditions X, here is the code and the traces", it clears G1 (if the missing
comparison is finally run), G2 (null results here are scarce), G3 (people are actively
building on the assumption it wins) and G4 (the limits are the point).
[asserted]

Written up as a success would contradict the recorded evidence. [asserted]

**The missing experiment is the whole paper.** [asserted] Run the jump-forward comparison
first. [asserted]

### C3. Escalation-on-verification vs learned routing in the coding domain
**Status: bundle into C1.** [asserted] It is simulation-only today and does not yet carry a
separate paper-sized claim. [asserted]

### C4. Meta-harness adapter interface across heterogeneous coding agents
**Status: speculative.** [asserted] It is a paper candidate only if the interface proves
non-obvious across four real CLIs; otherwise it remains a research note or practitioner
article. [asserted]

## Format

`docs/publications/NNNN-short-title/` contains `paper.md` (or `.tex`), safe `code/`, safe
`data/`, a disclosure record, a frozen submission manifest and a `README.md` stating which
gates it clears and which it does not. [asserted]

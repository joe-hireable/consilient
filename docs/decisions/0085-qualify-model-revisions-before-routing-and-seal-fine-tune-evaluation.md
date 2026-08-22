# 0085. Qualify model revisions before routing, defer matrix factorisation, and seal fine-tune evaluation

- **Status:** PROVISIONAL — EXP-111 is the killing experiment
- **Date:** 2026-08-22
- **Deciders:** Codex dispatch `20260822T140634-824a8280e8` for the provisional technical decision;
  no principal approval of the mechanism is inferred
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision is a fail-closed lifecycle contract; EXP-111 carries the
  prospective comparison and fixed stopping rule

## Context

[measured] The live Cursor model surface has a static 22-row registry and a local drift refresher.
Every row currently defaults to unknown reasoning capability. An explicit unregistered unknown model
is refused, but a registered unknown model is exempt from that check and may be selected by headroom
and registry order. The refresher's `--write` path is discovery, not qualification.

[measured] A `2026-08-22T14:40:41Z` projection of the local trajectory has 111 dispatch outcomes but
no structured model or task-family fields and only one attempt outcome/verdict pair. There is no
accepted-outcome task×model matrix to factorise.

[measured] Consent recording, private harvest, experiment-training prototypes and local hardware-fit
helpers exist, but trusted principal ingress, use-time consent enforcement, a model fine-tune
trainer, sealed model evaluation, a checkpoint activation pointer and exact model rollback do not.
The relevant ADR-0076 and ADR-0077 mechanisms are working-tree proposals rather than landed
guarantees.

[asserted] The requirement contains four decisions with different failure modes: discovery and
adoption, model selection, fine-tuning, and cost. Treating “new release”, “high predicted quality”,
“training completed” or “cheaper” as one approval would let an unverified model silently replace an
incumbent.

## Decision

[asserted] Automatically **discover and quarantine** revisions, but never make them routable from
catalogue metadata. An exact revision becomes `qualified` only after identity, rights, capability,
accepted outcomes and the full cost vector are measured on the frozen bank. It becomes `routable`
only after existing gates still pass and the principal authenticates approval of the exact manifest.
Until trusted ingress exists, that transition is unavailable.

[asserted] Keep the hand-maintained bootstrap registry and ADR-0003's simple verifier-gated policy.
Matrix factorisation remains an offline challenger until a structured outcome matrix exists and a
held-out, new-model comparison beats the strongest simpler rule without worsening verifier error or
cold-start refusal.

[asserted] Treat every local fine-tune as a new immutable revision. Training requires authenticated,
purpose-specific, live consent; an exact rights-filtered private dataset; a pinned base and adapter;
and a candidate-inaccessible evaluation bank and instrument. The principal may approve the exact
winning digest; no model, manager or scheduled process may approve for him. Every later fitting pass
is another candidate, not continuous mutation of the active model.

[asserted] Keep cost as the vector `(actual metered spend, provider-equivalent list price,
provider-native subscription quota, wall/device time, active human minutes)`. Reuse `budget.py`'s
atomic reservation transaction and require proved provider-call coupling before treating it as spend
authorisation. Never convert already-paid quota to cash or call provider-equivalent price an actual
saving.

## Evidence

- `[measured]` `scripts/refresh_models.py --write` renders bare `ModelOption` rows, while
  `scripts/dispatch.py::build_command` refuses unknown reasoning only when the selected option is not
  in `MODELS`. Registration can currently bypass the intended unknown-capability refusal.
- `[measured]` `dispatch.py` imports neither `routing.py` nor `budget.py`; current automatic model
  selection uses known unexhausted pool headroom and registry order, not task outcomes or cost.
- `[measured]` The `2026-08-22T14:40:41Z` private-trajectory projection has zero structured model
  fields and zero task-family fields across 111 dispatch outcomes. One attempt outcome/verdict cannot
  identify latent model and task factors.
- `[cited]` RouteLLM trained its MF router on 65,000 retained pairwise preferences among 64 models;
  Arena-only MF was below random on out-of-domain GSM8K. Ong et al. (2025), *RouteLLM*,
  arXiv:2406.18665.
- `[cited]` EmbedLLM uses a complete 112-model × 36,054-question matrix; adding a model requires
  retraining. Zhuang et al. (2025), *EmbedLLM*, arXiv:2410.02223.
- `[cited]` RouterBench records 405,467 outcomes, yet its learned KNN/MLP routers did not significantly
  beat the static cost-quality `Zero` router overall. Hu et al. (2024), *RouterBench*,
  arXiv:2403.12031.
- `[cited]` GraphRouter's held-out-model condition still uses 80 measured interactions for each new
  model. Feng, Shen & You (2025), *GraphRouter*, arXiv:2410.03834.
- `[measured]` `budget.py` atomically refuses or records caller-declared OpenRouter-labelled spend
  reservations but is not coupled to provider calls, while `usage.py` gives subscription quota and
  metered money different types. Dispatch outcomes record subprocess duration after lock acquisition,
  not end-to-end wall time, provider-equivalent cost or active human minutes.
- `[measured]` The consent validator records purpose/retention/withdrawal fields but says trusted
  principal ingress is absent; no training consumer currently checks an active grant.
- `[asserted]` A cryptographic model/data/instrument lineage plus exact rollback is the minimum
  reversible boundary. Model names, hashes without isolation and training loss cannot establish
  accepted output quality.

## Evidence against

- `[asserted]` The strongest alternative is to keep the hand-maintained list for another year.
  Frontier models can improve faster than a local adapter can be collected, trained and requalified;
  a hosted alias may not expose a stable revision; each automatic download widens the supply-chain
  boundary; and human review may cost more than any provider-equivalent saving.
- `[cited]` RouteLLM shows contrary positive transfer to prespecified new strong/weak pairs, and
  EmbedLLM reports a positive MF margin at 1,000 questions. `[asserted]` Those are the strongest
  reasons not to reject MF permanently. They do not provide zero-shot qualification of an arbitrary
  new registry member: the first assumes pair ordering and the second retrains to add a model.
- `[asserted]` RouterBench is stronger evidence for restraint. `[cited]` Its benchmark contains
  405,467 inference outcomes; KNN/MLP routers trained on 70% per-task splits excluding MT-Bench did
  not significantly beat the static cost-quality `Zero` router overall.
- `[asserted]` Fine-tuning may improve a narrow familiar distribution while regressing general work,
  learning evaluator artefacts or becoming obsolete during training. A sealed bank reduces those
  risks but does not prove transfer.
- `[measured]` The repository cannot currently enforce the full decision: its routing arithmetic is
  unwired; consent identity is unauthenticated; no trainer isolation or rollback pointer exists; and
  the cost vector is incomplete.
- `[asserted]` We therefore accept the alternative operationally now. Only discovery/quarantine and
  experimental qualification are proposed; the static list remains active, MF remains off and a
  fine-tune remains unroutable unless EXP-111 and the implementation gates both pass.

## Consequences

**Positive** — [asserted] a new release cannot become an ordinary automatic route merely because its
ID appeared. Model quality comes from common executed outcomes; consent and sealed evaluation precede
training use; rollback names exact bytes; and “price” cannot hide quota, time or human work.

**Negative** — [asserted] qualification consumes at least one complete frozen-bank run per candidate,
human-labelled safety may remain insufficient, unpinnable hosted models will become stale often, and
promising fine-tunes can remain quarantined indefinitely. The design deliberately leaves model gains
unused when their provenance or instrument is incomplete.

**Neutral but load-bearing** — [asserted] discovery, qualification, training and activation remain
states of the existing dispatch/event/work-item system. This ADR adds no second orchestrator, no CLI
command, no gate pass and no authority delegation.

## Enforcement

[asserted] This ADR specifies the invariant and pre-registers its falsifier; this change does not implement
the lifecycle. The implementation must land with tests that: refuse every registered unknown or
non-routable model; turn discovery only into quarantine; enforce consent at data read; deny the
candidate all instrument/controller/result access; preserve all cost dimensions; and prove exact
rollback by restored artefact.

- Check: future focused lifecycle invariant tests plus existing AST, six-command, private-corpus,
  secret, foreign-identifier and gate checks
- Fails CI: no — the new lifecycle checks do not exist yet; existing checks remain binding
- Added in the same commit as the implementation: required; there is no implementation in this change

## What would overturn this

[asserted] EXP-111 kills automatic qualification or local fine-tune activation under its fixed rule
if safety, accepted outcomes, provider-equivalent cost, wall time, human minutes, consent, instrument
isolation or rollback loses. An absent eligible candidate is inconclusive, not a pass.

[asserted] Matrix factorisation remains rejected until ADR-0025's conjunction holds—about 5,000
structured, model-attributed labelled routing outcomes and an applicable measured wasted-work
multiplier of at least 2×—and a separately pre-registered time-and-new-model holdout shows MF beating
the static frontier, empirical and KNN baselines without worsening beta, alpha, missingness or
cold-start refusal.

[asserted] One unqualified revision becoming routable, one forged/delegated principal approval, one
withdrawn datum consumed, one candidate-visible instrument or one rollback that does not restore
exact bytes overturns the activation design immediately.

## Publication candidate?

No. [asserted] It is an internal, provisional lifecycle decision tied to private evidence and
unimplemented controls. A public treatment must wait for measured results and remove instance detail.

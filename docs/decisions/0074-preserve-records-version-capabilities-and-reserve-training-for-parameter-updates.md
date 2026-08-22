# 0074. Preserve records, version capabilities and reserve training for parameter updates

- **Status:** PROVISIONAL — EXP-101 can kill automatic capability reuse and can confirm it only
  for the frozen task mixture. [asserted]
- **Date:** 2026-08-22. [measured]
- **Deciders:** Joe Brown supplied the product requirement recorded in
  `../00-context/the-machine-2026-08-22.md`; Codex dispatch
  `20260822T122851-6fe9119269` owns this provisional mechanism, which he has not reviewed.
  [measured]
- **Inquiry tier reached:** T1 — grounded in the live implementation, EXP-45 and retrievable
  external work; the outcome decision is deferred to EXP-101. [measured]
- **Executable model:** none — the immediate decision is a categorical storage, identity and
  training boundary; EXP-101 is the executable outcome comparison. [asserted]

## Context

**Correction:** Consilient already has deterministic skill selection and a private,
trajectory-backed adapted-instruction layer, but dispatch does not use that assembly; its storage is
not durability-perfect or retrieval-complete, and EXP-45's committed 20 August snapshot reported
59.29% mechanically extracted entity loss, not consequential loss. [measured]

The principal requires a Machine that retains created capabilities, has “perfect” memory and makes
deep study persist in training as well as memory. These are three different technical claims:
durable records, bounded retrieval, and model parameter change. Treating them as one would permit a
prompt update to masquerade as training and an append-only filename to masquerade as recall.
[measured: `../00-context/the-machine-2026-08-22.md`] [asserted]

The current trajectory retains valid events that were captured, but a general append has neither a
cross-process lock nor `fsync`; malformed lines are excluded from recall; dispatch retains outcome
metadata rather than transcript and artefact bodies; and `recall.py` removes the oldest selected
events until its 8,000-character bound fits. [measured]

`capabilities.py` validates and selects an external inventory fail-closed, while
`instructions.py` can select skills and reconstruct reversible adapted instructions. Neither gives
a successful capability durable identity, version, outcome history or duplicate control, and
production dispatch does not call the instruction assembly. [measured]

This is reversible as a product decision. The archive and explicit retrieval remain useful if
automatic reuse fails; projections and selectors can be removed without rewriting the event
history. [asserted]

## Decision

We will distinguish **record**, **recall**, **capability** and **training** at the event schema and
projection boundaries. [asserted]

1. Acknowledged retained content will be immutable, content-addressed and private, linked from the
   existing append-only trajectory; SQLite remains a rebuildable projection, not an authority.
   [asserted]
2. “Perfect recall” will mean integrity-checked addressability plus an honest bounded-retrieval
   receipt. Scan and context completeness are reported separately; semantic status is `unknown`
   outside a frozen gold bank, where raw critical loss is measured. [asserted]
3. Capabilities will carry immutable manifests and provenance. Payloads deduplicate by digest, but
   manifests merge only across equivalent purpose/postcondition, interface, permission, trust,
   verifier semantics, provenance and licence. At most one head per execution-contract/destination
   class is selectable; superseded and inactive history remains addressable. [asserted]
   Recall and capability selection will enforce workspace, consent and destination boundaries before
   content enters a harness context. [asserted]
4. `capabilities.py` remains the only selector, `instructions.py` the assembler, `dispatch.py` the
   caller, `events.py` the authoritative state writer and `projection.py` disposable. No second
   memory service, loader, router or orchestrator is introduced. [asserted]
5. Retrieval ends at any persistent mutation of learned model state. Training is a data-driven
   fitting or editing mutation, whether optimiser, closed-form or direct; checkpoint emission is an
   admission requirement, not part of classification. Computing embeddings is retrieval, while
   fitting their model is training. All persistent learned-state changes receive provenance and
   quarantine, and model weights never replace the source archive. [asserted]
6. Wrong or stale facts are corrected by append-only supersession/invalidation and temporal
   validity, never destructive rewrite. Supported conflicts return `contested`; external claims
   past their recheck condition return stale until refreshed from source. [asserted]
7. Automatic capability reuse stays inert until EXP-101 improves blinded joint outcomes against the
   same capable Owner without the library, under equal budget, without cost or alpha/beta regression.
   Experiment-only eligibility is isolated and promotes no capability; product `active` remains
   exclusive to an ADR-0018-valid promotion. Capture and explicit/manual selection do not depend on
   that activation result. [asserted]

The detailed fields, retrieval-loss measure, acceptance conditions and training procedure are fixed
in `../superpowers/specs/2026-08-22-memory-and-capability.md`. [asserted]

## Evidence

- `[measured]` `events.py`, `projection.py`, `recall.py`, `capabilities.py`, `instructions.py` and
  `dispatch.py` already form the reusable storage-to-context path described above; the missing
  durability, identity, outcome and wiring properties are visible in those sources on 22 August
  2026.
- `[measured]` EXP-45's committed snapshot covered 1,495 files/203 sessions, retained 40.71% of
  mechanically extracted entities and observed a 0.00% consequential-loss proxy; it recorded no
  reproducible private-corpus digest. A 22 August rerun over 1,725 files/266 sessions reported
  42.35% retention with the consequential verdict unchanged. Its limitations exclude silent
  semantic loss and paraphrased retention.
- `[measured]` The frozen external organisation bar requires a single accountable Owner comparator,
  provenance-bearing artefacts, independent execution/source evidence and downstream outcomes;
  EXP-101 uses that shape rather than agent agreement.
- `[cited]` Rasmussen et al. (2025), *Zep: A Temporal Knowledge Graph Architecture for Agent
  Memory*, arXiv:2501.13956, https://arxiv.org/abs/2501.13956 — temporal validity and provenance are
  the relevant incumbent mechanism; its vendor benchmark points are not adopted.
- `[cited]` Dey and Viradecha (2026), *Spatial Metaphors for LLM Memory: A Critical Analysis of the
  MemPalace Architecture*, arXiv:2604.21284, https://arxiv.org/abs/2604.21284 — supports verbatim,
  deterministic local storage while warning that the spatial metaphor is not the measured cause of
  the reported result.
- `[cited]` Official Google and NVIDIA skill repositories expose catalogues and versioned reusable
  instruction packages: https://github.com/google/skills and https://github.com/NVIDIA/skills.
  Discovery is therefore an incumbent feature, not evidence of outcome improvement.
- `[algebra]` For any frozen question bank, weighted retrieval loss is bounded in `[0, 1]`, because
  omitted non-negative gold-record weight cannot exceed total gold-record weight.
- `[asserted]` Separating payload deduplication from semantic manifest equivalence, then allowing one
  selectable head per execution-contract/destination class, is the smallest rule found that
  preserves provenance while bounding the automatic surface.

## Evidence against

The strongest case is that accumulated memory makes the Machine worse. Bounded context means old,
highly matched material can displace fresh evidence; a confidently wrong retrieval can anchor the
Owner; and multiple nearly identical procedures can produce inconsistent selection and negative
transfer. ADR-0030 provisionally prefers compact retrieval because full history may crowd fresh
evidence out; that performance rationale remains asserted rather than measured. [asserted]

Training makes the objection irreversible. Indiscriminate recursive training on model-generated
data caused distribution tails to disappear across the studied generative models. [cited:
Shumailov et al. (2024), *AI models collapse when trained on recursively generated data*, Nature
631, https://doi.org/10.1038/s41586-024-07566-y]

That result is conditional rather than universal: accumulating synthetic generations alongside the
original real data avoided collapse in the tested language and generative-model settings, whereas
replacing the real data did not. [cited: Gerstgrasser et al. (2024), *Is Model Collapse Inevitable?
Breaking the Curse of Recursion by Accumulating Real and Synthetic Data*, arXiv:2404.01413,
https://arxiv.org/abs/2404.01413]

The mitigation — bounded selectable heads, temporal invalidation, source confirmation, explicit
semantic unknowns, preserved real/adverse/corrective observations and held-out comparison — reduces
but does not eliminate stale retrieval, semantic omission or negative transfer. “Perfect” is
therefore limited to the named retention/addressability contract and feasible frozen recall bank.
[asserted]

A second serious objection is that Graphiti, MemPalace or an existing skills registry should be
adopted instead of extending Consilient. They clear useful sub-bars, but none is the authoritative
choice here: Graphiti adds a dependency and vendor-authored evaluation, MemPalace's critical
analysis disputes its claimed causal mechanism, and registries package skills without measuring
joint outcome lift or verifier error. They remain P2 candidates against the stdlib exact/SQLite
baseline rather than becoming a second source of truth now. [cited] [asserted]

Known weaknesses are material: no crash/concurrency durability fixture has yet passed; the proposed
retrieval bank does not exist; EXP-101 is blocked; the MemPalace paper is one critical analysis;
and no local fine-tune result establishes that deep study belongs in weights. [measured]

## Consequences

**Positive** — acknowledged material has an auditable preservation boundary; every bounded recall
exposes omissions; capabilities can be reused or reversed by stable version; stale facts do not
silently overwrite history; and retrieval cannot be renamed training. [asserted]

**Negative** — durable payload capture consumes private disk and write latency; receipts consume
context; temporal validity and contract keys demand metadata; strict deduplication can quarantine a
useful variant; and the outcome gate may leave automatic reuse inert indefinitely. [asserted]

**Neutral but load-bearing** — a single local copy is not disaster-proof; explicit deletion and
retention policy override “never lost”; model checkpoints are capabilities but not memory authority;
the principal's reserved approvals, spend, publication and gate decisions cannot be inferred from
historical records; and all gates remain unchanged. [asserted]

## Enforcement

This ADR and EXP-101 register the contract; they do not implement or activate it. Existing privacy,
AST, commit-attribution and provisional-ADR checks continue to run, but no current CI check proves
durable acknowledgement, recall coverage or capability uniqueness. [measured]

Each later implementation increment must add its executable invariant in the same commit:
[asserted]

- crash and concurrent-writer fixtures prove that every acknowledged object/event pair re-reads by
  digest; [asserted]
- recall tests keep semantic status `unknown` outside a bank, require zero raw critical loss and
  full scan/context completion on its feasible arm, and require valid continuation on overflow;
  [asserted]
- projection tests exercise semantic-key collision and trivial-evasion fixtures, fail two
  selectable heads per execution-contract/destination class, and reconstruct every supersession;
  [asserted]
- event validation records optimiser, closed-form, direct-edit, embedding-fit and failed-checkpoint
  mutations under the training/model-change boundary, with an admitted result requiring base,
  dataset, update-run and checkpoint digests; [asserted]
- privacy checks keep payload, capability and training stores ignored and reject credential values;
  [asserted]
- context-assembly tests refuse cross-root, unconsented-destination and escaping capability paths
  without rendering their content; [asserted]
- EXP-101 alone can admit the library-level selection policy for its frozen supervised mixture; it
  promotes no member and no result changes `routing_orchestration_enabled`, Gate A or Gate B.
  [asserted]

- **Check:** future focused tests plus the existing `test_v0_invariants.py`, privacy scanner and
  record-number checker. [asserted]
- **Fails CI:** no for the future checks today; yes when each implementation lands. [measured]
- **Added in the same commit as the implementation:** this commit has no implementation; same-commit
  enforcement is a condition of every later increment. [measured] [asserted]

## What would overturn this

- EXP-101 kills automatic capability selection if reuse does not improve joint success, harms the
  no-applicable-capability stratum, worsens a mature alpha/beta bound by more than 0.05, or causes an
  irreversible/exposed action through a stale or wrong capability. The archive and explicit/manual
  retrieval remain. [asserted]
- Any raw critical loss or incomplete scan/context result on the feasible bank overturns its
  “perfect critical recall” label; any overflow query without a valid continuation also blocks
  activation. [asserted]
- A crash or concurrent-write test that loses an acknowledged record overturns the durability
  contract; changing the wording instead of the writer is not an admissible repair. [asserted]
- A matched held-out local run in which training loses to retrieval, or synthetic recursion loses
  source-distribution tails, quarantines that checkpoint and removes training from that task's
  preferred path. [asserted]
- A dependency that beats exact/SQLite retrieval on retrieval loss, stale-return rate, latency,
  privacy and maintenance burden can replace the P2 retrieval implementation without changing this
  boundary. [asserted]

## Publication candidate?

**No.** This is a provisional product boundary with no completed retrieval or capability outcome
experiment. A later negative or replicated result may be publishable; this ADR is not. [asserted]

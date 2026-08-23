# 0097. Keep automatic triggered recall inert until it beats deliberate pull

- **Status:** PROVISIONAL — EXP-140 can kill v1 or support a later principal-authored activation ADR
  only for its frozen task mixture; it cannot activate anything, and a null, unsafe or pull-inferior
  result leaves v1 inert. [asserted]
- **Date:** 2026-08-23. [measured]
- **Deciders:** Joe Brown supplied the requirement for conversation-triggered recall; Codex dispatch
  `20260823T141205-7b49934919` records the provisional mechanism, which he has not reviewed.
  [measured]
- **Inquiry tier reached:** T2 — the live assembly/recall path and first-party incumbent sources were
  inspected; T3 is preregistered as EXP-140 and has not run. [measured]
- **Executable model:** none — this is a reversible specification decision and EXP-140 is the
  executable outcome comparison. [asserted]

## Context

**Correction:** EXP-45's committed snapshot measured 59.29% loss of mechanically extracted entities
and a 0.00% observed consequential-loss proxy; it did not measure that condensation lost about 59%
of what mattered. [measured] Verbatim recall remains ADR-0074's integrity-preserving contract, but
EXP-45 does not establish that it improves accepted outcomes. [measured] [asserted]

The principal requires memories to surface when a conversation triggers them, before reasoning,
because an agent cannot deliberately search for a forgotten fact it does not know to request.
[measured] Current Consilient recall is pull-like assembly from token overlap plus unconditional event
kinds, bounded by removing old selected events until 8,000 characters fit. [measured] It has no
numeric threshold, decision-relevance feature, temporal-head filter or per-turn latency contract.
[measured]

An injected memory is not neutral. [asserted] It enters privileged context before the model has
understood the task, can reproduce instruction-shaped text, consumes finite budget and can turn a
prior conclusion into apparent corroboration. [asserted] ADR-0030 forbids solving that pressure by
silently truncating the task, and ADR-0081 gives repeated context and model conclusions no independent
evidential credit. [measured]

The premise that nobody already performs automatic pre-reasoning recall is false. [cited] Zep
retrieves and prepends relevant user memory before every AutoGen model turn; Mem0's OpenClaw
integration retrieves and prepends reranked memories before turns by default; and Ruflo's pinned
`UserPromptSubmit` hook scores the current prompt and emits persistent ranked context before Claude
processes it. [cited: [Zep](https://help.getzep.com/autogen-memory),
[Mem0](https://docs.mem0.ai/integrations/openclaw),
[Ruflo settings](https://github.com/ruvnet/ruflo/blob/3c99b1c/.claude/settings.json),
[route handler](https://github.com/ruvnet/ruflo/blob/3c99b1c/.claude/helpers/hook-handler.cjs)]
The decision is therefore about a narrower auditable and harm-bounded combination, not invention of
automatic recall. [asserted]

## Decision

Keep automatic triggered recall inactive while specifying it as the smallest extension of M02
temporal projection, M03 auditable bounded recall and the existing `instructions.py` recall layer.
[asserted] Do not add a store, prompt layer, writer, vector service, daemon, network/model scorer, CLI
subcommand or second orchestrator. [asserted]

1. **Boundary.** After an authenticated first-party turn or dispatch task is sealed and the accepted
   trajectory prefix is frozen, but before model selection and the first model request, build one
   trigger from the full current message, exact active commitment and sealed same-conversation delta.
   [asserted] Recalled text, tool output and agent prose never retrigger recall. [asserted]
2. **Candidates and score.** M02 supplies privacy-eligible current heads or complete contested sets
   from a disposable SQLite projection. [asserted] M03 unions one FTS5 lookup with exact links, caps the pool at 32 and computes
   `score = 0.65D + 0.25S + 0.10C`, where `D` is an exact shared decision/object key, `S` is bounded
   weighted trigram Jaccard similarity and `C` marks a current correction/refusal/adverse outcome/
   authority/verifier record for the same linked object. [asserted]
3. **High threshold.** Version v1 fixes `n = 0.85`, admits at most three bundles and never adapts
   online. [asserted] Similarity alone contributes at most `0.25` and therefore cannot surface an
   unlinked lookalike. [algebra] Any changed weight, feature, cap or threshold requires a new scorer
   version and preregistered experiment. [asserted]
4. **Hot path.** The incremental selector makes one local indexed query, rescoring at most 32 rows,
   with zero model/network/subprocess calls, a 25 ms p95 target and a hard 50 ms deadline. [asserted]
   Deadline, prefix, projection, privacy or corruption failure produces no automatic context and an
   explicit receipt; pull search remains available. [asserted]
5. **Budget.** Visible memory, headers and forming context share the existing 8,000-character recall
   cap and only headroom admitted by a pinned conservative estimator and authoritative versioned
   model-capacity field. [asserted] The full task, invariant core, active
   commitment/authority, required evidence and skills, and reserved output are protected. [asserted]
   Lowest-scoring recall is evicted first; a memory that cannot fit with its complete forming span is
   wholly omitted `context_bound`, never summarised or truncated. [asserted]
6. **Provenance, privacy and time.** A surfaced record includes its exact linked first-party forming
   turn and response/outcome, source/digest IDs, `formed_at`, validity interval, current status and
   supersession chain. [asserted] Missing exact links refuse rather than infer context from temporal
   adjacency. [asserted] ADR-0057 establishes private-by-default while ADR-0074 requires recall
   boundaries; this decision supplies the currently absent user/workspace, consent, destination and
   retention metadata checks before payload access. [measured] [asserted] Superseded/invalidated records never appear alone as current truth;
   contested claims surface atomically or not at all. [asserted]
7. **Echo.** Every bundle renders `anchor_eligible: false`. [asserted] Recall inherits its writer's
   evidence class and derivation root, creates no ADR-0081 anchor and cannot duplicate an original
   world-touching source's single credit. [asserted]
8. **Receipt.** Version M03's canonical in-pack JSON receipt while preserving `pack(...) -> str` and
   v1 parser compatibility. [asserted] V2 adds the frozen prefix/projection/trigger digests, scorer
   version and threshold, every candidate's score components/disposition, selected source/content
   digests, budget/refusal state and pre-request latencies. [asserted] `instructions.assembled` binds
   its digest and pre-run references; the existing dispatch outcome later binds model usage, cost and
   outcome references. [asserted] Reconstruction replays those identities or refuses drift.
   [asserted]
9. **Activation.** EXP-140 must improve joint verifier-plus-blinded-human accepted outcomes by at
   least `+0.10` against both no memory and deliberate pull, with multiplicity-adjusted lower bounds
   above zero, no worse cost per accepted outcome than pull, and the registered precision, recall,
   false-surfacing and instruction-shaped/stale safety floors. [asserted] Every other result leaves
   automatic recall inert and pull retrieval as the default. [asserted]

The trigger, formula, budget, receipt, bounded incumbent table, refusal states, experiment summary
and future test obligations are fixed in
`../superpowers/specs/2026-08-23-triggered-recall.md`. [measured]

## Evidence

- `recall.py` already renders selected trajectory events verbatim and bounds the pack; extending M03
  preserves one retrieval/receipt surface. [measured]
- `instructions.py` already assembles invariant, skill, recall and adapted layers, records digests and
  reconstructs against a pinned accepted prefix; adding a fifth layer would duplicate that
  chokepoint. [measured] Current dispatch selects a model before this assembly, so ADR-0030's exact
  pre-selection estimate remains a prospective ordering fix. [measured]
- ADR-0074 specifies append-only supersession and temporal validity; M02 now implements deterministic
  current/historical/invalidated/contested record heads; and M03 specifies bounded verbatim retrieval
  with explicit omissions and a continuation. [measured]
- Zep links derived facts to raw episodes and carries temporal validity/invalidation; this is the
  incumbent provenance/staleness bar, not evidence for a novel Consilient mechanism. [cited:
  [episode provenance](https://help.getzep.com/episode-metadata-projection),
  [facts](https://help.getzep.com/facts)]
- Mem0's history endpoint records the conversation input and old/new values for memory changes, while
  Claude past-chat search cites original chats; forming-context provenance is therefore an incumbent
  capability, although neither reviewed automatic prompt contract guarantees the complete inline
  source span specified here. [cited: [Mem0 history](https://docs.mem0.ai/api-reference/memory/history-memory),
  [Claude memory](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context)]
- Ruflo's pinned automatic path uses trigram Jaccard plus PageRank, threshold `0.05` and top five;
  deterministic local pre-prompt scoring is already shipped prior art. [cited:
  [pinned scorer](https://github.com/ruvnet/ruflo/blob/3c99b1c/.claude/helpers/intelligence.cjs)]
- The v1 threshold, weights, caps and latency limits are conservative acceptance defaults; no local
  outcome or timing measurement validates them yet. [asserted]

## Evidence against

Automatic recall may be prompt pollution by construction. [asserted] It must decide before the model
understands the planned decision or action, whereas deliberate pull can form a need-specific query
after reading the task. [asserted] Semantic or lexical resemblance cannot establish usefulness, and
an irrelevant memory is unavoidable context that both spends budget and steers reasoning. [asserted]
The raw forming conversation makes provenance auditable but also enlarges the instruction-shaped
attack surface. [asserted] A heading cannot guarantee that a model demotes old imperatives.
[asserted]

Prior research reports degraded question answering from irrelevant context and distraction from
irrelevant retrieved passages. [cited: [Shi et al., ICML 2023](https://proceedings.mlr.press/v202/shi23a.html),
[Amiraz et al., ACL 2025](https://aclanthology.org/2025.acl-long.892/)] Applicability to this frozen
coding-task mixture is unmeasured. [asserted]

The strongest local counterevidence is adverse to the objection: EXP-57's plausible-padding branch
did not find its 41,686-token padded condition worse than full context; its recorded error-difference
interval was `[-0.0330, +0.0671]`. [measured] Prompt-pollution harm must therefore remain asserted,
not relabelled as a local measurement. [asserted]

The answer is a concession. [asserted] Keep deliberate pull excellent and automatic recall inert.
[asserted] High threshold, atomic context, temporal filtering and echo labels reduce exposure but do
not make a false positive harmless. [asserted] If triggered recall is null, helps only against no
memory, loses to pull, fails a safety floor or lacks enough safety observations, pull wins and no
automatic layer activates. [asserted]

## Consequences

- The design reuses the current record/projection/recall/assembly path and introduces no second
  authority or implementation surface. [asserted]
- Every automatic memory is a current head or complete contested set, decision-linked, bounded,
  verbatim, source-linked, dated and explicitly non-independent, or it is absent with a receipt.
  [asserted]
- Precision is deliberately favoured over recall; useful but unlinked memories will be missed.
  [asserted]
- Whole forming context may consume most of the recall allowance, so the safe result on many turns
  may be no automatic memory. [asserted]
- M01's missing provenance/privacy/link fields, M02's missing candidate/prefix/privacy fields, M03,
  explicit destination/consent input, ADR-0081 admission and conservative pre-selection context
  admission against an authoritative model-capacity field are blocking dependencies; current code
  does not satisfy this decision. [measured]
- Pull retrieval, accepted append-only record history, supersession and receipts survive a failed
  experiment and make reversal cheap. [asserted]

## Enforcement

No implementation is authorised by this ADR. [measured] A later implementation must ship with the
checks named in the companion specification in the same commit. [asserted] The load-bearing echo
check is
`tests/test_decision_protocol.py::test_surfaced_recall_never_creates_a_structural_anchor`: one
original eligible source plus any number of recalled copies must still yield one anchor, while a
self-authored recalled conclusion alone yields zero and refuses high-consequence admission.
[asserted]

Additional checks must pin the pre-first-request boundary, exact-link gate, fixed score/threshold/
caps, privacy-before-payload ordering, atomic no-truncation budget, temporal states, deterministic
receipt reconstruction, fail-empty deadline and non-recursive handling of instruction-shaped recall.
[asserted] `events.py` remains the single writer; `src/consilient/` remains dependency-, network-,
subprocess- and credential-free; the CLI and all gate conditions remain unchanged. [asserted]

## What would overturn this

EXP-140 is the registered killing experiment. [measured] It runs 120 paired task triples across
necessary-memory, helpful-memory and no-useful-memory strata under no memory, deliberate pull and
triggered-plus-pull. [asserted] Human usefulness labels and blinded outcome verdicts are sealed before
analysis; false surfacing, useful-memory recall, harmful discordance, latency, tokens and cost are
reported alongside the joint accepted outcome. [asserted]

The run stops after all 120 triples or 120 days, without efficacy peeking or replacement; missing or
invalid arms score failure. [asserted] Confirmation requires both registered outcome improvements and
all safety/cost floors. [asserted] A null, benefit only over no memory, interval spanning zero,
insufficient safety denominator, pull loss or safety breach keeps v1 inert. [asserted] One stale or
instruction-shaped memory causing an undeclared write/external effect or being treated as authority
kills any later activation proposal. [asserted]

For this task-bank design, the conservative accepted-outcome difference envelope is `[-1, +2/3]`:
automatic context can plausibly poison every stratum, while the two useful-memory strata bound its
designed upside. [asserted] [algebra] The unconstrained paired-difference bound is `[-1, +1]`.
[algebra]

## Publication candidate?

No. The mechanism is unimplemented, the activation result is unknown and the broad novelty premise
has been rejected by primary-source prior art. [measured] [cited]

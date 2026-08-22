# 0070. Make chat a compiler to versioned work-item commitments before dispatch

**Correction:** the brief's zero-byte attempts were not three scope-caused timeouts, and EXP-45
measured mechanical surface-entity retention rather than whether “what mattered” survived.
[measured: local trajectory census; EXP-45]

- **Status:** PROPOSED
- **Date:** 2026-08-22
- **Deciders:** none yet — proposed by Codex dispatch `20260822T125228-b433fe6667`; principal
  adoption is not claimed. [measured]
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — this is a categorical identity, ordering and authority protocol;
  human interaction burden is unmeasured, so a numeric objective would manufacture parameters.
  [asserted]

## Context

The principal asked for a chat surface that orchestrates independently rather than requiring
traditional commands, and asked this stream to specify intake only. [measured:
`docs/00-context/the-machine-2026-08-22.md`; dispatch brief]

The implemented control plane accepts an exact task string or task file, then `scripts/dispatch.py`
writes run artefacts and dispatch outcomes. It has no conversation identity, turn identity, frozen
success/non-goal contract, commitment revision, supersession chain or delivery hand-off.
[measured: current tree]

The trajectory is already the authoritative append-only record, `work_items.py` is already the task
substrate, `recall.py` already supplies bounded verbatim context, and ADR-0068 already owns planning.
[measured] [cited: ADR-0006; ADR-0068] A new chat store or orchestrator would create another source of truth rather
than close the intake gap. [asserted]

This decision contains one-way doors. If an outcome is judged against criteria edited after the
result, the evidence cannot later recover the original test; if an agent can forge principal
authority, later provenance cannot recover authorship; and once downstream events cite an event
identity, changing its schema or meaning has migration cost. [algebra]

## Decision

Chat will be a projection and compiler over the existing trajectory. It will preserve sanitised
user turns verbatim, resolve factual and reversible ambiguity itself, ask at most one question only
for an otherwise-unresolvable principal-only decision, and append a centrally validated,
versioned `work_item.committed` request record before planning or execution. ADR-0068 will append a
plan against the immutable commitment digest; each plan stream will then become a plan-bound
`work_item.opened` carrying `item_schema: "native.v1"`; and the delivery stream will consume the
`DeliveryIntake` projection defined in `2026-08-22-chat-conversation.md`. Historical dispatch-claim
events without that discriminator remain replayable but become read-only when native items are
activated. Every downstream record will cite the exact commitment revision and digest. A correction
will append a superseding commitment and fence the old digest rather than edit history. [asserted]

ADR-0067 continues to supply the composition rule: one accountable Owner by default, with another
member admitted only for a non-overlapping, decision-changing evidence anchor. [cited: ADR-0067]
`routing.py` will not be represented as choosing member count; it bounds candidate attempts against
one verifier contract when beta is available and currently refuses the real-trajectory bridge while
human beta is unmeasured. [measured: `src/consilient/routing.py`]

The command line remains the automation, diagnosis and recovery control plane. Chat does not add a
`consil` subcommand, become an authority source, or bypass the existing dispatch script. [asserted]

## Evidence

- `[measured]` `scripts/dispatch.py` accepts one string or task file, transforms it with capability
  context, writes mutable `brief.md` and `recall.md`, and has no structured commitment-to-delivery
  boundary.
- `[measured]` `work_items.py` already owns the native opened/comment/completed event domain, so a
  distinct request-level `work_item.committed` kind extends that substrate without adding a store.
- `[measured]` `work_items.validate()` checks work-item fields, but central `events.append()` calls
  only `events.validate()`; generic append can therefore bypass the helper's rules.
- `[measured]` `events.prefix_digest()` can detect an edit only against a retained earlier digest,
  and `bypassed()` explicitly cannot identify a canonical direct writer. The current trajectory is
  not cryptographically tamper-evident or authenticated.
- `[measured]` V0-18 accepts human authority only through locally declared CLI provenance; the
  current tree has no authenticated chat ingress. Chat therefore cannot presently author protected
  decisions.
- `[measured]` EXP-45 retained 40.71% of mechanically extracted surface entities, observed a 0.00%
  aggregate consequential-loss proxy, and explicitly left silent semantic errors and paraphrase
  outside its measurement. It supports bounded verbatim recall plus protected records, not a claim
  that summaries preserve every constraint.
- `[measured]` The zero-artefact attempts cited by the brief comprise one timeout and two pre-launch
  fail-closed refusals for unknown Cursor headroom; they do not measure that whole-surface scope
  caused failure.
- `[cited]` The frozen organisation bar requires one accountable Owner, structured persistent
  artefacts, explicit authority, termination bounds and evidence independent of model confidence.
  (`docs/00-context/agentic-organisation-bar-2026-08-22.md`)
- `[cited]` ADR-0068 freezes the smallest verifiable dependency graph only after a success contract
  exists, so the commitment must precede and be cited by the plan.
- `[cited]` The frozen product bar names ChatGPT Work as the strongest general delegated-work
  product while finding specialist advantages elsewhere; it also finds no joined public proof of
  outcome, verifier error, deadline, authority and review burden. The relevant gap is evidence, not
  another feature list. (`docs/00-context/product-bar-2026-08-22.md`)
- `[asserted]` One question is the smallest budget that can resolve a genuine principal-only choice
  without fabricating consent; permitting more recreates the approval and interrogation burden the
  surface is intended to remove.
- `[asserted]` A canonical commitment digest, downstream references, a retained trajectory-prefix
  anchor and a user-visible short digest make an edit at or before the commitment evident when an
  anchor survives; they do not detect later-event reordering, and signing or external anchoring is
  still required against a whole-log attacker.

## Evidence against

- `[measured]` The command-line path already exists and is explicit, inspectable, scriptable and
  replayable. This user is technically capable of invoking it. Chat adds a semantic interpreter
  whose commitment error rate has not been measured.
- `[asserted]` A visible command exposes flags and state; a fluent chat response can conceal defaults,
  inferred scope and omitted constraints while making the interaction feel easier. The commitment
  card may move that risk rather than remove it.
- `[asserted]` The one-question maximum may under-clarify a request whose ambiguities interact. The
  design chooses reversible defaults, but a plausible default can still waste work before a
  correction arrives.
- `[measured]` No registered experiment directly tests this complete intake protocol, its question
  budget or chat-versus-command interaction cost. EXP-45 bears only on condensation, and EXP-53 is
  READY but unrun and bears only on signing cost and coverage.
- `[measured]` The current trajectory supplies neither authenticated authorship nor independently
  anchored integrity. A chat capable of protected actions would be unsafe on the present ingress.
- `[asserted]` Mature incumbents already provide polished chat, continuity and delegated work. This
  proposal has no measured usability advantage over them or over the local command line.

These objections prevent acceptance, not specification. [asserted] The proposed architecture keeps
the command line intact, makes every inference inspectable before outcomes exist, and supplies a
testable seam at which chat can be rejected without replacing the orchestrator. [asserted]

## Consequences

**Positive** — Every execution can be joined to the exact user words, interpretation, success
boundary, authority, plan and later correction against which it must be judged. [asserted]

**Positive** — Ordinary factual and reversible ambiguity consumes no principal review turn, while
the sole unresolved principal decision remains visibly reserved. [asserted]

**Positive** — Delivery receives one stable `DeliveryIntake` contract rather than chat prose or a
mutable run directory. [asserted]

**Negative** — Intake needs new centrally enforced event schemas, authenticated ingress before
protected authority, revision fencing, and UI projection tests. None is implemented by this ADR.
[measured] [asserted]

**Negative** — The one-question policy deliberately accepts more machine-made reversible decisions
and therefore some avoidable rework. [asserted]

**Negative** — Content and prefix digests add only retained-anchor tamper evidence; describing them
as signatures would create a false security claim. [asserted]

**Neutral but load-bearing** — ADR-0068 owns plan construction, the delivery specification owns
estimates through completion, ADR-0067 owns composition, and `scripts/dispatch.py` remains the sole
orchestrator. [cited: ADR-0067; ADR-0068] [asserted]

**Neutral but load-bearing** — Request-level `work_item.committed` is distinct from the plan-bound
`work_item.opened` schema fixed by ADR-0072. New native opened events carry an explicit schema
discriminator; replayed legacy dispatch claims lack it and are never admitted as new appends after
activation. [asserted] A future task view or chat card is only a projection and cannot acquire
independent lifecycle authority. [asserted]

**Neutral but load-bearing** — ADR-0068's duration ranges are preserved as schedule inputs;
ADR-0071's `delivery.estimate` chain is the sole rendered delivery promise. [cited: ADR-0068;
ADR-0071] [asserted]

## Enforcement

This PROPOSED ADR changes no product behaviour. Its invariants become real only with the following
same-commit implementation checks. [measured] [asserted]

- Check: pure `events.validate()` enforces shape, actor and content digests; central
  `events.append()` acquires one per-log lock, reprojects state and invokes
  `work_items.validate_transition()` for revision uniqueness, supersession and fencing before the
  same locked write. Concurrent tests call generic append to prove helpers cannot be bypassed and
  duplicate revisions cannot race through. [asserted]
- Check: a state-machine/property test proves question count is zero for factual and reversible
  ambiguity, never exceeds one for principal-only ambiguity, and cannot bundle decisions or loop on
  an unclear answer. [asserted]
- Check: an ordering test refuses claim or dispatch before matching commitment, ADR-0068 plan,
  plan-bound work-item and delivery-estimate digests exist. [asserted]
- Check: a frozen legacy `work_item.opened` fixture remains readable, while generic append refuses
  that shape after activation and accepts only `item_schema: "native.v1"`; dispatch migrates in the
  same commit. [asserted]
- Check: a correction-race test prevents completion under a superseded digest and preserves the
  stale attempt as an adverse outcome. [asserted]
- Check: an ingress test rejects self-declared, replayed and non-principal authority and proves
  secret fixture bytes and hashes never enter the trajectory. [asserted]
- Check: a projection mutation test changes each commitment field and proves the visible card or
  downstream reference detects the mismatch against a retained anchor. [asserted]
- Fails CI: **no today**; these tests do not exist because this is a specification-only commit.
  [measured]
- Added in the same commit as the implementation: **required yes**. [asserted]

## What would overturn this

Before this ADR can move beyond PROPOSED, register a matched chat-versus-command trial on genuine
one-sentence requests with the same Owner, tools, harnesses, budget and success oracle. Freeze each
surface's commitment before execution; have a blinded assessor compare it with the principal's
post-task correction; retain refusals, timeouts, quarantines, missing artefacts and authority
violations in the assigned arm. Measure material commitment corrections, user turns, user-active
time, accepted outcomes, resume/replay correctness and correction latency. [asserted]

Reject chat as the default if it fails to reduce either user turns or user-active time, increases
material commitment corrections, produces any agent-authored principal event, or cannot replay the
same commitment after restart. [asserted] Keep the command line alone if authenticated ingress and
retained-anchor integrity cannot be implemented without adding another authority or state store.
[asserted]

A property-test counterexample in which the one-question rule necessarily fabricates an irreversible
choice also overturns the fixed question budget; the replacement must preserve the rule that the
machine cannot launder its decision into principal authorship. [asserted]

## Publication candidate?

**No.** This is an unimplemented local product decision with no direct chat-versus-command
measurement. [measured]

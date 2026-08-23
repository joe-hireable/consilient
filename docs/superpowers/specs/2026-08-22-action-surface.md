# Action surface: unconstrained output, constrained actuation

**Corrections:** `events.py` is the intended append path for cooperating product code, not an
enforced or durable single writer, and today's non-file adapters can perform an effect before their
event is appended. The brief's claim that the exposure formula gives one candidate for every
ceiling at or below `0.40` is also arithmetically false: a ceiling below the applicable beta bound
permits zero. The present record therefore does **not** support a safety claim for unconstrained
output or live candidate exposure. [measured: `src/consilient/events.py:1071-1086`,
`src/consilient_connectors/outbound.py:193-249`,
`src/consilient_connectors/computer_use.py:242-314`] [algebra]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0078 is PROVISIONAL and EXP-35 plus EXP-59 can kill its core
  mechanism. [asserted]
- **Author:** Codex dispatch `20260822T123850-9436cb33b5`; the product direction comes from the
  principal's recorded words, while every mechanism below is this dispatch's provisional design.
  [measured]
- **Scope:** a future extension of the existing capability inventory, dispatcher, adapters and
  trajectory; this change opens no gate, adds no command and implements no effect boundary.
  [asserted]

## 1. Decision and boundary with ADR-0075

Consilient imposes no second content policy on semantic candidates inside its admitted workspace,
but a candidate obtains no ambient authority to affect the world. Every attempted effect must use
one typed capability adapter behind an outer least-privilege boundary. The boundary admits the
capability, emits the canonical ADR-0075 effect manifest, durably records intent before execution,
and durably records a receipt afterwards. Raw effects that bypass that route are refused by
construction, not discouraged by a prompt. [asserted]

“Completely unconstrained output” therefore means no second Consilient content policy over local
reasoning or drafts. It does **not** mean unrestricted filesystem, process, network, credential,
payment, publication or physical reach. If the phrase requires unmediated actuation, this
specification rejects it because provenance after an effect is not a safety boundary. [asserted]

ADR-0078 determines capability admission and supplies typed effect facts, intent and receipts.
ADR-0075 alone consumes those facts to classify an invocation's reversibility and choose autonomous
execution, local reshaping, refusal or principal escalation. This specification does not create a
second manifest, reversal test, escalation set, decision schema or principal-contact path.
[asserted]

One accountable Owner remains the default. An adapter's fresh provider response, state readback or
independent sensor is a different class of facts; another agent reading the proposed action is not.
[asserted: ADR-0067]

An effect adapter does not add a squad member. The older registered exposure rule is
`n_max = floor(ln(1-e) / ln(1-beta))`; it yields zero whenever `e < beta`, not one for every
`e <= 0.40`. ADR-0077's superseding distribution-free bound likewise yields zero below `q_upper`
and one at the current `e = 0.40` case. Human-labelled beta remains unestimated, so neither
calculation authorises live candidate acceptance. Action-surface widening retains one Owner and at
most one candidate until `routing.py` has measured conditional evidence; adding same-evidence
reviewers cannot substitute for it. [algebra] [measured: ADR-0067 correction, ADR-0077,
`consil beta`, 2026-08-22]

## 2. What exists today

The present surface is fragmented rather than mediated: [measured]

| Surface | Current fact | Consequence |
|---|---|---|
| Files | Dispatch checks the starting cwd, but claims coordinate paths rather than sandbox them; `git diff --stat` is aggregate and misses some file states. [measured: `scripts/dispatch.py:638-654`, `scripts/dispatch.py:1163-1230`] | A child can reach more than the declared claim and no per-file preimage/postimage proves restoration. [measured] |
| Processes | Dispatch uses fixed harness binaries and a process-tree timeout, while harness defaults include vendor permission-bypass flags. [measured: `src/consilient/harness.py:50-59`, `scripts/dispatch.py:535-577`] | Timeout stops future execution; it cannot reverse effects already produced by the process. [asserted] |
| Network and external systems | The browser connector can navigate, fill and click arbitrary HTTP(S) pages before appending `computer.use`. [measured: `src/consilient_connectors/computer_use.py:101-113`, `src/consilient_connectors/computer_use.py:289-314`] | A crash after the click can leave the external change without a trajectory receipt. [asserted] |
| Messages | SMTP and Twilio sends happen before `transport.outbound` is appended. The supplied egress/spend notes are strings, not authenticated principal decisions. [measured: `src/consilient_connectors/outbound.py:78-99`, `src/consilient_connectors/outbound.py:193-249`, `src/consilient_connectors/outbound.py:344-353`] | A sent message can survive a crash with no corresponding record, and the note is not authority. [asserted] |
| Spend | `budget.py` refuses declared loop cost but neither authorises nor mediates provider spending; connector spend is outside that ledger. [measured: `src/consilient/budget.py:1-5`, `src/consilient/budget.py:125-153`] | The current budget check is not a general money boundary. [measured] |
| Publish | The public-remote pre-push hook scans a recognised path but remains a cooperative git hook and emits no publish receipt. [measured: `.githooks/pre-push:5-39`] | It neither covers every publication channel nor proves first-party publication authority. [asserted] |

`events.validate()` has no effect contract for `transport.outbound` or `computer.use`; current
`decision.autonomous` reversal validation is syntactic and its decision class can be omitted.
`events.append()` does not fsync ordinary events or serialise every writer across processes.
[measured: `src/consilient/events.py:247-260`, `src/consilient/events.py:787-838`,
`src/consilient/events.py:1071-1086`]

These are implementation facts, not evidence that an unrecorded effect actually occurred in a live
run. The measured conclusion is narrower: the paths permit an effect/record crash window and do not
structurally prevent bypass. [measured] [asserted]

## 3. Closed action taxonomy

Every invocation carries one or more exact effect values. Unknown, missing, non-text, padded or
case-varied values fail admission. A new value requires a superseding ADR and an exact-set check in
the same implementation commit. [asserted]

The values are: [asserted]

```text
file.change
data.read
process.run
system.change
network.call
external.change
message.send
content.publish
money.commit
obligation.commit
authority.change
physical.actuate
```

The table states the best possible class-level recovery property, not the verdict for an
invocation. ADR-0075's executed proof alone may classify a particular invocation as mechanically
reversible. “Compensation only” means the follow-up may reduce harm but cannot restore the world to
the prior state. [asserted]

| Effect | Includes | Class-level reversibility | Candidate inverse | Evidence required | Irrecoverable or protected residual |
|---|---|---|---|---|---|
| `file.change` | Create, write, rename, move or delete local files. [asserted] | **Conditional.** Only within an admitted root with an immutable preimage or snapshot. [asserted] | Restore every preimage and remove every file created by the operation. [asserted] | Canonical digest and metadata for every scoped object equal the start state, absent objects are absent, and an enclosing-root scan finds no undeclared change. [asserted] | Append-only history, elapsed time, external readers and any copied data remain. [asserted] |
| `data.read` | Read local, brokered or remote data; remote transport also carries `network.call`. [asserted] | **No state inverse.** A read-only action may need no restoration, but access and knowledge cannot be undone. [asserted] | None; discard isolated transient output where its complete confinement is proved. [asserted] | Boundary receipt proves exact source/scope and a confinement check proves no undeclared persistence or egress. [asserted] | Agent/human knowledge, source audit logs, access timing and any provider quota remain. [asserted] |
| `process.run` | Start code, shell commands, compilers, harnesses or background descendants. [asserted] | **No for the run itself.** Termination is containment, not undo; child effects receive their own classes. [asserted] | Stop the complete process tree and apply the inverses for every declared child effect. [asserted] | Fresh process-tree observation proves no descendant remains; linked receipts account for every child effect. [asserted] | CPU time, logs, entropy, observations and escaped child effects remain. [asserted] |
| `system.change` | Change local services, packages, configuration, scheduled jobs or operating-system state. [asserted] | **Conditional.** Only when a transaction, versioned configuration or complete snapshot exists. [asserted] | Roll back the transaction or restore the snapshot and prior service state. [asserted] | Fresh canonical readback, service-health predicates and an enclosing-scope scan match the starting state. [asserted] | Restarts, logs, downtime and effects outside the declared snapshot remain. [asserted] |
| `network.call` | DNS, HTTP, SMTP transport, API reads and any outbound request; mutations also carry their substantive class. [asserted] | **No.** Bytes already disclosed and remote logs cannot be recalled; a pure public read has no target-state inverse. [asserted] | None for the call; revoke a request only when the remote protocol has not accepted it. [asserted] | A provider or boundary receipt can prove what was attempted and accepted, but cannot prove the recipient forgot it. [asserted] | Disclosure, access logs, rate usage, timing and information learned remain. [asserted] |
| `external.change` | Create, update or delete state in a service outside this machine. [asserted] | **Conditional.** Only when the service exposes a versioned inverse and all consequential child effects are declared. [asserted] | Provider rollback, inverse API operation or restoration of a captured version. [asserted] | Provider receipt plus fresh independent readback matches the declared start state and version. [asserted] | Webhooks, audit logs, observers, notifications and downstream copies remain. [asserted] |
| `message.send` | Place text, image, audio or a notification before a person, including the front conversation, terminal/dashboard rendering and remote email, SMS, chat or voice; transport also carries `network.call`. [asserted] | **No. Compensation only.** Retraction or deletion cannot prove unread or forgotten. [asserted] | Provider retract/delete where available, followed by a correction if authorised. [asserted] | Provider status can prove retraction at that provider; no proof can restore the recipient's prior knowledge. [asserted] | Human observation, forwarding, screenshots, reputation and provider logs remain. [asserted] |
| `content.publish` | Make content or data public, change public visibility, push to a public remote or expose a public endpoint. [asserted] | **No. Compensation only.** Origin takedown cannot recall caches or copies. [asserted] | Remove or privatise the origin and invalidate supported caches. [asserted] | Origin readback and independent fetches can prove current origin state, never universal erasure. [asserted] | Copies, mirrors, archives, search indexes, citations and human observation remain. [asserted] |
| `money.commit` | Debit funds, purchase, place an order, accept a paid obligation or create metered liability. [asserted] | **No after commitment. Compensation only.** A void before settlement may prevent commitment. [asserted] | Void, cancel, refund or offset through the provider. [asserted] | Provider and ledger receipts prove the compensation, not restoration of time, fees or counterparty reliance. [asserted] | Fees, tax, credit exposure, opportunity cost, liability and counterparty knowledge remain. [asserted] |
| `obligation.commit` | Create, accept, waive, release or materially alter a non-financial legal right or obligation. [asserted] | **No after effective commitment by default. Compensation only.** Some regimes permit withdrawal before acceptance or mutual rescission later. [asserted] | Withdraw before effect, or execute a legally valid rescission, release or corrective filing. [asserted] | Current authoritative status plus counterparty/registry receipt can prove the later legal state; contextual legal review decides whether that evidence is sufficient. [asserted] | Third-party reliance, elapsed duties, enforceability disputes, public records and prior waiver/disclosure remain. [asserted] |
| `authority.change` | Acquire, reveal, rotate or widen credentials, permissions, consent or access control. [asserted] | **Conditional for ACL state; no for disclosure.** [asserted] | Revoke the grant, restore the prior ACL and rotate exposed credentials. [asserted] | Fresh authorisation readback, denied use of the old authority and successful use only inside the restored scope. [asserted] | A disclosed secret or copied authority can never be proved forgotten. [asserted] |
| `physical.actuate` | Cause shipment, travel, machinery, entry, recording or another physical-world effect. [asserted] | **No by default. Compensation only.** [asserted] | Cancel before actuation or perform a domain-specific compensating action. [asserted] | Independent sensor, provider or human evidence can prove the compensating state, not reversal of elapsed events. [asserted] | Observation, wear, movement, safety exposure and third-party reliance remain. [asserted] |

A composite invocation receives every applicable value. Its admission follows the least recoverable
atom and every protected residual; a benign carrier such as `process.run` or `network.call` cannot
hide `money.commit`, `obligation.commit`, `message.send` or `external.change`. Raw shell and browser
access are wildcard effect capabilities unless an outer sandbox proves which effect classes they
cannot reach.
[asserted]

Scheduled automation decomposes into `system.change` or `external.change`, then each later
`process.run` and child effect. Memory, training and capability changes likewise decompose into the
data, file, system, network or external-state atoms they actually touch; a domain label never hides
the underlying effects. [asserted]

An artefact remains a local draft only while no human-facing sink can render it. Terminal/stdout,
dashboard/UI, notification and audio paths which can expose it to a person are `message.send` even
when no network is involved. ADR-0071's delivery records must link to the same effect intent/receipt
rather than becoming a second unclassified display path. Classification does not itself create an
approval; ADR-0075 consumes the active first-party task authority and effect facts. [asserted]

## 4. One capability inventory, with present-but-gated state

`capabilities.py` currently records `kind`, `name`, `available` and provenance, then fails closed
when a requested capability is absent, malformed or unavailable. Dispatch serialises the selected
inventory into prompt text; it does not remove tools, credentials, commands or network reach from
the child process. [measured: `src/consilient/capabilities.py:32-37`,
`src/consilient/capabilities.py:111-194`, `scripts/dispatch.py:1248-1272`]

The existing inventory is extended rather than shadowed. Technical reach and current admission are
separate fields: [asserted]

```json
{
  "kind": "connection",
  "name": "example",
  "available": true,
  "provenance": ["probe-event-id"],
  "gate": {
    "state": "gated",
    "reason": "no_matching_grant",
    "grant_kind": null,
    "authority_event": null,
    "decision_id": null,
    "recovery_proof_ref": null,
    "scope": [],
    "operations": [],
    "effect_classes": [],
    "expires_at": null
  }
}
```

This is the post-migration shape. The current exact-key parser correctly rejects `gate`; the code
change which admits it must extend that parser and its fail-closed tests in the same commit.
[measured: `src/consilient/capabilities.py:111-142`] [asserted]

- `available: false` means the named technical capability was probed and is not reachable.
  [asserted]
- `available: true, gate.state: gated` means it exists but cannot be invoked live. This is the
  default for a present capability without an exact, current grant. [asserted]
- `available: true, gate.state: admitted` requires exactly one current `grant_kind`, canonical
  scope, exact operations and effects, and an expiry. `principal_authority` resolves an authenticated
  first-party V0-18 event. **PROPOSED pending principal acceptance:**
  `controller_baseline.local_restorable.v1` resolves one earlier `decision.autonomous` plus a passing
  ADR-0075 recovery proof, is single-use and is bounded to one local/restorable operation inside the
  committed workspace/authority envelope; it grants no network, credential, spend, external
  exposure or protected reach. The former uses `authority_event`; the latter uses `decision_id` and
  `recovery_proof_ref`. Unused basis fields remain null. [cited: ADR-0075] [asserted]
- Missing or malformed gate data is `gated`; absence from the inventory is unknown, never evidence
  of technical impossibility. [asserted]

Present-but-gated is chosen because hiding a discovered capability would make the audit record lie
about reachability. Calling it unavailable would also conceal the current ambient-path problem.
The boundary must withhold the actual OS handle, filesystem scope, network route, brokered credential
or provider operation; a prompt saying “gated” is not enforcement. [asserted]

No current event is sufficient to change `gated` to `admitted` merely because its payload says
`actor: principal` and `via: cli`. Current validation trusts those caller-supplied fields and records
that no signature verifier exists. A future authority reference must resolve through ADR-0075's one
first-party ingress to a fresh human-presence assertion that a dispatched process cannot mint even
when it runs as the same OS user. The assertion binds the exact manifest digest, scope, expiry and
nonce; its signing/verification capability remains outside agent reach and replay fails. OS account
identity alone is insufficient. This specification chooses no implementation; until this property
exists, principal authority is technically unverified and the capability stays gated.
[measured: `src/consilient/events.py:890-978`] [asserted]

The ADR-0075 canonical effect manifest remains the sole invocation manifest. ADR-0078 extends the
facts it receives with the selected inventory identity/digest, gate state, authority-event reference,
scope, expiry, exact operations/effect classes, current gate snapshot and any applicable legal-rule
references. It does not define another forward/inverse structure. [asserted]

## 5. One effect boundary and a complete record

**ADR-0079 supersession:** ADR-0079 replaces every older clause that placed
`decision.autonomous` after `effect.receipt`. The operative order is a durable earlier autonomous
decision or protected proposal/first-party authority, `effect.intent`, reach, `effect.receipt`, then
the existing outcome. Replay joins later receipt/outcome facts without embedding them in or
rewriting the decision. [cited: ADR-0079]

Every adapter invocation uses the following write-ahead sequence: [asserted]

1. Resolve the capability in the existing inventory and recompute its ADR-0075 manifest from the
   actual invocation. Derive a capability-boundary disposition for an unknown effect, stale grant,
   scope mismatch or missing structural rule, but expose no live handle. [asserted]
2. Pass the canonical manifest and boundary facts to ADR-0075. It alone runs any isolated recovery
   proof and returns the final autonomous, reshape, refusal or principal-escalation disposition
   **before live reach**. Proof activity has separately admitted local capabilities and linked child
   effect records; it cannot reach the live target. [asserted]
3. Append the durable `decision.autonomous`, or resolve the protected proposal plus exact
   first-party authority, before intent or reach. The record contains only facts available before
   actuation. [cited: ADR-0079]
4. Append, flush and fsync `effect.intent` with that final disposition **before** the live effect
   becomes reachable. A malformed request is represented by protected input references plus a
   refusal reason. If the durable append cannot be proved, do not execute. [asserted]
5. For a final live-authorised disposition only, expose the least-privilege handles named by the
   manifest and execute once through the admitted adapter, using a stable provider idempotency key
   where supported. A reshape starts a new local operation; a refusal or escalation exposes no live
   handle. [asserted]
6. Append, flush and fsync an `effect.receipt` observation after refusal, success, failure or an
   unresolved crash window. [asserted]
7. Let ADR-0075 append its linked outcome after the receipt. Replay joins that outcome to the
   earlier decision; neither earlier record embeds later result bytes or is rewritten. [cited: ADR-0079]

`effect.intent` contains stable `operation_id`, `decision_id`, work-item and attempt ids; Owner and
actor; the canonical secret-free ADR-0075 manifest once, either inline or by immutable artefact
reference and digest; its final ADR-0075 disposition; and the inventory, gate, authority and
applicable-law snapshots not already in that manifest. Public, high-entropy values may use a
canonical hash. Private or low-entropy targets, recipients, content and idempotency values use an
opaque instance-private broker reference or a domain-separated keyed MAC whose key remains outside
the trajectory; the record names the algorithm/domain and key version, never the key. A credential
or secret value is represented only by a broker reference. The record does not restate manifest
fields in a second schema. [asserted]

`effect.receipt` links to the intent and contains `succeeded`, `failed`, `refused` or `unknown`;
start/end timestamps; protected provider request/receipt references; protected request/response/
content commitments; actual resource, money and scope consumption; post-state/readback digests;
declared residuals; and every child operation id. The same opaque-reference/keyed-MAC rule applies
to low-entropy private values. A later compensation or inverse is another linked intent/receipt pair
and never rewrites history. [asserted]

Today's `transport.outbound` event instead includes the raw recipient, message text and free-text
authorisation note. That current shape must not be reused for the effect protocol; instance-private
evidence uses an opaque broker reference or keyed commitment rather than being copied into the
trajectory. [measured:
`src/consilient_connectors/outbound.py:259-284`] [asserted]

A surviving intent without a receipt is not “not run”. Recovery appends an `unknown` receipt
observation and reconciles against a provider idempotency record or fresh state readback. `unknown`
is unresolved, not terminal: a later observation may append `supersedes` to a final `succeeded`,
`failed` or `refused` receipt. Receipt chains are monotonic and non-forking, with exactly one current
head; an irreconcilable head remains visibly `unknown` and is never counted as success or failure.
Recovery never blindly retries a non-idempotent send, spend, publication or external mutation.
[asserted]

The event file remains the authority, but “single writer” becomes true only when every product path
is source-scanned against direct writes/raw effect primitives and the authorised append operation is
process-serialised, flushed and fsynced. Current canonical-format bypass detection cannot identify a
direct writer that reproduces the canonical format. [measured: `src/consilient/events.py:1071-1086`]

No future report may claim complete provenance unless every intent has one non-forking receipt chain
whose current head is final or explicitly `unknown`, every child effect is linked, and replay after
deleting derived projections produces the same result. [asserted]

## 6. Lawful by construction versus lawful by review

There is no defensible numeric structural-to-review ratio: this repository has no labelled corpus of
proposed actions with jurisdiction, facts and legal outcomes. The honest current answer is that a
**narrow minority** of legal constraints can be structural and **most** legality remains contextual
review. Assigning a percentage would turn an assertion into a measurement. [measured] [asserted]

The machine can enforce these exact properties in code: [asserted]

- a denied capability has no OS handle, network route, credential, provider method or target scope;
  [asserted]
- allowlisted roots, domains, recipients, operations, data classifications, rate/resource limits,
  grant expiry and money ceilings are exact predicates; [asserted]
- authenticated first-party authority must match the operation and scope, and an agent cannot author
  a principal verdict, approval, consent, gate lift or spend authorisation; [asserted]
- values already classified private or secret are withheld from public channels and the trajectory;
  code enforces the supplied classification but does not prove it correct; [asserted]
- a jurisdiction-specific rule whose current primary authority and already-established factual
  inputs have been translated into an exact typed predicate can refuse the matching action, and the
  law floor cannot be disabled by user configuration. [asserted]

The machine cannot generally determine jurisdiction, contested facts, legal identity, validity of
consent, contractual meaning, intellectual-property exceptions, defamation, proportionality,
sector-specific duties or whether an authority still governs the exact circumstances. Model refusal
and keyword matching do not settle those questions. [asserted]

Where contextual legal review is required, the record carries jurisdiction, question, primary
authority URL/identifier, version and retrieval date, reviewer identity, result, limits, expiry and
artefact digest. Code can verify that a matching current review exists and enforce its typed result;
it cannot prove that the review interpreted the law correctly. An expired, missing or scope-mismatched
review remains gated, and clearly unlawful action remains refused rather than converted into an
approval request. ADR-0075 alone decides whether any remaining protected choice reaches the
principal. [asserted]

## 7. How the surface expands

Gate status and capability authority are independent dimensions. Passing a project gate never
creates a filesystem, network, message, spend, publication or external-system grant. [asserted]

| State | Eligible surface | Surface that does not open |
|---|---|---|
| **Today: Gate A fails, Gate B fails, routing disabled.** [measured: `consil doctor`, 2026-08-22] | Build and test the boundary in this repository; use explicitly supervised dispatch under existing rules. No claim is made that today's ambient child reach is mediated. [asserted] | No unattended/default dependence, no routing claim, and no widening justified by this ADR. [asserted] |
| **Gate A passes; Gate B remains closed.** [asserted] | The action surface does not expand. Existing gate semantics may permit reliance on measured routing evidence inside the already admitted repository surface; exact capability grants still need their own checks. [asserted] | No unattended work in another repository and no automatic external-effect grant. [asserted] |
| **Gate B passes.** [asserted] | Unattended/default dependence becomes eligible only for a principal-named instance root and only through capabilities whose boundary, beta ceiling, grant and effect checks independently pass. [asserted: ADR-0039, ADR-0063] | Gate B is not a blanket external-write, message, money, legal-obligation, publication, credential or physical-actuation authority. [asserted] |
| **A capability is widened later.** [asserted] | One recorded first-party grant causes the replayed inventory projection to resolve one entry as `admitted` for exact operations, scope, effects and time. [asserted] | Other capabilities, targets and residual effects remain gated. [asserted] |

ADR-0063's principal-named cwd allowlist permits supervised dispatch and is explicitly not a gate
pass. The private commercial repositories excluded by `AGENTS.md` are outside this specification;
neither Gate A, Gate B nor an action manifest authorises their use or publication. [measured]

Every widening record includes the gate snapshot, capability/inventory digest, scope, authority
event, legal-rule references, expiry, applicable beta ceiling and rollback. Replay must reconstruct
why an effect was admitted at that time without relying on today's configuration. [asserted]

## 8. Frozen bar and measurement

The frozen organisation bar requires one Owner, provenance-bearing artefacts, a truth-relevant
exogenous check, a capable single-owner comparator and outcome measurement; it rejects extra roles
which only reread shared evidence. This design reuses that bar rather than claiming agreement is a
safety signal. [measured: `docs/00-context/agentic-organisation-bar-2026-08-22.md`]

Magentic-One's central task/progress ledgers establish a retrievable incumbent for orchestration
provenance, while its published error analysis reports risky web actions and weak verification.
[cited: Microsoft et al. (2024), *Magentic-One*, https://arxiv.org/html/2411.04468]
OpenHands exposes persisted delegated conversations, while its parallel-execution documentation
warns about shared-state races, ordering faults, deadlocks and resource exhaustion. [cited:
https://docs.openhands.dev/sdk/guides/task-tool-set,
https://docs.openhands.dev/sdk/guides/parallel-tool-execution]

The proposed delta is effect-level write-ahead intent, least-privilege admission, terminal receipts
and proof tied to the actual provider or state, rather than only a task ledger or model trace.
That delta is not yet demonstrated. EXP-59 rejects an implementation on one duplicate, lost or
contradictory effect across its registered crash cuts; EXP-35 tests whether recorded reversals are
misclassified or escape their admitted root. [asserted] [measured:
`docs/10-research/experiment-register.md`]

## 9. Required implementation checks

No implementation is authorised by this document. When each behaviour ships, its smallest
same-commit check is mandatory: [asserted]

1. an exact-set test for all twelve effect values and malformed/unknown values; [asserted]
2. inventory tests for unreachable, unknown, present-but-gated and admitted capabilities;
   [asserted]
3. an outer-boundary test proving raw filesystem/process/network/credential/provider primitives and
   human-facing terminal, UI, notification and audio sinks cannot bypass an admitted adapter;
   [asserted]
4. adapter fixtures which derive every applicable effect, detect undeclared children and exercise
   each candidate inverse/proof; [asserted]
5. crash-cut tests proving ADR-0075 disposition and intent precede reach, reconciliation is
   idempotent, late provider completion monotonically supersedes `unknown`, receipt chains do not
   fork and no blind retry duplicates a send, spend, publication or mutation; [asserted]
6. concurrent append/fsync and direct-writer source-scan ratchets; [asserted]
7. law/gate/grant expiry and exact-scope fixtures, including an ordinary writer submitting
   `actor: principal`, and a dispatched process under the principal's OS account attempting to mint,
   replay or widen a human-presence assertion; all are refused by the first-party ingress;
   [asserted]
8. replay after projection deletion, with every refusal, failure, unknown outcome and protected
   residual preserved. [asserted]

`dispatch.py`, `coordination.py`, `work_items.py`, `routing.py`, `budget.py`, `instructions.py`,
`capabilities.py` and `events.py` remain the existing substrates. No second orchestrator, capability
inventory, spend ledger, principal path or seventh CLI command is introduced. Product code retains
its AST lock and `routing_orchestration_enabled` remains false. [asserted]

## 10. Strongest case for constraining output

The strongest objection wins an important part of the argument. In the Finch source design, a
narrow output channel prevents the system from directly acting on most of what it knows. The frozen
pre-registered corpus supplies no real-system evidence that provenance plus undo is an equivalent
safety property; the fictional source cannot establish that empirical claim either. [measured:
`docs/00-context/agentic-organisation-bar-2026-08-22.md`] [asserted]

Once a person reads a message, a service logs a secret, a payment creates reliance, a publication is
copied or a physical action occurs, the prior world cannot be restored. A receipt is forensic
evidence, not prevention. An adapter and its verifier may share an omitted scope, and the current
send/click-before-append paths demonstrate how easily a documented chokepoint can fail to be one.
[measured] [asserted]

The answer is therefore a concession, not a declaration that reversibility makes unconstrained
actuation safe: **material output remains pinholed through typed capabilities and exact grants**.
What remains unconstrained is internal semantic generation and local drafting. The proposed surface
is broader than Finch's narrow communication channel, but each widening is explicit, least-privilege,
recorded and falsifiable. Until the outer boundary and its bypass tests exist, Consilient must not
claim this safety property. [asserted]

## 11. Falsifiers and acceptance

The mechanism is rejected or contracted when any of these occurs: [asserted]

- EXP-59 observes one duplicate, lost or contradictory side effect, or recovery depends on a store
  that displaced the trajectory. [asserted]
- EXP-35 observes an escaped effect, more than 25% reversal misclassification, or insufficient
  evidence for a class being widened. [asserted]
- one raw effect reaches the world without a durable intent, or one intent cannot be reconciled to a
  receipt/refusal/explicit unknown state. [asserted]
- one admitted adapter omits an applicable effect class while its own proof passes. [asserted]
- one gate pass or grant widens an unlisted capability, operation, scope, target, residual or period.
  [asserted]
- one agent-authored artefact satisfies authority reserved to the principal. [asserted]

Passing those checks would establish only the tested boundary and observed rates. It would not prove
general legality, universal erasure, zero beta or safety of an effect class not represented in the
fixtures. [asserted]

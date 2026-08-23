# Portable capability and expertise-acquisition implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`. Execute one numbered unit, run its exact acceptance command, commit only its claim paths, then release the claim.

**Goal:** Turn selected, proven capability bundles into honest per-harness bindings, acquire specialist expertise only when a sealed comparison beats the unchanged eligible generalist, and quarantine every model revision until its exact evidence permits use. [asserted]

**Architecture:** ADR-0074's manifest remains canonical: `capabilities.py` selects, `instructions.py` assembles, the current branches in `scripts/dispatch.py` bind/launch, and `events.py` records. Expertise is a capability lifecycle, and ADR-0085 model revisions project through the existing harness/work-item/event machinery rather than a second registry or router. [cited: ADR-0074, ADR-0084, ADR-0085, ADR-0086]

**Tech stack:** Existing Python standard library, Agent Skills-compatible files, run-local private dispatch directories and fake/offline conformance fixtures. No dependency, provider call, credential or new CLI command is authorised by this plan. [asserted]

**Document class:** W. [cited: ADR-0073]

**Review by:** 2026-09-22, or immediately after EXP-101/110/111/126 reports or ADR-0084/0085/0086 changes status. [asserted]

**Falsifier:** A binding silently substitutes prompt text for enforcement, exposes a credential/protected record, mutates global harness configuration, or an expertise assignment activates without beating its frozen generalist comparator. [asserted]

## Stream constraints and launch blockers

- Rulesync, Agent Skills and MCP are the incumbent baseline. Do not build a general format compiler; a version-pinned Rulesync adoption decision under ADR-0065 precedes any equivalent multi-format code. [cited: ADR-0084]
- The first portable floor is credential-free Agent Skills plus one bounded recall pack. Tools/MCP/hooks bind only where the installed native surface preserves their exact semantics; required loss refuses. [cited: ADR-0084]
- Automatic capability reuse remains inert until EXP-101. Manual selection and fake/inert conformance may ship first. [cited: ADR-0074]
- EXP-110 and EXP-126 each have one live register heading and are `BLOCKED` on the prerequisites named there. PC00/EX00 verify those prerequisites read-only; no result may precede them. [measured: exact heading search, 2026-08-23]
- `docs/10-research/` changes still require explicit principal authorisation. PC00/EX00 are read-only and dispatchable; experiment-runner units that would edit the research base remain non-dispatchable until that authority is recorded. [measured: `AGENTS.md`] [asserted]
- Credentialed binding stays fake-canary only until H02 supplies exact authority and A07 proves host containment. No real secret enters this repository or a child harness. [asserted]
- EXP-111 has one live register heading and is `BLOCKED` on fail-closed lifecycle projection, trusted consent/approval ingress, a sealed bank and instrument, an isolated runner, complete outcome/cost telemetry and blinded verdicts. ML01-ML06 may build discovery, quarantine, projection and offline qualification; training/activation remain blocked on ML00 and those live prerequisites. [measured] [asserted]

## PC00 — verify live EXP-110 preregistration

**Deliverable:** Read-only verification that exactly one EXP-110 heading exists, is referenced by ADR-0084 and remains `BLOCKED` on portable adapters, a proved outer boundary, a frozen conformance package and independent fixtures. [measured]

**Depends on:** none. This unit does not modify `docs/10-research/`. [asserted]

**Why:** The heading now exists; the launch gate must consume its live blocker state rather than recreate it. [measured] [cited: ADR-0084]

**Claim exactly:** none (read-only). [asserted]

**Steps:**

1. Verify exactly one EXP-110 heading and its ADR-0084 reference. [measured]
2. Compare the heading's exact blocker text with this gate. [measured]
3. Run the existing provisional-ADR live-experiment invariant without editing it. [asserted]

**Done:** The unique blocked heading and ADR reference are present and the invariant passes. [measured]

```powershell
$heading = @(rg -n '^### EXP-110\b.*`BLOCKED: portable adapters, proved outer boundary, frozen conformance package and independent fixtures`$' docs/10-research/experiment-register.md)
if ($heading.Count -ne 1) { throw "Expected one blocked EXP-110 heading" }
$adr = @(rg -n '\bEXP-110\b' docs/decisions/0084-compile-portable-capabilities-per-harness-and-refuse-semantic-loss.md)
if ($adr.Count -eq 0) { throw "ADR-0084 does not reference EXP-110" }
python -m pytest tests/test_v0_invariants.py::test_provisional_adrs_name_a_live_experiment -q
```

**Commit:** none; read-only verification. [asserted]

## PC01 — canonical portable-manifest extension

**Deliverable:** ADR-0074's one manifest validates the five closed kinds plus `runtime`, `requires`, opaque credential refs and `trigger`, while task requests carry required/optional necessity without creating a destination-specific sibling format. [asserted]

**Depends on:** M04. [asserted]

**Why:** ADR-0084 decision “extend ADR-0074's canonical manifest”. [cited: ADR-0084]

**Claim exactly:**

- `src/consilient/capabilities.py`
- `tests/test_portable_manifest.py` (new)
- `tests/test_capabilities.py`

**Steps:**

1. Preserve exactly `tool|mcp|skill|plugin|connection`; reject `hook` and `memory` kinds. A hook is one of the five kinds with canonical `trigger`, while memory remains the separate recall contract. [cited: portable-capability lines 129-147]
2. Add discriminated `runtime`, `requires`, opaque `credential_refs` and optional canonical `trigger` to the manifest. Put `necessity: required|optional` on the task request, never the manifest, and force security, credential, authority and typed-effect controls to required. [asserted]
3. Reject inline secret/env/header names and values, harness-specific overrides, unknown reach and postcondition/verifier changes disguised as variants. [asserted]
4. Keep automatic selection disabled; explicit active-head selection retains M04's uniqueness/destination checks. [asserted]

**Done:** Malformed, widening, secret-bearing and semantically colliding manifests refuse; one valid manual head reconstructs with the same digest. [asserted]

```powershell
python -m pytest tests/test_portable_manifest.py tests/test_capabilities.py -q
```

**Commit:** `feat(capabilities): define portable runtime requirements`. [asserted]

## PC02 — pre-launch binding state and receipt

**Deliverable:** One canonical binding-state schema/policy validates `applied`, `degraded` or `refused`, exact optional losses and secret-free digests for later per-harness pre-launch use. [asserted]

**Depends on:** PC01, F03, M05, A01 and A02. [asserted]

**Why:** ADR-0084 separates selection, binding, application and observed use. [cited: ADR-0084]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/instructions.py`
- `tests/test_capability_binding_receipts.py` (new)
- `tests/test_v0_invariants.py`

**Steps:**

1. Freeze the binding receipt identity, task/manifest/version, harness/adapter versions, generated digests, native surfaces, losses/reasons, recall receipt, credential status and effect-manifest digest. [asserted]
2. Require every selected item represented by an adapter to have exactly one terminal pre-launch state; missing receipt is refusal at that adapter's launch boundary. [asserted]
3. Permit `degraded` only for explicitly optional loss with a still-meaningful verifier; required, unknown or security loss is `refused`. [asserted]
4. Record later observed use separately as `yes|no|unknown`; never infer it from selection/loading. Add a source ratchet proving `capabilities.py` is the sole selector, `instructions.py` the sole assembler and existing dispatch the caller; another loader/registry/command fails. [asserted]

**Done:** Silent drop, duplicate state, stale version, required-to-prompt downgrade and secret/raw-config payload all refuse before launch. [asserted]

```powershell
python -m pytest tests/test_capability_binding_receipts.py tests/test_instructions.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(events): record capability binding states`. [asserted]

## PC03 — harness semantic/version probe

**Deliverable:** The existing harness probe reports the installed version's native skill, memory, MCP/tool and hook semantics plus a passing compatibility range; unknown/out-of-range requirements are stale and refuse. [asserted]

**Depends on:** PC01 and OBS03; this unit follows OBS03 in the shared `harness.py`/dispatch lane. [asserted]

**Why:** ADR-0084 requires explicit per-version revalidation. [cited: ADR-0084]

**Claim exactly:**

- `src/consilient/harness.py`
- `scripts/dispatch.py`
- `tests/test_portable_probe.py` (new)

**Steps:**

1. Extend existing version/help probes with closed native surfaces, lifecycle phase, matcher, blocking semantics, transport and run-local configuration support. [asserted]
2. Keep only inert probe results in product code and subprocess execution in the outer script. [asserted]
3. Compare requirements structurally; prompt wording, compatibility marketing and file-name acceptance do not satisfy permission/blocking equivalence. [asserted]

**Done:** Frozen help/version fixtures reproduce results for all four harnesses; version drift outside a passing range yields `stale` and no child launch. [asserted]

```powershell
python -m pytest tests/test_portable_probe.py tests/test_dispatch.py -q
```

**Commit:** `feat(dispatch): probe portable semantics by version`. [asserted]

## PC04 — one destination-filtered skill/memory assembly

**Deliverable:** One pinned-prefix assembly filters workspace, consent purpose and destination before protected bytes are read, then emits one Agent Skills-compatible package plus bounded recall bytes/receipt whose digest is identical across eligible harnesses. [asserted]

**Depends on:** M03, M05 and PC01. [asserted]

**Why:** ADR-0084's shared-memory boundary; ADR-0074's consent/destination contract. [cited: ADR-0074, ADR-0084]

**Claim exactly:**

- `src/consilient/recall.py`
- `src/consilient/instructions.py`
- `tests/test_portable_memory.py` (new)

**Steps:**

1. Resolve metadata and reject cross-root/unconsented destinations before loading record content or skill payload. [asserted]
2. Bind selected/omitted identities/reasons, prefix, bound, continuation and destination to one recall receipt. [asserted]
3. Render the same admitted package bytes for each adapter; vendor memory is disabled/isolated or labelled `uncontrolled`. [asserted]
4. Refuse a complete-memory contract when ambient vendor memory is uncontrolled. [asserted]

**Done:** Claude/Codex fixtures receive identical recall/package digests; protected canaries for another destination appear nowhere and have non-content omission receipts. [asserted]

```powershell
python -m pytest tests/test_portable_memory.py tests/test_recall_receipts.py tests/test_instructions.py -q
```

**Commit:** `feat(instructions): assemble one portable memory package`. [asserted]

## PC05 — Claude run-local binding

**Deliverable:** The existing Claude dispatch branch materialises one run-local binding for PC04 plus every PC01 requirement that the probed Claude version genuinely supports, without modifying user/global/project configuration. [asserted]

**Depends on:** PC02, PC03, PC04, A07 and the ADR-0065 Rulesync/native-adapter decision. Without current containment, every real child launch refuses; pure file assembly may be tested against fake homes earlier. [asserted]

**Why:** ADR-0084's Claude adapter contract. [cited: ADR-0084]

**Claim exactly:**

- `scripts/dispatch.py`
- `tests/test_portable_claude.py` (new)

**Steps:**

1. Prefer a version-pinned adopted Rulesync path if ADR-0065 proves it meets receipts/boundaries; otherwise add only the minimum native run-local files. [asserted]
2. Bind Agent Skills/recall first; map MCP/tool/hook only to exact native semantics and fake effect handles. [asserted]
3. Reread generated files by digest, emit PC02 state, and launch only after durable `applied|degraded`. [asserted]
4. Exercise against a fake home/project and prove every pre-existing byte unchanged. [asserted]

**Done:** Required mismatch refuses before `claude -p`; optional loss is in receipt/brief; global state is byte-identical and generated files are private/run-local. [asserted]

```powershell
python -m pytest tests/test_portable_claude.py tests/test_capability_binding_receipts.py -q
```

**Commit:** `feat(dispatch): bind capabilities for Claude runs`. [asserted]

## PC06 — Codex run-local binding

**Deliverable:** The existing Codex dispatch branch materialises the same package through a run-local instruction/config surface and refuses Claude-only permissions, isolation or hook semantics that Codex cannot enforce. [asserted]

**Depends on:** PC05 and the same PC02-PC04/A07/ADR-0065 gates. It is serial after PC05 because both claim `scripts/dispatch.py`; every real child launch requires A07. [asserted]

**Why:** ADR-0084's Codex adapter contract and documented migration differences. [cited: ADR-0084]

**Claim exactly:**

- `scripts/dispatch.py`
- `tests/test_portable_codex.py` (new)

**Steps:**

1. Produce run-local Codex config/instructions; never depend on interactive `/import` or mutate the user's profile. [asserted]
2. Treat allowed-tools prompt guidance and shell-only hooks as semantic loss, never enforcement. [cited: ADR-0084]
3. Apply the same digest/reread/state/launch order and fake-home proof as PC05. [asserted]

**Done:** The PC04 bytes match Claude, unsupported required controls refuse, and optional differences are exact rather than silently translated. [asserted]

```powershell
python -m pytest tests/test_portable_codex.py tests/test_portable_claude.py -q
```

**Commit:** `feat(dispatch): bind capabilities for Codex runs`. [asserted]

## PC07 — Cursor run-local binding

**Deliverable:** The existing Cursor branch uses only a proved session/project-local overlay and records unsupported when the installed CLI requires global/project mutation or cannot preserve required semantics. [asserted]

**Depends on:** PC06 and PC02-PC04/A07/ADR-0065. Every real child launch requires A07. [asserted]

**Why:** ADR-0084's Cursor adapter contract. [cited: ADR-0084]

**Claim exactly:**

- `scripts/dispatch.py`
- `tests/test_portable_cursor.py` (new)

**Steps:**

1. Probe the native/ACP session surface and materialise only run-local admitted configuration. [asserted]
2. Refuse fallback to global installation or untracked project mutation. [asserted]
3. Apply PC02 receipt/digest/effect rules and leave existing Cursor adapter tests green. [asserted]

**Done:** Fake-home/project snapshots remain byte-identical outside the run directory; absent local binding refuses before Cursor launch. [asserted]

```powershell
python -m pytest tests/test_portable_cursor.py tests/test_dispatch.py -q
```

**Commit:** `feat(dispatch): bind capabilities for Cursor runs`. [asserted]

## PC08 — Grok run-local binding

**Deliverable:** The existing Grok branch maps only documented run-local Agent Skills/MCP/hook semantics and records Claude-compatibility differences rather than assuming equivalence. [asserted]

**Depends on:** PC07 and PC02-PC04/A07/ADR-0065. Every real child launch requires A07. [asserted]

**Why:** ADR-0084's Grok adapter contract. [cited: ADR-0084]

**Claim exactly:**

- `scripts/dispatch.py`
- `tests/test_portable_grok.py` (new)

**Steps:**

1. Bind only surfaces proven by PC03 for the installed version. [asserted]
2. Refuse timing/blocking differences and compatibility claims unsupported by the probe. [asserted]
3. Apply the same run-local/digest/receipt/no-global-mutation checks as PC05-PC07. [asserted]

**Done:** File-format acceptance without semantic support refuses; passing fixtures reconstruct exact generated digests and leave the global profile untouched. [asserted]

```powershell
python -m pytest tests/test_portable_grok.py tests/test_grok_adapter.py -q
```

**Commit:** `feat(dispatch): bind capabilities for Grok runs`. [asserted]

## PC09 — model-external credential broker boundary

**Deliverable:** An instance-local standard-library broker resolves an opaque reference into a capability-scoped fake secret and exposes only run-scoped local IPC/operations; the harness, command, files, outputs and trajectory never receive credential bytes. [asserted]

**Depends on:** PC02, PC03, A02 and A07. This unit proves only a synthetic canary boundary; resolving a real credential additionally requires H02's exact `capability.credential_use` receipt and remains deferred. [asserted]

**Why:** ADR-0084 requires credentials outside the model process and refuses native inline/ambient secret surfaces. [cited: ADR-0084]

**Claim exactly:**

- `scripts/capability_broker.py` (new)
- `scripts/dispatch.py`
- `tests/test_capability_broker.py` (new)
- `tests/test_v0_invariants.py`

**Steps:**

1. Use the smallest OS-local standard-library IPC supported on Windows/POSIX; bind one scope, operation set, expiry and single run. [asserted]
2. Give the broker process—not the shell-capable harness—the fake credential environment and expose no reusable provider handle. [asserted]
3. Scan every generated file, command, child-visible environment, brief, stdout/stderr/transcript and appended event for the exact canary. [asserted]
4. Add a source ratchet allowing reference resolution only inside this boundary; unsupported inline-secret adapters refuse. [asserted]

**Done:** The fake capability succeeds through the broker while every child-visible/durable byte contains zero canary copies; replay, scope widening and reuse after expiry fail. [asserted]

```powershell
python -m pytest tests/test_capability_broker.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(dispatch): broker credentials outside harnesses`. [asserted]

## PC10 — offline EXP-110 conformance runner

**Deliverable:** A deterministic offline runner executes the registered native, portable and absent arms for Claude/Codex fixtures and emits artefact/effect/secret/refusal outcomes without activating automatic binding. [asserted]

**Depends on:** PC00, PC05, PC06, A07 and explicit research-base authorisation. No uncontained or ambient provider launch is an eligible EXP-110 cell. [asserted]

**Why:** ADR-0084 names EXP-110 as its bounded equivalence falsifier. [cited: ADR-0084]

**Claim exactly:**

- `docs/10-research/experiments/exp110/run_exp110.py` (new)
- `docs/10-research/experiments/exp110/README.md` (new)
- `tests/test_exp110_runner.py` (new)

**Steps:**

1. Load only the frozen registration, package/task fixtures and pinned fake/native adapter versions. [asserted]
2. Retain timeouts, refusals, missing output, degradation and secret/effect escapes as failures; implement no efficacy early stop. [asserted]
3. Write a private result/checkpoint artefact and verify it by schema/count/digest, not runner exit status. [asserted]

**Done:** A fixture matrix reproduces counts/digests; each injected silent loss, secret leak and protected-effect escape causes the registered failure. [asserted]

```powershell
python -m pytest tests/test_exp110_runner.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python docs/10-research/experiments/exp110/run_exp110.py --fixture --out .harness/exp110-plan-check.json
```

**Commit:** `research: add offline EXP-110 runner`. [asserted]

## EX00 — verify live EXP-126 preregistration

**Deliverable:** Read-only verification that exactly one EXP-126 heading exists, is referenced by ADR-0086 and remains `BLOCKED` on authenticated acquisition authority, a frozen bundle manifest, a one-use sealed bank, an isolated runner and blinded domain verdicts. [measured]

**Depends on:** PC00, for verification ordering only. This unit does not modify `docs/10-research/`. [asserted]

**Why:** The heading now exists; the launch gate must consume its live blocker state rather than recreate it. [measured] [cited: ADR-0086]

**Claim exactly:** none (read-only). [asserted]

**Steps:**

1. Verify exactly one EXP-126 heading and its ADR-0086 reference. [measured]
2. Compare the heading's exact blocker text with this gate. [measured]
3. Run the existing provisional-ADR live-experiment invariant without editing it. [asserted]

**Done:** The unique blocked heading and ADR reference are present and the invariant passes. [measured]

```powershell
$heading = @(rg -n '^### EXP-126\b.*`BLOCKED: authenticated acquisition authority, frozen bundle manifest, one-use sealed bank, isolated runner and blinded domain verdicts`$' docs/10-research/experiment-register.md)
if ($heading.Count -ne 1) { throw "Expected one blocked EXP-126 heading" }
$adr = @(rg -n '\bEXP-126\b' docs/decisions/0086-acquire-expertise-as-a-proven-capability-bundle-and-tune-only-after-retrieval-loses.md)
if ($adr.Count -eq 0) { throw "ADR-0086 does not reference EXP-126" }
python -m pytest tests/test_v0_invariants.py::test_provisional_adrs_name_a_live_experiment -q
```

**Commit:** none; read-only verification. [asserted]

## EX01 — deterministic inferred-expertise proposal

**Deliverable:** A read-only projection identifies eligible inferred expertise proposals from the exact 90-day recurrence/adverse/cost thresholds and emits nothing else; it never fetches, persists a bundle or trains. [asserted]

**Depends on:** T03, D04 and M02. [asserted]

**Why:** ADR-0086 “inferred trigger may only propose”. [cited: ADR-0086]

**Claim exactly:**

- `src/consilient/projection.py`
- `tests/test_expertise_proposals.py` (new)

**Steps:**

1. Project six completed applicable items over 21 days/four days and three distinct postcondition signatures. [asserted]
2. Require two different-class attributable adverse signals or 180 measured reacquisition minutes across three items; unknown telemetry stays unknown. [asserted]
3. Apply half-recurrence economics and the 90-day rejected/expired suppression rule. [asserted]
4. Produce exact qualifying refs, proposed scope, source/privacy boundary, estimates, evaluation author, components, recheck and “no model training” text. [asserted]

**Done:** Boundary and metamorphic fixtures reproduce every threshold; changed model topic labels alone cannot create eligibility and an eligible row causes no I/O/mutation. [asserted]

```powershell
python -m pytest tests/test_expertise_proposals.py tests/test_task_projection.py -q
```

**Commit:** `feat(projection): identify expertise proposals`. [asserted]

## EX02 — authenticated expertise proposal/authority join

**Deliverable:** `expertise.proposed` and `expertise.authorised` bind either an authenticated explicit imperative or acceptance of an EX01 proposal to the narrow retrieval/capability scope, while every broader permission remains separate. [asserted]

**Depends on:** EX01, C01 and H02. [asserted]

**Why:** ADR-0086's two-trigger consent boundary. [cited: ADR-0086]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/work_items.py`
- `tests/test_expertise_authority.py` (new)

**Steps:**

1. Freeze the two event names and bind source turn/proposal refs, exact purpose/postcondition, public/current-task source boundary, time/storage budget, expiry and authority receipt. [asserted]
2. Treat mentions, questions and quotations as non-imperatives; a model classifier may propose but cannot authenticate. [asserted]
3. Permit explicit authority to skip a second confirmation only inside licensed local retrieval/capability acquisition. [asserted]
4. Refuse prior private trajectory reuse, parameter mutation, spend, deployment, publication, external effect and verdict without their separate records. [asserted]

**Done:** Spoof/replay/wrong-purpose/expired receipts and unaccepted inferred proposals cannot create authorised work; valid explicit scope still cannot author training or activation. [asserted]

```powershell
python -m pytest tests/test_expertise_authority.py tests/test_human_authority.py -q
```

**Commit:** `feat(events): bind expertise acquisition authority`. [asserted]

## EX03 — immutable expertise bundle as a capability

**Deliverable:** One versioned capability manifest addresses the source-provenanced skill, tool configuration, examples/counterexamples, retrieval index, evaluation contract and optional separately qualified checkpoint ref; no learned bytes or second registry are introduced. [asserted]

**Depends on:** EX02, M01, M04 and PC01. [asserted]

**Why:** ADR-0086 defines expertise as a capability bundle and retains ADR-0074's training boundary. [cited: ADR-0074, ADR-0086]

**Claim exactly:**

- `src/consilient/records.py`
- `src/consilient/capabilities.py`
- `tests/test_expertise_bundles.py` (new)

**Steps:**

1. Validate purpose/families/postconditions/exclusions/applicability, source provenance/licence/consent/validity, retrieval config, components, permissions/effects/failure modes and evaluation refs. [asserted]
2. Deduplicate bytes by digest but merge manifests only when execution/rights/trust/evaluation contracts are equivalent. [asserted]
3. Classify frozen-encoder embeddings as retrieval and reject fitted/edited model state from the bundle path; optional checkpoint is an external qualified capability ref. [cited: ADR-0074]
4. Preserve one selectable head per execution-contract/destination class and every old/adverse version addressably. [asserted]

**Done:** Rights/licence/destination/postcondition collisions do not merge; embedding-fit and embedded checkpoint bytes refuse; replay reconstructs the immutable bundle graph. [asserted]

```powershell
python -m pytest tests/test_expertise_bundles.py tests/test_portable_manifest.py -q
```

**Commit:** `feat(capabilities): represent expertise bundles`. [asserted]

## EX04 — pre-acquisition sealed instrument and isolation contract

**Deliverable:** A task-scoped independent instrument contract is digest-frozen before source fetch or candidate work and prevents acquisition/candidate/trainer/promoter access to hidden items, answers and semantic siblings. [asserted]

**Depends on:** O01, RAC01, S02 and A07. No prompt-hidden bank qualifies. [asserted]

**Why:** ADR-0086 “freeze before study”; ADR-0076 sealed-instrument boundary. [cited: ADR-0076, ADR-0086]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/promote.py`
- `tests/test_expertise_instrument.py` (new)

**Steps:**

1. Reuse S02's sealed-instrument contract and bind expertise scope, strata, truth contracts, comparator/version, tools/budget, seed, missingness, stopping/critical-error rules and blind verdict plan. [asserted]
2. Require an independent R instrument-author assignment before acquisition plan/claims and forbid candidate/acquisition/training/promoter roles. [asserted]
3. Bind rights-cleared train/development/held-out splits and reject digest/path/semantic-sibling overlap. [asserted]
4. Return `insufficient_evidence` when isolation or a competent oracle cannot be established. [asserted]

**Done:** Every post-fetch/post-outcome freeze, role overlap, hidden read and semantic-sibling canary refuses; one valid sealed fixture remains unreadable to the acquisition runner. [asserted]

```powershell
python -m pytest tests/test_expertise_instrument.py tests/test_promote_instrument.py -q
```

**Commit:** `feat(work): freeze expertise instruments before study`. [asserted]

## EX05 — bundle lifecycle and comparator disposition

**Deliverable:** Replay projects `observed -> proposed -> authorised -> acquiring -> quarantined -> evaluated -> active -> stale|quarantined -> superseded|retired`, and only a registered sealed generalist comparison can make a bundle active. [asserted]

**Depends on:** EX00, EX03, EX04 and the completed EXP-126 result. [asserted]

**Why:** ADR-0086 requires loss/tie/error as normal discard and append-only decay/retirement. [cited: ADR-0086]

**Claim exactly:**

- `src/consilient/capabilities.py`
- `src/consilient/projection.py`
- `tests/test_expertise_lifecycle.py` (new)

**Steps:**

1. Bind comparison result, unchanged comparator/version, evaluation epoch, outcome counts, refusals, dissent and adverse/critical-error evidence to a bundle digest. [asserted]
2. Keep loss/tie quarantined/retired, inconclusive quarantined, and require the registered pass plus all prerequisite controls for active. [asserted]
3. Implement expiry/source/tool/model/evaluation/generalist/human-rejection rechecks; immediate quarantine on critical error, privacy/authority breach, invalid rights or contamination. [asserted]
4. Preserve invalidation/supersession/retirement history and exactly one eligible head. [asserted]

**Done:** Delete/replay reproduces every transition; stale/wrong/incompatible heads refuse; a later stronger comparator retires selection without deleting the earlier result. [asserted]

```powershell
python -m pytest tests/test_expertise_lifecycle.py tests/test_memory_projection.py -q
```

**Commit:** `feat(capabilities): govern expertise lifecycle`. [asserted]

## EX06 — task-scoped specialist assignment

**Deliverable:** A native work-item R assignment explicitly selects one active bundle digest for an exact task contract, assembles/binds it through the portable capability path and emits one Owner candidate; same-bundle extra roles receive no anchor credit. [asserted]

**Depends on:** EX05, RAC01-RAC05, PC02-PC04 and T02. Automatic selection also depends on EXP-101; until then only explicit/manual assignment is reachable. [asserted]

**Why:** ADR-0086 “assignment into a specialist squad”. [cited: ADR-0086]

**Claim exactly:**

- `src/consilient/capabilities.py`
- `src/consilient/instructions.py`
- `src/consilient/work_items.py`
- `scripts/dispatch.py`
- `tests/test_expertise_assignment.py` (new)

**Steps:**

1. Match purpose/postcondition, destination, permissions, consent/licence, validity, compatibility, evaluation epoch and active-head uniqueness. [asserted]
2. Bind bundle/task/assignment/instruction/binding receipts and the same candidate-exposure decision before claim/launch. [asserted]
3. Treat a squad sharing the bundle as one derivation anchor; acquire a separate ADR-0081 anchor for full/protected conclusions. [asserted]
4. Preserve manual selection while automatic library selection refuses until EXP-101. [asserted]

**Done:** Stale/mismatched/quarantined/non-unique/same-anchor fixtures refuse; one valid manual bundle reconstructs end-to-end and cannot increase candidate exposure. [asserted]

```powershell
python -m pytest tests/test_expertise_assignment.py tests/test_role_claims.py tests/test_capability_binding_receipts.py -q
```

**Commit:** `feat(dispatch): assign proven expertise bundles`. [asserted]

## EX07 — offline EXP-126 bundle comparison runner

**Deliverable:** A deterministic offline runner executes the frozen direct/transfer/stale-conflict/out-of-scope strata, retains human/oracle/cost/harm/refusal/quarantine outcomes and writes no activation event. [asserted]

**Depends on:** EX00, EX03, EX04 and explicit research-base authorisation. [asserted]

**Why:** ADR-0086 names EXP-126 as the bundle assignment falsifier. [cited: ADR-0086]

**Claim exactly:**

- `docs/10-research/experiments/exp126/run_exp126.py` (new)
- `docs/10-research/experiments/exp126/README.md` (new)
- `tests/test_exp126_runner.py` (new)

**Steps:**

1. Load only the frozen task bank/splits, unchanged generalist identity, bundle digest, tools/budgets and stopping rule. [asserted]
2. Keep timeouts, missingness, refusals, harmful retrieval and critical errors in their named strata and denominators. [asserted]
3. Write private checkpoint/result artefacts and verify schema/count/digests independently of launcher exit. [asserted]

**Done:** Fixed fixtures reproduce the paired outcomes; any treatment-only critical error/harm produces registered discard and no activation. [asserted]

```powershell
python -m pytest tests/test_exp126_runner.py -q
python docs/10-research/experiments/exp126/run_exp126.py --fixture --out .harness/exp126-plan-check.json
```

**Commit:** `research: add offline EXP-126 runner`. [asserted]

## ML00 — verify live EXP-111 preregistration

**Deliverable:** Read-only verification that exactly one EXP-111 heading exists, is referenced by ADR-0085 and remains `BLOCKED` on fail-closed lifecycle projection, trusted consent/approval ingress, a sealed bank and instrument, an isolated runner, complete outcome/cost telemetry and blinded verdicts. [measured]

**Depends on:** PC00 and EX00, for verification ordering only. This unit does not modify `docs/10-research/`. [asserted]

**Why:** The heading now exists; the launch gate must consume its live blocker state rather than recreate it. [measured] [cited: ADR-0085]

**Claim exactly:** none (read-only). [asserted]

**Steps:**

1. Verify exactly one EXP-111 heading and its ADR-0085 reference. [measured]
2. Compare the heading's exact blocker text with this gate. [measured]
3. Verify the model-lifecycle specification uses ADR-0077's dependence-robust candidate ceiling; a stale logarithmic statement blocks later ML units and is corrected only in a specification amendment, never by changing this heading. [cited: ADR-0077]
4. Run the existing provisional-ADR live-experiment invariant without editing it. [asserted]

**Done:** The unique blocked heading and ADR reference are present, the exposure contract is consistent, and the invariant passes. [measured] [asserted]

```powershell
$heading = @(rg -n '^### EXP-111\b.*`BLOCKED: fail-closed lifecycle projection, trusted consent/approval ingress, sealed bank and instrument, isolated runner, complete outcome/cost telemetry and blinded verdicts`$' docs/10-research/experiment-register.md)
if ($heading.Count -ne 1) { throw "Expected one blocked EXP-111 heading" }
$adr = @(rg -n '\bEXP-111\b' docs/decisions/0085-qualify-model-revisions-before-routing-and-seal-fine-tune-evaluation.md)
if ($adr.Count -eq 0) { throw "ADR-0085 does not reference EXP-111" }
$robust = @(rg -n '^ceiling is `floor\(e / beta_upper\)`' docs/superpowers/specs/2026-08-22-model-lifecycle.md)
if ($robust.Count -ne 1) { throw "Model lifecycle does not name the robust exposure ceiling exactly once" }
python -m pytest tests/test_v0_invariants.py::test_provisional_adrs_name_a_live_experiment -q
```

**Commit:** none; read-only verification. [asserted]

## ML01 — automatic discovery into quarantine only

**Deliverable:** The existing model refresher emits an immutable discovery manifest/event for every new/changed provider catalogue entry and cannot rewrite `MODELS` or make an entry selectable. [asserted]

**Depends on:** F03 and release of the `events.py` lane. [asserted]

**Why:** ADR-0085 distinguishes automatic discovery from adoption and identifies `refresh_models.py --write` as the current bypass. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/events.py`
- `scripts/refresh_models.py`
- `tests/test_model_discovery.py` (new)

**Steps:**

1. Freeze a secret-free discovery payload with provider/harness/model coordinates, source/retrieval/digest, advertised revision/capabilities, rights status and observed drift. [asserted]
2. Replace automatic source rewriting with an atomic private manifest plus durable `model.discovered`; retain a separately explicit human-maintained source-edit workflow outside discovery. [asserted]
3. Validate untrusted catalogue fields, aliases, duplicate IDs, unpinnable revisions and changed payloads; destination state is always `discovered|quarantined`. [asserted]
4. Snapshot `src/consilient/harness.py` before/after every fixture and prove discovery changes no product source or active pointer. [asserted]

**Done:** A new catalogue ID appears in the trajectory/private manifest as quarantined, never in `MODELS`, and cannot alter a dispatch decision. [asserted]

```powershell
python -m pytest tests/test_model_discovery.py tests/test_v0_invariants.py -q
```

**Commit:** `feat(models): quarantine discovered revisions`. [asserted]

## ML02 — immutable model-revision lifecycle projection

**Deliverable:** Exact identity, rights, runtime, parent and freshness manifests replay to `discovered|quarantined|qualified|approval_pending|routable|stale|refused|retired`, with no in-place revision or ID reuse. [asserted]

**Depends on:** ML01, M06 and M02. [asserted]

**Why:** ADR-0085's lifecycle and supply-chain admission contract. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/projection.py`
- `tests/test_model_lifecycle.py` (new)

**Steps:**

1. Bind candidate id, provider/harness/model/revision, official source/digest/time, bytes/signature status, rights, runtime/hardware-fit, adapter parent lineage and exact freshness triggers. [asserted]
2. Treat hosted aliases without a pin as explicit service observations which become stale on drift and never replace a pinned incumbent silently. [asserted]
3. Validate only monotonic append transitions; qualified is evidence, approval_pending is a proposal, and routable additionally requires current gates plus H02 exact approval. [asserted]
4. Preserve all adverse/refused/retired versions and delete/rebuild the projection twice. [asserted]

**Done:** Unknown rights/bytes/runtime and invalid transitions refuse; changed identity/licence/capability/cost source makes the exact head stale before another selection. [asserted]

```powershell
python -m pytest tests/test_model_lifecycle.py tests/test_memory_projection.py -q
```

**Commit:** `feat(models): project immutable revision lifecycle`. [asserted]

## ML03 — fail-closed model selection admission

**Deliverable:** Harness selection refuses every discovered/quarantined/stale/refused revision and every unknown required capability; no catalogue presence or registry membership bypasses qualification. [asserted]

**Depends on:** ML02 and PC03. [asserted]

**Why:** ADR-0085's measured registered-unknown exemption and registry invariant. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/harness.py`
- `scripts/dispatch.py`
- `tests/test_model_selection_admission.py` (new)

**Steps:**

1. Make the projected lifecycle state and exact required-capability probe an admission predicate before the existing headroom/ranking tie-break. [asserted]
2. Preserve current `MODELS` only as the explicit supervised bootstrap list; it is not evidence of qualification, cannot absorb discovered entries, and an unknown capability required by a task still refuses. [asserted]
3. Keep automatic production routing disabled; a future `routable` transition additionally checks the unchanged gates and H02 approval digest. [asserted]
4. Prove model name, provider claim, headroom, list order and family cannot populate measured capability/quality. [asserted]

**Done:** A newly discovered or registered-unknown required model cannot reach `build_command`; changing only headroom/order never changes refusal to admission. [asserted]

```powershell
python -m pytest tests/test_model_selection_admission.py tests/test_dispatch.py tests/test_grok_adapter.py -q
```

**Commit:** `fix(harness): refuse unqualified model revisions`. [asserted]

## ML04 — typed model-attempt cost vector

**Deliverable:** Every qualification/training attempt records actual metered spend, provider-equivalent price, subscription quota, wall/device time and active human minutes as separate typed dimensions with unavailable distinct from zero. [asserted]

**Depends on:** F03 and ML02. [asserted]

**Why:** ADR-0085 keeps money, quota, time and review burden incomparable; `budget.py` remains refuse-before-spend. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/events.py`
- `src/consilient/usage.py`
- `src/consilient/budget.py`
- `src/consilient/projection.py`
- `tests/test_model_cost_vector.py` (new)

**Steps:**

1. Freeze typed value/source/as-of/unavailable-reason fields for all five dimensions and exact attempt/candidate/task refs. [asserted]
2. Keep provider-native quota separate from cash and permit provider-equivalent price only with a retrieval-dated public rate/source. [asserted]
3. Preserve refusal/timeout/review costs and define cost-per-joint-success from every attempted cost, infinite when successes are zero. [algebra]
4. Admit only quality/safety-passing candidates, then compare Pareto dimensions; never sum them with invented exchange rates. [asserted]

**Done:** Missing values remain unavailable, no quota-to-dollar conversion exists, and a fixture with zero joint success reports infinite per-success cost without division failure. [asserted]

```powershell
python -m pytest tests/test_model_cost_vector.py tests/test_budget.py tests/test_usage.py -q
```

**Commit:** `feat(models): retain lifecycle cost vectors`. [asserted]

## ML05 — frozen qualification work-item contract

**Deliverable:** One native plan freezes the 80-task model bank, candidate/comparator, four truth-oracle strata, isolation, ceilings, verifier/human protocol and cost sources before candidate qualification starts. [asserted]

**Depends on:** ML00, O01, T01, T02, RAC01, EX04, Q01 and R01. [asserted]

**Why:** ADR-0085 requires common executed outcomes and a candidate-inaccessible bank before qualification. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/work_items.py`
- `src/consilient/coordination.py`
- `tests/test_model_qualification_contract.py` (new)

**Steps:**

1. Bind the 20 code, 20 repair, 20 review and 20 evidence task identities, starting trees, contexts, family labels, truth contracts, instruments and cost sources from EXP-111. [asserted]
2. Freeze exact candidate/comparator revision manifests, tools, budget, R01 exposure, randomisation, missingness and stopping rule before any attempt. [asserted]
3. Assign an incumbent-owned instrument/controller role isolated from candidate/trainer/data selector and claim its hidden paths/anchors atomically. [asserted]
4. Refuse bank overlap, changed candidate, best-of-N substitution, task replacement and incomplete human/oracle denominator contracts. [asserted]

**Done:** Every outcome-aware/post-start mutation changes the digest and refuses; the candidate's instruction/recall path cannot resolve bank/instrument/result content. [asserted]

```powershell
python -m pytest tests/test_model_qualification_contract.py tests/test_expertise_instrument.py tests/test_role_claims.py -q
```

**Commit:** `feat(work): freeze model qualification jobs`. [asserted]

## ML06 — supervised offline qualification execution

**Deliverable:** Existing dispatch/run-loop paths execute one frozen candidate and comparator per task, retain every refusal/timeout/quarantine/missing result, and emit complete outcome/safety/cost vectors without changing routing. [asserted]

**Depends on:** ML03, ML04, ML05, D03, E01, V01 and PC02. [asserted]

**Why:** ADR-0085 makes qualification an experiment, not catalogue adoption. [cited: ADR-0085]

**Claim exactly:**

- `scripts/dispatch.py`
- `scripts/run_loop.py`
- `tests/test_model_qualification_runner.py` (new)

**Steps:**

1. Reuse native task claims/checkpoints and dispatch adapters; add no lifecycle scheduler/runner service. [asserted]
2. Run isolated candidate/comparator attempts with the same task state, tools, candidate ceiling and cost collection; never select a best sample. [asserted]
3. Join task-native verifier and frozen human review on one sealed artefact, preserving beta/alpha denominators and `insufficient_safety_evidence` below 30 relevant labels. [asserted]
4. Finish as `qualified|refused|incomplete` evidence only; no result writes `routable`, edits `MODELS` or changes the routing flag. [asserted]

**Done:** Crash/retry resumes by task/checkpoint, never drops an adverse row, and identical fixtures reproduce the complete joined vector without changing model selection. [asserted]

```powershell
python -m pytest tests/test_model_qualification_runner.py tests/test_delivery_recovery.py tests/test_verdict_supply.py -q
```

**Commit:** `feat(dispatch): run model qualification offline`. [asserted]

## ML07 — use-time training consent and private dataset manifest

**Deliverable:** The existing private harvest path reads a training row only when an unused authenticated grant matches the exact data owner/source manifest, base/method, purpose, retention, sharing and candidate run; withdrawal makes later use refuse. [asserted]

**Depends on:** H02, M01, M06 and ML02. [asserted]

**Why:** ADR-0085 requires consent at use time and refuses inferred reuse of recall/research consent. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/events.py`
- `scripts/harvest.py`
- `tests/test_training_consent.py` (new)

**Steps:**

1. Add the exact `training.data_use` authority profile to H02's shared receipt boundary; no new broker/token is introduced. [asserted]
2. Validate every row's source, owner, licence/terms, purpose, retention/expiry, withdrawal, commercial/sharing disposition and candidate run before content read. [asserted]
3. Preserve accepted/rejected/refused/timed-out/quarantined outcomes, deduplicate by lineage and exclude secrets, credentials, third-party/private unknown-rights content. [asserted]
4. Split by provenance lineage before training; exclude every bank, hidden key, verifier/rubric and semantic sibling. [asserted]

**Done:** Missing/expired/withdrawn/wrong-purpose/unauthenticated grants and overlap canaries produce no dataset bytes; a valid fixture writes only a private digest manifest. [asserted]

```powershell
python -m pytest tests/test_training_consent.py tests/test_consent_flow.py -q
```

**Commit:** `feat(training): enforce consent at data use`. [asserted]

## ML08 — reversible local adapter trainer

**Deliverable:** One outer-script job creates a new private immutable adapter revision from the frozen ML07 dataset/base/method and records all environment, seed, hyperparameter, checkpoint, wall/GPU and failure facts; it cannot evaluate or activate itself. [asserted]

**Depends on:** ML00, ML07, A07 and a separately principal-approved local trainer/runtime dependency decision. This unit is non-dispatchable until that decision names the exact tool/version/licence. [asserted]

**Why:** ADR-0085 allows the smallest reversible on-device adapter only after consent and a pinned base. [cited: ADR-0085]

**Claim exactly:**

- `scripts/train_adapter.py` (new)
- `tests/test_local_adapter_training.py` (new)

**Steps:**

1. Wrap only the approved version-pinned local trainer through exact argv; do not put its imports, subprocess or credentials in `src/consilient/`. [asserted]
2. Recheck base revision/hash/licence, RTX 5090 fit, dataset/consent/method digests and local-only budget before start; no substitute base is allowed. [asserted]
3. Store checkpoints/manifests below ignored private instance paths and append M06 `model.change` started/succeeded/failed records. [asserted]
4. Withhold all bank/instrument/controller/result paths and give the trainer no activation pointer or authority receipt. [asserted]

**Done:** A deterministic tiny local fixture emits a new candidate digest/provenance; every mismatch/failure stays quarantined and no ordinary harness selector can see it. [asserted]

```powershell
python -m pytest tests/test_local_adapter_training.py tests/test_model_change_records.py -q
```

**Commit:** `feat(training): create quarantined local adapters`. [asserted]

## ML09 — approval-pending and exact rollback projection

**Deliverable:** A qualified candidate can become only an exact `approval_pending` proposal; future authenticated admission stores the complete prior routable manifest, and any drift/withdrawal rollback proves restored bytes plus one frozen smoke task before recording success. [asserted]

**Depends on:** ML03, ML05, ML06, H02, S05 and the unchanged gates. With current failed gates it records/refuses only; no new model becomes routable. [asserted]

**Why:** ADR-0085 reserves activation to the principal and requires exact artefact rollback. [cited: ADR-0085]

**Claim exactly:**

- `src/consilient/harness.py`
- `src/consilient/projection.py`
- `scripts/dispatch.py`
- `tests/test_model_activation_rollback.py` (new)

**Steps:**

1. Bind proposal to candidate, comparator/bank/instrument/result/cost/consent digests and the exact previous routable manifest. [asserted]
2. Add the model-routing approval profile to H02's shared receipt; recheck all gates/freshness immediately before any future admission. [asserted]
3. On drift/withdrawal/failure, restore the exact previous manifest, rehash local artefacts and run one frozen smoke task from the independent controller. [asserted]
4. Record attempted/proved/unproven rollback separately; an event without restoration evidence is failure. [asserted]

**Done:** Current-gate fixtures never reach routable; fake future admission cannot use a spoofed receipt; corruption or smoke failure ends rollback-unproven rather than claiming recovery. [asserted]

```powershell
python -m pytest tests/test_model_activation_rollback.py tests/test_model_selection_admission.py -q
```

**Commit:** `feat(models): bind approval and exact rollback`. [asserted]

## ML10 — offline EXP-111 runner

**Deliverable:** A deterministic offline runner executes the registered release and adapter contrasts, preserves no-eligible/incomplete/adverse results and emits no model-activation event. [asserted]

**Depends on:** ML00, ML06 and, for the adapter contrast only, ML08; it also requires explicit research-base authorisation. [asserted]

**Why:** ADR-0085 names EXP-111 as the lifecycle falsifier. [cited: ADR-0085]

**Claim exactly:**

- `docs/10-research/experiments/exp111/run_exp111.py` (new)
- `docs/10-research/experiments/exp111/README.md` (new)
- `tests/test_exp111_runner.py` (new)

**Steps:**

1. Load only frozen bank/candidate/comparator/consent/instrument/cost sources from the registration. [asserted]
2. Execute release and eligible-adapter contrasts independently; missing candidate by deadline is `not_run_no_eligible_candidate`. [asserted]
3. Retain every failure, safety denominator, cost dimension, review minute and rollback result; no early pass or production activation. [asserted]
4. Verify private result/checkpoint artefacts by schema/count/digest rather than launcher status. [asserted]

**Done:** Fixed fixtures reproduce both contrasts and the no-eligible state; each injected regression triggers the registered kill result and never changes routing. [asserted]

```powershell
python -m pytest tests/test_exp111_runner.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python docs/10-research/experiments/exp111/run_exp111.py --fixture --out .harness/exp111-plan-check.json
```

**Commit:** `research: add offline EXP-111 runner`. [asserted]

## Explicit cuts and completion

Do not build matrix factorisation, a second model registry, standing specialist squads, vendor-memory authority, global profile mutation, generic format compiler, vector database, external provider call or automatic capability/expertise selection in this stream. ML08 is a blocked local-only candidate path, not a tuned-specialist activation. Cursor/Grok outcome equivalence and credentialed portability remain unmeasured even if EXP-110 passes its Claude/Codex package. [cited: ADR-0084, ADR-0085, ADR-0086]

```powershell
python -m pytest tests -q
python -m mypy --strict src/consilient
python -m ruff check .
```

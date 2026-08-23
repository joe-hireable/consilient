# Dependency corrections for the 57-unit build graph

The brief is wrong in two operational particulars: `.harness/build_driver.py` loads the static
`.harness/plan-units.json` rather than reparsing the plans on each tick, and that JSON both adds
edges which their `Depends on:` prose rejects and omits the declared `F04 -> F05` edge. [measured]
The brief also gives two incompatible test baselines, 932 passed/1 skipped and 891 passed; neither
number affects this report-only graph audit. [measured]

## Scope and method

The measured 24-level baseline is reproduced exactly by the 57 units and 127 `deps` edges in
`.harness/plan-units.json` at SHA-256
`38080302EA1A6AD981C0D5C261D17479A75DF62FDA631138CDAFF3A2B6AA681A`. [measured]
Because the assignment says every declared dependency, this audit covers those 127 modelled edges
plus `F04 -> F05`, which is declared in the plan but absent from the JSON: 128 examined edges in
total. [measured] Principal decisions, ADR rulings, experiment outcomes and external configuration
remain blockers but are not unit vertices and are outside the edge count. [asserted]

The source snapshots are: [measured]

- `EDA`: `2026-08-22-evidence-decision-action-plan.md`, SHA-256
  `6C5532D5EBF52D4779618C1175A6050342EE20F42672735E7FB6D54D8FB8D787`.
- `FTD`: `2026-08-22-foundation-task-delivery-plan.md`, SHA-256
  `B001B1F252B9F857A3A12CF2DDB32FC8C47AB2C399E801E47865CD31407A42CB`.
- `HSI`: `2026-08-22-human-self-improvement-plan.md`, SHA-256
  `3D154BD09350D0929E9B686EF9587AB01B6192D444951DD4C071A1B17D6E634D`.
- `MD`: `2026-08-22-memory-documentation-plan.md`, SHA-256
  `5480952AA085A4161F259ABD6663055519EF7AF018F6E28A4ABDED91B008093F`.

`REAL` means the dependent consumes a predecessor output and cannot satisfy its own focused tests
without it. `ORDERING-ONLY` means the edge only serialises a shared claimed path. `UNJUSTIFIED`
means neither semantic consumption nor a live shared claim is established. [asserted] Ambiguous
semantic consumption is retained as `REAL`, as the brief requires. [asserted]

The JSON `claims` arrays are cumulative and are not unit-local. Every claim comparison below is
therefore copied from the unit's Markdown `Claim exactly` block; `(new)` annotations are not part of
path identity. [measured] All quotations, line locators, path sets and intersections below are
measured from the four snapshots; every verdict and semantic explanation is asserted. [measured]
[asserted]

## Edge audit: evidence, decision and action

| Edge | Exact supporting text, or its absence | Verdict |
|---|---|---|
| `F03 -> E01` | E01 requires a “complete, replayable component-verification record required for later correlation” (`EDA:108`); F03 supplies “one stable event_id” and exact earlier-event resolution (`FTD:82,96`). Direct consumption is ambiguous. | **REAL** [asserted] |
| `F03 -> V01` | V01 “quarantines relationally invalid verdict rows” and tests unknown/duplicate joins (`EDA:138,155`); F03 supplies unique exact references. Direct consumption is ambiguous. | **REAL** [asserted] |
| `E01 -> V01` | V01 tests “unknown/duplicate outcomes and verdicts” and “missing component joins” (`EDA:155`); E01 defines the outcome record being joined (`EDA:108-119`). | **REAL** [asserted] |
| `F03 -> A01` | The unit says “F03, E01 by shared-path order” (`EDA:175`); nothing says A01 consumes F03 output. | **ORDERING-ONLY** [asserted] |
| `E01 -> A01` | The same “by shared-path order” sentence is the only support (`EDA:175`); A01 defines intent/receipt, not verification outcomes. | **ORDERING-ONLY** [asserted] |
| `A01 -> A02` | A02 derives admission “from actual manifest facts” (`EDA:203`); A01 defines `EffectManifest` and the closed effect set (`EDA:171,183`). | **REAL** [asserted] |
| `F03 -> P01` | “Enforce ... earlier exact references through F03” (`EDA:257`). | **REAL** [asserted] |
| `A02 -> P01` | P01 tests “every admission class” and derives `record_level` (`EDA:250,254`); A02 produces the admission enum/disposition (`EDA:217`). | **REAL** [asserted] |
| `T03 -> P01` | No closure/conflict output is named. The only support is the shared-path sequence `T03 -> P01` on `work_items.py` (`EDA:61`). | **ORDERING-ONLY** [asserted] |
| `P01 -> P02` | P02 makes reconstructed assembly “a required decision reference” (`EDA:271`); P01 defines the protocol-bearing decision record (`EDA:250`). | **REAL** [asserted] |
| `C01 -> P02` | P02 requires “complete same-question lookup” and an “earlier same-task assembly” (`EDA:282,292`); C01 supplies the committed-request contract (`FTD:108`). Consumption is ambiguous. | **REAL** [asserted] |
| `T01 -> P02` | P02 requires an “earlier same-task assembly” (`EDA:292`); T01 supplies native work-item identity/state (`FTD:192`). Consumption is ambiguous. | **REAL** [asserted] |
| `L02 -> P02` | Nothing in P02 mentions a generated-document manifest, generated requirements or any L02 output. | **UNJUSTIFIED** [asserted] |
| `D01 -> P02` | `protocol_threshold()` consumes “relative cost” (`EDA:282`); D01 produces the durable delivery estimate/reforecast (`FTD:330`). | **REAL** [asserted] |
| `F03 -> Q01` | Q01 must reproduce “exposure identities/order” from replay (`EDA:324`); F03 supplies stable event identity (`FTD:82`). Consumption is ambiguous. | **REAL** [asserted] |
| `E01 -> Q01` | Q01's source check fails if “a component-outcome producer can run without the start token” (`EDA:325`); E01 supplies that component-outcome kind. | **REAL** [asserted] |
| `V01 -> Q01` | Q01 passes replay-derived sampling through `beta.from_connection()` (`EDA:324`); V01 implements the admissible human-beta consumer/projection (`EDA:151,158`). | **REAL** [asserted] |
| `P01 -> Q01` | Nothing in Q01 consumes a decision record; `EDA:306` identifies shared `events.py` claim order. | **ORDERING-ONLY** [asserted] |
| `Q01 -> Q02` | Q02 “joins one selected exposure” (`EDA:350`); Q01 creates and freezes the selected exposure queue (`EDA:302,317`). | **REAL** [asserted] |
| `E01 -> Q02` | Q02 joins the “exact protocol component key-set” and complete component roll-up (`EDA:350,356`); E01 supplies component outcomes. | **REAL** [asserted] |
| `V01 -> Q02` | Q02 is read-only and contributes no authenticated verdict or beta row (`EDA:337,358-360`). Only `projection.py` overlaps. | **ORDERING-ONLY** [asserted] |
| `F03 -> G01` | G01 resolves “unique valid earlier id/kind/hash references” (`EDA:389`), exactly F03's output. | **REAL** [asserted] |
| `E01 -> G01` | G01 must “refuse repeated verification identities/correlation keys” (`EDA:389`); E01 defines those records/keys. | **REAL** [asserted] |
| `P01 -> G01` | G01 classifies “a decision's immutable evidence references” (`EDA:370`); P01 creates those references (`EDA:250,257`). | **REAL** [asserted] |
| `Q02 -> G01` | The dependency is explicitly “by shared projection-path order” (`EDA:374`); no review-card output is consumed. | **ORDERING-ONLY** [asserted] |
| `A02 -> A03` | `RecoveryProof` binds the manifest (`EDA:414`) and failures become capability gaps/refusals (`EDA:424`); A02 supplies manifest-derived admission/capability classification. | **REAL** [asserted] |
| `F02 -> A03` | A03 requires its proof operation's decision/intent identities and emits a bound result (`EDA:402,421`); those records transitively consume F02's atomic transaction. Consumption is ambiguous. | **REAL** [asserted] |
| `F03 -> A03` | A03 binds the completed proof digest to a separate proposed operation (`EDA:421`), transitively requiring exact stable references. Consumption is ambiguous. | **REAL** [asserted] |
| `P01 -> A03` | The proof operation requires “its own minimal decision/intent identities” (`EDA:421`); P01 supplies the decision. | **REAL** [asserted] |
| `P02 -> A03` | Nothing in A03 mentions Better-Than-Best selection, instruction assembly, reconstruction or a P02 output. | **UNJUSTIFIED** [asserted] |
| `A03 -> A04` | A03 emits “a bound proof result for a later live-operation decision” (`EDA:402`); A04 consumes the valid pre-action chain (`EDA:434`). | **REAL** [asserted] |
| `F02 -> A04` | “Use the F02 locked transition” (`EDA:453`). | **REAL** [asserted] |
| `F03 -> A04` | A04 reserves operation identity and validates the complete ordered chain (`EDA:453,457`), consuming F03 identity/reference semantics. | **REAL** [asserted] |
| `P01 -> A04` | A04 consumes an “autonomous decision” or protected proposal/authority chain (`EDA:447`). | **REAL** [asserted] |
| `P02 -> A04` | P02 makes its assembly a required decision reference when the protocol completes (`EDA:271`); A04 consumes a valid complete pre-action chain (`EDA:434,447`). Conditional but semantic. | **REAL** [asserted] |
| `A04 -> G02` | G02 evaluates inside “the fake action boundary” before fake reach (`EDA:467,484`); A04 creates that boundary. | **REAL** [asserted] |
| `G01 -> G02` | `evaluate_consilience()` “consumes the G01 report” (`EDA:478`). | **REAL** [asserted] |
| `A04 -> A05` | Outbound can reach only “through A04” and “consumes only effects.admit_effect()” (`EDA:498,509`). | **REAL** [asserted] |
| `G02 -> A05` | Nothing in A05 consumes `evaluate_consilience()` or its annotation; it names only the frozen A04 interface (`EDA:509,515`). | **UNJUSTIFIED** [asserted] |
| `A04 -> A06` | Computer use executes only “through A04” and “consumes only effects.admit_effect()” (`EDA:529,540`). | **REAL** [asserted] |
| `G02 -> A06` | Nothing in A06 consumes G02 output; its only named boundary input is A04. | **UNJUSTIFIED** [asserted] |
| `A04 -> A07` | A07 must not grant another boundary handle and requires every admitted child effect to have its own operation chain (`EDA:560,581`); A04 supplies that handle/chain. | **REAL** [asserted] |
| `A05 -> A07` | A07 requires the executable scan to find no unmediated raw sink (`EDA:578,583`); A05 removes the existing send-before-record path (`EDA:500,515`). | **REAL** [asserted] |
| `A06 -> A07` | The same scan requires A06's removal of the act-before-append browser path (`EDA:531,545-548`). | **REAL** [asserted] |
| `A05 -> A08` | A08 builds a generic event projection and names no outbound-connector output; its fixtures can use canonical events directly. | **UNJUSTIFIED** [asserted] |
| `A06 -> A08` | A08 names no computer-use output; its generic replay fixtures do not require connector migration. | **UNJUSTIFIED** [asserted] |
| `G01 -> A08` | A08's projection includes “consilience status” (`EDA:605`); G01 produces that status/report (`EDA:370,382`). | **REAL** [asserted] |
| `G02 -> A08` | A08 renders “report-only consilience status” (`EDA:605`); G02 produces the report-only annotation (`EDA:478,485`). | **REAL** [asserted] |
| `Q02 -> A08` | Nothing in A08 consumes a review card/presentation. Only `projection.py` and `dashboard.py` overlap; `EDA:57,63` fixes their claim order. | **ORDERING-ONLY** [asserted] |
| `A02 -> A09` | A09 derives counts from the “closed classification contract” and six protected classes (`EDA:637,642`); A02 implements that mapping (`EDA:222`). | **REAL** [asserted] |
| `A08 -> A09` | A09 consumes attempt/refusal/timeout states (`EDA:625,637`); A08 projects refused, failed, unknown and residual states (`EDA:593,605`). | **REAL** [asserted] |
| `Q02 -> A09` | Nothing in A09 consumes a review card/presentation. Only `projection.py` and `dashboard.py` overlap. | **ORDERING-ONLY** [asserted] |

## Edge audit: foundation, task delivery, memory and documentation

| Edge | Exact supporting text, or its absence | Verdict |
|---|---|---|
| `F01 -> F02` | “while holding the F01 lock” (`FTD:56`). | **REAL** [asserted] |
| `F02 -> F03` | “Reject duplicate IDs inside one transaction and against the locked prefix” (`FTD:94`). | **REAL** [asserted] |
| `F03 -> C01` | C01 requires “source turns ... [to be] digest-bound” (`FTD:108`); F03 supplies stable identity and exact references. | **REAL** [asserted] |
| `C01 -> C02` | “always retain active commitment/corrections” (`FTD:137`). | **REAL** [asserted] |
| `O01 -> C02` | “It may run in parallel with O01 because its paths are disjoint” (`FTD:139`). | **UNJUSTIFIED** [asserted] |
| `C01 -> C03` | “resolves the exact commitment/plan references and prefix anchor” (`FTD:303`). | **REAL** [asserted] |
| `O01 -> C03` | “resolves the exact commitment/plan references and prefix anchor” (`FTD:303`). | **REAL** [asserted] |
| `T01 -> C03` | “A correction fences the old revision and reuses only byte-compatible sealed work” (`FTD:303`). | **REAL** [asserted] |
| `T02 -> C03` | “fence new claims and stale completion under the atomic transition” (`FTD:317`). | **REAL** [asserted] |
| `T03 -> C03` | “a correction racing closure retains the old adverse attempt, blocks stale closure” (`FTD:320`). | **REAL** [asserted] |
| `C01 -> C04` | “emits C01/O01/T01/D01 records” (`FTD:442`). | **REAL** [asserted] |
| `C03 -> C04` | C04 requires a correction fixture and runs `tests/test_delivery_intake.py` (`FTD:457,467`). Consumption is ambiguous. | **REAL** [asserted] |
| `D01 -> C04` | “emits C01/O01/T01/D01 records” (`FTD:442`). | **REAL** [asserted] |
| `D04 -> C04` | “returns its D04 start projection” (`FTD:442`). | **REAL** [asserted] |
| `O01 -> C04` | “emits C01/O01/T01/D01 records” (`FTD:442`). | **REAL** [asserted] |
| `T01 -> C04` | “emits C01/O01/T01/D01 records” (`FTD:442`). | **REAL** [asserted] |
| `C01 -> O01` | “binding the commitment digest and whole-plan digest” (`FTD:177`). | **REAL** [asserted] |
| `F03 -> O01` | “Store predecessor identity/revision/hand-off-contract digest only” (`FTD:179`). | **REAL** [asserted] |
| `O01 -> T01` | “Materialise only streams from a matching frozen plan” (`FTD:207`). | **REAL** [asserted] |
| `T01 -> T02` | T02 requires task readiness, predecessor receipts and candidate ordinal before issuing a lease (`FTD:221`). | **REAL** [asserted] |
| `E01 -> T03` | T03 requires “every frozen verifier receipt” before closure (`FTD:250`); E01 supplies the verification record (`EDA:108`). | **REAL** [asserted] |
| `T01 -> T03` | “A native item closes only after its matching attempt.outcome” (`FTD:250`). | **REAL** [asserted] |
| `T02 -> T03` | “Run after T02 if both would claim current work-item tests in the same branch” (`FTD:252`). The exact claims are disjoint, so the condition is false. | **UNJUSTIFIED** [asserted] |
| `T03 -> T04` | T04 requires exact blockers and latest sealed artefacts/receipts in the task projection (`FTD:277`). | **REAL** [asserted] |
| `C03 -> D01` | Nothing beyond bare `Depends on:`. D01 never mentions `DeliveryIntake`, correction fencing or any C03 output; its focused acceptance omits C03 tests (`FTD:330-350`). | **UNJUSTIFIED** [asserted] |
| `O01 -> D01` | D01 requires “resource, stream” fields (`FTD:342`), consuming O01's frozen stream plan. | **REAL** [asserted] |
| `D01 -> D02` | Nothing in D02 consumes an estimate. Both units claim `events.py`, so only global path sequencing applies. | **ORDERING-ONLY** [asserted] |
| `T02 -> D02` | D02 binds the checkpoint's “fencing epoch” and compares “the live claim epoch” (`FTD:357,373`). | **REAL** [asserted] |
| `D02 -> D03` | D03 projects “the latest valid checkpoint” and starts a “new run/epoch” (`FTD:386`). | **REAL** [asserted] |
| `T03 -> D03` | D03 “never reruns a completed predecessor” and reconstructs “ready unfinished streams” (`FTD:386,399`). | **REAL** [asserted] |
| `A05 -> D04` | D04 is same-machine only and “any later outward delivery consumes” A05 (`FTD:415`). Later delivery is not this unit. | **UNJUSTIFIED** [asserted] |
| `D01 -> D04` | D04 requires a deterministic “start/window projection” and pre-breach exception, consuming the estimate (`FTD:413`). | **REAL** [asserted] |
| `D02 -> D04` | D04 binds “checkpoint chains” and an invalid checkpoint refuses Done (`FTD:428,432`). | **REAL** [asserted] |
| `T03 -> D04` | D04 requires closure and refuses Done for a missing dependency/check (`FTD:427,432`). | **REAL** [asserted] |
| `T04 -> D04` | D04 requires the final delivery card and makes visible messages projections, extending T04's dashboard output (`FTD:413,429`). | **REAL** [asserted] |
| `E01 -> M01` | The schedule says this “serialises events.py” and “do[es] not add product semantics” (`MD:47`). | **ORDERING-ONLY** [asserted] |
| `F03 -> M01` | M01 requires “exact F03 validation” and says “Append through F02/F03 only” (`MD:78-79`). | **REAL** [asserted] |
| `M01 -> M02` | M02 projects the captured-record view and operates on capture/object/relation outputs (`MD:92,103-107`). | **REAL** [asserted] |
| `T03 -> M02` | The schedule says this only “serialises projection.py” and adds no product semantics (`MD:47`). | **ORDERING-ONLY** [asserted] |
| `M02 -> M03` | M03 requires superseded/contested records and binds “exact accepted prefix/projection identity” (`MD:132,134`). | **REAL** [asserted] |
| `M01 -> M04` | M01 supplies the “event/object” seam; M04 requires a resolvable source object (`MD:151,164`). | **REAL** [asserted] |
| `M02 -> M04` | M02 supplies the “temporal projection” seam; M04 extends it with manifest heads (`MD:151,165`). | **REAL** [asserted] |
| `M03 -> M04` | Nothing does. M04 never consumes recall text, receipts, cursors or selection output. | **UNJUSTIFIED** [asserted] |
| `M04 -> M05` | M05 consumes “the M04 selector result” and binds selected manifest IDs/version digests (`MD:193,195`). | **REAL** [asserted] |
| `T02 -> M05` | The schedule says this only “serialises scripts/dispatch.py” and adds no product semantics (`MD:47`). | **ORDERING-ONLY** [asserted] |
| `M04 -> M06` | M06 resolves every capability reference “through F03/M01/M04” (`MD:223`). | **REAL** [asserted] |
| `F03 -> L01` | “Depends on: none. It may start after F03 in parallel with M01” (`MD:239`). No shared path or consumed output exists. | **UNJUSTIFIED** [asserted] |
| `M01 -> L01` | The same sentence says L01 may run “in parallel with M01”; exact claims are disjoint (`MD:239`). | **UNJUSTIFIED** [asserted] |
| `L01 -> L02` | L02 admits `docs/decisions/index.md` through `scripts/build_decision_index.py --check` (`MD:283`). | **REAL** [asserted] |
| `L01 -> L03` | “Depends on: none. It may run in parallel with L01-L05” (`MD:303`). | **UNJUSTIFIED** [asserted] |
| `L05 -> L03` | “Depends on: none. It may run in parallel with L01-L05” (`MD:303`). | **UNJUSTIFIED** [asserted] |
| `L02 -> L04` | “Derive generated surfaces from docs/generated-manifest.json” (`MD:352`). | **REAL** [asserted] |
| `L04 -> L05` | “Run the L04 checker across all twenty-one paths” (`MD:405`). | **REAL** [asserted] |
| `L02 -> L06` | L06 requires the manifest runner in CI (`MD:434-435`). | **REAL** [asserted] |
| `L03 -> L06` | L06 requires the settled-record ratchet in CI (`MD:434-435`). | **REAL** [asserted] |
| `L05 -> L06` | L06 requires the Class-W checker over the full specification glob (`MD:434-435`). | **REAL** [asserted] |

## Edge audit: trusted human ingress and self-improvement

| Edge | Exact supporting text, or its absence | Verdict |
|---|---|---|
| `A07 -> H01` | “H01 is also blocked until A07 proves child harnesses and direct wrappers cannot invoke the issuer” and “Refuse to begin until A07” (`HSI:23,80`). | **REAL** [asserted] |
| `F03 -> H01` | Nothing says H01 consumes F03's stable-reference output. H01 only adds transitions to “the existing writer”; the schedule identifies the shared `events.py` lane (`HSI:64,70,82`). | **ORDERING-ONLY** [asserted] |
| `H01 -> H02` | H01 “durably mints human_action_receipt.v1”; H02 makes writers “consume the same receipt ID atomically” and validates the “shared envelope” (`HSI:68,95,113`). | **REAL** [asserted] |
| `Q01 -> H02` | H02 consumes “Q01's frozen review-queue contract”; its verdict profile binds queue/protocol/attempt (`HSI:36,97`). | **REAL** [asserted] |
| `H02 -> H03` | “consume it through H02's validator” (`HSI:135`). | **REAL** [asserted] |
| `S03 -> H03` | H03 consumes the receipt “against the exact S03 proposal card” and tests card mutation (`HSI:123,134`). | **REAL** [asserted] |
| `F03 -> S01` | Nothing ties S01's contract/receipt/policy to F03's stable-reference output. The schedule identifies only an `events.py` lane (`HSI:64`). | **ORDERING-ONLY** [asserted] |
| `H01 -> S01` | S01 says the opposite: “Refusal machinery may precede H01”; the lane also runs `S01 -> H01`, not this direction (`HSI:64,150`). | **ORDERING-ONLY** [asserted] |
| `A07 -> S02` | “Offline fixtures may land first; an uncontained real candidate records candidate_unexecutable” (`HSI:176`). | **UNJUSTIFIED** [asserted] |
| `S01 -> S02` | Nothing in S02 names an S01 output. The only support is the bare dependency assertion and shared `promote.py` lane (`HSI:64,176`). | **ORDERING-ONLY** [asserted] |
| `M03 -> S03` | M03 creates canonical recall receipts/omission validation; S03 adds “explicit non-content omission reasons to recall/instruction receipts” (`MD:120,133`; `HSI:215`). | **REAL** [asserted] |
| `S02 -> S03` | S03 renders the card “from S02 facts” (`HSI:200`). | **REAL** [asserted] |
| `T04 -> S03` | Nothing says S03 consumes T04's task-view output. S03 only extends the “existing dashboard”; both claim `dashboard.py` (`HSI:200`). | **ORDERING-ONLY** [asserted] |
| `A07 -> S04` | The activation predicate requires “A07 is current”; S04 says “Refuse before editing if any dependency reference is absent” (`HSI:45,229,240`). | **REAL** [asserted] |
| `H03 -> S04` | S04 admits a commit only with “one unused H03 receipt” (`HSI:227`). | **REAL** [asserted] |
| `S02 -> S04` | S04 requires staged/resulting objects to “match S02/S03” (`HSI:227`). | **REAL** [asserted] |
| `S03 -> S04` | The exact S03 proposal/card binds the commit (`HSI:227,243`). | **REAL** [asserted] |
| `S04 -> S05` | S04 produces a commit-bound receipt; S05 activates only the durably approved candidate (`HSI:245,255-257,275`). | **REAL** [asserted] |
| `S05 -> S06` | S05 produces the durable active pointer; S06 restores and proves the prior pointer (`HSI:255,272-275,285,301-304`). | **REAL** [asserted] |

## Declared edge absent from the modelled graph

| Edge | Exact supporting text | Verdict |
|---|---|---|
| `F04 -> F05` | F05 “may touch harness.py only on the measured deregistration branch, so F04 must release the harness.py lane first” (`FTD:544`). No F04 semantic output is consumed. | **ORDERING-ONLY** [asserted] |

## Claim sets for every non-REAL edge

All path sets and exact intersections in this section are measured. [measured]

| Edge | Predecessor claim set | Dependent claim set | Intersection; disjoint? |
|---|---|---|---|
| `F03 -> A01` | `{src/consilient/events.py, tests/test_event_identity.py}` | `{src/consilient/effects.py, src/consilient/events.py, tests/test_effect_contract.py}` | `{src/consilient/events.py}`; no |
| `E01 -> A01` | `{src/consilient/events.py, tests/test_v0_invariants.py}` | `{src/consilient/effects.py, src/consilient/events.py, tests/test_effect_contract.py}` | `{src/consilient/events.py}`; no |
| `T03 -> P01` | `{src/consilient/work_items.py, src/consilient/projection.py, tests/test_work_item_closure.py}` | `{src/consilient/events.py, src/consilient/work_items.py, tests/test_decision_protocol.py, tests/test_work_items.py}` | `{src/consilient/work_items.py}`; no |
| `L02 -> P02` | `{docs/generated-manifest.json, .github/scripts/check_generated_documents.py, scripts/build_requirements.py, docs/40-spec/requirements.md, tests/test_generated_documents.py}` | `{src/consilient/instructions.py, tests/test_instructions.py}` | `empty`; yes |
| `P01 -> Q01` | `{src/consilient/events.py, src/consilient/work_items.py, tests/test_decision_protocol.py, tests/test_work_items.py}` | `{src/consilient/events.py, src/consilient/projection.py, src/consilient/beta.py, src/consilient/verification.py, tests/test_review_queue.py, tests/test_v0_invariants.py}` | `{src/consilient/events.py}`; no |
| `V01 -> Q02` | `{src/consilient/projection.py, src/consilient/beta.py, src/consilient/cli.py, tests/test_verdict_supply.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py, scripts/verdict.py, tests/test_review_card.py}` | `{src/consilient/projection.py}`; no |
| `Q02 -> G01` | `{src/consilient/projection.py, src/consilient/dashboard.py, scripts/verdict.py, tests/test_review_card.py}` | `{src/consilient/events.py, src/consilient/projection.py, tests/test_consilience_gate.py}` | `{src/consilient/projection.py}`; no |
| `P02 -> A03` | `{src/consilient/instructions.py, tests/test_instructions.py}` | `{src/consilient/effects.py, scripts/dispatch.py, tests/test_recovery_proof.py}` | `empty`; yes |
| `G02 -> A05` | `{src/consilient/effects.py, tests/test_consilience_gate.py}` | `{src/consilient_connectors/outbound.py, tests/test_outbound.py}` | `empty`; yes |
| `G02 -> A06` | `{src/consilient/effects.py, tests/test_consilience_gate.py}` | `{src/consilient_connectors/computer_use.py, tests/test_computer_use.py}` | `empty`; yes |
| `A05 -> A08` | `{src/consilient_connectors/outbound.py, tests/test_outbound.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py, tests/test_action_projection.py}` | `empty`; yes |
| `A06 -> A08` | `{src/consilient_connectors/computer_use.py, tests/test_computer_use.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py, tests/test_action_projection.py}` | `empty`; yes |
| `Q02 -> A08` | `{src/consilient/projection.py, src/consilient/dashboard.py, scripts/verdict.py, tests/test_review_card.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py, tests/test_action_projection.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py}`; no |
| `Q02 -> A09` | `{src/consilient/projection.py, src/consilient/dashboard.py, scripts/verdict.py, tests/test_review_card.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py, tests/test_autonomy_friction.py}` | `{src/consilient/projection.py, src/consilient/dashboard.py}`; no |
| `O01 -> C02` | `{src/consilient/events.py, src/consilient/work_items.py, tests/test_organisation_plan.py}` | `{src/consilient/recall.py, src/consilient/instructions.py, tests/test_recall.py, tests/test_instructions.py}` | `empty`; yes |
| `T02 -> T03` | `{src/consilient/coordination.py, scripts/dispatch.py, tests/test_coordination.py, tests/test_dispatch.py}` | `{src/consilient/work_items.py, src/consilient/projection.py, tests/test_work_item_closure.py}` | `empty`; yes |
| `C03 -> D01` | `{src/consilient/work_items.py, src/consilient/coordination.py, tests/test_delivery_intake.py}` | `{src/consilient/events.py, src/consilient/projection.py, tests/test_delivery_estimates.py}` | `empty`; yes |
| `D01 -> D02` | `{src/consilient/events.py, src/consilient/projection.py, tests/test_delivery_estimates.py}` | `{src/consilient/events.py, src/consilient/coordination.py, scripts/dispatch.py, tests/test_checkpoints.py, tests/test_dispatch.py}` | `{src/consilient/events.py}`; no |
| `A05 -> D04` | `{src/consilient_connectors/outbound.py, tests/test_outbound.py}` | `{src/consilient/events.py, src/consilient/work_items.py, src/consilient/projection.py, src/consilient/dashboard.py, tests/test_delivery_outcome.py}` | `empty`; yes |
| `E01 -> M01` | `{src/consilient/events.py, tests/test_v0_invariants.py}` | `{.gitignore, src/consilient/events.py, src/consilient/records.py, tests/test_records.py}` | `{src/consilient/events.py}`; no |
| `T03 -> M02` | `{src/consilient/work_items.py, src/consilient/projection.py, tests/test_work_item_closure.py}` | `{src/consilient/projection.py, tests/test_memory_projection.py}` | `{src/consilient/projection.py}`; no |
| `M03 -> M04` | `{src/consilient/recall.py, scripts/recall.py, tests/test_recall_receipts.py}` | `{src/consilient/events.py, src/consilient/capabilities.py, src/consilient/projection.py, scripts/capability_context.py, tests/test_capability_manifests.py}` | `empty`; yes |
| `T02 -> M05` | `{src/consilient/coordination.py, scripts/dispatch.py, tests/test_coordination.py, tests/test_dispatch.py}` | `{src/consilient/instructions.py, scripts/dispatch.py, tests/test_dispatch_memory.py}` | `{scripts/dispatch.py}`; no |
| `F03 -> L01` | `{src/consilient/events.py, tests/test_event_identity.py}` | `{scripts/build_decision_index.py, docs/decisions/index.md, tests/test_decision_index.py}` | `empty`; yes |
| `M01 -> L01` | `{.gitignore, src/consilient/events.py, src/consilient/records.py, tests/test_records.py}` | `{scripts/build_decision_index.py, docs/decisions/index.md, tests/test_decision_index.py}` | `empty`; yes |
| `L01 -> L03` | `{scripts/build_decision_index.py, docs/decisions/index.md, tests/test_decision_index.py}` | `{.github/scripts/check_adr_trail.py, tests/test_adr_trail.py}` | `empty`; yes |
| `L05 -> L03` | `{tests/test_living_document_inventory.py, docs/superpowers/specs/2026-08-22-answer-quality.md, docs/superpowers/specs/2026-08-22-autonomous-qa.md, docs/superpowers/specs/2026-08-22-dependency-scheduling.md, docs/superpowers/specs/2026-08-22-living-documentation.md, docs/superpowers/specs/2026-08-22-memory-and-capability.md, docs/superpowers/specs/2026-08-22-model-lifecycle.md, docs/superpowers/specs/2026-08-22-observability-and-steering.md, docs/superpowers/specs/2026-08-22-one-surface.md, docs/superpowers/specs/2026-08-22-portable-capability.md, docs/superpowers/specs/2026-08-22-self-improvement.md, docs/superpowers/specs/2026-08-22-squad-roles.md, docs/superpowers/specs/2026-08-22-task-management.md, docs/superpowers/specs/2026-08-22-verdict-supply.md}` | `{.github/scripts/check_adr_trail.py, tests/test_adr_trail.py}` | `empty`; yes |
| `F03 -> H01` | `{src/consilient/events.py, tests/test_event_identity.py}` | `{src/consilient/events.py, scripts/human_action_broker.py, tests/test_human_action_ingress.py}` | `{src/consilient/events.py}`; no |
| `F03 -> S01` | `{src/consilient/events.py, tests/test_event_identity.py}` | `{src/consilient/events.py, src/consilient/promote.py, tests/test_promote_contracts.py}` | `{src/consilient/events.py}`; no |
| `H01 -> S01` | `{src/consilient/events.py, scripts/human_action_broker.py, tests/test_human_action_ingress.py}` | `{src/consilient/events.py, src/consilient/promote.py, tests/test_promote_contracts.py}` | `{src/consilient/events.py}`; no |
| `A07 -> S02` | `{scripts/dispatch.py, .github/scripts/check_effect_paths.py, tests/test_dispatch.py, tests/test_v0_invariants.py}` | `{src/consilient/promote.py, scripts/promote_loop.py, tests/test_promote_instrument.py}` | `empty`; yes |
| `S01 -> S02` | `{src/consilient/events.py, src/consilient/promote.py, tests/test_promote_contracts.py}` | `{src/consilient/promote.py, scripts/promote_loop.py, tests/test_promote_instrument.py}` | `{src/consilient/promote.py}`; no |
| `T04 -> S03` | `{src/consilient/dashboard.py, tests/test_task_dashboard.py}` | `{src/consilient/dashboard.py, src/consilient/recall.py, src/consilient/instructions.py, tests/test_promote_card.py}` | `{src/consilient/dashboard.py}`; no |
| `F04 -> F05` | `{src/consilient/harness.py, tests/test_headroom.py, tests/test_model_pools.py}` | `{scripts/dispatch.py, src/consilient/harness.py, tests/test_grok_arm.py, docs/00-context/grok-arm-2026-08-23.md}` | `{src/consilient/harness.py}`; no |

## Verdict counts and chain findings

The 127 modelled edges contain 94 `REAL`, 17 `ORDERING-ONLY` and 16 `UNJUSTIFIED` verdicts.
[measured count of asserted verdicts] Including the omitted `F04 -> F05` declaration gives 94
`REAL`, 18 `ORDERING-ONLY` and 16 `UNJUSTIFIED` across 128 examined edges. [measured count of
asserted verdicts]

The H chain is genuinely semantic and serial: `H01 -> H02 -> H03` is `REAL`, and H03 also consumes
S03's exact proposal card. [asserted] `F03 -> H01` is only the `events.py` lane. [asserted]

The six-unit S sequence is not fully semantic. `S01 -> S02` is only shared-`promote.py` ordering;
`S02 -> S03 -> S04 -> S05 -> S06` is genuinely serial. [asserted] `H01 -> S01` is an ordering edge
in the wrong direction, `A07 -> S02` is not a build edge because offline fixtures may land first,
and `T04 -> S03` only serialises `dashboard.py`. [asserted]

## Corrected critical path

For each unit, the computation is `level(unit) = 1 + max(level(real predecessor))`, or level 1
when no `REAL` predecessor remains; the critical path is the maximum unit level. This is the same
topological-level method that reproduces the brief's baseline. [measured]

Applying all 33 non-REAL corrections to the 127-edge modelled graph reduces the critical path from
24 to **16 levels**. [measured] At the brief's approximate thirty minutes per level, eight removed
levels are approximately **four hours**. [algebra]

```text
L1:  A01 F01 F04 F05 L01 L03 R01 S01 S02
L2:  A02 F02 L02
L3:  F03 L04
L4:  C01 E01 L05 M01 P01
L5:  A03 C02 G01 L06 M02 O01 V01
L6:  D01 M03 M04 Q01 T01
L7:  M05 M06 P02 Q02 S03 T02 T03
L8:  A04 C03 D02 T04
L9:  A05 A06 D03 D04 G02
L10: A07 A08 C04
L11: A09 H01
L12: H02
L13: H03
L14: S04
L15: S05
L16: S06
```

One corrected critical path is: [measured]

```text
F01 -> F02 -> F03 -> C01 -> O01 -> T01 -> P02 -> A04 -> A06 -> A07
    -> H01 -> H02 -> H03 -> S04 -> S05 -> S06
```

`F04 -> F05` is already absent from the modelled graph and is `ORDERING-ONLY`, so including its
declaration in the audit does not change the corrected levels. [measured] [asserted]

## Three removals with the largest immediate delivery value

An exhaustive comparison of all three-edge subsets of the 33 modelled corrections finds two
optimal sets, each reducing the current graph from 24 to 19 levels. [measured] The preferred set is
below because it removes the graph edge whose direction directly contradicts its plan: [asserted]

1. Remove `H01 -> S01`: 24 to 22 levels by itself; S01 explicitly may precede H01. [measured]
   [asserted]
2. Then remove `C03 -> D01`: 22 to 21; D01 consumes the frozen O01 stream plan, not C03 output.
   [measured] [asserted]
3. Then remove `T03 -> P01`: 21 to 19; it is only the shared `work_items.py` lane. [measured]
   [asserted]

Those three corrections save five levels, approximately two and a half hours at the brief's
assumption. [algebra] Replacing `H01 -> S01` with `S01 -> S02` gives the other equally deep
three-edge correction set; applying both first does not add their individual savings because they
break the same old tail. [measured]

## Conservative holds and blind spots

The following ambiguous edges remain `REAL`: `F03 -> E01`, `F03 -> V01`, `C01 -> P02`,
`T01 -> P02`, `F03 -> Q01`, `F02 -> A03`, `F03 -> A03`, `P02 -> A04` and `C03 -> C04`.
[asserted] A focused implementation-level consumer trace could demote them; the plan text alone is
not strong enough to remove them safely, so the brief's conservative rule controls. [asserted]

This audit did not test implementations, validate the referenced ADRs/specifications, exercise
external verifier configuration or model merge conflicts. [measured] Ordering-only edges still
require claim-aware integration sequencing; removing them from the build dependency graph assumes
the driver's stated separate-worktree build and serial merge discipline. [asserted] No plan, spec,
ADR, source file, gate or graph input was edited. [measured]

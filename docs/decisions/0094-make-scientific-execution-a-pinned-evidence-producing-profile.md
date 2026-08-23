# 0094. Make scientific execution a pinned evidence-producing profile, not a second laboratory platform

- **Status:** PROVISIONAL — EXP-137 can remove the scientific profile while retaining ordinary
  generic execution. [asserted]
- **Date:** 2026-08-23. [measured]
- **Deciders:** Joe Brown supplied the native scientific, mathematical and open-data requirement in
  `../00-context/the-machine-2026-08-22.md`; Codex dispatch
  `20260823T104916-1ac395a993` owns this provisional mechanism, which he has not reviewed.
  [measured]
- **Inquiry tier reached:** T1 ground for the design and incumbents. The dependency footprint is a
  local measurement, not the decision's T3 test; the killing comparison, EXP-137, has not run.
  [measured]
- **Executable model:** none for this categorical boundary decision. EXP-137 is the executable,
  paired outcome comparison that can remove the profile. [asserted]

## Context

The principal requires native scientific and mathematical capability, including experiments and
simulations that can find and use open data. Open data is a different class of facts from a model's
weights only when the retrieved bytes, licence and transformation are identified; a recalled number
or mutable URL is still an assertion. [measured: working principle 10] [asserted]

The brief states the Inquiry trigger too narrowly. The live contract is
`(G1 reversibility OR G2 blast radius) AND G3 prior dispersion AND G4 formalizability`, followed by
the expected-regret/cost stop; G4 requires a decision variable, objective and one free parameter.
Simulation reports sign, threshold and regime, never a world-number. [measured:
`../20-design/inquiry-tier.md:13-22,39-66`]

The requested mathematical operations are already mature library capabilities, and frontier tools
already execute Python. The architectural question is therefore not whether Consilient should write
another statistics stack. It is whether a thin, reproducible scientific contract produces better
decisions than the same Owner using generic executable tools. [cited:
`../superpowers/specs/2026-08-23-scientific-capability.md` S1-S5] [asserted]

The product package deliberately declares no runtime dependencies and package-wide AST tests reject
third-party imports. Existing dispatch, work-item, instruction, recall, knowledge, coordination,
budget and event surfaces already own execution and durable records. A separate scientific
orchestrator would duplicate those chokepoints. [measured: `../../pyproject.toml:28-35`;
`../../tests/test_v0_invariants.py:3226-3235,4206-4227`; scientific-capability specification §2]

## Decision

Adopt a **single-Owner scientific profile** provisionally. It extends existing orchestration and
recording; it is not another platform, queue, router, writer, model vote or source dependency.
[asserted]

1. **Location.** Scientific execution runs in a separately locked, isolated local environment outside
   `src/consilient/`. The implementation build unit chooses its path. No scientific distribution is
   added to product metadata, and no new `consil` subcommand is created. [asserted]
2. **Dependency floor.** Pin `numpy==2.5.2`, `scipy==1.18.1`, `sympy==1.14.0` and
   `pandas==3.0.5`, including every transitive wheel and hash. Use the standard library and the
   existing knowledge path for no-key HTTPS acquisition. Add a specialised package only when a
   pre-registered method or selected data format cannot be executed by this floor. [cited:
   scientific-capability specification §3] [asserted]
3. **One lifecycle.** `dispatch.py` launches the Owner; `work_items.py` holds the task;
   `instructions.py` supplies the profile; `recall.py` supplies bounded prior context;
   `scripts/knowledge.py` and its existing `knowledge.retrieved` event hold acquisition receipts;
   `coordination.py` owns claims; `budget.py` owns ceilings; and `events.py` remains the only durable
   append path. Extend these paths where fields are missing. [measured] [asserted]
4. **Data before result.** Metadata-only discovery and licence admission precede the hypothesis. The
   hypothesis is registered before any outcome-bearing body is requested or cache opened; a bounded
   acquisition process then seals unread bytes and exposes only the manifest until the start event.
   Record the dataset selection rule, immutable version identity, content URL, data-licence identity
   and text digest, retrieval time, exact bytes and SHA-256, redistribution obligations and a private content-addressed snapshot.
   Every deterministic transform binds ordered input, code, environment, parameters and output
   hashes. Absence of an explicit admissible licence, any credential/account requirement,
   mutable-only identity or ambiguous sensitive-data authority refuses acquisition. [cited: scientific-capability
   specification S6-S9] [asserted]
5. **Expiry.** Re-run from an exact matching snapshot when the source disappears, while reporting that
   the source is unavailable. Different remote bytes are a new dataset version. With neither exact
   remote bytes nor an exact snapshot, derived results expire as decision support. A missing or
   changed licence refuses reuse or redistribution even when cached bytes remain. [asserted]
6. **Hypothesis before access.** Add `hypothesis.registered` and `experiment.started` contracts to the
   existing event-reference boundary. Direct URL, cache and content-file reads remain unavailable to
   the Owner. Start must resolve an earlier hypothesis event by ID, kind and digest plus the sealed
   dataset digest before the runner becomes the only admitted content reader; a result resolves that
   start plus hypothesis, dataset, code and environment digests. Amendments append a reasoned
   superseding version before start. Any change after start is a new experiment and leaves the original outcome assigned. [measured: existing
   event identity/reference/atomic-append substrate in `../../src/consilient/events.py`] [asserted]
7. **Simulation gate.** T0/T1 remains the default unless the live Inquiry trigger and regret/cost
   check pass. Pre-register the full parameter range and a source-anchored inventory of materially
   different plausible structural forms, with explicit exclusions. A blinded pre-outcome challenger
   checks the set against independently retrieved domain sources; inability to bound serious rivals
   returns `structurally_unbounded`. Sweep the admitted forms. If any reverses the action/sign, removes the threshold or
   moves it beyond the material tolerance, return `assumption_determined`, name the discriminating
   measurement and refuse the action-level conclusion. Stable simulations emit only sign, threshold
   and regime tagged `[simulated]`. [algebra] [asserted]
8. **Different-class verification.** Default to one candidate Owner, then require an isolated second
   agent to execute the sealed artefact and independently re-derive the decision without the first
   write-up before a T2/T3 result is decision-grade. This is the live Inquiry minimum, not a vote:
   missing, non-reproducible or disagreeing derivation refuses decision-grade status. Executed data
   and verifier artefacts are the new inductions; agreement over prose earns no credit, and the
   verifier cannot inherit the principal's verdict, gate, spend or publication authority. [measured:
   `../20-design/inquiry-tier.md:85-94`] [asserted]
9. **Routing remains shut.** `routing_orchestration_enabled` stays `false`; this decision opens no gate,
   unattended route, external repository, credential, metered call, spend or publication. [measured]

The complete capability, provenance schema, hypothesis fields, sensitivity rule and implementation
checks are normative in `../superpowers/specs/2026-08-23-scientific-capability.md`. [measured]

## Evidence

- A binary-only CPython 3.13/Windows x86-64 resolution on 23 August 2026 produced eight wheels:
  **66,334,930 download bytes (63.262 MiB)** and an installed target of **10,866 files,
  326,691,897 logical bytes (311.558 MiB)**. Every wheel hash is recorded in the specification.
  Windows Application Control blocked SciPy loading from the temporary target, so this measures cost
  and identity, not successful execution on that policy configuration. [measured]
- NumPy, SciPy, SymPy and pandas document the array/random, statistical/numerical/optimisation,
  symbolic and tabular capabilities adopted here. ChatGPT Data Analysis documents that a frontier
  incumbent already writes and executes Python for calculations and statistical analysis. [cited:
  scientific-capability specification S1-S5]
- W3C Data on the Web Best Practices, PROV-O, DataCite's current metadata schema and the Open
  Definition licence catalogue supply the version, provenance, citation and licence precedents; the
  design projects their necessary fields into the existing event record rather than inventing an
  ontology. [cited: scientific-capability specification S6-S9]
- The current knowledge path already records URI, query and content digest, while the event validator
  already requires source, licence, retrieval time and status. Its current policy conflates source
  and licence URLs and does not enforce an open-data licence set, so extension is necessary but a
  second ledger is not. [measured: scientific-capability specification §2]
- The event substrate already provides UUID identity, duplicate refusal, locked-prefix transition
  validators, atomic compare-and-append and exact earlier-reference resolution. Hypothesis ordering is
  an extension of an enforced boundary, not a prose-only promise. [measured:
  `../../src/consilient/events.py`]

## Evidence against

This may be a laboratory nobody needs. The repository's earlier design says code, files,
spreadsheets and experiments are table stakes already supplied by harnesses and skills; only deciding
when to experiment was worth building. Frontier tools already execute code, and the selected
libraries already embody the algorithms. A capable Owner using a short instruction, ordinary Python
and retained scripts may match this profile without persistent scientific machinery. [measured:
`../20-design/living-system.md:106-121`] [cited: scientific-capability specification S1-S5]

Execution can make decisions worse: a biased dataset, wrong test, leaked oracle, incorrect objective
or assumption-determined model produces precise nonsense. Pre-registration freezes bad plans as
effectively as good ones, while structural-sensitivity checklists can become ritual comparisons
between similarly wrong models. Domain expertise and causal identification are not installed with
SciPy. [asserted]

Data acquisition is maintenance-heavy plumbing. URLs disappear, schemas drift, licence terms differ,
native wheels age and pinned environments need security and compatibility work. The reference floor
alone occupies 311.558 MiB before any dataset. For many decisions, strong reasoning plus retrieved
citations is faster, cheaper and sufficient. [measured] [asserted]

The generic-execution arm in EXP-137 is therefore the serious alternative, not a weak control. If it
matches the scientific profile, keep ordinary tools and delete the claimed outcome advantage of the
profile. [asserted]

## Consequences

- Scientific numbers can be traced to exact source, licence, bytes, transform, environment,
  hypothesis and result identities. [asserted]
- A source disappearing produces an explicit reproducible-from-cache or expired result instead of a
  silent replacement. [asserted]
- Assumption-determined simulation refuses false precision, and reasoning/retrieval remains the cheap
  default. [asserted]
- The product package remains standard-library-only, while the optional scientific environment adds
  eight pinned artefacts and at least the measured reference footprint. [measured] [asserted]
- Implementers must maintain locks, provenance validation, snapshots and result bundles; the added
  review and expiry work may outweigh the decisions rescued. [asserted]
- No claim is made that the temporary environment executed successfully, that these packages prove a
  model correct, or that the profile generalises beyond EXP-137's frozen composition. [measured]

## Enforcement

This specification-only decision claims no source enforcement. Each implementation increment must
ship its smallest executable check in the same commit. At minimum, prospective checks must refuse:
third-party product imports; ambient or hash-mismatched packages; missing/custom licences;
credentialled or metered acquisition; private/loopback redirects; changed or oversized bytes; direct
outcome reads before hypothesis/start; post-start hypothesis edits; wrong-order or wrong-digest event
references; simulated world-numbers; trusted thresholds from structure-flipping or omitted-form
fixtures; and decision-grade results with no blinded independent re-derivation receipt. Existing CLI count, routing flag and
principal-authority invariants remain green. [asserted]

EXP-137 is the killing check for the organisational claim. It freezes 60 tasks before any evaluated
outcome, runs all tasks in reasoning-only (`R`), generic-execution (`G`) and scientific-profile (`S`)
arms, retains refusals/timeouts/missing receipts as adverse intent-to-treat outcomes, and counts both
rescues and harms. `G` versus `R` tests execution; only `S` versus `G` tests whether this profile earns
existence. [asserted]

## What would overturn this

- If EXP-137 does not show the pre-registered material `G`-over-`R` improvement without more
  false-safe errors, retain reasoning/retrieval as default and ordinary execution as an explicit
  task-local tool. [asserted]
- If `G` improves on `R` but `S` does not materially improve decision-grade outcomes over `G`, retain
  the locked tools and receipts but remove the scientific profile's claimed outcome advantage.
  [asserted]
- If imports cannot be exercised from an approved isolated location, the environment is unavailable;
  measured footprint is not a substitute for execution. [measured] [asserted]
- If source/licence/byte identity cannot be reproduced, results bind to historical artefacts only and
  expire for current decisions. [asserted]
- Any implementation that needs a second writer, queue, router, credential or product dependency
  requires a successor ADR rather than an exception to this one. [asserted]

## Publication candidate

No. The design is provisional, its killing experiment is unrun, its isolated environment has not
been execution-verified on this machine policy, and publication remains the principal's decision.
[measured] [asserted]

# Design capability assessment: mechanical verification, open tooling, and surface cohesion

## Scope and provenance

- [measured] Read-only assessment conducted from worktree `fleet-condensation`; writes restricted to this dispatch artefact.
- [measured] Figma, Lucid, and Claude Design connectors are unauthenticated locally and treated purely as architectural reference points.
- [asserted] Design capability is not v0; Consilience remains bounded by the observe-only v0 increment.

## 1. The fast oracle split

- [asserted] Design bifurcates into a mechanical fast-oracle tier and an aesthetic slow-oracle tier. The split strictly holds.
- [cited] Mechanical checks run in seconds via headless execution: WCAG 2.2 contrast ratios, tap-target bounding boxes, focus order, ARIA attributes (`axe-core`, MPL-2.0), layout containment across breakpoints (320px–1440px), text overflow, and cumulative layout shift (`Playwright`, Apache-2.0).
- [asserted] The non-mechanical tier (aesthetic hierarchy, brand coherence, mental-model clarity, conversion efficacy) lacks a fast oracle. Its true oracle is delayed market adoption (weeks to months) with confounded attribution (`docs/20-design/q24-oracle-latency-2026-08-20.md`).
- [asserted] Consilience can measure verifier false-accept rate (β) solely on the mechanical tier. The aesthetic tier cannot be verified by models without violating Working Principle 5 (self-reported scores are not signal); the system must label aesthetic output `unverified`.

## 2. Different-class facts: surviving structures vs echo

Applying Whewell's second clause and Ao et al. (2026, arXiv:2603.26993) [cited]:

- **Surviving structures (Consilient):**
  1. *Generator model vs. Headless mechanical checker:* Model emits code/DOM; headless browser runs deterministic DOM geometry and accessibility assertions. Exogenous signal: physical layout engine [asserted].
  2. *Token schema vs. Pixel rasterisation:* Model modifies Design Tokens Community Group (DTCG) JSON; automated rasteriser renders PNG and executes visual regression diffing. Exogenous signal: raster matrix vs. AST [asserted].
  3. *Artefact vs. Static component inventory:* Linter checks emitted tokens against a strictly typed design system schema. Exogenous signal: external repository constraint [asserted].
- **Cut structures (Echo):**
  1. *Multi-model design review panels (e.g. Claude + Gemini debating beauty):* **CUT.** Shared prompt context without exogenous ground truth is pure echo [asserted].
  2. *Persona-prompted design critics (e.g. "Review as VP of Design"):* **CUT.** Prompt variation does not supply a different class of facts [asserted].
  3. *Brief vs. output debate:* **CUT.** Models arguing over requirements text is ungrounded conversation [asserted].

## 3. Prior art and adopt-versus-build

- [cited] **W3C Design Tokens Community Group (DTCG):** Standardised JSON specification for design tokens. Makes design systems textually diffable in Git and mechanically verifiable via JSON Schema.
- [cited] **Penpot (Kaleidos, MPL-2.0):** Open-source web design platform using SVG and DTCG tokens natively. Exposes an MCP server and plugin API.
- [cited] **Style Dictionary (Amazon, Apache-2.0):** Build system transforming DTCG JSON into platform-specific CSS/iOS/Android constants.
- [asserted] **Recommendation: Adopt open standards; build zero design editor software.** Adopt DTCG JSON for token definitions and Git-diffable SVG for layout primitives (per ADR-0036). Use `axe-core` and `Playwright` for headless mechanical verification. Wrap Penpot's MCP export if visual editing is required; never build a bespoke canvas.

## 4. Why existing surfaces feel convoluted

- [asserted] The confusion Joe observes across chats, cowork, code, dispatch, and remote control stems from **state fragmentation without an append-only provenance spine**, not a missing design canvas.
- [asserted] Each vendor surface maintains an ephemeral, isolated conversation session and a disjoint artefact store. When an agent moves between chat, code, and dispatch, state is lost or laundered through lossy summaries.
- [asserted] **Prescription: Fewer surfaces, not a seventh.** Adding a bespoke "Consilience Design App" would compound fragmentation. Design must be treated as repository artefacts (tokens, CSS, SVG, screenshots) managed through the single append-only event ledger and projected into existing workspaces.

## 5. Indefinite deferral case and judgement record

- [asserted] **Strongest deferral argument:** In coding, tests give an immediate binary signal with unambiguous artefact attribution. In design, mechanical checks catch only structural flaws; semantic and aesthetic efficacy remains in the slow, confounded oracle regime.
- [measured] Consilience has not yet established an unbiased sampling frame or calibrated β for code (`src/consilience/beta.py` has zero empirical rows). Expanding to design before Gate A/B would dilute focus.
- [asserted] **Reasoning:** Prioritise coding where fast oracles exist; defer design to a post-v0 gate.
- [asserted] **Rejected option:** Build an LLM design critique harness now. Rejected because it produces echo without ground truth.
- [asserted] **Reversal command:** `rm /mnt/c/Users/jpbpr/Repositories/consilience/.harness/dispatch/design-surface.md`
- [asserted] **Falsifiers:** (1) A machine-checkable aesthetic oracle appears that predicts conversion > chance; (2) Coding β calibration completes and proves domain-blind transferability.

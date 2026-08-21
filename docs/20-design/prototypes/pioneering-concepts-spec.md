# Pioneering Frontend Concepts: The Consilient Agent Command Post

> Status: `[asserted]` — exploratory design architecture for Consilient web, desktop, and mobile surfaces.
> Governed by: ADR-0060 (Open Design method & brand constraints), ADR-0061 (Agent Command Post descriptor),
> ADR-0062 (Command post not a meta-harness), and `docs/20-design/DESIGN.md`.

---

## 1. Executive Summary & Brand Paradigm

Every contemporary AI workspace — Claude Cowork, ChatGPT Work, Hermes Agent, Gemini Spark — is built on the same 2023 legacy metaphor: **a chat column flanked by conversational sidebars, streaming tokens, and "thinking" loading theatre**.

Consilient rejects this entire paradigm. **Consilient is an Agent Command Post. It sends harnesses.**

An Agent Command Post applies mature industrial supervisory control principles (ISA-101.01 High-Performance HMI) to autonomous agent orchestration rather than adopting conversational chatbot tropes:
1. **The resting state is calm:** When the autonomous fleet is executing cleanly within proven verification envelopes, *nothing needs the operator*. (ISA-101 principle: visually calm normal state with immediately recognizable abnormal conditions).
2. **Surfaces are state, not narrative:** The core is the immutable, append-only trajectory record (`.harness/log`), not an ephemeral chat stream.
3. **Pioneering interaction mechanics:**
   - **The Command Post Bridge (Dispatch & Fleet Operations):** Spatial multi-harness fleet radar and capability-gap radar.
   - **The Trajectory Observatory (Deep Proof Inspection):** Non-linear, time-scrubbable execution causality graph and mutation census replay.
   - **The Mobile Enclave Signer (Clear-Signing Asks):** WYSIWYS (What You See Is What You Sign, ERC-7730 pattern) cryptographic attestation for unavoidable human decisions.

---

## 2. The 3 Pioneering Concepts Detailed

### Concept A: The Command Post Bridge (`bridge-command-post.html`)
* **Role:** Primary live operator workstation.
* **Core Paradigm:** Spatial dispatch matrix + active fleet telemetry.
* **Key Mechanics:**
  - **Fleet Radar & Concurrency:** Displays active concurrency against placeholder ceiling bounds ($T_{\text{cycle}} / T_{\text{review}} = 3.125$ capacity vs $\beta$-conditioned 1-slot ceiling).
  - **Capability-Gap Matrix:** Directly maps which harness (`Claude Code`, `Cursor`, `Codex`, `Grok`) is routed to which task class based on *measured empirical outcomes*, not vendor marketing labels (ADR-0054).
  - **Unavoidable Asks Alert:** Elevates only strict ADR-0033 §2 asks across the 7 permitted classes:
    1. Money & spend limits
    2. Passwords, keys & credentials
    3. Publishing, transmitting or exposing anything beyond the machine
    4. Irrecoverable deletion or overwriting
    5. Preferential choices where no fact settles it
    6. Ground truth $\beta$-verdict on candidate diffs
    7. Lifting a gate or approving a specification

### Concept B: The Trajectory Observatory (`trajectory-observatory.html`)
* **Role:** Verification, audit, and failure causality inspection.
* **Core Paradigm:** Interactive trajectory scrubber + mutation census visualizer.
* **Key Mechanics:**
  - **Time-Scrubbable Trajectory Stream:** Replaces scrolling chat with an event-scrubbing timeline. Every state transition is hash-linked to `.harness/log`.
  - **Mutant Survivor Radar & $\beta$-Meter:** Real-time visual representation of killed vs surviving mutants across the verifier suite (EXP-47: $n=1,871$ non-equivalent mutants, $\beta = 0.3132\ [0.29, 0.33]$).
  - **Causality Graph:** Bipartite map of which harness touched which code boundaries, proving cross-family independence vs echo.

### Concept C: The Mobile Enclave Signer (`mobile-signer.html`)
* **Role:** Remote operator on-call verdict & permission device.
* **Core Paradigm:** Hardware-attested, clear-signing action stream (Concept C3 & WYSIWYS pattern).
* **Key Mechanics:**
  - **Clear-Signing Diff Inspection:** Anti-blind-signing interface showing full diff preview before signing buttons activate.
  - **Affordability Floor:** Surfaces ADR-0033 §4 latency floor warning (approvals submitted faster than inspection time logged as `unread`).
  - **Ed25519 Enclave Signature:** Hardware key attestation that signs the human verdict directly into the trajectory log.

---

## 3. Figma Export Specification & Token Mapping

All three prototypes strictly adhere to `docs/20-design/DESIGN.md` tokens:

```
/* Canvas & Surfaces */
--bg:          #0C0E12 (Deep Charcoal Black)
--surface-0:    #14171E (Dark Slate Base Card)
--surface-1:    #1C202A (Elevated Focus Container)
--border:       #2A2F3D (1px Structural Boundary)

/* Inks & Foreground */
--fg-primary:   #F0F2F5 (17.2:1 contrast off-white)
--fg-secondary: #C4C9D4 (11.8:1 secondary copy)
--fg-muted:     #8B93A5 (6.3:1 labels and units)

/* Focal Action & Semantics (Desaturated ~55-65% non-Tailwind) */
--action:       #E2B340 (Electric Ochre — exclusive to pending human decisions)
--action-tint:  #2A2412
--valid:        #2E9E66 (Laboratory Green — measured verification passes)
--valid-tint:   #11261C
--attention:    #DDA136 (Warm Ochre Amber — unmeasured gap / draft state)
--attention-tint:#2B2012
--fault:        #E05349 (Terracotta Crimson — verifier failure / hard stop)
--fault-tint:   #2D1617

/* Typography */
Display:        "Syne", "Cabinet Grotesk", sans-serif (700 / 600)
Body:           "Plus Jakarta Sans", sans-serif (500 / 400)
Numbers/Data:   "Space Mono", "Fragment Mono", monospace (tabular-nums)
```

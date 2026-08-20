# Verified Dynamic Code: Decidability, Empirical β, and Practical Limits

## 1. Existence Proofs and Failure Rates

Admitting dynamic code behind automated verifiers is not new, but empirical history demonstrates non-zero false-accept rates ($\beta > 0$):

| System | Decided Property (Safety Envelope) | Undecided Property (Intent / Semantics) | Documented Failure Rate & Vulnerabilities |
|---|---|---|---|
| **eBPF** (Linux Kernel) | Termination, memory bounds, type safety `[cited]` | Semantic correctness of packet/trace logic `[asserted]` | ~50% of eBPF CVEs reside in the verifier (e.g. ALU range tracking CVE-2021-3490, CVE-2022-23222; 56+ CVEs) `[cited]` |
| **Proof-Carrying Code** (Necula, POPL 1997) | Formal safety invariant via machine-checked proof `[cited]` | Functional program correctness `[asserted]` | Low in small TCB proof checkers; adoption blocked by proof-generation cost `[cited]` |
| **WebAssembly** (Wasmtime) | Linear memory bounds, control-flow integrity `[cited]` | Host-call semantics, logical correctness `[asserted]` | Compiler backend miscompilations enable sandbox escapes (e.g. CVE-2023-26489, CVE-2026-34971) `[cited]` |
| **Erlang/OTP** (`code_change/3`) | Bytecode replacement, process suspension `[cited]` | State compatibility between version schemas `[asserted]` | Zero automated semantic verification; relies on supervisor crash-recovery `[cited]` |
| **Upgradeable Contracts** (ERC-1967) | Admin caller authorisation `[cited]` | Storage layout collisions, re-initialisation, logic `[asserted]` | >$400M lost across 37 incidents; 31,407 upgrade risks detected (arXiv:2508.02145) `[cited]` |
| **Shielded RL** (Alshiekh et al., AAAI 2018) | LTL safety specifications via reactive shields `[cited]` | Policy optimality, unmodelled dynamics `[asserted]` | Sound within discrete model; fails on sim-to-real specification gaps `[cited]` |

## 2. The Decidability Boundary: Safety vs Intent

Rice's Theorem establishes that any non-trivial semantic property of general code is undecidable `[algebra]`. Mechanical verifiers cannot decide intent or functional correctness `[asserted]`. They only decide membership in a restricted, syntactically enforceable safety envelope (e.g., loop bounds, memory ranges, typed contracts) `[asserted]`.

Conflating safety with correctness is fatal `[asserted]`. A verifier guarantees that dynamic code will not violate bounded invariants; it cannot guarantee that the dynamic code does what the user intended `[asserted]`.

## 3. Use-Case Analysis and Cost Distribution

Dynamic code is valuable only where the safety envelope is mathematically specifiable and internal adaptation is high-leverage `[asserted]`:

1. **Kernel Observability & Networking (eBPF):** Packet filtering and tracing without kernel reboots `[cited]`. Envelope: bounded compute and memory. Cost bearer: operator. $\beta$ is managed via privilege controls.
2. **Safe Robotics & Industrial Control:** Action masking via formal shields `[cited]`. Envelope: kinematic keep-out zones. Cost bearer: plant operator.
3. **Adaptive User Interfaces & Accessibility:** Dynamic DOM restructuring or pacing. Envelope: WCAG contrast, layout bounds, non-destructive mutations. Cost bearer: user.

**The Governance Boundary:** Where the cost of a false accept falls on third parties or unconsenting users (e.g., medical devices, autonomous vehicles, automated financial transfers), statistical $\beta$ is insufficient `[asserted]`. The gating constraint is formal regulatory certification (e.g., FDA 510(k), ISO 26262, DO-178C), which requires deterministic guarantees rather than probabilistic confidence `[cited]`.

## 4. Proposed Consilient Experiment: Measuring Verifier β

To measure $\beta$ empirically for dynamic code without relying on self-report:
- **Change Class:** LLM-generated eBPF filters or Python AST transforms constrained by refinement types and memory limits `[asserted]`.
- **Verifier (Test):** In-kernel eBPF verifier or static contract checker `[asserted]`.
- **Independent Oracle (Different Class):** Dual-execution differential fuzzing (Syzkaller/LKL harness) against an adversarial corpus with known ground-truth safety violations `[asserted]`.
- **Metric:** $\beta = \frac{\text{Verifier-accepted buggy artefacts}}{\text{Total buggy artefacts}}$ `[algebra]`.

## 5. The Sceptical Challenge and Verdict

**The Sceptic's Argument:** Dynamic code is a solved problem where the envelope is trivial (memory isolation) and an impossible one everywhere else (Rice's Theorem forbids general correctness verification) `[asserted]`.

**The Refutation:** Dynamic code does not need to verify intent `[asserted]`. Its value lies in decoupling the *safety invariant* (verified mechanically with known $\beta$) from the *optimisation policy* (exploring dynamic code within the envelope) `[asserted]`. The user is shown confidence in the bounded invariant, not a guarantee of functional perfection `[asserted]`.

**Verdict:** Verified dynamic code is practical exclusively within mechanically specifiable safety envelopes where failure costs are internalised; outside bounded sandboxes, automated assurance of intent is impossible `[asserted]`.

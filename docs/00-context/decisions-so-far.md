# Decision log

Every row carries a status and what would overturn it. Nothing here is final; several
were made in a single turn with one reviewer.

Status key: **DECIDED** (Joe stated it) · **PROPOSED** (an ADR argues it) ·
**PROPOSED-UNCONFIRMED** (argued, not yet explicitly accepted) · **SUPERSEDED IN PART**
(a later ADR replaces part of the boundary) · **OPEN** (deliberately unresolved)

---

| # | Decision | Status | Basis | What would overturn it |
|---|---|---|---|---|
| D1 | Build a **meta-harness** above existing agents, not a standalone harness | DECIDED; SUPERSEDED IN PART BY ADR-0027 | Joe: "your definition of meta harness is correct and what I want to do"; EXP-05 exercised six coding compositions over seven control paths [measured] | Adapter maintenance proves disproportionate in continuing use |
| D2 | **Fully open source**, MIT, donate button; acqui-hire welcome but not the goal | DECIDED | Joe, revising an earlier exit-asset framing | — |
| D3 | Not a DeepSeek Harness plugin | PROPOSED | v0.1 breaking changes; wrong audience; it orchestrates models not agents | DSH stabilises and adds agent-level orchestration |
| D4 | **β (verifier false-accept rate) is the organising parameter** | PROVISIONAL | ADR-0002; EXP-01 first pass returned insufficient data [measured] | EXP-01 cannot measure it usefully or the quality identity fails |
| D5 | Cascade with **≥3 tiers**, verified at each hop | PROPOSED | `findings.md` §3: 44% of frontier cost at +4.1pp quality | Bimodal difficulty (Q3) |
| D6 | **No learned routing policy** in v0 | DECIDED; REOPENED FOR INVESTIGATION | `findings.md` §4; EXP-07 crossed the ≥2× investigation trigger on n=1, not the replication threshold [measured] | Replicated EXP-07 evidence overturns ADR-0003 |
| D7 | **No trajectory-corpus moat** | PROPOSED | Follows D6 and D2 | — |
| D8 | Communication via a **native agent-first ticket store**: SQLite coordination projected from an append-only JSONL record | DECIDED | Joe stated native; ADR-0006 decided the substrate [asserted] | ADR-0006's measured overturn conditions fire |
| D9 | **Bounded meetings**, no open-ended agent chat | DECIDED | Joe: "dedicated 'meetings' should be possible though, not open-ended conversation" | — |
| D10 | Every multi-agent structure must name its **exogenous signal** | PROPOSED | Ao/Gao/Simchi-Levi arXiv:2603.26993 | Someone finds an error in the theorem's applicability |
| D11 | **No model battling / debate** | PROPOSED | Verifier available ⇒ best-of-n dominates deliberation | A domain inside the loop with no oracle |
| D12 | **Gate on verifier outcomes, never self-reported confidence** | PROPOSED | Routing literature; calibration failures | A calibrated confidence signal (GATEKEEPER-style) proves cheap enough |
| D13 | Parallelism ceiling **derived**, not user-chosen: `n = T_cycle / T_eff_review` | PROPOSED | `findings.md` §5 (exact algebra) | — |
| D14 | **Critic tier** is the throughput lever | PROPOSED | `findings.md` §5; recall ≡ 1−β | — |
| D15 | `/learn` produces a **compiled skill artifact + held-out eval**, not weight updates | PROPOSED | Model-collapse risk; ACE (ICLR 2026) is the right shape | — |
| D16 | **No RL** until a reward signal is named | PROPOSED | No reward exists for research/spec/planning | — |
| D17 | **Credentials via OS keychain + OAuth device flow**, never chat | PROPOSED | Chat lands in logs/context/session records | — |
| D18 | Cut CASB, semantic ToS scanner, SOC2/HIPAA trails, mTLS-to-GCP | PROPOSED | Enterprise cosplay for a solo OSS project; ToS scanning is not a legal defence | Project acquires enterprise users with those requirements |
| D19 | **One interaction surface** in v0 | PROPOSED | Six channels = six auth models before the loop is proven | — |
| D20 | Keep from the Gemini session: Engineering Ratchet, sandbox tiering, ticket-as-unit-of-work, five-section agent template | PROPOSED | See `30-source-material/gemini-session-critique.md` | — |
| D21 | Cut PSN auto-refactor-at-150-lines | PROPOSED | Arbitrary threshold triggering autonomous rewrites of the skill library | — |
| D22 | Cinch / CASD (constrained decoding work) **shelved as a product**; thesis transplanted | DECIDED | Joe: "use it if useful otherwise shelve it" | — |
| D23 | Add an **Inquiry tier** for research-grade agent decisions | DECIDED (want) / OPEN (design, and whether v0) | Joe's stated requirement; design sketch in `20-design/inquiry-tier.md` | Q14 |
| D24 | Name the project **Consilience** | DECIDED | ADR-0008 [asserted] | Trademark clearance fails |

---

## Standing invariants (adopted from the jobboard-v2 post-mortem)

- **I1.** Any declared chokepoint ships with the lint rule that bans bypassing it, in the
  same commit. Non-negotiable — this is the exact failure that hollowed out the `llm()`
  boundary in `jobboard-v2` (5 access paths, breaker on ~12 call sites, highest-cost paths
  bypassing it entirely).
- **I2.** Any documented behaviour ships with the test that proves it. `jobboard-v2` had a
  flagship pipeline whose queue had no producer, undetected because an empty queue is
  indistinguishable from a healthy one.
- **I3.** No claim in `docs/` without a status tag. See `AGENTS.md`.

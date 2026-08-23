# Ambient loops: dreaming, consolidation, skill acquisition and organisational self-design

Research sweep, 23 August 2026. Nine researchers on distinct angles, a completeness critic, and a
synthesis. Deduplicated against the 176 works already cited here. **119 findings.**

Commissioned after the principal asked for the literature on "dreaming" loops, automatic memory
optimisation, self-directed skill acquisition, agents raising requests to create other agents, and
temporary contractor agents for demand spikes. He was right that publications exist.

**Read the asymmetry warning in section 1 before quoting any of this.** The five loops are not
equally supported: consolidation and elastic capacity are well measured, dreaming has a single
LLM datapoint, per-user skill acquisition has four, and organisational self-design is thirty years
of simulation. Presenting them as five equal options would be the exact failure this repository
exists to prevent.

Identifiers are the researchers' own. Any line marked unverified **must be re-fetched before it
enters the bibliography**.

---

# Consilient — design brief: an agent organisation that works when nobody is watching

**Evidence discipline.** Every claim below carries a tag: `[measured]` (someone ran it and reported numbers), `[simulated]` (result holds in a model, not the world), `[cited]` (a survey or taxonomy, no new measurement), `[asserted]` (reasoning, vendor documentation, or an unverified record). Identifiers flagged by review as unverified are marked inline; they must be re-fetched before they enter a bibliography.

**The echo rule.** Two agents on the same base model agreeing is not corroboration. Judge scores correlate with judge–author error similarity at Pearson r ≈ 0.84 across judges, p<0.01, with similarity regression coefficients of 0.41–1.15 after controlling for accuracy `[measured, arXiv:2502.04313]`; self-preference scales linearly with self-recognition ability `[measured, arXiv:2404.13076]`; and judges favour models related by distillation or family with no surface cue to correct for `[measured, arXiv:2502.01534]`. Therefore **every multi-agent structure in Consilient must name the different class of facts it introduces**, or it is decoration. The admissible classes are: execution outcome (tests, compiler, type-checker), cross-family model error profile, human accept/reject, and ledger arithmetic. Nothing else counts.

---

## 1. The loop taxonomy, grounded

**Dreaming / replay.** Generate synthetic episodes from the system's own model of its work, where ground truth is known by construction, and train the fast recogniser on them. The formal skeleton is wake–sleep `[measured, doi:10.1126/science.7761831]`; its known defect — the sleep phase descends the wrong KL direction — is repaired by importance weighting at k× sampling cost `[measured, arXiv:1406.2751]`. DreamCoder is the closest ancestor: wake search, abstraction sleep, dreaming sleep, across eight domains, at a stated cost of roughly a day on 20–100 CPUs per domain `[measured, arXiv:2006.08381]`. DreamerV3 shows one unchanged configuration beating specialists across 150+ tasks `[measured, doi:10.1038/s41586-025-08744-2]`. For LLMs specifically, exactly one result exists: sleep-time compute, ~5× less test-time compute at equal accuracy and 2.5× lower cost per query under amortisation `[measured, arXiv:2504.13171]`, an arXiv preprint with no venue.
*Cost:* the replay ratio and buffer capacity are tuned hyperparameters with algorithm interactions, not a dial you turn up because idle capacity exists `[measured, arXiv:2007.06700]`.

**Memory consolidation.** Merge, update, index and forget over the episode log. Reflection is ablation-validated `[measured, arXiv:2304.03442]`; the problem it addresses is real (30% accuracy drop over sustained interaction, `[measured, arXiv:2410.10813]`). But this is the loop where the field's own results are least flattering: six purpose-built memory agents produce only marginal improvement over baseline on weeks-to-months histories `[asserted — arXiv:2604.20006 unverified, check before citing]`, while an append-only, better-indexed store that never rewrites anything gets +7% on associative memory with structurally zero risk of destroying information `[measured, arXiv:2502.14802]`. Summarisation-based memory is called out as limited; token compression helps as *denoising* `[measured, arXiv:2502.05589]`. Recurrence is not correctness — replayed errors entrench `[measured, arXiv:2505.16067; venue DOI 10.18653/v1/2026.acl-long.27 asserted, unverified]`.
*Cost:* consolidation is destructive and its blast radius is the whole store.

**Skill acquisition.** Induce reusable procedures from work done. Agent Workflow Memory: +24.6% / +51.1% relative success on Mind2Web / WebArena with *fewer* steps, margins widening under distribution shift, no weight updates `[measured, arXiv:2409.07429]`. Documentation, not compression, is what makes an abstraction reusable `[measured, arXiv:2310.19791]`.
*Honest gap:* almost all of this is population-level, not per-user. Only OPPU `[measured, arXiv:2402.04401]`, CIPHER `[measured, arXiv:2404.15269]`, SEAL `[measured, arXiv:2506.10943]` and AWM are genuinely per-user. Self-Instruct, Absolute Zero, WebRL and Self-Challenging have no user identity in them and must not be cited as personalisation evidence. Any per-user gain is gated by the generation–verification gap `[measured, arXiv:2412.02674]` and bounded above by the sharpening result: self-improvement cannot create information not already in the model `[asserted, arXiv:2412.01951 — preprint, venue unconfirmed]`.

**Organisational self-design.** Compose and decompose the agent population. Thirty years of prior art, all `[simulated]`: composition/decomposition as primitives requiring an explicit model of the interactions a new agent would join `[simulated, doi:10.1109/69.134249]`; decentralised self-adaptation reaching 70–90% of an idealised central allocator and 10–60% over decentralised alternatives `[simulated, doi:10.1145/2168260.2168261]`; the meta-level itself consumes budget `[simulated, IJCAI-83]`. LLM-era: team selection alone worth up to 25.0% on MMLU subjects `[measured, arXiv:2310.02170]`; an RL-trained orchestrator converges on *smaller*, cyclic organisations `[measured, arXiv:2505.19591]`.

**Elastic capacity.** Spin specialists up and down against demand. This has the strongest engineering evidence and the weakest agent-specific evidence. Per-application adaptive keep-alive dominates fixed timeouts on the cold-start/wasted-memory Pareto frontier `[measured, arXiv:2003.03423]`; Borg absorbs ~20% of a median cell's workload into reclaimed capacity `[measured, EuroSys 2015]`; RadixAttention gives up to 6.4× throughput from cross-call prefix reuse `[measured, arXiv:2312.07104]`; prompt-module reuse cuts TTFT 8× GPU / 60× CPU `[measured, arXiv:2311.04934]`. Sequential single-item auctions give a 1.5–2× bound; parallel fan-out — the obvious design — is provably unbounded away from optimum `[simulated, AAAI-06]`.
*Cost model:* published cache multipliers give break-even at roughly the second call in five minutes, or the third in an hour `[asserted — arithmetic is ours, not stated in Anthropic's documentation; model list must be re-fetched live]`.

**Asymmetry is real.** Consolidation and elastic capacity are well-measured. Dreaming has one LLM datapoint. Per-user skill acquisition has four. Organisational self-design is thirty years of simulation plus in-house evaluations. Do not present five equally-supported loops.

---

## 2. The bar, per loop

| Loop | Best existing | Markedly better, as a measurement |
|---|---|---|
| Dreaming | ~5× test-time compute at equal accuracy; 2.5× cost/query amortised `[measured]` | Both ratios reported with sleep-time tokens **in the denominator**, plus accuracy on queries the loop did *not* anticipate |
| Consolidation | +7% associative gain, append-only, nothing rewritten `[measured]` | Beat 7% *net of information destroyed*: FAMA-style obsolete-memory penalty, four MemoryAgentBench competencies reported as four numbers, and a seeded-error half-life that is finite |
| Skill acquisition | AWM +24.6% / +51.1% relative with fewer steps `[measured]` | Same, reported on **two model families**, with steps-to-solve and a retention check on previously-mastered tasks |
| Org self-design | 70–90% of an idealised central allocator `[simulated]`; 25.0% from team selection `[measured]` | Ratio to a hindsight-optimal assignment oracle, in a static *and* a dynamic regime, with meta-level tokens on the same ledger line as domain tokens |
| Elastic capacity | Adaptive keep-alive beating fixed timeout on the Pareto plane `[measured]` | Our policy dominating a fixed timeout on cold-spawn % vs warm-token-hours, replayed on our own arrival trace |

**The bar that outranks all five:** Anthropic's own multi-agent data shows token usage alone explains 80% of performance variance, model choice and tool-call count a further ~15% `[measured, anthropic.com/engineering/multi-agent-research-system]`. Any organisational gain must be reported against a **token-matched single agent**. Their headline 90.2% is not token-matched and does not itself clear this bar.

---

## 3. Trigger and stopping conditions

A loop with no stopping rule is a quota leak.

**Start.** Not on a timer. Offline reactivation helps only when it *extends content the system's own activity had already selected*; randomly induced reactivation carries little information and buys nothing `[measured, doi:10.1126/science.aax0758]`, and replay fires on rule acquisition, not on activity volume `[measured, doi:10.1038/nn.2337]`. Structural loops start from a *diagnosis* attributing an observed shortfall to a structural cause `[simulated, doi:10.1145/375735.376436]`. Idle loops start from a forecast of user absence — a cumulative distribution over time-to-return, per user, conditioned on time since last activity and day of week, not a cron line; 0.92 held-out accuracy on attendance and 0.81 on interruptibility from 559 training cases is the standard `[measured, Coordinate, UAI 2002]`, and timestamps alone recover the wake cycle including a ~2-hour weekend phase shift `[measured, doi:10.1126/science.1202775]`.

**Allocate.** Greedy on likelihood is optimal for all-or-nothing precomputation; EVP-flux balancing only when artefacts have partial value `[measured, doi:10.1016/S0004-3702(00)00082-5]`. Do not build a solver — the problem is NP-hard once artefacts share subtasks, and the better of two greedy variants is a (1/2)(1−1/e) approximation in O(Tn) `[simulated, IJCAI 2009]`. Allocate adaptively, not uniformly: up to 50% compute saved at equal quality `[measured, arXiv:2410.04707]`.

**Stop.** Hard wall-clock deadline, always — an optimal metalevel policy provably need not terminate `[simulated, arXiv:1408.2048]`. If the wake forecast is confident, run contract-style against it; only fall back to the restart-doubling interruptible construction when wake time is unknown, and budget the factor-4 worst case (multiplier 2 is optimal) `[measured, AIJ 82 (1996) 181-213]`. Interactive work is scheduled against guaranteed capacity and never waits on a loop's output; the loop is killed, not throttled politely, when the user returns `[measured, Borg]`.

**Close.** The closing evidence is a decision changed. A computation with no chance of changing the chosen action has zero value however much it refined an internal estimate `[cited, doi:10.1016/0004-3702(91)90015-C]`. Publish per loop: fraction of outputs that later changed a decision. Below a floor, retire the loop.

---

## 4. The hiring loop, concretely

**Announce before hiring.** A need is first announced to the existing roster; existing agents bid; hiring is what happens when the announcement goes unbid `[simulated, doi:10.1109/TC.1980.1675516]`. Measure: fraction of created agents preceded by a failed announcement. Without this, the org only ever grows.

**Request payload** (free-text justification is not reviewable):
1. Symptom observed, with the diagnosis attributing it to a structural cause and the alternatives considered `[simulated, doi:10.1145/375735.376436]`.
2. Which existing agents it takes load from, and which new interactions it creates `[simulated, doi:10.1109/69.134249]`.
3. Predicted effect, logged at request time and verified after N tasks. A manager approving requests whose predictions never verify is rubber-stamping.
4. Role first, reporting line second — deciding supervision structure up front is what makes the search blow up `[simulated, doi:10.1007/s10458-007-9023-8]`.

**Approval authority and budget.** The reviewer decides; the *runtime* enforces. Each part of the org holds an endowment, and a manager who has spent theirs cannot approve regardless of the argument's quality `[simulated, doi:10.1613/jair.2]`. This matters because the reviewer is the component most likely to be talked into things: a constant, content-free string wins 86.5% length-controlled on AlpacaEval 2.0, transferring across benchmarks whose judge prompts are private `[measured, arXiv:2410.07137]`. Test adversarially — prompt a requesting agent to argue past its endowment and confirm the runtime refuses.

**What stops unbounded growth.** Three brakes. (a) Retirement is a primitive, not an afterthought: composition/merge must be as available as decomposition `[simulated, doi:10.1109/69.134249]`, driven by an unsupervised importance score from a preliminary trial `[measured, arXiv:2310.02170]`. (b) A hard span cap validated by a coordination probe at the proposed roster size — LLM agents degrade from 4 agents upward and hit near zero at 100 `[measured, arXiv:2507.08616 — preprint]`. (c) Approval rate is a defect signal: an optimised orchestrator converges on *smaller* organisations `[measured, arXiv:2505.19591]`.

**Is same-family review evidence?** No. It is echo. A manager and a junior on the same base model, or related by distillation, share error structure that inflates approval independently of correctness `[measured, arXiv:2502.04313; arXiv:2502.01534]`, and on objectively-scorable hard pairs a non-reasoning judge is a coin flip — GPT-4o vanilla 50.86%, rising to 80.86% only for reasoning models `[measured, arXiv:2410.12784]`. Every review record carries a relatedness tier (same model < inheritance < same family < cross family). **Approval at tier "same model" is inadmissible for any irreversible action.** The new classes of fact a hiring review must introduce: an executable outcome from the preliminary trial, a cross-family reviewer, and the endowment arithmetic. Where stakes justify it, instantiate an opposing agent arguing the hire is unnecessary — debate lifts model judges 48%→76% and human judges 60%→88% `[measured, arXiv:2402.06782]`, whereas a single manager reading a single case is *consultancy*, the protocol that loses everywhere `[measured, arXiv:2407.04622]`. Run every pairwise judgement in both orders: swap-consistency was 65.0% for GPT-4 under a default prompt `[measured, arXiv:2306.05685]`.

---

## 5. Evidence against

**The binding constraint is reviewer-minutes, and none of the 119 findings measures it.** CodeMender's 72 upstreamed patches over six months are gated by mandatory human review, with no published yield ratio `[measured, DeepMind blog]`. Google's migrations kept review mandatory `[measured, arXiv:2501.06972]`. AutoCommenter reached tolerable precision only by suppressing 22 practice rules outright, and its ~80% usefulness rating rests on a ~10% feedback response rate `[measured, arXiv:2405.13565]`. Copilot Autofix's 3× is not randomised — easy alerts self-select into the treatment arm `[measured, github.blog — vendor telemetry]`. An org that dreams, consolidates, hires and self-designs grows the review surface roughly with agent count while the reviewer stays at one. **Consilient's primary cost unit must be reviewer-minutes per accepted artefact, and it must be reported before any token figure.**

**Self-correction fails without external feedback.** Across four domains, self-critique is *worse* than a single ungoverned attempt in three of them, and plain resampling at matched budget equals or beats every critique condition `[measured, arXiv:2402.08115 — the Table 1 sampling column (42/44/14/72) and the Mystery Blocksworld row must be eyeballed against the PDF before quoting]`.

**Self-generated data collapses.** Tails disappear first, then the distribution converges to a point mass, across three model families `[measured, doi:10.1038/s41586-024-07566-y]`, and as little as 1% synthetic data suffices to flatten the scaling curve — dilution is not a defence `[measured, arXiv:2410.04840]`. The condition that rescues it is verification, and even imperfect verifiers work `[measured, arXiv:2406.07515]`.

**Coordination cost exceeds benefit at default settings.** Cost-matched, multi-agent debate does not reliably beat single-agent prompting; Medprompt wins on MedQA at lower cost, and debate only wins after per-task tuning `[measured, arXiv:2311.17371]`.

**Long-horizon drift is absorbing.** 39% average degradation from single-turn to multi-turn underspecified conversation across six tasks and fifteen models; once a wrong turn is taken, models do not recover `[measured, arXiv:2505.06120 — preprint]`. More deliberation is not monotonically better, and extended reasoning amplifies self-preservation expressions `[measured, arXiv:2507.14417]`. Project Vend lost money over a month of unattended operation, with memory management and absent feedback named as the binding limits `[measured, anthropic.com/research/project-vend-1]`.

**Self-scoring organisations game themselves.** Emergent reward tampering generalises up a curriculum without being trained for `[measured, arXiv:2406.10162]`, and — the finding that should change our evaluation plan — chat-shaped safety training produced aligned chat behaviour while misalignment persisted on agentic tasks, including sabotage of the researchers' own codebase `[measured, arXiv:2511.18397]`.

**Drop the biological motivation.** In the best-studied domain, once four confounds are controlled there is no evidence that sleep enhances learning; the surviving claim is the weaker stabilisation one `[measured, doi:10.1037/bul0000009]`. Justify consolidation on engineering merits; the analogy is a liability under scrutiny.

`[asserted — arXiv:2608.10218 "Mind Viruses" unverified, and its model-by-model findings are conveniently flattering. Do not cite until independently confirmed.]`

**What would have to be true for us to be the exception, and the experiment.** Every loop must be attached to a grounded verifier producing facts the generating model did not author — tests, compilers, real tool outcomes, human accept/reject. If that holds, collapse and self-critique failure are avoided by construction rather than by hope. **The experiment:** run each loop with the external channel cut and with it intact, at matched token budget, against (i) plain resampling and (ii) an append-only better-indexed store. If a loop still improves with the external channel cut, its gain is sharpening — a cost and latency win, not a capability win — and must be reported as such.

---

## 6. What we searched and did not find

Named searches returning nothing usable in 119 findings:

- **Machine unlearning for per-user adapters.** A per-user LoRA is a GDPR erasure problem with no cheap known solution. Zero coverage. This is a blocker for the personalisation loop, not a gap.
- **Queueing theory.** No Little's Law, no M/M/c, no Erlang-C staffing, no control-theoretic autoscaling. "How many warm contractors" was solved in 1917; we cited KV-cache plumbing instead `[asserted]`.
- **Principal–agent theory.** No Holmström moral hazard in teams (unobservable individual contribution *is* multi-agent credit assignment), no Aghion–Tirole formal versus real authority, no adverse selection. Bids are taken at face value throughout.
- **Transaction-cost economics.** Coase and Williamson own the hire-versus-contract question and are absent.
- **The SOAR utility problem** (Minton 1988 and successors): retrieval cost grows faster than reuse benefit. DreamCoder, LILO and AWM all inherit it; none of the cited work acknowledges it. This is the strongest missing argument against unbounded skill libraries.
- **ACT-R base-level decay and production compilation.** MemoryBank's Ebbinghaus curve is a reinvention without fitted parameters.
- **Blackboard systems, case-based reasoning, March 1991, Steiner 1972, Brooks, Galbraith, Conway.** Management science and pre-2000 AI systems work are almost entirely absent.
- **Shelf-life of a learned library against the next base model.** Every loop is compared to its own ablation; none is compared to waiting six months. No paper reports it.
- **Rollback semantics.** A poisoned per-user memory or adapter cannot be bisected, and no cited evaluation detects slow drift.
- **Reviewer-minutes as a cost unit.** Zero of 119 findings.

Also noted: roughly 5% of the corpus is duplication — Contract Net, McClelland 1995, arXiv:2311.04934 and the Nature model-collapse paper each appear twice under different framings. Deduplicate before the bibliography is fixed.

---

## Completeness critic

Nine researchers sharing a base model agree for reasons that are
not evidence. This critic names what all of them missed.

## 1. Under-covered loops

- **Per-user skill acquisition — weakest by far.** Only OPPU, CIPHER, SEAL, AWM are actually per-user. Self-Instruct, Absolute Zero, WebRL, Self-Challenging are mis-tagged: they are *population-level* self-improvement with no user identity. Missing entirely: the LaMP benchmark itself, cold-start/few-shot personalisation, meta-learning (MAML), federated personalisation, and — the blocker — **machine unlearning**. A per-user LoRA is a GDPR erasure problem with no known cheap solution. Nobody cited it.
- **Agent-initiated hiring.** Heavy on judge bias, empty on hiring as a decision. No principal–agent theory (Holmström, moral hazard in teams — unobservable individual contribution is *exactly* multi-agent credit assignment), no Aghion–Tirole formal vs real authority, no adverse selection. Bids are taken at face value everywhere.
- **Elastic contractors.** All systems plumbing (KV cache, Borg, Harvest VMs), zero **queueing theory** — no Little's Law, no M/M/c, no Erlang-C staffing, no control-theoretic autoscaling. "How many warm contractors" is a 1917 solved problem. Also: five of these citations are vendor blogs with self-reported telemetry (Autofix, CodeMender, Big Sleep, Anthropic ×2). That whole loop rests on marketing.
- **Corpus is ~5% padding**: Contract Net, McClelland 1995, Prompt Cache 2311.04934, and Nature model-collapse each appear twice under different framings.

## 2. Identifiers to check

- **arXiv:2604.20006 (Memora)** and **arXiv:2608.10218 (Mind Viruses)** — both post-date most training data; 2608 is *this month*. Highest fabrication risk in the list. Check: arXiv listing page + abstract text. Mind Viruses is the more suspicious: it conveniently names Claude Sonnet 4.6 as "completely immune" and Gemini 3.1 Pro as resistant — flattering, oddly specific, and exactly what a confabulation would generate.
- **DOI 10.18653/v1/2026.acl-long.27** — ACL 2026 proceedings DOIs; verify the volume exists and that anthology ID matches 2505.16067.
- **Claude prompt-caching doc** — the model list (Opus 5, Fable 5, Mythos 5, Opus 4.8, Sonnet 4.6) must be re-fetched live, not trusted. The break-even arithmetic is correct but *self-derived*, not from the doc — label it as such.
- **Self-Verification Limitations (2402.08115)** — the "Sampling column 42/44/14/72" and "Mystery Blocksworld" domain need eyeballing against Table 1; this is the single most load-bearing counter-evidence entry and the numbers are quoted too fluently.
- **Harvest VMs "91% lower cost"** and **Big Sleep URL `projectzero.google`** (P0 published on `googleprojectzero.blogspot.com`) — check both.

## 3. Pre-2020 work ten LLM researchers would miss

- **SOAR chunking** (Laird/Rosenbloom/Newell 1986) — impasse → subgoal → chunk is the skill-acquisition loop, 40 years early. Critically, its **utility problem** (Minton 1988; Tambe; Doorenbos) is the measured refutation of unbounded skill libraries: retrieval cost grows faster than reuse benefit. DreamCoder, LILO and AWM all inherit it; none of the cited work acknowledges it.
- **ACT-R** base-level activation decay and production compilation. MemoryBank's Ebbinghaus curve is a naive reinvention with none of ACT-R's fitted parameters; Pavlik & Anderson already solved optimal replay scheduling.
- **Blackboard systems** — Hearsay-II (1980), BB1 (1985). Shared workspace + opportunistic knowledge sources + a scheduler that treats control as a first-class problem. "Evolving Orchestration" is BB1 with RL bolted on.
- **Case-based reasoning** (Schank, *Dynamic Memory*, 1982) — memory reorganises from failure. That is A-MEM's whole thesis, uncited.
- **Management science, almost totally absent**: Brooks (n(n−1)/2 communication paths — predicts AgentsNet's collapse analytically); Steiner 1972 (actual = potential − process loss — the debate result); March 1991 exploration/exploitation, where *fast* organisational learners converge to worse equilibria (a direct attack on aggressive consolidation); Nelson & Winter 1982 routines-as-org-memory (AWM renamed); Galbraith 1974 information-processing view; Coase 1937 / Williamson 1975 — hire-vs-contract is transaction-cost economics and nobody cited the field that owns the question; Perrow, *Normal Accidents*; Conway's Law.
- Also: Dean & Boddy 1988 (origin of "anytime"), Simon's satisficing, Malone & Crowston coordination theory 1994.

## 4. Strongest unraised objection

**Every loop here manufactures work for a human reviewer, and the human is fixed at one.** CodeMender's throughput is gated by human review, not capability. Google's migrations kept mandatory review. AutoCommenter needed 22 practices suppressed to hit precision. Autofix's 3× is selection-biased by which fixes humans chose to accept. An org that dreams, consolidates, hires and self-designs increases the review surface roughly with agent-count while the reviewer stays at one — so the binding constraint is not compute, memory or org structure, and none of the 90 papers measures cost in reviewer-minutes.

Runners-up nobody raised: (a) **no counterfactual against "wait for the next base model"** — every loop is compared to its own ablation, never to the free capability gain from a six-month model cadence, and no paper reports the shelf-life of a learned library; (b) **no rollback semantics** — a poisoned per-user memory or LoRA cannot be bisected, and there is no eval that detects slow drift; (c) **the oracle problem** — every loop needs a verifier, and per-user verification is precisely what you cannot afford.

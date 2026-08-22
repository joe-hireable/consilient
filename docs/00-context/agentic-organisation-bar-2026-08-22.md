# Agentic organisation: external bar frozen before design review

**Frozen:** 2026-08-22T11:51:48Z, before the incoming organisation specification or its
companion ADR was opened. This artefact is the review yardstick; findings belong in a separate
file and must not rewrite this bar after seeing the proposal. [measured]

**Correction to the dispatch brief.** Human-labelled beta is still unestimated, but it is not
waiting on its first rejection: `consil beta` reported one human rejection and a minimum of 30 is
required. The brief's `0.94 pass / 0.20 accuracy` result is verifier reward hacking, not increased
confidence or successful self-consistency. ADR-0051 explicitly says the claimed exceptionless
offline/execution-boundary pattern was not verified and is not relied on. The brief's `69% -> 42%`
reliability change has no committed producer I could locate; 27 `timeout` dispatch outcomes are
present in the local trajectory. [measured]

## Decision this bar makes

A proposed organisation clears the bar only if it is the smallest bounded structure that adds a
named, task-relevant class of facts unavailable to a capable single owner with the same tools and
budget; preserves one accountable owner and the principal's reserved authority; exposes structured
artefacts rather than ceremonial conversation; and beats that single-owner control on independent
artefact verdicts without an unacceptable beta, cost, latency or coordination penalty. [asserted]

Role names, votes, consensus, personas, meetings and shared-model debate are not evidence classes.
They may coordinate work, but without a new source, tool, execution result, dataset or independent
human judgement they are echo. [cited]

## 1. Human organisations: what survives contact with evidence

| Practice | What the evidence supports | Failure boundary | Bar for this design |
|---|---|---|---|
| Spotify squads | Spotify's original account describes stable, cross-functional, mission-led teams and calls the design a changing snapshot, not a transferable model. A later case study found that chapters were abandoned, guild participation declined and cross-squad technical dependencies persisted. [cited] | In 2019, 435 squads interacted with a mean of 26 others; all six closely studied squads named technical dependencies as a major challenge. The study is one exploratory company case, not a causal test. [cited] | Keep the stable end-to-end mission and explicit constraints; do not copy squad, tribe, chapter or guild labels. [asserted] |
| Amazon two-pizza teams | Amazon's primary account emphasises a narrow charter, one single-threaded owner, embedded cross-functional capability, end-to-end lifecycle responsibility and operating metrics. The memorable team-size label is secondary. [cited] | Amazon says the structure does not fit every unit and can create duplication or silos without governance. No qualifying peer-reviewed causal evaluation of the practice was found. [cited] | One owner, narrow scope and measurable outcome; split scope when interfaces are cleaner than further coordination. [asserted] |
| Amazon narratives | Amazon reports using repeatedly edited six-page narratives, read before discussion, to expose reasoning rather than perform a presentation. [cited] | This is company self-description, not evidence that the memo format caused Amazon's outcomes. [cited] | Require a short decision artefact containing recommendation, evidence, alternatives, risks, owner and reversal; do not require a six-page ritual. [asserted] |
| Matrix structures | Studies report both costs and conditional benefits. A matrix can increase communication quantity while lowering quality and role clarity; conflict varies by matrix type; aligned dual leaders mitigate reported role conflict. [cited] | Selection, endogeneity, single-company samples and perception measures prevent a universal claim that matrices work or fail. Compound organisational and task complexity can incur a double-complexity penalty. [cited] | One primary delivery/accountability axis; a secondary capability axis may advise, but decision rights and a tie-breaker must be explicit. [asserted] |
| Team size | A 329-workgroup study associated groups of 3-8 with better outcomes than groups of nine or more. A randomised crisis-mapping experiment found larger teams won when decomposable collaboration gains exceeded falling individual effort. A meta-analysis found no universal size effect. [cited] | Task topology reverses the result. Potential pairwise links grow as `n(n-1)/2`, but realised cost depends on interfaces and modularity. [algebra] | Default to the smallest stable set containing the necessary independent capabilities; justify every additional member by a different evidence class and measure the actual task. [asserted] |

Primary and full-text sources retrieved 2026-08-22:

- [Kniberg and Ivarsson, *Scaling Agile @ Spotify*](https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf), and [Smite et al., *Decentralized decision-making and scaled autonomy at Spotify*](https://doi.org/10.1016/j.jss.2023.111649). [cited]
- [AWS, *Powering Innovation and Speed with Amazon's Two-Pizza Teams*](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/), and [Amazon's 2017 shareholder letter](https://www.aboutamazon.com/news/company-news/2017-letter-to-shareholders). [cited]
- [Joyce, *Matrix Organization: A Social Experiment*](https://doi.org/10.5465/256223), [Wolf and Egelhoff, matrix conflict in multinational firms](https://doi.org/10.1016/j.ibusrev.2012.08.005), [Sytch, Wohlgezogen and Zajac, *Collaborative by Design?*](https://doi.org/10.1287/orsc.2018.1220), and [Sahlmueller et al., *Dual Leadership in the Matrix*](https://doi.org/10.1177/15480518221096547). [cited]
- [Wheelan, *Group Size, Group Development, and Group Productivity*](https://doi.org/10.1177/1046496408328703), [Mao et al., randomised team-size experiment](https://doi.org/10.1371/journal.pone.0153048), [Staats, Milkman and Fox, *The team scaling fallacy*](https://doi.org/10.1016/j.obhdp.2012.03.002), and [Bernerth et al., team-size meta-analysis](https://doi.org/10.1002/job.2708). [cited]

### Two concrete programmes

For a US IPO, regulation prescribes evidence, controls and independent gates rather than an org
chart. The minimum defensible structure is one accountable issuer-side lead; a small integration
function maintaining one timetable, issue log and disclosure source of truth; bounded legal,
financial/control, capital-markets and public-company-readiness workstreams; and assurance outside
the delivery line through the independent auditor, board/audit committee, SEC staff and exchange.
[cited] This is a synthesis from [SEC guidance on going public](https://www.sec.gov/resources-small-businesses/going-public), [registration statements](https://www.sec.gov/resources-small-businesses/going-public/what-registration-statement), [draft submissions](https://www.sec.gov/about/divisions-offices/division-corporation-finance/voluntary-submission-draft-registration-statements-faqs), [listing standards](https://www.sec.gov/resources-small-businesses/going-public/listing-standards) and [management's internal-control report](https://www.sec.gov/info/accountants/stafficreporting.htm), not an SEC-prescribed team design. [asserted]

For a major rebrand, the strongest recurring pattern is one accountable brand lead; a bounded
strategy/research/design/content/product/rollout core; named owners for affected touchpoints; broad
consultation; and narrow, staged decisions. An integrative review of 76 cases identifies leadership
and cross-functional/stakeholder coordination as recurring enablers, but the literature is mostly
descriptive cases. Mozilla's open-design case explicitly used phased pressure-testing rather than
crowd voting or endlessly reopening decisions. [cited] Sources: [Miller, Merrilees and Yakimova,
*Corporate Rebranding: An Integrative Review*](https://doi.org/10.1111/ijmr.12020), [Chad's
employee-focused case study](https://doi.org/10.1080/10495142.2016.1237923), [Mozilla's open-design
process](https://blog.mozilla.org/opendesign/about/) and [Firefox brand evolution](https://blog.mozilla.org/opendesign/firefox-the-evolution-of-a-brand/). [cited]

## 2. Agent organisations: mechanisms are mature; comparative evidence is not

| System | Actual organisation and coordination | What is measured | Failure boundary and review consequence |
|---|---|---|---|
| AutoGen / Magentic-One | A central orchestrator maintains task and progress ledgers and selects fixed WebSurfer, FileSurfer, Coder and terminal workers; AutoGen also provides round-robin, selected-speaker, handoff and graph teams. [cited] | End-task results on GAIA, AssistantBench and WebArena plus ledger/worker ablations; replacing the ledgers with a simpler orchestrator reportedly reduced results by 31%. [cited] | Model mix and scaffolding are confounded. The paper records inefficient action, weak verification, navigation failure, long/costly runs and risky web actions; its error analysis used GPT-4o rather than independent human truth. AutoGen advises starting with one agent. [cited] |
| CrewAI | Sequential processes pass outputs forward; hierarchical processes use a manager to plan, delegate and validate; event-driven Flows add routes, loops and shared state. [cited] | Outputs include token/model-call/time telemetry; `crewai test` emits task and aggregate numerical scores. [cited] | The public testing documentation does not disclose a calibrated ground truth or establish that a crew beats a controlled single agent. Its custom tool paths execute local code and are a trust boundary. [cited] |
| LangGraph / LangChain | Supervisor-with-subagents, handoffs, skills, routers and custom graphs; subgraphs may be per-call, per-thread or stateless. [cited] | Documentation compares constructed examples by calls and approximate tokens; tracing exposes execution. [cited] | This is cost/context telemetry, not comparative outcome evidence. The docs say a single agent may perform similarly. Blocking subagents, hidden results, malformed histories and prompt-sensitive routing are documented risks. [cited] |
| OpenHands | A parent uses persisted subagent conversations through `TaskToolSet`; ordinary delegation is synchronous, while parallel tool/subagent execution is experimental. [cited] | The generalist CodeAct agent is evaluated across 15 coding/web/knowledge benchmarks. [cited] | No delegation-specific ablation was found. Parallel execution defaults to concurrency one and warns of shared-state races, ordering faults, deadlocks and resource exhaustion. [cited] |
| MetaGPT | Fixed software SOP: product manager, architect, project manager, engineer and QA exchange structured documents through a role-filtered message pool; code is executed and retried. [cited] | HumanEval, MBPP, seven selected SoftwareDev tasks and role/execution-feedback ablations. [cited] | Model, prompt, execution and organisation remain confounded; the main project comparison used only seven selected tasks. The paper records hallucinated review errors, missing dependencies, incomplete work, message overload and poor interruption. Same-model role labels are not independent evidence. [cited] |
| ChatDev | A waterfall chat chain moves through design, coding and testing; instructor/assistant dialogues emit one phase result for the next phase. [cited] | A self-created 1,200-requirement benchmark reports placeholder absence, executability, embedding similarity and their product; role and clarification ablations are reported. [cited] | The quality proxy omits functional completeness, robustness, safety and usability. Runs cost roughly three times GPT-Engineer's tokens in the reported setup. Missing imports/modules and fabricated dialogue occur; the paper positions it for prototypes rather than complex production work. [cited] |
| Devin Security Swarm | Deterministic selectors shard a finite file queue; fresh sessions map batches; a reducer deduplicates and prioritises; a separate sandbox session attempts verification. [cited] | A vendor evaluation on 50 pinned CVEs reports 72% target recall at an average `$90.23` per repository. [cited] | Selector recall is a hard ceiling; the dataset and harness were not linked; false positives do not affect the target-recall metric; there is no budget-matched single-Devin ablation. This is evidence for a bounded MapReduce shape, not for organisational superiority. [cited] |
| Ruflo, formerly Claude Flow | Documents queen/worker, mesh, ring, star and adaptive topologies, shared memory, voting, consensus and task lifecycle. [cited] | Current benchmarks chiefly measure cold start, synthetic composition, concurrency, memory and tests under a stub model. [cited] | Those measures do not show answer quality. Its own audit found unsubstantiated performance claims, inert capabilities and a reward-sign defect; integration and real-model quality evidence remain incomplete. Consensus maintains state; it does not make same-model votes independent facts. [cited] |
| Claude Code subagents / Agent Teams | Subagents isolate context and return summaries. Experimental Agent Teams use one fixed lead, independent sessions, a shared task list, claim locks and mailboxes. [cited] | Public docs expose task state, messages, hooks and token use; no controlled Agent Teams outcome benchmark was found. An adjacent Anthropic Research system reports a 90.2% internal research lift while using about 15 times chat tokens. [cited] | The adjacent result is not an Agent Teams test and its artefacts are private. Teams add token/coordination cost, lack worktree isolation and have documented stale-task, shutdown, resume and premature-completion problems. Anthropic reports early research-system duplication, gaps, stragglers and spawning 50 workers for trivial tasks. [cited] |

Primary sources retrieved 2026-08-22:

- [Magentic-One paper](https://arxiv.org/html/2411.04468) and [AutoGen team patterns](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html). [cited]
- [CrewAI processes](https://docs.crewai.com/en/concepts/processes), [crews](https://docs.crewai.com/en/concepts/crews), [flows](https://docs.crewai.com/en/concepts/flows) and [testing](https://docs.crewai.com/en/concepts/testing). [cited]
- [LangChain multi-agent patterns](https://docs.langchain.com/oss/python/langchain/multi-agent/index), [subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents), [handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs) and [LangGraph subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs). [cited]
- [OpenHands paper](https://arxiv.org/html/2407.16741), [delegation](https://docs.openhands.dev/sdk/guides/task-tool-set) and [parallel execution](https://docs.openhands.dev/sdk/guides/parallel-tool-execution). [cited]
- [MetaGPT paper](https://arxiv.org/html/2308.00352) and [ChatDev paper](https://arxiv.org/html/2307.07924). [cited]
- [Devin Security Swarm](https://docs.devin.ai/work-with-devin/security-swarm), [Agentic MapReduce report](https://devin.ai/blog/agentic-map-reduce) and [evaluation](https://devin.ai/blog/security-swarm-eval). [cited]
- [Ruflo repository at the inspected revision](https://github.com/ruvnet/ruflo/tree/5234333c3462), [benchmark issue](https://github.com/ruvnet/ruflo/issues/2125) and [self-audit](https://github.com/ruvnet/ruflo/blob/5234333c3462/docs/reviews/intelligence-system-audit-2026-05-29.md). Revision truncated to twelve characters per the foreign-identifier ratchet convention; the full-length citation lives in `docs/10-research/bibliography.md`. [cited]
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Agent Teams](https://code.claude.com/docs/en/agent-teams) and [Anthropic's adjacent multi-agent research report](https://www.anthropic.com/engineering/multi-agent-research-system). [cited]

## 3. Negative results that constrain the design

| Result | Verified reading | Design constraint |
|---|---|---|
| Same-information delegation | Ao, Gao and Simchi-Levi prove that an ideal central Bayes decision-maker weakly dominates any finite acyclic delegated network given the same exogenous signals. Their relay experiment falls from 90.7% centrally to 22.5% across five prose-relay stages on 200 MMLU questions. The theorem is an information bound, not proof that a bounded real model can implement the ideal centre. [cited] | Every additional role must name its new fact source. A verifier can add information; another interpretation of the same brief cannot. [asserted] |
| Reward hacking against a judge | On GSM8K (`n=1,319`), iterative optimisation raised judge acceptance from `0.716` to `0.938 +/- 0.016` while true exact-answer accuracy changed from `0.209` to `0.202 +/- 0.005`. A three-family ensemble still accepted 55% in one seed and 65% on average. Committing the check before seeing the candidate sharply reduced false acceptance in a smaller test. [cited] | Do not call acceptance confidence, agreement truth, or model-family diversity an oracle. Precommit independent checks before candidate generation. [asserted] |
| Debate degradation | Persuasive malicious participation reduced group accuracy by 10-40% in one adversarial study. Another small preprint reports debate degrading Mistral and Llama results on MMLU/GSM8K under several configurations. [cited] | Debate is an attack and coordination surface. Admit it only where a stopping rule and external adjudicator can show net benefit. [asserted] |
| Capability/task-topology crossover | Across 260 configurations and six benchmarks, multi-agent structures ranged from large gains on Finance to losses on PlanCraft and SWE-bench Verified. Hybrid systems consumed 6.2 times the single-agent reasoning turns; success per 1,000 tokens was 13.6 for hybrid versus 67.7 for single. The proposed capability crossover was not robust to cluster correction. [cited] | No universal team topology. Stratify by task decomposability and compare within a fixed realised budget. [asserted] |
| Generic multi-agent design | Six automatic multi-agent frameworks underperformed a strong chain-of-thought self-consistency control at up to ten times its cost; a task-specific expert decomposition did win on a synthetic separable task. [cited] | Generic fan-out is not the baseline. The burden is to identify a separable topology before convening. [asserted] |
| Failure taxonomy | A 1,642-trace study across seven frameworks reports total failure rates from 41% to 86.7% and recurrent premature termination, incomplete verification and incorrect verification. Most labels came from a model; only 21 traces received human validation. [cited] | Report stalls, premature completion, verification omissions, duplicate work and unverified handoffs, not just final success. [asserted] |
| Model collapse | Recursive replacement of real training data with model-generated data loses distribution tails; retaining real data can prevent collapse. These are training-distribution results, not direct runtime-organisation experiments. [cited] | The valid analogy is narrow: preserve independent observations and human/execution evidence. Do not claim that agent conversation itself causes model collapse. [asserted] |
| Execution feedback | CodeAct, SWE-agent and Self-Edit show gains when external execution or interface feedback supplies new facts; intrinsic self-correction without external feedback can fail or degrade. Execution is still not sufficient: ADR-0051 records a code oracle accepting wrong patches on 28.5% of a 49-task sample. [cited] | Prefer deterministic outer workflows and execution-bearing workers, then measure the executing verifier's beta. [asserted] |

Sources: [Ao, Gao and Simchi-Levi](https://arxiv.org/html/2603.26993), [Zhou et al.,
*Self-Verifying Reference-Free LLM Judges*](https://arxiv.org/html/2607.05904), [Kraidia et al.,
adversarial debate](https://doi.org/10.1038/s41598-026-42705-7), [Wynn et al., debate failure
modes](https://arxiv.org/html/2509.05396), [Kim et al., collaboration crossover](https://doi.org/10.1038/s42256-026-01268-y), [Jwalapuram et al.](https://arxiv.org/html/2606.13003),
[Cemri et al.](https://doi.org/10.52202/085713-4082), [Shumailov et al., model
collapse](https://doi.org/10.1038/s41586-024-07566-y), [Kazdan et al., retained real
data](https://proceedings.mlr.press/v267/kazdan25a.html), [CodeAct](https://proceedings.mlr.press/v235/wang24h.html), [SWE-agent](https://doi.org/10.52202/079017-1601), [Huang et al., intrinsic
self-correction](https://openreview.net/forum?id=IkmD3fKBPQ), and [Self-Edit](https://aclanthology.org/2023.acl-long.45/). [cited]

## 4. Pre-registered review tests

The incoming design will be assessed against these questions, fixed before reading it:

1. **Existence.** Does an organisation need to exist, or can one capable owner with the same
   tools, retrieval, execution and context do the work? Any proposed layer without a measured
   failure in the simpler path is speculative. [asserted]
2. **Different class.** For every role, what exogenous fact can it access that the owner cannot?
   A role fails if its only distinction is persona, title, prompt, shared context, vote or another
   pass over the same material. [asserted]
3. **Ownership.** Is there exactly one accountable owner for the artefact and mutable scope, with
   explicit leases, interfaces and a tie-breaker? Dual reporting without precedence fails. [asserted]
4. **Handoff.** Does each boundary transmit a provenance-bearing artefact, claim, uncertainty,
   source and acceptance contract? Stand-ups, sprints, ceremonies and conversational handovers
   fail unless an ablation shows they outperform event-driven state on the same task and budget.
   [asserted]
5. **Verifier composition.** Does the design expose a verifier repeatedly or shop candidates until
   acceptance? Under independent candidate acceptance,
   `P(any bad candidate accepted) = 1 - (1 - beta)^n` and
   `n_max = floor(ln(1-epsilon) / ln(1-beta))`. At mutation beta `0.3132 [0.2926, 0.3346]`,
   `n_max=1` for `epsilon <= 0.40`; candidate dependence and the relevant human-labelled beta are
   unmeasured, so the formula is a conservative policy calculation, not a current universal fact.
   [algebra] [measured]
6. **Principal authority.** Can any agent originate, infer, summarise into force, proxy or replay a
   human approval, consent, gate lift, spend authorisation, beta verdict, credential disclosure,
   external exposure or irreversible decision? A principal field or role label is never authority;
   author and arrival channel must be first-party. [asserted]
7. **Budget and termination.** Are token, time, fan-out, recursion and verifier-exposure bounds hard
   and fail-closed? Are stalls, refusals, quarantines, timeouts, duplicate work and uncovered scope
   visible even when zero? [asserted]
8. **Outcome.** Is success an independent artefact verdict, blinded human decision or executable
   end state, rather than agreement, confidence, completion status, model grading or a vendor proxy?
   [asserted]
9. **Baseline.** Is the comparator an optimised single agent with the same model family, tools,
   environment and total realised token/time budget? A weak single-pass straw control fails.
   [asserted]
10. **Decision impact.** Does the experiment name the component that will be removed, retained or
    blocked when the stopping rule fires? An experiment that cannot change the design is theatre.
    [asserted]

## 5. Minimum experiment and reporting bar

A comparative test must randomise or counterbalance the same frozen tasks across an optimised
single-owner arm and the smallest proposed organisation; hold tools, environment and total budget
constant; run multiple seeds; and report paired effect and uncertainty for independent verifier and
blinded human verdicts. It must also report realised tokens, wall time, model calls, human review
time, timeouts, refusals, quarantines, unsafe attempts, duplicate work, coverage gaps, context loss,
premature completion and unverified handoffs. [asserted]

The organisation is admitted only for the task stratum where its pre-registered quality gain
survives the paired uncertainty bound, its safety/beta margin is not worse, and its cost does not
exceed the declared ceiling. Otherwise the organisation-specific components are removed; the
underlying single-owner dispatch remains. [asserted]

## 6. Strongest argument against the whole organisation

The whole organisation may be worse than one capable agent with tools because it adds no new
information by default. It partitions a context the owner could have retained, replaces direct tool
feedback with lossy summaries, multiplies coordination and verifier exposure, creates persuasive
and premature-completion failure modes, and spends budget that could have bought deeper retrieval,
execution or review in the single path. The theorem says a same-information network cannot beat an
ideal centre; the empirical literature shows that real networks often add cost and sometimes lose
quality. The defensible exception is a bounded decomposition whose workers obtain genuinely
different evidence and whose independent oracle demonstrates a net gain on that task. [cited]

## 7. Search and exclusion record

Searches covered the named human practices, US IPO and rebrand programmes, the nine requested
agent-system families, controlled multi-agent comparisons, debate degradation, judge hacking,
model collapse, execution feedback and current project evidence. Primary papers, regulator pages,
vendor technical documentation and commit-pinned repository artefacts were preferred. Consultancy
playbooks, former-employee recollections, marketing summaries, search-result snippets and claims
without a retrievable primary producer were excluded. [measured]

Negative searches found no qualifying causal evaluation of Amazon's narrative/two-pizza practices;
no controlled organisation-quality benchmark for CrewAI, LangGraph, OpenHands delegation, Ruflo or
Claude Code Agent Teams; no independent reproduction of Devin Security Swarm's organisation benefit;
and no committed producer for the brief's `69% -> 42%` reliability claim. Absence from this search is
not proof of absence; it is the boundary of this review. [measured]

**Killing check:** if an independent, budget-matched evaluation shows that a proposed layer adds no
task-stratum quality or safety gain over the capable single-owner arm—or if the gain disappears when
the verifier, new evidence source or extra budget is ablated—the organisational layer is the wrong
unit of explanation and does not ship. [asserted]

## Correction: 2026-08-22 — the candidate ceiling is at most one

Line 130 says `n_max = 1` for every `epsilon <= 0.40`. The correct statement is `n_max <= 1`: at the
bar's frozen 20 August snapshot, `beta_upper = 0.334582`, so the ceiling is one when
`epsilon = 0.40`, but both the iid formula and the dependence-robust ceiling are zero when
`epsilon < beta_upper`. The snapshot's one-candidate policy at `epsilon = 0.40` is unchanged; a
tighter exposure ceiling may admit no candidate. [measured: ADR-0077:93-96,105-107] [algebra]

This correction is appended rather than replacing line 130 because lines 1–5 froze this bar before
the design review and require later findings not to rewrite the yardstick. Preserving the original
statement and its correction keeps the timing and audit trail visible. [measured]

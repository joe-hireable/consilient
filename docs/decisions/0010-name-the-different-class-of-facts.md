# 0010. Every multi-agent structure must name its different class of facts

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground (a theorem, plus published measurements)
- **Executable model:** none — the constraint is a theorem, not a parameter.

## Context

Q7. The project's original scope included real-time inter-agent communication, model
battling, debate, and a governance layer of CEO/CTO/COO agents. All of these assume that
more agents conferring produces better answers.

## Decision

**No multi-agent structure ships unless it names the different class of facts it
introduces.** This is `CONSILIENCE.md` clause 2 as an engineering rule, and it is a hard
gate, not a heuristic.

Applying it:

| Structure | Different class of facts | Verdict |
|---|---|---|
| Critic tier | **Runs the tests** — observes execution output absent from the worker's context | Consilient |
| Parallel worktrees | Different repository states | Consilient |
| Discovery agents on separate sources | Different primary sources | Consilient |
| Independent verification of a lead | Re-derives from primary evidence | Consilient |
| Escalation to a frontier model | A fresh draw from a different model | Consilient *(weakly — see below)* |
| Debate / model battling | None | **Echo — cut** |
| Planner → implementer handoff | None | **Echo — cut** |
| Governance layer of role-played executives | None | **Echo — cut** |

**The pattern: structures that touch the world are consilient; structures that only talk are
echo.**

## Evidence

- `[cited]` Ao, Gao & Simchi-Levi, *On the Reliability Limits of LLM-Based Multi-Agent
  Planning* (arXiv:2603.26993, MIT). Without new exogenous signals, any delegated acyclic
  network is decision-theoretically dominated by a centralised Bayes decision maker
  observing the same information. Under proper scoring rules the gap is an expected
  posterior divergence — conditional mutual information under log loss.
- `[cited]` Same paper, measured: gpt-4.1-mini on a controlled four-way task went 90.7%
  (one stage) → 41.2% (two) → 43.5% (three) → **22.5% (five), below the 25% chance
  baseline**. Interface form mattered: structured posterior relay lost 2.8 points per stage,
  prose relay 8.5.
- `[cited]` Tran & Kiela (arXiv:2604.02460): single agents match or beat multi-agent at
  matched thinking-token budgets; Data Processing Inequality argument. Predicts MAS becomes
  competitive precisely when single-agent context utilisation degrades — **which is the
  justification for parallel worktrees and against debate.**
- `[cited]` Kim et al., *Nature Machine Intelligence* 2026: 260 configurations, compute
  matched; capability-saturation threshold predicts the sign of the multi-agent effect on
  SWE-bench Verified and Terminal-Bench in 94% of validation configs. MAS overheads
  1.6–6.2× tokens at matched performance.
- `[cited]` *The Illusion of Multi-Agent Advantage* (arXiv:2606.13003): audit of six
  automatic MAS-design frameworks found architectural bloat and functional collapse back to
  a single agent.
- `[measured]` Joe's own `CODEBASE_ASSESSMENT.md` pipeline already satisfies this rule and
  works: 12 discovery agents on separate sources → independent verification of all 197 leads
  → 1 fabrication caught → fabrication audit, 0 failures in 50 sampled citations.

## Evidence against

- The theorem assumes an acyclic delegated network with a fixed information set. Real agent
  systems have loops and can acquire information mid-run; the mapping is not exact.
- **Escalation passes on a technicality.** A fresh sample from a different model is new
  information in the statistical sense, but not new *evidence about the world*. The
  guarantee here is weaker than for the critic tier and this ADR does not resolve it.
- Rejecting debate outright forgoes any benefit in domains without an oracle. Coding has
  one, so the cost is bounded — but the rule as stated would misfire if the harness were
  ever pointed at open-ended work.

## Consequences

**Positive.** Cuts a large amount of speculative architecture on principled grounds. Makes
the multi-agent surface small enough for one maintainer: orchestrator, workers, critic.

**Negative.** Forgoes any real gain from deliberation. Makes the product look less
impressive than competitors that advertise swarms.

**Neutral but load-bearing.** Every future feature proposal now has a gate to pass, which
will feel obstructive and is the point.

## Enforcement

- Check: each agent role definition declares an `evidence_class`. A structure whose
  participants all declare the same class fails validation at configuration load, not at
  runtime. Same commit as the orchestrator (I1).
- Check: a test asserts no two participants in any convened structure share an
  `evidence_class`.

## What would overturn this

- A structure demonstrably beating a single agent at matched token budget on this project's
  own evaluation set, while sharing evidence classes. That would falsify the applicability
  of the theorem here and this ADR should be superseded, not patched.

## Publication candidate?

No — the theorem is someone else's. An *applied* write-up of the evidence-class gate as an
engineering mechanism could bundle into the β paper.

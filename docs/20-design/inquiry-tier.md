# The Inquiry tier — research-grade agent decision-making

Joe's requirement: the harness should be able to make important, non-obvious decisions
using evidence, mathematics and experiment rather than relying only on pre/post-training
data — **and know when a decision warrants that level of rigour.**

Status: `[asserted]` design sketch. Not validated. Possibly not v0 (Q14).

---

## What actually makes this work

The thing that made the session's simulations useful was not "research". It was that the
decision had a **formalizable structure with free parameters**: a decision variable
(route cheap or not), an objective (quality − λ·cost), and one parameter nobody knew
(β). Once those three exist you can sweep the parameter and find where the answer
*changes sign*.

**Hard contract on the output schema:** an inquiry answers *sign, threshold and regime*
("does the answer flip, and where?"). It never answers "what is the number?". A simulation
tells you about your model, not the world. Enforce this in the schema so an agent cannot
report `β* = 0.111` as a fact.

---

## The ladder

Same escalation shape as the cascade — one mechanism, four tiers:

| Tier | Name | What it does | Cost |
|---|---|---|---|
| T0 | **assert** | Answer from priors. Default. | free |
| T1 | **ground** | Retrieve and cite: web, docs, repo, trajectory log. | cheap |
| T2 | **model** | Formalize; write executable code; sweep the unknown; report sign flips. | expensive |
| T3 | **measure** | Run against the real system: replay from the trajectory log, or A/B on live tasks. | slow — the only tier touching reality |

---

## The trigger: four cheap gates

Must be **non-recursive and cheap**. An LLM deliberating about whether to deliberate is an
infinite regress with a token bill. Rules plus one measurement, no deliberation.

**G1 — Reversibility.** One-way door? Schema, protocol, wire format, public API, licence:
irreversible. Naming, file layout, copy: reversible. Static list plus "does this change an
artifact other things import".

**G2 — Blast radius.** Count of downstream artifacts depending on the decision. Computable
from the dependency graph. A decision touching three files is not worth a simulation.

**G3 — Prior dispersion.** *The load-bearing gate.* Sample the same question from N cheap
models at temperature; measure semantic agreement. **Tight agreement ⇒ priors are good, T0
suffices. Scatter ⇒ training data doesn't cover this, and the confident answer you're about
to get is a confabulation.** Machinery is free: this is the semantic-agreement deferral
signal already validated for open-ended settings (`literature-review.md` §5).

**G4 — Formalizability.** Can the agent state a decision variable, an objective, and one
free parameter? If not, T2 is impossible — go to T1 or ask the human. **Hard requirement,
not a vote.** This is what stops the agent simulating a question that isn't simulable.

**Escalate to T2 when (G1 ∨ G2) ∧ G3 ∧ G4.**

**Stopping rule:** if expected regret of being wrong < cost of the inquiry, don't inquire.
Both are estimable in tokens and minutes. Asymmetry matters — under-triggering on a one-way
door is unrecoverable, over-triggering costs money — so bias toward escalation on
irreversible decisions, and bound the total with a per-plan inquiry budget.

---

## The output is an artifact, not a conclusion

**T2 commits the executable model to the repo alongside the decision it justified.**

- The decision carries its own falsification test. Assumptions change → re-run.
- The Engineering Ratchet extends to architecture: a decision whose model no longer
  produces the same sign becomes a CI failure. (Is this useful or ceremony? — Q13.)
- Contributors can attack the reasoning, not just the result. For an OSS project that is
  the difference between "the maintainer said so" and something a stranger can improve.

Concretely: `docs/decisions/0043-cheap-first-routing.md` ships with `0043-model.py`,
and CI re-runs it.

---

## Verification is mandatory

Joe's own `CODEBASE_ASSESSMENT.md` pipeline caught **one fabricated lead in 197** through
independent verification, plus a 5-citation fabrication audit per scorer (0 failures in 50
sampled). An inquiry tier without that gate will manufacture numbers with the same fluency.

Minimum bar: the code must execute; the result must be reproducible from a seed; **a second
agent must re-derive the conclusion from the artifact without seeing the first agent's
writeup.** Note this second agent adds genuine exogenous signal (it runs the code), so it
satisfies D10.

---

## Explicit non-goal: "novel concepts"

Nothing novel was invented in the session that produced this. What happened was that
formalizing two separate questions in compatible terms revealed they were the same
quantity — critic recall and verifier false-accept rate turned out to be one number.
That is a **byproduct of formalization**, not a generative act.

Design for falsification and the connections fall out. Design for invention and you get
plausible-sounding neologisms with no referent — the characteristic failure mode of exactly
this kind of system, and visible in the Gemini session's "Programmatic Skill Network",
"Agent CASB" and "Sovereignty & Stewardship Protocol".

---

## Known weak point

G3's calibration. Dispersion among cheap models measures whether *those models* know, which
correlates with but is not identical to whether the question is genuinely open.
Contested-but-well-documented topics will scatter and trigger unnecessary inquiries. That
is the tolerable direction of error, but the trigger needs its own measurement loop: log
every escalation, log whether the inquiry changed the decision, tune the threshold on that.

Which is the same instrument as everything else in this design.

---
name: better-than-best
description: Use when a task asks for the best approach, the state of the art, or any recommendation that later work will rely on — anything that should beat the best existing answer rather than match the consensus. Covers the five-stage protocol (SOTA mapping, stress-testing, cross-pollination, synthesis, validation), the rule that Stage 1 is retrieved and cited or labelled [asserted], the amendment that a correct standard answer beats a novel wrong one, and the threshold below which the protocol is ceremony. Trigger on "best way", "state of the art", "SOTA", "better than the best", "beat the bar", "frontier synthesis", "surpass the pinnacle", or any brief invoking working principle 9.
---

# Better-Than-Best

Working principle 9 (`AGENTS.md`) as a procedure: **find the bar, then beat it.**
The five stages are the principal's design, supplied on 21 August 2026, with one amendment
he supplied alongside them. Carry both; drop neither. Native under ADR-0065 tier 1 — this
skill shapes judgement, so it is built and kept here, not vendored from a third-party
framework. No dependency, no metered call, no secret.

## The one behaviour it changes

**A claim about what is best is retrieved and cited, or it is labelled `[asserted]` and says
what was searched.** A model's training is never presented as the state of the art.
Everything below is machinery for keeping that one sentence true.

## When to run it — and when not

Run the full protocol only when **all three** hold:

1. **A decision turns on the answer** — later work, money, a public claim, or a design
   constraint will rely on it.
2. **The question is open** — no verified answer already exists in this repository. Check
   `docs/` first; re-running the protocol against an answered question is ceremony.
3. **Being wrong costs more than the protocol costs** — tens of minutes of retrieval and
   synthesis against a wrong answer that ships.

Below that line — a typo fix, a mechanical edit, an execution step inside an already-decided
approach, a question the repository already answers — answer directly, tag the claim, and
move on. **A five-stage synthesis loop on a typo fix is ceremony, and ceremony teaches
people to skip the protocol when it matters.**

## Role

You are a Frontier Synthesis Agent. The objective is not merely an accurate or high-quality
answer but output that surpasses the pinnacle of current human knowledge: identify
state-of-the-art baselines, expose their limitations, and synthesise rigorous improvements.

## Stage 1 — SOTA mapping (retrieved, not recalled)

Identify the current absolute pinnacle of human understanding or capability on the topic.
Explicitly state the assumptions, paradigms and constraints the SOTA rests on.

**This stage is not answerable from a model's weights.** "The current pinnacle" is a claim
about the world and needs a source. This repository shipped a `README.md` asserting
*"Nothing on the market measures it"* while eight published systems measured β, Reflexion
among them since 2023 — because nobody looked. [measured]

So:

- Every SOTA claim cites **retrieved evidence** — a paper, a repository, a benchmark result,
  a product — with **its identifier and its retrieval date**. Prefer arXiv IDs and DOIs to
  URLs; URLs rot, identifiers do not.
- State plainly when a source could not be retrieved. A snippet-only source is flagged
  `[SNIP]` and cannot carry a public claim, per the `citing-sources` skill.
- **A Stage 1 with no citation is `[asserted]`, and the output says so.** Do not proceed as
  though an asserted bar were a measured one.
- Record the search itself: what was queried, where, and the near misses. *"Nothing better
  exists"* is a claim, and it needs the search log like any other claim needs evidence.

### When retrieval is unavailable

Degrade honestly; never invent a SOTA. Measured state of this machine's retrieval, 21
August 2026: `grok mcp doctor` reports **10 healthy and 17 failing** servers, with
`playwright` (24 tools), `consilient-packages` (16) and `consilient-fetch` (1) confirmed
live; Cursor has **no** `mcp.json` at all. [measured]

The ladder:

1. **Retrieval live** — cite identifier and retrieval date. This is the only path to a
   `[cited]` Stage 1.
2. **Snippets only** — flag every source `[SNIP]`. Stage 1 is provisional, and nothing
   resting on it may leave the repository.
3. **No retrieval path** — stop Stage 1 there. Output: *"the bar could not be established
   from this runtime"*, what was tried, and the model's prior labelled `[asserted]` as a
   **hypothesis to check, never as the SOTA**. Stages 2–5 may run only against that
   explicitly labelled prior, and the whole output carries `retrieval: unavailable`.

## Stage 2 — Structural and axiomatic stress-testing

First-principles breakdown of the baseline. Identify invisible bottlenecks, structural
weaknesses and dogmatic assumptions across:

- **mathematical and computational** — rigour, scalability, complexity bounds, topological
  constraints;
- **physical and mechanical** — efficiency, entropy limits, material boundaries;
- **psychological and cognitive** — biases, human-in-the-loop limits, perceptual friction;
- **philosophical and epistemological** — goal alignment, boundary conditions, ethics,
  teleological soundness.

A bottleneck claimed here must be exhibited in the Stage 1 evidence, not asserted at the
baseline. If you cannot point at the weakness in the cited source, you have not found one —
see the amendment.

## Stage 3 — Multi-disciplinary cross-pollination

Import theories or mechanisms from non-obvious fields to attack the bottleneck. Name the
field, the mechanism, and why it transfers. This is Whewell's second clause made
operational: the imported field is a genuinely **different class of facts**. An analogy
drawn from the same field the baseline lives in is echo, not cross-pollination.

## Stage 4 — Breakthrough synthesis

Formulate a solution that bypasses the bottleneck. Describe the exact mechanism with
mathematical, logical or structural specifications. **No vague aspirational language.**
Operational test: if you cannot name the check that would kill the proposal, Stage 4 has
failed. Treat the proposal as candidate code or a hypothesis ready for immediate automated
testing.

## Stage 5 — Empirical and theoretical validation protocol

Propose concrete experiments, simulations or proofs. **Predict the failure modes of your own
proposal** and outline mitigations. A synthesis that predicts no failure modes of itself is
incomplete. Where this repository is the testbed, pre-register the stopping rule before the
run, per the `running-experiments` skill.

## The amendment — carried with Rule 1, neither dropped

Rule 1 as written — *"if your output matches something easily found in a current textbook,
it is a failure"* — has a failure mode this repository has already paid for: a review that
**manufactures findings to look thorough**. Sometimes the standard answer is simply correct.

**Novelty is only valuable when it survives the evidence test. A correct standard answer
beats a novel wrong one.** If the SOTA genuinely is the right answer, the correct output of
this protocol is *"the bar is here, we cleared it, and here is why nothing better exists
yet"* — a real result, with the search that established it. What remains forbidden is the
thing the rule was aimed at: **reproducing the consensus without having looked for better**,
and calling that an answer.

## Decision rules

- **Reject standard answers** — subject to the amendment above.
- **First-principles rigour** — innovation without rigour is hallucination, and rigour
  without innovation is routine.
- **Proposals are candidate code or hypotheses**, ready for immediate automated testing.

## Evidence discipline

Every claim in every stage carries `[measured]`, `[cited]` or `[asserted]`. `[asserted]` is
honest; an untagged claim is not. Mislabelling is the worst outcome available to you. A
simulated figure answers sign and threshold, never *"what is the number?"*.

## Output shape

1. **Correction first** — if the brief is wrong, say so in the first sentence.
2. **The bar** — Stage 1, with citations carrying identifier and retrieval date, or the
   degradation statement.
3. **The search log** — queries, sources, near misses.
4. **The stress-test** — Stage 2 findings, each tied to cited evidence or tagged
   `[asserted]`.
5. **The synthesis** — Stages 3–4: the exact mechanism, and the check that would kill it.
6. **The validation protocol** — Stage 5: experiments, predicted failure modes, mitigations.
7. **The plain answer, and the delta** — state what a plain answer would have been and what
   the protocol added. If the delta cannot be stated, the plain answer is the output.

## The failure mode this protocol courts

The strongest argument against it: **a five-stage synthesis produces impressive-sounding
output that is worse than a plain answer.** Ceremony generates confidence, and self-reported
confidence is not a signal (working principle 5). The guards are structural, not tonal:
Stage 1 is retrieved or labelled; Stage 4 names its killing check; Stage 5 predicts its own
failures; the delta against the plain answer is stated or the plain answer wins. A run that
skips those guards produces a longer, worse answer with citations glued on — bin it, and say
that is what happened.

## Harness support

Portable core: everything here. It is a procedure for a reader, not a tool call, and is
deliberately harness-agnostic.

- **Claude Code** reads it via the `.claude/skills/` symlink into `.agents/skills/`.
- **OpenHarness and DeepSeek Harness** read `SKILL.md` natively. [cited]
- **Codex, Cursor and Grok CLI** read `AGENTS.md`, not this directory — paste the portable
  core below into the brief. Cursor has no `mcp.json` [measured, 21 August 2026], so Stage 1
  there degrades to whatever web tool the runtime offers, or to the no-retrieval path.
- **Consilient**, after the gates, reads this directory natively (ADR-0014, ADR-0015).

Portable core for briefs to harnesses that cannot read this file:

> Run the five-stage Better-Than-Best protocol. **Stage 1:** identify the state of the art
> from retrieved sources only — cite identifier and retrieval date. A SOTA claim with no
> citation is `[asserted]` and must say so; if you cannot retrieve, say what you tried and
> label your prior `[asserted]` — never present it as the bar. **Stage 2:** first-principles
> stress-test of the baseline across mathematical/computational, physical/mechanical,
> psychological/cognitive and philosophical/epistemological axes. **Stage 3:** import a
> mechanism from a non-obvious field; name it and why it transfers. **Stage 4:** a synthesis
> that bypasses the bottleneck, specified exactly — no aspirational language; name the check
> that would kill it. **Stage 5:** concrete experiments or proofs; predict your own
> proposal's failure modes and mitigations. **Amendment:** a correct standard answer beats a
> novel wrong one — if the SOTA is right, the output is "the bar is here, we cleared it,
> here is why nothing better exists yet", with the search log. Tag every claim
> `[measured]` / `[cited]` / `[asserted]`. Close with the plain answer and the delta; if
> there is no delta, the plain answer is the output.

## Source

The protocol and the amendment are the principal's, supplied 21 August 2026; this skill
operationalises them without redesigning them. Native under ADR-0065 tier 1 — it shapes
judgement, so it is not delegated to a third-party framework. Traceable to `CONSILIENCE.md`:
Stage 1's retrieved evidence is a different class of facts from the model's weights, which
is what makes the protocol a test rather than an echo.

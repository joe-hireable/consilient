# Ways to contribute

Code is the smallest part of this. **The majority of the work is research, experimentation,
evaluation and benchmarking** — and those contributions are worth more here than a pull
request against the orchestrator.

Everything below follows one rule from `CONSILIENCE.md`: a contribution is valuable in
proportion to the **new class of facts** it brings. A second opinion on something already
settled is echo. A measurement nobody has taken is consilience.

---

## Research and evidence

**Promote a source.** `docs/10-research/bibliography.md` flags most entries `[SNIP]` —
snippet-only, unread. Fetch one, read it, correct anything we got wrong, promote the flag.
**This is the single most useful low-effort contribution available** and several of our
claims currently depend on unread sources.

**Falsify something.** Every ADR has a *What would overturn this* section. Overturning one is
a better contribution than confirming ten.

**Prior-art checks.** "Someone already built this, MIT-licensed" has been the correct answer
three times. Finding the fourth saves months.

## Experiments and benchmarks

`docs/10-research/experiment-register.md` holds fifteen entries with preconditions,
measurements and stopping rules. Several are `READY` and need no harness at all.

**Measure β on your repository.** The single most valuable dataset this project could
accumulate is verifier false-accept rates across many real codebases of differing
verification quality. We have one low-β repo and a warning that it flatters the thesis. **We
need weakly-verified repos more than well-verified ones.**

**Run an experiment and report a negative result.** Null results are scarce and clear the
publication bar as readily as positive ones. If EXP-14 shows meetings are ceremony, that
finding is worth more than the feature.

**Reproduce a simulation.** `docs/10-research/experiments/` is runnable. Re-run with
different assumptions — particularly non-logistic competence curves, which is the remaining
exposure in ADR-0002's closed form.

## Report outcomes — the low-touch contribution that feeds the instrument

A contributor class for users who opt in to **reporting on task outcomes** — not rating
responses (response rating does not exist in this product, deliberately: see
`../20-design/feedback-signals.md`). At most three questions, at task close only,
skippable with no consequence: was the pre-stated goal achieved; if not, what was
missing; optionally, was there a better approach in hindsight. Everything else — cost,
turns, escalations, whether the outcome survived — is derived from the trajectory log
and repository, never asked.

This is a real contribution, not a courtesy: your answers are exactly the human-verdict
labels the β instrument is short of, and ADR-0002 shows those labels are the scarcest
input in the system. Contributors are credited equally with code contributors — release
notes and the contributors file, opt-in to naming — and per ADR-0024 the recognition is
social only: no perks, no unlocked features, no tiers, and nothing about declining ever
changes what the software does. Consent is per purpose, never bundled, and by default
nothing leaves your machine.

## Prompting, context and agent design

Report what actually worked, with the trajectory log to back it. The field is full of
confident advice and thin on measurement. A context-engineering strategy with before/after
token counts and quality on a fixed task set is a real contribution.

## Legal, and it is genuinely needed

`docs/legal/README.md` is a brief for a solicitor with eleven open questions. Contributions
welcome on:

- **Contributor agreements** — is clickwrap sufficient for formation under English law, or
  should the CLA be executed as a deed? Consumer-status and unfair-terms risk under the CRA
  2015. Enforceability across jurisdictions.
- **Model and skill licensing** — gated open-weight licences, acceptable-use terms that are
  not OSI-open, and whether pointing at third-party weights makes a project a distributor.
- **EU AI Act** — whether a local-first orchestrator carries GPAI obligations. Currently
  unassessed (`0022`).
- **Trademark** — clearance on "Consilience" across UK/EU/US, still outstanding.
- **The disclosure standard** in `0022` — "prevention of imminent loss of life or severe
  destruction" needs legal drafting, not engineering drafting.

Nothing here is legal advice and nothing contributed becomes legal advice. It is expertise
that makes the eventual professional review cheaper and better.

## Roles that would help and are usually forgotten

- **Statisticians and decision scientists.** ADR-0002's β* closed form rests on a Rasch/1PL
  assumption. ADR-0012 concerns dependence between check classes. ADR-0021 applies decision
  hygiene to human-agent disagreement. All would benefit from someone who does this properly.
- **Security researchers.** Skill supply chain (`0016`), sandbox tiering, prompt injection
  through synthesised tools (`0018`). A registry install runs package-manager commands on
  behalf of a manifest nobody read.
- **Technical writers.** A project whose credibility rests on honest evidence tagging lives
  or dies on whether its documentation is readable and precise.
- **Accessibility.** ADR-0007 chose CLI-only partly *because* TUIs have poor accessibility.
  Someone should check that reasoning holds.
- **People with weakly-tested repositories.** Genuinely — the thesis needs high-β cases and
  we have none.
- **Sceptics.** ADR-0019 asks what was systematically missed because one model with one
  framing produced the initial material. That question cannot be answered by anyone who was
  in the room.

## What is not wanted

- Features with no falsifiable claim attached (`AGENTS.md`).
- Multi-agent structures that cannot name their different class of facts (`0010`).
- Invented terminology. If a concept needs a new name to sound important, it probably is not
  a concept.
- Benchmark scores as a goal in themselves (`0013`).

## How to contribute

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for DCO and the contributor agreement position.
Research and experimental contributions follow the same evidence-tagging discipline as
everything else: `[measured]` / `[simulated]` / `[cited]` / `[algebra]` / `[asserted]`, and
`[asserted]` is honest.

# 0060. Call Consilient a command post, not a meta-harness

- **Status:** **ACCEPTED 21 August 2026.** Public descriptor **superseded by [0061](0061-the-descriptor-is-agent-command-post.md)** (*Agent Command Post*). Child = harness, meta-harness retired, and product = Consilient still stand.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the instruction to choose and adopt; the operator sentence "don't ask ChatGPT, ask Consilient"). Grok (the choice among his list, recorded here).
- **Amends category language in:** [`0001`](0001-build-a-meta-harness-not-a-harness.md) (the *meta-harness* label only; the "sit above existing agents" decision stands). Does **not** supersede [`0038`](0038-rename-the-project-consilient.md).
- **Inquiry tier reached:** T1 ground — three independent naming arms, live product collisions, this repository's own lexical inventory.
- **Executable model:** none — a naming convention. Gate G4 is not satisfied.

## Context

"Harness" now names the child correctly: Claude Code, Cursor, Codex, Grok. Hugging Face, Claude's glossary, and CSO's 2026 security write-up all use it that way. `[cited]` The parent was being called a *meta-harness*. That prefix does not pick a sense, and Stanford/MIT already occupy **Meta-Harness** as a different object (search over harness *code*, arXiv:2603.28052). `[cited]`

Joe's operator sentence, 21 August 2026: you do not ask a model; you ask Consilient, and it sends harnesses — to explore, to check, and to come back. Verification-only labels ("verification desk") undersell inquiry. Super/hyper/giga prefixes on *harness* repeat the meta- mistake. "Agent Command Centre" is OpenAI's phrase for the Codex *app* (February 2026) and Collibra/Netskope/Salesforce's phrase for a governance dashboard. `[cited]`

Three families wrote naming reports without reading each other (`.harness/dispatch/naming-plain.md`, `naming-field.md`, `naming-repo.md`). This ADR is the choice, not an average of those reports.

## Decision

**The category word for Consilient is *command post*.**

| Seat | Word | Example |
|---|---|---|
| Product | **Consilient** | the thing you install |
| Concept | **consilience** | Whewell's test; `CONSILIENCE.md` |
| Child runtime | **harness** | Claude Code, Cursor, Codex, Grok |
| Parent category | **command post** | Consilient, relative to those harnesses |
| Local data | **`.harness/`** | unchanged; renaming the directory is not this decision |

Shop sentence: **Don't ask ChatGPT. Ask Consilient. It sends harnesses.**

Operator-facing prose (README, AGENTS.md, getting-started, the operating skill) uses *command post* for the parent and *harness* for the child. Historical ADRs keep the words they were written with. Identifiers, the `.harness/` directory, and `HARNESSES` in code do not change.

## The debate (Joe's list)

Each candidate was scored on four tests: (1) does it sit *above* a harness, not replace it; (2) can a non-specialist say it; (3) is it already spent on a different product; (4) does it smuggle echo (agents agreeing) or empty grandeur.

| Candidate | Verdict | Why |
|---|---|---|
| **hub** | reject | GitHub, Azure, every "AI hub". A switchboard. No test, no inquiry. |
| **nucleus** | reject | Biology / atomic. Sounds important. Does not dispatch. |
| **command post** | **take** | Small-unit HQ: you ask it, it sends units. Less SaaS-occupied than "command centre". British. Matches the operator sentence. |
| **control center** | reject | Collibra, Netskope, ServiceNow. American spelling. Governance dashboard, not a test of truth. |
| **mainframe** | reject | IBM, one machine, wrong era. The opposite of many harnesses. |
| **engine room** | reject | **Wrong layer.** Engine room is where the engines (harnesses) live. Consilient is the bridge. |
| **crucible** | reject for category | Honest about trial-by-fire and experiment. Literary. No shop sentence. Keep as a metaphor in research prose if needed. |
| **nexus** | reject | Sonatype, Nexus Mods, every architecture slide. Means "connection", which is echo-adjacent. |
| **agent orchestration kernel** | reject | Three jargon words. Gemini-session invented vocabulary. Kernel is an OS. |
| **hypervisor** | reject for category; keep as internal analogy | Exact computer image (guests = harnesses). VMware owns it. A games publisher will blank. Allowed in architecture notes, not in the README first paragraph. |
| **gateway** | reject | API / payments. Consilient refuses and tests; it is not a pass-through. |
| **matrix** | reject | The film, Matrix protocol, ADR-0020's RACI *schema*. Collaboration-shaped. |
| **engine** | reject | Search engine, game engine, "AI engine". Empty. Wrong layer (engines are models). |
| superagent / hyperagent / gigaharness / meta-harness | already rejected | Prefix on the child word, or a live mark / Meta's DGM-H. |

**Why not "desk" or "rig".** Two earlier arms recommended those. Joe rejected desk as QC-only. Rig collides with test equipment. Command post is the item on *his* list that matches the dispatch sentence without being OpenAI's "command center for agents".

## Evidence

- `[measured]` This checkout: `harness` has four live referents (product shorthand, category, child, `.harness/` path). 1,548 substring hits in `docs/`+`src/`. `naming-repo.md`.
- `[measured]` Two families, no shared transcript, both offered *desk*; Joe refused the QC-only reading.
- `[cited]` OpenAI Codex app described as a "command center for agents" (Feb 2026). Collibra *AI Command Center*; Netskope *AI Command Center*; Salesforce Command Center (now Agentforce Observability); ServiceNow AI Control Tower as "centralized command center".
- `[cited]` Meta HyperAgents / DGM-H (arXiv:2603.19461); Superagent Technologies USPTO 98439646; H2O "AI SUPER AGENT"; Stanford/MIT Meta-Harness (arXiv:2603.28052).
- `[cited]` Hugging Face May 2026: "If you're not the model, you're the harness." Macedo arXiv:2606.10106: orchestrator ≠ agent harness.
- `[asserted]` "Command post" is sayable in a wargames / publishing shop in a way "hypervisor" and "orchestration kernel" are not.
- `[asserted]` Consilience is not a squad agreeing. EXP-16 cut convened meetings. The command post *sends* harnesses; it does not chair them.

## Evidence against

- **Military.** A command post is C2. Some readers will hear war, not inquiry. Taken anyway because the operator sentence is send-units, and the milder "command centre" is already a product category.
- **Does not encode β or different-class.** Neither does "harness". The product name Consilient still carries the test. The category word has to be sayable first.
- **Sounds like a dashboard.** ADR-0007/0053 already refuse a review SPA. A reader may expect a glowing wall of agent cards (the Reddit "I built a command center" genre). Mitigation: the shop sentence names *sending harnesses*, and the interface remains `python scripts/dispatch.py`.
- **Joe listed thirteen options and asked an orchestrator to pick.** That is a preference question he could have answered. The pick is recorded as his instruction to choose, not as a measurement that "command post" wins a comprehension test. No such test was run. `[asserted]`
- **What was searched:** the three naming-arm files; USPTO/Justia hits for Superagent; Meta HyperAgents; OpenAI/Collibra/Netskope/Salesforce/ServiceNow "command center"; this repository's `harness` inventory. Not a full trademark clearance. Not a street interview.

## Consequences

**Positive.** Parent and child are different words. "Meta-harness" stops being the first sentence a new reader hits. The operator sentence can go on the README.

**Negative.** Historical ADRs still say meta-harness. Two vocabularies will coexist. `.harness/` looks like we did not mean it. Renaming that directory is a later, mechanical decision and is **not** authorised here.

**Neutral but load-bearing.** New operator-facing prose uses command post. Child CLIs remain harnesses. The product remains Consilient. Architecture notes may still say hypervisor as an analogy, never as the category.

## Enforcement

Operator-facing entry points must not reintroduce the retired category label.

- Check: `tests/test_category_language.py` — `AGENTS.md` must not contain `meta-harness`;
  `README.md`'s opening ("What this is") must call Consilient a command post and must not
  contain `open-source meta-harness`. Citing Stanford/MIT Meta-Harness as prior art later
  in the file is allowed.
- Fails CI: yes (the invariants pytest job).
- Added in the same commit as the implementation: **yes**.

Historical files under `docs/decisions/` are exempt. They are the trail.

## What would overturn this

- A comprehension test on people who have never heard "harness" in which "command post" loses to another word on Joe's list by a margin that would change the README. None has been run.
- OpenAI, or a similarly large vendor, shipping a product actually named "Command Post" for this layer, the way they already used "command center for agents" for Codex.
- Joe picking a different word from the table in writing. That is a new ADR, not an edit.

## Publication candidate?

No. Category language for one product. The collision table might be useful to others stuck on "meta-harness"; it stays here until someone asks to publish it.

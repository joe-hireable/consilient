# 0061. The descriptor is Agent Command Post

- **Status:** **ACCEPTED 21 August 2026.** Joe, in writing: *"Agent Command Post i think is the descriptor."*
- **Date:** 2026-08-21
- **Deciders:** Joe Brown. The orchestrator had recommended dropping "Agent"; he kept it.
- **Supersedes:** the public category phrase in [`0060`](0060-call-consilient-a-command-post-not-a-meta-harness.md). 0060's other decisions stand and are restated here: child runtimes stay *harnesses*; Consilient is not one; "meta-harness" stays retired in operator-facing prose; the product name is still Consilient (ADR-0038).
- **Inquiry tier reached:** T1 ground — a preference the principal is the only valid decider for (ADR-0033).
- **Executable model:** none. Naming convention.

## Context

ADR-0060 chose *command post* from Joe's list and stripped *Agent* because that word names the child (the harness) and because OpenAI already called the Codex app a "command center for agents." `[cited]` Joe has now set the descriptor in writing as **Agent Command Post**.

The shop sentence is unchanged: don't ask ChatGPT; ask Consilient; it sends harnesses.

## Decision

**Operator-facing descriptor: Agent Command Post.**

| Seat | Word |
|---|---|
| Product | Consilient |
| Descriptor | **Agent Command Post** |
| Concept | consilience (`CONSILIENCE.md`) |
| Child runtime | harness |
| Local data | `.harness/` (not renamed) |

First sentence shape: *Consilient is an Agent Command Post. It sends harnesses.*

"Command post" remains acceptable as the short form once the descriptor has been given in full. "Agent Command Centre" is not used — Centre is the SaaS collision (Collibra, Netskope, OpenAI). Post is the word 0060 already chose.

## Evidence

- `[measured]` Joe's words, this conversation, 21 August 2026.
- `[cited]` The collisions that made the orchestrator recommend dropping Agent are unchanged: OpenAI "command center for agents"; Collibra/Netskope AI Command Center; harness = child in Hugging Face's glossary.
- `[asserted]` A descriptor is allowed to contain "agent" as the *domain* (this command post is for agent work) rather than as the *unit being sent*. That reading is a stretch. It is the principal's stretch.

## Evidence against

- **Agent names the child.** A reader can still hear "a command post that is itself an agent." That is the confusion 0060 existed to kill. Adopted anyway because Joe set the descriptor, and category language is his (AGENTS.md: naming is ask-first; he answered).
- **OpenAI's phrase is one noun away.** "Command center for agents" vs "Agent Command Post." Press will conflate them. Post vs Centre is the whole distinction and it is thin.
- **The orchestrator is the party that preferred the shorter form**, so this record is partly a reversal of its own recommendation. That is not independent evidence that the longer form is better.

## Consequences

**Positive.** The README can say what Joe actually wants said.

**Negative.** "Agent" is back in the first sentence. The four-way collision on *harness* is not joined by a fifth on *agent* only if every use of Agent Command Post is immediately followed by "it sends harnesses."

**Neutral.** Historical ADRs, including 0060, keep their wording. Identifiers do not change.

## Enforcement

- Check: `tests/test_category_language.py` — `AGENTS.md` and the README opening must contain `agent command post` (any case) and must not contain `meta-harness` as Consilient's category.
- Fails CI: yes.
- Same commit as the prose change: **yes**.

## What would overturn this

Joe writing a different descriptor. That is a new ADR.

## Publication candidate?

No.

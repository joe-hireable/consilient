# EXP-16 stopping rule 1 has fired: Arm B does not beat Arm A

**20 August 2026.** Joe delegated this — *"DECIDE AND UNBLOCK FOR ME"*. What follows is the
result, the substitution it rests on, and why the graders' own verdict says the opposite of the
data.

## What was actually done, and how it differs from the registration

**The stopping rule names Joe's judgement as ground truth.** It has not been obtained. Asking an
agent to grade the multi-agent structure is the echo failure `CONSILIENCE.md` exists to name, so
grading it myself was not available.

**Substituted:** the blind pack was graded independently by **two different model families**
— Cursor (Gemini) and Codex (GPT) — neither of which wrote any of the options, and neither of
which could see the other. **This answers a different question** than the registration asked:
*"do independent readers of a different lineage prefer this arrangement's outputs?"* rather than
*"does the maintainer?"*. The pack is intact and **Joe's grading supersedes this whenever he
wants it.** [asserted]

## The result

Twelve judgements — six decisions, two graders — mapped through the sealed key **after** both were
recorded.

| | best | worst |
|---|---|---|
| **Arm A — single agent, no communication layer** | **9** | **1** |
| Arm B — the ADR-0020 Owner meeting | 2 | 3 |
| Arm C — free-form group | 1 | **8** |

Both graders agreed on four of six decisions. **On all four agreements, the single agent won.**
On the three decisions both independently called *material*, Arm A took four of six best-calls,
Arm B one, Arm C one. [measured]

## The methodological finding, which is worth more than the result

**Both graders concluded the spread was noise. Both were right about what they could see, and
wrong about the world.**

Cursor: *"the substantive spread across the actual strategic choices is largely noise"*.
Codex: *"No letter earned its keep as a robust quality signal… the apparent spread looks like
noise rather than a stable quality difference."*

Their letter tallies were nearly flat — T 3 / M 2 / V 1 and T 3 / M 2 / V 1 — and flat reads as
noise. **But flat is exactly what a dominant arm produces**, because the labels were randomised
independently per decision so that each letter carries each arm exactly twice. An arm that won
every time would still show a flat *letter* tally.

**The randomisation that made the grading honest also made the graders' own summary statistic
uninformative.** The signal exists only after the key is applied, and the graders were correctly
forbidden the key. [measured]

That is a real trap for any blind protocol of this shape, and it belongs in the register:
**a blind grader must not be asked to report a tally over randomised labels, because that
statistic is designed to be flat. It must report per-item judgements and let the unblinding
compute the aggregate.** Both did supply per-item judgements, which is the only reason this is
recoverable.

## The rule, applied as written

> *"If Arm B does not beat Arm A at matched budget → meetings are ceremony; ADR-0020 and the
> authority matrix are cut."*

**Arm B did not beat Arm A.** It was best twice in twelve and worst three times, against Arm A's
nine and one — and it did so at **4.8× the tokens and 3.7× the wall-clock** already measured.
The structural evidence pointed the same way in the original run: the same substantive decisions
in four of six cases.

**The rule fires.** ADR-0020's convened-meeting machinery is cut.

## What is cut, and what is not

**Cut:** the convened meeting as a mechanism — Owner-plus-Evidence-agents assembling to produce a
decision. It costs several times a single agent and produces worse output on this evidence.

**Retained:** the **Owner / Evidence / Informed / Escalation matrix as a schema** for recording
who decided a thing and on what evidence. Nothing in this result argues against writing down
accountability; what failed is convening a meeting to manufacture it. The authority matrix is a
record format, and record formats were not on trial.

**Also retained**, because the original run measured them and they are not decision quality:
Arm B uniquely preserved dissent and enforced provenance-by-format. **Arm C's collapse — worst in
eight of twelve — is the strongest single number here**, and it is the arm that recorded no
dissent on any decision. That is a finding about *free-form group discussion*, not about
structure per se.

## Reversal

`git revert` of this commit and the ADR-0020 status change. The pack, the key and both grade sets
are committed, so the whole judgement can be re-derived or overturned by Joe's own grading without
re-running anything.

## What would overturn it

1. **Joe's blind grading disagreeing.** It is the registered oracle and this is not. One
   afternoon with the pack settles it.
2. **A different-family grader preferring Arm B** on a fresh decision set — two graders on six
   decisions is a small sample, and both are model families with their own priors about what good
   reasoning looks like.
3. **A case where the meeting's preserved dissent later proves decisive.** The graders scored
   decision quality at the moment of decision; dissent's value is that it survives to be useful
   later, which no snapshot grading can see. This is the strongest argument against the cut and
   it is not answered by this result.

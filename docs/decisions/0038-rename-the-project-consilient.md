# 0038. Rename the project Consilient — the predicate, not the phenomenon

- **Status:** ACCEPTED
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the decision; naming is reserved to him by `AGENTS.md`)
- **Supersedes:** [`0008`](0008-name-the-project-consilience.md), which stays as written
- **Inquiry tier reached:** T1 ground — availability checked, blast radius measured
- **Executable model:** none. No decision variable, no objective, no free parameter; Gate G4
  is not satisfied and a naming convention does not get a model.

## Context

Joe, 20 August 2026: *"I think we should rename the project the adjective — consilient and I
can get the domain name consilient.dev."*

ADR-0008 chose the noun on 19 August against a requirement that the name *illustrate the
concept* rather than describe a category. That requirement is unchanged and is still met. What
has changed is that a day of building revealed the noun and the adjective do different jobs, and
the project had already started using the adjective for the job the product actually does.

## Decision

**The product, repository, package and domain become `Consilient`. The concept remains
consilience, and `CONSILIENCE.md` keeps its name.**

| | before | after |
|---|---|---|
| product / domain | Consilience | **Consilient**, `consilient.dev` |
| public repository | `joe-hireable/consilience` | `joe-hireable/consilient` |
| private working repository | `consilience-work` | `consilient-work` |
| Python package | `src/consilience/` | `src/consilient/` |
| CLI | `consil` | `consil` — unchanged, correct for both |
| grounding document | `CONSILIENCE.md` | `CONSILIENCE.md` — **unchanged** |

## Evidence

- `[measured]` **The adjective was already the verdict word, before anyone proposed it as a
  name.** `CONSILIENCE.md`'s own table classifies every candidate structure as **Consilient**
  or **Echo**: a critic tier that runs the tests is consilient; a debate over shared context is
  echo. The repository contained **28 occurrences of "consilient"** at the time of the rename,
  all of them predicates. The product's entire job is to answer *"is this structure
  consilient?"* — so the name is the question the harness asks, not the phenomenon it hopes for.
  That is a stronger fit than ADR-0008 had, on ADR-0008's own criterion.
- `[asserted]` **The noun over-claims and the adjective does not.** "Consilience" names the
  jumping-together itself — a thing that either occurs or does not, and which this project has
  measured itself *failing* to achieve at least once, when a same-family control reproduced a
  finding and killed the claim. A product named after a phenomenon asserts the phenomenon.
  A product named after the predicate asserts only that it applies the test.
- `[measured]` **The blast radius is small and mostly prose.** 406 occurrences across 102
  tracked files; only 38 were identifier- or path-shaped and needed mechanical change. The CLI
  name `consil` was already an abbreviation of both.
- `[cited]` Joe reports `consilient.dev` is available. **Acquiring it is his action and his
  money; nothing here purchases anything.**

## Evidence against

- **This is the second naming decision in two days, on a one-way door.** ADR-0008 itself says
  naming is one-way "once packages are published and a repository is public", and the
  repository *is* public. The mitigation is weak but real: the public repository holds a single
  squashed commit, no package has been published to any registry — `packages/consilient/`
  is a reservation whose own description says *"nothing is published here yet"* — and GitHub
  redirects the old URL. **A third rename would not have these mitigations and should be
  refused.** [asserted]
- **The noun is the term of art and the adjective is not.** Whewell coined "consilience"; E. O.
  Wilson popularised it. Anyone who recognises the reference recognises the noun. Naming the
  product with the adjective trades a small amount of that recognition for a better description
  of function. [asserted] Reasonable people would decide this the other way.
- **Keeping `CONSILIENCE.md` under a different name from the product is a deliberate
  inconsistency** and will read as an oversight to anyone who does not read this ADR. It is
  kept because the file explains Whewell's noun, which is the thing the product is named after;
  renaming it would make the grounding document describe a word Whewell never used. [asserted]
- **Nothing was searched for prior art on the name "Consilient" beyond Joe's domain check.**
  ADR-0008 checked live registries; this decision inherits that check for the noun and has not
  repeated it for the adjective. Trademark and npm collisions are unexamined. [asserted]

## Consequences

**Positive.** The name states what the product does rather than what it hopes for, and matches
the vocabulary the repository already used. A shorter, available domain.

**Negative.** Every external reference to the old name is now a redirect, and the trail of two
naming ADRs in two days is itself a small signal about decision stability.

**Neutral but load-bearing — the append-only log keeps the old name, and that is correct.**
`.harness/log/*.jsonl` was deliberately excluded from the rename sweep. Those events said
"consilience" because that was the name when they were written; rewriting them would be exactly
the tampering the append-only record exists to prevent. **A rename that edits history is not a
rename, it is a forgery.** The same reasoning kept ADR-0008 unedited: a mechanical sweep changed
one line in it, and the change was reverted, because an ACCEPTED ADR records the decision as it
was made.

## Enforcement

- **Check, shipped in the same commit:** the `pre-push` hook that refuses pushes of this
  repository's history to the public mirror now matches **both** names. A hook matching only
  the old name would have silently stopped protecting the public repository at the moment of
  the rename — the failure it exists to prevent, arriving through a rename rather than a
  mistake. Verified by running it against all five URL forms: three public forms refused, both
  private forms permitted. [measured]
- Prose occurrences of the concept are **not** mechanically swept. "Consilience" is frequently
  the correct word in a sentence about the idea, and a global replace would have produced
  sentences claiming a jumping-together where the text meant the test.

## What would overturn this

A trademark or registry collision on "Consilient" that ADR-0008's registry check would have
caught for the noun and which nobody has run for the adjective. That check is owed and is
cheap; until it is done this decision rests on a domain lookup.

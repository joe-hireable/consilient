# How this gets believed — evidence, not claims

**Date:** 20 August 2026
**Status:** `[measured]` for every number quoted from this repository; `[asserted]` for the strategy,
which is judgement and should be read as such.
**Asked by Joe:** *"how we can prove that the harness is world changing? Demos? Publications? Eval
results? Must be done autonomously — transparently and truthfully. Things that will grasp the
attention of the world like OpenClaw did… Aim for more stars than deepseek harness."*

---

## The honest opening, because the alternative wastes the effort

**You cannot prove it is world-changing in advance, and claiming it is what makes people stop
listening.** Every AI project on GitHub says it is revolutionary. The claim is now negative
evidence: a README that opens with "revolutionary" is read as a signal that there is no result
behind it.

So the question is not *how do we say this is important*. It is: **what can we put in front of a
sceptical engineer that they cannot dismiss?**

Two things have historically worked, and they are different from each other:

1. **A result that changes what people believed was possible.** DeepSeek's attention did not come
   from marketing — it came from a number, with weights attached so anyone could check it. The
   result *was* the marketing.
2. **An experience that takes under a minute and does something surprising.** No signup, no
   configuration, no belief required.

This project can do both, and the two are not the same artefact.

## What this project has that nobody else does

Not the orchestration. Orchestration is crowded — `ruvnet/ruflo` alone has 68.5k stars, 100+ agents
and 210 MCP tools. Competing there is competing on features against a field that ships faster.

**What is genuinely unusual is that this project measures how often its own checks are wrong, and
publishes the answer even when it is bad.**

Today's own numbers, all `[measured]` and all uncomfortable:

| | |
|---|---|
| The product's own check suite | **β = 0.3132** [0.2926, 0.3346] — roughly one bad change in three passes everything |
| The research instruments that produce our figures | **β = 0.6825** [0.6700, 0.6948] — twice as permissive as the code they measure |
| Mutants inside functions where **nothing** is caught | **32.7%**, including the retro-verifier's own oracle |
| Gate conditions found unpassable by construction | **4 of 7** |
| Commits on the published branch authored by a test fixture | **51 of 156** |

**No competitor publishes anything like this, and that is the opportunity.** A project that
publishes its own bad numbers is making a claim that cannot be faked: you can only do it if you
measure, and you can only keep doing it if you are not embarrassed by what you find.

`ruflo` has quality gates that grade 1–100 and **discloses no false-accept rate for them.** [cited]
That is not a criticism of `ruflo` specifically — it is the norm. Being the exception is the
position.

## The wedge: a tool that is useful to someone who does not care about the harness

The meta-harness is the long game and it requires belief. **The β meter does not.**

> `npx consilient measure` — point it at any repository, wait two minutes, get back the rate at
> which that repository's own CI accepts a bad change. No account, no key, no data leaves the
> machine.

Why this specifically:

- **It answers a question every engineer already has** and none can currently answer: *how much does
  my CI actually catch?* Mutation testing has existed since 1978 and almost nobody runs it, because
  it is awkward to set up. Making it one command is the whole product.
- **It is measured on their repository, not ours.** No benchmark to dispute, no cherry-picked demo.
- **The number is shareable and slightly competitive.** *"My β is 0.41. What's yours?"* is a thing
  people post. That is not a growth hack; it is what happens when a number is personal and easy to get.
- **It requires no belief in anything else we claim**, which is precisely why it can carry the rest.
- EXP-47 ran **1,931 mutants in 104 seconds** [measured]. The performance is already there.

The harness is what you reach for *after* the number tells you your checks are worse than you
thought. **The tool creates the problem the harness solves, honestly, by measuring it.**

## What to build, in order

1. **`consilient measure`** — the single command above. Local, no telemetry, works offline.
   Everything else is downstream of this existing and being genuinely good.
2. **A public, automatically updated page showing this project's own numbers**, including the bad
   ones and the ones that got worse. Generated from the trajectory by the harness itself, so it
   cannot drift from reality without the drift being visible. This is the transparency claim made
   checkable rather than stated.
3. **The papers, submitted in the order the release plan already argues** — P2 first, because a
   catalogue of thirteen inert checks in a system built to prevent them is the most concrete thing
   here and needs no one to accept a thesis first.
4. **The self-development record.** Joe's instinct that *"using itself to develop itself is proof in
   itself"* is right, but only if the record is auditable. It is: the trajectory is append-only, the
   ADRs preserve reversals rather than deleting them, and the failures are committed alongside the
   successes. **Point at it; do not narrate it.**

## What not to do — each of these actively costs credibility

- **Do not claim a benchmark win.** This project has no benchmark result and manufacturing one is
  the fastest way to be dismissed by the people whose opinion matters.
- **Do not publish a demo video of agents "collaborating".** Everyone has one. They persuade nobody
  who has seen the others.
- **Do not chase stars directly.** Stars follow usefulness. `ruflo` has 68.5k of them and no measured
  error rate; the count is not the evidence. Aiming past DeepSeek is a fine ambition and a terrible
  metric — **it is exactly the kind of composite number ADR/V0-21 forbids inside the product, and the
  reasoning does not stop applying because it is about us.**
- **Do not describe unbuilt capability in the present tense.** The README already had its founding
  claim refuted by a paper nobody had read (Ratchet, arXiv:2605.22148v3). That is a survivable
  embarrassment once.
- **Do not hide the bad numbers to launch.** They are the product.

## The strongest single sentence available, and it is true today

> We measured how often our own checks accept bad work. It is about one time in three. Here is the
> instrument — run it on yours.

That is a result, an invitation and an admission at once. It cannot be said by anyone who has not
done the work, and it does not require the reader to believe anything we assert.

## Evidence against this whole plan

- **The wedge may not convert.** People may run `consilient measure`, learn their β, feel briefly
  bad, and never adopt a harness. The tool would then be a public service that builds no product.
  **That is the central risk and it is not mitigated by anything here.**
- **Mutation testing is forty-eight years old.** If ease of use were the only barrier, someone would
  have removed it. Possibly the honest reason nobody runs it is that the number does not change
  behaviour — and if so, this plan fails at its foundation. `mutmut`, `PIT` and `cosmic-ray` all
  exist and none is widely adopted. **That is evidence against, and it is strong.**
- **Publishing bad numbers may read as incompetence rather than rigour.** The audience that
  understands why it is a strength is smaller than the audience that does not.
- **"Autonomously" is doing a lot of work in the brief.** Nothing here is autonomous today. The
  measurement is, the publication is not, and pretending otherwise would breach the transparency the
  same sentence asks for.
- **There is no evidence anyone wants this.** Zero users, zero requests, no measured demand. Every
  claim above about what engineers would do is `[asserted]` and some of it is wishful.

## The falsifier

Ship `consilient measure`. If it is run on **1,000 distinct repositories and fewer than 1% go on to
use anything else in the project**, the wedge does not convert, and the strategy above is wrong
rather than early. That is measurable, it is cheap, and the number should be published whichever way
it goes — including if it is embarrassing, because that is the entire premise.

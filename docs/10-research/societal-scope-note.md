# The societal and macro sphere — a scope note

**Status:** scope note, 20 August 2026. Written to answer a single question and expected to
close it: can this project say anything about societal or macro-scale outcomes that is not
advocacy? [asserted] Nine primary sources were fetched and read at source for this note;
five further leads were seen only through an indexing API and are listed at the end so that
nobody re-imports them. [measured] Nothing in this file is a Consilience measurement.
[measured]

Companion to [`human-success-and-the-human-side-of-beta.md`](human-success-and-the-human-side-of-beta.md),
which covers the individual half of the same question and found it partly instrumentable.
This file covers the collective half and finds it is not. [asserted]

---

## Verdict

**The societal sphere is out of instrument range for this project, and the reason is
architectural rather than budgetary.** [asserted] The origin-alignment recommendation not to
put the societal sentence in `README.md` is upheld, and on stronger grounds than "one
sentence with no instrument behind it": the instrument is foreclosed by a decision this
project has already taken and should keep. [asserted]

Three things follow, and the third is the only one that costs anything.

1. There **is** measured work on the societal and macro effects of AI coding assistance. It
   is genuine, recent, and it points in two directions at once. It cannot be summarised into
   a project mission without misrepresenting it. [cited]
2. A solo-maintainer harness with telemetry off by default cannot measure any of it, and
   could not measure most of it even with telemetry on. [algebra]
3. There is exactly one collective contribution in range, it is not a measurement, and it
   must not be described as one: **publishing a β method and its measured intervals is a
   contribution to a public good; it is not evidence about society.** [asserted]

---

## 1. What was asked, and where it splits

The stated ambition is to work out how best to work with humans "for the maximal betterment
of humanity, on an individual level but also a collective societal and socio-cultural macro
level".

That sentence contains two different research programmes, and only one of them has a
sensor attached.

| Half | Unit of observation | Instrument status |
|---|---|---|
| Individual | one developer, one diff, one session | Partly instrumentable — six behavioural signals survive, six named outcomes do not. See the companion file. [cited] |
| Collective | a labour market, an ecosystem, a skill distribution, a profession | No instrument. This file. [asserted] |

The split is not about importance. It is about whether the harness ever touches the class of
facts in question. Under `CONSILIENCE.md` clause 1, an induction carries the provenance of the
facts it came from. A harness observes diffs, checks, and one maintainer. It does not observe
a labour market, and no amount of reasoning over diffs produces an induction about one.
[asserted]

---

## 2. Measured, modelled, advocacy — the six areas, sorted

House rule for this section: a figure is **measured** only if I fetched and read the source
that produced it; **modelled** if the number is the output of an assumption-driven projection
rather than an observation; **advocacy** if its function is to motivate rather than to
constrain. Verification flags follow `bibliography.md`: `[FULL]` fetched and read, `[ABS]`
abstract or landing page read at source.

### 2.1 Labour market and displacement — MEASURED, and contradictory

- **Brynjolfsson, Chandar & Chen**, *Canaries in the Coal Mine? Six Facts about the Recent
  Employment Effects of Artificial Intelligence* (Stanford Digital Economy Lab, revised 12
  August 2026). `[ABS]`, landing page read 2026-08-20. High-frequency ADP payroll data
  through June 2026. Workers aged 22–25 in AI-exposed occupations show employment **19% below
  expected levels** relative to less-exposed peers; experienced workers show no comparable
  gap; the divergence widens from August 2025; adjustment runs through **reduced hiring
  rather than increased separations**, and through employment rather than base compensation.
  [cited] The authors state there is **"no evidence of widespread, economy-wide job
  displacement"** and describe their own findings as **"early, descriptive indicators —
  canaries in the coal mine — rather than causal estimates"**. [cited]
- **Humlum & Vestergaard**, *Still Waters, Rapid Currents: Early Labor Market Transformation
  under Generative AI* (NBER WP 33777, May 2025, revised March 2026). `[ABS]`, landing page
  read 2026-08-20. Adoption surveys combined with Danish administrative records: adoption is
  widespread and workers report productivity gains, but earnings and hours are essentially
  unchanged, **ruling out effects larger than 2%** two years after ChatGPT's launch;
  transformation shows up as internal task reorganisation. [cited]

**What this pair licenses.** That the sign and magnitude of the labour-market effect depend on
the population, the outcome variable and the window — an entry-cohort hiring effect in US
payroll data coexists with a near-null on earnings and hours in Danish administrative data.
[cited] **What it forbids.** Any project sentence of the form "AI coding assistance
displaces / does not displace developers". Both halves of that sentence are currently
defensible from a read source, which is the definition of a claim not worth making.
[asserted]

### 2.2 Skill distribution and inequality — MEASURED, but not on developers

- **Brynjolfsson, Li & Raymond**, *Generative AI at Work* (arXiv:2304.11771). `[ABS]`,
  abstract read at source 2026-08-20. 5,172 customer-support agents: **+15% issues resolved
  per hour** on average, with substantial heterogeneity — **less experienced and lower-skilled
  workers improve both speed and quality, while the most experienced and highest-skilled see
  small gains in speed and small declines in quality.** [cited]

That is the compression result everyone cites for "AI narrows the skill gap". It was measured
on customer support, not on software engineering. The companion file already records the
coding-side heterogeneity (less experienced developers adopting more and gaining more in the
enterprise field experiments) and the opposite-signed result for veteran maintainers on their
own mature repositories. Transfer from support agents to developers is an **inference across
a population gap**, and this repository has already been burned once by exactly that move.
[asserted]

No source read for this note measures a *distributional* outcome — a Gini, a variance ratio,
a between-firm or between-country spread — for software work specifically. [measured]

### 2.3 Open-source ecosystem health — MEASURED once, cleanly, and it is the best result here

- **del Rio-Chanona, Laurentsyeva & Wachs**, *Are Large Language Models a Threat to Digital
  Public Goods? Evidence from Activity on Stack Overflow* (arXiv:2307.07367). `[ABS]`,
  abstract read at source 2026-08-20. Difference-in-differences against Russian and Chinese
  counterpart platforms (where ChatGPT access is limited) and against maths forums (where it
  is less capable): a **16% decrease in weekly posts on Stack Overflow**, increasing in
  magnitude over time, larger for the most widely used programming languages. Post voting
  scores are similar before and after, so **the loss is not concentrated in duplicate or
  low-quality content**. [cited]

This is the single cleanest collective-outcome measurement located: an identified design, a
named counterfactual, a public-goods outcome, and a control for the obvious alternative
explanation. It is also the one result in this note that a coding harness could plausibly
*worsen* — every question answered privately by an orchestrated agent is a question not asked
in public. [asserted]

### 2.4 Code-quality externalities at ecosystem scale — MEASURED

- **Agarwal, He & Vasilescu**, arXiv:2601.13597. `[FULL]`, already read in full and recorded
  in `bibliography.md`. Static-analysis warnings up **~18%** and cognitive complexity up
  **~39%**, persisting across the full six-month window in **both** agent-first and IDE-first
  groups, while velocity gains fade. [cited] Repository-month level, observational, with the
  authors flagging isolated significant pre-treatment coefficients that weaken parallel
  trends. [cited]
- **Meng et al.** harness survey §6.3, `[FULL]`, recorded in `bibliography.md`: **maintainer
  merge rates average 24.2 pp below SWE-bench automated grader scores for the same PRs.**
  [cited] This is ecosystem-scale false-accept evidence and it is the closest thing in the
  literature to β measured on somebody else's population.
- **Stenberg**, *Death by a thousand slops* (14 July 2025). `[FULL]`, fetched 2026-08-20.
  curl's bug bounty: **~20% of 2025 submissions AI slop**; roughly **two security reports per
  week**; only **~5% of submissions genuine** by early July 2025, a valid-rate materially
  down on previous years; a **seven-person** security team, **3–4 people per report** at
  **30 minutes to three hours each**; 81 genuine vulnerabilities and over **$90,000** paid
  since 2019. [cited]

The curl figures are a maintainer's own count on one project. They are primary and honest and
they are **not a sample of anything**. [asserted] Treat them as an existence proof of the
externality's mechanism, never as its magnitude.

### 2.5 Concentration of capability — NOT MEASURED, at least not reachable here

No instrument was located that measures concentration of AI coding capability — across
vendors, across firms, or across countries — in a form this project could read, replicate or
contribute to. [measured] Structured search for one returned nothing on topic. That is a
negative result about my search, not proof of absence, and it is the weakest paragraph in
this note. [asserted]

### 2.6 Validated instruments for collective outcomes — NONE FOUND in this domain

- **CHAOSS** (Community Health Analytics in Open Source Software, a Linux Foundation
  project). `[FULL]`, knowledge base read 2026-08-20. **89 metric articles and 17
  metric-model articles**, each metric framed as answering "one single question about the
  health of the community". [cited] **The page states no validation study, no reliability
  estimate and no psychometric validation of any metric.** [measured]

CHAOSS is the nearest thing the software world has to a collective-outcome instrument, and it
is a consensus-derived metric catalogue rather than a validated scale. The companion file
already rejects unvalidated self-report constructs as sensors for individual outcomes; the
same standard applied here disqualifies the entire collective catalogue as a *measurement*
instrument, while leaving it perfectly usable as a *description*. [asserted]

Validated collective-level constructs do exist elsewhere in social science — neighbourhood-
level, population-level, built on purpose-designed sampling frames of thousands of
respondents. That fact sharpens the negative rather than softening it: **the missing piece is
not the instrument, it is the sampling frame.** [asserted]

### 2.7 Advocacy — the category, named so it can be excluded

Not a source list, because the rule is not to import them. The category is: vendor impact
reports, "AI for good" position frameworks, and any percentage whose recoverable provenance
is a blog or marketing page summarising a paper. `AGENTS.md` and `bibliography.md` already
ban these as `[2ND]`. The relevant point for *this* file is that **the societal literature has
a far higher advocacy-to-measurement ratio than the individual literature**, because the
outcomes are slower, the counterfactuals are harder, and the audience is policy rather than
practice. [asserted] A project that wandered in here would be importing that ratio.

---

## 3. Why this is out of range — the argument, not the mood

A claim about a society is a claim about a **population**. Measuring one needs four things,
and failing any single one is sufficient to make the claim unmeasurable. [algebra]

| Precondition | What this project has |
|---|---|
| **A sampling frame** over the population the claim is about | One maintainer, plus whatever repositories voluntarily adopt an unreleased tool. n is 1 and the frame is self-selected. [measured] |
| **A counterfactual** for the population | None. There is no unassisted control society, and unlike the individual case there is not even a within-subject design available. [algebra] |
| **An observable at population scale** | Foreclosed by decision. **ADR-0024: "Default: nothing is transmitted. No phone-home, no version check, no crash report, no anonymous counters"**, with ADR-0022's test class asserting nothing leaves a local install. [measured] |
| **Latency shorter than the decision it informs** | Labour-market effects surface in payroll and administrative data on a multi-year lag; the strongest study here is still calling its own findings descriptive after three years. [cited] Architecture decisions here are made weekly. [asserted] |

All four fail independently. The third is the decisive one and it is worth being explicit
about: **the project cannot measure society because it has decided not to receive the data
that would let it, and that decision is correct.** [asserted] A societal-impact instrument
and ADR-0024 cannot both exist. If anyone later proposes the instrument, they are proposing
to reverse ADR-0024, and should be made to say so in those words.

### The Whewell trace

`AGENTS.md` forbids adding structure that cannot be traced to `CONSILIENCE.md`. Run the trace
on a hypothetical societal-outcome module:

- **Clause 1, provenance.** The harness never observes the facts. Any societal induction it
  emitted would carry provenance it did not have — the exact laundering the repository bans.
- **Clause 2, a different class of facts.** A societal claim assembled from the harness's own
  trajectory log is not a different class; it is the same class, restated at a scale it does
  not support. That is echo with a bigger noun. [asserted]
- **Clause 3, a test with an error rate.** There is no test here whose error rate could be
  measured, because there is no oracle. Coding is v0 precisely because it is the only domain
  with a cheap automated oracle; society is the limiting case of a domain with none.

The trace fails at all three clauses. That is as clean a "does not belong" as this repository
can produce. [asserted]

---

## 4. What *is* in range

Three things, honestly labelled.

**4.1 A public-goods contribution, which is not a measurement.** β is a method for measuring
how often automated checks accept a bad artefact. Published openly — method, thresholds,
intervals, insufficient-data verdicts — it lets *other* maintainers measure their own
verifiers. The Meng/METR 24.2 pp gap and the curl figures say there is a real externality for
such a method to bite on. [cited] But the project measures its own β and no one else's. The
defensible sentence is **"contributes an instrument others can use"**, never **"reduces
ecosystem-wide false acceptance"**. The second sentence has no measurement behind it and
never will at this scale. [asserted]

**4.2 An externality this project can at least not make worse.** The Stack Overflow result
means every question answered privately is a question not asked in public. [cited] A
meta-harness is, structurally, a private-answering machine. This does not generate a feature;
it generates a standing caution against any design that quietly substitutes for public
exchange, and a reason to keep the trajectory record local and the artefacts in git where a
human can read them. [asserted]

**4.3 A negative that is worth writing down.** "We looked for a collective instrument, and
here is why there isn't one" is a publishable-quality answer to a real question, and it is the
kind of result `publications/README.md` already treats as valuable. It costs nothing further
to maintain. [asserted]

### Explicitly out of range, and to be refused on sight

A societal-impact score. A dashboard aggregating usage into a claim about inequality. A
"developers helped" counter. Any figure derived from adoption numbers. Each requires
telemetry ADR-0024 forbids, and each would be a point estimate presented where the honest
answer is an interval crossing zero. [asserted]

---

## 5. No invariant is proposed, and why

The rule is that any invariant ships with its check. The lazy and correct move here is to
propose none: **I3 already forbids a claim in `docs/` without an evidence tag**, and the
recommendation of this note is that the societal sentence is not written at all. A check
guarding a sentence nobody is writing is speculative scaffolding. [asserted]

If the maintainer overrules and the sentence goes in, the minimum enforceable version is one
grep in the existing tag checker: any line in `README.md` containing a population-scope term
(*society, societal, humanity, inequality, the industry, workers, ecosystem-wide*) must carry
`[asserted]` or a registered EXP id, and may never carry `[measured]` or `[cited]`. That is
the whole check, and it is the only one this area can support. [asserted]

---

## 6. What cuts against this conclusion

Reported with the same prominence as the argument, per house rule.

- **The Stack Overflow result is a genuine counterexample to "collective outcomes are
  unmeasurable".** It is measured, identified, controlled and about a public good. [cited] It
  demonstrates that the *field* can measure collective outcomes — with platform-scale data
  and a natural experiment. The negative in this note is about **this project's** reach, not
  about the possibility of the measurement. Someone with GitHub-scale data could do the
  ecosystem β study; this maintainer cannot. That distinction is the whole load-bearing edge
  of the verdict, and if it blurs the verdict is wrong.
- **The concentration-of-capability paragraph is a failed search, not a finding.** §2.5 is
  the weakest claim here. One better search, or one specialist who knows the literature,
  could overturn it in an afternoon.
- **ADR-0024 is PROPOSED, not accepted.** The decisive precondition failure in §3 rests on a
  decision that has not been ratified. If ADR-0024 changed — consented, per-purpose,
  inspectable contribution of trajectory data at scale — the third precondition would move
  from *foreclosed* to *merely very hard*, and this note would need rewriting rather than
  amending. I judge that unlikely and undesirable, but it is a decision, not a law of nature.
- **Two of the strongest sources here were read only at abstract or landing-page level.**
  Brynjolfsson/Chandar/Chen and Humlum/Vestergaard are both `[ABS]`. The 19% and the 2% are
  quoted from summaries, not from the papers' own tables. Neither should be repeated in a
  publication until promoted to `[FULL]`.
- **"Out of instrument range" is not "unimportant", and the note should not be read as
  licence to stop thinking about it.** The curl figures describe a real seven-person team
  losing real hours to machine-generated noise. [cited] That harm is downstream of exactly
  the thing this project measures. Declining to *claim* a societal effect is not the same as
  declining to care about one. [asserted]
- **A negative is the cheapest thing to write and the easiest to be lazy about.** I searched
  six areas and found instruments in four of them; the conclusion that none is reachable
  rests on the four-precondition argument in §3, which is algebra over this project's own
  constraints. If that argument has a hole, the verdict goes with it.

---

## 7. Disposition

- **README:** no change. The origin-alignment recommendation stands, now with a reason
  attached. [asserted]
- **Experiment register:** nothing registered. There is no experiment here with a stopping
  rule that a solo maintainer could fire. Registering one would be data collection with a
  hopeful name, which this register exists to prevent. [asserted]
- **Review trigger for this note — the stopping rule for the negative itself.** Reopen if
  **either** (a) ten or more independent repositories, not the maintainer's, publish β
  intervals produced by this method, giving a frame with n > 1 — at which point the
  ecosystem-β question becomes an experiment rather than an aspiration; **or** (b) ADR-0024 is
  superseded in a direction that permits consented population-scale contribution. Absent
  both, this file is closed and should be cited rather than re-litigated. [asserted]

---

## Leads seen but not read — do not cite

Located through an indexing API only. Under `bibliography.md`'s rule these are `[2ND]` and
may not appear in an ADR's `[cited]` line, a publication, or any public claim until fetched
and read. They are named here **only** so that the next reader does not spend the search
budget rediscovering them. [measured]

- Dell'Acqua et al., *Navigating the Jagged Technological Frontier* — SSRN 4573321 (2023);
  published *Organization Science* (2026), doi:10.1287/orsc.2025.21838. Field experiment,
  knowledge workers. Relevant to §2.2.
- *The Unequal Adoption of ChatGPT Exacerbates Existing Inequalities Among Workers* — PNAS
  (2024), doi:10.1073/pnas.2414972121. Danish worker survey. The most directly on-topic
  inequality lead; the PNAS page returned 403 on fetch.
- *The Consequences of Generative AI for Online Knowledge Communities* — *Scientific Reports*
  (2024), doi:10.1038/s41598-024-61221-0. Adjacent to §2.3; the Nature page redirected to an
  identity provider and was not fetched.
- *Generative Artificial Intelligence, Human Creativity, and Art* — *PNAS Nexus* (2024),
  doi:10.1093/pnasnexus/pgae052. Reports concentration and novelty effects in a creative
  ecosystem; a possible template for an ecosystem-level design.
- The neighbourhood collective-efficacy literature (Sampson, Raudenbush & Earls, *Science*,
  1997) as the canonical validated collective-level instrument. Cited nowhere in this note's
  argument; listed because it is the right comparison if anyone tries to build one.

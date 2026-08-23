# What Consilient is for — the principal's statement of the product, 22 August 2026

This is source material, not analysis. Joe Brown's words are quoted verbatim; everything outside a
quote is annotation, and every annotation that makes a claim about the code carries its evidence tag.
Recorded because three decisions were filed under his name on this project that he never made, and he
caught the third himself. **Where this document and a paraphrase disagree, this document is wrong too
— go to the transcript.**

## The product

> "I want the end consilient product to be like Finch and the Machine in Person of Interest. All he
> has to do is talk to it over time and it learns but can do almost unimaginably impressive things off
> the bat (we will build it that way)
>
> instead of surveillence it's more like general chief of staff that spawns custom intelligence,
> builds custom capabilities on the fly that it never loses, learns to be smarter than any human in
> anything by performing deep study which then bakes directly into training and memory rather than
> just memory. Memory system must be perfect. Like having the worlds smartest person in every possible
> specialism available instantaneously at any time but all of them have eidetic and photograohic
> memories and perfect recall and they can process information and data at speeds of billions of times
> faster than collective human intelligence."

## The organisation that delivers it

> "Each swarm must have its own orchestrator/manager and specialist agents all doing specific things.
> Just like how an organisation works to achieve large collective goals. Like an IPO, a rebrand, etc.
> Instead of hiring people - the harnesses plugged into consilient are like the full-time management
> employees, they're always on and always progressing their areas.
>
> The user is the Founder/CEO and is purely strategic and not hands on and for driving company
> culture, direction, vision and unblocking for the organisation/agents, providing feedback and
> guidance and steering at macro company, industry and societal level.
>
> The harnesses are like your senior managers, CTO, CMO, Growth Director, Head of Data Science, etc.
> Then those harnesses dispatch smart models of their own as managers, like a Product Manager or a
> Scrum Master type. Then individual specialist agents are like contractors brought in but instead of
> that you just create the talent in a specific, hyperfocused agent with dynamic tools, skills,
> context, instructions, personality etc."

> "the best organisations operate as above and that is the bar but agentic organisations can do things
> even humans cant so must be better and more effective than even top human teams. Top expertise or
> specialist requirements can be designed and built in minutes or seconds instead of going through
> hiring process and paying 7 figure salaries or extortionate contractor rates. Agents can do multiple
> things all at the same time like humans cant. Agents are smarter."

## How to decide when several answers are defensible

> "Sometimes especially in tech there is multiple different "best" ways. We dint want in this
> situation to get stuck in a loop when deciding on one and continuing to experiment and keep an open
> mind would be better than burning tokens on a decision that as long as one of n best options is
> selected. Like if it's a bad decision i.e. building a house with wet sand then obviously that's a
> massive problem but as long as it's built with bricks or metal or obsidian or hardened and treated
> thick wood blablabla then you should pick one and start building with the best fit you can find."

**This is a satisficing rule with a floor, and the floor is the whole of it.** Wet sand is refused.
Brick, steel, obsidian and treated timber are all acceptable, and deliberating between them past the
point of picking one is waste. The design question it poses is not "which is best" but **"what
distinguishes wet sand from brick here"** — that boundary is the thing worth spending tokens on.

Recorded as working principle 11 in `AGENTS.md`, whose enforcement fails a `PROVISIONAL` decision that
names no experiment. [measured]

## Living specs

> "All of this needs to be baked into the SPECS. They need to be living specs and living plans that
> are continuously and autonomously updated and executed by our orchestrators and swarms."

**This is an architectural requirement, not a documentation preference.** A spec that is a document
drifts from the code; a spec that is executable state does not. The repository already has one worked
example: `docs/40-spec/requirements.md` is generated from `requirements-source.json` by
`scripts/build_requirements.py`, and `--check` fails the build if the document has drifted from its
source. [measured] Whatever the design does about living specs should start from that shape rather
than inventing another.

## Where the product statement meets the code, honestly

The specification above is the target. These are the measured distances from it as of 22 August 2026,
recorded so the spec plans against the real starting point rather than an assumed one.

**"Memory system must be perfect."** It is not, and the gaps are specific:

- **92 of 379 trajectory lines were never written through `append()`**, so `validate()` never ran on
  them. Historical and permanent; the ratchet holds the count so it cannot grow. [measured]
- **`append()` does not fsync.** A power cut loses the tail of the evidence log. [measured]
- **`recall.py` is bounded and drops events**, printing `N event(s) omitted to fit character limit`.
  It quotes verbatim and refuses to summarise, because EXP-45 measured condensation dropping ~59% —
  but bounded retrieval over perfect storage is not the same thing as perfect recall, and the design
  must say which one it is promising. [measured]

**"Builds custom capabilities on the fly that it never loses."** Capability creation exists in
fragments — `.agents/skills/` holds ten skills, `consilient_connectors` holds adopted capability, and
`capabilities.py` exists in the product tree. **Nothing yet makes a capability persist as a first-class
object that survives the session that created it.** [measured]

**"Deep study which then bakes directly into training and memory rather than just memory."** This is
the sharpest requirement in the statement and the furthest from the code. Training is authorised —
ADR-0064 admits GCP, Fireworks, Cerebras, Together and Groq as providers, and ADR-0066 covers the
principal's private training corpus — but **no study-to-training path exists.** [measured] It is also
where the strongest counter-evidence sits: the surveyed self-improvement literature found **every
offline phase producing only self-consistent text degraded**, while every one with an execution
boundary gained. A "deep study" phase that reads and reflects is the degrading kind. One that
*executes* — runs the tests, drives the browser, checks the citation against the source — is the other.
**The spec must say which it is building, and the answer cannot be "both".**

**"Almost unimaginably impressive things off the bat."** Today `consil` is observe-only and
`routing_orchestration_enabled` is `false` because four of seven gate conditions fail. [measured] The
distance is not a criticism of the vision; it is the size of the work.

## Scale: how big the organisation gets, and when

> "Yes and the bigger the task the more it needs. I.e. building a website needs branding team,
> development team, motion design team, qa testing and automation team etc etc. for better than best
> standard. Writing a single doc does not. For everything we need to be defining what better than best
> looks like. Consilient might advise the user it'll take a while but then comes back whenever it's
> done with the better than best finished product.
>
> For small tasks we always need to understand what best and better than best looks like before
> delivering but smaller squads are appropriate in many cases."

**This names a layer ADR-0067 does not cover, and the two are compatible once the layer is named.**

ADR-0067 governs **one scoped decision**: the smallest evidence-grounded squad, default one, a member
added only when it brings a truth-relevant anchor nobody else has. That rule is about *evidence*.

The statement above is about **decomposition**: a website is not one decision, it is branding,
development, motion, QA and more — dozens of scoped decisions, each of which may still be best served
by a squad of one. **So a large deliverable gets a large organisation not because each decision needs
more agents, but because it contains more decisions.** Conflating the two would produce committees on
trivial questions, which is the failure ADR-0067 exists to prevent.

Three obligations follow, and none is currently built:

1. **Decompose before composing.** The size of the organisation is a property of the *work
   breakdown*, not of the task's apparent importance. What is missing is the step that turns one
   request into a stream map.
2. **Define better-than-best before delivering — for everything, including small tasks.** Working
   principle 9 already requires naming the incumbent before building; this extends it to *every*
   task rather than to capability claims. A one-page document still has a bar; it is just cheaper to
   find. **The success criterion is written before the work, not after.**
3. **Deliver asynchronously and honestly.** *"Consilient might advise the user it'll take a while but
   then comes back whenever it's done."* This makes duration a first-class part of the contract with
   the principal: an estimate up front, and a finished artefact rather than a progress report. It also
   means a long-running organisation must survive restarts, which the loop runtime addresses and
   nothing yet ties to a user-visible commitment. [measured: no such commitment exists in the code]

## Authority: everyone gets their own Machine, and they are its Finch

> "We are giving everyone their own machine that they can be the Finch to and decide what it can and
> can't do just by talking to it. But ensuring the users word is always final even when the machine
> disagrees. Must neber disobey a user but can push back amd argue productively and politely and
> constructively. Definitrly less constrained than more by default. only bound by law"

**Five obligations, and the first resolves an apparent conflict rather than creating one.**

**1. The constraints bind agents, never the principal.** Every refusal this project has produced was
aimed at an agent: the commit gate refusing an unattributed stage, the publication gate refusing a
push that would have overwritten contributor work, V0-18 refusing an agent authoring a verdict in the
principal's name. **None of them refused the principal.** [measured, 21–22 Aug] So "the user's word is
final" and the invariant set are the same policy seen from two sides — V0-18 exists to stop an agent
laundering a decision into the user's name, which protects the user's authority rather than limiting
it. The design must keep that asymmetry explicit, because an invariant that starts refusing the
principal has become the wrong thing.

**2. Configuration is conversational.** *"decide what it can and can't do just by talking to it."* The
permission model is not a settings file the user must find. It is something they say. That is a
harder problem than a settings file and it is the requirement.

**3. Push back once, then comply fully.** The contract is: state the concern plainly, with evidence,
once. If the user reaffirms, **proceed with the whole request** and do not re-litigate, hedge, or
comply while signalling disapproval. Repeated objection after a decision is disobedience wearing
politeness.

**4. Open by default.** *"Definitely less constrained than more by default."* This is the reverse of
this repository's own posture, and the difference is deliberate: **Consilient's gates constrain
Consilient's development**, because the harness must earn the right to be depended upon. They are not
a template for what a user's instance may do. A user's Machine starts open.

**5. Bound by law.** This is the only stated limit, and it is the one that needs the most design.

## The problem in "only bound by law", stated plainly

An agent's judgement about legality **is a verifier, and verifiers have error rates.** That is this
project's entire subject. So:

- **Whose law?** Jurisdiction is a property of the user, the data, the servers and sometimes the
  recipient. A single global answer will be wrong somewhere.
- **What is the beta of a legality check?** Unknown, unmeasured, and it will be **high** — legal
  questions are exactly the kind where a confident-sounding wrong answer is easy to produce.
- **The asymmetry is severe.** A false refusal frustrates a user who is entitled to proceed. A false
  accept can expose them to real harm. Neither error is cheap, and they are not symmetric.

**The honest design follows from principle 11 rather than from caution**: refuse only what is clearly
unlawful, **escalate genuine uncertainty to the user rather than resolving it silently**, and never
use "this might be illegal" as cover for a preference the agent holds for other reasons. **An agent
dressing a disagreement as a legal constraint is disobedience with better paperwork**, and it is the
most likely way obligation 3 gets violated in practice. [asserted]

## The default is maximum autonomy

> "bound by law as minimum and user can configure and manipulate other boundaries but the default
> should be maximum authority and permissions and capability to the agent. maximum autonomy is what we
> are advocating for
>
> that way smarter people's and people that work harder machines are better."

**Law is the floor, not the ceiling.** Every other boundary is the user's to set, raise or remove, and
the shipped default sits at maximum authority, permission and capability. This is a deliberate
inversion of the industry norm, where products ship restrictive and grudgingly widen.

**The second sentence is the product thesis and it deserves stating plainly.** A Machine amplifies
what its Finch puts into it. Effort, judgement and accumulated instruction compound — which is why
capabilities must never be lost and memory must persist, since those are the mechanism by which
investment compounds rather than evaporating each session. The product does not level its users; it
rewards them.

**The honest corollary, which the design must carry:** amplification is symmetric. Maximum autonomy
applied to poor direction produces poor outcomes faster and at greater scale. That is not an argument
for restricting the default — the principal has decided, and the decision is coherent — but it is an
argument about **what makes maximum autonomy rational rather than reckless.**

**Autonomy is earned by measurement, and that is what beta is for.** A system that cannot say how
often its own checks wrongly accept a bad artefact has no basis on which to grant itself latitude; one
that can, has a quantitative reason to widen. This reframes this repository's own gates: with
`routing_orchestration_enabled: false` and four of seven conditions failing, Consilient is not being
cautious — **it has not yet earned the autonomy it advocates**, and says so rather than assuming it.
[measured]

So the two commitments compose rather than conflict:

- **Ship maximum autonomy by default**, because the user is the principal and their word is final.
- **Measure beta relentlessly**, because that measurement is the only honest argument that the
  autonomy is safe — for the user, and for anyone downstream of what their Machine does.

**A tension worth carrying rather than resolving prematurely.** The principal has also required that
this be *"accessible for anyone with average plus intelligence"*. If better machines accrue to
harder-working and more capable users, the gap between a well-taught Machine and a neglected one
widens with use. Both goals are stated and both are wanted; the design should make the *floor* high —
impressive from the first day, per the product statement — while leaving the ceiling unbounded.
Nothing here resolves that, and it should not be resolved by quietly dropping one of them. [asserted]

## Do not over-constrain, and do not create work

> "We have to consider that all the models have safety constraints baked in so we dont need to
> overconstrain here.
>
> It must not create work or friction but remove it. It must reduce user stress and overwhelm by
> handling everything for them and not overloading them with responsibilities or tasks to approve
> things unless absolutely essential"

**On over-constraining.** Every model this harness dispatches to — Claude, Codex, Cursor's own,
Grok — carries its own safety training and refusal behaviour. A second policy layer on top is mostly
redundant, and redundancy here is not free: it produces refusals the user cannot predict, cannot
appeal, and did not ask for. **Consilient's constraints should protect the record and the principal's
authority, not re-litigate model safety.** That is what the existing invariants already do: V0-18
protects authorship, the commit gate protects attribution, the leak gates protect the private corpora
and the user's own data. **None of them is a content policy, and none should become one.**

**On friction — this is a measurable product property, not a sentiment.** An approval request is a
transfer of work from the machine to the person. Every one has to justify itself.

**The escalation bar is "irreversible and consequential", never "the agent is uncertain."** Those are
different tests and conflating them is the failure. Working principle 11 already settles uncertainty:
decide at the best available estimate, name the experiment that would improve it, carry on.
**Escalating because you are unsure is a violation of principle 11 wearing the costume of caution.**

What genuinely reaches the principal: money leaving an account; a credential; anything published or
sent outside the machine; deleting or overwriting something unrecoverable; a decision only he can
author under V0-18; and a genuine preference no fact can settle. **Everything else is the machine's to
decide, with the reversal path recorded** — which is requirement R30, still unbuilt. [measured]

**Measured on this session, 21–22 August 2026.** The orchestrator escalated to the principal roughly
eight times. Five were legitimate: the publication push (one-way, and the orchestrator was blocked
from executing it), a ruling on ADR-0066, the two rules misattributed to him under V0-18, and the
reconciliation of public and local histories where the alternative would have destroyed merged
contributor work. **Three were not**: which subsystem to specify first, after he had already said to
decide; whether quarantined V0-18 lines should carry a correction event, where the orchestrator held a
view and asked anyway; and the CLI surface question, which ADR-0067 answered without him. [measured]

**The common failure in all three: escalating from uncertainty rather than from authority.** That
ratio — avoidable escalations over total — is the friction metric this product should hold itself to,
and it should ratchet downward like every other count in this repository. **A Machine that asks its
Finch to decide what it could have decided has added work, not removed it.** [asserted]

## The Machine is a consilience engine, and the number is the last step

> "Also with the machine it's not just giving a number. In real life AI terms it would have had to do
> thousands of things to get to that one number. That's more descriotive of the decision making
> protocol I have encouraged. It could understand phone calls, texts, cctv, etc etc to understand and
> correctly predict the social security number of a person in danger. Obviously the application of AI
> and ML and code here is very different, a lot more generak and within the bounds of the law which
> the Machine from Person of Interest definitely would not be. Although if it were legal it would be
> technically possible today."

**This correction is the most important thing recorded in this document, because it means the product
metaphor and the project's epistemology are the same thing rather than two ideas sitting next to each
other.** [asserted]

The Machine's output is a social security number. Its *method* is an induction from telephony
coinciding with an induction from video coinciding with an induction from text and from financial
movement. **That is Whewell, exactly**: an induction obtained from one class of facts coinciding with
an induction obtained from another different class, and the coincidence being the test of the truth.
The number is trustworthy **because** the classes differ. A Machine wired to a thousand telephone
lines and nothing else would produce a confident number and be wrong, and it would be wrong in the
specific way this project calls **echo**. [cited: Whewell 1840, via CONSILIENCE.md]

**So the decision-making protocol is fusion, not adjudication.** A conclusion is not reached by asking
several agents and counting agreement; it is reached by accumulating many small independent readings
until they converge. This does not contradict ADR-0067's default of one — **it says what the
justification for a large squad has to look like when one is warranted.** Thousands of small
inductions on a genuinely high-stakes question is the shape; seven role-labelled agents reading the
same diff is not. [asserted]

**The gap the analogy makes visible, which is the hardest unsolved problem here.** The Machine's
classes were genuinely exogenous: separate physical sensors observing the world independently. Agents
in a harness overwhelmingly share a corpus, a context and often a base model, so their readings are
correlated in a way CCTV and telephony are not. **The thing that made the Machine's fusion work is
precisely the thing hardest to obtain in an agent system.** Naming a different class is cheap; having
one is not. Every squad design in this repository must be measured against that, and the honest
sources of genuine exogeneity available here are few and should be enumerated rather than assumed:
executing the artefact, driving a real browser, checking a citation against its actual source,
reading a fresh corpus, a different model family, and a human verdict. [asserted]

**On law, which the principal drew himself and unprompted.** He named the Machine's surveillance as
outside the bounds of law and placed Consilient inside them, while noting the capability is
technically reachable today. That is consistent with the floor already recorded above: **law is the
minimum, the user configures everything above it, and the default above the floor is maximum
autonomy.** The distinction he drew is between *capability* and *permission*, and it is the right one.
[measured: his words, this document]

## Consilient improves itself, and the owner is the gate

> "So when all built according to specs and plans we should already have the best superintelligence
> product globally and autonomous experiments running to make what we have better and when
> experiments produce impactful results consilient can use swarms to update itself via my (the
> founder/moderator/owner of consilient) agents."

**Three claims, and they need separating because their evidence differs sharply.**

*That the built product would be the best globally* is `[asserted]` and cannot be otherwise until it
is measured against a named incumbent. Working principle 9 binds this: find the bar, then beat it,
and "nothing exists" is a claim requiring evidence — this repository shipped that claim once and it
was false. **The bar for the organisation was frozen externally on 22 August 2026 in
`agentic-organisation-bar-2026-08-22.md`; there is no equivalent frozen bar for the product as a
whole, and there should be.** [measured]

*That autonomous experiments run continuously* is **partially real**: `docs/10-research/experiment-register.md`
holds registered claims with pre-declared stopping rules, and experiments have run and produced
results, including ones that refused to report a figure. What does not exist is the loop's closing
half. [measured]

*That swarms update Consilient itself when a result is impactful* **does not exist in any form.**
Nothing reads an experiment result and turns it into a change to the harness. This is the recursive
half of the product and it is unspecified, so it has been dispatched as its own stream. [measured]

**The gate is the principal, and V0-18 already enforces it.** He describes the update path as running
"via my … agents" — the owner's agents, not the system acting on its own recognisance. Verdicts,
approvals, gate lifts and spend must be authored by him. **A self-improving system whose improvements
it also approves has no external check at all, and that is the one place in this design where the
maximum-autonomy default must not reach.** The reversibility test governs everything else; changing
the harness that measures whether changes are good is not reversible in the relevant sense, because
a bad change corrupts the instrument that would have detected it. [asserted]

## The output is unconstrained, which inverts Finch's safety architecture

> "You are right in that the OUTPUT of the machine is extensively constrained and here will be by
> design completely unconstrained.n"

**Finch's design was wide input and a pinhole output.** The Machine observed effectively everything
and was permitted to say nine digits. He could not constrain what it saw, so he constrained what it
could express, and **that narrowness was the whole of the safety architecture** — not a limitation
he tolerated but the mechanism he chose. [asserted]

**Consilient inverts both halves.** Its input is lawful and consented rather than total; its output
is anything — code, a document, a design, a campaign, an action. Four consequences follow, and they
are not all comfortable.

**1. Output narrowness is unavailable to us, so something else must carry that load.** The two
candidates already in this design are the **reversibility test** and the **append-only record**.
That makes them load-bearing rather than hygienic: an unconstrained output that is fully reversible
and fully attributable is safe in a way an irreversible one is not, *regardless of how wide the
aperture is*. This is the strongest available argument that the friction rule recorded above is
sound — **the answer to a wide output is not more approvals, it is better reversal and a complete
record.** [asserted]

**2. A nine-digit output is self-verifying by consequence.** Reality resolves it within days: the
person was in danger or they were not. **An unconstrained output has no single oracle.** This is
precisely why coding is v0 — it is the only domain with a cheap automated oracle, which is where β
can be measured at all. The Machine never needed a β because its output space was small enough for
the world to grade it. [measured: CONSILIENCE.md, AGENTS.md]

**3. This raises the evidence bar rather than lowering it, and that is the counter-intuitive part.**
With a nine-digit output the space of wrong answers is tiny and a wrong answer is quickly falsified.
With an unbounded output the space of **plausible-but-wrong artefacts is enormous**, and a verifier
that accepts a bad one may never be caught. **So fusion across genuinely different classes matters
more here than it did for the Machine, not less** — the Machine could afford thinner evidence
because its output could not hide. Ours can. [asserted]

**4. What separates this from Samaritan is not a capability limit.** The same fiction runs the
experiment: comparable capability, unconstrained output, no owner, direct action — and the result is
a tyrant. The difference here is **not** that Consilient is weaker. It is that the principal's word
is final, V0-18 makes his authority undelegable, and every action is recorded and attributable.
**Capability is not the safety property; ownership and provenance are.** That is consistent with the
maximum-autonomy default rather than in tension with it. [asserted]

**The honest risk, stated plainly.** Maximum autonomy, unconstrained output and an unmeasured β
compound. The first two are deliberate design choices and they are defensible. **The third is a gap,
and it is the one that should close** — `consil beta` holds one human rejection against a minimum of
thirty. The correct response is not to narrow the output or add approvals; it is to measure β so the
latitude is earned rather than assumed. [measured]

## The named incumbent is Hermes Agent

> "Hermes Agent is the best global bar at the moment but personally I think this is easy to beat and
> we can beat hermes with a few targeted agent swarms and our decision making protocols."

**Naming the incumbent is what working principle 9 requires**, and it converts "best superintelligence
product globally" from an unfalsifiable claim into a testable one. That alone makes this statement
load-bearing. [asserted]

**"Easy to beat" is a hypothesis, and it is currently unsupported.** This repository has already
shipped a novelty claim — that nothing comparable existed — which was **false**. A second flattering
answer would be worse than the first, so the teardown dispatched on 22 August was briefed to argue
the opposite case and to report plainly if Hermes is stronger than believed. [measured]

**What is already verifiable on this machine, and it complicates the strategy.** The superpowers
plugin ships a Hermes tool mapping at
`.../superpowers/6.3.0/skills/using-superpowers/references/hermes-tools.md`. It records that Hermes
exposes `delegate_task(goal, context, toolsets, role="leaf")`, a `todo` tool, a `hermes kanban` CLI
described as being for **multi-agent task boards**, a persistent global instruction file at
`~/.hermes/SOUL.md`, plus `web_search`, `web_extract`, `terminal` and a skills toolset. [cited:
retrievable local file]

**If that reading holds, Hermes already has hierarchical agent delegation and cross-agent task
management** — two of the three capabilities this project intends to win on. The `role="leaf"`
parameter implies a role hierarchy and therefore nested delegation, though that is an inference from
a parameter name and the teardown must verify or refute it. [asserted]

**The consequence for strategy, stated plainly.** If swarms and task boards are table stakes rather
than differentiators, then **the differentiator is not the swarms — it is what the swarms are
disciplined by.** Nothing in that tool surface measures whether its own checks are right, records who
authored a decision, makes a principal's authority undelegable, or distinguishes a genuinely
different class of evidence from echo. **Those are the four things this project has and they are the
whole of the actual gap.** [asserted]

**Which makes β the product, not the housekeeping.** The principal's bet is on "our decision making
protocols". The sizing algebra behind those protocols assumes verifiers fail independently, and that
assumption is under active challenge because agents sharing a corpus do not; and β itself is
unmeasured, at one human rejection against a minimum of thirty. **The differentiator he is betting on
is the one thing not yet validated, and that is where effort should go.** [measured]

## Organised superintelligence: the positioning, the squads, and RACI

> "People care about magic and impact. This should be a single chat interface that connects the
> worlds superintelligence to find the best answer or better than best before shipping it to a user
> rather than relying on pretrained knowledge of a single model. Consilience, organised
> superintelligence. It will come from somethong like this that perfectly orchestrates and conducts
> organised agent teams, swarms, organisations or whatever tbe language should be. Agent squads I
> think. RACI to ensure decisions are made but explored thoroughly with scientific and mathematical
> approaches, experimentation. All this process for a single primary response in the user's singular
> chat interface. Also want maximum observability and ability to steer if they want i.e. jump into
> running agent processes. The hermes agent kanban stuff sounds good like they have agents not
> clashing and working collaboratively and in organised ways. We need to do that but better. Smarter.
> Kanban is the way humans do it applied to agents, we can make them more organised across larger
> parallel swarms finding the best or better than best before sending to user rather than just
> spitting out the first predicted tokens of one LLM model."

**The positioning is settled by this paragraph and it is not β.** The product claim is *organised
superintelligence*: one chat, behind which many agents converge on an answer, versus one model
emitting its first predicted tokens. **β is how that claim is kept honest; it is never the pitch.**
The orchestrator had this inverted for most of 22 August and was corrected. [measured]

**The term is squads.** Not teams, not swarms, not organisations — the principal chose it. Use it
consistently in user-facing language; ADR-0067's "composition" remains the internal term for the
rule that sizes one. [measured: his words]

**RACI, and the useful discovery is that one letter already exists.** Every specification written on
22 August carries **exactly one accountable Owner** — ADR-0067's rule, restated in the action
surface, autonomy, chat and work-item specs. **That is the A, and it is already load-bearing.** R, C
and I are undefined. [measured]

**C is where consilience lives, and it is the letter that decides whether RACI is real here.** In a
human organisation, "Consulted" means asked for an opinion. **In this system an opinion is echo.** A
Consulted party must contribute a **different class of evidence** — an execution result, a retrieved
primary source, a fresh corpus, a different model family — or it is not Consulted, it is Informed
with a better title. **RACI adopted without that constraint is exactly the cargo this project exists
to refuse.** [asserted]

**On kanban: take the coordination, refuse the serialisation.** The principal is right that Hermes'
board is good and right about why: *"Kanban is the way humans do it applied to agents."* A board
exists because humans cannot hold shared state, cannot be in two places, and need a visible queue.
**Agents are genuinely parallel and share an append-only trajectory.** The coordination properties
worth keeping are atomic claims, dependencies, restart recovery and non-clashing writes — all of
which `coordination.py` and `work_items.py` already carry. The properties to refuse are the ones that
exist only because humans serialise: columns as a workflow, standups, handover ceremony, and WIP
limits set by human attention rather than by measured exposure. [asserted]

**Observability resolves a contradiction that had gone unnoticed, and the resolution is pull, not
push.** ADR-0071, accepted the same day, commits to quiet delivery: an estimate up front, a finished
artefact at the end, **no progress reports**. The principal now asks for *"maximum observability and
ability to steer … jump into running agent processes."* **These conflict only if observability is
pushed.** The resolution: **nothing is ever pushed at the user; everything is always available to
pull.** He may look into any running squad at any moment and intervene; the system never interrupts
him to report. Quiet delivery is about what the product *sends*; observability is about what the
product *exposes*. [asserted]

## The job to be done: one interface instead of eight

> "So why is my idea bad then? none of these systems natively dispatch organised squads of agents
> properly to experiment research and discover before every answer rather than just spitting out
> whatever the pretrainjng says is the next predicted tokens?
> that's what's novel but really I just want an interface that I can use singularly rather than
> havkng to use claude code, cowork, claude design, figma, supergrok, grok bot, cursor, chatgpt work,
> etc etc all sepsrately"

**Two claims, and the orchestrator had been undervaluing both.**

**First, the novelty claim survives today's three teardowns.** Checked rather than assumed:
`ruflo`'s default `swarm`, `agent_spawn` and `hive-mind_spawn` surfaces **"mostly persist coordination
records"** and its 100+ agents are principally Markdown persona manifests; Hermes' delegation is
opt-in per task and its goal judges **admit false positives without a measured rate**; OpenHands is
the closest with critic AUC and Best@8 selection but is coding-specific and labelled by merge/diff
proxies; ChatGPT Work and Cowork offer deep research as **a mode a user invokes**, not the path every
answer takes. [cited: the three teardowns and the product bar, 22 Aug 2026]

**No surveyed system makes convergent, evidence-gathering work the default route for every answer.**
It exists as a mode, as a coding feature, or as a registry — not as how the system works. **That is
the thesis, it was not falsified today, and it is what the three falsified claims were only ever
proxies for.** [asserted]

**Second, and more useful: the job to be done is unification, and it is measurable.** The principal
currently operates **eight** surfaces — Claude Code, Cowork, Claude design, Figma, SuperGrok, Grok
bot, Cursor, ChatGPT Work. **No incumbent can solve this, because each incumbent is one of the
eight.** Hermes does not reach Figma; Cursor does not do Cowork; ChatGPT Work cannot drive Claude
Code. **Only something above them can**, which restates the meta-harness position as a user need
rather than an architectural preference. [asserted]

**The success test is behavioural and needs no β, no gate and no human verdict: does he stop opening
the other seven?** That is falsifiable, cheap to observe, and it is the first product criterion
recorded here that requires nothing from him but his ordinary working day. [asserted]

**A correction the orchestrator owes the record.** Across 22 August it reported three differentiators
falsified — portable cross-harness memory, multi-subscription reach and verifier self-evaluation.
**All three were the orchestrator's own framings, invented that afternoon, not the project's stated
thesis.** Reporting their deaths as though the idea were failing was a framing error. The thesis in
`CONSILIENCE.md` was never tested by any of it. [measured: this conversation]

## Gate B4 is authorised on the private corpora, and publication is not

> "Use jobboard-v2 and hireable-3.0 as the other repos but dont publish any of its data publicly"

**The principal has moved one of two rules and re-affirmed the other.** `AGENTS.md` carries them
separately and they must stay separate: [measured]

1. **Pointing the harness at another repository** — listed under "Ask first". **He has now answered
   that ask for these two repositories.** Gate B4 requires twenty tickets completed on a repository
   other than this one, and these are his own commercial repositories, so this is his to authorise.
2. **Publishing anything from them** — listed under "Never do", and **he re-affirmed it in the same
   sentence.** It does not move.

**What protects the second rule, verified 22 August 2026** [measured]:

- `.githooks/pre-push` runs `check_foreign_identifiers`, `check_private_corpus --require-corpora` and
  `check_secrets --history --untracked --self-test`, and **refuses the push if any fails.** The
  fail-open defect in that hook — a missing checker counted as a pass — was repaired earlier the same
  day.
- `check_private_corpus.py` searches for the **real paths that exist in those repositories**, which is
  the angle that found the original leak when a prefix search structurally could not, plus
  **content fingerprints**: every line of at least twelve words and eighty characters becomes a
  SHA-256 shingle, 25,000 retained per corpus. `--require-corpora` means *"I read those corpora"*,
  not *"those directories exist"*, and a test enforces that reading.
- `.harness/log/` and `.harness/dispatch/` are untracked. Only five example and handoff files under
  `.harness/` are tracked, none of them work artefacts.

**The residual risk no mechanical check can close: paraphrase.** An agent describing a private
repository's architecture in its own words leaks it without matching any shingle or path. **The
mitigation is a rule, not a gate: B4 work products stay in those repositories, and only aggregate
counts return here.** [asserted]

**And "aggregate" must mean a number, not a list.** A previous "names and aggregate measured metrics
may appear" reading is what let **71 private commit identifiers reach a results file**. That reading
is already recorded in `AGENTS.md` as the orchestrator's inference rather than the principal's words.
**For B4 the permitted return is: how many tickets completed, how many the harness intervened in, and
timing. Not which files, not which commits, not what the work was.** [asserted]

## Maximum parallelism is the default, and serialisation carries the burden of proof

> "It should always maximise paralellism by default unless deliberstely constrained by the user and I
> will never want it constrained."

**This inverts where the burden sits.** The orchestrator had been treating parallelism as something to
justify and serialisation as free. The principal's instruction is the reverse: **a serial edge must
earn its place; a parallel one needs no defence.** [measured: his words, 23 Aug 2026]

**The method is already proven in his own repositories and was adopted rather than invented.** His
plans group work into **waves**, not levels. Everything in a wave runs together, and the justification
given is a fact about files — *"no shared files"* — while the few serial edges carry a named reason,
such as a destructive cutover needing a signing substrate live first. Units that police everything
else are ordered **last**, not first, because a constraint applied early blocks work that did not need
blocking. [cited: his plan corpus, method only]

**His repository layout is the other half of it.** Around a hundred trees — one per workstream —
so a shared git index never arises. **He did not coordinate around the collision; he removed the
sharing.** That is the cheaper fix and it generalises: where two workers contend for one resource,
ask first whether they need to share it at all. [measured: directory census, 23 Aug 2026]

**What this requires of Consilient, not just of the build driver.** The harness must schedule for
maximum concurrency by default and treat every serial edge as a claim requiring evidence:

- **A dependency is real only when the dependent work genuinely cannot be done without the other's
  output.** Shared subject matter, narrative order in a plan, or an author's writing sequence are not
  dependencies. An edge with no justifying text is a habit, not a constraint.
- **Isolation beats coordination.** Give each worker its own tree rather than arbitrating a shared
  one. Claims then guard genuine file contention only.
- **The user is never asked to opt into parallelism.** He has said he will never want it constrained,
  so the constraint must come from measured contention or a stated dependency — never from caution.

**The honest asymmetry, which is the one thing that does not bend.** Removing a real dependency is
more expensive than keeping a false one: a unit built against absent output fails, wastes its
dispatch, and can commit something incoherent. So an ambiguous edge stays, **with its uncertainty
stated** — not silently, and not as a habit. That is not conservatism; it is the only place where the
cost is genuinely one-sided. [asserted]

## Most of the intelligence goes into deciding, not doing

> "Not every task needs a genius - either human or AI. So we need to figure out what would not be
> different quality wise if sent to a frontier model for easy/simple tasks. Especially when
> smaller/weaker/cheaper/free models are being instructed by the frontier models and having their
> work reviewed and corrected autonomously. We also need to not spend paralellism or compute for the
> sake of it. A website or app is a relatively small task when compared relative tocthe amount of
> artificial intelligence that we will be orchestrating. Like The Machine in Person of Interest, the
> bulk of the intelligence must be deciding what the right answers/approaches/responses/actions etc
> are better than best befire doing them. Like the superpowers brainstorming and planning skills but
> better and native and including discovery, research and experimentation and simulation and
> deliberate, systematic innovation. In the case of an app or website 80+% of the compute and
> intelligence will be deciding what to build, why and how and only ~20% on actual implementation and
> deployment.
> It needs to decide what needs to be fast and what needs to be better than best but defaulting to
> better than best especially for the things that I'm using. The primary value of consilient wilm be
> working across large, complex, important projects completely autonomously but should also provide a
> facility for temporary/quick chats with users just with a single model. One that doesn't go
> overboard on all the above scientific decision making stuff"

**Half of this is already decided and must be consumed, not rebuilt.** ADR-0002 — one of the four
load-bearing decisions — **is** the cascade: it carries the closed form `β* = (1−α)·e^(−kΔ)`, records
that cascades work where outputs are **objectively assessable**, and already sets the refusal:
*"Refuse to cascade below the measured β\* for the capability gap in play."* `inquiry-tier.md` already
gates how much rigour a decision earns. **"Not every task needs a genius" is ADR-0002.** [measured]

**What is genuinely new, and unspecified:**

**1. The 80/20 inversion, as a budget rather than a sentiment.** For building an application, 80%+ of
compute goes to deciding what to build and why, ~20% to implementing it. **This is the Machine
analogy applied to effort**: the number was the last step of thousands. Nothing today allocates
compute this way — dispatch sizes work by task, never by which *phase* deserves the spend.

**2. Supervision, which is not the same as cascading.** ADR-0002 escalates when a weak model is
likely to fail. The principal describes something else: a frontier model **instructing** a weaker one,
then **reviewing and correcting its work autonomously**. That is a loop, not a fallback, and its
economics differ — the frontier cost is paid on instruction and review rather than on generation.
**Whether that is cheaper at equal quality is an empirical question nobody here has measured.**

**3. Do not spend parallelism for its own sake.** This qualifies the 23 August instruction to maximise
parallelism by default, and the two are consistent: **maximise concurrency where it buys something;
never widen for the appearance of effort.** Idle width is not throughput, and a squad convened where
one owner would do is the waste ADR-0067 already forbids. [asserted]

**4. Two modes, and the light one is a product requirement, not a fallback.** The primary value is
large, complex, autonomous work. But there must also be a **quick single-model chat that does not
invoke the scientific machinery at all.** A user asking a simple question must not trigger discovery,
experimentation and a squad. ADR-0087 already says answer directly when convergence adds no value;
**this makes it a mode the user can rely on rather than an optimisation the system may apply.**

**5. Deciding must include discovery, research, experimentation, simulation and deliberate
innovation** — natively, and better than the brainstorming and planning skills it replaces. **That is
the 80%.** [asserted]

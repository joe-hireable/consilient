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

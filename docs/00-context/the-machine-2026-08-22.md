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

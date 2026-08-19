# How this design position was reached

Source: a single chat session between Joe Brown and Claude (Opus 5), 19 August 2026.
Written by Claude. Biases noted where known.

---

## Starting point

Joe wanted to build "the best harness in the world" — open source and/or commercial —
with a large stated feature set: parallel orchestration of Claude Code / OpenCode / Codex /
Antigravity, real-time inter-agent communication, plug-and-play memory, dynamic tool
loading, reinforcement learning, a `/learn` command that studies a subject "to post-doc
level", dynamic model selection driven by a constrained optimisation, near-total automation
with fine-grained control, self-building custom agents, agent spending under budget,
access via phone/WhatsApp/SMS/email/Slack/app/voice, model battling, on-device models,
self-updating code for new model releases, and world-class standards throughout.

Prior art he brought: a Gemini design session (78pp) that had produced a five-document
"Enterprise Autonomous Agent Harness" playbook, and two of his own repos.

---

## What got cut, and why

**A standalone harness.** Rejected in favour of a meta-harness. DeepSeek released an
MIT-licensed harness with a plugin kernel on 13 Aug 2026 (135k GitHub stars in four days);
Claude Code, Codex, opencode and Antigravity CLI all exist and are maintained by teams with
more resources than a solo founder has hours. Rebuilding tool loops, sandboxes, session
stores and permission prompts is a year of undifferentiated work.
Joe agreed: *"your definition of meta harness is correct and what I want to do."*

**A DeepSeek Harness plugin.** Rejected: v0.1 with promised breaking changes, a
DeepSeek-model-centric audience, and — decisively — it orchestrates *models*, not *agents*.
The thing Joe wants is a layer above it.

**Real-time open-ended inter-agent chat.** Rejected on evidence (see `literature-review.md`).
Replaced by: a native agent-first ticket store as the communication substrate, plus bounded
**"meetings"** — triggered, budgeted, artifact-terminated sessions. This was Joe's own
revision: *"Real-time communication should happen via some sort of project management
system... dedicated 'meetings' should be possible though, not open-ended conversation...
a native one."*

**Model battling / debate.** Rejected: with a verifier available, best-of-n plus tests
dominates deliberation on cost per unit quality. Debate is a technique for domains
*without* an oracle. Coding has one.

**`/learn` as weight updates.** Rejected: conflates retrieval with training; training on
self-generated study material is a documented collapse risk. Replaced by a compiled skill
artifact plus a held-out eval that proves the learning stuck.

**RL as a configurable default.** Deferred: no reward signal exists for research,
spec-writing or planning. Do not ship a config key that does nothing.

**The learned routing policy.** Killed by simulation, not argument — see `findings.md` §4.
~5,000 trajectories to merely *match* plain always-cheap-then-escalate, and no gain after.
This also killed the trajectory-corpus-as-moat idea.

**Enterprise security theatre.** The Gemini playbook's Agent CASB, semantic ToS scanner,
SOC 2 / NIST / HIPAA audit trails and mTLS-to-GCP-Secret-Manager were cut as
procurement cosplay for a solo OSS project. Kept: OS-keychain credentials, outbound
allowlist, sandbox tiering.

**Credentials in chat.** Joe originally wanted the agent to "instruct user to enter
securely these details in chat". Rejected — chat messages land in logs, context windows and
session records. OS keychain plus OAuth device flow instead.

**Every channel at once.** WhatsApp + SMS + email + Slack + app + voice is six auth models
and six failure modes before the core loop is proven. One surface until routing works.

**The RoL formula and the constrained-optimisation screenshot.** Both were *Gemini's*
inventions, not Joe's — confirmed by reading the transcript. Both gate decisions on
quantities unobservable at decision time. See `gemini-session-critique.md`.

---

## What survived and became the thesis

Working from the corrected form of Joe's optimisation screenshot: quality is not observable
at decision time, so model selection is decision-making under uncertainty, and the practical
solution is a **cascade with a verifier** — run cheap, verify against ground truth, escalate
on failure. Coding is the rare domain where ground truth exists (tests, typecheck, build).

Simulating that produced the finding the project is now organised around: **the verifier's
false-accept rate β is the master parameter**, and it governs routing safety, parallelism
ceiling, and human review load simultaneously. See `findings.md`.

---

## Commercial position (changed mid-session)

Initially: exit asset, OSS as go-to-market, with a closed hosted routing service and
aggregate trajectory corpus as the moat.

Revised by Joe: *"I want it to be fully open source - if I get acqui hired great but if not
then it's fine. True open source, giving away everything and having a buy me coffee or
donate button."*

Consequence: no hosted service, no aggregate corpus, no telemetry consent flow. The design
becomes genuinely local-first, which is better software. The binding constraint is Joe's
time, not money — nobody funds a solo founder full-time on donations. That argues for a
small sharply-scoped core with a plugin boundary, not a platform.

---

## Known biases in this document

- Written by Claude, made by Anthropic, whose product (Claude Code) is one of the agents
  this meta-harness would orchestrate. Flagged in-session; treat any comparative claim
  about Claude Code with that discount.
- The simulations were written by the same party that formed the hypothesis. They were not
  independently reviewed. Re-run and attack them.
- Joe's own repos were read; `hermes` turned out to be an empty create-next-app scaffold.

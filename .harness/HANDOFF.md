# Codex → Claude Code orchestration handoff

State: **RELEASE AUTHORISED — successor acknowledgement controls transfer**
Prepared: 20 August 2026
Principal: Joe Brown
Current owner: Codex root in the main worktree
Successor: the existing Remote Control Claude Code session, Claude Opus 5, ultracode,
xhigh effort, authenticated Max subscription path
Release baseline: `ac0072e`

This manifest transfers programme coordination, not hidden reasoning. Git and the append-only
trajectory remain authoritative. Joe may send free-form messages to the successor through
Remote Control while this handoff is staged. Until an explicit `RELEASED` message appears in
that session, the successor must not write to the repository or dispatch workers. Ownership
transfers when the successor replies `HANDOFF-ACCEPTED` to that message.

## Non-negotiable rules

1. Read `CONSILIENCE.md`, `AGENTS.md`, `docs/decisions/index.md`,
   `docs/10-research/experiment-register.md` and `docs/20-design/backends.md`, in that order,
   before acting.
2. British English; every substantive `docs/` claim has an honest evidence tag.
3. Never promote evidence status without new evidence. Apply every stopping rule as written.
4. Supersede ADRs rather than rewriting them. Any declared invariant ships with its check in
   the same commit.
5. Never publish `[SNIP]` or `[2ND]` material. Never publish content from `../hireable-3.0`
   or `../jobboard-v2`; aggregate measurements only.
6. Keep `docs/00-context/friction-log.md` current. One writer per file/task.
7. The repository is pre-approval. Research, experimental adapters, ADRs, invariant checks
   and draft specification work are authorised. Product implementation is not authorised
   until Joe explicitly approves the specification or supersedes that gate.
8. Never use Claude/OpenAI/Google API credits or metered OpenRouter without a separately
   authorised numeric hard cap. Included subscription paths must fail closed before overage.
9. Multi-agent work must name the different class of facts it introduces. Shared-context
   agreement is echo. Stop a line after two no-delta rounds.

## Joe's current direction

- Product outcome: verified human gain while preserving agency—better quality, speed, cost,
  review burden, learning, self-efficacy, stress and user-valued outcomes reported separately,
  not hidden inside one score.
- Target users include individuals, developers and AI enthusiasts, GTM engineers and firms
  with inference spend above £100k/month. The product should help people achieve meaningful
  goals, feel less stressed and deploy bounded companies of agents.
- Research is a first-class output. Joe is the accountable human author/submission principal;
  AI assistance is disclosed and formal publication remains behind exact human approval.
- Prefer sufficient usable context for orchestration. Claude Code Opus 5 is the current
  senior-orchestrator default. OpenRouter `google/gemini-3.7-flash` at high effort is a
  middle-management candidate, subject to EXP-30 and a numeric hard cap.
- Joe reports 20× Max/Ultra individual plans on Claude, Codex and Cursor. Use all three to
  create incremental verified value, never to burn allowance. Check fresh headroom before
  dispatch, use bounded non-overlapping tasks and record every contribution and verifier.
- Antigravity may be used only when its live plan tier, remaining quota and
  `useG1Credits=false` state are observable. Otherwise skip it without blocking progress.
- Local machine: RTX 5090 with 32 GB VRAM, 64 GB RAM and ample disk. Thirty-billion-class
  local experiments are encouraged after hardware admission and pre-registration.

## Authoritative repository state

- Main before the pending checkpoint: `bcc439e`.
- Existing public design record: ADRs 0001–0029, draft v0 specification and experiments
  EXP-01–EXP-29.
- Pending checkpoint adds prompt/feedback research, unnecessary-scope research, publication
  governance, EXP-28/29 hardening, ADR-0030/EXP-30 and the EXP-07 result-isolation invariant.
- Do not stage `.claude/worktrees/`, `.harness/dispatch-specialist.py`,
  `.harness/empty-mcp.json` or `.harness/verify-exp07-result.py` without re-deriving a need.

## Active experiment

EXP-07 is running from the main worktree and writes checkpoints to
`docs/10-research/experiments/exp07/results-exp07.json`. The current Codex PTY identifier is
`36016`, which is not a portable control surface. Frontier completed 5/5 fixtures; local
`qwen3:8b` repetitions are still running. Do not edit `run_exp07.py`, terminate the process
or interpret the partial JSON while it is active. The fixed protocol permits stopping only
for its registered safety/resource conditions or wall-clock cap.

After termination:

1. distinguish verifier instrumentation failure from a model scope violation before summary;
2. exclude true verifier errors from eligible pairs but retain model scope failures as
   rejected attempts;
3. record that out-of-repository writes are not observable under the current bypassed sandbox;
4. run the 15-test suite and prove the retained result hash survives unchanged;
5. write `findings-exp07.md`, update the register, apply the ADR-0003 reopen rule honestly,
   append the trajectory and commit the raw result plus finding.

The first completed result was lost because tests deleted the production path. The autouse
temporary-path fixture now prevents recurrence; `15 passed` and the secret-history invariant
passed before this handoff.

## Pending research inputs

- Human-success/HCI: a read-only delegated pass returned 18 primary sources covering
  calibrated reliance, explanations, autonomy, cognitive load, self-efficacy, skill transfer,
  anthropomorphism and real-work productivity. Treat the memo as leads only until the
  successor independently reads each source used in a public claim.
- Real-time collaboration: the strongest current design separates transport, authoritative
  coordination, human collaboration projection and prompt attention. Slack is a projection,
  not authority; typed control must distinguish persisted, projected, adapter-accepted,
  model-included and effect-evidenced stages.
- Prompt/feedback and unnecessary-work research are drafted in
  `docs/10-research/prompt-context-and-feedback.md` and
  `docs/10-research/unnecessary-scope-and-fanout.md`; EXP-28 and EXP-29 are blocked on frozen
  fixtures and admitted runtimes.

## Highest-value next work after release

1. Finish, verify and commit EXP-07 without outcome-aware protocol changes.
2. Independently ground the HCI memo and pre-register the smallest experiments that decide
   selective reliance, agency/skill retention and segment-level cost per accepted outcome.
3. Pre-register hardware admission and a 30B local-model qualification before any new model
   download; do not claim a size effect across confounded model families.
4. Continue EXP-05/OpenCode/Cursor-ACP/Antigravity evidence closure and resource admission.
5. Converge surviving evidence into ADRs and the draft specification without crossing the
   product-code gate.

## Handoff protocol

When Codex sends `RELEASED <commit>` in the Remote Control session:

1. acknowledge `HANDOFF-ACCEPTED <commit>`;
2. inspect main and the append-only trajectory;
3. ensure no other writer holds the target file/task lease;
4. take the main-tree orchestration lease;
5. post only compact evidence deltas, blockers, handoffs and decisions;
6. keep the Remote Control session open so Joe can continue the conversation from his phone.

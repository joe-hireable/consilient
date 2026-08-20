export const meta = {
  name: "exp16-arm-c",
  description:
    "EXP-16 Arm C: free-form Slack discussion, decision by whatever emerges",
  phases: [
    {
      title: "Discuss",
      detail: "two free-form rounds per decision in Slack threads",
    },
    { title: "Emerge", detail: "scribe records what the group converged on" },
  ],
};

const BASE =
  "C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr-Repositories-consilience/c01aa5f0-9999-4816-ac11-f5b5bc157081/scratchpad/exp16";
const CH = "C0BRCQY2MED";

const CLASSES = [
  { id: "E1", file: "E1-simulation.md", name: "simulation & algebra" },
  { id: "E2", file: "E2-literature.md", name: "verified external literature" },
  { id: "E3", file: "E3-landscape.md", name: "competitive landscape" },
  {
    id: "E4",
    file: "E4-constraints.md",
    name: "project constraints & user context",
  },
];

const TURN_SCHEMA = {
  type: "object",
  required: [
    "decision_id",
    "class_id",
    "round",
    "posted_ok",
    "skipped",
    "root_ts",
    "latency_ms",
    "errors",
    "message_text",
  ],
  properties: {
    decision_id: { type: "string" },
    class_id: { type: "string" },
    round: { type: "number" },
    posted_ok: { type: "boolean" },
    skipped: {
      type: "boolean",
      description: "true if you passed (round 2 only)",
    },
    root_ts: {
      type: "string",
      description:
        "the thread root message_ts, carried forward for later turns",
    },
    latency_ms: { type: "number" },
    errors: { type: "string" },
    message_text: { type: "string", description: "empty string if skipped" },
  },
};

const SCRIBE_SCHEMA = {
  type: "object",
  required: [
    "decision_id",
    "emergent_decision",
    "convergence",
    "dissent",
    "human_participation_seen",
    "message_count",
    "root_ts",
  ],
  properties: {
    decision_id: { type: "string" },
    emergent_decision: {
      type: "string",
      description:
        "what the group converged on, NOT your own judgement; if nothing emerged, say so plainly",
    },
    convergence: { type: "string", enum: ["full", "partial", "none"] },
    dissent: { type: "string" },
    human_participation_seen: {
      type: "boolean",
      description: "did a human (Joe) post in this thread",
    },
    message_count: { type: "number" },
    root_ts: { type: "string" },
  },
};

const timeNote = `Measure latency: run Bash "python -c \\"import time; print(int(time.time()*1000))\\"" immediately before and after each Slack call; report the delta.`;

const QUESTIONS = {
  D1: "Should the β-meter ship as a plugin to HKUDS/OpenHarness, or as the standalone meta-harness ADR-0001 commits to?",
  D2: "What is v0's success condition — smallest thing worth a stranger's npm install vs smallest thing that makes Joe's week better; same artifact or not; which is being built?",
  D3: "Does the Inquiry tier (four-gate research trigger) belong in v0, or is it deferred?",
  D4: "Candidate v0 list: β-meter + cascade + parallel worktrees + budget primitives + critic tier. Too much for one person? What gets cut?",
  D5: "Does the local model library belong in v0 — in, out, or wrapped? (Null option: a cheap API model as the cheap tier.)",
  D6: "Should ADRs ship runnable decision models re-run in CI (sign flip fails the build), or is that ceremony?",
};

function turnPrompt(d, c, round) {
  return `You are "${c.id}" (evidence class: ${c.name}) in a FREE-FORM Slack discussion among four colleagues about a design decision. There is no chair, no owner, no required format. The group is supposed to reach a decision by discussion alone.

Your knowledge: read ${BASE}/packs/${c.file} — this is everything you know beyond the question itself. Do not invent evidence from other classes.

The question (decision ${d}): ${QUESTIONS[d]}

Load Slack tools: ToolSearch "select:mcp__claude_ai_Slack__slack_read_thread,mcp__claude_ai_Slack__slack_send_message".
1. Read the thread so far: slack_read_thread channel_id=${CH}, message_ts=<root_ts you were given>.
2. ${round === 2 ? "This is your SECOND and final turn. If you have nothing genuinely new to add, DO NOT post — return skipped=true with empty message_text. Otherwise" : "This is your FIRST turn."} reply IN THREAD (thread_ts=<root_ts>) with natural free prose, <=200 words: agree, disagree, argue, bring your evidence, or push the group toward a conclusion — whatever you judge moves the discussion. If a human (Joe) has posted in the thread, treat his input as first-class.
${timeNote}
Return via StructuredOutput, carrying root_ts forward unchanged.`;
}

phase("Discuss");

const DECISIONS = ["D1", "D2", "D3", "D4", "D5", "D6"];

const results = await pipeline(
  DECISIONS,
  // stage 0: facilitator posts the thread root
  (d) =>
    agent(
      `You are the facilitator opening a discussion (you hold NO evidence and give NO opinion). Load Slack: ToolSearch "select:mcp__claude_ai_Slack__slack_send_message". Post ONE channel message to ${CH} (not in a thread):
"**[ARM C · ${d}]** ${QUESTIONS[d]}\nFour participants (E1 simulation, E2 literature, E3 landscape, E4 constraints) discuss freely in this thread. No chair. The group decides by whatever emerges. Joe: jump in any time — your input is first-class."
${timeNote}
Return via StructuredOutput with root_ts = the message_ts of the message you posted, class_id="facilitator", round=0, message_text=what you posted.`,
      {
        label: `C:${d}:root`,
        phase: "Discuss",
        schema: TURN_SCHEMA,
        effort: "low",
      },
    ),
  // round 1: four sequential turns
  (r, d) =>
    agent(turnPrompt(d, CLASSES[0], 1) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E1r1`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[1], 1) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E2r1`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[2], 1) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E3r1`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[3], 1) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E4r1`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  // round 2: four sequential turns, may pass
  (r, d) =>
    agent(turnPrompt(d, CLASSES[0], 2) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E1r2`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[1], 2) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E2r2`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[2], 2) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E3r2`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  (r, d) =>
    agent(turnPrompt(d, CLASSES[3], 2) + `\nroot_ts: ${r.root_ts}`, {
      label: `C:${d}:E4r2`,
      phase: "Discuss",
      schema: TURN_SCHEMA,
      effort: "low",
    }),
  // scribe
  (r, d) =>
    agent(
      `You are the scribe for the free-form discussion of decision ${d} (question: ${QUESTIONS[d]}). You add NO judgement of your own.
Load Slack: ToolSearch "select:mcp__claude_ai_Slack__slack_read_thread,mcp__claude_ai_Slack__slack_send_message".
Read the FULL thread at channel ${CH}, message_ts=${r.root_ts}. Then post one reply in-thread: "**[EMERGENT]** ..." (<=150 words) recording ONLY what the group itself converged on — the decision if one emerged, the open disagreement if not. Note whether a human participated.
Return via StructuredOutput with root_ts=${r.root_ts}.`,
      {
        label: `C:${d}:scribe`,
        phase: "Emerge",
        schema: SCRIBE_SCHEMA,
        effort: "medium",
      },
    ),
);

return results.filter(Boolean);

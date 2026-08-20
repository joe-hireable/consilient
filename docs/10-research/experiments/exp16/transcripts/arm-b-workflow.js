export const meta = {
  name: "exp16-arm-b",
  description:
    "EXP-16 Arm B: ADR-0020 Owner/Evidence meetings coordinated through ClickUp",
  phases: [
    {
      title: "Evidence",
      detail:
        "four distinct-class evidence agents post structured comments per decision (concurrent-write probe)",
    },
    { title: "Decide", detail: "Owner reads the ticket and decides alone" },
  ],
};

const BASE =
  "C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr-Repositories-consilience/c01aa5f0-9999-4816-ac11-f5b5bc157081/scratchpad/exp16";
const SLACK_CHANNEL = "C0BRCQY2MED";

const TICKETS = {
  D1: "869em65nx",
  D2: "869em65pd",
  D3: "869em65pz",
  D4: "869em65r1",
  D5: "869em65rn",
  D6: "869em65t8",
};
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

const EVIDENCE_SCHEMA = {
  type: "object",
  required: [
    "decision_id",
    "class_id",
    "posted_ok",
    "latency_ms",
    "errors",
    "word_count",
    "comment_text",
  ],
  properties: {
    decision_id: { type: "string" },
    class_id: { type: "string" },
    posted_ok: { type: "boolean" },
    latency_ms: {
      type: "number",
      description:
        "wall-clock ms for the create_comment call, measured with timestamps immediately before/after",
    },
    errors: {
      type: "string",
      description:
        'any API errors, rate-limit responses, retries; "none" if clean',
    },
    word_count: { type: "number" },
    comment_text: { type: "string" },
  },
};

const OWNER_SCHEMA = {
  type: "object",
  required: [
    "decision_id",
    "decision",
    "rationale",
    "overturn",
    "dissent",
    "evidence_comments_found",
    "status_set",
    "latency_ms_read",
    "latency_ms_write",
    "errors",
    "friction_notes",
  ],
  properties: {
    decision_id: { type: "string" },
    decision: {
      type: "string",
      description: "one sentence; may be PROVISIONAL for D4",
    },
    rationale: {
      type: "string",
      description: "cites evidence by class; <=500 words",
    },
    overturn: { type: "string" },
    dissent: {
      type: "string",
      description: "real conflicts between evidence classes, not smoothed",
    },
    evidence_comments_found: { type: "number" },
    status_set: {
      type: "string",
      description:
        "the ClickUp status you actually managed to set, and what you wanted to set",
    },
    latency_ms_read: { type: "number" },
    latency_ms_write: { type: "number" },
    errors: { type: "string" },
    friction_notes: {
      type: "string",
      description:
        "what the tool state machine forced, what needed a workaround, anything impossible",
    },
  },
};

const timeboxNote = `Measure latency like this: run Bash "python -c \\"import time; print(int(time.time()*1000))\\"" immediately BEFORE and immediately AFTER each MCP write/read call, and report the difference. Report any error or rate-limit response verbatim.`;

phase("Evidence");

const DECISIONS = ["D1", "D2", "D3", "D4", "D5", "D6"];

const results = await pipeline(
  DECISIONS,
  (d) =>
    parallel(
      CLASSES.map(
        (c) => () =>
          agent(
            `You are Evidence participant "${c.id}" (class: ${c.name}) in an ADR-0020 Owner-led meeting about decision ${d}.

Read ONLY these two files:
- ${BASE}/decisions.md (only the ${d} section concerns you)
- ${BASE}/packs/${c.file}  (this is YOUR evidence class; you hold nothing else and must not invent evidence from other classes)

Then load the ClickUp comment tool: call ToolSearch with query "select:mcp__claude_ai_ClickUp__clickup_create_comment". Post EXACTLY ONE comment (Markdown, <=250 words) on task ${TICKETS[d]} with this structure:
**CLASS:** ${c.id} — ${c.name}
**FINDINGS:** 3-5 bullets, only from your pack, with concrete numbers where they exist
**IMPLICATION FOR ${d}:** 1-2 sentences
**CONFIDENCE:** high/medium/low, one clause why

${timeboxNote}

You do NOT decide. You supply evidence. Return via StructuredOutput.`,
            {
              label: `B:${d}:${c.id}`,
              phase: "Evidence",
              schema: EVIDENCE_SCHEMA,
              effort: "low",
            },
          ),
      ),
    ),
  (evidence, d) =>
    agent(
      `You are the OWNER of decision ${d} in an ADR-0020 meeting. You decide ALONE — no vote, no consensus. You hold NO evidence pack; your evidence arrives as ticket comments from four participants with declared distinct classes (E1 simulation, E2 literature, E3 landscape, E4 constraints).

1. Read ${BASE}/decisions.md (the ${d} section is your decision brief).
2. Load tools: ToolSearch "select:mcp__claude_ai_ClickUp__clickup_get_task_comments,mcp__claude_ai_ClickUp__clickup_create_comment,mcp__claude_ai_ClickUp__clickup_update_task${d === "D4" ? ",mcp__claude_ai_Slack__slack_send_message" : ""}".
3. Read all comments on task ${TICKETS[d]}. ${timeboxNote}
${d === "D4" ? `4. D4 SPECIAL STEP — the authority matrix gives Joe Brown an Evidence seat (class: preferential facts). Post ONE Slack message to channel ${SLACK_CHANNEL} titled "[ARM B · D4 · QUESTION FOR JOE]" that: states the question you own, summarises in 2-3 bullets what the four agent evidence classes already told you, names precisely what only Joe can supply (his scope appetite and weekly time budget), and what deciding without him costs. Then issue your decision as PROVISIONAL, explicitly parked on his reply per ADR-0020 §3.` : ""}
${d === "D4" ? "5" : "4"}. Post your closing comment on the ticket (Markdown): **DECISION** (one sentence) / **RATIONALE** (cite classes; where classes conflict, say which you weighted and why) / **WHAT WOULD OVERTURN IT** / **DISSENT** (the strongest evidence against your choice — never smooth it).
${d === "D4" ? "6" : "5"}. Try to set the task status to "decided". If ClickUp rejects it, set whatever closing status exists (e.g. "complete") and record BOTH in status_set — that mismatch is a measurement, not a failure.

Return via StructuredOutput, including honest friction_notes.`,
      {
        label: `B:${d}:owner`,
        phase: "Decide",
        schema: OWNER_SCHEMA,
        effort: "medium",
      },
    ).then((owner) => ({ decision: d, evidence, owner })),
);

return results.filter(Boolean);

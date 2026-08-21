# The capability layer — curate, do not build

Status: **v1+ design documentation. Not v0** (ADR-0015 Stage 2 gates v0 at
instrumentation only). Written 19 Aug 2026; every licence below verified from the
repository or package on that date, not from directories or blog posts.

The premise checked out for the fifth consecutive time: "someone already built this,
MIT-licensed" (model library → LM Studio; harness → DeepSeek/OpenHarness; harness
optimisation → Meta-Harness; skill distribution → skills.sh et al.; now capability
provision → the MCP ecosystem). Nothing in this layer justifies first-party code beyond
configuration and curation.

## What the layer is for — stated precisely, because the obvious claim failed

The obvious claim — "tools narrow the capability gap Δ and loosen β*" — **did not survive
scrutiny** (`../10-research/experiments/capability_context_beta_star.py`, and the Δ
section in ADR-0002). Missing capabilities are not a competence deficit; they are
**structural zeros** — tasks the cheap tier cannot attempt at any difficulty. What that
does to routing depends on whether the verifier catches capability failures:

- Caught reliably (a missing docx fails a file-exists check): blocked tasks always
  escalate. The tool layer buys **cost** (avoided guaranteed escalations), not safety.
  `[algebra]`
- Not caught (the model hallucinates instead of searching; tests cannot check facts):
  the effective threshold drops below the closed form — β*  0.112 → 0.059 at 30%
  blocked tasks — and the closed form is **false-safe** about tasks it does not model.
  Here the tool layer is a genuine safety lever. `[algebra]`
- Which regime a repo is in is a per-check-class measurement (ADR-0012), not a
  derivable fact. `[asserted]`

Either way the layer earns its place; it just is not a Δ mechanism, and giving a 4B
model a browser leaves it a 4B model — recovered tasks succeed at the cheap tier's
unchanged rate (43.9% in the reference model). `[algebra]`

## Default tool set — sourced, with verified licences

| Capability | Supply | Licence (verified 19 Aug 2026) | Maintainer / status |
|---|---|---|---|
| Browser | **Playwright MCP** (`microsoft/playwright-mcp`) | Apache-2.0 | Microsoft; 36.3k★, active. The de facto standard. (`browser-use`, MIT, 109k★, is the heavier LLM-in-loop alternative; puppeteer reference server is archived — do not supply.) |
| Fetch (URL→markdown) | Reference server `modelcontextprotocol/servers` `src/fetch` | MIT→Apache-2.0 transition (repo SPDX NOASSERTION; permissive either way) | Anthropic/MCP project; active |
| Filesystem / git | Reference servers `src/filesystem`, `src/git` | same | Supply **only** for the native path — every delegated agent has its own |
| Web search | Brave (`brave/brave-search-mcp-server`, MIT) · Exa (MIT) · Tavily (MIT) | MIT, all official | All require API keys → ship **config templates, not working defaults** |
| Documents (docx/xlsx/pptx/pdf) | **anthropics/skills document skills — CANNOT BE BUNDLED** | **Proprietary source-available**: "All rights reserved", explicit no-redistribution / no-derivatives clauses, per-directory LICENSE.txt | **The licence landmine of this sweep.** ADR-0014's "consume anthropics/skills" holds only as *point the user at the marketplace install*; an MIT harness that vendors these violates the licence. The Apache-2.0 example skills in the same repo are fine. An open replacement (docx via python-docx etc.) is a genuine gap — see below. |
| Email | Resend MCP (MIT, official) | MIT | Modest adoption (562★); optional, API-key-gated |
| Scheduling / cron | **Nothing to supply** — no standard exists (best candidates are stale sub-100★ personal repos) | — | Use OS cron / the harness's own scheduler; this is the one slot where the harness's own machinery is the right answer |

The binding record for third-party components selected or licence-refused here is `../legal/adopted-components.json`. `[measured]`

## Genuinely missing — the honest build-or-gap list

1. **Open document-creation skills.** The Anthropic ones are not open source. The open
   path (Joe's suggestion, 19 Aug 2026, assessed and adopted as the plan of record):
   **pandoc** (GPL-2, shelled out) for markdown→docx/odt; **python-docx / openpyxl /
   python-pptx** (MIT) for structured authoring; **LibreOffice headless** (MPL-2.0,
   shelled out, never bundled) for the convert/render leg — `soffice --headless
   --convert-to pdf` is the battle-tested core of most server-side converters. Known
   costs: ~700 MB install, startup latency, and profile-locking under concurrency
   (needs per-process `-env:UserInstallation`). Authoring via LibreOffice's UNO API is
   heavyweight — avoid; author with the Python libraries, render with soffice. For
   templated documents, **docxtpl** (python-docx-template, MIT) puts Jinja2 syntax
   inside a .docx template — the strongest authoring leg for anything with a repeating
   structure, and a pattern already proven in Joe's private repos (the *pattern*
   transfers; those repos' templates are strictly private and are never copied here —
   AGENTS.md "Never do"). Still not v0; a thin Apache-2.0 skill wrapping
   pandoc + python-docx/openpyxl + docxtpl + soffice is the v1+ shape. `[asserted]`
2. **A scheduling MCP** — see table; harness-native.
3. **Small-model-tuned tool descriptions** — not missing as software but as *knowledge*:
   see EXP-17.

## Inherited vs native — build nothing twice

Verified: **Claude Code ships MCP tool search natively, auto mode on by default, since
v2.1.7 (13 Jan 2026)** — the user's belief was exactly right. `[measured]` So:

- **Delegated path** (Claude Code, and increasingly Codex etc.): progressive disclosure,
  tool search, and skill loading are **inherited**. The harness attaches MCP servers and
  gets context discipline for free. Nothing to build.
- **Native path** (OpenRouter / local models): a bare chat-completions API — no deferral,
  no search. This is the only place context management is the harness's problem, and the
  space is **commoditised** (all verified active, Apache-2.0/MIT): MCP gateways with
  dynamic discovery (Docker MCP Gateway, ToolHive vMCP, IBM MCP Context Forge, Microsoft
  MCP Gateway, MCPX), framework-side tool retrieval (LlamaIndex `tool_retriever`,
  langgraph-bigtool, pydantic-ai toolsets), and code-execution-instead-of-tool-calls
  (smolagents CodeAgent, Cloudflare Code Mode — both Apache-2.0/MIT). `claude-code-router`
  (MIT, 36.7k★) is the pragmatic bridge: keep Claude Code's harness and its inherited
  disclosure, swap the model underneath. **Adopt one; build none.** Caution: MCP Router
  (the desktop app) is Sustainable-Use licensed, not open source — excluded.

Full pattern-level treatment: `context-loading.md`.

## EXP-17 — the question that is actually unmeasured

The headline framing ("do small models succeed with frontier-tuned tools?") is **not
novel**: PA-Tool (arXiv:2510.07248) already showed SLMs fail on schemas with unfamiliar
naming and gain ~17% from model-aligned renaming; Hammer (arXiv:2410.04587) documented
naming-convention sensitivity; RoTBench perturbs names/descriptions per model; RAG-MCP
swept tool count 1→11,100 on one large model. What nobody has published
(`experiment-register.md` § EXP-17 for the runnable version):

- the **factorial interaction** — model size (4B/8B/14B) × loaded-tool count ×
  description variant — yielding per-model optimum-N curves;
- **per-tool acceptance profiles** — *which* tools a given small model succeeds with,
  rather than aggregate accuracy over synthetic APIs;
- measured on a **real harness inventory** (this repo's default set above), not
  benchmark APIs.

Directly downstream of β: the profile decides what the cheap tier may be handed, which
sets the feasible-task mass φ, which sets the effective threshold (§ above).

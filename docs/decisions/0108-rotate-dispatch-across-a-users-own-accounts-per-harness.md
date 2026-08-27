# 0108. Rotate dispatch across a user's own accounts, per harness, where the vendor allows it

- **Status:** PROVISIONAL
- **Date:** 2026-08-26
- **Deciders:** Joe Brown (principal), orchestrator
- **Supersedes:** none
- **Inquiry tier reached:** T1 ground
- **Executable model:** all four, as of EXP-146 on 27 August 2026. Each harness isolates a
  sign-in session by its own variable — `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `GROK_HOME`, and
  `HOME` for Cursor under WSL. This line previously read that Claude's model was blocked and
  that Cursor had no model at all "because no isolation mechanism exists to build one from".
  Both were wrong, and EXP-146 measured them wrong in the same publication as this file.

## Context

Joe, 26 August 2026: *"I know many hardcore devs that have multiple accounts on the $200-300
max plans"* — individual developers already run several personal subscriptions on one harness
for their own work. The question raised is whether Consilient should formalise switching
dispatch between a user's own several accounts on the same harness, to raise the effective
concurrent headroom a single-account deployment hits during a long build session (this
project's own night of 26 August 2026 hit exactly this ceiling on Claude and Cursor both, and
`ARMS` was rebalanced away from both as a result — see `.harness/build_driver.py`, commit
`9782cd7`).

**The scenario this ADR evaluates is narrow and matters for what follows.** One person owns and
pays for several accounts on one harness. Consilient runs entirely on that person's own
machine. It never reads, stores, or relays a credential or session token — it only selects
which of the person's own already-authenticated local profile directories the *real, unmodified*
harness binary should be pointed at for a given dispatch, the same way a person could manually
run `HOME=~/.claude-account-2 claude ...` themselves. No other human's account is ever touched.
This is a materially different fact pattern from a multi-tenant product that logs *other
people's* accounts in and routes their credentials through a shared service — that pattern is
the one every vendor's terms squarely and explicitly prohibit, and this ADR does not propose it.

§7.1 of `../40-spec/v0-draft.md` already keys resource records by "account, provider, plan,
native bucket and native window" — an account dimension the schema anticipates but that nothing
today populates with more than one value per provider. [measured]

## Decision

Consilient may dispatch to more than one of a user's own accounts on the same harness,
per-harness, only where both hold:

1. **A vendor-documented mechanism exists that isolates the credential itself**, not just
   ancillary session state — confirmed by reading the primary documentation, not inferred from
   a config-directory name. [asserted]
2. **Nothing in that vendor's actual written terms squarely names this scenario and prohibits
   it**, evaluated against the narrow scenario above, not the reselling/sharing scenario a
   naive reading collapses it into. [asserted]

Per harness, as of this ADR:

- **Codex: build it.** `CODEX_HOME` is documented to include `auth.json`; independent
  third-party tooling (`codex-accounts`) already does exactly this; non-interactive auth exists
  (`CODEX_API_KEY`/`CODEX_ACCESS_TOKEN`) so a rotated account can dispatch unattended. [cited]
- **Grok: build it.** `GROK_HOME` is documented to include `auth.json`; xAI ships its own
  `/dual-grok-account` helper naming this exact use case; non-interactive auth exists
  (`XAI_API_KEY`, `grok login --device-auth`). [cited] `scripts/dispatch.py` currently does the
  opposite of the documented recipe — it re-points every dispatch's `GROK_AUTH_PATH` back at one
  shared `auth.json` (see `Section 1` finding below) — so this is a real code change, not
  configuration.
- **Claude: build it. EXP-146's mechanism half returned clean.** [measured 27 August 2026]
  `CLAUDE_CONFIG_DIR` does not leave the session behind in `~/.claude.json` as this bullet
  originally feared — it **relocates that file**, and relocates `.credentials.json` with it. A
  never-authenticated directory reports `{"loggedIn": false}` while the home configuration is
  untouched, and seeding that directory with a credential flips it to `loggedIn: true`, which is
  the positive control proving the directory is the thing consulted. Two caveats the procedure
  did not anticipate: the credential is a FILE, not a keychain entry (Windows Credential Manager
  holds nothing), and an isolated directory reports `email: null` until a real login completes
  there, so attribution must never assert against a directory seeded by copying. EXP-146's
  remaining clause — two accounts dispatching concurrently, each correctly attributed — needs an
  interactive second sign-in and is not yet run. Nothing routes a second Claude account into
  dispatch before it does.
- **Cursor: buildable, and this bullet was wrong twice.** [measured 27 August 2026] It said no
  config-directory override exists and that the credential lives in the OS keychain. Neither
  holds. The credential is a file, `~/.cursor/cli-config.json`, and `cursor-agent` runs under
  WSL on this machine, where `HOME` is honoured — so `HOME=<dir> cursor-agent` isolates a
  session cleanly, a fresh directory reporting `Not logged in` against a default that is signed
  in. There is no dedicated variable, which is why the original reading found nothing to point
  at; the isolation comes from the namespace the binary runs in. Note the asymmetry with Grok,
  measured the same day: overriding `HOME`/`USERPROFILE` on Windows does **not** move Grok's
  configuration, only `GROK_HOME` does. No single mechanism covers all four — per-harness
  isolation is forced, not a convenience.

**A rotated account is treated exactly like any other harness failure mode this project already
handles.** A banned, rate-limited, or otherwise unavailable account is not evidence about the
work in flight (the same F-05 discipline `.harness/build_driver.py` already applies to
infrastructure deaths) — it is refunded, not counted against the unit, and the pool simply
routes elsewhere. The user, not Consilient, bears whatever account-standing risk the vendor's
enforcement systems might apply; this feature does not shift or obscure that risk, it only
described honestly.

## Evidence

- `[cited]` Codex: `CODEX_HOME` documentation names `auth.json` as part of what it relocates;
  `github.com/omarhoumz/codex-accounts` is a working third-party implementation of exactly this.
- `[cited]` Grok: xAI's own `02-authentication.md` states the multi-account recipe directly and
  ships `/dual-grok-account`; `scripts/dispatch.py` lines ~1994-2000 already set `GROK_HOME` per
  dispatch run but explicitly re-point `GROK_AUTH_PATH` at the one shared credential file,
  confirming the repository's own code, not just the vendor, treats this as a live, close gap.
- `[cited]` Claude: Anthropic's Claude Code "Legal and compliance" page, read in full, frames its
  prohibition on "rout[ing] requests through Free, Pro, or Max plan credentials on behalf of
  their users" under a heading about third-party developers building products *other people*
  log into — a different actor from this scenario — and states plainly that "an end user
  sign[ing] in to the unmodified Claude Code binary with their own Claude subscription" is not
  restricted. The one clause broad enough to textually reach automated local switching
  ("access... through automated or non-human means") carries an explicit "or where we otherwise
  explicitly permit it" carve-out that Claude Code's own headless/automation features already
  occupy. Anthropic's Usage Policy's only "multiple accounts" language sits under
  ban-evasion/malicious-coordination, not rate-limit or quota language.

  **Removed 27 August 2026, before this file was ever published.** [asserted] This paragraph
  continued with three further claims: that a named, identifiable Anthropic employee had
  publicly stated multiple Max account ownership is not itself a ToS violation; that a February
  2026 ban wave was later attributed by Anthropic to a crackdown on harness-spoofing; and that
  it caught legitimate multi-account users as collateral damage. None carried a URL, an archive
  link or a retrieval date, and a pre-publication audit found them on their way to a public
  repository. An unsourced assertion about what a named real person said is not evidence, and
  putting one in the shop window of a project whose subject is measurement honesty is the same
  defect as the README superlative — larger, because it is about somebody. The claims are
  recorded as removed rather than deleted silently. Restore any of them with its source.
- `[cited]` A real, publicly visible open-source ecosystem (cc-hotswap, clauth, teamclaude,
  claude-code-multi-account, ccrotate, claude-swap) already performs Claude account rotation via
  local config-directory switching, with no confirmed enforcement action found against this
  specific pattern — every confirmed Anthropic enforcement episode found targets a different act
  (harness-spoofing, resale, commercial use on a consumer plan).
- `[cited]` OpenAI's own product ships a first-party "account switching" feature letting one
  person stay signed into two accounts and flip between them — direct vendor precedent that
  "one person, several of their own accounts, switched locally" is ordinary, sanctioned use, on
  at least one frontier lab's own product design.
- `[cited]` Cursor's Terms of Service, read in full directly, contains no clause on multiple
  accounts or automated access beyond generic reverse-engineering and account-responsibility
  language. **No URL, version or retrieval date was recorded**, and a vendor's contract changes
  without notice, so this is a reading of an undated document and cannot be relied on as
  current. Re-read it with provenance before anything depends on it.

  Retagged from `[measured]` on 27 August 2026 after a pre-publication audit. Reading a document
  is `[cited]` in this repository's vocabulary; `[measured]` is reserved for something that was
  run. An absence claim about a named vendor's contract, unsourced and undated, carried at the
  strongest tag available was the tag doing rhetorical work its evidence did not support.

- `[measured 27 August 2026]` The second half of that bullet — "no config-directory override or
  headless login exists in its CLI reference" — was **wrong**, and EXP-146 measured it wrong.
  There is no dedicated variable, but `cursor-agent` runs under WSL here and `HOME` isolates it:
  a fresh `HOME` reports `Not logged in` against a default that is signed in, and the credential
  is a file at `~/.cursor/cli-config.json`, not a keychain entry.

## Evidence against

- `[asserted]` Anthropic "reserves the right to take measures to enforce these restrictions...
  without prior notice," and its own enforcement systems have already produced false-positive
  bans of legitimate multi-account users as collateral from an unrelated sweep. The written
  terms not squarely naming this scenario is not the same as the terms being tested against it;
  the honest position is "reasonably supported, not certain," and this ADR does not upgrade that.
- `[cited, weak]` One secondary, non-Anthropic source (a marketing/affiliate blog) frames
  "hitting a limit on one account and switching to another repeatedly" as "medium risk... may be
  read as circumventing service restrictions." No enforcement action or primary-source citation
  backs this reading; it is recorded because it is the one piece of commentary arguing against
  the practice, not because it is well-evidenced.
- `[asserted]` xAI's own Terms of Service and Acceptable Use Policy could not be fetched from a
  primary source during this research (repeated 403s); Grok's technical picture is clean but its
  legal picture rests on the same generic automated-access language every vendor carries, without
  the confirmation Anthropic's case has. This is a real gap, not a confirmed silence, and should
  not be read as equivalent to Cursor's confirmed-silent position.
- `[measured 27 August 2026]` Claude's isolation mechanism is verified in exactly the dimension
  that matters: `CLAUDE_CONFIG_DIR` relocates the sign-in session, `.credentials.json` included.
  Until that date this bullet read that it was *unverified*, and carried a `[measured]` tag while
  doing so — a tag on the absence of a measurement, which is the inflation this repository's
  evidence discipline exists to prevent. What remains ungated is concurrent dual-account
  attribution, which is EXP-146's second clause and needs an interactive sign-in.

## Consequences

**Positive** — Codex and Grok get a working, vendor-sanctioned path to more effective personal
headroom with low legal and technical risk; the resource-accounting schema in
`../40-spec/v0-draft.md` §7.1 gets a real second value in its account dimension instead of an
anticipated-but-unused one.

**Negative** — this is real new surface: per-account credential directories to manage, a
rotation policy to design (round-robin, headroom-aware, or failure-driven), and a genuine,
if probably small, residual account-standing risk on Claude that Consilient does not eliminate
and must not understate. Cursor stays a single-account harness until its own tooling changes,
which narrows this feature's benefit exactly where this project hit its worst contention
tonight.

**Neutral but load-bearing** — this ADR does not authorise reading, storing, or relaying any
credential Consilient does not already need for its existing single-account operation. Any
future proposal that has Consilient itself hold, generate, or broker a session token on a
user's behalf is a different and much more exposed act than what this ADR evaluated, and does
not inherit this ADR's evidence.

## Enforcement

- Check: a rotation implementation must set the per-account directory before invoking the real,
  unmodified harness binary, and must never itself read, log, or transmit the contents of that
  directory's credential file. No such check exists today.
- Check: `scripts/dispatch.py`'s Grok path must stop re-pointing `GROK_AUTH_PATH` at one shared
  file when multi-account mode is active, per the gap this ADR's evidence section names. Not
  written yet.
- Check: Claude account rotation must refuse to activate until EXP-146 records a clean result;
  a stale or absent EXP-146 record fails closed to single-account behaviour. Not written yet.
- Check: Cursor must not be offered as a rotation target; attempting to configure it should
  refuse with a clear message naming the missing isolation mechanism, not silently no-op.
- Fails CI: no — **none of these checks exist today**, and until they run in `invariants.yml`
  this ADR's constraints are prose rather than chokepoints, exactly as ADR-0098 records for its
  own unimplemented enforcement.
- Added in the same commit as the implementation: not applicable; this ADR authorises no code
  change itself.

## What would overturn this

**For Claude specifically:** EXP-146 finding that `CLAUDE_CONFIG_DIR` does not isolate the
sign-in session under any tried configuration reverts Claude to single-account-only, with no
change to Codex or Grok's status.

**For any harness:** a confirmed enforcement action — an account ban, a policy update, or a
direct statement from the vendor — specifically against this narrow scenario (own accounts,
local automation, no credential extraction), as opposed to the harness-spoofing and resale
patterns the evidence above already distinguishes from it, would mean this ADR's central
distinction does not hold in practice and the feature should be withdrawn for that harness
immediately, not merely paused.

**For xAI specifically:** if a primary-source read of xAI's Terms of Service or Acceptable Use
Policy, once obtained, contains language equivalent to Anthropic's third-party-intermediation
clause, Grok moves from "build it" to gated-pending-review alongside Claude.

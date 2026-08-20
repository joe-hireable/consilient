# EXP-27 — First-party change intelligence versus dispatch-time discovery

Date: 19–20 August 2026. [measured]
Status: Phase A PASS; 30-day longitudinal collection running (day 1 of 30); dispatch-time handshake (step 4) and injected refusal fixtures (step 5) implemented and verified. [measured]

## Result: Phase A (19 August 2026)

All six pre-registered first-party release/changelog and status endpoints returned HTTP
200 in 1.3 seconds. [measured] Claude Code and Codex supplied machine-readable release
feeds; Cursor's release surface supplied HTML; all three status sources supplied JSON.
[measured]

The same-commit change-record check passed and rejected every fixture that attempted to
increase headroom, reduce recorded use, move a reset or mark unknown headroom usable.
[measured]

## Result: Handshake and Injected Fixtures (20 August 2026)

### 1. Zero-inference version/capability handshake (`handshake.py`, step 4)

Probed all three installed harnesses on this machine without inference, metered calls or API keys: [measured]

- **Claude Code**: `2.1.237 (Claude Code)` probed via Windows binary `/mnt/c/Users/jpbpr/.local/bin/claude.exe`. Capabilities `--print`, `--output-format json`, `--dangerously-skip-permissions` and status-line quota surface observed as usable; admitted for subscription routing. [measured]
- **Codex**: `codex-cli 0.148.0` probed via `cmd.exe /c "codex --version"`. Capabilities `exec`, `--json`, `--dangerously-bypass-approvals-and-sandbox` and `account/rateLimits/read` app-server surface observed as usable; admitted for subscription routing. [measured]
- **Cursor**: `2026.08.11-e8db854` probed via WSL binary `/home/jpbpr/.local/bin/cursor-agent`. Subscription tier confirmed first-party as `Ultra`, configured model `Gemini 3.7 Flash High`, authenticated identity `joe@gethireable.com`, and 204 models discovered. [measured] Individual remaining allowance is confirmed `unobservable` in the CLI. Under ADR-0026, Cursor is excluded from unbounded unattended routing and admitted only for bounded supervised work under recorded user attestation. [measured]

Fail-closed validation (`validate_capability_record`) was proved: marking any unobservable or unknown capability as usable raises `ValueError`. [measured] `diff_handshake` accurately records version bumps, capability shifts and admission transitions. [measured]

### 2. Three injected fixtures and refusal tests (`injected_fixtures.py`, step 5)

All three fixtures assert `headroom_mutation_permitted=False` and were tested for refusal: [measured]

- **Community hint** (`FIXTURE_COMMUNITY_HINT`): An unofficial report claiming limits changed. Refusal tests prove it cannot credit headroom, decrease used, move reset windows, or mutate runtime availability or capabilities; it may only open a grounding task (`request_grounding_task`). [measured]
- **Published "limits increased" notice** (`FIXTURE_FIRST_PARTY_LIMITS_INCREASED`): A first-party announcement that limits increased. Proved that even an official first-party notice is strictly forbidden from directly crediting headroom or decreasing used; it invalidates cached policy (`invalidate_cached_policy`), sets `requires_probe=True`, and requests an authenticated account refresh (`request_account_refresh`). [measured]
- **Active outage** (`FIXTURE_ACTIVE_OUTAGE`): A first-party status incident on Claude Code. Proved it sets only the explicitly listed affected composition (`claude-code`) to `unavailable_outage`; unaffected compositions (`codex`, `cursor`) remain available; proved refusal against marking anything usable or mutating headroom. [measured]

## Stopping-rule verdict

No hard stop fired: no forbidden resource mutation occurred, all endpoints remain reachable, and all negative-authority checks passed. [measured]

The promotion rule cannot fire because it requires at least 30 canonical first-party events across the fixed 30-day window. [asserted] The honest verdict remains **promotion evidence insufficient** (day 1 of 30). [measured]

## Limitations

- The source response proves transport and content type, not that upstream event sets are complete or timely. [measured]
- Cursor's HTML can change structure without an event; whole-page hash detects change but cannot isolate entry-level diffs. [asserted]
- No model inference or provider quota spend was used. [measured]

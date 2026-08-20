# EXP-27 phase A — first-party source probe

Date: 19 August 2026. [measured]

## Result

All six pre-registered first-party release/changelog and status endpoints returned HTTP
200 in 1.3 seconds. [measured] Claude Code and Codex supplied machine-readable release
feeds; Cursor's release surface supplied HTML; all three status sources supplied JSON.
[measured]

The same-commit change-record check passed and rejected every fixture that attempted to
increase headroom, reduce recorded use, move a reset or mark unknown headroom usable.
[measured]

Phase A therefore establishes source reachability and the negative-authority invariant;
it does not measure event recall, latency, re-probe noise or useful decisions changed.
[measured] ADR-0029 remains PROVISIONAL and the 30-day phase has not started. [measured]

## Stopping-rule verdict

No phase-A hard stop fired: no forbidden resource mutation occurred and every fixed source
was reachable. [measured] The promotion rule cannot fire because it requires at least 30
canonical first-party events over 30 days. [asserted] The honest verdict is **phase A
passed; promotion evidence insufficient**. [measured]

## Limitations

- The source response proves transport and content type, not that the upstream event set
  is complete or timely. [measured]
- Cursor's HTML can change structure without an event; its parser risk is not measured by
  this probe. [asserted]
- No model inference, authenticated quota refresh or provider resource state was used.
  [measured]
- Direct checks performed before the scripted run made endpoint availability unsurprising;
  the stopping rules were nevertheless committed before the recorded instrument run.
  [measured]

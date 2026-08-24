#!/bin/bash
# Dispatch publication only once integration has demonstrably completed and every gate is green.
#
# Preconditions are checked by ARTEFACT, never by assuming the integration agent succeeded:
#   * main and the working branch point at the same commit (one branch holds everything)
#   * the full suite passes
#   * all three leak gates pass
#   * nothing else is dispatching
#
# Kill switch: touch .harness/STOP-PUBLISH

cd "C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto" || exit 1
S="C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr/4119b9a5-e07e-43de-bc2f-e873fbd124d2/scratchpad"
B=".harness/dispatch/briefs-2026-08-22"
LOG=".harness/publish-waiter.log"

say() { echo "$(date +%H:%M:%S) $*" >> "$LOG"; }

say "publish waiter started; will not dispatch until integration is verified complete"
deadline=$(( $(date +%s) + 43200 ))   # 12 hours, then stop rather than publish something unverified

while :; do
  if [ -f .harness/STOP-PUBLISH ]; then say "stop file present; exiting without publishing"; exit 0; fi
  if [ "$(date +%s)" -ge "$deadline" ]; then say "deadline reached without verified integration; NOT publishing"; exit 1; fi

  n=$("$S/count_streams.sh" 2>/dev/null); [ -z "$n" ] && n=0
  if [ "$n" -ne 0 ]; then sleep 120; continue; fi

  main_sha=$(git rev-parse main 2>/dev/null)
  wt_sha=$(git rev-parse worktree-consilience-cto 2>/dev/null)
  if [ "$main_sha" != "$wt_sha" ]; then
    say "integration not complete yet (main=$main_sha wt=$wt_sha); holding"
    sleep 120; continue
  fi

  if ! python -m pytest tests/ -q > .harness/publish-suite.txt 2>&1; then
    say "suite RED; refusing to publish. tail: $(tail -1 .harness/publish-suite.txt)"
    sleep 300; continue
  fi

  ok=1
  python .github/scripts/check_foreign_identifiers.py >/dev/null 2>&1 || { say "gate FAIL: foreign identifiers"; ok=0; }
  python .github/scripts/check_private_corpus.py --require-corpora >/dev/null 2>&1 || { say "gate FAIL: private corpus"; ok=0; }
  python .github/scripts/check_secrets.py --history --untracked --self-test >/dev/null 2>&1 || { say "gate FAIL: secrets"; ok=0; }
  if [ "$ok" -ne 1 ]; then say "a leak gate is red; refusing to publish"; sleep 300; continue; fi

  say "all preconditions verified: one branch, suite green ($(tail -1 .harness/publish-suite.txt)), three gates pass"
  say "dispatching publication"
  nohup python scripts/dispatch.py --task-file "$B/publish.md" \
    --harness cursor-composer --model composer-2.5 --allow-exhausted \
    --timeout 3600 --permissions bypass \
    > "$B/publish.out" 2> "$B/publish.err" &
  say "publication dispatched (pid $!); waiter exiting"
  exit 0
done

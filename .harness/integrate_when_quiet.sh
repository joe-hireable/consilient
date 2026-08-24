#!/bin/bash
# Wait for the build to go quiet, then dispatch the integration merge.
#
# "Quiet" means: no dispatcher process alive AND the build loop reports no tick in flight,
# sustained across consecutive checks — a single momentary gap between two units is not
# quiescence. Verified by artefact, never by exit code.
#
# Runs detached under nohup. Kill switch: touch .harness/STOP-INTEGRATION

cd "C:/Users/jpbpr/Repositories/consilience/.claude/worktrees/consilience-cto" || exit 1
S="C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr/4119b9a5-e07e-43de-bc2f-e873fbd124d2/scratchpad"
B=".harness/dispatch/briefs-2026-08-22"
LOG=".harness/integrate-waiter.log"

say() { echo "$(date +%H:%M:%S) $*" >> "$LOG"; }

say "waiter started; holding until the build goes quiet"
quiet_streak=0
deadline=$(( $(date +%s) + 39600 ))   # 11 hours, then give up rather than wait forever

while :; do
  if [ -f .harness/STOP-INTEGRATION ]; then say "stop file present; exiting without merging"; exit 0; fi
  if [ "$(date +%s)" -ge "$deadline" ]; then say "deadline reached with the build still busy; NOT merging"; exit 1; fi

  n=$("$S/count_streams.sh" 2>/dev/null); [ -z "$n" ] && n=0
  inflight=$(python scripts/run_loop.py --name build --status --json 2>/dev/null | grep -o '"in_flight": *true' | wc -l)

  if [ "$n" -eq 0 ] && [ "$inflight" -eq 0 ]; then
    quiet_streak=$((quiet_streak + 1))
  else
    quiet_streak=0
  fi

  # Six consecutive quiet minutes. The driver ticks every five, so this outlasts one full
  # tick gap and will not fire in the pause between two units.
  if [ "$quiet_streak" -ge 6 ]; then
    say "quiet for 6 consecutive checks; stopping the build loop before merging"
    python scripts/run_loop.py --name build --stop >> "$LOG" 2>&1
    sleep 20
    say "dispatching the integration merge"
    nohup python scripts/dispatch.py --task-file "$B/integrate.md" \
      --harness cursor-composer --model kimi-k3-max --allow-exhausted \
      --timeout 3600 --permissions bypass \
      > "$B/integrate.out" 2> "$B/integrate.err" &
    say "integration dispatched (pid $!); waiter exiting"
    exit 0
  fi

  sleep 60
done

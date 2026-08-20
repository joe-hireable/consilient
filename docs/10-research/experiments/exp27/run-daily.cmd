@echo off
REM EXP-27 daily collector wrapper — invoked by the Windows scheduled task
REM "Consilience-EXP27-Collector". Authorised by Joe on 20 August 2026.
REM
REM Why a wrapper and not a bare python call: a scheduled task that fails silently is
REM worse than no scheduled task, because the 30-day window then accumulates missing days
REM while looking healthy. This logs every run, succeeds or fails loudly, and says which
REM checkout it used.

setlocal enabledelayedexpansion

set "WORKTREE=C:\Users\jpbpr\Repositories\consilience\.claude\worktrees\consilience-cto"
set "MAINREPO=C:\Users\jpbpr\Repositories\consilience"
set "REL=docs\10-research\experiments\exp27\collector.py"

REM Prefer the worktree, where the collector currently lives; fall back to the main
REM checkout so this keeps working after the branch is merged and the worktree removed.
set "TARGET="
if exist "%WORKTREE%\%REL%" set "TARGET=%WORKTREE%"
if not defined TARGET if exist "%MAINREPO%\%REL%" set "TARGET=%MAINREPO%"

set "LOGDIR=%MAINREPO%\.harness"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "RUNLOG=%LOGDIR%\exp27-daily.log"

for /f "tokens=* usebackq" %%t in (`powershell -NoProfile -Command "Get-Date -Format o" 2^>nul`) do set "STAMP=%%t"
if not defined STAMP set "STAMP=%DATE% %TIME%"

if not defined TARGET (
  echo [%STAMP%] FAILED: collector.py not found in either checkout. >> "%RUNLOG%"
  echo [%STAMP%]   looked in %WORKTREE%\%REL% >> "%RUNLOG%"
  echo [%STAMP%]   and in %MAINREPO%\%REL% >> "%RUNLOG%"
  echo [%STAMP%]   EXP-27's 30-day window is NOT being collected. >> "%RUNLOG%"
  exit /b 2
)

echo [%STAMP%] running from %TARGET% >> "%RUNLOG%"
pushd "%TARGET%"
python "%TARGET%\%REL%" >> "%RUNLOG%" 2>&1
set "RC=%ERRORLEVEL%"
popd

if not "%RC%"=="0" (
  echo [%STAMP%] collector exited %RC% — one or more sources unreachable. >> "%RUNLOG%"
) else (
  echo [%STAMP%] ok >> "%RUNLOG%"
)
exit /b %RC%

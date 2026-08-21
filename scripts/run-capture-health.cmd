@echo off
REM Daily trajectory capture health check — Gate A condition 3.
REM Invoked by the Windows scheduled task "Consilient-Capture-Health".
REM
REM Why a wrapper: a scheduled task that fails silently is worse than none, because the
REM consecutive-day run then accumulates missing days while the gate looks like it is
REM progressing. That is exactly the state A3 was in before this existed. This logs every
REM run and says which checkout it used.

setlocal enabledelayedexpansion

set "WORKTREE=C:\Users\jpbpr\Repositories\consilience\.claude\worktrees\consilience-cto"
set "MAINREPO=C:\Users\jpbpr\Repositories\consilience"
set "REL=scripts\capture_health.py"

set "TARGET="
if exist "%WORKTREE%\%REL%" set "TARGET=%WORKTREE%"
if not defined TARGET if exist "%MAINREPO%\%REL%" set "TARGET=%MAINREPO%"

set "RUNLOG=%MAINREPO%\.harness\capture-health.log"

for /f "tokens=* usebackq" %%t in (`powershell -NoProfile -Command "Get-Date -Format o" 2^>nul`) do set "STAMP=%%t"
if not defined STAMP set "STAMP=%DATE% %TIME%"

if not defined TARGET (
  echo [%STAMP%] FAILED: capture_health.py not found in either checkout. >> "%RUNLOG%"
  echo [%STAMP%]   Gate A3 has NO evidence source and its run will break on the next quiet day. >> "%RUNLOG%"
  exit /b 2
)

echo [%STAMP%] running from %TARGET% >> "%RUNLOG%"
pushd "%TARGET%"
python "%TARGET%\%REL%" >> "%RUNLOG%" 2>&1
set "RC=%ERRORLEVEL%"
popd

if not "%RC%"=="0" (
  echo [%STAMP%] capture health exited %RC% >> "%RUNLOG%"
) else (
  echo [%STAMP%] ok >> "%RUNLOG%"
)
exit /b %RC%

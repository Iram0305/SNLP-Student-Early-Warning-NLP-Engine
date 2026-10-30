@echo off
REM ---------------------------------------------------------------
REM  Student Early-Warning NLP Engine - stop the local web app
REM ---------------------------------------------------------------
title Student Early-Warning Engine - stop
cd /d "%~dp0"
set "URL=http://127.0.0.1:8765"
set "PIDFILE=webapp\server.pid"

echo.
echo  Stopping the Student Early-Warning Engine...

REM 1) Ask the server politely (same as the Shut down button).
powershell -NoProfile -Command "try { Invoke-RestMethod -Method Post '%URL%/api/shutdown' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo  The server did not answer. It may already be stopped.
) else (
    echo  Shutdown request sent.
)
timeout /t 2 /nobreak >nul

REM 2) If it is somehow still alive, end the process recorded in server.pid.
if not exist "%PIDFILE%" goto done
set /p SERVER_PID=<"%PIDFILE%"
tasklist /FI "PID eq %SERVER_PID%" 2>nul | find /i "python" >nul
if not errorlevel 1 (
    echo  Server process %SERVER_PID% is still running. Ending it...
    taskkill /PID %SERVER_PID% /T /F >nul 2>nul
)
del "%PIDFILE%" >nul 2>nul

:done
echo  The app is stopped.
echo.
timeout /t 3 /nobreak >nul
exit /b 0

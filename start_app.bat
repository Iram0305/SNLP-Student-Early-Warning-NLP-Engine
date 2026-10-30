@echo off
REM ---------------------------------------------------------------
REM  Student Early-Warning NLP Engine - start the local web app
REM  Double-click this file. The app opens at http://127.0.0.1:8765
REM ---------------------------------------------------------------
title Student Early-Warning Engine - launcher
cd /d "%~dp0"
set "URL=http://127.0.0.1:8765"

echo.
echo  Student Early-Warning NLP Engine
echo  ================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo  [X] Python was not found. Install Python 3.10+ and tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM Is the app already running? Then just open the browser.
powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%/api/status' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 (
    echo  The app is already running. Opening your browser...
    start "" "%URL%"
    timeout /t 2 /nobreak >nul
    exit /b 0
)

REM Install packages only if something is missing (first run).
python -c "import importlib.util as u, sys; sys.exit(0 if all(u.find_spec(m) for m in ['fastapi','uvicorn','sentence_transformers','sklearn','pandas','joblib']) else 1)"
if errorlevel 1 (
    echo  [1/3] Installing required Python packages. This happens only once...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo  [X] Package installation failed. See the messages above.
        pause
        exit /b 1
    )
) else (
    echo  [1/3] Python packages found.
)

echo  [2/3] Starting the server in a minimised window...
start "Early-Warning Engine server (close with stop_app.bat)" /min python webapp\server.py

echo  [3/3] Waiting for the server to answer...
for /l %%i in (1,1,60) do (
    powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%/api/status' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
    if not errorlevel 1 goto ready
    timeout /t 1 /nobreak >nul
)
echo  [X] The server did not start within 60 seconds.
echo      Open the minimised "Early-Warning Engine server" window to see the error.
pause
exit /b 1

:ready
echo.
echo  Running at %URL%
echo  The model finishes loading in the background (watch the pill at the top right).
echo  To stop: click "Shut down" in the app, or double-click stop_app.bat.
start "" "%URL%"
timeout /t 4 /nobreak >nul
exit /b 0

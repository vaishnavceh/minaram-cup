@echo off
setlocal enabledelayedexpansion

title MINARAM CUP — Web Platform & API Server
echo ========================================================
echo      MINARAM CUP - ESPORTS WEB PLATFORM & LIVE API
echo ========================================================
echo.

set "PY_CMD="
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py"
    goto :START
)
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :START
)
set "PY_CMD=python"

:START
echo [OK] Using Python: %PY_CMD%
echo.
echo Starting FastAPI Web Server at http://127.0.0.1:8000 ...
echo Public Website: http://localhost:8000/
echo Live Event Stream: http://localhost:8000/api/events
echo Interactive API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C in this terminal window to stop the server.
echo ========================================================
echo.

%PY_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause

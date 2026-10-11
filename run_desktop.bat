@echo off
setlocal enabledelayedexpansion

title MINARAM CUP — Tournament Manager Desktop App
echo ========================================================
echo     MINARAM CUP - DESKTOP TOURNAMENT MANAGER
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
echo Launching desktop application...
%PY_CMD% "%~dp0main.py" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application closed with exit code %ERRORLEVEL%.
    pause
)

@echo off
setlocal enabledelayedexpansion

title MINARAM CUP — 1-Click Cloud Sync
echo ========================================================
echo        MINARAM CUP - CLOUD SYNCHRONIZATION
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
echo [1] Push Local Database to Render Cloud (Publish Changes)
echo [2] Pull Cloud Database to Local Desktop
echo.
set /p ACTION="Choose action [1 or 2] (Default 1): "
if "%ACTION%"=="" set ACTION=1

if "%ACTION%"=="1" (
    %PY_CMD% "%~dp0tools\cloud_sync.py" push
) else (
    %PY_CMD% "%~dp0tools\cloud_sync.py" pull
)

echo.
pause

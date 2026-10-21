@echo off
setlocal
cd /d "%~dp0"

:: Check if py command is available
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py check_matches.py %*
    goto :END
)

:: Check if python command is available
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python check_matches.py %*
    goto :END
)

:: Fallback direct executable
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" check_matches.py %*
    goto :END
)

echo [ERROR] Python not found. Please install Python or ensure it is in your PATH.
pause

:END
if "%~1"=="" (
    echo.
    echo Press any key to exit...
    pause >nul
)

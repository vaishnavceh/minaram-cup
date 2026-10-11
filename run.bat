@echo off
setlocal enabledelayedexpansion

title MINARAM CUP — Elite Tournament Platform
echo ===================================================================
echo               MINARAM CUP - ELITE ESPORTS PLATFORM
echo     Desktop Management Software + Public Live Website + API
echo ===================================================================
echo.

:: Detect Python interpreter
set "PY_CMD="

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py"
    goto :FOUND_PYTHON
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :FOUND_PYTHON
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    goto :FOUND_PYTHON
)

echo [ERROR] No compatible Python 3 installation detected!
pause
exit /b 1

:FOUND_PYTHON
echo [System OK] Python detected: %PY_CMD%
echo.
echo Choose an option to launch:
echo.
echo  [1] Launch Full Platform (Backend API + Live Website + Desktop App)
echo  [2] Launch Desktop Tournament Manager App
echo  [3] Launch Web Server & Public Website (http://localhost:8000)
echo  [4] Run Asset Enhancement Pipeline (Process logos and wallpapers)
echo  [5] Run Full Automated Test Suite (pytest)
echo  [6] Sync Local Desktop Data with Cloud (Render)
echo  [7] Exit
echo.
set /p CHOICE="Enter option [1-7] (Default 1): "

if "%CHOICE%"=="" set CHOICE=1
if "%CHOICE%"=="1" goto :OPT_FULL
if "%CHOICE%"=="2" goto :OPT_DESKTOP
if "%CHOICE%"=="3" goto :OPT_WEB
if "%CHOICE%"=="4" goto :OPT_ASSETS
if "%CHOICE%"=="5" goto :OPT_TESTS
if "%CHOICE%"=="6" goto :OPT_SYNC
if "%CHOICE%"=="7" exit /b 0

echo Invalid choice.
pause
exit /b 1

:OPT_SYNC
echo.
echo ========================================================
echo   MINARAM CUP - CLOUD SYNCHRONIZATION
echo ========================================================
echo.
%PY_CMD% "%~dp0tools\cloud_sync.py" push
echo.
pause
goto :DONE

:OPT_FULL
echo.
echo Launching Web Server in background window...
start "MINARAM CUP - Web Server" "%~dp0start_web.bat"
timeout /t 2 >nul
echo.
echo Starting Desktop Tournament Manager...
%PY_CMD% "%~dp0main.py"
goto :DONE

:OPT_DESKTOP
echo.
echo Starting Desktop Tournament Manager...
%PY_CMD% "%~dp0main.py"
goto :DONE

:OPT_WEB
call "%~dp0start_web.bat"
goto :DONE

:OPT_ASSETS
echo.
echo Running Asset Enhancement Pipeline...
%PY_CMD% "%~dp0tools\asset_pipeline.py"
echo.
pause
goto :DONE

:OPT_TESTS
echo.
echo Running Test Suite...
%PY_CMD% -m pytest -v
echo.
pause
goto :DONE

:DONE
endlocal

@echo off
setlocal
title Project Sekai 2DMV Database - Local Server
set "PORT=8000"

echo.
echo ========================================
echo   Project Sekai 2DMV Database
echo   Local Server Launcher
echo ========================================
echo.

cd /d "%~dp0"
if errorlevel 1 (
    echo Failed to enter project directory:
    echo %~dp0
    pause
    exit /b 1
)

echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python was not found.
    echo Install Python from:
    echo https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is enabled.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting local HTTP server...
echo URL: http://127.0.0.1:%PORT%
echo Press Ctrl+C to stop the server.
echo.

python scripts\build_site.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to build the static site.
    pause
    exit /b 1
)

rem Open the page shortly after the blocking server process starts.
start "" /b powershell.exe -NoProfile -Command "Start-Sleep -Milliseconds 800; Start-Process 'http://127.0.0.1:%PORT%/'" >nul 2>&1

python -m http.server %PORT% --bind 127.0.0.1 --directory dist

pause

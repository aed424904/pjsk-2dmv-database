@echo off
setlocal
title Project Sekai 2DMV Database - Local Server

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
echo URL: http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.

python -m http.server 8000

pause

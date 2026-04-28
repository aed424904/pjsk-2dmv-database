@echo off
setlocal
title Project Sekai 2DMV Database - Local Server

echo.
echo ========================================
echo   Project Sekai 2DMV Database
echo   Local HTTP Server
echo ========================================
echo.
echo Starting local HTTP server...
echo.
echo Server Info:
echo    URL: http://localhost:8000
echo    Port: 8000
echo.
echo Instructions:
echo    1. Keep this window open
echo    2. Open browser and visit: http://localhost:8000
echo    3. Press Ctrl+C to stop server
echo.
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
    echo ERROR: Python not found!
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python environment OK
echo.
echo Server starting...
echo.
echo ========================================
echo   Press Ctrl+C to stop server
echo ========================================
echo.

python -m http.server 8000

pause

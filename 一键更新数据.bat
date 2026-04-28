@echo off
chcp 65001 >nul
echo ========================================
echo   Project Sekai 2DMV Database 数据更新
echo ========================================
echo.
cd /d "%~dp0"
python scripts/auto_update.py
echo.
pause

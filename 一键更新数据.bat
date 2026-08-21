@echo off
setlocal
chcp 65001 >nul
title Project Sekai 2DMV Database - Data Update

echo ========================================
echo   Project Sekai 2DMV Database 数据更新
echo ========================================
echo.

cd /d "%~dp0"
if errorlevel 1 (
    echo 错误：无法进入项目目录：
    echo %~dp0
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python。
    echo 请安装 Python 并勾选 "Add Python to PATH"。
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo 正在抓取、重建并校验数据...
echo.
python scripts/auto_update.py
set "UPDATE_EXIT_CODE=%ERRORLEVEL%"

echo.

if not "%UPDATE_EXIT_CODE%"=="0" (
    echo 数据更新失败，旧版正式数据仍保留在 output 目录中。
    echo 退出码：%UPDATE_EXIT_CODE%
    pause
    exit /b %UPDATE_EXIT_CODE%
)

echo 数据更新并校验成功。
pause
exit /b 0

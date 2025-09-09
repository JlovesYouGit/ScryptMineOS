@echo off
title GPU-ASIC Simple System Test
color 0A

echo ================================================================
echo                   GPU-ASIC SIMPLE SYSTEM TEST
echo              Components Test (Works Around Issues)
echo ================================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

echo 🚀 Testing GPU-ASIC complete system components...
echo.

python SIMPLE_RUN.py

echo.
echo ================================================================
echo                     Testing complete!
echo ================================================================
pause
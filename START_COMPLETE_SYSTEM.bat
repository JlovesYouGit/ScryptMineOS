@echo off
title GPU-ASIC Complete System Launcher
color 0A

echo.
echo ================================================================
echo                GPU-ASIC COMPLETE SYSTEM LAUNCHER
echo    Performance Optimization + Hardware Emulation + Hybrid Layer
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

REM Run the complete system
echo 🚀 Starting complete GPU-ASIC system...
echo.
python run_complete_system.py

echo.
echo ================================================================
echo                     System execution complete
echo ================================================================
pause
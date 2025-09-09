@echo off
title GPU-ASIC Auto Launcher
color 0A

echo ================================================================
echo                     GPU-ASIC AUTO LAUNCHER  
echo          Complete System - No Questions Asked!
echo ================================================================
echo.
echo 🚀 Auto-starting in 2 seconds...
timeout /t 2 /nobreak >nul
echo.

cd /d "%~dp0"
python RUN_AUTO.py

echo.
echo ================================================================
pause
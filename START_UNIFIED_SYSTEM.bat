@echo off
title Unified GPU-ASIC Mining System
color 0A

echo ================================================================
echo              UNIFIED GPU-ASIC MINING SYSTEM
echo            Single Entry Point - No More Individual Components!
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

echo 🚀 Starting Unified GPU-ASIC Mining System...
echo.

echo Choose your operation mode:
echo 1. Quick Start (Educational Mode)
echo 2. Full Performance Mode
echo 3. Production Mode
echo 4. Hardware Emulation Mode
echo 5. Custom Configuration
echo.
choice /c 12345 /m "Select mode"

if %errorlevel% == 1 (
    echo.
    echo 🚀 Starting Quick Start (Educational Mode)...
    python unified_miner.py --mode educational --continuous --monitor
) else if %errorlevel% == 2 (
    echo.
    echo 🚀 Starting Full Performance Mode...
    python unified_miner.py --mode educational --continuous --monitor --optimize-all --hardware-emulation
) else if %errorlevel% == 3 (
    echo.
    echo 🚀 Starting Production Mode...
    python unified_miner.py --mode production --continuous --monitor --optimize-all --hardware-emulation
) else if %errorlevel% == 4 (
    echo.
    echo 🚀 Starting Hardware Emulation Mode...
    python unified_miner.py --mode educational --hardware-emulation --monitor
) else if %errorlevel% == 5 (
    echo.
    echo 🚀 Starting Custom Configuration...
    echo Available options:
    echo   --mode [educational^|production^|testing]  System operation mode
    echo   --continuous                              Start continuous mining
    echo   --monitor                                 Enable system monitoring
    echo   --optimize-all                            Enable all optimizations
    echo   --hardware-emulation                      Enable ASIC hardware emulation
    echo   --status                                 Show system status
    echo.
    echo Example: python unified_miner.py --mode educational --continuous --monitor --optimize-all
    echo.
    set /p CUSTOM_CMD="Enter your custom command: "
    python unified_miner.py %CUSTOM_CMD%
)

echo.
echo ================================================================
echo                    System execution complete
echo ================================================================
pause
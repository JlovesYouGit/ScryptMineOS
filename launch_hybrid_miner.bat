@echo off
REM Enhanced Professional Mining Launcher with GPU-ASIC Hybrid Layer
REM Now supports educational mode for development and testing

echo.
echo ==========================================
echo 🚀 PROFESSIONAL GPU-ASIC HYBRID MINER
echo ==========================================
echo.

echo Available launch modes:
echo.
echo 1. 🎓 EDUCATIONAL MODE (Recommended for testing)
echo    - Bypasses economic safeguards
echo    - Enables GPU-ASIC hybrid layer
echo    - Perfect for development and testing
echo.
echo 2. 🔬 PROFESSIONAL MODE (Production ready)
echo    - Full economic safeguards active
echo    - Requires profitable hashrate
echo    - For real ASIC mining operations
echo.
echo 3. 🧪 HYBRID TEST MODE (Demo only)
echo    - GPU-ASIC emulation demonstration
echo    - Shows external L7 appearance
echo    - API compatibility testing
echo.

set /p choice="Enter your choice (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🎓 Starting EDUCATIONAL MODE...
    echo ✅ Economic safeguards: BYPASSED for development
    echo 🎭 GPU-ASIC hybrid layer: ACTIVE
    echo 💡 Perfect for fleet management development
    echo.
    python runner.py --educational --pool f2pool_global
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo 🔬 Starting PROFESSIONAL MODE...
    echo ⚠️  Economic safeguards: ACTIVE
    echo 💰 Will abort if unprofitable
    echo 🏭 Designed for real ASIC operations
    echo.
    python runner.py --pool f2pool_global
    goto :end
)

if "%choice%"=="3" (
    echo.
    echo 🧪 Starting HYBRID TEST MODE...
    echo 🎭 Pure GPU-ASIC emulation demonstration
    echo 📡 API compatibility: http://localhost:8080
    echo 🔧 Development and testing only
    echo.
    python runner.py --hybrid-test --educational --pool f2pool_global
    goto :end
)

echo Invalid choice. Please run the script again.

:end
echo.
echo Press any key to exit...
pause >nul
@echo off
echo ================================================================
echo    GPU-ASIC Performance Optimization Launcher
echo    Targeting 1.0 MH/J (5x efficiency improvement)
echo ================================================================
echo.
echo Available optimization modes:
echo   1. Complete Roadmap (all optimizations)
echo   2. L2-Cache Kernel Only (+38%% target)
echo   3. Voltage Tuning Only (-60W power)
echo   4. Clock Gating Only (-27W average)
echo   5. Hardware Emulation (ASIC supporting blocks)
echo   6. Complete System (performance + hardware)
echo   7. Educational Mode (bypass economics)
echo   8. Standard Mining (no optimization)
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" (
    echo.
    echo Running complete optimization roadmap...
    echo Target: 1.0 MH/J efficiency achievement
    python runner.py --educational --optimize-performance
) else if "%choice%"=="2" (
    echo.
    echo Applying L2-cache-resident kernel optimization...
    python runner.py --educational --use-l2-kernel
) else if "%choice%"=="3" (
    echo.
    echo Applying voltage-frequency curve optimization...
    python runner.py --educational --voltage-tuning
) else if "%choice%"=="4" (
    echo.
    echo Applying dynamic clock gating optimization...
    python runner.py --educational --clock-gating
) else if "%choice%"=="5" (
    echo.
    echo Starting ASIC hardware emulation layer...
    echo Target: Complete supporting block emulation
    python runner.py --educational --hardware-emulation
) else if "%choice%"=="6" (
    echo.
    echo Starting complete system (performance + hardware)...
    echo Target: Full ASIC emulation with 1.0 MH/J efficiency
    python runner.py --educational --optimize-performance --hardware-emulation
) else if "%choice%"=="7" (
    echo.
    echo Running in educational mode (development/testing)...
    python runner.py --educational
) else if "%choice%"=="8" (
    echo.
    echo Running standard mining (no optimization)...
    python runner.py
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Performance optimization complete!
echo Check the output above for efficiency metrics.
echo ================================================================
pause
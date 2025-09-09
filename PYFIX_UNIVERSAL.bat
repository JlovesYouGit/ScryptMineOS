@echo off
REM Universal Python Code Quality Fixer - Windows Batch Version
REM Implements the "kill-the-chaos" workflow for Windows users
REM This replaces all the separate code quality batch files

setlocal enabledelayedexpansion
set "TARGET_FOLDER=%~1"
if "%TARGET_FOLDER%"=="" set "TARGET_FOLDER=."

echo.
echo ===============================================
echo 🚀 UNIVERSAL PYTHON CODE QUALITY FIXER
echo    Kill the Chaos - One Tool to Rule Them All
echo ===============================================
echo 📁 Target folder: %TARGET_FOLDER%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if our unified pyfix script exists
if not exist "pyfix.py" (
    echo ❌ Error: pyfix.py not found in current directory
    echo Please ensure you're running from the correct directory
    pause
    exit /b 1
)

REM Menu for user selection
echo Select mode:
echo   1. Full Workflow (Format + Lint + Security + Audit + Clean)
echo   2. Format Only (Quick formatting)
echo   3. Security Only (Security scan + dependency audit)
echo   4. Batch Mode (Direct ruff + bandit + pip-audit + pyclean)
echo   5. Exit
echo.
set /p "choice=Enter choice (1-5): "

if "%choice%"=="1" goto full_workflow
if "%choice%"=="2" goto format_only
if "%choice%"=="3" goto security_only
if "%choice%"=="4" goto batch_mode
if "%choice%"=="5" goto exit
echo Invalid choice. Defaulting to full workflow.

:full_workflow
echo 🚀 Running Full Workflow...
python pyfix.py "%TARGET_FOLDER%"
goto done

:format_only
echo 🧽 Running Format-Only Workflow...
python pyfix.py "%TARGET_FOLDER%" --format-only
goto done

:security_only
echo 🛡️ Running Security-Only Workflow...
python pyfix.py "%TARGET_FOLDER%" --security-only
goto done

:batch_mode
echo 🔧 Running Batch Mode (Direct Tool Execution)...
echo.

echo 🧽 FORMAT - Formatting code with ruff...
ruff format "%TARGET_FOLDER%"
ruff check --fix "%TARGET_FOLDER%"

echo.
echo 🔍 LINT - Checking code quality...
ruff check "%TARGET_FOLDER%"

echo.
echo 🛡️ SECURITY - Scanning for security issues...
bandit -r "%TARGET_FOLDER%" -f txt

echo.
echo 📦 DEPENDENCY-AUDIT - Checking for vulnerable packages...
pip-audit --desc --format=json

echo.
echo 🗑️ CACHE-CLEAN - Cleaning Python cache files...
pyclean -v "%TARGET_FOLDER%"

echo.
echo ✅ Batch mode completed!
goto done

:done
echo.
echo ===============================================
echo 🎉 Python Code Quality Check Complete!
echo ===============================================
echo.
echo 💡 Next steps:
echo   - Review any reported issues above
echo   - Commit your changes: git add . && git commit -m "Apply code quality fixes"
echo   - Set up pre-commit hooks: pre-commit install
echo.
echo 📚 Quick reference:
echo   - Format only:    python pyfix.py --format-only
echo   - Security only:  python pyfix.py --security-only
echo   - Quiet mode:     python pyfix.py --quiet
echo   - Help:           python pyfix.py --help
echo.
pause
goto exit

:exit
exit /b 0
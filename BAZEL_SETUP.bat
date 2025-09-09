@echo off
REM Bazel Setup Script for scrypt_doge

echo Setting up Bazel for scrypt_doge project...

REM Check if Bazel is installed
bazel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Bazel is not installed or not in PATH
    echo Please install Bazel from https://docs.bazel.build/versions/main/install.html
    pause
    exit /b 1
)

echo Bazel is installed.

REM Initialize Bazel workspace
echo Initializing Bazel workspace...
bazel info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Failed to initialize Bazel workspace
    pause
    exit /b 1
)

echo Bazel workspace initialized successfully.

REM Try to build the project
echo Building project with Bazel...
bazel build //... >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Build completed with errors. Check BUILD files.
) else (
    echo Project built successfully.
)

echo.
echo Bazel setup completed!
echo.
echo You can now use Bazel commands:
echo   bazel build //...          - Build all targets
echo   bazel run //:runner        - Run the main miner
echo   bazel test //...           - Run all tests
echo.
echo For more information, see BAZEL_USAGE.md
echo.

pause
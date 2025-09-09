@echo off
REM Batch file to set the PAYOUT_ADDR environment variable for Mining OS

echo Mining OS - Set PAYOUT_ADDR Environment Variable
echo =================================================

if "%1"=="" (
    echo Usage: set-payout-addr.bat ^<your_wallet_address^>
    echo.
    echo You must use either:
    echo   1. Your Litecoin address: ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99
    echo   2. Your Dogecoin address: DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd
    echo.
    echo Example:
    echo   set-payout-addr.bat "ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99"
    echo.
    exit /b 1
)

REM Set the PAYOUT_ADDR environment variable
set PAYOUT_ADDR=%1
echo PAYOUT_ADDR has been set to: %PAYOUT_ADDR%

REM Verify the variable is set
echo.
echo Verification:
echo PAYOUT_ADDR = %PAYOUT_ADDR%

echo.
echo You can now start the Mining OS with:
echo   python -m src.mining_os
echo Or use Docker:
echo   docker compose up -d

echo.
echo Note: This environment variable will only be available in the current command prompt session.
echo To make it permanent, you need to set it through System Properties ^> Environment Variables.
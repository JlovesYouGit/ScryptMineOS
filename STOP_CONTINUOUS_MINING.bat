@echo off
echo ========================================
echo   CONTINUOUS MINING - STOP
echo ========================================
echo.
echo Stopping continuous mining...

python start_continuous_mining.py --stop

echo.
echo Checking final status...
python start_continuous_mining.py --status

pause
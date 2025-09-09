@echo off 
cd /d "N:\miner\NBMiner_42.3_Win\scrypt\scrypt_doge\scrypt_doge_refactored\scripts\" 
call venv\Scripts\activate.bat 
python main.py 
echo. 
echo Press any key to exit... 
pause >nul 

@echo off
echo Running runner.py and redirecting output to debug_output.log...
python runner.py > debug_output.log 2>&1
echo Debugging complete. Check debug_output.log for output.

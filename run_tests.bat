@echo off
REM ============================================================================
REM Smart Business Data Assistant - Test Runner
REM ============================================================================
echo Running test suite...
cd /d "%~dp0"
python -m pytest tests/ -v
pause

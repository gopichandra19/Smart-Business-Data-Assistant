@echo off
REM ============================================================================
REM Smart Business Data Assistant - Backend Launcher
REM ============================================================================
echo Starting Smart Business Data Assistant Backend (FastAPI)...
cd /d "%~dp0"
python -m uvicorn apps.api.main:app --reload --port 8000
pause

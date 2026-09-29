@echo off
REM ============================================================================
REM Smart Business Data Assistant - Full Stack Launcher
REM ============================================================================
echo Starting Backend and Frontend simultaneously...

start "Business Assistant - Backend (FastAPI)" cmd /k "cd /d %~dp0 && python -m uvicorn apps.api.main:app --reload --port 8000"
start "Business Assistant - Frontend (Vite)" cmd /k "cd /d %~dp0apps\frontend && npm run dev"

echo.
echo ============================================================================
echo  Backend:  http://localhost:8000 (Docs: http://localhost:8000/docs)
echo  Frontend: http://localhost:5173
echo ============================================================================
echo.
pause

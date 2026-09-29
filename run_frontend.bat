@echo off
REM ============================================================================
REM Smart Business Data Assistant - Frontend Launcher
REM ============================================================================
echo Starting Frontend (React + Vite)...
cd /d "%~dp0apps\frontend"
if not exist node_modules (
    echo Installing node dependencies...
    npm install
)
npm run dev
pause

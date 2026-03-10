@echo off
echo ================================
echo  YabaTech School Manager
echo  Development Mode Launcher
echo ================================
echo.

:: Start Flask backend in background
echo [1/2] Starting Flask backend on http://127.0.0.1:5000 ...
start /b "" python "%~dp0..\run.py"

:: Give Flask a moment to initialize
echo Waiting for Flask to start...
timeout /t 3 /nobreak > nul

:: Start Electron in dev mode
echo [2/2] Launching Electron (dev mode)...
cd /d "%~dp0"
npx electron .

:: When Electron closes, kill the Flask process
echo Shutting down Flask backend...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Flask" 2>nul
echo Application closed.
pause

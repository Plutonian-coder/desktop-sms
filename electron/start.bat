@echo off
echo ================================
echo  YabaTech School Manager
echo  Starting Desktop Application
echo ================================
echo.

:: Start Flask backend in background
echo [1/2] Starting Flask backend...
start /b "Flask" python "%~dp0..\run.py"

:: Give Flask a moment to initialize
timeout /t 2 /nobreak > nul

:: Start Electron
echo [2/2] Launching desktop app...
cd /d "%~dp0"
npx electron .

:: When Electron closes, kill the Flask process
taskkill /f /im python.exe /fi "WINDOWTITLE eq Flask" 2>nul
echo Application closed.

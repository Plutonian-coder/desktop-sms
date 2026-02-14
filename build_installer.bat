@echo off
echo ========================================
echo YabaTech Desktop - Build Application
echo ========================================
echo.

REM Step 1: Install PyInstaller
echo [1/4] Installing PyInstaller...
call .venv\Scripts\pip install pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo.

REM Step 2: Build Flask backend
echo [2/4] Building Flask backend executable...
call .venv\Scripts\pyinstaller flask_app.spec --clean
if %errorlevel% neq 0 (
    echo ERROR: Failed to build backend
    pause
    exit /b 1
)
echo.

REM Step 3: Copy backend to electron resources
echo [3/4] Preparing Electron resources...
if not exist "electron\resources" mkdir "electron\resources"
copy /Y "dist\yabatech_backend.exe" "electron\resources\yabatech_backend.exe"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy backend executable
    pause
    exit /b 1
)
echo.

REM Step 4: Package Electron app (no code signing needed)
echo [4/4] Packaging desktop application...
cd electron
call npx @electron/packager . "YabaTech School Manager" --platform=win32 --arch=x64 --out=dist --overwrite --extra-resource=resources/yabatech_backend.exe
if %errorlevel% neq 0 (
    echo ERROR: Failed to package application
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Application folder: electron\dist\YabaTech School Manager-win32-x64\
echo.
echo To launch: double-click "YabaTech School Manager.exe" inside that folder
echo You can copy the entire folder anywhere and run it!
echo.
pause

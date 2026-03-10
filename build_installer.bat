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

REM Step 2: Build Flask backend (single-folder distribution)
echo [2/4] Building Flask backend...
call .venv\Scripts\pyinstaller flask_app.spec --clean
if %errorlevel% neq 0 (
    echo ERROR: Failed to build backend
    pause
    exit /b 1
)
echo.

REM Step 3: Copy entire backend folder to electron resources
echo [3/4] Preparing Electron resources...
if exist "electron\resources\yabatech_backend" rmdir /s /q "electron\resources\yabatech_backend"
if not exist "electron\resources" mkdir "electron\resources"
xcopy /E /I /Y "dist\yabatech_backend" "electron\resources\yabatech_backend"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy backend folder
    pause
    exit /b 1
)
echo.

REM Step 4: Install Electron dependencies & package the app
echo [4/4] Packaging desktop application...
cd electron
call npm install
call npx @electron/packager . "YabaTech School Manager" --platform=win32 --arch=x64 --out=dist --overwrite --extra-resource=resources/yabatech_backend
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
echo To launch: double-click "YabaTech School Manager.exe" inside that folder.
echo You can copy the entire folder to a USB drive and run it on any Windows PC.
echo.
echo The app runs fully offline - no internet connection required.
echo The local database (school.db) is stored in the data\ folder next to the exe.
echo.
pause

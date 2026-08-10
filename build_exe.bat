@echo off
title Build Kokoro Voice Studio Pro Windows Installer
echo ============================================================
echo   Kokoro Voice Studio Pro - Professional Build Engine
echo   Lead Developer: Dilshan Chandrarathne
echo ============================================================
echo.
cd /d "%~dp0"

echo [1/3] Ensuring PyInstaller is installed...
pip install pyinstaller Pillow --quiet

echo.
echo [2/3] Building Standalone Application Package with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --icon="icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --add-data "icon.ico;." ^
    --add-data "icon.png;." ^
    --name "KokoroVoiceStudio" ^
    app.py

if not exist "dist\KokoroVoiceStudio\KokoroVoiceStudio.exe" (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Compiling Windows Setup Installer with Inno Setup...
set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    "%ISCC_PATH%" installer.iss
    echo.
    echo ============================================================
    echo   BUILD SUCCESSFUL!
    echo   1. Standalone Portable Folder: dist\KokoroVoiceStudio\
    echo   2. Setup Installer Wizard: dist_installer\Kokoro_Voice_Studio_Setup_v2.5.exe
    echo ============================================================
) else (
    echo [NOTE] Inno Setup compiler was not found. 
    echo Standalone portable build is ready in: dist\KokoroVoiceStudio\
)

echo.
pause

@echo off
title Build Kokoro Voice Studio Pro Windows Installer
echo ============================================================
echo   Kokoro Voice Studio Pro - Professional Build Engine
echo   Lead Developer: Dilshan Chandrarathne
echo ============================================================
echo.
cd /d "%~dp0"

echo [1/4] Ensuring PyInstaller & dependencies are ready...
pip install pyinstaller Pillow --quiet

echo.
echo [2/4] Building Standalone Application Package via Spec...
pyinstaller --noconfirm KokoroVoiceStudio.spec

if not exist "dist\KokoroVoiceStudio\KokoroVoiceStudio.exe" (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Mirroring Phonemizer & Linguistic Data Packages...
python -c "import os, shutil, sys, importlib; pkgs = ['language_tags', 'kokoro_onnx', 'espeakng_loader', 'phonemizer', 'segments', 'csvw']; dist_internal = os.path.join('dist', 'KokoroVoiceStudio', '_internal'); [shutil.copytree(os.path.dirname(importlib.import_module(p).__file__), os.path.join(dist_internal, p)) for p in pkgs if (shutil.rmtree(os.path.join(dist_internal, p), ignore_errors=True) or True)]; print('All linguistic and phonemizer assets mirrored 100%!')"

echo.
echo [4/4] Compiling Windows Setup Installer with Inno Setup...
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

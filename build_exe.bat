@echo off
title Build Kokoro Studio Standalone EXE
echo ============================================================
echo   Building Kokoro Voice Studio Standalone Windows EXE
echo ============================================================
cd /d "%~dp0"

echo Installing PyInstaller if needed...
pip install pyinstaller

echo.
echo Packaging application with all model assets and UI styling...
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "assets;assets" ^
    --add-data "core;core" ^
    --name "KokoroVoiceStudio" ^
    app.py

echo.
echo ============================================================
echo   Build complete! Output is inside: dist\KokoroVoiceStudio\
echo ============================================================
pause

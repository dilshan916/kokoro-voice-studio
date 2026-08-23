@echo off
title Kokoro Voice Studio
echo ============================================================
echo   Launching Kokoro Voice Studio Desktop...
cd /d "%~dp0"
python desktop_launcher.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)

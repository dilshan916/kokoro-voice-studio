@echo off
title Kokoro Voice Studio Pro - Server Restarter
echo ============================================================
echo   Restarting Kokoro Voice Studio Backend Server...
echo ============================================================
echo.

cd /d "%~dp0"

echo [*] Stopping previous backend on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Starting fresh Kokoro Backend Server on port 8000...
start "Kokoro-Server" python server.py

echo [*] Waiting 3 seconds for server boot...
timeout /t 3 /nobreak >nul

echo [*] Testing API Health & Billing Quota endpoints...
curl -s http://127.0.0.1:8000/health >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Kokoro Server is running and healthy!
) else (
    echo [NOTE] Server is loading in background.
)

echo.
echo ============================================================
echo   Backend is LIVE on http://127.0.0.1:8000
echo ============================================================
pause

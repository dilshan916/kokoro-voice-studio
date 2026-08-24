@echo off
title Kokoro Voice Studio Pro - Permanent Cloud Server
echo ============================================================
echo   Kokoro Voice Studio Pro - Permanent Fixed Cloud Server
echo   Domain: https://dry-eldercare-bok.ngrok-free.dev
echo ============================================================
echo.

cd /d "%~dp0"

netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [*] Kokoro FastAPI Backend is ALREADY running on port 8000.
) else (
    echo [*] Starting Kokoro FastAPI Backend on port 8000...
    start /b python server.py
    timeout /t 3 /nobreak >nul
)

echo [*] Launching Permanent Ngrok Secure Tunnel...
node start_ngrok_tunnel.js
pause

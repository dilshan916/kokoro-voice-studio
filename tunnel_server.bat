@echo off
title Kokoro Voice Studio Pro - Permanent Cloud Gateway
echo ============================================================
echo   Kokoro Voice Studio Pro - Permanent Cloud Gateway
echo   Fixed Domain: https://kokoro-studio-dilshan.loca.lt
echo ============================================================
echo.
echo [*] Starting Kokoro FastAPI Backend on port 8000...
start /b python server.py
timeout /t 3 /nobreak >nul
echo.
echo [*] Launching Fixed Domain Tunnel...
echo [*] Public URL: https://kokoro-studio-dilshan.loca.lt
echo.
npx -y localtunnel --port 8000 --subdomain kokoro-studio-dilshan
pause

@echo off
title Kokoro Voice Studio Pro - Global Cloud Server
echo ============================================================
echo   Kokoro Voice Studio Pro - Cloudflare HTTPS Gateway
echo ============================================================
echo.
echo [*] Starting Local Kokoro Neural FastAPI Backend...
start /b python server.py
timeout /t 3 /nobreak >nul
echo.
echo [*] Launching Cloudflare Public HTTPS Tunnel...
echo [*] Forwarding port 8000 to public internet...
echo.
.\cloudflared.exe tunnel --url http://127.0.0.1:8000 --no-autoupdate
pause

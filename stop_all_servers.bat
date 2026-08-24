@echo off
title Kokoro Voice Studio Pro - Stop All Servers
echo ============================================================
echo   Stopping Kokoro Server & Ngrok Tunnel Processes...
echo ============================================================
echo.
powershell -Command "Get-Process -Name node, python, cloudflared -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*server.py*' -or $_.CommandLine -like '*ngrok*' -or $_.CommandLine -like '*cloudflared*' } | Stop-Process -Force"
echo [*] All Kokoro background servers and tunnels stopped.
pause

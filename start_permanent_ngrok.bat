@echo off
title Kokoro Voice Studio Pro - Permanent Cloud Server
echo ============================================================
echo   Kokoro Voice Studio Pro - Permanent Cloud Server
echo   Domain: https://dry-eldercare-bok.ngrok-free.dev
echo ============================================================
cd /d "%~dp0"
python start_ngrok.py
pause

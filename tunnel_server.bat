@echo off
title Kokoro Voice Studio - Mobile Tunnel Gateway
echo ============================================================
echo   Kokoro Voice Studio - Mobile HTTPS Tunnel Gateway
echo   Lead Developer: Dilshan Chandrarathne
echo   Public Secure URL: https://kokoro-studio-dilshan.loca.lt
echo ============================================================
echo.
echo [*] Forwarding local port 8000 to https://kokoro-studio-dilshan.loca.lt ...
echo [*] Connect your mobile app instantly with ZERO firewall/hotspot issues!
echo.
npx -y localtunnel --port 8000 --subdomain kokoro-studio-dilshan
pause

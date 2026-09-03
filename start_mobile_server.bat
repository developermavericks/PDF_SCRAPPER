@echo off
title Article PDF Generator Mobile Launcher
echo ========================================================
echo   Launching Android Mobile PDF Generator Service...
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Detecting Local Wi-Fi IP Address...
python get_ip.py

echo [2/3] Starting Backend Server (0.0.0.0:8000)...
start "PDF Generator Server" /B python -m uvicorn server:app --host 0.0.0.0 --port 8000

timeout /t 2 >nul

echo [3/3] Launching Public HTTPS Tunnel...
start "Cloudflare Mobile Tunnel" cmd /k "npx -y cloudflared tunnel --url http://127.0.0.1:8000"

echo.
echo ========================================================
echo   HOW TO CONNECT ON YOUR ANDROID PHONE:
echo.
echo   1. Check the 'Cloudflare Mobile Tunnel' window for your URL.
echo   2. Or open Chrome on Android: http://YOUR_IP:8000
echo ========================================================
echo.
pause

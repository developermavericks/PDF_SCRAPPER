@echo off
title Article PDF Generator Launcher
echo ========================================================
echo   Launching Universal Article PDF Generator Server...
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend Service on http://127.0.0.1:8000 ...
start "Article PDF Generator Server" /B python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

timeout /t 2 >nul

echo [2/2] Opening Web Dashboard UI in your default browser...
start http://127.0.0.1:8000

echo.
echo ========================================================
echo   Server is running! Keep this window open.
echo   Web Dashboard: http://127.0.0.1:8000
echo ========================================================
pause

@echo off
title Lottery Tracker - Server + Auto-Updater
color 0D
echo.
echo ================================================
echo   LOTTERY TRACKER - COMPLETE SYSTEM
echo ================================================
echo.
echo Starting components:
echo   1. Web Server (port 8000)
echo   2. Auto-Updater (every 30 min)
echo.
echo Server will be at: http://localhost:8000
echo.
echo Press Ctrl+C to stop everything
echo.
echo ================================================
echo.

cd /d "%~dp0"

:: Start server in background
start /MIN "Lottery Server" python server.py

:: Wait 3 seconds for server to start
timeout /t 3 /nobreak >nul

:: Start scheduler in this window
python auto_scheduler.py

pause

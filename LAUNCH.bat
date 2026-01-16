@echo off
title Lottery Tracker Server
color 0D
echo.
echo ================================
echo   LOTTERY TRACKER SERVER
echo ================================
echo.
echo Starting server on port 8000...
echo.
echo Open in browser: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ================================
echo.

cd /d "%~dp0"
python server.py

pause

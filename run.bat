@echo off
title FinPilot Launcher
echo ==============================================
echo       Starting FinPilot Application
echo ==============================================

echo [1/2] Starting Backend Server (FastAPI)...
start "FinPilot Backend" cmd /k "cd /d C:\Users\preet\OneDrive\Desktop\AI_Personal_Finance_Management && .\.venv_backend\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Starting Frontend Server (Vite / React)...
start "FinPilot Frontend" cmd /k "cd /d C:\Users\preet\OneDrive\Desktop\AI_Personal_Finance_Management\frontend && npm.cmd run dev"

echo.
echo Both servers are launching in separate windows!
echo Opening browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:5173

echo.
echo Done! Keep the two opened command windows running while using the app.

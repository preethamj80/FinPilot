@echo off
title FinPilot Launcher
echo ===================================================
echo   FinPilot - Launching Full Stack Application
echo ===================================================
echo.
echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000...
start "FinPilot Backend (FastAPI :8000)" powershell -NoExit -ExecutionPolicy Bypass -Command "& '%~dp0start_backend.ps1'"

echo [2/3] Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo [3/3] Starting React Frontend on http://localhost:5173...
start "FinPilot Frontend (React :5173)" powershell -NoExit -ExecutionPolicy Bypass -Command "& '%~dp0start_frontend.ps1'"

timeout /t 2 /nobreak >nul

echo.
echo Opening http://localhost:5173 in default browser...
start http://localhost:5173
echo.
echo FinPilot is running! Keep the backend and frontend terminal windows open.

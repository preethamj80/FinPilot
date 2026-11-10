# start_app.ps1 - Single command launcher for FinPilot
$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "       Launching FinPilot (Full Stack)     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$backendPath = "C:\Users\preet\OneDrive\Desktop\AI_Personal_Finance_Management"
$frontendPath = "C:\Users\preet\OneDrive\Desktop\AI_Personal_Finance_Management\frontend"

# 1. Start Backend in a new window
Write-Host "1. Starting Backend..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k cd /d `"$backendPath`" && .\.venv_backend\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000"

# 2. Start Frontend in a new window
Write-Host "2. Starting Frontend..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k cd /d `"$frontendPath`" && npm.cmd run dev"

# 3. Open browser
Start-Sleep -Seconds 3
Write-Host "3. Opening browser at http://localhost:5173..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host "`nAll set! FinPilot is running." -ForegroundColor Green
Write-Host "Keep the two opened command windows open while using the app." -ForegroundColor Gray

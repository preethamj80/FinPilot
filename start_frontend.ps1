# FinPilot - Start React Frontend Dev Server
# Frontend will be available at http://localhost:5173

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location "$scriptDir\frontend"

Write-Host "Starting FinPilot React frontend..." -ForegroundColor Cyan
Write-Host "   App:  http://localhost:5173" -ForegroundColor Green
Write-Host "   Make sure the backend is running at http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $env:Path = "C:\Program Files\nodejs;" + $env:Path
}

npm run dev

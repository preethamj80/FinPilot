# FinPilot - Start FastAPI Backend
# Backend will be available at http://127.0.0.1:8000
# Swagger API docs at http://127.0.0.1:8000/docs

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location $scriptDir

Write-Host "Starting FinPilot FastAPI backend..." -ForegroundColor Cyan
Write-Host "   API: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""

& "$scriptDir\.venv_backend\Scripts\uvicorn.exe" backend.main:app --host 127.0.0.1 --port 8000 --reload

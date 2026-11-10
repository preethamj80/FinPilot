# FinPilot — Run All Tests
# Runs the complete 89-test suite (30 API + 59 service/ML tests) in one command.

Write-Host "🧪 Running FinPilot complete test suite (89 tests)..." -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

.\.venv_backend\Scripts\python.exe -m pytest tests/ -v -W ignore::DeprecationWarning

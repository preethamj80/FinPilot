# FinPilot — Start Streamlit Fallback UI
# Run this if you want the original Streamlit dashboard (legacy user_id=0 data).

Write-Host "📊 Starting FinPilot Streamlit fallback..." -ForegroundColor Cyan
Write-Host "   App: http://localhost:8501" -ForegroundColor Green
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

.\.venv\Scripts\streamlit.exe run app.py

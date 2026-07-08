$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "HDFC MF AI Assistant - Phase 0 setup" -ForegroundColor Cyan

& "$PSScriptRoot\sync-schemes.ps1"

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

Write-Host "Installing Python dependencies..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Set-Location frontend
    npm install
    Set-Location $ProjectRoot
}

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

if (-not (Test-Path "backend\.env")) {
    Copy-Item backend\.env.example backend\.env
    Write-Host "Created backend\.env from backend\.env.example"
}

if (-not (Test-Path "frontend\.env.local")) {
    Copy-Item frontend\.env.example frontend\.env.local
    Write-Host "Created frontend\.env.local from frontend\.env.example"
}

Write-Host ""
Write-Host "Setup complete. Run scripts\verify-phase0.ps1 to validate." -ForegroundColor Green

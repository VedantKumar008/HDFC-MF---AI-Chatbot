$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Virtual environment not found. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Phase 3 verification" -ForegroundColor Cyan
& $Python scripts\verify_phase3.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Phase 3 exit criteria met." -ForegroundColor Green

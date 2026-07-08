$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Phase 0 verification" -ForegroundColor Cyan

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Virtual environment not found. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/4] Scheme manifest"
& $Python -c "from shared.schemes import load_schemes; schemes = load_schemes(); print(f'  OK: {len(schemes)} approved schemes')"

Write-Host ""
Write-Host "[2/4] Scraper scaffold"
& $Python -m scraper.scraper
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[3/4] Pipeline scaffold"
& $Python -m pipeline.pipeline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[4/4] Frontend dependencies"
if (Test-Path "frontend\node_modules") {
    Write-Host "  OK: frontend node_modules present"
} else {
    Write-Host "  FAIL: run scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Phase 0 exit criteria met." -ForegroundColor Green

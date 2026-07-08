# Verify Phase 4 exit criteria: RAG & LLM Integration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 4 Verification: RAG & LLM Integration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $projectRoot

# Check if backend is running
Write-Host "`nChecking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running. Start it with: .\scripts\run-backend.ps1" -ForegroundColor Red
    exit 1
}

# Run Python verification script
Write-Host "`nRunning Phase 4 verification tests..." -ForegroundColor Yellow
python scripts\verify_phase4.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Phase 4 verification passed!" -ForegroundColor Green
    Write-Host "`nPhase 4 Exit Criteria:" -ForegroundColor Cyan
    Write-Host "  ✅ Factual questions return accurate answers from indexed data"
    Write-Host "  ✅ Responses stream token-by-token via SSE"
    Write-Host "  ✅ Average end-to-end response under 5 seconds"
    Write-Host "  ✅ Vector retrieval under 1 second"
} else {
    Write-Host "`n❌ Phase 4 verification failed" -ForegroundColor Red
    exit 1
}

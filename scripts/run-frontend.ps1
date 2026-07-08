$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location "$ProjectRoot\frontend"

Write-Host "Starting Next.js frontend on http://localhost:3000" -ForegroundColor Cyan
npm run dev

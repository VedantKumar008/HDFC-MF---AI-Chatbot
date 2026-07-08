$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $ProjectRoot "shared\schemes.json"
$Target = Join-Path $ProjectRoot "frontend\lib\schemes-data.json"

Copy-Item $Source $Target -Force
Write-Host "Synced shared\schemes.json -> frontend\lib\schemes-data.json"

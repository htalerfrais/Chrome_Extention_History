# Build script for Chrome Extension History Backend
# Rebuilds the backend Docker image

Write-Host "🔨 Building Chrome Extension History Backend..." -ForegroundColor Green

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "📂 Project root: $projectRoot" -ForegroundColor Yellow

# Build backend image
Write-Host "🐳 Building backend Docker image..." -ForegroundColor Yellow
docker-compose build backend --no-cache

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend built successfully!" -ForegroundColor Green
    Write-Host "🚀 To start services: .\scripts\dev_up.ps1" -ForegroundColor Cyan
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

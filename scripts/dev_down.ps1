# Development shutdown script for Chrome Extension History Backend
# Run this script to stop the backend services

Write-Host "🛑 Stopping Chrome Extension History Backend..." -ForegroundColor Yellow

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "📂 Project root: $projectRoot" -ForegroundColor Yellow

# Stop services
Write-Host "🔄 Stopping services..." -ForegroundColor Yellow
docker-compose down

# Optional: Remove volumes (uncomment if you want to reset data)
# Write-Host "🗑️ Removing volumes..." -ForegroundColor Yellow
# docker-compose down -v

Write-Host "✅ Services stopped successfully!" -ForegroundColor Green
Write-Host "💡 To start again: .\scripts\dev_up.ps1" -ForegroundColor Cyan

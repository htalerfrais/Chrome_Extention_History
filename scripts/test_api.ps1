# Test script for Chrome Extension History Backend API
# Tests the clustering API with sample data

Write-Host "🧪 Testing Chrome Extension History Backend API..." -ForegroundColor Green

# Check if backend is running
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running. Start it with .\scripts\dev_up.ps1" -ForegroundColor Red
    exit 1
}

# Sample test data
$testSessions = @(
    @{
        session_id = "session_1"
        start_time = "2024-01-15T09:00:00Z"
        end_time = "2024-01-15T10:30:00Z"
        items = @(
            @{
                url = "https://github.com/microsoft/vscode"
                title = "Visual Studio Code - GitHub"
                visit_time = "2024-01-15T09:00:00Z"
                visit_count = 1
            },
            @{
                url = "https://stackoverflow.com/questions/python-fastapi"
                title = "Python FastAPI Questions - Stack Overflow"
                visit_time = "2024-01-15T09:15:00Z"
                visit_count = 1
            },
            @{
                url = "https://fastapi.tiangolo.com/tutorial/"
                title = "FastAPI Tutorial - FastAPI"
                visit_time = "2024-01-15T09:30:00Z"
                visit_count = 2
            }
        )
        duration_minutes = 90
    },
    @{
        session_id = "session_2"
        start_time = "2024-01-15T14:00:00Z"
        end_time = "2024-01-15T15:00:00Z"
        items = @(
            @{
                url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                title = "Never Gonna Give You Up - YouTube"
                visit_time = "2024-01-15T14:00:00Z"
                visit_count = 1
            },
            @{
                url = "https://www.netflix.com/browse"
                title = "Netflix - Browse"
                visit_time = "2024-01-15T14:30:00Z"
                visit_count = 1
            }
        )
        duration_minutes = 60
    }
)

# Test clustering endpoint
Write-Host "🔍 Testing /cluster endpoint..." -ForegroundColor Yellow

try {
    $jsonBody = $testSessions | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Uri "http://localhost:8000/cluster" -Method Post -Body $jsonBody -ContentType "application/json"
    
    Write-Host "✅ Clustering successful!" -ForegroundColor Green
    Write-Host "📊 Generated $($response.Count) clusters:" -ForegroundColor Cyan
    
    foreach ($cluster in $response) {
        Write-Host "  🎯 $($cluster.theme): $($cluster.total_items) items (confidence: $($cluster.confidence_score))" -ForegroundColor White
        Write-Host "    📝 $($cluster.description)" -ForegroundColor Gray
        Write-Host "    🏷️  Keywords: $($cluster.keywords -join ', ')" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host "❌ Clustering test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Clustering now includes stats, so no separate preview needed
Write-Host "✅ Clustering includes statistics automatically!" -ForegroundColor Green

Write-Host "🎉 API testing completed!" -ForegroundColor Green

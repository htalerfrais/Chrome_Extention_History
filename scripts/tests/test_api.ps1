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

# Sample test session (single session for /cluster-session endpoint)
$testSession = @{
    session_id = "session_test_1"
    start_time = "2024-01-15T09:00:00Z"
    end_time = "2024-01-15T10:30:00Z"
    items = @(
        @{
            url = "https://github.com/microsoft/vscode"
            title = "Visual Studio Code - GitHub"
            visit_time = "2024-01-15T09:00:00Z"
            url_hostname = "github.com"
            url_pathname_clean = "/microsoft/vscode"
            url_search_query = ""
        },
        @{
            url = "https://stackoverflow.com/questions/python-fastapi"
            title = "Python FastAPI Questions - Stack Overflow"
            visit_time = "2024-01-15T09:15:00Z"
            url_hostname = "stackoverflow.com"
            url_pathname_clean = "/questions/python-fastapi"
            url_search_query = ""
        },
        @{
            url = "https://fastapi.tiangolo.com/tutorial/"
            title = "FastAPI Tutorial - FastAPI"
            visit_time = "2024-01-15T09:30:00Z"
            url_hostname = "fastapi.tiangolo.com"
            url_pathname_clean = "/tutorial"
            url_search_query = ""
        },
        @{
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            title = "Never Gonna Give You Up - YouTube"
            visit_time = "2024-01-15T09:45:00Z"
            url_hostname = "www.youtube.com"
            url_pathname_clean = "/watch"
            url_search_query = "v=dQw4w9WgXcQ"
        },
        @{
            url = "https://www.netflix.com/browse"
            title = "Netflix - Browse"
            visit_time = "2024-01-15T10:00:00Z"
            url_hostname = "www.netflix.com"
            url_pathname_clean = "/browse"
            url_search_query = ""
        }
    )
    duration_minutes = 90
}

# Test clustering endpoint
Write-Host "🔍 Testing /cluster-session endpoint..." -ForegroundColor Yellow

try {
    $jsonBody = $testSession | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Uri "http://localhost:8000/cluster-session" -Method Post -Body $jsonBody -ContentType "application/json"
    
    Write-Host "✅ Clustering successful!" -ForegroundColor Green
    Write-Host "📊 Session: $($response.session_id)" -ForegroundColor Cyan
    Write-Host "⏰ Time range: $($response.session_start_time) → $($response.session_end_time)" -ForegroundColor Cyan
    Write-Host "📊 Generated $($response.clusters.Count) clusters:" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($cluster in $response.clusters) {
        Write-Host "  🎯 Cluster: $($cluster.theme)" -ForegroundColor White
        Write-Host "    📝 Summary: $($cluster.summary)" -ForegroundColor Gray
        Write-Host "    🔗 Items: $($cluster.items.Count)" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host "❌ Clustering test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

Write-Host "🎉 API testing completed!" -ForegroundColor Green

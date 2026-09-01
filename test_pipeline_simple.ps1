# Deep-Guardian Pipeline Test Script

Write-Host ""
Write-Host "=== Deep-Guardian Pipeline Test ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check services
Write-Host "[1/4] Checking services..." -ForegroundColor Yellow
docker-compose ps

# 2. Check NPU Worker
Write-Host "`n[2/4] Checking NPU Worker..." -ForegroundColor Yellow
try {
    $npuHealth = Invoke-RestMethod -Uri "http://localhost:9001/health" -TimeoutSec 5
    if ($npuHealth.model_loaded) {
        Write-Host "  [OK] NPU Worker is running (model loaded)" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] NPU Worker running but model not loaded" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Cannot connect to NPU Worker" -ForegroundColor Red
    Write-Host "  Start NPU Worker: .\start_server.ps1" -ForegroundColor Yellow
}

# 3. Check database
Write-Host "`n[3/4] Checking database..." -ForegroundColor Yellow
docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT COUNT(*) as total, COUNT(CASE WHEN validation_result = true THEN 1 END) as validated FROM potholes;"

# 4. Check test files
Write-Host "`n[4/4] Checking test files..." -ForegroundColor Yellow
$videoDir = "ai-core\videos"
if (Test-Path $videoDir) {
    $files = Get-ChildItem -Path $videoDir -File | Where-Object { 
        $_.Extension -match '\.(jpg|jpeg|png|mp4|avi|mov|mkv)$' 
    }
    if ($files.Count -gt 0) {
        Write-Host "  [OK] Found test files: $($files.Count)" -ForegroundColor Green
        foreach ($file in $files) {
            Write-Host "    - $($file.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [INFO] No test files found" -ForegroundColor Yellow
        Write-Host "  Place test files in: $((Get-Location).Path)\$videoDir\" -ForegroundColor Cyan
    }
} else {
    Write-Host "  [INFO] Video directory not found (will be created automatically)" -ForegroundColor Yellow
}

Write-Host "`n=== Test Ready ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Place test image/video in ai-core\videos\ folder" -ForegroundColor White
Write-Host "2. AI Core will process automatically (check logs: docker-compose logs -f ai-core)" -ForegroundColor White
Write-Host "3. View results in dashboard: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Or manual test:" -ForegroundColor Cyan
Write-Host '  docker-compose exec ai-core python3 test_pipeline.py --image /app/videos/test.jpg' -ForegroundColor White
Write-Host ""

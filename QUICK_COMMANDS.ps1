# Deep-Guardian Quick Commands Script
# Run this script to execute common commands from the TEST directory

# Change to TEST directory
$testDir = "C:\Users\shkim1\Desktop\TEST"
if (Test-Path $testDir) {
    Set-Location $testDir
    Write-Host "Changed to directory: $testDir" -ForegroundColor Green
} else {
    Write-Host "Error: Directory not found: $testDir" -ForegroundColor Red
    exit 1
}

# Command menu
Write-Host "`n=== Deep-Guardian Commands ===" -ForegroundColor Cyan
Write-Host "1. View AI Core logs (real-time)" -ForegroundColor Yellow
Write-Host "2. Connect to database" -ForegroundColor Yellow
Write-Host "3. Run database query (record count)" -ForegroundColor Yellow
Write-Host "4. Check container status" -ForegroundColor Yellow
Write-Host "5. View all container logs" -ForegroundColor Yellow
Write-Host "0. Exit" -ForegroundColor Yellow

$choice = Read-Host "`nSelect (0-5)"

switch ($choice) {
    "1" {
        Write-Host "`nViewing AI Core logs... (Press Ctrl+C to exit)" -ForegroundColor Cyan
        docker-compose logs -f ai-core
    }
    "2" {
        Write-Host "`nConnecting to database... (Type \q to exit)" -ForegroundColor Cyan
        docker-compose exec db psql -U pothole_user -d pothole_db
    }
    "3" {
        Write-Host "`nRunning database query..." -ForegroundColor Cyan
        docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT COUNT(*) as total, COUNT(CASE WHEN validation_result = true THEN 1 END) as validated FROM potholes;"
    }
    "4" {
        Write-Host "`nChecking container status..." -ForegroundColor Cyan
        docker-compose ps
    }
    "5" {
        Write-Host "`nViewing all container logs... (Press Ctrl+C to exit)" -ForegroundColor Cyan
        docker-compose logs -f
    }
    "0" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid selection." -ForegroundColor Red
    }
}

# Deep-Guardian Full System Startup Script

Write-Host "=" * 60
Write-Host "Deep-Guardian Full System Startup"
Write-Host "=" * 60

# 0. Copy YOLOv8 model if needed
Write-Host "`n[0/3] Checking YOLOv8 model..." -ForegroundColor Yellow
$modelPath = ".\ai-core\models\best2.pt"
if (-not (Test-Path $modelPath)) {
    Write-Host "[INFO] YOLOv8 model not found, copying..." -ForegroundColor Yellow
    & ".\copy_model.ps1"
} else {
    Write-Host "[OK] YOLOv8 model found: $modelPath" -ForegroundColor Green
}

# 1. Check NPU Worker
Write-Host "`n[1/3] Checking NPU Worker..." -ForegroundColor Yellow
$npuResponse = $null
try {
    $npuResponse = Invoke-RestMethod -Uri "http://localhost:9001/health" -TimeoutSec 2 -ErrorAction Stop
    if ($npuResponse.model_loaded) {
        Write-Host "[OK] NPU Worker is running (model loaded)" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] NPU Worker is running but model not loaded" -ForegroundColor Yellow
        Write-Host "   Load model: .\load_model_now.ps1" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] NPU Worker is not running" -ForegroundColor Red
    Write-Host "   Please start NPU Worker first: .\start_server.ps1" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# 2. Start Docker Compose
Write-Host "`n[2/3] Starting Docker containers..." -ForegroundColor Yellow

# Check Docker installation
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "[ERROR] Docker is not installed" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker Desktop is running
Write-Host "   Checking Docker Desktop status..." -ForegroundColor Gray
$dockerRunning = $false
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
    }
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "[ERROR] Docker Desktop is not running" -ForegroundColor Red
    Write-Host "`nPlease do the following:" -ForegroundColor Yellow
    Write-Host "  1. Start Docker Desktop application" -ForegroundColor White
    Write-Host "  2. Wait until Docker Desktop is fully started (whale icon in system tray)" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host "`nTo start Docker Desktop:" -ForegroundColor Cyan
    Write-Host "  - Search for 'Docker Desktop' in Start Menu" -ForegroundColor White
    Write-Host "  - Or run: Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" -ForegroundColor White
    
    $startDocker = Read-Host "`nWould you like to try starting Docker Desktop now? (y/n)"
    if ($startDocker -eq "y") {
        $dockerPaths = @(
            "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
            "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
            "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
        )
        
        $found = $false
        foreach ($path in $dockerPaths) {
            if (Test-Path $path) {
                Write-Host "`nStarting Docker Desktop: $path" -ForegroundColor Cyan
                Start-Process $path
                Write-Host "Please wait for Docker Desktop to start, then run this script again." -ForegroundColor Yellow
                $found = $true
                break
            }
        }
        
        if (-not $found) {
            Write-Host "[ERROR] Could not find Docker Desktop executable" -ForegroundColor Red
            Write-Host "   Please start Docker Desktop manually" -ForegroundColor Yellow
        }
    }
    exit 1
}

Write-Host "[OK] Docker Desktop is running" -ForegroundColor Green

# Docker Compose execution
Write-Host "`nStarting Docker Compose..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[3/3] Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "`n[OK] All services started successfully!" -ForegroundColor Green
    Write-Host "`nAccess URLs:" -ForegroundColor Cyan
    Write-Host "  - Web Dashboard: http://localhost" -ForegroundColor White
    Write-Host "  - Streamlit (direct): http://localhost:8501" -ForegroundColor White
    Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
    Write-Host "`nView logs:" -ForegroundColor Cyan
    Write-Host "  docker-compose logs -f" -ForegroundColor White
    Write-Host "`nStop services:" -ForegroundColor Cyan
    Write-Host "  docker-compose stop" -ForegroundColor White
} else {
    Write-Host "`n[ERROR] Docker Compose startup failed" -ForegroundColor Red
    Write-Host "   Check logs: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n" + ("=" * 60)


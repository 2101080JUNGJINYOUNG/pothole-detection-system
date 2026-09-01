# Check Docker Desktop Status

Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan

# Check if Docker command exists
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "[ERROR] Docker is not installed" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop from:" -ForegroundColor Yellow
    Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor White
    exit 1
}

# Check if Docker Desktop is running
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker Desktop is running" -ForegroundColor Green
        Write-Host "`nDocker version:" -ForegroundColor Cyan
        docker --version
        exit 0
    } else {
        throw "Docker not running"
    }
} catch {
    Write-Host "[ERROR] Docker Desktop is not running" -ForegroundColor Red
    Write-Host "`nPlease start Docker Desktop:" -ForegroundColor Yellow
    Write-Host "  1. Search for 'Docker Desktop' in Start Menu" -ForegroundColor White
    Write-Host "  2. Wait until Docker Desktop is fully started" -ForegroundColor White
    Write-Host "  3. Look for the Docker whale icon in system tray" -ForegroundColor White
    
    # Try to find and start Docker Desktop
    $dockerPaths = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )
    
    Write-Host "`nAttempting to start Docker Desktop..." -ForegroundColor Cyan
    $found = $false
    foreach ($path in $dockerPaths) {
        if (Test-Path $path) {
            Write-Host "  Found: $path" -ForegroundColor Green
            Start-Process $path
            Write-Host "`n[INFO] Docker Desktop is starting..." -ForegroundColor Yellow
            Write-Host "  Please wait 30-60 seconds for it to fully start" -ForegroundColor Yellow
            Write-Host "  Then run this script again to verify" -ForegroundColor Yellow
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "[ERROR] Could not find Docker Desktop executable" -ForegroundColor Red
        Write-Host "  Please start Docker Desktop manually" -ForegroundColor Yellow
    }
    
    exit 1
}





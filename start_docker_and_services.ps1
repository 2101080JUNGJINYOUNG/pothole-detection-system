# Deep-Guardian 프로젝트 전체 시작 스크립트

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deep-Guardian 프로젝트 시작" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Docker Desktop 확인 및 시작
Write-Host "[1] Docker Desktop 확인 중..." -ForegroundColor Yellow
$dockerRunning = $false

try {
    $dockerInfo = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker Desktop 실행 중" -ForegroundColor Green
        $dockerRunning = $true
    }
} catch {
    Write-Host "  [INFO] Docker Desktop 실행 안 됨" -ForegroundColor Yellow
}

if (-not $dockerRunning) {
    Write-Host "  Docker Desktop 시작 중..." -ForegroundColor Cyan
    $dockerPaths = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )
    
    $found = $false
    foreach ($path in $dockerPaths) {
        if (Test-Path $path) {
            Start-Process $path
            Write-Host "  [OK] Docker Desktop 시작됨: $path" -ForegroundColor Green
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "  [ERROR] Docker Desktop 실행 파일을 찾을 수 없습니다" -ForegroundColor Red
        Write-Host "  수동으로 Docker Desktop을 시작해주세요" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "`n  Docker Desktop이 완전히 시작될 때까지 대기 중..." -ForegroundColor Yellow
    Write-Host "  (보통 30-60초 소요)" -ForegroundColor Gray
    
    $maxWait = 120  # 최대 2분 대기
    $waited = 0
    $interval = 5   # 5초마다 확인
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds $interval
        $waited += $interval
        
        try {
            $dockerInfo = docker info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Docker Desktop 준비 완료! ($waited 초 경과)" -ForegroundColor Green
                $dockerRunning = $true
                break
            }
        } catch {
            # 계속 대기
        }
        
        Write-Host "  대기 중... ($waited 초)" -ForegroundColor Gray
    }
    
    if (-not $dockerRunning) {
        Write-Host "  [WARN] Docker Desktop 시작 시간 초과" -ForegroundColor Yellow
        Write-Host "  수동으로 Docker Desktop이 완전히 시작되었는지 확인 후 다시 시도하세요" -ForegroundColor Yellow
        exit 1
    }
}

# 2. Docker 컨테이너 시작
Write-Host "`n[2] Docker 컨테이너 시작 중..." -ForegroundColor Yellow
Write-Host "  docker-compose up -d 실행..." -ForegroundColor Cyan

try {
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker 컨테이너 시작 완료" -ForegroundColor Green
        
        # 컨테이너 상태 확인
        Start-Sleep -Seconds 3
        Write-Host "`n  컨테이너 상태:" -ForegroundColor Cyan
        docker-compose ps
    } else {
        Write-Host "  [ERROR] Docker 컨테이너 시작 실패" -ForegroundColor Red
        Write-Host "  로그 확인: docker-compose logs" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "  [ERROR] Docker Compose 실행 오류: $_" -ForegroundColor Red
    exit 1
}

# 3. NPU Worker 시작 안내
Write-Host "`n[3] NPU Worker 시작 안내" -ForegroundColor Yellow
Write-Host "  NPU Worker는 별도 PowerShell 터미널에서 실행해야 합니다:" -ForegroundColor Cyan
Write-Host "  .\start_npu_worker.ps1" -ForegroundColor White
Write-Host "`n  또는 수동으로:" -ForegroundColor Gray
Write-Host "  & `$env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  python npu_worker.py --model `"C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml`" --device `"AUTO:NPU,GPU,CPU`" --port 9001" -ForegroundColor Gray

# 4. 서비스 접근 정보
Write-Host "`n[4] 서비스 접근 정보" -ForegroundColor Yellow
Write-Host "  대시보드 (Nginx): http://localhost" -ForegroundColor Cyan
Write-Host "  대시보드 (직접): http://localhost:8501" -ForegroundColor Cyan
Write-Host "  NPU Worker: http://localhost:9001/health" -ForegroundColor Cyan

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "시작 완료!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "  1. NPU Worker를 별도 터미널에서 시작하세요" -ForegroundColor White
Write-Host "  2. 브라우저에서 http://localhost 접속하여 대시보드 확인" -ForegroundColor White
Write-Host ""






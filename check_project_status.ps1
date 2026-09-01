# Deep-Guardian 프로젝트 상태 점검 스크립트

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deep-Guardian 프로젝트 상태 점검" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$allChecks = @()

# 1. Docker Desktop 상태 확인
Write-Host "[1] Docker Desktop 상태 확인..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker Desktop 실행 중" -ForegroundColor Green
        $allChecks += @{Name="Docker Desktop"; Status="OK"}
    } else {
        throw "Docker not running"
    }
} catch {
    Write-Host "  [ERROR] Docker Desktop 실행 안 됨" -ForegroundColor Red
    Write-Host "    → Docker Desktop을 시작해주세요" -ForegroundColor Yellow
    $allChecks += @{Name="Docker Desktop"; Status="ERROR"}
}

# 2. Docker 컨테이너 상태 확인
Write-Host "`n[2] Docker 컨테이너 상태 확인..." -ForegroundColor Yellow
try {
    $containers = docker-compose ps 2>&1
    if ($LASTEXITCODE -eq 0 -and $containers -notmatch "error") {
        Write-Host "  [OK] Docker Compose 정상" -ForegroundColor Green
        $containerList = docker-compose ps --format json | ConvertFrom-Json
        if ($containerList.Count -gt 0) {
            Write-Host "  실행 중인 컨테이너:" -ForegroundColor Cyan
            foreach ($container in $containerList) {
                $status = if ($container.State -eq "running") { "OK" } else { "STOPPED" }
                $color = if ($status -eq "OK") { "Green" } else { "Red" }
                Write-Host "    - $($container.Name): $($container.State)" -ForegroundColor $color
                $allChecks += @{Name="Container: $($container.Name)"; Status=$status}
            }
        } else {
            Write-Host "  [WARN] 실행 중인 컨테이너 없음" -ForegroundColor Yellow
            Write-Host "    → docker-compose up -d 실행 필요" -ForegroundColor Yellow
            $allChecks += @{Name="Docker Containers"; Status="WARN"}
        }
    } else {
        Write-Host "  [ERROR] Docker Compose 오류" -ForegroundColor Red
        $allChecks += @{Name="Docker Compose"; Status="ERROR"}
    }
} catch {
    Write-Host "  [ERROR] Docker Compose 확인 실패" -ForegroundColor Red
    $allChecks += @{Name="Docker Compose"; Status="ERROR"}
}

# 3. NPU Worker 상태 확인
Write-Host "`n[3] NPU Worker 상태 확인..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:9001/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  [OK] NPU Worker 실행 중 (포트 9001)" -ForegroundColor Green
    Write-Host "    상태: $($response.status)" -ForegroundColor Cyan
    $allChecks += @{Name="NPU Worker"; Status="OK"}
} catch {
    $portCheck = Get-NetTCPConnection -LocalPort 9001 -ErrorAction SilentlyContinue
    if ($portCheck) {
        Write-Host "  [WARN] 포트 9001 사용 중이지만 응답 없음" -ForegroundColor Yellow
        $allChecks += @{Name="NPU Worker"; Status="WARN"}
    } else {
        Write-Host "  [ERROR] NPU Worker 실행 안 됨 (포트 9001)" -ForegroundColor Red
        Write-Host "    → start_npu_worker.ps1 실행 필요" -ForegroundColor Yellow
        $allChecks += @{Name="NPU Worker"; Status="ERROR"}
    }
}

# 4. 필수 파일 확인
Write-Host "`n[4] 필수 파일 확인..." -ForegroundColor Yellow
$requiredFiles = @(
    @{Path='docker-compose.yml'; Name='Docker Compose 설정'},
    @{Path='ai-core\main.py'; Name='AI Core 메인'},
    @{Path='ai-core\models\best2.pt'; Name='YOLOv8 모델'},
    @{Path='dashboard\app.py'; Name='Dashboard 앱'},
    @{Path='npu_worker.py'; Name='NPU Worker'},
    @{Path='database\init.sql'; Name='DB 초기화 스크립트'},
    @{Path='start_npu_worker.ps1'; Name='NPU Worker 시작 스크립트'}
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file.Path) {
        Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
        $allChecks += @{Name="File: $($file.Name)"; Status="OK"}
    } else {
        Write-Host "  [ERROR] $($file.Name) 없음: $($file.Path)" -ForegroundColor Red
        $allChecks += @{Name="File: $($file.Name)"; Status="ERROR"}
    }
}

# 5. OpenVINO 모델 확인
Write-Host "`n[5] OpenVINO 모델 확인..." -ForegroundColor Yellow
$modelPath = "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"
if (Test-Path $modelPath) {
    Write-Host "  [OK] OpenVINO 모델 파일 존재" -ForegroundColor Green
    $allChecks += @{Name="OpenVINO Model"; Status="OK"}
} else {
    Write-Host "  [WARN] OpenVINO 모델 파일 없음" -ForegroundColor Yellow
    Write-Host "    경로: $modelPath" -ForegroundColor Gray
    $allChecks += @{Name="OpenVINO Model"; Status="WARN"}
}

# 6. 가상환경 확인
Write-Host "`n[6] 가상환경 확인..." -ForegroundColor Yellow
$venvPath = "$env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "  [OK] 가상환경 존재" -ForegroundColor Green
    $allChecks += @{Name="Python Virtual Environment"; Status="OK"}
} else {
    Write-Host "  [WARN] 가상환경 없음" -ForegroundColor Yellow
    Write-Host "    경로: $venvPath" -ForegroundColor Gray
    $allChecks += @{Name="Python Virtual Environment"; Status="WARN"}
}

# 7. 서비스 접근 확인
Write-Host "`n[7] 서비스 접근 확인..." -ForegroundColor Yellow
$services = @(
    @{Url='http://localhost'; Name='대시보드 (Nginx)'},
    @{Url='http://localhost:8501'; Name='대시보드 (직접)'},
    @{Url='http://localhost:9001/health'; Name='NPU Worker'}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -Method Get -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  [OK] $($service.Name) 접근 가능" -ForegroundColor Green
        $allChecks += @{Name="Service: $($service.Name)"; Status="OK"}
    } catch {
        Write-Host "  [ERROR] $($service.Name) 접근 불가" -ForegroundColor Red
        $allChecks += @{Name="Service: $($service.Name)"; Status="ERROR"}
    }
}

# 요약
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "점검 결과 요약" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$okCount = ($allChecks | Where-Object { $_.Status -eq "OK" }).Count
$warnCount = ($allChecks | Where-Object { $_.Status -eq "WARN" }).Count
$errorCount = ($allChecks | Where-Object { $_.Status -eq "ERROR" }).Count

Write-Host "정상: $okCount" -ForegroundColor Green
Write-Host "경고: $warnCount" -ForegroundColor Yellow
Write-Host "오류: $errorCount" -ForegroundColor Red

if ($errorCount -eq 0 -and $warnCount -eq 0) {
    Write-Host "`n[결과] 프로젝트가 정상적으로 동작 중입니다! ✅" -ForegroundColor Green
} elseif ($errorCount -eq 0) {
    Write-Host "`n[결과] 프로젝트가 대체로 정상이지만 일부 경고가 있습니다. ⚠️" -ForegroundColor Yellow
} else {
    Write-Host "`n[결과] 프로젝트에 문제가 있습니다. 위의 오류를 확인하세요. ❌" -ForegroundColor Red
    Write-Host "`n권장 조치사항:" -ForegroundColor Yellow
    if ($allChecks | Where-Object { $_.Name -eq "Docker Desktop" -and $_.Status -eq "ERROR" }) {
        Write-Host "  1. Docker Desktop을 시작하세요" -ForegroundColor White
    }
    if ($allChecks | Where-Object { $_.Name -like "Container:*" -and $_.Status -ne "OK" }) {
        Write-Host "  2. docker-compose up -d 실행" -ForegroundColor White
    }
    if ($allChecks | Where-Object { $_.Name -eq "NPU Worker" -and $_.Status -eq "ERROR" }) {
        Write-Host "  3. start_npu_worker.ps1 실행" -ForegroundColor White
    }
}

Write-Host ""


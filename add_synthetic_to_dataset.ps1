# 파인튜닝 데이터셋에 합성 포트홀 추가 스크립트 (PowerShell)
# 사용법: .\add_synthetic_to_dataset.ps1

param(
    [string]$RoadImages = "/app/shared_images/detections",
    [string]$DatasetDir = "/app/models/finetune_dataset",
    [int]$NumPotholes = 1
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "파인튜닝 데이터셋에 합성 포트홀 추가" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

Write-Host "도로 이미지 디렉토리: $RoadImages" -ForegroundColor Yellow
Write-Host "데이터셋 디렉토리: $DatasetDir" -ForegroundColor Yellow
Write-Host "이미지당 포트홀 개수: $NumPotholes" -ForegroundColor Yellow
Write-Host ""

# Docker 컨테이너 확인 및 대기
$containerName = "deep-guardian-ai"
$maxWaitTime = 60  # 최대 대기 시간 (초)
$waitInterval = 2  # 대기 간격 (초)
$elapsed = 0

Write-Host "Docker 컨테이너 상태 확인 중..." -ForegroundColor Yellow

while ($elapsed -lt $maxWaitTime) {
    $containerStatus = docker inspect -f '{{.State.Status}}' $containerName 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        if ($containerStatus -eq "running") {
            Write-Host "컨테이너가 실행 중입니다." -ForegroundColor Green
            break
        } elseif ($containerStatus -eq "restarting") {
            Write-Host "컨테이너가 재시작 중입니다... ($elapsed/$maxWaitTime 초)" -ForegroundColor Yellow
            Start-Sleep -Seconds $waitInterval
            $elapsed += $waitInterval
        } else {
            Write-Host "컨테이너 상태: $containerStatus. 시작 중..." -ForegroundColor Yellow
            docker-compose start ai-core 2>$null
            Start-Sleep -Seconds $waitInterval
            $elapsed += $waitInterval
        }
    } else {
        Write-Host "컨테이너를 찾을 수 없습니다. 시작 중..." -ForegroundColor Yellow
        docker-compose up -d ai-core 2>$null
        Start-Sleep -Seconds $waitInterval
        $elapsed += $waitInterval
    }
}

# 최종 상태 확인
$finalStatus = docker inspect -f '{{.State.Status}}' $containerName 2>$null
if ($finalStatus -ne "running") {
    Write-Host "오류: 컨테이너를 실행할 수 없습니다. (상태: $finalStatus)" -ForegroundColor Red
    Write-Host "다음 명령으로 컨테이너를 시작하세요: docker-compose up -d ai-core" -ForegroundColor Yellow
    exit 1
}

Write-Host "Docker 컨테이너에서 합성 데이터 추가 중..." -ForegroundColor Green
Write-Host ""

# 명령어 실행
docker exec $containerName python /app/add_synthetic_potholes.py `
    --road_images $RoadImages `
    --dataset_dir $DatasetDir `
    --num_potholes $NumPotholes

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "합성 데이터 추가 완료!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "오류 발생! (종료 코드: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}


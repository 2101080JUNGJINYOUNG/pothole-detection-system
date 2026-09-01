# Docker Desktop 준비 대기 스크립트

Write-Host "Docker Desktop 준비 대기 중..." -ForegroundColor Cyan

$maxWait = 120  # 최대 2분
$waited = 0
$interval = 5   # 5초마다 확인

while ($waited -lt $maxWait) {
    try {
        $dockerInfo = docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Docker Desktop 준비 완료! ($waited 초 경과)" -ForegroundColor Green
            Write-Host "이제 docker-compose up -d 를 실행할 수 있습니다." -ForegroundColor Cyan
            exit 0
        }
    } catch {
        # 계속 대기
    }
    
    Start-Sleep -Seconds $interval
    $waited += $interval
    Write-Host "." -NoNewline -ForegroundColor Gray
}

Write-Host "`n[WARN] Docker Desktop 시작 시간 초과" -ForegroundColor Yellow
Write-Host "수동으로 Docker Desktop이 완전히 시작되었는지 확인하세요" -ForegroundColor Yellow
exit 1






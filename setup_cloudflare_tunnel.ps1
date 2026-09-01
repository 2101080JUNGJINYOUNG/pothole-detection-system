# Cloudflare Tunnel 설정 스크립트
# Deep-Guardian 프로젝트용

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Tunnel 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Cloudflare 계정 확인
Write-Host "[1/5] Cloudflare 계정 확인" -ForegroundColor Yellow
Write-Host "Cloudflare 계정이 필요합니다. 계정이 없으면 https://dash.cloudflare.com 에서 생성하세요."
$continue = Read-Host "Cloudflare 계정이 있으신가요? (y/n)"
if ($continue -ne "y") {
    Write-Host "Cloudflare 계정을 생성한 후 다시 실행해주세요." -ForegroundColor Red
    exit 1
}

# 2. Cloudflared 설치 확인
Write-Host "`n[2/5] Cloudflared 설치 확인" -ForegroundColor Yellow
$cloudflaredInstalled = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredInstalled) {
    Write-Host "Cloudflared가 설치되어 있지 않습니다." -ForegroundColor Yellow
    Write-Host "다음 방법 중 하나로 설치하세요:" -ForegroundColor Yellow
    Write-Host "1. Chocolatey: choco install cloudflared" -ForegroundColor Cyan
    Write-Host "2. Scoop: scoop install cloudflared" -ForegroundColor Cyan
    Write-Host "3. 수동 다운로드: https://github.com/cloudflare/cloudflared/releases" -ForegroundColor Cyan
    $install = Read-Host "`n설치를 진행하시겠습니까? (y/n)"
    if ($install -eq "y") {
        Write-Host "Chocolatey를 사용하여 설치합니다..." -ForegroundColor Yellow
        choco install cloudflared -y
        if ($LASTEXITCODE -ne 0) {
            Write-Host "설치 실패. 수동으로 설치해주세요." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Cloudflared를 먼저 설치한 후 다시 실행해주세요." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Cloudflared가 설치되어 있습니다." -ForegroundColor Green
}

# 3. Cloudflare 로그인
Write-Host "`n[3/5] Cloudflare 로그인" -ForegroundColor Yellow
Write-Host "브라우저가 열리면 Cloudflare에 로그인하세요." -ForegroundColor Yellow
cloudflared tunnel login
if ($LASTEXITCODE -ne 0) {
    Write-Host "로그인 실패. 다시 시도해주세요." -ForegroundColor Red
    exit 1
}

# 4. 터널 생성
Write-Host "`n[4/5] 터널 생성" -ForegroundColor Yellow
$tunnelName = "deep-guardian-tunnel"
Write-Host "터널 이름: $tunnelName" -ForegroundColor Cyan
cloudflared tunnel create $tunnelName
if ($LASTEXITCODE -ne 0) {
    Write-Host "터널 생성 실패. 이미 존재할 수 있습니다." -ForegroundColor Yellow
    $useExisting = Read-Host "기존 터널을 사용하시겠습니까? (y/n)"
    if ($useExisting -ne "y") {
        exit 1
    }
}

# 5. Credentials 파일 복사
Write-Host "`n[5/5] Credentials 파일 복사" -ForegroundColor Yellow

# 터널 목록에서 UUID 가져오기
$tunnelList = cloudflared tunnel list 2>&1
$tunnelUuid = $null

if ($tunnelList -match $tunnelName) {
    # 터널 목록에서 UUID 추출
    $tunnelLine = $tunnelList | Select-String $tunnelName
    if ($tunnelLine) {
        $parts = $tunnelLine.ToString().Split() | Where-Object { $_ -match '^[a-f0-9-]{36}$' }
        if ($parts) {
            $tunnelUuid = $parts[0]
        }
    }
}

if ($tunnelUuid) {
    $credentialsPath = "$env:USERPROFILE\.cloudflared\$tunnelUuid.json"
    $targetPath = ".\cloudflared\credentials.json"
    
    if (Test-Path $credentialsPath) {
        Copy-Item $credentialsPath $targetPath -Force
        Write-Host "✓ Credentials 파일이 복사되었습니다: $targetPath" -ForegroundColor Green
        Write-Host "  터널 UUID: $tunnelUuid" -ForegroundColor Cyan
    } else {
        Write-Host "Credentials 파일을 찾을 수 없습니다: $credentialsPath" -ForegroundColor Red
        Write-Host "수동으로 다음 경로에서 파일을 찾아 cloudflared/credentials.json으로 복사하세요:" -ForegroundColor Yellow
        Write-Host "$env:USERPROFILE\.cloudflared\" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "터널 UUID를 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "터널이 제대로 생성되었는지 확인하세요:" -ForegroundColor Yellow
    Write-Host "  cloudflared tunnel list" -ForegroundColor Cyan
    exit 1
}

# 6. DNS 라우팅 설정 안내
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "다음 단계: DNS 라우팅 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cloudflare 대시보드에서 다음 DNS 레코드를 추가하세요:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. CNAME 레코드 추가:" -ForegroundColor Cyan
Write-Host "   이름: deep-guardian (또는 원하는 서브도메인)" -ForegroundColor White
Write-Host "   대상: [터널 UUID].cfargotunnel.com" -ForegroundColor White
Write-Host "   프록시: 활성화 (주황색 구름)" -ForegroundColor White
Write-Host ""
Write-Host "2. 또는 다음 명령으로 자동 설정:" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel route dns $tunnelName deep-guardian.your-domain.com" -ForegroundColor White
Write-Host ""
Write-Host "3. config.yml 파일에서 도메인을 수정하세요:" -ForegroundColor Yellow
Write-Host "   - deep-guardian.your-domain.com -> 실제 도메인으로 변경" -ForegroundColor White
Write-Host ""
Write-Host "설정 완료 후 다음 명령으로 터널을 시작하세요:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d cloudflared" -ForegroundColor Cyan
Write-Host ""


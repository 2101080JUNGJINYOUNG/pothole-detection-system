# Cloudflare Tunnel 설정 수정 스크립트
# Origin Certificate 문제 해결

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Tunnel 설정 수정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Origin Certificate 다운로드
Write-Host "[1/3] Origin Certificate 다운로드" -ForegroundColor Yellow
Write-Host ""
Write-Host "다음 단계를 따라주세요:" -ForegroundColor Yellow
Write-Host "1. 브라우저에서 다음 URL 열기:" -ForegroundColor Cyan
Write-Host "   https://one.dash.cloudflare.com/" -ForegroundColor White
Write-Host ""
Write-Host "2. Networks > Tunnels 메뉴로 이동" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. 'Create a tunnel' 클릭 또는 기존 터널 선택" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. 'Configure' 탭에서 'Download a certificate' 클릭" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. 다운로드한 cert.pem 파일을 다음 위치에 저장:" -ForegroundColor Cyan
Write-Host "   $env:USERPROFILE\.cloudflared\cert.pem" -ForegroundColor White
Write-Host ""

$certPath = "$env:USERPROFILE\.cloudflared\cert.pem"
if (Test-Path $certPath) {
    Write-Host "✓ Origin Certificate가 이미 있습니다: $certPath" -ForegroundColor Green
} else {
    $continue = Read-Host "Origin Certificate를 다운로드하셨나요? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Origin Certificate를 다운로드한 후 다시 실행해주세요." -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $certPath)) {
        Write-Host "cert.pem 파일을 찾을 수 없습니다." -ForegroundColor Red
        Write-Host "다운로드한 파일을 다음 위치에 복사해주세요:" -ForegroundColor Yellow
        Write-Host "  $certPath" -ForegroundColor Cyan
        exit 1
    }
}

# 2. 터널 생성 (origin certificate 사용)
Write-Host "`n[2/3] 터널 생성" -ForegroundColor Yellow
$tunnelName = "deep-guardian-tunnel"

# 기존 터널 확인
$existingTunnels = cloudflared tunnel list 2>&1
if ($existingTunnels -match $tunnelName) {
    Write-Host "터널 '$tunnelName'이 이미 존재합니다." -ForegroundColor Yellow
    $recreate = Read-Host "기존 터널을 삭제하고 새로 만들까요? (y/n)"
    if ($recreate -eq "y") {
        cloudflared tunnel delete $tunnelName
        Write-Host "기존 터널이 삭제되었습니다." -ForegroundColor Green
    }
}

# 터널 생성 (origin certificate 경로 지정)
$env:TUNNEL_ORIGIN_CERT = $certPath
cloudflared tunnel create $tunnelName
if ($LASTEXITCODE -ne 0) {
    Write-Host "터널 생성 실패. origin certificate 경로를 확인해주세요." -ForegroundColor Red
    exit 1
}

Write-Host "✓ 터널이 생성되었습니다: $tunnelName" -ForegroundColor Green

# 3. Credentials 파일 복사
Write-Host "`n[3/3] Credentials 파일 복사" -ForegroundColor Yellow

# 터널 목록에서 UUID 가져오기
$tunnelList = cloudflared tunnel list 2>&1
$tunnelUuid = $null

if ($tunnelList -match $tunnelName) {
    $tunnelLines = $tunnelList | Select-String $tunnelName
    foreach ($line in $tunnelLines) {
        $parts = $line.ToString().Split() | Where-Object { $_ -match '^[a-f0-9-]{36}$' }
        if ($parts) {
            $tunnelUuid = $parts[0]
            break
        }
    }
}

if ($tunnelUuid) {
    $credentialsPath = "$env:USERPROFILE\.cloudflared\$tunnelUuid.json"
    $targetPath = ".\cloudflared\credentials.json"
    
    if (Test-Path $credentialsPath) {
        # 디렉토리 생성
        if (-not (Test-Path ".\cloudflared")) {
            New-Item -ItemType Directory -Path ".\cloudflared" | Out-Null
        }
        
        Copy-Item $credentialsPath $targetPath -Force
        Write-Host "✓ Credentials 파일이 복사되었습니다: $targetPath" -ForegroundColor Green
        Write-Host "  터널 UUID: $tunnelUuid" -ForegroundColor Cyan
    } else {
        Write-Host "Credentials 파일을 찾을 수 없습니다: $credentialsPath" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "터널 UUID를 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "터널 목록:" -ForegroundColor Yellow
    Write-Host $tunnelList
    exit 1
}

# 4. config.yml에 origin certificate 경로 추가
Write-Host "`n[4/4] config.yml 업데이트" -ForegroundColor Yellow
$configPath = ".\cloudflared\config.yml"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw
    if ($configContent -notmatch "origincert") {
        # Docker 컨테이너 내부 경로로 추가
        $newConfig = $configContent -replace "credentials-file:", "credentials-file: /etc/cloudflared/credentials.json`norigincert: /etc/cloudflared/cert.pem"
        Set-Content $configPath $newConfig -NoNewline
        Write-Host "✓ config.yml이 업데이트되었습니다." -ForegroundColor Green
    } else {
        Write-Host "✓ config.yml에 이미 origincert가 설정되어 있습니다." -ForegroundColor Green
    }
}

# 5. cert.pem을 cloudflared 디렉토리로 복사
Write-Host "`n[5/5] Origin Certificate 복사" -ForegroundColor Yellow
$targetCertPath = ".\cloudflared\cert.pem"
Copy-Item $certPath $targetCertPath -Force
Write-Host "✓ Origin Certificate가 복사되었습니다: $targetCertPath" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "설정 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. DNS 라우팅 설정 (선택사항)" -ForegroundColor Cyan
Write-Host "   cloudflared tunnel route dns $tunnelName deep-guardian.your-domain.com" -ForegroundColor White
Write-Host ""
Write-Host "2. 터널 시작:" -ForegroundColor Cyan
Write-Host "   docker-compose up -d cloudflared" -ForegroundColor White
Write-Host ""




# Cloudflare Quick Tunnel 시작 스크립트
# 가장 간단한 방법 - 별도 설정 없이 바로 사용 가능

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Quick Tunnel 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cloudflared 설치 확인
$cloudflaredInstalled = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredInstalled) {
    Write-Host "Cloudflared가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "설치 방법:" -ForegroundColor Yellow
    Write-Host "  choco install cloudflared" -ForegroundColor Cyan
    Write-Host "  또는 https://github.com/cloudflare/cloudflared/releases 에서 다운로드" -ForegroundColor Cyan
    exit 1
}

Write-Host "Cloudflare Quick Tunnel을 시작합니다..." -ForegroundColor Yellow
Write-Host "외부 접근 URL이 생성되면 터미널에 표시됩니다." -ForegroundColor Yellow
Write-Host ""
Write-Host "중지하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ""

# Quick Tunnel 시작 (포트 80으로)
cloudflared tunnel --url http://localhost:80




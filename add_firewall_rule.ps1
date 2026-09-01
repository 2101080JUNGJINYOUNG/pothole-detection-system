# NPU Worker 방화벽 규칙 추가 스크립트
# 관리자 권한으로 실행 필요

Write-Host "NPU Worker 방화벽 규칙 추가 중..." -ForegroundColor Cyan

try {
    # 기존 규칙 확인
    $existing = Get-NetFirewallRule -DisplayName "NPU Worker Port 9002" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "방화벽 규칙이 이미 존재합니다. 제거 후 재생성합니다..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName "NPU Worker Port 9002" -ErrorAction SilentlyContinue
    }
    
    # 새 규칙 추가 (한 줄로 작성)
    New-NetFirewallRule -DisplayName "NPU Worker Port 9002" -Direction Inbound -LocalPort 9002 -Protocol TCP -Action Allow -Description "Allow NPU Worker (Phi-3-mini) on port 9002 for Docker containers"
    
    Write-Host ""
    Write-Host "✅ 방화벽 규칙 추가 완료!" -ForegroundColor Green
    Write-Host "이제 Docker 컨테이너에서 NPU Worker에 접근할 수 있습니다." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "관리자 권한으로 실행했는지 확인하세요." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "대안: 다음 명령어를 직접 실행해보세요:" -ForegroundColor Cyan
    Write-Host "netsh advfirewall firewall add rule name='NPU Worker Port 9002' dir=in action=allow protocol=TCP localport=9002" -ForegroundColor Green
    exit 1
}

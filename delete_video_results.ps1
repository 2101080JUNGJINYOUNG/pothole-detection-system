# 비디오 추론 결과 삭제 스크립트
# PowerShell에서 실행

Write-Host "비디오 추론 결과 삭제 중..." -ForegroundColor Yellow

# AI Core 컨테이너에서 삭제 스크립트 실행
$result = docker exec deep-guardian-ai python3 /app/delete_video_results.py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 비디오 추론 결과가 삭제되었습니다." -ForegroundColor Green
    Write-Host $result
} else {
    Write-Host "❌ 삭제 중 오류 발생:" -ForegroundColor Red
    Write-Host $result
    Write-Host "`nAI Core 컨테이너가 실행 중인지 확인해주세요:" -ForegroundColor Yellow
    Write-Host "  docker-compose ps ai-core" -ForegroundColor Cyan
}


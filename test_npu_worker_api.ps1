# NPU Worker API 테스트 스크립트

Write-Host "`n=== NPU Worker API 테스트 ===" -ForegroundColor Cyan

# 1. Health Check (GET 요청)
Write-Host "`n1. Health Check (GET /health)" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://127.0.0.1:9001/health" -Method GET
    Write-Host "✅ 서버 상태: $($healthResponse.status)" -ForegroundColor Green
    Write-Host "   모델 로드됨: $($healthResponse.model_loaded)" -ForegroundColor White
    Write-Host "   OpenVINO 사용 가능: $($healthResponse.openvino_available)" -ForegroundColor White
    if ($healthResponse.model_path) {
        Write-Host "   모델 경로: $($healthResponse.model_path)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Health Check 실패: $_" -ForegroundColor Red
    exit 1
}

# 2. Depth Inference (POST 요청) - 테스트 이미지 필요
Write-Host "`n2. Depth Inference (POST /depth)" -ForegroundColor Yellow
Write-Host "   이 엔드포인트는 이미지 파일을 POST로 전송해야 합니다." -ForegroundColor White
Write-Host "   사용 예시:" -ForegroundColor Cyan
Write-Host "   curl -X POST -F 'image=@test_image.jpg' http://127.0.0.1:9001/depth" -ForegroundColor White
Write-Host "`n   또는 Python으로:" -ForegroundColor Cyan
Write-Host "   import requests" -ForegroundColor White
Write-Host "   with open('test_image.jpg', 'rb') as f:" -ForegroundColor White
Write-Host "       response = requests.post('http://127.0.0.1:9001/depth', files={'image': f})" -ForegroundColor White

Write-Host "`n=== 테스트 완료 ===" -ForegroundColor Green




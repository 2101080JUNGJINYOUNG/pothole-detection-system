# 현재 실행 중인 서버에 모델 로드 스크립트

$modelPath = "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"
$serverUrl = "http://localhost:9001"

Write-Host "=" * 50
Write-Host "NPU Worker 모델 로드"
Write-Host "=" * 50

# 모델 파일 확인
if (-not (Test-Path $modelPath)) {
    Write-Host "`n에러: 모델 파일을 찾을 수 없습니다: $modelPath"
    exit 1
}

Write-Host "`n모델 경로: $modelPath"
Write-Host "서버 URL: $serverUrl"
Write-Host "`n모델 로드 중...`n"

# JSON 페이로드 생성
$body = @{
    model_path = $modelPath
    device = "AUTO:NPU,CPU"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$serverUrl/load_model" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "응답:"
    $response | ConvertTo-Json -Depth 10
    
    if ($response.success) {
        Write-Host "`n모델 로드 성공!" -ForegroundColor Green
    } else {
        Write-Host "`n모델 로드 실패: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "`n에러 발생: $_" -ForegroundColor Red
    Write-Host "서버가 실행 중인지 확인하세요." -ForegroundColor Yellow
}





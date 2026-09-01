# OpenVINO용 Phi-3-mini 모델 다운로드 스크립트

Write-Host "=== OpenVINO용 Phi-3-mini 모델 다운로드 ===" -ForegroundColor Cyan
Write-Host ""

# huggingface-cli 확인
Write-Host "huggingface-cli 확인 중..." -ForegroundColor Yellow
$cliCheck = huggingface-cli --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "huggingface-cli가 설치되지 않았습니다. 설치 중..." -ForegroundColor Yellow
    pip install -q huggingface_hub[cli]
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 설치 실패" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 설치 완료" -ForegroundColor Green
} else {
    Write-Host "✅ huggingface-cli 확인 완료" -ForegroundColor Green
}

# 모델 저장 디렉토리 생성
Write-Host ""
Write-Host "모델 저장 디렉토리 생성 중..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "models/llm" | Out-Null
Write-Host "✅ 디렉토리 생성 완료: models/llm" -ForegroundColor Green

# OpenVINO용 모델 다운로드
Write-Host ""
Write-Host "OpenVINO용 Phi-3-mini 모델 다운로드 시작..." -ForegroundColor Cyan
Write-Host "모델: OpenVINO/Phi-3-mini-4k-instruct-int4-ov" -ForegroundColor White
Write-Host "저장 위치: ./models/llm/Phi-3-mini-int4" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  다운로드 중... (시간이 걸릴 수 있습니다)" -ForegroundColor Yellow
Write-Host ""

huggingface-cli download OpenVINO/Phi-3-mini-4k-instruct-int4-ov --local-dir ./models/llm/Phi-3-mini-int4

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "✅ 다운로드 완료!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "다운로드된 모델 경로: ./models/llm/Phi-3-mini-int4" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "사용 방법:" -ForegroundColor Yellow
    Write-Host "python slm_npu_worker_phi3.py --model ./models/llm/Phi-3-mini-int4 --device NPU --port 9002" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ 다운로드 실패" -ForegroundColor Red
    exit 1
}



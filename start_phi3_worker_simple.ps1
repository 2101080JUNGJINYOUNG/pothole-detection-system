# Phi-3-mini SLM NPU Worker 간단 시작 스크립트 (백그라운드 실행)

Write-Host "=== Phi-3-mini SLM NPU Worker 시작 ===" -ForegroundColor Cyan
Write-Host ""

# 가상환경 활성화
$venvPath = "$env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "경고: 가상환경을 찾을 수 없습니다: $venvPath" -ForegroundColor Yellow
    Write-Host "계속 진행합니다..." -ForegroundColor Yellow
}

# 기본 설정
$modelPath = "./models/llm/Phi-3-mini-int4"  # OpenVINO용 변환된 모델
$device = "NPU"
$port = 9002

Write-Host "=== 설정 정보 ===" -ForegroundColor Cyan
Write-Host "모델: $modelPath" -ForegroundColor White
Write-Host "디바이스: $device" -ForegroundColor White
Write-Host "포트: $port" -ForegroundColor White
Write-Host ""

# OpenVINO GenAI 설치 확인 및 설치
Write-Host "OpenVINO GenAI 확인 중..." -ForegroundColor Yellow
$checkGenAI = python -c "import openvino_genai; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "OpenVINO GenAI가 설치되지 않았습니다." -ForegroundColor Red
    Write-Host "설치 중..." -ForegroundColor Yellow
    pip install openvino-genai
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 설치 실패. 수동으로 설치해주세요: pip install openvino-genai" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ OpenVINO GenAI 설치 완료" -ForegroundColor Green
} else {
    Write-Host "✅ OpenVINO GenAI 확인 완료" -ForegroundColor Green
}

# Worker 시작
Write-Host ""
Write-Host "Phi-3-mini SLM NPU Worker 시작 중..." -ForegroundColor Green
Write-Host "서버 URL: http://localhost:$port" -ForegroundColor Cyan
Write-Host "종료하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ""

# Worker 시작
python slm_npu_worker_phi3.py --model $modelPath --device $device --port $port


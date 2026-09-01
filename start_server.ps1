# Deep-Guardian NPU Worker 서버 시작 스크립트 (올바른 모델 경로 포함)

Write-Host "=" * 50
Write-Host "Deep-Guardian NPU Worker 시작"
Write-Host "=" * 50

# 가상환경 활성화
Write-Host "`n가상환경 활성화 중..."
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# 모델 경로 설정
$modelPath = "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"

# 모델 파일 확인
if (-not (Test-Path $modelPath)) {
    Write-Host "`n경고: 모델 파일을 찾을 수 없습니다: $modelPath" -ForegroundColor Yellow
    Write-Host "서버는 모델 없이 시작됩니다." -ForegroundColor Yellow
    Write-Host "서버 시작 후 /load_model 엔드포인트로 모델을 로드할 수 있습니다." -ForegroundColor Yellow
} else {
    Write-Host "`n모델 파일 확인: $modelPath" -ForegroundColor Green
}

# 서버 시작
Write-Host "`nNPU Worker 서버 시작 중...`n"
python npu_worker.py --model $modelPath --device "AUTO:NPU,CPU" --port 9001





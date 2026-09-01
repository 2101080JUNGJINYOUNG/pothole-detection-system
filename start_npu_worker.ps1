# Deep-Guardian NPU Worker 시작 스크립트

Write-Host "=" * 50
Write-Host "Deep-Guardian NPU Worker 시작"
Write-Host "=" * 50

# 가상환경 활성화
Write-Host "`n가상환경 활성화 중..."
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# 모델 경로 확인
$defaultModelPath = "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"
$modelPath = "openvino_model.xml"

# 기본 경로에 모델이 있으면 사용
if (Test-Path $defaultModelPath) {
    $modelPath = $defaultModelPath
    Write-Host "`n모델 파일을 찾았습니다: $modelPath"
} elseif (-not (Test-Path $modelPath)) {
    Write-Host "`n경고: 모델 파일을 찾을 수 없습니다."
    Write-Host "기본 경로: $defaultModelPath"
    Write-Host "현재 디렉토리: $(Get-Location)"
    Write-Host "`n모델 파일 경로를 확인하거나 --model 옵션으로 지정해주세요."
}

# 서버 시작
Write-Host "`nNPU Worker 서버 시작 중...`n"
Write-Host "디바이스 우선순위: NPU > GPU > CPU`n"
python npu_worker.py --model $modelPath --device "AUTO:NPU,GPU,CPU" --port 9001


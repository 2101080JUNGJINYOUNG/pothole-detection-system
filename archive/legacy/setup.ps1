# Depth Anything V2 NPU 추론 환경 설정 스크립트

Write-Host "=" * 50
Write-Host "Depth Anything V2 NPU 추론 환경 설정"
Write-Host "=" * 50

# 가상환경 활성화
Write-Host "`n가상환경 활성화 중..."
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# 필요한 패키지 설치
Write-Host "`n필요한 패키지 설치 중..."
pip install -r requirements.txt

Write-Host "`n설정 완료!"
Write-Host "`n사용 방법:"
Write-Host "  python inference_npu.py --input 이미지경로.jpg"
Write-Host "=" * 50





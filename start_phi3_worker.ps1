# Phi-3-mini NPU Worker 시작 스크립트
# Windows Host에서 실행하여 Docker 컨테이너에서 접근 가능하도록 함

Write-Host "========================================" -ForegroundColor Green
Write-Host "Phi-3-mini NPU Worker 시작" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 현재 디렉토리 확인
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Python 경로 확인 (Windows에서 일반적인 순서로 확인)
$pythonCmd = $null

# 1. py launcher 시도 (Windows에서 가장 일반적)
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
    Write-Host "✅ Python launcher (py) 발견" -ForegroundColor Green
}
# 2. python 명령어 시도
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "✅ Python (python) 발견" -ForegroundColor Green
}
# 3. python3 명령어 시도
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
    Write-Host "✅ Python (python3) 발견" -ForegroundColor Green
}
# 4. 직접 경로 확인
else {
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:ProgramFiles\Python*\python.exe",
        "$env:ProgramFiles(x86)\Python*\python.exe"
    )
    
    foreach ($path in $possiblePaths) {
        $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $pythonCmd = $found.FullName
            Write-Host "✅ Python 발견: $pythonCmd" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "Python 설치 방법:" -ForegroundColor Yellow
    Write-Host "  1. Microsoft Store에서 Python 설치" -ForegroundColor White
    Write-Host "  2. python.org에서 Python 다운로드" -ForegroundColor White
    Write-Host "  3. 또는 다음 명령어로 확인:" -ForegroundColor White
    Write-Host "     where.exe python" -ForegroundColor Gray
    Write-Host "     where.exe py" -ForegroundColor Gray
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

# 모델 경로 확인 (로컬 모델이 있으면 사용)
$modelPath = "microsoft/phi-3-mini-4k-instruct"
if (Test-Path "models\llm\Phi-3-mini-int4") {
    $modelPath = "models\llm\Phi-3-mini-int4"
    Write-Host "✅ 로컬 모델 발견: $modelPath" -ForegroundColor Green
} else {
    Write-Host "ℹ️  로컬 모델을 찾을 수 없습니다. Hugging Face에서 다운로드합니다." -ForegroundColor Yellow
}

# 디바이스 선택
$device = "NPU"
Write-Host ""
Write-Host "디바이스 선택:" -ForegroundColor Cyan
Write-Host "  1. NPU (Intel Arc GPU NPU)" -ForegroundColor White
Write-Host "  2. CPU" -ForegroundColor White
Write-Host "  3. AUTO (자동 선택)" -ForegroundColor White
$deviceChoice = Read-Host "선택 (1-3, 기본값: 1)"

switch ($deviceChoice) {
    "2" { $device = "CPU" }
    "3" { $device = "AUTO" }
    default { $device = "NPU" }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "NPU Worker 시작 중..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "모델: $modelPath" -ForegroundColor Cyan
Write-Host "디바이스: $device" -ForegroundColor Cyan
Write-Host "포트: 9002" -ForegroundColor Cyan
Write-Host "URL: http://localhost:9002" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  이 창을 닫지 마세요. NPU Worker가 실행 중입니다." -ForegroundColor Yellow
Write-Host ""

# NPU Worker 실행
try {
    & $pythonCmd slm_npu_worker_phi3.py --model $modelPath --device $device --port 9002 --host 0.0.0.0
} catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "  1. Python이 설치되어 있는지 확인" -ForegroundColor White
    Write-Host "  2. 필요한 패키지 설치: pip install openvino-genai flask flask-cors" -ForegroundColor White
    Write-Host "  3. 모델 경로 확인: models\llm\Phi-3-mini-int4" -ForegroundColor White
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
}

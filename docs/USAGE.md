# NPU Worker 사용 가이드

## 현재 설정

- **모델 경로**: `C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml`
- **서버 포트**: 9001
- **디바이스**: AUTO:NPU,CPU

## 서버 시작 방법

### 방법 1: 자동 스크립트 사용 (권장)

```powershell
.\start_server.ps1
```

이 스크립트는:
- 가상환경을 자동으로 활성화
- 올바른 모델 경로를 사용
- 서버를 시작

### 방법 2: 수동 실행

```powershell
# 1. 가상환경 활성화
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# 2. 서버 시작
python npu_worker.py --model "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml" --device AUTO:NPU,CPU --port 9001
```

### 방법 3: 모델 없이 시작 후 런타임 로드

서버를 먼저 시작하고 나중에 모델을 로드할 수도 있습니다:

```powershell
# 1. 서버 시작 (모델 없이)
python npu_worker.py --port 9001

# 2. 다른 터미널에서 모델 로드
python load_model_example.py "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"
```

또는 PowerShell 스크립트 사용:
```powershell
.\load_model_now.ps1
```

## 서버 상태 확인

```powershell
# 헬스 체크
Invoke-RestMethod -Uri "http://localhost:9001/health" | ConvertTo-Json
```

예상 응답:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "openvino_available": true,
  "model_path": "C:\\Users\\shkim1\\Documents\\KakaoTalk Downloads\\depth_npu\\depth_npu\\openvino_model.xml"
}
```

## 깊이 추정 테스트

```powershell
python test_npu_worker.py --image test.png
```

## API 사용 예제

### Python에서 호출

```python
import requests

url = "http://localhost:9001/depth"
with open("pothole_crop.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post(url, files=files)
    result = response.json()
    
    if result["success"]:
        print(f"깊이 비율: {result['depth_ratio']:.4f}")
        print(f"검증 결과: {'통과' if result['validation_result'] else '실패'}")
```

### PowerShell에서 호출

```powershell
$file = Get-Item "test.png"
$response = Invoke-RestMethod -Uri "http://localhost:9001/depth" -Method Post -InFile $file.FullName -ContentType "multipart/form-data"
$response | ConvertTo-Json
```

### Docker 컨테이너에서 호출

```python
import requests

# Docker 컨테이너 내부에서
url = "http://host.docker.internal:9001/depth"
with open("pothole_crop.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post(url, files=files)
    result = response.json()
```

## 문제 해결

### 모델이 로드되지 않는 경우

1. **런타임 로드** (서버 실행 중):
   ```powershell
   python load_model_example.py "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"
   ```

2. **서버 재시작** (올바른 경로로):
   ```powershell
   .\start_server.ps1
   ```

### 서버가 시작되지 않는 경우

1. 포트 9001이 이미 사용 중인지 확인:
   ```powershell
   netstat -ano | findstr :9001
   ```

2. 다른 포트 사용:
   ```powershell
   python npu_worker.py --model "..." --port 9002
   ```

### 추론이 실패하는 경우

1. 모델이 로드되었는지 확인:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:9001/health"
   ```

2. 서버 로그 확인 (에러 메시지 확인)

3. OpenVINO 설치 확인:
   ```python
   from openvino import Core
   core = Core()
   print(core.available_devices)
   ```

## 주의사항

- 서버를 중지하려면 `Ctrl+C`를 누르세요
- 모델 파일 경로에 공백이 있으므로 따옴표로 감싸야 합니다
- NPU는 AUTO:NPU,CPU 모드로만 동작합니다 (NPU 단독 불가)





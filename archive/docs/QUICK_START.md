# NPU Worker 빠른 시작 가이드

## ✅ 현재 상태

- ✅ 모델 파일 위치 확인 완료
- ✅ 모델 로드 성공
- ✅ 추론 테스트 통과

## 모델 파일 위치

```
C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\
├── openvino_model.xml
└── openvino_model.bin
```

## 서버 시작 (모델 자동 로드)

**권장 방법:**
```powershell
.\start_server.ps1
```

이 스크립트는 올바른 모델 경로를 자동으로 사용합니다.

**또는 직접 실행:**
```powershell
# 가상환경 활성화
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# 서버 시작
python npu_worker.py --model "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml" --device AUTO:NPU,CPU --port 9001
```

## 런타임 모델 로드 (서버 실행 중)

서버가 이미 실행 중이지만 모델이 없는 경우:

```powershell
# 방법 1: Python 스크립트 사용
python load_model_example.py "C:\Users\shkim1\Documents\KakaoTalk Downloads\depth_npu\depth_npu\openvino_model.xml"

# 방법 2: PowerShell 스크립트 사용
.\load_model_now.ps1
```

## 테스트

```powershell
python test_npu_worker.py --image test.png
```

## API 사용 예제

### 헬스 체크
```powershell
Invoke-RestMethod -Uri "http://localhost:9001/health"
```

### 깊이 추정
```powershell
$file = Get-Item "test.png"
$response = Invoke-RestMethod -Uri "http://localhost:9001/depth" -Method Post -InFile $file.FullName -ContentType "multipart/form-data"
$response | ConvertTo-Json
```

## Docker 컨테이너에서 호출

`ai-core` 컨테이너에서:
```python
import requests

url = "http://host.docker.internal:9001/depth"
with open("pothole_crop.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post(url, files=files)
    result = response.json()
    
    if result["success"]:
        depth_ratio = result["depth_ratio"]
        is_valid = result["validation_result"]
        print(f"깊이 비율: {depth_ratio:.4f}")
        print(f"검증 결과: {'통과' if is_valid else '실패'}")
```

## 문제 해결

### 모델이 로드되지 않는 경우
1. 모델 파일 경로 확인
2. `/load_model` 엔드포인트로 런타임 로드
3. 서버 재시작 시 `--model` 옵션으로 경로 지정

### 서버가 응답하지 않는 경우
1. 포트 9001이 사용 중인지 확인
2. 방화벽 설정 확인
3. 서버 로그 확인


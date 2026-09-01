# Phi-3-mini with OpenVINO + NPU 설정 가이드

OpenVINO GenAI를 사용하여 Phi-3-mini 모델을 NPU에서 실행하는 방법입니다.

## 🎯 Phi-3-mini 선택 이유

- **작은 크기**: 약 2.3GB (4K 컨텍스트) 또는 3.8GB (128K 컨텍스트)
- **빠른 추론**: NPU에서 매우 빠른 속도
- **좋은 성능**: 작은 모델 치고는 뛰어난 성능
- **OpenVINO 지원**: OpenVINO GenAI에서 공식 지원

## 설치 방법

### 1. OpenVINO GenAI 설치

```powershell
# 가상환경 활성화 (OpenVINO가 설치된 환경)
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# OpenVINO GenAI 설치
pip install openvino-genai

# 또는 직접 설치
pip install openvino-genai[transformers]
```

### 2. 모델 다운로드 및 변환

OpenVINO GenAI는 자동으로 모델을 다운로드하고 최적화합니다:

```python
from openvino_genai import LLMPipeline

# 자동으로 다운로드 및 최적화
pipeline = LLMPipeline.from_pretrained("microsoft/phi-3-mini-4k-instruct", device="NPU")
```

또는 명시적으로 IR 형식으로 저장:

```python
from openvino_genai import LLMPipeline

pipeline = LLMPipeline.from_pretrained("microsoft/phi-3-mini-4k-instruct")
pipeline.save_ov_model("./phi3_ov_ir")  # OpenVINO IR로 저장
```

### 3. SLM NPU Worker 실행

```powershell
# 방법 1: Hugging Face 모델 ID 사용 (자동 다운로드)
python slm_npu_worker_phi3.py --model microsoft/phi-3-mini-4k-instruct --device NPU --port 9002

# 방법 2: 로컬 IR 모델 사용
python slm_npu_worker_phi3.py --model ./phi3_ov_ir --device NPU --port 9002

# 방법 3: CPU로 테스트 (NPU가 없는 경우)
python slm_npu_worker_phi3.py --model microsoft/phi-3-mini-4k-instruct --device CPU --port 9002
```

## 사용 가능한 Phi-3 모델

| 모델 | 크기 | 컨텍스트 | 설명 |
|------|------|----------|------|
| `microsoft/phi-3-mini-4k-instruct` | 2.3GB | 4K | 기본 (권장) |
| `microsoft/phi-3-mini-128k-instruct` | 3.8GB | 128K | 긴 컨텍스트 |
| `microsoft/phi-3-medium-4k-instruct` | 7GB | 4K | 더 큰 모델 |

## API 사용 예시

### 1. 헬스 체크

```powershell
Invoke-RestMethod -Uri "http://localhost:9002/health"
```

### 2. 모델 로드 (런타임)

```powershell
$body = @{
    model_path = "microsoft/phi-3-mini-4k-instruct"
    device = "NPU"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:9002/load_model" -Method Post -Body $body -ContentType "application/json"
```

### 3. 챗 (질문/답변)

```powershell
$body = @{
    prompt = "오늘 가장 위험했던 포트홀 위치는 어디인가요?"
    system_message = "당신은 도로 포트홀 탐지 시스템의 AI 어시스턴트입니다."
    max_tokens = 200
    temperature = 0.7
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:9002/chat" -Method Post -Body $body -ContentType "application/json"
```

### 4. Python에서 사용

```python
import requests

# 챗
response = requests.post(
    "http://localhost:9002/chat",
    json={
        "prompt": "오늘 가장 위험했던 포트홀 위치는 어디인가요?",
        "system_message": "당신은 도로 포트홀 탐지 시스템의 AI 어시스턴트입니다.",
        "max_tokens": 200,
        "temperature": 0.7
    }
)

result = response.json()
print(result['response'])
```

## Dashboard 통합

`slm_npu_chatbot.py`를 사용하여 Dashboard에 통합:

```python
from slm_npu_chatbot import SLMNPUChatbot

chatbot = SLMNPUChatbot(worker_url="http://host.docker.internal:9002")
response = chatbot.answer_question("오늘 가장 위험했던 곳이 어디야?")
```

## 성능 최적화

### 1. NPU 디바이스 확인

```python
from openvino import Core

core = Core()
print(core.available_devices)  # ['CPU', 'GPU', 'NPU'] 등
```

### 2. 배치 처리 (선택사항)

여러 질문을 배치로 처리하려면:

```python
# 각각 따로 호출 (현재 구현)
# 향후 배치 처리 추가 가능
```

### 3. 메모리 최적화

- 모델을 한 번만 로드 (현재 구현)
- 필요시 양자화 모델 사용 (INT8)

## 문제 해결

### 모델 다운로드 실패

```powershell
# Hugging Face 토큰이 필요한 경우
$env:HUGGING_FACE_HUB_TOKEN="your_token_here"
```

### NPU가 인식되지 않는 경우

```python
# 디바이스 확인
from openvino import Core
core = Core()
if "NPU" not in core.available_devices:
    print("NPU를 사용할 수 없습니다. CPU로 fallback합니다.")
    device = "CPU"
```

### 메모리 부족

- 더 작은 모델 사용 (phi-3-mini-4k)
- 배치 크기 감소
- 양자화 모델 사용

## 시작 스크립트

`start_phi3_worker.ps1`:

```powershell
# 가상환경 활성화
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# Worker 시작
python slm_npu_worker_phi3.py --model microsoft/phi-3-mini-4k-instruct --device NPU --port 9002
```

## 테스트

```powershell
# 헬스 체크
python -c "import requests; print(requests.get('http://localhost:9002/health').json())"

# 간단한 챗 테스트
python -c "import requests; r = requests.post('http://localhost:9002/chat', json={'prompt': '안녕하세요', 'max_tokens': 50}); print(r.json())"
```

## 현재 구현 상태

- ✅ `slm_npu_worker_phi3.py`: Phi-3-mini NPU Worker
- ✅ `slm_npu_chatbot.py`: NPU Worker 클라이언트 (재사용 가능)
- ✅ Dashboard 통합 준비 완료

다음 단계:
1. OpenVINO GenAI 설치
2. Worker 실행
3. Dashboard에서 테스트



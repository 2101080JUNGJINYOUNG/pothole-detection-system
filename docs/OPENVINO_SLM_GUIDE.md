# OpenVINO + NPU를 사용한 SLM 실행 가이드

OpenVINO를 사용하여 NPU에서 Small Language Model을 실행하는 방법입니다.

## 🎯 장점

- **NPU 활용**: Intel Arc GPU의 NPU를 활용하여 빠른 추론
- **로컬 실행**: 인터넷 연결 없이도 동작
- **효율적**: NPU 전용 최적화로 빠른 속도
- **프라이버시**: 데이터가 외부로 전송되지 않음

## 아키텍처

```
┌─────────────────┐
│  Dashboard      │
│  (Streamlit)    │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│  SLM NPU Worker │
│  (OpenVINO)     │
│  Port: 9002     │
└────────┬────────┘
         │
┌────────▼────────┐
│  Intel NPU      │
│  (Arc GPU)      │
└─────────────────┘
```

## 구현 방법

### 방법 1: SLM NPU Worker 사용 (권장)

기존 NPU Worker와 유사한 구조로 SLM 전용 Worker 생성:

1. **SLM 모델을 OpenVINO IR 형식으로 변환**
   - Model Optimizer 사용
   - 또는 OpenVINO GenAI 지원 모델 사용

2. **SLM NPU Worker 실행**
   ```powershell
   python slm_npu_worker.py --model model.xml --device AUTO:NPU,CPU --port 9002
   ```

3. **Dashboard에서 사용**
   - `road_chatbot.py` 대신 `slm_npu_chatbot.py` 사용
   - 또는 둘 다 지원하도록 통합

### 방법 2: Ollama 대비 장단점

| 항목 | Ollama | OpenVINO + NPU |
|------|--------|----------------|
| **설치** | 간단 | 모델 변환 필요 |
| **NPU 활용** | 제한적 | **완전 지원** |
| **속도** | 보통 | **NPU에서 매우 빠름** |
| **모델 선택** | 다양함 | 변환된 모델만 |
| **메모리** | 보통 | 최적화됨 |

## OpenVINO GenAI 지원 모델

OpenVINO는 다음 SLM 모델들을 지원합니다:

- **Llama 2/3** (7B, 13B)
- **Phi-3** (mini, small, medium)
- **TinyLlama**
- **Gemma** (2B, 7B)

## 모델 변환 방법

### 1. OpenVINO GenAI 사용 (권장)

```bash
# OpenVINO GenAI 설치
pip install openvino-genai

# 모델 다운로드 및 변환
from openvino_genai import LLMPipeline

# 모델 로드 및 IR로 내보내기
pipeline = LLMPipeline.from_pretrained("microsoft/phi-3-mini")
pipeline.save_ov_model("phi3_ov_ir")
```

### 2. Model Optimizer 사용

```bash
# Hugging Face 모델을 OpenVINO IR로 변환
mo --input_model model.onnx --output_dir ./ir_model
```

## SLM NPU Worker 실행

### 1. 모델 준비

```powershell
# 모델 변환 (예시)
# phi3 모델을 OpenVINO IR로 변환
```

### 2. Worker 시작

```powershell
python slm_npu_worker.py --model ./phi3_ov_ir/model.xml --device AUTO:NPU,CPU --port 9002
```

### 3. 헬스 체크

```powershell
Invoke-RestMethod -Uri "http://localhost:9002/health"
```

### 4. 테스트

```powershell
$body = @{
    prompt = "안녕하세요"
    max_tokens = 100
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:9002/chat" -Method Post -Body $body -ContentType "application/json"
```

## Dashboard 통합

### 옵션 1: OpenVINO 전용 사용

`dashboard/app.py`에서:

```python
from slm_npu_chatbot import SLMNPUChatbot, check_slm_npu_connection

if check_slm_npu_connection():
    chatbot = SLMNPUChatbot()
    response = chatbot.answer_question(question)
```

### 옵션 2: Ollama와 OpenVINO 둘 다 지원

우선순위:
1. OpenVINO NPU Worker (연결 가능하면)
2. Ollama (대안)

```python
if check_slm_npu_connection():
    # OpenVINO NPU 사용
    chatbot = SLMNPUChatbot()
elif check_ollama_connection():
    # Ollama 사용
    chatbot = RoadChatbot()
else:
    # 둘 다 없으면 오류
    st.warning("SLM이 사용 가능하지 않습니다.")
```

## NPU 최적화 팁

1. **배치 크기 조정**: NPU에 맞게 배치 크기 최적화
2. **정밀도 설정**: INT8 양자화 사용 (속도 향상)
3. **컴파일 옵션**: NPU 전용 컴파일 옵션 사용

```python
compiled_model = core.compile_model(
    model,
    device_name="NPU",
    config={
        "PERFORMANCE_HINT": "LATENCY",
        "INFERENCE_PRECISION_HINT": "f16"  # 또는 "i8"
    }
)
```

## 문제 해결

### NPU가 인식되지 않는 경우

```python
# 사용 가능한 디바이스 확인
core = Core()
print(core.available_devices)  # ['CPU', 'GPU', 'NPU'] 등

# NPU가 없으면 CPU로 fallback
device = "NPU" if "NPU" in core.available_devices else "CPU"
```

### 모델 변환 오류

- OpenVINO GenAI를 사용하면 자동 변환 지원
- 또는 사전 변환된 모델 사용

### 메모리 부족

- 더 작은 모델 사용 (Phi-3 mini, TinyLlama)
- 배치 크기 감소
- 양자화된 모델 사용 (INT8)

## 현재 상태

현재 구현:
- ✅ `slm_npu_worker.py`: SLM NPU Worker 기본 구조
- ✅ `slm_npu_chatbot.py`: NPU Worker 클라이언트
- ⚠️ 모델 변환 및 실제 테스트 필요

다음 단계:
1. OpenVINO GenAI로 모델 변환
2. NPU Worker 테스트
3. Dashboard 통합



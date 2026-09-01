# Phi-3-mini-int4 LAMP 컨테이너 통합 완료

## ✅ 완료된 작업

### 1. 패키지 추가
- `lamp-container/app/requirements.txt`에 추가:
  - `openvino-genai>=0.3.0`
  - `openvino>=2024.0.0`

### 2. Phi-3 챗봇 클래스 생성
- `lamp-container/app/phi3_chatbot.py` 생성
  - `Phi3Chatbot` 클래스
  - OpenVINO GenAI를 사용한 Phi-3 모델 로드
  - NPU → GPU → CPU 순서로 폴백
  - 프로젝트 컨텍스트 포함

### 3. Flask API 엔드포인트 추가
- `lamp-container/app/app.py`에 추가:
  - `POST /api/chat` - 챗봇 대화 API
  - `POST /api/chat/load_model` - 모델 로드 API
  - `/health` 엔드포인트에 Phi-3 상태 추가

### 4. 웹 UI 챗봇 인터페이스 추가
- `lamp-container/web/index.html`에 추가:
  - 챗봇 토글 버튼 (우측 하단)
  - 챗봇 컨테이너 (고정 위치)
  - 메시지 입력 및 전송 기능
  - 실시간 대화 UI

### 5. Docker 설정 업데이트
- `docker-compose.yml`에 추가:
  - Phi-3 모델 볼륨 마운트: `./models/llm:/app/models/llm:ro`
  - 환경 변수:
    - `PHI3_MODEL_PATH=/app/models/llm/Phi-3-mini-int4`
    - `PHI3_DEVICE=NPU`

---

## 🚀 사용 방법

### 1. 컨테이너 빌드 및 시작

```powershell
docker-compose up -d --build
```

### 2. 웹 접속

브라우저에서 http://localhost 접속

### 3. 챗봇 사용

1. 우측 하단의 💬 버튼 클릭
2. 챗봇 창이 열림
3. 메시지 입력 후 전송 또는 Enter 키

### 4. 모델 수동 로드 (필요시)

```powershell
# 컨테이너 내부 접속
docker exec -it deep-guardian-lamp bash

# Python으로 모델 로드
python3 -c "
from phi3_chatbot import Phi3Chatbot
chatbot = Phi3Chatbot(model_path='/app/models/llm/Phi-3-mini-int4', device='NPU')
chatbot.load_model()
print('모델 로드 완료')
"
```

또는 API로 로드:

```bash
curl -X POST http://localhost/api/chat/load_model \
  -H "Content-Type: application/json" \
  -d '{
    "model_path": "/app/models/llm/Phi-3-mini-int4",
    "device": "NPU"
  }'
```

---

## 📋 API 엔드포인트

### POST /api/chat

챗봇과 대화

**요청**:
```json
{
  "message": "오늘 탐지된 포트홀은 몇 개인가요?",
  "max_tokens": 200,
  "temperature": 0.7
}
```

**응답**:
```json
{
  "success": true,
  "response": "오늘 탐지된 포트홀은...",
  "device": "NPU"
}
```

### POST /api/chat/load_model

Phi-3 모델 로드

**요청**:
```json
{
  "model_path": "/app/models/llm/Phi-3-mini-int4",
  "device": "NPU"
}
```

**응답**:
```json
{
  "success": true,
  "model_path": "/app/models/llm/Phi-3-mini-int4",
  "device": "NPU",
  "loaded": true
}
```

### GET /health

시스템 상태 확인 (Phi-3 상태 포함)

**응답**:
```json
{
  "status": "healthy",
  "database": "connected",
  "phi3_chatbot": "loaded"
}
```

---

## 🔧 설정

### 환경 변수

`.env` 파일 또는 `docker-compose.yml`에서 설정:

```env
PHI3_MODEL_PATH=/app/models/llm/Phi-3-mini-int4
PHI3_DEVICE=NPU
```

### 디바이스 옵션

- `NPU`: NPU 우선, 실패 시 GPU → CPU 폴백
- `GPU`: GPU 직접 사용
- `CPU`: CPU 직접 사용

---

## 🐛 문제 해결

### 모델이 로드되지 않을 때

1. **모델 경로 확인**:
```powershell
docker exec -it deep-guardian-lamp ls -la /app/models/llm/
```

2. **OpenVINO 설치 확인**:
```powershell
docker exec -it deep-guardian-lamp pip list | grep openvino
```

3. **수동 모델 로드**:
```powershell
docker exec -it deep-guardian-lamp python3 -c "from phi3_chatbot import get_chatbot; chatbot = get_chatbot(); print(chatbot.is_model_loaded())"
```

### NPU가 인식되지 않을 때

- 자동으로 GPU 또는 CPU로 폴백됩니다
- 로그에서 확인:
```powershell
docker-compose logs lamp | grep -i "device\|npu\|gpu"
```

### 챗봇이 응답하지 않을 때

1. **헬스 체크**:
```bash
curl http://localhost/health
```

2. **API 직접 테스트**:
```bash
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

---

## 📝 주의사항

1. **모델 파일 크기**: Phi-3-mini-int4 모델은 약 2GB입니다
2. **메모리 요구사항**: 모델 로드 시 충분한 메모리 필요
3. **NPU 지원**: NPU가 없으면 자동으로 CPU로 폴백
4. **초기 로딩**: 첫 모델 로드는 시간이 걸릴 수 있습니다

---

## ✅ 통합 완료 확인

- ✅ 카카오 API: 포함됨
- ✅ 자동 파인튜닝: 포함됨
- ✅ Phi-3-mini-int4: **LAMP 컨테이너에 통합 완료**

모든 기능이 2개 컨테이너 구조에 포함되었습니다!


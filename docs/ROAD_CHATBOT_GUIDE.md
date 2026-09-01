# 도로 포트홀 챗봇 가이드

SLM (Small Language Model)을 사용한 대화형 질의응답 기능입니다.

## 기능 소개

- **자연어 질의응답**: SQL 쿼리를 몰라도 자연어로 포트홀 데이터에 대해 질문
- **실시간 데이터 조회**: Django ORM을 통해 최신 포트홀 데이터 실시간 조회
- **이미지 표시**: 관련 포트홀 이미지 자동 표시
- **대화 히스토리**: 질문과 답변 히스토리 유지

## 사용 예시

### 질문 예시

- "오늘 가장 위험했던 곳이 어디야?"
- "오늘 몇 개의 포트홀이 탐지되었어?"
- "위험도가 높은 포트홀을 알려줘"
- "최근 탐지된 포트홀 통계를 보여줘"
- "Critical 등급 포트홀은 몇 개야?"

### 답변 예시

**사용자**: "오늘 가장 위험했던 곳이 어디야?"

**AI**: "오늘 총 15건이 탐지되었으며, 그중 군산대 정문 앞에서 발견된 포트홀이 깊이 비율 0.35로 가장 위험합니다(Critical 등급). 해당 구역 사진을 확인해드릴까요?"

## Ollama 설치 및 설정

### 1. Ollama 설치

**Windows:**
1. https://ollama.ai/download 에서 Ollama 다운로드
2. 설치 파일 실행하여 설치
3. Ollama가 자동으로 시작됩니다

**Linux/Mac:**
```bash
curl https://ollama.ai/install.sh | sh
```

### 2. 모델 다운로드

권장 모델:
- **llama3.2** (기본값, 권장): 빠르고 효율적
- **phi3**: 작은 크기, 빠른 응답
- **llama3.1:8b**: 더 정확한 응답

```bash
# 기본 모델 (llama3.2) 다운로드
ollama pull llama3.2

# 또는 Phi-3 다운로드
ollama pull phi3

# 또는 Llama 3.1 8B 다운로드
ollama pull llama3.1:8b
```

### 3. Ollama 서버 확인

기본적으로 Ollama는 `http://localhost:11434`에서 실행됩니다.

확인 방법:
```bash
curl http://localhost:11434/api/tags
```

또는 브라우저에서:
```
http://localhost:11434/api/tags
```

### 4. Docker 컨테이너에서 접근

Docker 컨테이너에서 호스트의 Ollama에 접근하려면:
- `OLLAMA_URL=http://host.docker.internal:11434` (기본값)

이미 `docker-compose.yml`에 설정되어 있습니다.

## 환경 변수 설정

### Docker Compose

`docker-compose.yml`에 이미 설정되어 있습니다:

```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
  - OLLAMA_MODEL=llama3.2
```

### 수동 설정

```bash
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2
```

## 사용 방법

### 웹 대시보드에서 사용

1. Streamlit 대시보드 접속: `http://localhost:8501`
2. "대시보드" 페이지로 이동
3. "💬 도로 포트홀 챗봇 (Chat with Road)" 섹션 찾기
4. 질문 입력 후 "📤 질문하기" 버튼 클릭

### 예시 질문 버튼

- "오늘 가장 위험했던 곳이 어디야?" 버튼 클릭
- 자동으로 질문이 입력되고 답변이 생성됩니다

## 기술적 세부사항

### 데이터 조회 함수

챗봇은 다음 함수들을 사용하여 데이터를 조회합니다:

- `get_today_detections()`: 오늘 탐지된 포트홀
- `get_most_dangerous_today()`: 오늘 가장 위험한 포트홀
- `get_statistics_today()`: 오늘 통계 데이터
- `get_data_by_location()`: 위치 키워드로 포트홀 검색

### 프롬프트 구조

챗봇은 다음과 같은 프롬프트를 사용합니다:

1. 시스템 프롬프트: 챗봇 역할 정의
2. 컨텍스트 데이터: 오늘의 포트홀 통계 및 정보
3. 사용자 질문: 실제 질문

### 답변 포맷

답변은 다음 정보를 포함할 수 있습니다:

- **텍스트 답변**: 자연어로 작성된 답변
- **데이터**: 관련 포트홀 데이터 (JSON 형식)
- **이미지**: 관련 포트홀 이미지 (있을 경우)

## 문제 해결

### Ollama 연결 실패

**증상**: "Ollama가 실행되지 않았습니다" 메시지 표시

**해결 방법:**
1. Ollama가 설치되어 있는지 확인
2. Ollama 서버가 실행 중인지 확인:
   ```bash
   curl http://localhost:11434/api/tags
   ```
3. Docker 컨테이너에서 접근하는 경우 `OLLAMA_URL` 환경 변수 확인

### 모델을 찾을 수 없음

**증상**: 모델 로드 오류

**해결 방법:**
1. 모델이 다운로드되었는지 확인:
   ```bash
   ollama list
   ```
2. 필요한 모델 다운로드:
   ```bash
   ollama pull llama3.2
   ```

### 응답이 느림

**해결 방법:**
1. 더 작은 모델 사용 (예: phi3)
2. Ollama 서버가 로컬에서 실행 중인지 확인
3. GPU 가속이 가능하면 Ollama GPU 지원 사용

## 고급 설정

### 다른 모델 사용

환경 변수로 모델 변경:
```bash
export OLLAMA_MODEL=phi3
```

또는 `docker-compose.yml`에서:
```yaml
environment:
  - OLLAMA_MODEL=phi3
```

### Ollama 서버 URL 변경

커스텀 Ollama 서버를 사용하는 경우:
```yaml
environment:
  - OLLAMA_URL=http://your-ollama-server:11434
```

## API 사용 예시

Python 코드에서 직접 사용:

```python
from road_chatbot import RoadChatbot

# 챗봇 초기화
chatbot = RoadChatbot(model_name="llama3.2")

# 질문하기
response = chatbot.answer_question("오늘 가장 위험했던 곳이 어디야?")
print(response['answer'])

# 관련 데이터
if response['data']:
    print(response['data'])

# 이미지 경로
if response['image_path']:
    print(response['image_path'])
```



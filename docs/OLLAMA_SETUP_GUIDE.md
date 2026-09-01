# Ollama 요약 기능 설정 가이드

Deep-Guardian 대시보드에 Ollama를 사용한 AI 요약 기능을 추가했습니다.

## 기능 소개

- Django DB의 포트홀 데이터를 Ollama LLM으로 분석
- 위험도, 위치 유형, 우선순위 등 통계 정보 요약
- 웹 대시보드에서 간단한 버튼 클릭으로 요약 생성

## 설치 방법

### 1. Ollama 설치

1. **Ollama 다운로드 및 설치**
   - 공식 사이트: https://ollama.ai
   - 운영체제에 맞는 설치 파일 다운로드
   - 설치 실행 (Windows/Mac/Linux 지원)

2. **모델 다운로드**
   ```bash
   # 작은 모델 (빠른 응답, 1B 파라미터)
   ollama pull llama3.2:1b
   
   # 또는 더 큰 모델 (더 정확한 요약, 3B 파라미터)
   ollama pull llama3.2:3b
   
   # 또는 한국어 지원 모델
   ollama pull qwen2.5:3b
   ```

3. **Ollama 서버 실행 확인**
   - 설치 후 Ollama는 자동으로 백그라운드에서 실행됩니다
   - 수동 실행: `ollama serve`
   - 기본 포트: `http://localhost:11434`

### 2. Python 패키지 설치

Dashboard 컨테이너에서 ollama 패키지 설치:

```bash
# Docker 컨테이너 내부에서
docker exec -it deep-guardian-dashboard pip install ollama

# 또는 requirements.txt로 재빌드
docker-compose restart dashboard
```

### 3. 환경 변수 설정 (선택사항)

`docker-compose.yml`의 dashboard 서비스에 환경 변수 추가:

```yaml
dashboard:
  environment:
    - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Ollama 서버 URL
    - OLLAMA_MODEL=llama3.2:1b  # 사용할 모델명
```

## 사용 방법

### 웹 대시보드에서 사용

1. **대시보드 접속**
   - http://localhost 접속
   - 또는 http://localhost:8501 (직접 접속)

2. **요약 생성**
   - 대시보드 메인 페이지에서 "🤖 AI 요약 (Ollama)" 섹션 확인
   - 요약할 기간 (일) 설정
   - 최소 우선순위 점수 설정
   - "📊 요약 생성" 버튼 클릭

3. **요약 결과 확인**
   - AI가 분석한 포트홀 데이터 요약 표시
   - 통계, 위험도 분석, 주요 포트홀 정보 포함

## 기능 상세

### 요약에 포함되는 정보

1. **통계 정보**
   - 전체 탐지 수
   - 검증 통과 비율
   - 평균 깊이 비율

2. **위험도 분포**
   - Critical/High/Medium/Low 비율

3. **위치 유형 분포**
   - 고속도로, 학교 주변, 병원 주변 등

4. **주요 포트홀**
   - 우선순위 상위 5개 포트홀 정보

### 모델 선택 가이드

- **llama3.2:1b** (기본값)
  - 빠른 응답 속도
  - 적은 메모리 사용
  - 기본적인 요약에 적합

- **llama3.2:3b**
  - 더 정확한 요약
  - 더 많은 메모리 필요
  - 상세한 분석에 적합

- **qwen2.5:3b**
  - 한국어 지원 우수
  - 더 자연스러운 한국어 요약
  - 한국어 환경에 권장

## 문제 해결

### Ollama 연결 실패

1. **Ollama 서버 실행 확인**
   ```bash
   # Windows PowerShell
   Get-Process ollama
   
   # Linux/Mac
   ps aux | grep ollama
   ```

2. **포트 확인**
   ```bash
   # Windows PowerShell
   netstat -an | findstr 11434
   
   # Linux/Mac
   netstat -an | grep 11434
   ```

3. **Docker에서 호스트 접근 확인**
   - `host.docker.internal` 사용 (Windows/Mac)
   - Linux에서는 `--network=host` 또는 IP 주소 직접 사용

### 요약 생성 실패

1. **모델 다운로드 확인**
   ```bash
   ollama list
   ```

2. **모델 이름 확인**
   - 환경 변수 `OLLAMA_MODEL` 값 확인
   - 대시보드에 설정된 모델명과 일치하는지 확인

3. **로그 확인**
   ```bash
   docker-compose logs dashboard
   ```

### 성능 최적화

1. **작은 모델 사용**
   - `llama3.2:1b` 사용 시 빠른 응답

2. **데이터 제한**
   - 요약 생성 시 최대 100개 데이터만 사용
   - 필요시 `ollama_summary.py`에서 `limit` 값 조정

3. **캐싱 활용**
   - 같은 조건의 요약은 캐시 사용 고려 (향후 구현 가능)

## API 사용 예시

프로그래밍 방식으로 요약 생성:

```python
from dashboard.ollama_summary import generate_custom_summary

# 최근 7일 데이터 요약
result = generate_custom_summary(days=7, limit=100, min_priority=0.0)

if result['success']:
    print(result['summary'])
else:
    print(f"오류: {result['error']}")
```

## 참고 자료

- Ollama 공식 문서: https://ollama.ai/docs
- Ollama Python 라이브러리: https://github.com/ollama/ollama-python
- 모델 목록: https://ollama.ai/library



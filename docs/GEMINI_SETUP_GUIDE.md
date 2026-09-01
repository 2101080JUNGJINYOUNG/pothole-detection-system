# Google Gemini AI 요약 기능 설정 가이드

Deep-Guardian 대시보드에 Google Gemini를 사용한 AI 요약 기능을 추가했습니다.

## 기능 소개

- Django DB의 포트홀 데이터를 Google Gemini AI로 분석
- 위험도, 위치 유형, 우선순위 등 통계 정보 요약
- 웹 대시보드에서 간단한 버튼 클릭으로 요약 생성

## 설치 방법

### 1. Google AI Studio에서 API 키 발급

1. **Google AI Studio 접속**
   - https://makersuite.google.com/app/apikey 방문
   - Google 계정으로 로그인

2. **API 키 생성**
   - "Create API Key" 버튼 클릭
   - 프로젝트 선택 또는 새 프로젝트 생성
   - API 키 복사 (나중에 복사할 수 없으므로 안전하게 보관)

3. **API 키 확인**
   - 발급된 API 키는 다음과 같은 형식: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

### 2. 환경 변수 설정

#### 방법 1: docker-compose.yml 파일에 직접 추가 (권장하지 않음, 보안 위험)

```yaml
dashboard:
  environment:
    - GEMINI_API_KEY=your_api_key_here
    - GEMINI_MODEL=gemini-1.5-flash
```

#### 방법 2: .env 파일 사용 (권장)

1. 프로젝트 루트에 `.env` 파일 생성:
```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

2. `docker-compose.yml` 수정:
```yaml
dashboard:
  env_file:
    - .env
```

#### 방법 3: 시스템 환경 변수 설정

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
$env:GEMINI_MODEL="gemini-1.5-flash"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your_api_key_here"
export GEMINI_MODEL="gemini-1.5-flash"
```

### 3. Python 패키지 설치

Dashboard 컨테이너에서 google-generativeai 패키지 설치:

```bash
# Docker 컨테이너 내부에서
docker exec -it deep-guardian-dashboard pip install google-generativeai

# 또는 requirements.txt로 재빌드
docker-compose build dashboard
docker-compose up -d dashboard
```

### 4. Docker 컨테이너 재시작

```bash
docker-compose restart dashboard
```

## 사용 방법

### 웹 대시보드에서 사용

1. **대시보드 접속**
   - http://localhost 접속
   - 또는 http://localhost:8501 (직접 접속)

2. **요약 생성**
   - 대시보드 메인 페이지에서 "🤖 AI 요약 (Google Gemini)" 섹션 확인
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

- **gemini-1.5-flash** (기본값, 권장)
  - 빠른 응답 속도
  - 무료 할당량: 분당 15회 요청
  - 기본적인 요약에 적합

- **gemini-1.5-pro**
  - 더 정확하고 상세한 요약
  - 무료 할당량: 분당 2회 요청
  - 복잡한 분석에 적합

- **gemini-pro** (이전 버전)
  - 안정적인 성능
  - 무료 할당량 제공

## API 사용 제한

### 무료 할당량

- **gemini-1.5-flash**: 분당 15회 요청
- **gemini-1.5-pro**: 분당 2회 요청
- **일일 할당량**: 약 1,500회 요청 (모델별 다름)

### 요금제

- 무료 할당량을 초과하면 Google Cloud Platform 계정 연결 필요
- 가격 정보: https://ai.google.dev/pricing

## 문제 해결

### API 키 오류

1. **API 키 확인**
   ```bash
   # Docker 컨테이너 내부에서 확인
   docker exec -it deep-guardian-dashboard printenv GEMINI_API_KEY
   ```

2. **API 키 유효성 확인**
   - Google AI Studio에서 API 키 상태 확인
   - API 키가 활성화되어 있는지 확인

3. **환경 변수 설정 확인**
   ```bash
   docker-compose config | grep GEMINI
   ```

### 요약 생성 실패

1. **패키지 설치 확인**
   ```bash
   docker exec -it deep-guardian-dashboard pip list | grep google-generativeai
   ```

2. **연결 로그 확인**
   ```bash
   docker-compose logs dashboard | grep -i gemini
   ```

3. **API 할당량 확인**
   - Google AI Studio 대시보드에서 사용량 확인
   - 할당량 초과 시 다음 시간까지 대기

### 성능 최적화

1. **빠른 모델 사용**
   - `gemini-1.5-flash` 사용 시 빠른 응답

2. **데이터 제한**
   - 요약 생성 시 최대 100개 데이터만 사용
   - 필요시 `gemini_summary.py`에서 `limit` 값 조정

3. **캐싱 활용**
   - 같은 조건의 요약은 캐시 사용 고려 (향후 구현 가능)

## API 사용 예시

프로그래밍 방식으로 요약 생성:

```python
from dashboard.gemini_summary import generate_custom_summary

# 최근 7일 데이터 요약
result = generate_custom_summary(days=7, limit=100, min_priority=0.0)

if result['success']:
    print(result['summary'])
else:
    print(f"오류: {result['error']}")
```

## 보안 주의사항

1. **API 키 보호**
   - API 키를 코드에 하드코딩하지 마세요
   - .env 파일을 .gitignore에 추가
   - 공개 저장소에 API 키를 업로드하지 마세요

2. **환경 변수 사용**
   - 프로덕션 환경에서는 환경 변수나 시크릿 관리 시스템 사용
   - Docker secrets 또는 Kubernetes secrets 활용

## 참고 자료

- Google AI Studio: https://makersuite.google.com
- Gemini API 문서: https://ai.google.dev/docs
- Python SDK 문서: https://ai.google.dev/api/python
- 가격 정보: https://ai.google.dev/pricing



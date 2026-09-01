# Deep-Guardian 아키텍처 업데이트 내역

**업데이트 일자**: 2025-12-16  
**원본 블록도 기준 변경사항 정리**

---

## 🔄 주요 변경사항

### 1. **데이터베이스 접근 방식 변경**

#### 원본 블록도
- **PostgreSQL** (직접 SQL 쿼리 사용)

#### 현재 구현
- **PostgreSQL + Django ORM** (추상화 레이어 추가)
- 모든 데이터베이스 접근이 Django ORM을 통해 이루어짐
- `django_app/models.py`에서 `Pothole`, `User` 모델 정의
- `managed = False` 설정으로 기존 PostgreSQL 스키마와 호환

**영향 범위:**
- `ai-core/main.py` - Django ORM으로 변경
- `dashboard/app.py` - Django ORM으로 변경
- `dashboard/auth.py` - Django ORM으로 변경
- `dashboard/gemini_summary.py` - Django ORM 사용

---

### 2. **대시보드 기능 확장**

#### 추가된 기능들:

##### 2.1 **AI 요약 기능 (Google Gemini)**
- **위치**: `dashboard/gemini_summary.py`
- **기능**: 
  - 포트홀 데이터를 Google Gemini API를 사용하여 자동 요약
  - 필터링 옵션 (기간, 최소 우선순위 점수)
  - 재시도 로직 (429 오류 처리)
- **UI**: 대시보드에 "🤖 AI 요약 (Google Gemini)" 섹션 추가

##### 2.2 **챗봇 기능 (Phi-3-mini + OpenVINO + NPU)**
- **위치**: 
  - `dashboard/slm_npu_chatbot.py` (클라이언트)
  - `slm_npu_worker_phi3.py` (서버)
- **기능**:
  - 자연어 질의응답 (예: "오늘 가장 위험했던 곳이 어디야?")
  - NPU 하드웨어 가속 (Intel NPU 사용)
  - 데이터베이스 쿼리 결과를 컨텍스트로 제공
- **UI**: 오른쪽 사이드바에 챗봇 인터페이스 추가
- **하드웨어**: AtomMan X7 Ti (Intel Core Ultra 9 185H)의 NPU 활용

---

### 3. **AI Core 파이프라인 확장**

#### 3.1 **합성 포트홀 생성 기능**
- **위치**: `ai-core/synthetic_pothole_generator.py`
- **기능**:
  - 실제 포트홀 이미지를 배경 도로 이미지에 합성
  - 학습 데이터셋 자동 증강
  - YOLO 형식 레이블 자동 생성
- **활성화**: `USE_SYNTHETIC_POTHOLES=true` 환경 변수로 제어
- **통합**: Auto Fine-Tuning 파이프라인에 통합

#### 3.2 **Django ORM 통합**
- 모든 데이터베이스 작업이 Django ORM을 통해 수행
- `ai-core/main.py`에서 `save_to_db()`, `prepare_finetune_dataset()` 등이 Django ORM 사용

---

### 4. **새로운 서비스/워커 추가**

#### 4.1 **SLM NPU Worker (Phi-3-mini)**
- **위치**: `slm_npu_worker_phi3.py`
- **포트**: 9002 (설정 가능)
- **기능**:
  - Phi-3-mini 모델 로딩 및 추론
  - OpenVINO GenAI 사용
  - NPU → GPU → CPU 순서로 폴백
- **통신**: Flask REST API (`/chat`, `/health`, `/load_model`)

#### 4.2 **NPU Worker (Depth Estimation) - 기존 유지**
- **위치**: `npu_worker.py`
- **포트**: 9001
- **기능**: Depth Anything V2 깊이 추정 (블록도에 명시된 기능)

---

### 5. **Docker Compose 구성 변경**

#### 추가된 환경 변수:
- `dashboard` 서비스:
  - `GEMINI_API_KEY`: Google Gemini API 키
  - `GEMINI_MODEL`: 사용할 Gemini 모델 (기본값: gemini-2.0-flash)
  - `SLM_NPU_WORKER_URL`: SLM NPU Worker URL
- `ai-core` 서비스:
  - `USE_SYNTHETIC_POTHOLES`: 합성 포트홀 생성 활성화 여부

#### 추가된 볼륨 마운트:
- `django_app` 디렉토리가 `dashboard`와 `ai-core` 컨테이너에 마운트

---

## 📊 업데이트된 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AI Core Processing Pipeline                         │   │
│  │  - YOLOv8n Detection                                 │   │
│  │  - Auto Fine-Tuning (with Synthetic Data) ◄── NEW   │   │
│  │  - Risk Assessment                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Web Infrastructure (Streamlit)                      │   │
│  │  - Dashboard Visualization                           │   │
│  │  - Gemini AI Summary ◄── NEW                         │   │
│  │  - SLM Chatbot (NPU) ◄── NEW                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL + Django ORM ◄── UPDATED                 │   │
│  │  (기존 PostgreSQL 스키마 유지)                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌──────────────────┐            ┌──────────────────┐
│  NPU Worker      │            │  SLM NPU Worker  │
│  (Depth V2)      │            │  (Phi-3-mini)    │ ◄── NEW
│  Port: 9001      │            │  Port: 9002      │
└──────────────────┘            └──────────────────┘
```

---

## 🔧 환경 변수 설정 가이드

### 필수 환경 변수 (.env 파일)

```env
# Google Gemini API (AI 요약 기능)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# SLM NPU Worker (챗봇 기능)
SLM_NPU_WORKER_URL=http://host.docker.internal:9002

# 합성 포트홀 생성 (선택사항)
USE_SYNTHETIC_POTHOLES=false
```

---

## 📝 주요 파일 변경 내역

### 새로 추가된 파일들:
1. `dashboard/gemini_summary.py` - Gemini API 통합
2. `dashboard/slm_npu_chatbot.py` - 챗봇 클라이언트
3. `slm_npu_worker_phi3.py` - SLM NPU Worker 서버
4. `ai-core/synthetic_pothole_generator.py` - 합성 포트홀 생성
5. `django_app/` - Django ORM 레이어 (전체 디렉토리)

### 주요 수정된 파일들:
1. `ai-core/main.py` - Django ORM 사용, 합성 데이터 통합
2. `dashboard/app.py` - Gemini 요약, 챗봇 UI 추가
3. `docker-compose.yml` - 환경 변수 및 볼륨 마운트 추가

---

## 🚀 사용 방법

### 1. SLM NPU Worker 시작 (챗봇 사용 시)

```powershell
# PowerShell에서 실행
.\start_phi3_worker_simple.ps1
```

### 2. Google Gemini API 키 설정

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 발급
2. `.env` 파일에 `GEMINI_API_KEY` 설정
3. Docker 컨테이너 재시작: `docker-compose restart dashboard`

### 3. 합성 포트홀 생성 활성화 (선택사항)

```env
USE_SYNTHETIC_POTHOLES=true
```

---

## 📌 블록도 업데이트 권장사항

원본 블록도에 다음 항목들을 추가/수정하는 것을 권장합니다:

### 추가해야 할 항목:
1. **Django ORM 레이어** (PostgreSQL 위에 추상화 레이어로 표시)
2. **Google Gemini API** (AI 요약 기능)
3. **SLM NPU Worker** (Phi-3-mini, 포트 9002)
4. **합성 포트홀 생성 모듈** (Auto Fine-Tuning 파이프라인 내)
5. **챗봇 UI** (대시보드 내 오른쪽 사이드바)

### 수정해야 할 항목:
1. **데이터베이스 접근**: "PostgreSQL (직접)" → "PostgreSQL + Django ORM"
2. **대시보드 기능**: AI 요약, 챗봇 기능 추가 표기

---

## ✅ 호환성

- **기존 PostgreSQL 스키마 유지**: Django ORM이 `managed = False`로 기존 스키마와 완벽 호환
- **기존 API/엔드포인트 유지**: 모든 기존 기능 정상 동작
- **하위 호환성**: 새로운 기능들은 선택적으로 활성화 가능



# Deep-Guardian Docker 구성 가이드

## 전체 구조

```
[User/Admin Browser]
        |
        v
[Container 1: web-server (Apache)] - 포트 80
        |
        v
[Container 2: dashboard (Streamlit)] - 포트 8501
        |
        v
[Container 4: db (PostgreSQL)] - 포트 5432

[Container 3: ai-core (AI Engine)]
        |
        v
[Windows Host: NPU Worker] - 포트 9001
```

## 사전 요구사항

1. **Docker & Docker Compose 설치**
2. **Windows Host에서 NPU Worker 실행 중**
   ```powershell
   .\start_server.ps1
   ```

3. **GPU 지원 (WSL, 선택사항)**
   - NVIDIA GPU가 있는 경우 WSL에서 GPU 패스스루 설정

## 시작 방법

### 1. 전체 시스템 시작

```powershell
docker-compose up -d
```

### 2. 개별 서비스 확인

```powershell
# 로그 확인
docker-compose logs -f dashboard
docker-compose logs -f ai-core
docker-compose logs -f web-server

# 상태 확인
docker-compose ps
```

### 3. 웹 접속

- **Apache (Reverse Proxy)**: http://localhost
- **Streamlit 대시보드 (직접 접속)**: http://localhost:8501
- **PostgreSQL**: localhost:5432

## 서비스 설명

### 1. web-server (Apache)
- **포트**: 80
- **역할**: Reverse Proxy, 외부 진입점
- **설정**: `apache/httpd.conf`

### 2. dashboard (Streamlit)
- **포트**: 8501
- **역할**: 포트홀 데이터 시각화 및 관리
- **기능**:
  - 지도 시각화 (Folium)
  - 통계 대시보드
  - 데이터 테이블

### 3. ai-core (AI Engine)
- **역할**: 포트홀 탐지 및 검증
- **처리 흐름**:
  1. YOLOv8로 포트홀 탐지
  2. 포트홀 영역 크롭
  3. NPU Worker 호출 (깊이 검증)
  4. 검증 통과 데이터만 DB 저장

### 4. db (PostgreSQL)
- **포트**: 5432
- **데이터베이스**: pothole_db
- **사용자**: pothole_user / pothole_pass
- **초기화**: `database/init.sql`

## 환경 변수

### ai-core
- `NPU_WORKER_URL`: NPU Worker URL (기본값: http://host.docker.internal:9001/depth)
- `DATABASE_URL`: PostgreSQL 연결 문자열

### dashboard
- `DATABASE_URL`: PostgreSQL 연결 문자열

## 문제 해결

### 웹페이지 접속 안 됨

1. **Apache 컨테이너 확인**:
   ```powershell
   docker-compose logs web-server
   ```

2. **포트 충돌 확인**:
   ```powershell
   netstat -ano | findstr :80
   ```

3. **컨테이너 상태 확인**:
   ```powershell
   docker-compose ps
   ```

### 데이터베이스 연결 실패

1. **PostgreSQL 컨테이너 확인**:
   ```powershell
   docker-compose logs db
   ```

2. **연결 테스트**:
   ```powershell
   docker-compose exec db psql -U pothole_user -d pothole_db
   ```

### NPU Worker 연결 실패

1. **Windows Host에서 NPU Worker 실행 확인**:
   ```powershell
   # 다른 터미널에서
   .\start_server.ps1
   ```

2. **컨테이너에서 호스트 접근 테스트**:
   ```powershell
   docker-compose exec ai-core curl http://host.docker.internal:9001/health
   ```

### GPU 사용 불가

1. **WSL GPU 설정 확인**:
   ```bash
   # WSL 내부에서
   nvidia-smi
   ```

2. **Docker Compose에서 GPU 설정 제거** (CPU만 사용):
   - `docker-compose.yml`의 `ai-core` 서비스에서 `deploy` 섹션 제거

## 중지 및 정리

```powershell
# 서비스 중지
docker-compose stop

# 서비스 중지 및 컨테이너 제거
docker-compose down

# 볼륨까지 삭제 (데이터 삭제)
docker-compose down -v
```

## 개발 모드

개별 서비스를 재빌드:
```powershell
docker-compose build dashboard
docker-compose up -d dashboard
```

로그 실시간 확인:
```powershell
docker-compose logs -f
```





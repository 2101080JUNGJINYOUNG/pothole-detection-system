# Deep-Guardian 2-Container 구조 빠른 시작

## 🚀 빠른 시작

### 1. 컨테이너 빌드 및 시작

```powershell
# 전체 시스템 빌드 및 시작
docker-compose up -d --build
```

### 2. 상태 확인

```powershell
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 컨테이너 로그
docker-compose logs -f inference
docker-compose logs -f lamp
```

### 3. 웹 접속

브라우저에서 http://localhost 접속

---

## 📋 컨테이너 구성

### inference (AI 추론)
- **포트**: 없음 (내부 네트워크만)
- **기능**: YOLOv8 포트홀 탐지, NPU Worker 호출
- **데이터베이스**: MySQL (lamp 컨테이너)

### lamp (LAMP 스택)
- **포트**: 80 (웹), 3306 (MySQL)
- **기능**: 웹서버, 데이터베이스, 웹 애플리케이션
- **구성**: Apache + MySQL + Python/Flask

---

## 🔧 주요 명령어

### 컨테이너 관리

```powershell
# 시작
docker-compose up -d

# 중지
docker-compose down

# 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f

# 컨테이너 내부 접속
docker exec -it deep-guardian-inference bash
docker exec -it deep-guardian-lamp bash
```

### 데이터베이스 접속

```powershell
# MySQL 접속
docker exec -it deep-guardian-lamp mysql -u pothole_user -ppothole_pass pothole_db

# 데이터베이스 확인
docker exec -it deep-guardian-lamp mysql -u pothole_user -ppothole_pass -e "SHOW DATABASES;"
```

### 볼륨 관리

```powershell
# 볼륨 목록
docker volume ls

# 볼륨 삭제 (주의: 데이터 삭제됨)
docker volume rm test_mysql_data
```

---

## 🐛 문제 해결

### 컨테이너가 시작되지 않을 때

1. **포트 충돌 확인**:
```powershell
netstat -ano | findstr :80
netstat -ano | findstr :3306
```

2. **이미지 재빌드**:
```powershell
docker-compose build --no-cache
docker-compose up -d
```

3. **로그 확인**:
```powershell
docker-compose logs
```

### MySQL 연결 오류

1. **MySQL 재시작**:
```powershell
docker exec -it deep-guardian-lamp service mysql restart
```

2. **사용자 권한 확인**:
```powershell
docker exec -it deep-guardian-lamp mysql -u root -proot_password -e "SELECT User, Host FROM mysql.user;"
```

### Apache 오류

1. **Apache 설정 테스트**:
```powershell
docker exec -it deep-guardian-lamp apache2ctl configtest
```

2. **Apache 재시작**:
```powershell
docker exec -it deep-guardian-lamp service apache2 restart
```

---

## 📝 환경 변수

`.env` 파일에 다음 변수들을 설정할 수 있습니다:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2
```

---

## 🔄 기존 구조에서 마이그레이션

### 데이터 마이그레이션

기존 PostgreSQL 데이터를 MySQL로 마이그레이션하려면:

1. **PostgreSQL 데이터 내보내기**:
```sql
COPY potholes TO '/tmp/potholes.csv' CSV HEADER;
```

2. **MySQL 데이터 가져오기**:
```sql
LOAD DATA INFILE '/tmp/potholes.csv'
INTO TABLE potholes
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

### 기존 컨테이너 정리

```powershell
# 기존 컨테이너 중지 및 제거
docker-compose -f docker-compose.yml.old down

# 볼륨 정리 (선택사항)
docker volume prune
```

---

## 📚 추가 문서

- **상세 가이드**: `2컨테이너_구조_가이드.md`
- **프로젝트 정리**: `프로젝트_정리.md`
- **파일 목록**: `파일_목록_정리.md`

---

## ⚠️ 주의사항

1. **데이터 백업**: 기존 데이터를 백업하세요
2. **포트 충돌**: 기존 서비스와 포트가 충돌하지 않는지 확인
3. **환경 변수**: `.env` 파일이 올바르게 설정되었는지 확인
4. **볼륨**: `mysql_data` 볼륨이 생성되어 데이터가 영구 저장됨


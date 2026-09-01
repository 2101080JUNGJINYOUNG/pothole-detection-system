# Deep-Guardian 2-Container 구조 빠른 시작 가이드

## 🚀 3단계로 시작하기

### 1단계: 컨테이너 빌드 및 시작

```powershell
cd C:\Users\shkim1\Desktop\test
docker-compose up -d --build
```

**예상 시간**: 5-10분 (첫 빌드 시)

### 2단계: 기본 사용자 생성

```powershell
docker exec -it deep-guardian-lamp python3 /var/www/app/create_default_users.py
```

**출력 예시**:
```
[OK] 관리자 계정 생성: admin / admin123
[OK] 일반 사용자 계정 생성: user / user123
```

### 3단계: 웹 접속

브라우저에서 **http://localhost** 접속

**로그인 정보**:
- 관리자: `admin` / `admin123`
- 사용자: `user` / `user123`

---

## ✅ 시작 확인

### 컨테이너 상태 확인

```powershell
docker-compose ps
```

**예상 출력**:
```
NAME                      STATUS
deep-guardian-lamp        Up
deep-guardian-inference   Up
```

### 헬스 체크

```powershell
curl http://localhost/health
```

또는 브라우저에서 http://localhost/health 접속

**예상 응답**:
```json
{
  "status": "healthy",
  "database": "connected",
  "phi3_chatbot": "loaded"
}
```

---

## 🔍 문제 해결

### 컨테이너가 시작되지 않을 때

```powershell
# 로그 확인
docker-compose logs

# 재시작
docker-compose restart
```

### 포트 충돌

```powershell
# 포트 80 사용 중인 프로세스 확인
netstat -ano | findstr :80

# 필요시 다른 포트 사용 (docker-compose.yml 수정)
```

### 데이터베이스 연결 오류

```powershell
# MySQL 재시작
docker exec -it deep-guardian-lamp service mysql restart
```

---

## 📚 더 많은 정보

- **상세 명령어**: `실행_명령어.md` 참조
- **프로젝트 구조**: `프로젝트_블록도.md` 참조
- **기능 설명**: `기능_복구_완료.md` 참조


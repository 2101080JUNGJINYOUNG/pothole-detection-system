# Deep-Guardian 명령어 사용 가이드

## PowerShell에서 실행하는 명령어들

### 1. AI Core 로그 확인 (실시간)

```powershell
docker-compose logs -f ai-core
```

- **실행 위치**: PowerShell
- **기능**: AI Core 컨테이너의 로그를 실시간으로 확인
- **종료**: `Ctrl + C` 누르기
- **예시 출력**:
  ```
  [INFO] Starting image processing: /app/videos/test.mp4
  [INFO] Detected potholes: 1
  [INFO] Processing pothole: bbox=(555, 617, 589, 649), confidence=0.505
  [INFO] Depth ratio: 0.8470, Validation: PASS
  [OK] Saved to database: 37.5665, 126.978
  ```

### 2. 데이터베이스 접속 (대화형)

```powershell
docker-compose exec db psql -U pothole_user -d pothole_db
```

- **실행 위치**: PowerShell
- **기능**: PostgreSQL 데이터베이스에 접속하여 SQL 쿼리 실행
- **사용법**:
  - 접속 후 SQL 쿼리 입력 가능
  - 예: `SELECT * FROM potholes LIMIT 10;`
  - 예: `SELECT COUNT(*) FROM potholes;`
- **종료**: `\q` 또는 `exit` 입력
- **예시**:
  ```sql
  pothole_db=# SELECT COUNT(*) FROM potholes;
   count 
  -------
     22
  (1 row)
  
  pothole_db=# \q
  ```

### 3. 데이터베이스 쿼리 직접 실행 (한 줄)

```powershell
docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT COUNT(*) FROM potholes;"
```

- **실행 위치**: PowerShell
- **기능**: SQL 쿼리를 실행하고 결과만 출력한 후 종료
- **장점**: 대화형 모드로 들어가지 않고 바로 결과 확인
- **예시 출력**:
  ```
   count 
  -------
     22
  (1 row)
  ```

### 4. 유용한 SQL 쿼리 예시

#### 모든 포트홀 데이터 조회
```powershell
docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT id, latitude, longitude, depth_ratio, validation_result, detected_at FROM potholes ORDER BY detected_at DESC LIMIT 10;"
```

#### 통계 조회
```powershell
docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT COUNT(*) as total, COUNT(CASE WHEN validation_result = true THEN 1 END) as validated, AVG(depth_ratio) as avg_depth FROM potholes;"
```

#### 최근 탐지된 포트홀
```powershell
docker-compose exec -T db psql -U pothole_user -d pothole_db -c "SELECT * FROM potholes WHERE detected_at >= NOW() - INTERVAL '1 hour' ORDER BY detected_at DESC;"
```

### 5. 다른 유용한 명령어

#### 모든 컨테이너 상태 확인
```powershell
docker-compose ps
```

#### 특정 컨테이너 로그 확인 (최근 50줄)
```powershell
docker-compose logs --tail 50 ai-core
```

#### 컨테이너 재시작
```powershell
docker-compose restart ai-core
```

#### 모든 컨테이너 중지
```powershell
docker-compose stop
```

#### 모든 컨테이너 시작
```powershell
docker-compose start
```

#### 모든 컨테이너 중지 및 제거
```powershell
docker-compose down
```

## 참고사항

- 모든 명령어는 `C:\Users\shkim1\Desktop\TEST` 디렉토리에서 실행해야 합니다
- PowerShell에서 따옴표(`"`)를 사용할 때는 백틱(`)으로 이스케이프하거나 작은따옴표(`'`)를 사용할 수 있습니다
- SQL 쿼리에서 작은따옴표가 필요할 때는 PowerShell에서 큰따옴표로 전체를 감싸고, SQL 내부는 작은따옴표를 사용합니다




# 사용자 인증 및 관리자 시스템 가이드

## 개요

Deep-Guardian 시스템은 일반 사용자와 관리자를 구분하여 접근 권한을 관리합니다. 관리자는 포트홀 이미지를 검토하고 파인튜닝에 사용할 이미지를 선정할 수 있습니다.

## 기능

### 1. 사용자 인증
- 로그인/로그아웃 기능
- 세션 기반 인증
- 역할 기반 접근 제어 (일반 사용자/관리자)

### 2. 관리자 기능
- 포트홀 이미지 검토
- 이미지 승인/거부
- 검토 메모 작성
- 파인튜닝 데이터 선정

### 3. 파인튜닝 연동
- 관리자가 승인한 이미지만 파인튜닝에 사용
- 자동 파인튜닝 시 승인된 이미지로만 학습

## 기본 계정

### 관리자 계정
- **사용자명**: `admin`
- **비밀번호**: `admin123`
- **권한**: 모든 기능 접근 가능, 이미지 검토 및 승인

### 일반 사용자 계정
- **사용자명**: `user`
- **비밀번호**: `user123`
- **권한**: 대시보드 조회만 가능

⚠️ **보안 주의**: 실제 운영 환경에서는 반드시 비밀번호를 변경하세요!

## 설치 및 설정

### 1. 데이터베이스 스키마 업데이트

```bash
# 데이터베이스 컨테이너에 접속
docker-compose exec db psql -U pothole_user -d pothole_db

# 인증 시스템 스키마 추가
\i /docker-entrypoint-initdb.d/add_user_auth.sql
```

또는 직접 실행:

```bash
docker-compose exec -T db psql -U pothole_user -d pothole_db < database/add_user_auth.sql
```

### 2. 기본 사용자 계정 생성

```bash
# 대시보드 컨테이너에서 실행
docker-compose exec dashboard python create_default_users.py
```

또는 대시보드가 실행되면 자동으로 기본 계정이 생성됩니다.

### 3. 컨테이너 재시작

```bash
docker-compose restart dashboard
```

## 사용 방법

### 로그인

1. 대시보드 접속: http://localhost:8501
2. 로그인 페이지에서 사용자명과 비밀번호 입력
3. 로그인 버튼 클릭

### 일반 사용자

일반 사용자는 다음 기능을 사용할 수 있습니다:
- 포트홀 데이터 조회
- 통계 및 차트 확인
- 지도 시각화
- 데이터 필터링

### 관리자

관리자는 일반 사용자 기능 외에 다음 기능을 사용할 수 있습니다:

#### 이미지 검토 페이지

1. 사이드바에서 "이미지 검토" 선택
2. 검토 대기 중인 포트홀 이미지 확인
3. 각 이미지에 대해:
   - **✅ 승인**: 파인튜닝에 사용할 이미지로 승인
   - **❌ 거부**: 파인튜닝에 사용하지 않음
   - **🔄 초기화**: 검토 상태 초기화
   - **💾 메모 저장**: 검토 메모 작성

#### 필터 옵션

- **검토 상태**: 전체, 검토 대기, 승인됨, 거부됨
- **검증 상태**: 전체, 검증됨, 미검증
- **표시 개수**: 10~100개

## 파인튜닝 연동

### 자동 파인튜닝

매일 00시에 실행되는 자동 파인튜닝은 다음 조건을 만족하는 이미지만 사용합니다:

1. `validation_result = true` (검증됨)
2. `approved_for_training = true` (관리자 승인)
3. 바운딩 박스 정보가 모두 있음
4. 이미지 경로가 유효함

### 수동 파인튜닝

수동으로 파인튜닝을 실행할 때도 동일한 조건이 적용됩니다.

## 데이터베이스 스키마

### users 테이블

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### potholes 테이블 추가 필드

```sql
ALTER TABLE potholes 
ADD COLUMN approved_for_training BOOLEAN DEFAULT NULL,
ADD COLUMN reviewed_by INTEGER REFERENCES users(id),
ADD COLUMN reviewed_at TIMESTAMP,
ADD COLUMN review_notes TEXT;
```

## 보안 고려사항

### 1. 비밀번호 변경

기본 계정의 비밀번호를 반드시 변경하세요:

```python
# Python에서 비밀번호 해시 생성
import bcrypt
password = "새비밀번호"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 데이터베이스에 업데이트
UPDATE users SET password_hash = '생성된해시' WHERE username = 'admin';
```

### 2. HTTPS 사용

프로덕션 환경에서는 HTTPS를 사용하여 비밀번호 전송을 암호화하세요.

### 3. 세션 관리

Streamlit의 세션 상태를 사용하므로, 브라우저를 닫으면 자동으로 로그아웃됩니다.

### 4. 추가 사용자 생성

```sql
-- 새 사용자 생성
INSERT INTO users (username, password_hash, role) 
VALUES ('newuser', 'bcrypt해시', 'user');
```

## 문제 해결

### 로그인 실패

1. 데이터베이스 연결 확인
2. 사용자 테이블 확인:
   ```sql
   SELECT * FROM users;
   ```
3. 기본 계정 재생성:
   ```bash
   docker-compose exec dashboard python create_default_users.py
   ```

### 관리자 권한 없음

1. 사용자 역할 확인:
   ```sql
   SELECT username, role FROM users WHERE username = 'your_username';
   ```
2. 역할 업데이트:
   ```sql
   UPDATE users SET role = 'admin' WHERE username = 'your_username';
   ```

### 이미지 검토 페이지 접근 불가

1. 관리자로 로그인했는지 확인
2. 사이드바에서 "이미지 검토" 메뉴 확인
3. 데이터베이스 스키마 업데이트 확인

## API 참조

### 인증 함수

- `check_authentication()`: 인증 상태 확인
- `is_admin()`: 관리자 여부 확인
- `authenticate_user(username, password)`: 사용자 인증
- `logout()`: 로그아웃

### 관리자 함수

- `approve_pothole(conn, pothole_id, reviewer_id, approved)`: 포트홀 승인/거부
- `save_review_note(conn, pothole_id, note)`: 검토 메모 저장

## 향후 개선 사항

- [ ] 비밀번호 변경 기능
- [ ] 사용자 관리 페이지 (관리자 전용)
- [ ] 역할별 세부 권한 설정
- [ ] 로그인 이력 기록
- [ ] 2단계 인증 (2FA)
- [ ] OAuth 연동






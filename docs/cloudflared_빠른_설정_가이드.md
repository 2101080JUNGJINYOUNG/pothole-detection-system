# Cloudflare Tunnel 빠른 설정 가이드

## 🔧 현재 문제

Cloudflare Tunnel이 아직 설정되지 않았습니다:
- ❌ cert.pem 파일 없음
- ❌ credentials.json 파일 없음 (또는 접근 불가)
- ❌ 터널이 생성되지 않음

## ✅ 해결 방법

### 방법 1: Cloudflare Tunnel 설정 (외부 접근 필요 시)

#### 1단계: Cloudflare 로그인

```powershell
cloudflared tunnel login
```

- 브라우저가 자동으로 열립니다
- Cloudflare 계정으로 로그인
- 도메인 선택 (Cloudflare에서 관리하는 도메인)
- 로그인 완료 후 `cert.pem` 파일이 자동 생성됩니다

#### 2단계: 터널 생성

```powershell
cloudflared tunnel create deep-guardian-tunnel
```

터널이 생성되면 다음과 같은 메시지가 표시됩니다:
```
Created tunnel deep-guardian-tunnel with id [터널-UUID]
```

#### 3단계: 파일 복사

```powershell
# 터널 ID 확인
cloudflared tunnel list

# Cert 파일 복사 (로그인 시 생성됨)
Copy-Item "$env:USERPROFILE\.cloudflared\cert.pem" ".\cloudflared\cert.pem"

# Credentials 파일 복사 (터널 ID는 실제 값으로 변경)
$tunnelId = "터널-UUID"  # cloudflared tunnel list에서 확인
Copy-Item "$env:USERPROFILE\.cloudflared\$tunnelId.json" ".\cloudflared\credentials.json"
```

#### 4단계: config.yml 수정

`cloudflared/config.yml` 파일을 열고 맨 위에 터널 ID 추가:

```yaml
tunnel: deep-guardian-tunnel  # 또는 터널 UUID
credentials-file: /etc/cloudflared/credentials.json
origincert: /etc/cloudflared/cert.pem

ingress:
  # Nginx (Reverse Proxy) - 포트 80 (메인 대시보드)
  - hostname: deep-guardian.your-domain.com
    service: http://web-server:80
  
  # Dashboard (Streamlit) - 포트 8501 (직접 접근)
  - hostname: deep-guardian-dashboard.your-domain.com
    service: http://dashboard:8501
  
  # 기본 라우트 (모든 요청을 Nginx로)
  - service: http_status:404
```

#### 5단계: 컨테이너 재시작

```powershell
docker-compose restart cloudflared
```

### 방법 2: cloudflared 비활성화 (외부 접근 불필요 시)

로컬에서만 사용한다면 cloudflared를 중지해도 됩니다:

```powershell
# cloudflared 중지
docker-compose stop cloudflared

# 또는 docker-compose.yml에서 주석 처리
```

**메인 기능(대시보드, AI 처리)은 cloudflared 없이도 정상 작동합니다!**

## 📝 단계별 명령어

### 전체 설정 (한 번에 실행)

```powershell
# 1. 로그인 (브라우저에서 로그인 필요)
cloudflared tunnel login

# 2. 터널 생성
cloudflared tunnel create deep-guardian-tunnel

# 3. 터널 ID 확인
cloudflared tunnel list

# 4. 파일 복사 (터널 ID는 실제 값으로 변경)
$tunnelId = "실제-터널-UUID"
Copy-Item "$env:USERPROFILE\.cloudflared\cert.pem" ".\cloudflared\cert.pem"
Copy-Item "$env:USERPROFILE\.cloudflared\$tunnelId.json" ".\cloudflared\credentials.json"

# 5. config.yml에 터널 ID 추가 (수동 편집 필요)
# tunnel: deep-guardian-tunnel

# 6. 컨테이너 재시작
docker-compose restart cloudflared
```

## 🔍 파일 위치 확인

### Cert 파일
```powershell
Get-ChildItem "$env:USERPROFILE\.cloudflared\cert.pem"
```

### Credentials 파일
```powershell
Get-ChildItem "$env:USERPROFILE\.cloudflared\*.json"
```

### 터널 목록
```powershell
cloudflared tunnel list
```

## ⚠️ 주의사항

1. **Cloudflare 계정 필요**
   - 무료 계정으로도 사용 가능
   - https://dash.cloudflare.com 에서 생성

2. **도메인 필요**
   - Cloudflare에서 관리하는 도메인
   - 무료 도메인도 가능 (예: Freenom, DuckDNS)

3. **파일 보안**
   - `cert.pem`과 `credentials.json`은 민감한 정보입니다
   - Git에 커밋하지 마세요
   - `.gitignore`에 추가되어 있는지 확인

## 🚀 빠른 해결 (외부 접근 불필요 시)

```powershell
# cloudflared 중지
docker-compose stop cloudflared
```

이렇게 하면:
- ✅ 대시보드: http://localhost (정상 작동)
- ✅ AI 처리: 정상 작동
- ✅ 데이터베이스: 정상 작동
- ❌ 외부 접근: 불가 (로컬에서만 접근)

## 📚 참고 문서

- `CLOUDFLARE_TUNNEL_SETUP.md` - 상세 설정 가이드
- `CLOUDFLARE_설정_가이드.md` - 설정 문제 해결 가이드


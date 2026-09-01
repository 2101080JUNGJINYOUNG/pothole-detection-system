# Cloudflare Tunnel 설정 가이드

## 🔧 현재 문제

cloudflared 컨테이너가 재시작 중인 이유는 터널 ID가 설정되지 않았기 때문입니다.

## ✅ 해결 방법

### 방법 1: config.yml에 터널 ID 추가 (권장)

1. **터널 ID 확인**
   ```powershell
   # Windows Host에서 실행
   cloudflared tunnel list
   ```
   
   또는 `credentials.json` 파일에서 확인:
   ```powershell
   # credentials.json 파일 위치
   # 일반적으로: C:\Users\[사용자명]\.cloudflared\[UUID].json
   ```

2. **config.yml 수정**
   
   `cloudflared/config.yml` 파일을 열고 맨 위에 터널 ID 추가:
   ```yaml
   tunnel: [터널-UUID-또는-이름]
   credentials-file: /etc/cloudflared/credentials.json
   origincert: /etc/cloudflared/cert.pem
   
   ingress:
     # ...
   ```

### 방법 2: 터널 생성 및 설정 (처음 설정하는 경우)

1. **Cloudflared 설치 확인**
   ```powershell
   cloudflared --version
   ```

2. **Cloudflare 로그인**
   ```powershell
   cloudflared tunnel login
   ```

3. **터널 생성**
   ```powershell
   cloudflared tunnel create deep-guardian-tunnel
   ```

4. **Credentials 파일 복사**
   ```powershell
   # 터널 목록 확인
   cloudflared tunnel list
   
   # Credentials 파일 복사 (UUID는 실제 값으로 변경)
   $tunnelId = "실제-터널-UUID"
   Copy-Item "$env:USERPROFILE\.cloudflared\$tunnelId.json" ".\cloudflared\credentials.json"
   ```

5. **Cert 파일 복사**
   ```powershell
   Copy-Item "$env:USERPROFILE\.cloudflared\cert.pem" ".\cloudflared\cert.pem"
   ```

6. **config.yml에 터널 ID 추가**
   ```yaml
   tunnel: deep-guardian-tunnel  # 또는 터널 UUID
   credentials-file: /etc/cloudflared/credentials.json
   origincert: /etc/cloudflared/cert.pem
   ```

7. **DNS 라우팅 설정** (선택사항)
   ```powershell
   cloudflared tunnel route dns deep-guardian-tunnel deep-guardian.your-domain.com
   ```

### 방법 3: cloudflared 비활성화 (외부 접근 불필요한 경우)

외부 접근이 필요하지 않다면 cloudflared를 비활성화할 수 있습니다:

```powershell
# docker-compose.yml에서 cloudflared 서비스 주석 처리
# 또는 컨테이너 중지
docker-compose stop cloudflared
```

## 📝 현재 설정 상태

- ✅ `config.yml` - 원래 5컨테이너 구조로 복원됨
  - `web-server:80` (Apache)
  - `dashboard:8501` (Streamlit)
- ⚠️ `credentials.json` - 터널 ID 확인 필요
- ⚠️ `cert.pem` - 인증서 파일 확인 필요

## 🔍 확인 방법

### 터널 ID 확인
```powershell
# Windows Host에서
cloudflared tunnel list
```

### Credentials 파일 위치
```powershell
# 일반적인 위치
Get-ChildItem "$env:USERPROFILE\.cloudflared\*.json"
```

### 컨테이너 재시작
```powershell
docker-compose restart cloudflared
```

## ⚠️ 주의사항

1. **credentials.json과 cert.pem은 보안상 중요합니다**
   - Git에 커밋하지 마세요
   - `.gitignore`에 추가되어 있는지 확인

2. **터널 ID는 두 가지 형식 가능**
   - 터널 이름: `deep-guardian-tunnel`
   - 터널 UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

3. **외부 접근이 필요하지 않다면**
   - cloudflared를 비활성화해도 메인 기능은 정상 작동합니다
   - 로컬에서만 접근: `http://localhost`

## 🚀 빠른 해결

외부 접근이 필요하지 않다면:

```powershell
# cloudflared 중지
docker-compose stop cloudflared

# 또는 docker-compose.yml에서 주석 처리
```

메인 기능(대시보드, AI 처리)은 cloudflared 없이도 정상 작동합니다!


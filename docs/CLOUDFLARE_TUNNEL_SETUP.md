# Cloudflare Tunnel 설정 가이드

## 개요

Cloudflare Tunnel은 산업에서 널리 사용되는 안전한 터널링 솔루션입니다. 로컬 서버를 외부에 노출시키지 않고도 안전하게 접근할 수 있게 해줍니다.

## 장점

- ✅ **무료**: 개인/상업용 모두 무료
- ✅ **안전**: 로컬 포트를 열지 않아도 됨 (방화벽 우회)
- ✅ **안정적**: Cloudflare의 글로벌 네트워크 활용
- ✅ **HTTPS 자동**: SSL 인증서 자동 관리
- ✅ **산업 표준**: 많은 기업에서 사용

## 사전 요구사항

1. Cloudflare 계정 (무료)
   - https://dash.cloudflare.com 에서 생성
2. 도메인 (Cloudflare에서 관리)
   - 무료 도메인도 가능 (예: Freenom, DuckDNS 등)
3. Cloudflared 설치

## 빠른 시작

### 1. 자동 설정 스크립트 실행

```powershell
.\setup_cloudflare_tunnel.ps1
```

스크립트가 다음을 자동으로 수행합니다:
- Cloudflared 설치 확인
- Cloudflare 로그인
- 터널 생성
- Credentials 파일 복사

### 2. 수동 설정 (스크립트 사용 불가 시)

#### 2.1 Cloudflared 설치

**Chocolatey 사용:**
```powershell
choco install cloudflared -y
```

**Scoop 사용:**
```powershell
scoop install cloudflared
```

**수동 다운로드:**
- https://github.com/cloudflare/cloudflared/releases
- Windows용 `.exe` 파일 다운로드 후 PATH에 추가

#### 2.2 Cloudflare 로그인

```powershell
cloudflared tunnel login
```

브라우저가 열리면 Cloudflare에 로그인하세요.

#### 2.3 터널 생성

```powershell
cloudflared tunnel create deep-guardian-tunnel
```

#### 2.4 Credentials 파일 복사

```powershell
# Credentials 파일 위치 확인
cloudflared tunnel list

# 파일 복사 (UUID는 실제 값으로 변경)
Copy-Item "$env:USERPROFILE\.cloudflared\[UUID].json" ".\cloudflared\credentials.json"
```

### 3. DNS 라우팅 설정

#### 방법 1: Cloudflare 대시보드에서 수동 설정

1. Cloudflare 대시보드 접속
2. 도메인 선택
3. DNS > Records로 이동
4. CNAME 레코드 추가:
   - **이름**: `deep-guardian` (또는 원하는 서브도메인)
   - **대상**: `[터널 UUID].cfargotunnel.com`
   - **프록시**: 활성화 (주황색 구름)
   - **TTL**: Auto

#### 방법 2: 명령줄로 자동 설정

```powershell
cloudflared tunnel route dns deep-guardian-tunnel deep-guardian.your-domain.com
```

### 4. 설정 파일 수정

`cloudflared/config.yml` 파일을 열어 도메인을 수정하세요:

```yaml
ingress:
  # 실제 도메인으로 변경
  - hostname: deep-guardian.your-domain.com
    service: http://web-server:80
```

### 5. 터널 시작

```powershell
docker-compose up -d cloudflared
```

### 6. 상태 확인

```powershell
# 로그 확인
docker-compose logs -f cloudflared

# 터널 상태 확인
cloudflared tunnel info deep-guardian-tunnel
```

## 접근 방법

설정이 완료되면 다음 URL로 접근할 수 있습니다:

- **메인 대시보드**: `https://deep-guardian.your-domain.com`
- **직접 접근**: `https://deep-guardian.your-domain.com:8501` (설정에 따라)

## 문제 해결

### 터널이 시작되지 않음

1. Credentials 파일 확인:
   ```powershell
   Test-Path .\cloudflared\credentials.json
   ```

2. 설정 파일 확인:
   ```powershell
   Get-Content .\cloudflared\config.yml
   ```

3. 로그 확인:
   ```powershell
   docker-compose logs cloudflared
   ```

### DNS가 작동하지 않음

1. DNS 전파 확인 (최대 24시간 소요, 보통 몇 분)
2. Cloudflare 대시보드에서 DNS 레코드 확인
3. 프록시가 활성화되어 있는지 확인 (주황색 구름)

### 연결 오류

1. Docker 컨테이너가 실행 중인지 확인:
   ```powershell
   docker-compose ps
   ```

2. 네트워크 연결 확인:
   ```powershell
   docker-compose exec cloudflared ping dashboard
   ```

## 보안 고려사항

1. **인증 설정**: Cloudflare Access를 사용하여 추가 인증 설정 가능
2. **IP 제한**: Cloudflare 대시보드에서 특정 IP만 허용 가능
3. **Rate Limiting**: DDoS 방지를 위한 Rate Limiting 설정 가능

## 추가 기능

### Cloudflare Access 설정 (선택사항)

추가 보안을 위해 Cloudflare Access를 설정할 수 있습니다:

1. Cloudflare 대시보드 > Access > Applications
2. Application 추가
3. Policy 설정 (예: 이메일 도메인 기반)

### 커스텀 도메인

무료 도메인도 사용 가능합니다:
- Freenom (무료 .tk, .ml, .ga 등)
- DuckDNS (무료 서브도메인)
- Cloudflare에서 관리하는 모든 도메인

## 참고 자료

- Cloudflare Tunnel 공식 문서: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Cloudflared GitHub: https://github.com/cloudflare/cloudflared




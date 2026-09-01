# Cloudflare Tunnel 빠른 시작 가이드

## 방법 1: Quick Tunnel (가장 간단, 추천)

별도 설정 없이 바로 사용할 수 있는 방법입니다.

### 시작하기

```powershell
.\cloudflared\quick_tunnel.ps1
```

또는 직접 실행:

```powershell
cloudflared tunnel --url http://localhost:80
```

### 특징

- ✅ **설정 불필요**: 별도 계정이나 도메인 불필요
- ✅ **즉시 사용**: 명령 한 줄로 시작
- ✅ **임시 URL**: 매번 새로운 URL 생성
- ⚠️ **임시성**: 재시작 시 URL 변경됨

### 사용 예시

```powershell
# 포트 80 (Nginx) 터널링
cloudflared tunnel --url http://localhost:80

# 포트 8501 (Dashboard) 터널링  
cloudflared tunnel --url http://localhost:8501
```

## 방법 2: 영구 터널 (도메인 필요)

영구적인 URL을 원하는 경우 사용합니다.

### 1. 설정 스크립트 실행

```powershell
.\setup_cloudflare_tunnel.ps1
```

### 2. DNS 설정

Cloudflare 대시보드에서 CNAME 레코드 추가:
- 이름: `deep-guardian`
- 대상: `[터널 UUID].cfargotunnel.com`
- 프록시: 활성화

### 3. config.yml 수정

`cloudflared/config.yml`에서 도메인 변경:
```yaml
- hostname: deep-guardian.your-domain.com  # 실제 도메인으로
```

### 4. 터널 시작

```powershell
docker-compose up -d cloudflared
```

## 문제 해결

### Quick Tunnel이 작동하지 않음

1. Cloudflared 설치 확인:
   ```powershell
   cloudflared --version
   ```

2. 포트 확인:
   ```powershell
   netstat -an | findstr ":80"
   ```

### 영구 터널 오류

1. Credentials 파일 확인:
   ```powershell
   Test-Path .\cloudflared\credentials.json
   ```

2. 로그 확인:
   ```powershell
   docker-compose logs cloudflared
   ```

3. 터널 재생성:
   ```powershell
   cloudflared tunnel delete deep-guardian-tunnel
   cloudflared tunnel create deep-guardian-tunnel
   ```

## 추천 방법

**개발/테스트**: Quick Tunnel 사용
**프로덕션**: 영구 터널 사용




# Cloudflare Tunnel 설정

이 디렉토리는 Cloudflare Tunnel 설정 파일을 포함합니다.

## 파일 구조

- `config.yml`: 터널 설정 파일
- `Dockerfile`: Cloudflared 컨테이너 빌드 파일
- `credentials.json`: 터널 인증 정보 (자동 생성, Git에 커밋하지 않음)

## 빠른 시작

1. `setup_cloudflare_tunnel.ps1` 스크립트 실행
2. DNS 라우팅 설정
3. `docker-compose up -d cloudflared` 실행

자세한 내용은 `CLOUDFLARE_TUNNEL_SETUP.md`를 참조하세요.




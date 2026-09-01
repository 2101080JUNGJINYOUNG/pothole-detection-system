# PostgreSQL 5-Container 아키텍처 (이전 버전)

한때 메인 구조였던 5-컨테이너 구성입니다(Apache + Streamlit + AI Core +
PostgreSQL + Cloudflare Tunnel). 하지만 팀이 최종 발표에서 공식적으로 제시한
아키텍처는 [`docs/references/`](../../docs/references/)의 발표자료에 있는
**2-컨테이너 LAMP 구조**(`lamp-container/` + `inference-container/`, MySQL)이므로,
지금은 이쪽이 저장소의 메인이고 이 폴더는 참고용으로 보관합니다.

## 내용물

- `apache/` — Reverse Proxy 컨테이너 (Streamlit 앞단)
- `dashboard/` — Streamlit 대시보드 (Gemini 요약, Ollama 챗봇 등 LAMP 쪽보다 기능이 더 많았던 버전)
- `ai-core/` — YOLOv8 탐지 + NPU Worker 호출 (PostgreSQL 버전)
- `database/` — PostgreSQL 초기화/마이그레이션 스크립트
- `nginx/` — Apache 대안으로 검토했던 Nginx 설정
- `docker-compose.yml` — 이 5-컨테이너 구조를 실행하는 원본 compose 파일

## 실행 방법 (참고용)

```powershell
docker-compose -f archive/postgresql-5container/docker-compose.yml up -d --build
```

`shared_images/`, `models/`은 현재 메인 구조와 공유하지만, `.env`의
`DATABASE_URL`을 PostgreSQL용으로 바꿔야 하는 등 별도 설정이 필요합니다.

# Archive — 지금 메인이 아닌 코드

지금 실제로 쓰는 구성은 저장소 루트의 `docker-compose.yml`(`lamp-container` +
`inference-container`, MySQL 기반 — 팀 발표자료의 공식 아키텍처)입니다. 이 폴더는
그 외의 것들을 보관합니다. 자세한 경위는
[`docs/PROJECT_HISTORY.md`](../docs/PROJECT_HISTORY.md)를 참고하세요.

## 내용물

- **[`postgresql-5container/`](./postgresql-5container/)** — 한때 메인이었던
  5-컨테이너(Apache+Streamlit+AI Core+PostgreSQL+Cloudflare Tunnel) 구조. 팀
  발표자료의 공식 아키텍처와 달라서 이제는 참고용입니다.
- **`app/` + `docker-compose-optimized.yml`** — 컨테이너를 3개(app 통합+db+
  cloudflared)로 줄여보려던 별도 실험. PostgreSQL 기반이라 위와 마찬가지로
  지금 메인 구조와는 다릅니다.

  ```powershell
  docker-compose -f archive/docker-compose-optimized.yml up -d --build
  ```

- **[`legacy/`](./legacy/)** — NPU/SLM 워커 쪽에서 더 나은 버전으로 대체된
  초기 구현들(RBLN 기반 깊이 추정, 미완성 SLM 워커 등).
- **[`docs/`](./docs/)** — 위 폐기된 구조들 전용 기술 문서.

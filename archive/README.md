# Archive — 폐기된 아키텍처 실험

이 폴더는 현재 사용 중이 아닌 코드입니다. 지금 실제로 쓰는 구성은 저장소 루트의
`docker-compose.yml`(5-컨테이너, PostgreSQL)입니다.

여기 있는 것들은 컨테이너 수를 줄이려고 시도했다가 최종적으로 5-컨테이너 구조로
되돌아가면서 남은 실험 코드입니다. 자세한 경위는 [`docs/PROJECT_HISTORY.md`](../docs/PROJECT_HISTORY.md)를 참고하세요.

## 내용물

- **`lamp-container/` + `inference-container/`** — 2-컨테이너(Apache+MySQL+Flask 통합 / YOLO 추론 분리) 구조 시도. 기능은 상당 부분 채워 넣었지만, 이 둘을 연결해서 실행할 `docker-compose.yml`이 없어서 **지금 상태로는 실행 자체가 불가능**합니다.
- **`app/` + `docker-compose-optimized.yml`** — 3-컨테이너(Streamlit 대시보드+AI 엔진 통합 컨테이너 + PostgreSQL + Cloudflare Tunnel) 구조 시도. 이쪽은 지금도 아래 명령으로 실행은 가능하지만, 실제로 쓰고 있지는 않습니다.

```powershell
docker-compose -f archive/docker-compose-optimized.yml up -d --build
```

관련 기술 문서는 [`archive/docs/`](./docs/)에 함께 있습니다.

- **[`legacy/`](./legacy/)** — 위 아키텍처 실험과는 별개로, NPU/SLM 워커 쪽에서
  더 나은 버전으로 대체된 초기 구현들(RBLN 기반 깊이 추정, 미완성 SLM 워커 등).

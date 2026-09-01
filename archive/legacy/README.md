# Legacy — 더 이상 쓰이지 않는 초기 버전

지금 실제로 쓰는 코드는 저장소 루트의 `npu_worker.py`(깊이 추정)와
`slm_npu_worker_phi3.py`(Phi-3 챗봇)입니다. 이 폴더는 그 이전에 있었던
초기 시도들로, 전부 더 나은 버전으로 대체되어 더 이상 사용되지 않습니다.

- **`inference_npu.py`, `example_usage.py`, `setup.ps1`** — RBLN NPU 기반의
  초기 깊이 추정 구현. 이후 OpenVINO 기반 `npu_worker.py`로 완전히 대체됨.
- **`slm_npu_worker.py`** — Phi-3 챗봇 워커의 초기 시도. 토크나이저 부분이
  미완성(`NotImplementedError`)인 채로 남아있음. `slm_npu_worker_phi3.py`가
  완성된 버전.
- **`slm_npu_chatbot.py`** — `dashboard/slm_npu_chatbot.py`의 이전 버전
  (날짜 범위 파싱, 위험도 높은 포트홀 목록 조회 등 일부 기능이 빠져 있음).
  Docker가 마운트하는 건 `dashboard/` 쪽이라 이 버전은 실행 경로에 걸리지 않음.
- **`config.example.json`** — `npu_worker.py`가 아직 JSON 설정 파일을 읽던
  시절의 예시. 지금은 `--model`/`--device`/`--port` 등 커맨드라인 인자로
  설정합니다.

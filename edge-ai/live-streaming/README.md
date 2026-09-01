# Live Streaming — UDP 기반 엣지 실시간 추론 프로토타입

메인 시스템(Docker + PostgreSQL + Django ORM)과는 완전히 별개인, 훨씬 가벼운
엣지 우선 파이프라인 프로토타입입니다. 카메라(또는 저장된 영상)를 촬영하는
쪽과 YOLO 추론을 수행하는 쪽을 UDP로 분리했습니다.

```
[camera.py]  --UDP(영상 프레임 + GPS)-->  [server.py]  --YOLO 추론+SQLite+업로드-->  [원격 서버]
```

## `camera.py` — 송신 측

영상 파일(또는 실제 카메라)의 프레임을 읽어 JPEG로 압축한 뒤, `edge-ai/gps-route/`의
`PRESET_POINTS`로 프레임마다 GPS 좌표를 보간해 붙여서 UDP로 전송합니다.

```bash
python camera.py   # 같은 폴더에 테스트용 영상 파일이 필요합니다
```

## `server.py` — 수신 측 (파일 내부 원래 이름: `local_worker.py`)

UDP로 프레임+GPS를 받아 로컬에서 YOLO 추론을 수행하고, IoU 기반으로 같은
포트홀의 중복 탐지를 걸러낸 뒤 로컬 SQLite(`pothole_local.db`)에 저장하고
비동기 큐로 원격 서버에 업로드합니다.

```bash
python server.py   # 같은 폴더에 학습된 모델(예: dec2.pt)이 필요합니다
```

## 참고

메인 시스템의 파이프라인(`ai-core/main.py`)은 PostgreSQL + Django ORM +
Docker 컨테이너 구조인 반면, 이 프로토타입은 UDP + SQLite로 훨씬 가볍게
구성돼 있습니다 — 라즈베리파이 같은 저사양 엣지 기기에서 로컬 추론이
가능한지 확인해보기 위한 별도 실험입니다.

# GPS Route — 주행 경로 좌표 생성

실제 GPS 로그 없이도, 미리 그려둔 주행 경로(KMZ)로부터 좌표를 뽑아 비디오
데모에 사용하기 위한 유틸리티입니다.

## 사용법

```bash
python map.py
```

같은 폴더의 `route.kmz`(Google Earth 등에서 그린 주행 경로 파일)를 읽어 좌표
리스트를 추출하고, `route_points.py`에 `PRESET_POINTS = [(lat, lon), ...]` 형태로
저장합니다. `route_points.py`는 이미 한 번 생성된 예시 결과물입니다.

`edge-ai/live-streaming/server.py`가 이 `PRESET_POINTS`를 읽어서, 비디오
프레임 번호에 맞춰 좌표를 선형보간(`get_interpolated_coord`)한 뒤 각 프레임에
GPS 좌표를 붙여 보냅니다 — 실제 GPS 모듈 없이 위치 기반 데모를 만들기 위한
방법입니다.

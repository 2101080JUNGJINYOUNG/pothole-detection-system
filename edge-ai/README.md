# Edge AI — 엣지 배포 실험

메인 시스템(`ai-core/` + `dashboard/` + `django_app/` + Docker 5-컨테이너 구성)과는
**독립적인** 실험 코드 모음입니다. 학습된 YOLOv8n 포트홀 탐지 모델을 라즈베리파이 등
엣지 기기에서 구동하기 위한 시도들을 모아 두었습니다. 아직 메인 파이프라인과
연결돼 있지 않습니다.

## 구성

- [`model-conversion/`](model-conversion/) — `best.pt`(PyTorch) → ONNX → TensorFlow →
  TFLite(INT8) 변환 스크립트
- [`gps-route/`](gps-route/) — KMZ 주행 경로 파일에서 GPS 좌표를 추출하고, 비디오
  프레임에 맞춰 좌표를 선형보간하는 유틸리티
- [`live-streaming/`](live-streaming/) — 카메라(또는 영상 파일)를 UDP로 스트리밍하고,
  수신 측에서 실시간 YOLO 추론 + 로컬 SQLite 저장 + 서버 업로드까지 수행하는
  경량 엣지 파이프라인 프로토타입

## 배경

원래 이 코드는 프로젝트 폴더 밖(카카오톡으로 공유된 압축 파일)에 있었고, 경로
흔적(`C:\Users\spick\...`)으로 보아 팀의 다른 구성원/환경에서 작업된 것으로
보입니다. 같은 포트홀 탐지 모델을 다루고 있어 이 저장소로 함께 옮겼습니다.
연구 배경이 되는 논문은 [`docs/references/`](../docs/references/)를 참고하세요.

## 참고

- 원본 압축 파일에는 이 코드들이 참조하는 학습된 모델 파일(`best.pt`/`best.onnx`)과
  대용량 데모 영상이 함께 있었지만, 저장소 용량 문제로 코드만 가져왔습니다.
  실행하려면 `ai-core/models/best2.pt`(또는 동등한 모델)를 준비해야 합니다.
- 오픈소스 `onnx2tf` 라이브러리는 코드를 그대로 가져오지 않고
  `pip install onnx2tf`로 설치해서 사용하도록 정리했습니다.

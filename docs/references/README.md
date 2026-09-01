# References

## 기계학습+논문.pdf

**"Improvement of the YOLOv8n Model for Pothole Detection"** — CLAHE, Sobel/
Canny/Laplacian 엣지 검출, Superpixel, Feature Fusion(R:Sobel, G:Superpixel,
B:Grayscale 채널 합성) 등의 전처리 기법으로 YOLOv8n의 포트홀 탐지 성능을
개선하려 한 연구입니다. AI Hub 데이터셋으로 데이터셋을 구성했습니다.

관련 코드: [`../../test.py`](../../test.py) — 이 논문의 전처리 파이프라인
(Log/Gamma 변환, Superpixel, Sobel, 3채널 Feature Fusion 합성)을 그대로
구현한 실험 스크립트입니다. 참고로 이 전처리는 현재 `ai-core/main.py`의
실제 운영 추론 코드에는 아직 통합되지 않은 상태입니다 — 연구용 실험과
운영 파이프라인이 분리돼 있습니다.

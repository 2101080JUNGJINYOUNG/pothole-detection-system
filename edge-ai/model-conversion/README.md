# Model Conversion — PyTorch → ONNX → TensorFlow → TFLite

학습된 YOLOv8n 가중치(`best.pt`)를 라즈베리파이 / Coral Edge TPU 등에서 돌릴 수
있는 TFLite(INT8) 모델로 변환하는 스크립트 3개입니다. 순서대로 실행합니다.

## 설치

```bash
pip install ultralytics onnx onnxslim onnx-tf tensorflow onnx2tf sng4onnx onnxsim
```

## 1. `convert_to_onnx.py` — PyTorch → ONNX

```bash
MODEL_PATH=best.pt ONNX_OUTPUT_PATH=best.onnx python convert_to_onnx.py
```
Opset 12, 입력 크기 640×640으로 고정 변환(라즈베리파이 호환성 목적).

## 2. ONNX → TensorFlow → TFLite (두 가지 방식 중 하나 선택)

**방식 A — `convert_to_tflite.py`**: `onnx-tf` 라이브러리로 ONNX → TF SavedModel →
TFLite(INT8, Flex Ops 포함)까지 한 번에 처리합니다.

```bash
ONNX_MODEL_PATH=best.onnx TF_SAVED_MODEL_DIR=converttflite TFLITE_MODEL_PATH=tflite/best.tflite python convert_to_tflite.py
```

**방식 B — `onnx_to_tensorflow.py`**: `onnx2tf` CLI(별도 설치 필요)를 호출해서
ONNX → TensorFlow SavedModel로 변환합니다(이후 TFLite 변환은 별도로 진행).

```bash
ONNX_MODEL_PATH=best.onnx TF_OUTPUT_DIR=tensorflow python onnx_to_tensorflow.py
```

두 스크립트는 서로 다른 라이브러리(`onnx-tf` vs `onnx2tf`)를 쓰는 대안적 실험이며,
YOLO 모델 구조상 어느 한쪽이 실패할 경우 다른 쪽을 시도해보는 용도로 함께
남겨두었습니다.

## 주의

- 모든 경로는 환경 변수로 뺐습니다(원본은 `C:\Users\...` 절대경로가 하드코딩돼
  있었습니다) — 실행 전 자신의 환경에 맞게 지정하세요.
- `onnx2tf` 라이브러리 코드 자체는 저장소에 포함하지 않았습니다. 위 설치 명령으로
  `pip install onnx2tf`를 하면 됩니다.

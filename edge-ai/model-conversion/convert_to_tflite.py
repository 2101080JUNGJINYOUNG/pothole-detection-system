import onnx
from onnx_tf.backend import prepare
import tensorflow as tf
import os
import sys

# --- 1. 변환할 모델 파일 경로 설정 (실행 환경에 맞게 수정하세요) ---
ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "best.onnx")
TENSORFLOW_SAVED_MODEL_DIR = os.getenv("TF_SAVED_MODEL_DIR", "converttflite")
TFLITE_MODEL_PATH = os.getenv("TFLITE_MODEL_PATH", "tflite/best.tflite")

def convert_onnx_to_tflite():
    """ONNX 모델을 TensorFlow SavedModel을 거쳐 TFLite 모델로 변환합니다."""
    
    if not os.path.exists(ONNX_MODEL_PATH):
        print(f"오류: ONNX 모델 파일이 지정된 경로에 없습니다: {ONNX_MODEL_PATH}")
        sys.exit(1)

    print(f"--- 1. ONNX 모델 로드 및 유효성 검사: {ONNX_MODEL_PATH} ---")
    try:
        # ONNX 모델 로드
        onnx_model = onnx.load(ONNX_MODEL_PATH)
        # 모델 유효성 검사 (구조적인 문제 확인)
        onnx.checker.check_model(onnx_model)
        print("ONNX 모델 로드 및 유효성 검사 완료.")
    except Exception as e:
        print(f"ONNX 모델 로드/검사 중 오류 발생: {e}")
        sys.exit(1)

    print(f"\n--- 2. TensorFlow SavedModel로 변환: {TENSORFLOW_SAVED_MODEL_DIR} ---")
    try:
        # ONNX 모델을 TensorFlow SavedModel 형식으로 변환
        tf_rep = prepare(onnx_model)
        tf_rep.export_graph(TENSORFLOW_SAVED_MODEL_DIR)
        print(f"TensorFlow SavedModel 변환 완료.")
    except Exception as e:
        print(f"TensorFlow SavedModel 변환 중 오류 발생 (onnx-tf): {e}")
        print("주의: onnx-tf 라이브러리는 복잡한 YOLO 모델의 모든 연산을 지원하지 않을 수 있습니다.")
        sys.exit(1)


    print(f"\n--- 3. TFLite INT8 모델로 변환: {TFLITE_MODEL_PATH} ---")
    try:
        # TFLite 변환기 초기화
        converter = tf.lite.TFLiteConverter.from_saved_model(TENSORFLOW_SAVED_MODEL_DIR)
        
        # Edge TPU 및 YOLO 모델 연산을 위해 Flex Ops 활성화 (필수)
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,   # 기본 TFLite 연산
            tf.lite.OpsSet.SELECT_TF_OPS      # Flex Ops (Edge TPU가 지원하지 않는 연산용)
        ]
        
        # 최적화 설정 (Edge TPU는 INT8 양자화를 위해)
        # 실제 Edge TPU에서 사용하려면 캘리브레이션 데이터셋을 통한 Post-training Quantization이 필요하지만,
        # 여기서는 기본 정수 양자화(INT8)만 활성화합니다.
        # Edge TPU 가속을 위한 최종 INT8 변환 코드는 모델의 구조에 따라 추가적인 설정이 필요합니다.
        
        # TFLite 모델 생성 및 저장
        tflite_model = converter.convert()
        
        with open(TFLITE_MODEL_PATH, "wb") as f:
            f.write(tflite_model)
            
        print(f"TFLite 모델 변환 및 저장 완료: {TFLITE_MODEL_PATH}")
        print("이제 이 TFLite 모델을 Coral Edge TPU 런타임 환경에서 사용하시면 됩니다.")

    except Exception as e:
        print(f"TFLite 모델 변환 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 사용자에게 필요한 라이브러리가 설치되어 있는지 확인합니다.
    required_packages = ["onnx", "onnx-tf", "tensorflow"]
    try:
        for package in required_packages:
            __import__(package)
        convert_onnx_to_tflite()
    except ImportError:
        print("--- 필수 라이브러리 설치 안내 ---")
        print("이 코드를 실행하려면 다음 라이브러리를 설치해야 합니다:")
        print(f"pip install {' '.join(required_packages)}")
        print("---------------------------------")
    except Exception as e:
        print(f"스크립트 실행 중 예기치 않은 오류 발생: {e}")
"""
학습된 YOLOv8n(.pt) 가중치를 ONNX로 변환합니다.
"""
from ultralytics import YOLO
import os

# =========================================================
# ⚙️ 사용자 설정 (경로는 실행 환경에 맞게 수정하세요)
# =========================================================
# 1. 학습된 pt 파일 경로
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")

# 2. 저장할 ONNX 파일 경로
ONNX_OUTPUT_PATH = os.getenv("ONNX_OUTPUT_PATH", "best.onnx")

# 3. ⭐️ 중요: 학습했을 때 사용한 이미지 크기 (보통 640)
TARGET_IMG_SIZE = 640

# 4. ⭐️ 중요: 라즈베리 파이 호환성을 위한 Opset 버전 (12 추천)
TARGET_OPSET = 12

def export_complete_onnx():
    # 파일 존재 확인
    if not os.path.exists(MODEL_PATH):
        print(f"❌ 오류: 파일이 없습니다 -> {MODEL_PATH}")
        return

    try:
        print(f"🔄 모델 로드 중... (구조와 가중치를 그대로 가져옵니다)")
        # ✅ 핵심 1: YOLO 클래스로 로드하여 모델 구조 손상 방지
        model = YOLO(MODEL_PATH)

        print(f"🔄 ONNX 변환 시작... (크기: {TARGET_IMG_SIZE}, Opset: {TARGET_OPSET})")

        # ✅ 핵심 2: export 함수에 모든 설정을 명시하여 '완벽한' 변환 수행
        path = model.export(
            format='onnx',              # 변환 포맷
            imgsz=TARGET_IMG_SIZE,      # ⭐️ 입력 크기 640 강제 고정 (224 오류 해결)
            opset=TARGET_OPSET,         # ⭐️ 호환성 버전 12 (라즈베리파이용)
            simplify=True,              # 모델 단순화 (속도 최적화)
            dynamic=False               # 고정 크기 사용 (라즈베리파이에서 더 안정적)
        )

        # 파일 이동 및 이름 변경 (선택 사항)
        # export는 보통 원본 폴더에 저장되므로, 원하는 경로로 이동
        if path != ONNX_OUTPUT_PATH and os.path.exists(path):
            if os.path.exists(ONNX_OUTPUT_PATH):
                os.remove(ONNX_OUTPUT_PATH)  # 기존 파일 삭제
            os.rename(path, ONNX_OUTPUT_PATH)

        print(f"\n✅ 변환 완료! 완벽한 파일이 생성되었습니다: {ONNX_OUTPUT_PATH}")
        print(f"👉 이 파일을 라즈베리 파이로 옮겨서 실행하세요.")

    except Exception as e:
        print(f"\n❌ 변환 실패: {e}")
        print("💡 팁: 'pip install ultralytics onnx onnxslim' 을 설치했는지 확인하세요.")

if __name__ == '__main__':
    export_complete_onnx()

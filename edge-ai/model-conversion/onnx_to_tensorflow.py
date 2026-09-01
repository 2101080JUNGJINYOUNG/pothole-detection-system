import os
import shutil
import subprocess

# =========================================================
# ⚙️ 사용자 설정 영역
# =========================================================
ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "best.onnx")       # 변환할 ONNX 파일 경로 (640x640 권장)
TF_OUTPUT_DIR = os.getenv("TF_OUTPUT_DIR", "tensorflow")          # 저장될 TensorFlow 모델 폴더명

def convert_onnx_to_tf():
    # 1. ONNX 파일 확인
    if not os.path.exists(ONNX_MODEL_PATH):
        print(f"❌ 오류: {ONNX_MODEL_PATH} 파일이 없습니다. 경로를 확인하세요.")
        return

    # 2. 기존 출력 폴더가 있으면 삭제 (충돌 방지)
    if os.path.exists(TF_OUTPUT_DIR):
        print(f"🗑️ 기존 {TF_OUTPUT_DIR} 폴더를 삭제하고 새로 만듭니다...")
        shutil.rmtree(TF_OUTPUT_DIR)

    print(f"\n🚀 변환 시작: {ONNX_MODEL_PATH} -> TensorFlow SavedModel")
    print("=" * 50)

    # 3. onnx2tf 명령어 실행
    # -i: 입력 파일
    # -o: 출력 폴더
    # -osp: static shape 최적화 (매우 중요)
    # -tps: Transpose 최적화 (NCHW -> NHWC 자동 변환의 핵심)
    command = f'onnx2tf -i "{ONNX_MODEL_PATH}" -o "{TF_OUTPUT_DIR}" -osp -tps'
    
    try:
        # subprocess를 사용하여 터미널 명령어를 Python에서 실행
        result = subprocess.run(command, shell=True, check=True)
        
        print("=" * 50)
        print(f"✅ 변환 성공! 저장 위치: {os.path.abspath(TF_OUTPUT_DIR)}")
        print("👉 이제 이 saved_model 폴더를 사용하여 TFLite로 변환하면 됩니다.")
        
    except subprocess.CalledProcessError as e:
        print("=" * 50)
        print(f"❌ 변환 실패! 오류 코드: {e.returncode}")
        print("💡 힌트: 'pip install onnx2tf sng4onnx onnxsim'이 설치되었는지 확인하세요.")

if __name__ == '__main__':
    convert_onnx_to_tf()
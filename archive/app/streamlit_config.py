# Streamlit 설정 파일
# shared_images를 정적 파일로 서빙하기 위한 설정

import os

# Streamlit 정적 파일 디렉토리 설정
STATIC_DIR = "/app/dashboard/.streamlit/static"
SHARED_IMAGES_DIR = "/app/shared_images"

# 심볼릭 링크 생성 (이미 start.sh에서 처리)
if os.path.exists(SHARED_IMAGES_DIR) and not os.path.exists(f"{STATIC_DIR}/shared_images"):
    os.makedirs(STATIC_DIR, exist_ok=True)
    try:
        os.symlink(SHARED_IMAGES_DIR, f"{STATIC_DIR}/shared_images")
    except Exception as e:
        print(f"Warning: Could not create symlink: {e}")


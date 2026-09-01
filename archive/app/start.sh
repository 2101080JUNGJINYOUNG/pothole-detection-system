#!/bin/bash

# AI-core를 백그라운드로 실행
cd /app/ai-core
python3 main.py &
AI_CORE_PID=$!
echo "[INFO] AI-core started with PID: $AI_CORE_PID"

# Streamlit을 포트 80으로 실행
cd /app/dashboard
# 포트 80은 root 권한이 필요하므로, setcap으로 권한 부여 또는 root로 실행
# shared_images를 정적 파일로 서빙하기 위해 심볼릭 링크 생성
mkdir -p /app/dashboard/.streamlit/static
ln -sf /app/shared_images /app/dashboard/.streamlit/static/shared_images 2>/dev/null || true
# Streamlit 실행 (정적 파일 서빙 활성화)
# Streamlit은 기본적으로 .streamlit/static 디렉토리를 /static 경로로 서빙
streamlit run app.py \
    --server.port=80 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableStaticServing=true \
    &
STREAMLIT_PID=$!
echo "[INFO] Streamlit started with PID: $STREAMLIT_PID"
echo "[INFO] Static files available at: http://localhost/static/shared_images/"

# 프로세스 종료 시그널 처리
cleanup() {
    echo "[INFO] Shutting down..."
    kill $AI_CORE_PID $STREAMLIT_PID 2>/dev/null
    wait $AI_CORE_PID $STREAMLIT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGTERM SIGINT

# 프로세스가 실행 중인지 주기적으로 확인
while true; do
    if ! kill -0 $AI_CORE_PID 2>/dev/null; then
        echo "[ERROR] AI-core process died, restarting..."
        cd /app/ai-core
        python3 main.py &
        AI_CORE_PID=$!
    fi
    if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "[ERROR] Streamlit process died, restarting..."
        cd /app/dashboard
        mkdir -p /app/dashboard/.streamlit/static
        ln -sf /app/shared_images /app/dashboard/.streamlit/static/shared_images 2>/dev/null || true
        streamlit run app.py \
            --server.port=80 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --server.enableStaticServing=true \
            &
        STREAMLIT_PID=$!
    fi
    sleep 10
done


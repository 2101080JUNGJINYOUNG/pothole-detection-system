FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# 시스템 패키지 설치 (한 번에 처리하여 레이어 최적화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 패키지 설치 (requirements.txt를 먼저 복사하여 캐싱 최적화)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 모델 디렉토리 생성
RUN mkdir -p /app/models /app/videos /app/dashboard/.streamlit/static

# 시작 스크립트 복사
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 포트 노출 (Streamlit 포트 80으로 직접 서빙)
EXPOSE 80

# 시작 스크립트 실행 (Streamlit + AI-core 백그라운드)
# root로 실행하여 포트 80 접근 가능
CMD ["/app/start.sh"]


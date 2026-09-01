# GPU 지원 설정 가이드

## 문제 상황
WSL2 환경에서 Docker 컨테이너에 GPU를 전달할 때 다음 오류 발생:
```
nvidia-container-cli: initialization error: WSL environment detected but no adapters were found
```

## 해결 방법

### 1. WSL2에서 NVIDIA 드라이버 확인

WSL2 내부에서 다음 명령어 실행:
```bash
# WSL2 터미널에서 실행
nvidia-smi
```

**예상 결과:**
- NVIDIA 드라이버가 설치되어 있으면 GPU 정보가 표시됨
- 오류가 발생하면 Windows에서 NVIDIA 드라이버 설치 필요

### 2. Windows에서 NVIDIA 드라이버 설치

1. NVIDIA 공식 웹사이트에서 최신 드라이버 다운로드
2. WSL2용 드라이버 설치 (Windows 11의 경우 자동 포함)
3. Windows 재시작

### 3. WSL2에서 NVIDIA Container Toolkit 설치

WSL2 터미널에서 실행:
```bash
# Ubuntu/Debian 기반 WSL2의 경우
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 4. Docker Desktop 설정 확인

1. Docker Desktop 열기
2. Settings → Resources → WSL Integration
3. 사용 중인 WSL 배포판 활성화 확인

### 5. GPU 지원 테스트

WSL2 터미널에서:
```bash
docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
```

### 6. 대안: CPU 모드 사용

GPU가 사용 불가능한 경우, CPU 모드로 실행:
- 현재 docker-compose.yml에서 GPU 설정이 주석 처리되어 있으면 CPU 모드로 실행됨
- YOLOv8은 CPU에서도 작동하지만 속도가 느림

## 현재 상태

- ✅ GPU 설정: docker-compose.yml에 활성화됨
- ❌ WSL2 GPU 어댑터: 인식되지 않음
- ✅ CPU 모드: 정상 작동 중

## 권장 사항

1. **즉시 사용**: CPU 모드로 계속 사용 (현재 정상 작동)
2. **GPU 활성화**: WSL2에서 NVIDIA 드라이버 및 Container Toolkit 설치 후 재시도

## 참고 링크

- [NVIDIA Container Toolkit 설치 가이드](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [WSL2 GPU 지원 가이드](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)




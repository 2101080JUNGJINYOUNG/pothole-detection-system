# Intel Arc GPU 설정 가이드

## 시스템 정보
- **GPU**: Intel Arc Graphics (Arc A770 등)
- **드라이버 버전**: 32.0.101.8331
- **기기**: 아톰맥 x7ti185h

## 현재 시스템 구조

### 1. AI Core (Docker 컨테이너)
- **역할**: YOLOv8을 사용한 포트홀 탐지
- **실행 환경**: Docker 컨테이너 (CPU 모드)
- **위치**: `deep-guardian-ai` 컨테이너

### 2. NPU Worker (Windows 호스트)
- **역할**: OpenVINO를 사용한 깊이 추정 및 검증
- **실행 환경**: Windows 호스트 (Intel Arc GPU 활용 가능)
- **위치**: Windows 호스트에서 직접 실행
- **엔드포인트**: `http://host.docker.internal:9001/depth`

## Intel Arc GPU 활용 방법

### OpenVINO 디바이스 설정

Intel Arc GPU를 활용하려면 OpenVINO의 디바이스 설정을 변경합니다:

#### 옵션 1: AUTO 모드 (권장)
```python
device = "AUTO:GPU,CPU"
```
- Intel Arc GPU를 우선적으로 사용
- GPU를 사용할 수 없으면 CPU로 자동 전환

#### 옵션 2: GPU 직접 지정
```python
device = "GPU"
```
- Intel Arc GPU만 사용
- GPU를 사용할 수 없으면 오류 발생

#### 옵션 3: CPU만 사용
```python
device = "CPU"
```
- CPU만 사용 (GPU 미사용)

### 현재 설정

NPU Worker는 다음 설정으로 실행됩니다:
- **디바이스**: `AUTO:GPU,CPU` (Intel Arc GPU 우선)
- **포트**: 9001
- **호스트**: 0.0.0.0 (모든 인터페이스에서 접근 가능)

## NPU Worker 시작 방법

### 방법 1: PowerShell 스크립트 사용
```powershell
cd C:\Users\shkim1\Desktop\TEST
.\start_npu_worker.ps1
```

### 방법 2: 직접 실행
```powershell
# 가상환경 활성화
& $env:USERPROFILE\venv-atomman-win\Scripts\Activate.ps1

# NPU Worker 시작
python npu_worker.py --model "openvino_model.xml" --device "AUTO:GPU,CPU" --port 9001
```

## GPU 사용 확인

### 1. OpenVINO에서 사용 가능한 디바이스 확인

NPU Worker 시작 시 다음 메시지가 표시됩니다:
```
사용 가능한 디바이스: ['CPU', 'GPU']
```

### 2. 실제 사용 디바이스 확인

NPU Worker 로그에서 다음을 확인:
```
모델 컴파일 중... (디바이스: AUTO:GPU,CPU)
```

실제로 GPU가 사용되면:
- 추론 속도가 향상됨
- GPU 메모리 사용량 증가

### 3. Windows 작업 관리자에서 확인

1. 작업 관리자 열기 (Ctrl+Shift+Esc)
2. 성능 탭 → GPU 선택
3. NPU Worker 실행 중 GPU 사용률 확인

## 성능 최적화

### Intel Arc GPU 활용 시 기대 효과

1. **추론 속도 향상**
   - CPU 대비 2-5배 빠른 추론 속도
   - 배치 처리 시 더 큰 성능 향상

2. **CPU 부하 감소**
   - GPU가 추론 작업을 처리하여 CPU 여유 확보
   - 다른 작업과 병렬 처리 가능

3. **전력 효율**
   - GPU 전용 하드웨어 활용으로 전력 효율 향상

## 문제 해결

### GPU가 인식되지 않는 경우

1. **드라이버 확인**
   ```powershell
   # Windows에서 GPU 정보 확인
   Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion
   ```

2. **OpenVINO 설치 확인**
   ```powershell
   python -c "from openvino import Core; print(Core().available_devices)"
   ```

3. **디바이스 목록 확인**
   - NPU Worker 시작 시 "사용 가능한 디바이스" 메시지 확인
   - GPU가 목록에 없으면 CPU 모드로 자동 전환

### GPU 사용률이 낮은 경우

1. **작업 크기 확인**
   - 작은 이미지는 CPU가 더 효율적일 수 있음
   - 배치 크기 증가 고려

2. **메모리 확인**
   - GPU 메모리 부족 시 CPU로 자동 전환
   - 이미지 크기 조정 고려

## 참고 사항

- **Docker 컨테이너에서 GPU 사용**: Intel Arc GPU를 Docker 컨테이너에서 직접 사용하는 것은 복잡하므로, 현재 구조(호스트에서 NPU Worker 실행)가 더 효율적입니다.
- **YOLOv8**: AI Core의 YOLOv8은 CPU 모드로 실행되며, 이는 일반적으로 충분히 빠릅니다.
- **깊이 추정**: NPU Worker의 깊이 추정 작업이 더 계산 집약적이므로 GPU 활용의 이점이 큽니다.

## 현재 설정 요약

✅ **NPU Worker**: Intel Arc GPU 우선 사용 (`AUTO:GPU,CPU`)
✅ **AI Core**: CPU 모드 (YOLOv8은 CPU에서 충분히 빠름)
✅ **시스템**: 정상 작동 중




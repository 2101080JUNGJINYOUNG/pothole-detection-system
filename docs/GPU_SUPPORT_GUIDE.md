# GPU 지원 가이드

## 현재 GPU 지원 상태

### ✅ NPU Worker (Windows Host)
- **상태**: Intel Arc GPU 사용 중
- **설정**: `AUTO:GPU,CPU` (GPU 우선, 실패 시 CPU)
- **용도**: OpenVINO 기반 깊이 추정 (Depth Anything V2)
- **위치**: Windows Host에서 직접 실행
- **포트**: 9001

### ⚠️ AI Core (Docker Container)
- **상태**: CPU 모드
- **용도**: YOLOv8 기반 포트홀 탐지
- **위치**: Docker 컨테이너 내부
- **GPU 설정**: 주석 처리됨 (WSL2 제약)

## GPU 사용 현황

### NPU Worker GPU 사용
NPU Worker는 이미 Intel Arc GPU를 사용하도록 설정되어 있습니다:

```python
device = "AUTO:GPU,CPU"  # Intel Arc GPU 우선 사용
```

**확인 방법:**
1. NPU Worker 시작 시 로그 확인:
   ```
   사용 가능한 디바이스: ['CPU', 'GPU']
   모델 컴파일 중... (디바이스: AUTO:GPU,CPU)
   ```

2. Windows 작업 관리자에서 GPU 사용률 확인
   - 작업 관리자 → 성능 → GPU
   - NPU Worker 실행 중 GPU 사용률 확인

### AI Core GPU 사용 (선택사항)

AI Core의 YOLOv8도 GPU를 사용할 수 있지만, Intel Arc GPU는 NVIDIA CUDA를 사용하지 않으므로:

**옵션 1: 현재 구조 유지 (권장)**
- AI Core: CPU 모드 (YOLOv8은 CPU에서도 충분히 빠름)
- NPU Worker: GPU 모드 (깊이 추정은 계산 집약적)
- **장점**: 안정적, 설정 간단

**옵션 2: AI Core에서도 GPU 사용 시도**
- Intel Arc GPU를 Docker 컨테이너에서 사용하려면 추가 설정 필요
- OpenVINO를 사용하여 YOLOv8을 변환해야 함
- **단점**: 복잡한 설정, 성능 향상이 크지 않을 수 있음

## GPU 성능 최적화

### NPU Worker 최적화

1. **배치 처리**
   - 여러 이미지를 한 번에 처리하면 GPU 효율 향상
   - 현재는 단일 이미지 처리 (향후 개선 가능)

2. **GPU 메모리 관리**
   - 이미지 크기 조정으로 메모리 사용량 최적화
   - 배치 크기 조정

3. **디바이스 우선순위**
   - `AUTO:GPU,CPU`: GPU 우선, 실패 시 CPU
   - `GPU`: GPU만 사용 (실패 시 오류)
   - `CPU`: CPU만 사용

### AI Core 최적화 (CPU 모드)

1. **YOLOv8 최적화**
   - 모델 크기 조정 (nano, small, medium, large)
   - 이미지 크기 조정 (640x640 권장)

2. **프레임 샘플링**
   - 비디오 처리 시 프레임 간격 조정
   - 불필요한 프레임 건너뛰기

## GPU 사용 확인 방법

### 1. NPU Worker 로그 확인

NPU Worker 시작 시 다음 메시지 확인:
```
사용 가능한 디바이스: ['CPU', 'GPU']
모델 컴파일 중... (디바이스: AUTO:GPU,CPU)
```

### 2. Windows 작업 관리자

1. 작업 관리자 열기 (Ctrl+Shift+Esc)
2. 성능 탭 → GPU 선택
3. NPU Worker 실행 중 GPU 사용률 확인
4. GPU 엔진 사용률 확인 (Compute_0, Compute_1 등)

### 3. OpenVINO 디바이스 확인

NPU Worker 실행 중:
```python
from openvino import Core
core = Core()
print("Available devices:", core.available_devices)
```

### 4. 성능 측정

**GPU 사용 시:**
- 추론 시간: ~50-100ms (이미지당)
- GPU 메모리 사용: ~500MB-1GB

**CPU 사용 시:**
- 추론 시간: ~200-500ms (이미지당)
- CPU 사용률: 높음

## 문제 해결

### GPU가 인식되지 않는 경우

1. **드라이버 확인**
   ```powershell
   Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion
   ```
   - Intel Arc Graphics 드라이버 버전 확인
   - 최신 드라이버 설치 권장

2. **OpenVINO 설치 확인**
   ```powershell
   python -c "from openvino import Core; print(Core().available_devices)"
   ```
   - GPU가 목록에 없으면 드라이버 문제 가능

3. **NPU Worker 로그 확인**
   - "사용 가능한 디바이스" 메시지 확인
   - GPU가 없으면 CPU 모드로 자동 전환

### GPU 사용률이 낮은 경우

1. **작업 크기 확인**
   - 작은 이미지는 CPU가 더 효율적일 수 있음
   - 배치 크기 증가 고려

2. **메모리 확인**
   - GPU 메모리 부족 시 CPU로 자동 전환
   - 이미지 크기 조정 고려

3. **디바이스 설정 확인**
   - `AUTO:GPU,CPU` 사용 시 GPU 우선 사용
   - `GPU` 직접 지정 시 GPU만 사용

## 성능 비교

### NPU Worker (깊이 추정)

| 디바이스 | 추론 시간 (이미지당) | 메모리 사용 |
|---------|-------------------|------------|
| Intel Arc GPU | ~50-100ms | ~500MB-1GB |
| CPU | ~200-500ms | ~2-4GB |

### AI Core (YOLOv8 탐지)

| 디바이스 | 추론 시간 (이미지당) | 메모리 사용 |
|---------|-------------------|------------|
| CPU | ~20-50ms | ~1-2GB |
| GPU (NVIDIA) | ~5-15ms | ~500MB-1GB |

**참고**: YOLOv8은 CPU에서도 충분히 빠르므로 GPU 사용의 이점이 크지 않을 수 있습니다.

## 권장 설정

### 현재 시스템 (권장)

```
✅ NPU Worker: Intel Arc GPU 사용 (AUTO:GPU,CPU)
✅ AI Core: CPU 모드 (YOLOv8은 CPU에서 충분히 빠름)
✅ 시스템: 안정적이고 효율적
```

### 향후 개선 가능 사항

1. **NPU Worker 배치 처리**
   - 여러 이미지를 한 번에 처리하여 GPU 효율 향상

2. **AI Core GPU 사용** (선택사항)
   - OpenVINO로 YOLOv8 변환
   - Intel Arc GPU에서 실행
   - 성능 향상은 제한적일 수 있음

3. **모니터링 시스템**
   - GPU 사용률 모니터링
   - 성능 메트릭 수집

## 참고 자료

- [Intel Arc GPU 드라이버](https://www.intel.com/content/www/us/en/download/726609/intel-arc-iris-xe-graphics-windows.html)
- [OpenVINO 문서](https://docs.openvino.ai/)
- [YOLOv8 문서](https://docs.ultralytics.com/)

## 현재 설정 요약

✅ **NPU Worker**: Intel Arc GPU 우선 사용 (`AUTO:GPU,CPU`)
✅ **AI Core**: CPU 모드 (YOLOv8은 CPU에서 충분히 빠름)
✅ **시스템**: 정상 작동 중
✅ **성능**: 최적화됨




# Deep-Guardian 프로젝트 구조

## 전체 아키텍처

```
[User/Admin Browser]
        |
        v
[Container 1: web-server (Apache)]
- 역할: 외부 진입점(Gateway), Reverse Proxy
- 포트: 80
        |
        v
[Container 2: dashboard (Streamlit)]
- 역할: 지도/데이터 시각화(UI)
- 포트: 8501
        |
        v
[Container 4: db (PostgreSQL)]
- 역할: 포트홀 데이터 저장/조회
- 포트: 5432(내부)

[Container 3: ai-core (AI Engine)]
- 역할: 영상 입력 처리 + 포트홀 검출/검증 + DB 저장
- 처리 흐름:
  1) [GPU] YOLOv8 → pothole bbox 탐지
  2) pothole만 crop 생성
  3) [NPU] depth 모델로 깊이 검증 (Windows host worker 호출)
  4) 검증 통과 데이터만 DB 저장
        |
        v
[Windows Host: NPU Worker (OpenVINO)] ← 현재 작업 위치
- 역할: depth 모델 추론 서비스(HTTP)
- 호출: ai-core → http://host.docker.internal:9001/depth
- 출력: depth_ratio 등 검증 결과
```

## 현재 디렉토리 (TEST) 구조

```
TEST/
├── npu_worker.py              # NPU Worker HTTP 서버 (메인)
├── test_npu_worker.py         # NPU Worker 테스트 스크립트
├── start_npu_worker.ps1       # 서버 시작 스크립트
├── requirements.txt           # Python 패키지 의존성
├── README.md                  # 사용 설명서
├── config.example.json         # 설정 예제 파일
├── PROJECT_STRUCTURE.md       # 이 파일
│
├── inference_npu.py           # (레거시) RBLN 기반 추론 코드
├── example_usage.py           # (레거시) 사용 예제
└── setup.ps1                  # (레거시) 환경 설정 스크립트
```

## 주요 파일 설명

### npu_worker.py
- **역할**: OpenVINO 기반 NPU Worker HTTP 서버
- **기능**:
  - OpenVINO IR 모델 로딩 및 컴파일
  - `/health` 엔드포인트: 서버 상태 확인
  - `/depth` 엔드포인트: 이미지 입력 → 깊이 추정 → 검증 결과 반환
- **사용 디바이스**: AUTO:NPU,CPU (NPU 단독 불가, 혼합 모드만 가능)

### test_npu_worker.py
- **역할**: NPU Worker 서버 테스트
- **기능**: 헬스 체크 및 깊이 추정 API 테스트

### start_npu_worker.ps1
- **역할**: 서버 시작 스크립트
- **기능**: 가상환경 활성화 및 서버 시작

## 완료된 작업

1. ✅ Windows OpenVINO 환경 구축
   - 가상환경: `C:\Users\shkim1\venv-atomman-win`
   - 디바이스 인식: CPU, GPU, NPU 확인

2. ✅ Depth Anything V2 → OpenVINO IR 변환
   - 모델 파일: `openvino_model.xml`, `openvino_model.bin`

3. ✅ NPU 컴파일 가능 범위 확인
   - NPU 단독: 실패 (ZE_RESULT_ERROR_UNKNOWN)
   - AUTO:NPU,CPU: 성공 ✅

4. ✅ NPU Worker HTTP 서비스 구현
   - Flask 기반 HTTP 서버
   - OpenVINO 모델 로딩 및 추론
   - Docker 컨테이너 호출 지원 (host.docker.internal)

## 다음 단계

1. OpenVINO IR 모델 파일 위치 확인 및 설정
2. NPU Worker 서버 테스트
3. Docker 컨테이너(ai-core)에서 호출 테스트
4. 전체 시스템 통합 테스트

## 모델 파일 위치

OpenVINO IR 모델 파일이 다른 위치에 있는 경우:
- `npu_worker.py` 실행 시 `--model` 옵션으로 경로 지정
- 또는 모델 파일을 TEST 디렉토리로 복사

예시:
```powershell
python npu_worker.py --model "C:\path\to\openvino_model.xml"
```





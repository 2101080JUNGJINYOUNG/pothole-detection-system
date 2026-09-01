# Flask를 사용하는 이유

## NPU Worker의 역할

NPU Worker는 **Windows 호스트에서 실행되는 독립적인 HTTP 서버**입니다.

### 시스템 아키텍처

```
┌─────────────────┐         HTTP 요청          ┌──────────────────┐
│   AI Core       │  ────────────────────────> │   NPU Worker     │
│  (Docker)       │  <──────────────────────── │  (Windows Host)  │
│                 │      JSON 응답             │                  │
│  - YOLOv8       │                            │  - OpenVINO      │
│  - 포트홀 탐지   │                            │  - 깊이 추정      │
└─────────────────┘                            └──────────────────┘
```

## Flask를 사용하는 이유

### 1. **HTTP 서버 필요**
- AI Core (Docker 컨테이너)에서 Windows 호스트의 NPU Worker에 접근해야 함
- HTTP 프로토콜을 통해 통신해야 함
- RESTful API로 이미지를 받아서 결과를 반환해야 함

### 2. **간단하고 효율적**
- Flask는 경량 웹 프레임워크
- API 서버 구축에 적합
- 빠른 개발과 배포 가능

### 3. **CORS 지원**
- Docker 컨테이너에서 호스트로 접근 시 CORS 문제 해결
- `flask_cors`로 간단히 처리 가능

### 4. **멀티파트 파일 업로드**
- 이미지 파일을 `multipart/form-data`로 받기 쉬움
- Flask의 `request.files`로 간단히 처리

## NPU Worker API 엔드포인트

### 1. GET /health
- **용도**: 서버 상태 확인
- **메서드**: GET
- **응답**: JSON
  ```json
  {
    "status": "healthy",
    "model_loaded": true,
    "openvino_available": true,
    "model_path": "..."
  }
  ```

### 2. POST /depth
- **용도**: 깊이 추정 수행
- **메서드**: POST (이미지 파일 필요)
- **입력**: multipart/form-data (필드명: 'image')
- **응답**: JSON
  ```json
  {
    "success": true,
    "depth_ratio": 0.25,
    "validation_result": true,
    "depth_map_shape": [518, 518],
    "message": "추론 완료"
  }
  ```

### 3. POST /load_model
- **용도**: 런타임에 모델 로드
- **메서드**: POST
- **입력**: JSON
  ```json
  {
    "model_path": "path/to/model.xml",
    "device": "AUTO:GPU,CPU"
  }
  ```

## 왜 브라우저에서 접근이 안 되는가?

### GET /depth → Method Not Allowed
- `/depth` 엔드포인트는 **POST 메서드만 허용**
- 브라우저 주소창은 **GET 요청**을 보냄
- 따라서 "Method Not Allowed" 오류 발생

### 해결 방법

1. **Health Check (GET 허용)**
   ```
   http://127.0.0.1:9001/health
   ```
   브라우저에서 접근 가능

2. **Depth Inference (POST 필요)**
   - 브라우저로는 직접 테스트 불가
   - curl, Postman, Python requests 등 사용 필요

## 대안 프레임워크

Flask 대신 사용할 수 있는 옵션:
- **FastAPI**: 더 빠르고 현대적, 자동 문서화
- **Django**: 더 무겁지만 기능이 많음
- **Tornado**: 비동기 처리에 강함

하지만 현재 구조에서는 Flask가 가장 적합합니다:
- 간단함
- 충분한 성능
- 이미 구현되어 있음

## 테스트 방법

### 1. Health Check (브라우저)
```
http://127.0.0.1:9001/health
```

### 2. Health Check (PowerShell)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9001/health" -Method GET
```

### 3. Depth Inference (curl)
```bash
curl -X POST -F "image=@test_image.jpg" http://127.0.0.1:9001/depth
```

### 4. Depth Inference (Python)
```python
import requests

with open('test_image.jpg', 'rb') as f:
    response = requests.post(
        'http://127.0.0.1:9001/depth',
        files={'image': f}
    )
    print(response.json())
```

## 요약

- **Flask 사용 이유**: HTTP 서버로 AI Core와 통신하기 위해
- **Method Not Allowed**: `/depth`는 POST만 허용, 브라우저는 GET 요청
- **해결 방법**: `/health`로 상태 확인, `/depth`는 POST 요청으로 테스트




# 포트홀 합성 데이터 생성 가이드

생성형 AI를 사용하여 포트홀이 없는 도로 이미지에 가짜 포트홀을 자연스럽게 합성하여 학습 데이터를 생성하는 기능입니다.

## 기능 소개

- **포트홀 텍스처 생성**: 프로그래밍 방식으로 현실적인 포트홀 텍스처 생성
- **자연스러운 합성**: 다양한 블렌딩 모드로 도로 이미지에 자연스럽게 합성
- **YOLO 형식 라벨링**: 자동으로 YOLO 형식의 라벨 파일 생성
- **배치 처리**: 여러 이미지를 한 번에 처리

## 사용 방법

### 1. 기본 사용 (독립 실행)

**Linux/Mac 또는 Docker 컨테이너 내부:**
```bash
# 도로 이미지에 포트홀 합성하여 새 데이터셋 생성
python generate_synthetic_potholes.py \
  --road_images /app/shared_images/detections \
  --output_dir /app/models/synthetic_dataset \
  --num_potholes 1
```

**Windows PowerShell (호스트에서 Docker 실행):**
```powershell
# Docker 컨테이너 내부에서 실행
docker exec deep-guardian-ai python /app/generate_synthetic_potholes.py `
  --road_images /app/shared_images/detections `
  --output_dir /app/models/synthetic_dataset `
  --num_potholes 1
```

**Windows PowerShell (한 줄로):**
```powershell
docker exec deep-guardian-ai python /app/generate_synthetic_potholes.py --road_images /app/shared_images/detections --output_dir /app/models/synthetic_dataset --num_potholes 1
```

### 2. 파인튜닝 데이터셋에 추가

**Linux/Mac 또는 Docker 컨테이너 내부:**
```bash
# 기존 파인튜닝 데이터셋에 합성 데이터 추가
python add_synthetic_potholes.py \
  --road_images /app/shared_images/detections \
  --dataset_dir /app/models/finetune_dataset \
  --num_potholes 1
```

**Windows PowerShell:**
```powershell
docker exec deep-guardian-ai python /app/add_synthetic_potholes.py `
  --road_images /app/shared_images/detections `
  --dataset_dir /app/models/finetune_dataset `
  --num_potholes 1
```

### 3. 환경 변수로 자동 통합

파인튜닝 시 자동으로 합성 데이터를 생성하려면:

```bash
# Docker 컨테이너 환경 변수 설정
export USE_SYNTHETIC_POTHOLES=true
```

또는 `docker-compose.yml`에 추가:

```yaml
ai-core:
  environment:
    - USE_SYNTHETIC_POTHOLES=true
```

## 파라미터 설명

### generate_synthetic_potholes.py

- `--road_images`: 포트홀이 없는 도로 이미지 디렉토리
- `--output_dir`: 출력 디렉토리 (이미지와 라벨 저장)
- `--num_potholes`: 이미지당 포트홀 개수 (기본값: 1)
- `--min_scale`: 최소 포트홀 크기 스케일 (기본값: 0.5)
- `--max_scale`: 최대 포트홀 크기 스케일 (기본값: 1.5)
- `--class_id`: YOLO 클래스 ID (기본값: 0, 포트홀)

### 합성 옵션

- **스케일**: 포트홀 크기 조절 (0.3 ~ 2.0 권장)
- **회전**: 랜덤 회전 각도 (-30° ~ 30°)
- **블렌딩 모드**: 
  - `normal`: 일반 블렌딩
  - `multiply`: 곱셈 블렌딩 (더 어두운 효과)
  - `overlay`: 오버레이 블렌딩 (자연스러운 그림자)

## 생성 과정

1. **포트홀 텍스처 생성**
   - 타원형 포트홀 모양
   - 내부 디테일 (균열, 그림자)
   - 도로 유형에 맞는 색상

2. **이미지 합성**
   - 랜덤 위치 배치
   - 크기 조절 및 회전
   - 블렌딩으로 자연스러운 효과

3. **라벨 생성**
   - YOLO 형식: `class_id center_x center_y width height`
   - 정규화된 좌표 (0-1 범위)

## 출력 구조

```
output_dir/
├── images/
│   └── train/
│       ├── image1.jpg
│       ├── image2.jpg
│       └── ...
└── labels/
    └── train/
        ├── image1.txt
        ├── image2.txt
        └── ...
```

각 `.txt` 파일 형식:
```
0 0.523456 0.345678 0.123456 0.098765
```

## 예제

### 예제 1: 기본 합성

**Docker 컨테이너 내부:**
```bash
python generate_synthetic_potholes.py --road_images /app/shared_images/detections --output_dir /app/models/synthetic_dataset
```

**PowerShell에서 Docker 실행:**
```powershell
docker exec deep-guardian-ai python /app/generate_synthetic_potholes.py --road_images /app/shared_images/detections --output_dir /app/models/synthetic_dataset
```

### 예제 2: 다양한 크기의 포트홀

**Docker 컨테이너 내부:**
```bash
python generate_synthetic_potholes.py --road_images /app/shared_images/detections --output_dir /app/models/synthetic_dataset --num_potholes 2 --min_scale 0.3 --max_scale 2.0
```

**PowerShell에서 Docker 실행:**
```powershell
docker exec deep-guardian-ai python /app/generate_synthetic_potholes.py --road_images /app/shared_images/detections --output_dir /app/models/synthetic_dataset --num_potholes 2 --min_scale 0.3 --max_scale 2.0
```

### 예제 3: 파인튜닝 데이터셋에 통합

**Docker 컨테이너 내부:**
```bash
python add_synthetic_potholes.py --road_images /app/shared_images/detections --dataset_dir /app/models/finetune_dataset --num_potholes 1
```

**PowerShell에서 Docker 실행:**
```powershell
docker exec deep-guardian-ai python /app/add_synthetic_potholes.py --road_images /app/shared_images/detections --dataset_dir /app/models/finetune_dataset --num_potholes 1
```

## 주의사항

1. **품질 관리**
   - 합성된 포트홀이 너무 비현실적이면 학습에 악영향을 줄 수 있음
   - 실제 포트홀 데이터와 균형있게 사용 권장

2. **데이터 비율**
   - 실제 데이터 : 합성 데이터 = 3:1 또는 2:1 권장
   - 합성 데이터가 너무 많으면 과적합 위험

3. **다양성**
   - 다양한 크기, 위치, 각도로 합성
   - 다양한 도로 유형에 적용

4. **검증**
   - 합성된 데이터를 시각적으로 확인
   - 학습 전에 품질 검증 권장

## 고급 사용

### 커스텀 포트홀 생성

`SyntheticPotholeGenerator` 클래스를 직접 사용:

```python
from synthetic_pothole_generator import SyntheticPotholeGenerator

generator = SyntheticPotholeGenerator()

# 포트홀 텍스처 생성
pothole_img = generator._generate_pothole_texture((200, 200), "asphalt")

# 도로 이미지에 합성
road_img = cv2.imread("road.jpg")
result, bbox = generator.composite_pothole_on_road(
    road_img, pothole_img,
    scale=1.0,
    rotation=0,
    blend_mode="multiply"
)

# YOLO 라벨 생성
yolo_bbox = generator.convert_bbox_to_yolo(bbox, road_img.shape[1], road_img.shape[0])
```

## 문제 해결

### 합성이 부자연스러운 경우

- 블렌딩 모드를 변경해보세요 (`multiply` 권장)
- 스케일 범위를 조정하세요
- 포트홀 텍스처 파라미터를 조정하세요

### 라벨 좌표 오류

- 이미지 크기와 라벨 좌표가 일치하는지 확인
- YOLO 형식 (정규화된 좌표)인지 확인

### 성능 문제

- 배치 크기를 줄여보세요
- 이미지 크기를 줄여보세요
- 멀티프로세싱 고려

## 향후 개선 계획

1. **실제 생성형 AI 통합**
   - DALL-E, Stable Diffusion 등 실제 생성형 AI 사용
   - 더 현실적인 포트홀 텍스처 생성

2. **데이터 증강 자동화**
   - 파인튜닝 시 자동으로 합성 데이터 생성
   - 실제 데이터와 합성 데이터 자동 균형 조절

3. **품질 검증**
   - 합성 품질 자동 평가
   - 부적절한 합성 자동 필터링


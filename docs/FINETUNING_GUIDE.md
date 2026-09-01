# YOLO 모델 자동 파인튜닝 가이드

## 개요

Deep-Guardian 시스템은 매일 00시에 자동으로 새로 감지된 포트홀 이미지 개수를 확인하고, 100장 이상이면 YOLO 모델을 자동으로 파인튜닝합니다.

## 동작 방식

### 1. 스케줄러
- **실행 시간**: 매일 00:00 (자정)
- **트리거**: APScheduler를 사용한 Cron 작업
- **조건**: 어제 00시부터 오늘 00시까지 새로 감지된 포트홀 이미지가 100장 이상

### 2. 파인튜닝 프로세스

1. **새 이미지 개수 확인**
   - 데이터베이스에서 검증된 포트홀 이미지 개수 확인
   - `detected_at` 필드를 기준으로 최근 1일간의 데이터 조회

2. **데이터셋 준비**
   - 검증된 포트홀 이미지와 바운딩 박스 정보 추출
   - YOLO 형식으로 데이터셋 변환
   - 최대 1000장까지 사용

3. **모델 백업**
   - 현재 사용 중인 모델을 백업 디렉토리에 저장
   - 백업 파일명: `backup_YYYYMMDD_HHMMSS.pt`

4. **파인튜닝 실행**
   - 현재 모델을 기반으로 파인튜닝
   - Epochs: 50
   - Batch size: 16
   - Image size: 640
   - Device: GPU (xpu) 또는 CPU

5. **모델 교체**
   - 파인튜닝된 모델을 `/app/models/best2.pt`로 저장
   - 새 모델을 자동으로 로드하여 추론에 사용

## 설정

### 파인튜닝 임계값 변경

`ai-core/main.py` 파일에서 임계값을 변경할 수 있습니다:

```python
# 파인튜닝 설정
self.finetune_threshold = 100  # 100장 이상이면 파인튜닝
```

### 파인튜닝 파라미터 조정

`finetune_model()` 함수에서 파인튜닝 파라미터를 조정할 수 있습니다:

```python
results = base_model.train(
    data=os.path.join(dataset_dir, "data.yaml"),
    epochs=50,          # 학습 에포크 수
    imgsz=640,         # 이미지 크기
    batch=16,          # 배치 크기
    device=self.device,
    project="/app/models",
    name="finetune",
    exist_ok=True,
    patience=10,       # Early stopping patience
    save=True,
    plots=True
)
```

## 수동 파인튜닝 실행

필요한 경우 수동으로 파인튜닝을 실행할 수 있습니다:

```python
from main import AICore

ai_core = AICore()
ai_core.check_and_finetune()
```

또는 직접 파인튜닝 실행:

```python
ai_core.finetune_model()
```

## 모델 백업

파인튜닝 전에 현재 모델이 자동으로 백업됩니다:
- 백업 위치: `/app/models/backup/`
- 백업 파일명 형식: `backup_YYYYMMDD_HHMMSS.pt`

## 데이터셋 구조

파인튜닝용 데이터셋은 다음 구조로 생성됩니다:

```
/app/models/finetune_dataset/
├── images/
│   └── train/
│       ├── pothole_000000.jpg
│       ├── pothole_000001.jpg
│       └── ...
├── labels/
│   └── train/
│       ├── pothole_000000.txt
│       ├── pothole_000001.txt
│       └── ...
└── data.yaml
```

## 로그 확인

파인튜닝 진행 상황은 AI Core 로그에서 확인할 수 있습니다:

```bash
docker-compose logs -f ai-core
```

## 주의사항

1. **디스크 공간**: 파인튜닝은 상당한 디스크 공간을 사용할 수 있습니다
   - 데이터셋: 약 100-1000장의 이미지
   - 모델 파일: 각 모델 약 10-50MB
   - 백업 파일: 이전 모델들 저장

2. **처리 시간**: 파인튜닝은 시간이 오래 걸릴 수 있습니다
   - 100장 기준: 약 10-30분 (GPU 사용 시)
   - 1000장 기준: 약 1-2시간 (GPU 사용 시)

3. **리소스 사용**: 파인튜닝 중에는 시스템 리소스를 많이 사용합니다
   - GPU 메모리 사용량 증가
   - CPU 사용량 증가

4. **데이터 품질**: 파인튜닝 품질은 데이터셋의 품질에 의존합니다
   - 검증된 포트홀 이미지만 사용
   - 바운딩 박스 정보가 정확해야 함

## 문제 해결

### 파인튜닝이 실행되지 않는 경우

1. **로그 확인**
   ```bash
   docker-compose logs ai-core | grep -i "fine"
   ```

2. **이미지 개수 확인**
   ```sql
   SELECT COUNT(DISTINCT image_path) 
   FROM potholes 
   WHERE detected_at >= CURRENT_DATE - INTERVAL '1 day'
     AND validation_result = true
     AND image_path IS NOT NULL;
   ```

3. **스케줄러 상태 확인**
   - AI Core 시작 시 스케줄러 초기화 메시지 확인
   - `[OK] Scheduler started - Fine-tuning will run daily at 00:00`

### 파인튜닝 실패 시

1. **데이터셋 확인**
   - 최소 10장 이상의 이미지 필요
   - 바운딩 박스 정보가 모두 있어야 함

2. **디스크 공간 확인**
   ```bash
   docker-compose exec ai-core df -h
   ```

3. **모델 파일 확인**
   ```bash
   docker-compose exec ai-core ls -lh /app/models/
   ```

## 성능 모니터링

파인튜닝 후 모델 성능을 모니터링하는 것을 권장합니다:

1. **탐지 정확도 확인**
   - 대시보드에서 탐지 결과 확인
   - False positive/negative 비율 확인

2. **모델 비교**
   - 백업된 이전 모델과 비교
   - 필요시 이전 모델로 롤백 가능

## 롤백 방법

파인튜닝된 모델에 문제가 있는 경우 이전 모델로 롤백:

```python
# 백업 디렉토리에서 이전 모델 선택
backup_model = "/app/models/backup/backup_20241215_000000.pt"

# 모델 교체
ai_core.load_yolo_model(backup_model)
```

또는 수동으로:

```bash
docker-compose exec ai-core cp /app/models/backup/backup_YYYYMMDD_HHMMSS.pt /app/models/best2.pt
docker-compose restart ai-core
```






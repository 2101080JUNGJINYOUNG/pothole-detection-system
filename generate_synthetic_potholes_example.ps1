# 포트홀 합성 데이터셋 생성 예제 스크립트

Write-Host "포트홀 합성 데이터셋 생성" -ForegroundColor Cyan
Write-Host ""

# 도로 이미지 디렉토리 (포트홀이 없는 이미지)
$roadImagesDir = "shared_images\detections"

# 출력 디렉토리
$outputDir = "ai-core\models\synthetic_dataset"

Write-Host "도로 이미지 디렉토리: $roadImagesDir"
Write-Host "출력 디렉토리: $outputDir"
Write-Host ""

# Docker 컨테이너 내부에서 실행
Write-Host "Docker 컨테이너에서 합성 데이터셋 생성 중..." -ForegroundColor Yellow

docker exec deep-guardian-ai python /app/generate_synthetic_potholes.py `
  --road_images /app/shared_images/detections `
  --output_dir /app/models/synthetic_dataset `
  --num_potholes 1 `
  --min_scale 0.5 `
  --max_scale 1.5

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "합성 데이터셋 생성 완료!" -ForegroundColor Green
    Write-Host "출력 위치: ai-core\models\synthetic_dataset"
} else {
    Write-Host ""
    Write-Host "오류 발생!" -ForegroundColor Red
}



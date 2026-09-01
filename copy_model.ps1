# Copy YOLOv8 model to project directory

$sourcePath = "C:\Users\shkim1\Documents\KakaoTalk Downloads\best2.pt"
$destPath = ".\ai-core\models\best2.pt"

Write-Host "Copying YOLOv8 model..." -ForegroundColor Cyan

# Create models directory if it doesn't exist
$modelsDir = ".\ai-core\models"
if (-not (Test-Path $modelsDir)) {
    New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null
    Write-Host "Created directory: $modelsDir" -ForegroundColor Yellow
}

# Check if source file exists
if (-not (Test-Path $sourcePath)) {
    Write-Host "[ERROR] Model file not found: $sourcePath" -ForegroundColor Red
    exit 1
}

# Copy model file
try {
    Copy-Item $sourcePath -Destination $destPath -Force
    Write-Host "[OK] Model copied successfully" -ForegroundColor Green
    Write-Host "  From: $sourcePath" -ForegroundColor Gray
    Write-Host "  To:   $destPath" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to copy model: $_" -ForegroundColor Red
    exit 1
}





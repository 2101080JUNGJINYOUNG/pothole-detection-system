# NPU Worker 시작 가이드

## 🎯 개요

Phi-3-mini-int4 챗봇을 사용하려면 **NPU Worker**를 Windows Host에서 실행해야 합니다.

NPU Worker는 Docker 컨테이너 외부에서 실행되며, 컨테이너 내부의 챗봇이 `http://host.docker.internal:9002`로 접근합니다.

## 🚀 시작 방법

### 방법 1: 시작 스크립트 사용 (권장)

1. **새 PowerShell 창 열기**
   - 현재 PowerShell 창과 별도로 새 창을 엽니다
   - 이 창은 NPU Worker가 실행되는 동안 열어두어야 합니다

2. **프로젝트 디렉토리로 이동**
   ```powershell
   cd C:\Users\shkim1\Desktop\test
   ```

3. **시작 스크립트 실행**
   ```powershell
   .\start_phi3_worker.ps1
   ```

4. **디바이스 선택**
   - NPU (Intel Arc GPU NPU) - 권장
   - CPU
   - AUTO (자동 선택)

### 방법 2: 직접 실행

```powershell
# 기본 실행 (NPU 사용)
python slm_npu_worker_phi3.py --port 9002

# CPU 사용
python slm_npu_worker_phi3.py --device CPU --port 9002

# 로컬 모델 사용
python slm_npu_worker_phi3.py --model models\llm\Phi-3-mini-int4 --port 9002
```

## ✅ 정상 작동 확인

NPU Worker가 정상적으로 시작되면 다음과 같은 메시지가 표시됩니다:

```
✅ Phi-3-mini 모델 로드 완료: microsoft/phi-3-mini-4k-instruct
✅ 디바이스: NPU
🚀 Phi-3-mini SLM NPU Worker 시작: http://0.0.0.0:9002
```

## 🔍 연결 확인

### 1. 포트 확인
```powershell
netstat -ano | findstr :9002
```

포트 9002가 LISTENING 상태여야 합니다.

### 2. Health Check
브라우저에서 다음 URL 접속:
```
http://localhost:9002/health
```

정상 응답 예시:
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "NPU"
}
```

### 3. 대시보드에서 확인
- 대시보드 접속: http://localhost
- 사이드바 챗봇 열기
- "🚀 **NPU 가속 활성화**: OpenVINO + Intel NPU + Phi-3-mini" 메시지 확인

## ⚠️ 문제 해결

### NPU Worker가 시작되지 않을 때

1. **Python 확인**
   ```powershell
   python --version
   ```

2. **필요한 패키지 설치**
   ```powershell
   pip install openvino-genai flask flask-cors
   ```

3. **모델 경로 확인**
   - 로컬 모델: `models\llm\Phi-3-mini-int4`
   - Hugging Face 모델: 자동 다운로드

### 포트 9002가 이미 사용 중일 때

다른 포트 사용:
```powershell
python slm_npu_worker_phi3.py --port 9003
```

그리고 환경 변수 설정:
```powershell
$env:SLM_NPU_WORKER_URL="http://host.docker.internal:9003"
```

### NPU를 찾을 수 없을 때

CPU로 실행:
```powershell
python slm_npu_worker_phi3.py --device CPU --port 9002
```

## 📝 주의사항

1. **NPU Worker 창을 닫지 마세요**
   - NPU Worker는 별도 PowerShell 창에서 실행됩니다
   - 창을 닫으면 챗봇이 작동하지 않습니다

2. **Docker 컨테이너와 별도 실행**
   - NPU Worker는 Windows Host에서 직접 실행됩니다
   - Docker 컨테이너 내부가 아닙니다

3. **포트 9002 사용**
   - 기본 포트는 9002입니다
   - 다른 포트를 사용하려면 환경 변수 설정 필요

## 🔄 자동 시작 설정 (선택사항)

Windows 시작 시 자동으로 NPU Worker를 실행하려면:

1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 트리거: 컴퓨터 시작 시
4. 동작: 프로그램 시작
   - 프로그램: `powershell.exe`
   - 인수: `-File "C:\Users\shkim1\Desktop\test\start_phi3_worker.ps1"`

## 📚 관련 파일

- `slm_npu_worker_phi3.py` - NPU Worker 메인 파일
- `start_phi3_worker.ps1` - 시작 스크립트
- `dashboard/slm_npu_chatbot.py` - 챗봇 클라이언트


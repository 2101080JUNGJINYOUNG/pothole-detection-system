# Ollama 설치 가이드 (Windows)

Ollama는 SLM (Small Language Model)을 로컬에서 실행할 수 있게 해주는 도구입니다.

## ✅ 현재 구현 상태

- **플랫폼**: Ollama (SLM 실행 플랫폼)
- **모델**: llama3.2, phi3, llama3.1:8b 등 (모두 SLM)
- **통신**: HTTP API (http://localhost:11434)

## 설치 방법

### Windows

1. **Ollama 다운로드**
   - 공식 사이트: https://ollama.ai/download
   - Windows 설치 파일 다운로드 후 실행

2. **설치 확인**
   ```powershell
   ollama --version
   ```

3. **모델 다운로드**
   ```powershell
   # 기본 모델 (llama3.2, 약 2GB)
   ollama pull llama3.2
   
   # 또는 더 작은 모델 (phi3, 약 2.3GB)
   ollama pull phi3
   
   # 또는 더 정확한 모델 (llama3.1:8b, 약 4.7GB)
   ollama pull llama3.1:8b
   ```

4. **서버 시작**
   - Ollama 설치 후 자동으로 서비스로 시작됩니다
   - 수동으로 시작하려면:
     ```powershell
     ollama serve
     ```

5. **연결 확인**
   ```powershell
   # 브라우저에서 확인
   # http://localhost:11434
   
   # 또는 PowerShell에서
   Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
   ```

## Docker 컨테이너에서 접근

Docker 컨테이너에서 호스트의 Ollama에 접근하려면:
- `OLLAMA_URL=http://host.docker.internal:11434` (기본값, 이미 설정됨)

## 모델 비교

| 모델 | 크기 | 속도 | 정확도 | 권장 용도 |
|------|------|------|--------|----------|
| llama3.2 | 2GB | 빠름 | 높음 | **권장 (기본값)** |
| phi3 | 2.3GB | 빠름 | 중간 | 빠른 응답이 필요한 경우 |
| llama3.1:8b | 4.7GB | 중간 | 매우 높음 | 더 정확한 답변이 필요한 경우 |

## 빠른 시작

```powershell
# 1. Ollama 설치 (https://ollama.ai/download)

# 2. 모델 다운로드
ollama pull llama3.2

# 3. 서비스 확인 (자동 시작됨)
ollama list

# 4. 테스트
ollama run llama3.2 "안녕하세요"
```

## 문제 해결

### Ollama가 시작되지 않는 경우

```powershell
# 서비스 재시작
# Windows 서비스 관리자에서 "Ollama" 서비스 재시작
# 또는
ollama serve
```

### 포트가 이미 사용 중인 경우

기본 포트(11434)가 사용 중이면 다른 포트 사용:
```powershell
$env:OLLAMA_HOST="0.0.0.0:11435"
ollama serve
```

그리고 `docker-compose.yml`에서:
```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11435
```

## 대안: 다른 SLM 서비스

현재는 Ollama만 지원하지만, 필요하면 다음을 추가할 수 있습니다:

1. **LM Studio** (Windows GUI)
2. **GPT4All** (로컬 실행)
3. **LocalAI** (서버 형태)

원하시면 다른 옵션도 구현해드릴 수 있습니다!



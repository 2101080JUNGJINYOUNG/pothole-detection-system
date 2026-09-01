# 문서 목록

## 시작하기

- [QUICK_START.md](QUICK_START.md) — 빠른 시작
- [USAGE.md](USAGE.md) / [USAGE_COMMANDS.md](USAGE_COMMANDS.md) — 사용법, 명령어 모음
- [README_DOCKER.md](README_DOCKER.md) — Docker 구성 가이드
- [간단한실행방법.md](간단한실행방법.md) / [실행방법_포트홀합성.md](실행방법_포트홀합성.md) — 합성 포트홀 데이터 생성 실행법
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) — NPU Worker 단독 실행 구조 (Docker 이전 문서, NPU Worker 부분만 최신)

## 기능 가이드

- [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) — 인증/관리자 시스템
- [RISK_PRIORITY_SYSTEM.md](RISK_PRIORITY_SYSTEM.md) — 위치 기반 위험도 우선순위
- [FINETUNING_GUIDE.md](FINETUNING_GUIDE.md) — 자동 파인튜닝
- [OVERFITTING_PREVENTION.md](OVERFITTING_PREVENTION.md) — 과적합 방지 전략
- [ROAD_CHATBOT_GUIDE.md](ROAD_CHATBOT_GUIDE.md) — 도로 포트홀 챗봇
- [SYNTHETIC_POTHOLES_GUIDE.md](SYNTHETIC_POTHOLES_GUIDE.md) — 합성 포트홀 데이터 생성
- [FLASK_USAGE_EXPLANATION.md](FLASK_USAGE_EXPLANATION.md) — NPU Worker가 Flask를 쓰는 이유

## 설정 가이드

- [KAKAO_API_SETUP.md](KAKAO_API_SETUP.md) — Kakao Map API
- [GEMINI_SETUP_GUIDE.md](GEMINI_SETUP_GUIDE.md) — Google Gemini API
- [OLLAMA_INSTALL_GUIDE.md](OLLAMA_INSTALL_GUIDE.md) / [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) — Ollama
- [OPENVINO_SLM_GUIDE.md](OPENVINO_SLM_GUIDE.md) / [PHI3_OPENVINO_SETUP.md](PHI3_OPENVINO_SETUP.md) — OpenVINO + Phi-3-mini
- [models_llm_Phi-3-mini-int4_README.md](models_llm_Phi-3-mini-int4_README.md) — Phi-3-mini-int4 모델 카드(Hugging Face)

## GPU / 하드웨어

- [GPU_SETUP_GUIDE.md](GPU_SETUP_GUIDE.md) / [GPU_SUPPORT_GUIDE.md](GPU_SUPPORT_GUIDE.md)
- [INTEL_ARC_GPU_SETUP.md](INTEL_ARC_GPU_SETUP.md)

## 인프라 / 트러블슈팅

- [ARCHITECTURE_UPDATES.md](ARCHITECTURE_UPDATES.md) — 원본 블록도 대비 아키텍처 변경 내역
- [CLOUDFLARE_QUICK_START.md](CLOUDFLARE_QUICK_START.md) / [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
- [cloudflared_CLOUDFLARE_설정_가이드.md](cloudflared_CLOUDFLARE_설정_가이드.md) / [cloudflared_README.md](cloudflared_README.md) / [cloudflared_로그인_문제_해결.md](cloudflared_로그인_문제_해결.md) / [cloudflared_빠른_설정_가이드.md](cloudflared_빠른_설정_가이드.md)
- [APACHE_ISSUE_SUMMARY.md](APACHE_ISSUE_SUMMARY.md) — Apache 재시작 루프 문제 요약

## 히스토리 / 참고자료

- [PROJECT_HISTORY.md](PROJECT_HISTORY.md) — 아키텍처 변천사 (5-컨테이너 → 2-컨테이너 LAMP 시도 → 5-컨테이너 복원)
- [references/](references/) — 관련 연구 논문
- [../archive/](../archive/) — 폐기된 2/3-컨테이너 아키텍처 코드와 전용 기술 문서
- [../edge-ai/](../edge-ai/) — 엣지 배포(ONNX/TFLite 변환), GPS 경로, 실시간 스트리밍 실험

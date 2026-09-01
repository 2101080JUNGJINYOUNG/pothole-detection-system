# 문서 목록

## 시작하기

- [README_2CONTAINER.md](README_2CONTAINER.md) / [2컨테이너_구조_가이드.md](2컨테이너_구조_가이드.md) — 현재 아키텍처(LAMP + inference) 개요
- [QUICK_START_2CONTAINER.md](QUICK_START_2CONTAINER.md) — 빠른 시작
- [실행_명령어.md](실행_명령어.md) — 자주 쓰는 Docker/MySQL 명령어 모음
- [USAGE.md](USAGE.md) / [USAGE_COMMANDS.md](USAGE_COMMANDS.md) — NPU Worker 사용법
- [프로젝트_블록도.md](프로젝트_블록도.md) / [프로젝트_블록도_간단버전.md](프로젝트_블록도_간단버전.md) — 아키텍처 다이어그램(Mermaid/ASCII)
- [간단한실행방법.md](간단한실행방법.md) / [실행방법_포트홀합성.md](실행방법_포트홀합성.md) — 합성 포트홀 데이터 생성 실행법
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) — NPU Worker 단독 실행 구조 (Docker 이전 문서, NPU Worker 부분만 최신)

## 기능 가이드

- [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) — 인증/관리자 시스템
- [PHI3_LAMP_통합_완료.md](PHI3_LAMP_통합_완료.md) — Phi-3 챗봇을 LAMP 컨테이너에 통합한 내역
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

- [CLOUDFLARE_QUICK_START.md](CLOUDFLARE_QUICK_START.md) / [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
- [cloudflared_CLOUDFLARE_설정_가이드.md](cloudflared_CLOUDFLARE_설정_가이드.md) / [cloudflared_README.md](cloudflared_README.md) / [cloudflared_로그인_문제_해결.md](cloudflared_로그인_문제_해결.md) / [cloudflared_빠른_설정_가이드.md](cloudflared_빠른_설정_가이드.md)

## 히스토리 / 참고자료

- [PROJECT_HISTORY.md](PROJECT_HISTORY.md) — 아키텍처 변천사 (5-컨테이너 → 2-컨테이너 LAMP 시도 → 팀 발표자료 기준 LAMP로 최종 확정)
- [references/](references/) — 팀 발표자료(공식 아키텍처 블록도), 관련 연구 논문
- [../archive/](../archive/) — 이전에 메인이었던 PostgreSQL 5-컨테이너 구조, 3-컨테이너 통합 실험 등 지금은 쓰지 않는 코드/문서
- [../edge-ai/](../edge-ai/) — 엣지 배포(ONNX/TFLite 변환), GPS 경로, 실시간 스트리밍 실험

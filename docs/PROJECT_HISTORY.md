# 프로젝트 히스토리

Deep-Guardian은 아키텍처를 여러 번 바꿔가며 발전했습니다. 이 문서는 그 변천사를
시간순으로 요약합니다(예전에 루트에 흩어져 있던 14개의 개별 "진행 상황" 문서를
하나로 압축한 것입니다).

## 1. 최초 구조 — 5-컨테이너 (Apache + Streamlit + AI Core + PostgreSQL + Cloudflare Tunnel)

Apache가 외부 진입점 역할을 하고, Streamlit 대시보드가 시각화를 담당하며,
AI Core 컨테이너가 YOLOv8 탐지 → NPU Worker(Windows 호스트) 호출로 깊이 검증 →
PostgreSQL 저장까지 처리하는 구조로 시작했습니다.

## 2. 기능 확장

기본 파이프라인 위에 다음 기능들을 순차적으로 추가했습니다:
- 위치 기반 위험도/우선순위 시스템(Kakao Map API로 학교·병원·고속도로 판별)
- 사용자 인증 및 관리자 검토(포트홀 이미지 승인/거부) 시스템
- 합성 포트홀 이미지 생성으로 학습 데이터 증강
- 매일 자정 자동 파인튜닝 스케줄러
- Phi-3-mini(OpenVINO NPU) 챗봇, Google Gemini 요약 기능

## 3. 2-컨테이너(LAMP) 전환 시도와 기능 격차

컨테이너 수를 5개→2개로 줄이기 위해 `lamp-container`(Apache+MySQL+Flask 통합)와
`inference-container`(YOLO 추론 분리)로 재구성을 시도했습니다. 그런데 이 과정에서
Streamlit에 있던 기능의 상당수(인증, 관리자 검토, 통계 대시보드, Gemini 요약,
비디오 결과 페이지, 라이브 스트리밍, 고급 챗봇, 데이터 내보내기)가 새 Flask
앱에는 빠진 채로 초기 버전이 나왔습니다(기능 완성도 약 40% 수준으로 평가됨).

이후 `lamp-container/app/`에 인증(`auth.py`)·통계(`statistics.py`)·고급 챗봇
(`advanced_chatbot.py`)·관리자 검토 API·데이터 내보내기 등을 추가로 구현해
기능 격차를 대부분 복구했습니다.

## 4. 원래 5-컨테이너 구조로 최종 복원

기능을 복구했음에도 불구하고, 최종적으로는 **원래의 5-컨테이너 구조(PostgreSQL
+ Streamlit)로 되돌아갔습니다.** 지금 저장소 루트의 `docker-compose.yml`이 바로
이 구조이며, 실제로 사용 중인 유일한 구성입니다.

## 5. 다른 컨테이너 통합 실험

별도로, `app/`(Streamlit+AI Core를 한 컨테이너로 합친 것) + PostgreSQL +
Cloudflare Tunnel로 컨테이너 수를 줄이는 실험(`docker-compose-optimized.yml`)도
있었습니다. 이 쪽은 지금도 실행은 가능하지만 마찬가지로 실사용 구성은 아닙니다.

## 6. 정리

`lamp-container/`, `inference-container/`, `app/`, `docker-compose-optimized.yml`과
관련 기술 문서는 [`archive/`](../archive/)로 옮겨 보관하고 있습니다. 이 저장소를
그대로 실행하려면 루트의 `docker-compose.yml`(5-컨테이너 구조)을 사용하면 됩니다.

## 알려진 이슈

- `slm_npu_worker_phi3.py`에 `threading` import가 빠져 있어 즉시 종료되던 버그를
  이번 정리 과정에서 수정했습니다.
- 기본 관리자 계정(`admin`/`admin123`)은 개발 편의를 위한 것으로, 운영 환경에서는
  반드시 변경해야 합니다.

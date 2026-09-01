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

## 4. 잠시 5-컨테이너 구조로 되돌아갔던 시기

기능을 복구한 뒤, 한때 다시 원래의 5-컨테이너 구조(PostgreSQL + Streamlit)로
되돌아간 적이 있습니다. 다만 이는 최종 결정이 아니었습니다 — 아래 5번 참고.

## 5. 팀 발표자료 기준 최종 아키텍처 = LAMP(2-컨테이너, MySQL)

팀의 최종 발표자료([`docs/references/`](references/)의 "6조" 발표 pptx, 슬라이드 4
블록도)를 확인한 결과, **공식적으로 제시한 아키텍처는 2-컨테이너 LAMP 구조**
(`inference` 컨테이너: YOLOv8+NPU 호출 / `lamp` 컨테이너: Apache+MySQL+Flask
통합, Cloudflare Tunnel로 외부 접속)였습니다. 한때 이 문서에는 "5-컨테이너
구조로 최종 복원됐다"고 적혀 있었는데, 발표자료를 직접 확인하고 나서
**LAMP/MySQL 구조가 저장소의 메인**이 되도록 바로잡았습니다.

- 발표자료의 블록도는 NPU/SLM 워커가 `inference` 컨테이너 "안"에 있는 것처럼
  단순화해서 그려져 있지만, 실제 코드상으로는 지금도 Windows 호스트에서 별도
  실행되고 `host.docker.internal`로 호출되는 구조입니다(발표 편의상 단순화된
  것으로 보입니다).
- `lamp-container`의 MySQL 초기화 스크립트(`database/init_mysql.sql`)에는
  원래 위험도/관리자검토 관련 컬럼(`location_type`, `risk_level`,
  `priority_score`, `approved_for_training` 등)이 빠져 있었는데, Django ORM
  모델(`django_app/models.py`)과 맞지 않아 이번에 함께 채워 넣었습니다.
- Apache 설정(`apache-config.conf`)이 실제로는 만들어지지 않는
  `/var/www/app/venv`를 `python-home`으로 지정하고 있던 버그도 함께 고쳤습니다.

## 6. 다른 컨테이너 통합 실험

별도로, `app/`(Streamlit+AI Core를 한 컨테이너로 합친 것) + PostgreSQL +
Cloudflare Tunnel로 컨테이너 수를 줄이는 실험(`docker-compose-optimized.yml`)도
있었습니다. 이쪽은 지금도 실행은 가능하지만 실사용 구성은 아닙니다.

## 7. 정리

한때 메인이었던 5-컨테이너(PostgreSQL) 구조는
[`archive/postgresql-5container/`](../archive/postgresql-5container/)로,
`app/` + `docker-compose-optimized.yml` 실험은 [`archive/`](../archive/)로
옮겨 보관하고 있습니다. 이 저장소를 그대로 실행하려면 루트의
`docker-compose.yml`(LAMP 2-컨테이너 구조)을 사용하면 됩니다.

## 알려진 이슈

- `slm_npu_worker_phi3.py`에 `threading` import가 빠져 있어 즉시 종료되던 버그를
  수정했습니다.
- 기본 관리자 계정(`admin`/`admin123`)은 개발 편의를 위한 것으로, 운영 환경에서는
  반드시 변경해야 합니다.

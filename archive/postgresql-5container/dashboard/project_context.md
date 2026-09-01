# Deep-Guardian 프로젝트 컨텍스트

## 프로젝트 개요
Deep-Guardian은 AI 기반 포트홀 탐지 및 모니터링 시스템입니다.

## 시스템 구조
1. **AI Core**: YOLOv8로 포트홀 탐지 → NPU Worker로 깊이 검증 → DB 저장
2. **Dashboard**: Streamlit 기반 웹 대시보드 (데이터 시각화, 관리)
3. **Database**: PostgreSQL (포트홀 데이터 저장)
4. **NPU Worker**: OpenVINO 기반 깊이 검증 서비스

## 데이터베이스 스키마 (Pothole 모델)

### 주요 필드:
- `id`: 포트홀 고유 ID
- `latitude`, `longitude`: GPS 좌표 (위도, 경도)
- `depth_ratio`: 깊이 비율 (0.0~1.0) - 깊이 맵에서 0.3 이상인 픽셀 비율
- `validation_result`: 검증 결과 (True/False) - depth_ratio >= 0.1일 때 True
- `detected_at`: 탐지 시각
- `image_path`: 이미지 파일 경로
- `confidence_score`: YOLOv8 탐지 신뢰도 (0.0~1.0)
- `bbox_x1, bbox_y1, bbox_x2, bbox_y2`: 바운딩 박스 좌표

### 위험도 평가 필드:
- `location_type`: 위치 유형 ('school', 'hospital', 'highway', 'general' 등)
- `risk_level`: 위험도 등급 ('critical', 'high', 'medium', 'low')
- `priority_score`: 우선순위 점수 (높을수록 더 위험/우선)
- `location_description`: 위치 설명 (예: "군산대학교 정문 앞")

### 검토 필드:
- `approved_for_training`: 학습 데이터 승인 여부 (True/False/None)
- `reviewed_by_id`: 검토한 관리자 ID
- `reviewed_at`: 검토 시각
- `review_notes`: 검토 노트

## 비즈니스 로직

### 위험도 평가
- Kakao Map API를 사용하여 주변 시설물 검색
- 학교, 병원 등 민감 지역: Critical/High
- 고속도로: High
- 일반 도로: Medium/Low

### 우선순위 점수 (priority_score)
- 깊이 비율 (depth_ratio) 기반
- 위치 유형에 따른 가중치
- 최근 탐지일수록 가중치 증가

### 검증 로직
1. YOLOv8로 포트홀 탐지 (confidence_score)
2. 포트홀 영역만 크롭
3. NPU Worker로 깊이 검증 (depth_ratio 계산)
4. depth_ratio >= 0.1이면 validation_result = True
5. 검증 통과 데이터만 DB 저장

## 주요 기능
1. **실시간 포트홀 탐지**: 이미지/비디오 입력 처리
2. **깊이 검증**: NPU 기반 깊이 모델로 실제 포트홀인지 검증
3. **위험도 평가**: 위치 기반 위험도 자동 평가
4. **데이터 시각화**: 지도, 통계, 차트
5. **관리자 검토**: 포트홀 승인/거부, 학습 데이터 선정
6. **파인튜닝**: 승인된 데이터로 YOLOv8 모델 재학습

## 데이터 통계
- 총 탐지 건수: 모든 포트홀 (검증 통과/미통과 포함)
- 검증 통과: validation_result = True인 포트홀
- 평균 깊이 비율: 검증 통과 포트홀의 평균 depth_ratio
- 위험도 분포: risk_level별 개수



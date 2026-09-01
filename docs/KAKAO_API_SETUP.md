# Kakao Map API 설정 가이드

## 현재 상태
- ✅ REST API 키가 정상적으로 설정되었습니다.
- ✅ API 인증이 완료되었으며 정상 작동 중입니다.

## 해결 방법

### 1. REST API 키 확인 및 발급

1. **Kakao Developers 콘솔 접속**
   - https://developers.kakao.com/ 접속
   - 로그인 후 내 애플리케이션 선택

2. **앱 키 확인**
   - 앱 설정 > 앱 키에서 **REST API 키** 확인
   - JavaScript 키가 아닌 **REST API 키**를 사용해야 합니다

3. **REST API 키가 없는 경우**
   - 앱 설정 > 플랫폼 > Web 플랫폼 추가
   - 사이트 도메인 등록 (예: http://localhost)
   - REST API 키가 활성화됩니다

### 2. API 키 설정 완료

현재 설정된 REST API 키:
```
KAKAO_MAP_APP_KEY=your_kakao_rest_api_key
```

✅ REST API 키가 정상적으로 설정되어 있습니다.

### 3. API 사용량 확인

- Kakao Developers 콘솔 > 내 애플리케이션 > 통계에서 API 사용량 확인
- 일일 사용량 제한 확인 (일반적으로 300,000건/일)

## 사용 중인 API

1. **좌표 → 주소 변환 API**
   - 엔드포인트: `/v2/local/geo/coord2address.json`
   - 용도: GPS 좌표를 주소로 변환하여 도로 유형 판단

2. **카테고리 검색 API**
   - 엔드포인트: `/v2/local/search/category.json`
   - 용도: 주변 학교(SC4), 병원(HP8) 검색

## 참고 자료

- Kakao Developers 문서: https://developers.kakao.com/docs/latest/ko/local/dev-guide
- 좌표 → 주소 변환: https://developers.kakao.com/docs/latest/ko/local/dev-guide#coord-to-address
- 카테고리 검색: https://developers.kakao.com/docs/latest/ko/local/dev-guide#search-by-category

## 문제 해결

### 401 Unauthorized 오류
- **원인**: REST API 키가 아니거나, 키가 잘못됨
- **해결**: REST API 키 확인 및 업데이트

### 403 Forbidden 오류
- **원인**: API 사용량 초과 또는 플랫폼 미등록
- **해결**: 사용량 확인 및 플랫폼 등록 확인

### API 호출 실패 시
- 시스템은 기본값(일반 도로)을 사용하여 계속 작동합니다
- API 호출 실패는 경고 메시지로만 표시되며, 시스템은 정상 작동합니다


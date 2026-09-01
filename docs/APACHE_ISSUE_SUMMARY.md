# Apache 웹서버 재시작 루프 문제 요약

## 문제 상황
- Apache 컨테이너가 계속 재시작됨
- 오류: `AH00025: configuration error: couldn't check user: /`
- Apache가 요청 처리 시 사용자 확인 실패

## 시도한 해결 방법
1. ✅ 모듈 로드 확인 (proxy, proxy_http, headers)
2. ✅ User/Group 설정 수정 (daemon, root)
3. ✅ CustomLog 설정 제거/수정
4. ✅ 기본 httpd.conf 사용 + VirtualHost 추가
5. ❌ 문제 지속

## 현재 상태
- ✅ Streamlit 대시보드: 정상 작동 (http://localhost:8501)
- ❌ Apache Reverse Proxy: 비활성화됨

## 해결 방안

### 옵션 1: Streamlit 직접 접근 (현재 사용 중) ✅
- **장점**: 즉시 사용 가능, 모든 기능 정상 작동
- **접속**: http://localhost:8501
- **상태**: 정상 작동 중

### 옵션 2: Nginx로 변경
- Nginx는 Apache보다 설정이 간단하고 안정적
- `apache/nginx.conf` 파일 준비됨
- docker-compose.yml에서 Apache를 Nginx로 교체 가능

### 옵션 3: Apache 문제 계속 해결
- Alpine Linux httpd 이미지의 알려진 이슈일 수 있음
- 더 깊은 조사 필요

## 권장 사항
**현재는 Streamlit 직접 접근 사용을 권장합니다.**
- Apache는 Reverse Proxy 역할만 수행
- 모든 기능은 Streamlit 직접 접근으로 사용 가능
- 필요시 나중에 Nginx로 대체 가능

## Nginx로 변경하는 방법
1. docker-compose.yml에서 web-server 서비스를 Nginx로 변경
2. nginx.conf 파일 사용
3. 컨테이너 재빌드 및 시작




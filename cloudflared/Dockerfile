FROM ngrok/ngrok:latest

# ngrok 설정 파일 복사
COPY ngrok.yml /etc/ngrok.yml

# ngrok을 통해 deep-guardian-web:80을 외부에 노출
# 외부 URL이 자동으로 생성되어 로그에 표시됩니다
ENTRYPOINT ["ngrok", "http", "deep-guardian-web:80", "--config", "/etc/ngrok.yml", "--log=stdout"]


FROM ubuntu:22.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV APACHE_RUN_USER=www-data
ENV APACHE_RUN_GROUP=www-data

WORKDIR /var/www

# 시스템 패키지 설치 (Apache, MySQL, Python, PHP)
RUN apt-get update && apt-get install -y \
    apache2 \
    mysql-server \
    python3.10 \
    python3-pip \
    python3-dev \
    php \
    php-mysql \
    php-curl \
    php-json \
    libapache2-mod-php \
    libapache2-mod-wsgi-py3 \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Apache 모듈 활성화
RUN a2enmod rewrite \
    && a2enmod proxy \
    && a2enmod proxy_http \
    && a2enmod headers \
    && a2enmod wsgi

# Python 패키지 설치
COPY app/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 웹 파일 복사
COPY web/ /var/www/html/
COPY app/ /var/www/app/

# Apache 설정
COPY apache-config.conf /etc/apache2/sites-available/000-default.conf
RUN a2ensite 000-default.conf

# MySQL 초기화 스크립트 준비
RUN mkdir -p /docker-entrypoint-initdb.d

# MySQL 시작 스크립트 생성
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# MySQL 시작\n\
service mysql start\n\
\n\
# 데이터베이스 초기화 대기\n\
sleep 10\n\
\n\
# 초기화 스크립트 실행\n\
if [ -f /docker-entrypoint-initdb.d/init.sql ]; then\n\
    mysql -u root -p${MYSQL_ROOT_PASSWORD:-root_password} < /docker-entrypoint-initdb.d/init.sql 2>/dev/null || true\n\
    mysql -u root -p${MYSQL_ROOT_PASSWORD:-root_password} -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE:-pothole_db};" 2>/dev/null || true\n\
    mysql -u root -p${MYSQL_ROOT_PASSWORD:-root_password} -e "CREATE USER IF NOT EXISTS '\''${MYSQL_USER:-pothole_user}'\''@'\''%'\'' IDENTIFIED BY '\''${MYSQL_PASSWORD:-pothole_pass}'\'';" 2>/dev/null || true\n\
    mysql -u root -p${MYSQL_ROOT_PASSWORD:-root_password} -e "GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE:-pothole_db}.* TO '\''${MYSQL_USER:-pothole_user}'\''@'\''%'\'';" 2>/dev/null || true\n\
    mysql -u root -p${MYSQL_ROOT_PASSWORD:-root_password} -e "FLUSH PRIVILEGES;" 2>/dev/null || true\n\
fi\n\
\n\
# Apache 시작\n\
apache2ctl -D FOREGROUND\n\
' > /start.sh && chmod +x /start.sh

# 포트 노출
EXPOSE 80 3306

# 시작 스크립트 실행
CMD ["/bin/bash", "/start.sh"]


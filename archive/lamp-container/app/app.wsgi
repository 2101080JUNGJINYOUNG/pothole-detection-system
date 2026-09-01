#!/usr/bin/env python3
import sys
import os

# 경로 추가
sys.path.insert(0, '/var/www/app')

# 환경 변수 설정
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_app.settings'

# Flask 애플리케이션 import
from app import app as application

if __name__ == "__main__":
    application.run()


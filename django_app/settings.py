"""
Django settings for Deep-Guardian project
"""
import os
from pathlib import Path

# Use pymysql instead of mysqlclient
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-deep-guardian-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_app',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'django_app.urls'

TEMPLATES = []

WSGI_APPLICATION = 'django_app.wsgi.application'

# Database
# Parse DATABASE_URL or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://pothole_user:pothole_pass@db:5432/pothole_db')

# Parse database URL (MySQL or PostgreSQL)
if DATABASE_URL.startswith('mysql://'):
    import re
    match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        user, password, host, port, dbname = match.groups()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': dbname,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
                'OPTIONS': {
                    'charset': 'utf8mb4',
                }
            }
        }
    else:
        # Fallback to default MySQL
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'pothole_db',
                'USER': 'pothole_user',
                'PASSWORD': 'pothole_pass',
                'HOST': 'lamp',
                'PORT': '3306',
                'OPTIONS': {
                    'charset': 'utf8mb4',
                }
            }
        }
elif DATABASE_URL.startswith('postgresql://'):
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        user, password, host, port, dbname = match.groups()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': dbname,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
            }
        }
    else:
        # Fallback to default PostgreSQL
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'pothole_db',
                'USER': 'pothole_user',
                'PASSWORD': 'pothole_pass',
                'HOST': 'db',
                'PORT': '5432',
            }
        }
else:
    # Default to MySQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'pothole_db',
            'USER': 'pothole_user',
            'PASSWORD': 'pothole_pass',
            'HOST': 'lamp',
            'PORT': '3306',
            'OPTIONS': {
                'charset': 'utf8mb4',
            }
        }
    }

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'UTC'  # Changed from 'Asia/Seoul' to avoid tzlocal issues
USE_I18N = True
USE_TZ = True

# Don't use migrations (we're using existing database)
# Set to False to prevent Django from creating migrations
MIGRATIONS_MODULES = {
    'django_app': None,
}



"""
기본 사용자 계정 생성 스크립트
"""

import os
import sys
import django

# Django setup
django_app_path_in_container = '/var/www/app/django_app'
if os.path.exists(django_app_path_in_container):
    if '/var/www/app' not in sys.path:
        sys.path.insert(0, '/var/www/app')
else:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django_app.models import User
from auth import hash_password

def create_default_users():
    """기본 사용자 계정 생성"""
    # 관리자 계정
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'role': 'admin',
            'is_active': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"[OK] 관리자 계정 생성: admin / admin123")
    else:
        print(f"[INFO] 관리자 계정 이미 존재: admin")
    
    # 일반 사용자 계정
    user, created = User.objects.get_or_create(
        username='user',
        defaults={
            'role': 'user',
            'is_active': True
        }
    )
    if created:
        user.set_password('user123')
        user.save()
        print(f"[OK] 일반 사용자 계정 생성: user / user123")
    else:
        print(f"[INFO] 일반 사용자 계정 이미 존재: user")

if __name__ == '__main__':
    create_default_users()


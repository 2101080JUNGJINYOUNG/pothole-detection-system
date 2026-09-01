"""
기본 사용자 계정 생성 스크립트
Django ORM을 사용하여 실제 bcrypt 해시를 생성하여 데이터베이스에 저장
"""

import sys
import os
import django

# Django setup
django_app_path_in_container = '/app/django_app'  # Docker 컨테이너에서 마운트된 경로
if os.path.exists(django_app_path_in_container):
    # Docker 컨테이너 환경
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')
else:
    # 로컬 환경
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django_app.models import User

def create_default_users():
    """기본 사용자 계정 생성 using Django ORM"""
    try:
        # 관리자 계정 (비밀번호: admin123)
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'admin', 'is_active': True}
        )
        if not created:
            # 이미 존재하는 경우 비밀번호 업데이트
            admin.set_password('admin123')
            admin.role = 'admin'
            admin.is_active = True
        else:
            admin.set_password('admin123')
        admin.save()
        print(f"[OK] 관리자 계정 {'생성' if created else '업데이트'}: admin / admin123")
        
        # 일반 사용자 계정 (비밀번호: user123)
        user, created = User.objects.get_or_create(
            username='user',
            defaults={'role': 'user', 'is_active': True}
        )
        if not created:
            # 이미 존재하는 경우 비밀번호 업데이트
            user.set_password('user123')
            user.role = 'user'
            user.is_active = True
        else:
            user.set_password('user123')
        user.save()
        print(f"[OK] 일반 사용자 계정 {'생성' if created else '업데이트'}: user / user123")
        
        print("\n[OK] 기본 사용자 계정이 생성되었습니다.")
        print("  - 관리자: admin / admin123")
        print("  - 일반 사용자: user / user123")
        
    except Exception as e:
        print(f"[ERROR] 사용자 계정 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_default_users()





"""
인증 모듈 (Flask 버전)
사용자 로그인 및 권한 관리
"""

import bcrypt
from datetime import datetime
from functools import wraps
from flask import session, request, jsonify

def hash_password(password):
    """비밀번호 해시화"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """비밀번호 검증"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def authenticate_user(username, password):
    """사용자 인증 using Django ORM"""
    try:
        from django_app.models import User
        user = User.objects.get(username=username)
        
        if not user.is_active:
            return None
        
        if user.check_password(password):
            # 마지막 로그인 시간 업데이트
            update_last_login(user.id)
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        else:
            return None
    except Exception:
        return None

def update_last_login(user_id):
    """마지막 로그인 시간 업데이트"""
    try:
        from django_app.models import User
        user = User.objects.get(id=user_id)
        user.last_login = datetime.now()
        user.save(update_fields=['last_login'])
    except Exception:
        pass

def check_authentication():
    """인증 상태 확인"""
    return session.get('authenticated', False)

def get_current_user():
    """현재 로그인한 사용자 정보"""
    if check_authentication():
        return session.get('user')
    return None

def is_admin():
    """관리자 여부 확인"""
    user = get_current_user()
    return user and user.get('role') == 'admin'

def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_authentication():
            return jsonify({'error': '로그인이 필요합니다'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """관리자 권한 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_authentication():
            return jsonify({'error': '로그인이 필요합니다'}), 401
        if not is_admin():
            return jsonify({'error': '관리자 권한이 필요합니다'}), 403
        return f(*args, **kwargs)
    return decorated_function


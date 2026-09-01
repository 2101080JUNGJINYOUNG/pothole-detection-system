"""
인증 모듈
사용자 로그인 및 권한 관리
"""

import streamlit as st
import time
from datetime import datetime
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

def hash_password(password):
    """비밀번호 해시화"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """비밀번호 검증"""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        return False

def authenticate_user(username, password):
    """사용자 인증 using Django ORM"""
    try:
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
    except User.DoesNotExist:
        return None
    except Exception as e:
        st.error(f"인증 오류: {str(e)}")
        return None

def update_last_login(user_id):
    """마지막 로그인 시간 업데이트"""
    try:
        user = User.objects.get(id=user_id)
        user.last_login = datetime.now()
        user.save(update_fields=['last_login'])
    except Exception as e:
        pass  # 로그인 시간 업데이트 실패는 무시

def check_authentication():
    """인증 상태 확인"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
    
    return st.session_state.authenticated

def is_admin():
    """관리자 여부 확인"""
    if not check_authentication():
        return False
    return st.session_state.user and st.session_state.user.get('role') == 'admin'

def login_page():
    """로그인 페이지"""
    st.title("🔐 Deep-Guardian 로그인")
    
    # 기본 사용자 계정 생성 시도
    try:
        from create_default_users import create_default_users
        create_default_users()
    except Exception as e:
        pass  # 이미 생성되었거나 오류 발생 시 무시
    
    with st.form("login_form"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submit_button = st.form_submit_button("로그인", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("사용자명과 비밀번호를 입력해주세요.")
            else:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"환영합니다, {user['username']}님!")
                    time.sleep(0.5)  # 성공 메시지 표시를 위한 짧은 대기
                    st.rerun()
                else:
                    st.error("사용자명 또는 비밀번호가 올바르지 않습니다.")
    
    # 기본 계정 정보 표시 (개발용)
    with st.expander("기본 계정 정보 (개발용)"):
        st.info("""
        **관리자 계정:**
        - 사용자명: admin
        - 비밀번호: admin123
        
        **일반 사용자 계정:**
        - 사용자명: user
        - 비밀번호: user123
        
        ⚠️ 실제 운영 환경에서는 반드시 비밀번호를 변경하세요!
        """)

def logout():
    """로그아웃"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


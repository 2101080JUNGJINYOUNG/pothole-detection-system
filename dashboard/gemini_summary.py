"""
Google Gemini를 사용한 포트홀 데이터 요약 기능
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Generative AI가 설치되지 않았습니다. pip install google-generativeai를 실행하세요.")


def get_gemini_api_key() -> Optional[str]:
    """Gemini API 키 가져오기"""
    return os.getenv('GEMINI_API_KEY', None)


def check_gemini_connection() -> bool:
    """Gemini API 연결 확인"""
    if not GEMINI_AVAILABLE:
        return False
    
    api_key = get_gemini_api_key()
    if not api_key:
        return False
    
    try:
        genai.configure(api_key=api_key)
        # 간단한 모델 목록 조회로 연결 테스트
        models = genai.list_models()
        return True
    except Exception as e:
        print(f"Gemini 연결 확인 실패: {str(e)}")
        return False


def get_default_model() -> str:
    """기본 Gemini 모델 이름"""
    # 사용 가능한 모델: gemini-2.0-flash (빠름), gemini-2.5-pro (정확), gemini-pro (구버전)
    return os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')  # 기본 모델 (빠른 응답)


def format_pothole_data_for_summary(potholes: List) -> str:
    """
    포트홀 데이터를 요약을 위한 텍스트 형식으로 변환
    
    Args:
        potholes: Pothole 객체 리스트 또는 딕셔너리 리스트
        
    Returns:
        str: 포맷된 텍스트
    """
    if not potholes:
        return "포트홀 데이터가 없습니다."
    
    lines = [f"총 {len(potholes)}개의 포트홀이 탐지되었습니다.\n"]
    
    # 위험도별 통계
    risk_stats = {}
    location_stats = {}
    total_depth = 0.0
    validated_count = 0
    
    for p in potholes:
        # 위험도 통계
        risk_level = getattr(p, 'risk_level', 'medium') if hasattr(p, 'risk_level') else p.get('risk_level', 'medium')
        risk_stats[risk_level] = risk_stats.get(risk_level, 0) + 1
        
        # 위치 유형 통계
        location_type = getattr(p, 'location_type', 'general') if hasattr(p, 'location_type') else p.get('location_type', 'general')
        location_stats[location_type] = location_stats.get(location_type, 0) + 1
        
        # 깊이 합계
        depth_ratio = float(getattr(p, 'depth_ratio', 0)) if hasattr(p, 'depth_ratio') else float(p.get('depth_ratio', 0))
        total_depth += depth_ratio
        
        # 검증 통과 수
        validation = getattr(p, 'validation_result', False) if hasattr(p, 'validation_result') else p.get('validation_result', False)
        if validation:
            validated_count += 1
    
    lines.append("=== 통계 정보 ===")
    lines.append(f"검증 통과: {validated_count}개 ({validated_count/len(potholes)*100:.1f}%)")
    lines.append(f"평균 깊이 비율: {total_depth/len(potholes):.3f}")
    
    lines.append("\n=== 위험도 분포 ===")
    for risk, count in sorted(risk_stats.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {risk}: {count}개 ({count/len(potholes)*100:.1f}%)")
    
    lines.append("\n=== 위치 유형 분포 ===")
    for loc_type, count in sorted(location_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        lines.append(f"- {loc_type}: {count}개")
    
    # 최근 상위 3개 포트홀만 표시 (토큰 절약)
    lines.append("\n=== 주요 포트홀 (우선순위 상위 3개) ===")
    sorted_potholes = sorted(
        potholes, 
        key=lambda x: float(getattr(x, 'priority_score', 0)) if hasattr(x, 'priority_score') else float(x.get('priority_score', 0)),
        reverse=True
    )[:3]  # 5개 → 3개로 감소
    
    for i, p in enumerate(sorted_potholes, 1):
        priority = float(getattr(p, 'priority_score', 0)) if hasattr(p, 'priority_score') else float(p.get('priority_score', 0))
        risk = getattr(p, 'risk_level', 'medium') if hasattr(p, 'risk_level') else p.get('risk_level', 'medium')
        loc_type = getattr(p, 'location_type', 'general') if hasattr(p, 'location_type') else p.get('location_type', 'general')
        
        lines.append(f"{i}. 우선순위:{priority:.1f}, 위험도:{risk}, 위치:{loc_type}")  # 깊이 제거로 간소화
    
    return "\n".join(lines)


def generate_summary_with_gemini(potholes: List, model: Optional[str] = None) -> Dict:
    """
    Google Gemini를 사용하여 포트홀 데이터 요약 생성
    
    Args:
        potholes: Pothole 객체 리스트
        model: 사용할 Gemini 모델 (None이면 기본값 사용)
        
    Returns:
        dict: {'success': bool, 'summary': str, 'error': str}
    """
    if not GEMINI_AVAILABLE:
        return {
            'success': False,
            'error': 'Google Generative AI가 설치되지 않았습니다. pip install google-generativeai를 실행하세요.'
        }
    
    api_key = get_gemini_api_key()
    if not api_key:
        return {
            'success': False,
            'error': 'Gemini API 키가 설정되지 않았습니다. GEMINI_API_KEY 환경 변수를 설정하세요.'
        }
    
    if not check_gemini_connection():
        return {
            'success': False,
            'error': 'Gemini API에 연결할 수 없습니다. API 키를 확인하세요.'
        }
    
    if not potholes:
        return {
            'success': False,
            'error': '요약할 포트홀 데이터가 없습니다.'
        }
    
    try:
        # Gemini API 설정
        genai.configure(api_key=api_key)
        
        # 데이터 포맷팅
        formatted_data = format_pothole_data_for_summary(potholes)
        
        # 프롬프트 생성 (간결하게)
        prompt = f"""포트홀 탐지 데이터 요약 (한국어, 3-5줄):

{formatted_data}"""
        
        # Gemini API 호출
        model_name = model or get_default_model()
        
        # 모델 이름 정규화: models/ 접두사가 있으면 제거 (GenerativeModel은 접두사 없이 사용)
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        # 구버전 모델 이름을 최신 버전으로 자동 변환
        if model_name == 'gemini-1.5-flash':
            model_name = 'gemini-2.0-flash'
        elif model_name == 'gemini-1.5-pro':
            model_name = 'gemini-2.5-pro'
        
        # 모델 생성
        gemini_model = genai.GenerativeModel(model_name)
        
        # 요약 생성 (재시도 로직 포함 - 429 Too Many Requests 처리)
        import time
        max_retries = 5  # 재시도 횟수 증가 (3 → 5)
        base_retry_delay = 10  # 기본 대기 시간 증가 (8초 → 10초)
        summary = None
        
        for attempt in range(max_retries):
            try:
                response = gemini_model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 300,  # 토큰 수 감소 (할당량 절약)
                    }
                )
                summary = response.text.strip() if hasattr(response, 'text') else str(response).strip()
                break  # 성공하면 루프 종료
            except Exception as e:
                error_msg = str(e)
                
                # 429 Too Many Requests 또는 할당량 초과 오류인 경우
                is_rate_limit_error = (
                    '429' in error_msg or 
                    'quota' in error_msg.lower() or 
                    'Quota exceeded' in error_msg or
                    'Too Many Requests' in error_msg or
                    'rate limit' in error_msg.lower()
                )
                
                if is_rate_limit_error:
                    if attempt < max_retries - 1:
                        # 지수 백오프: 재시도 횟수가 늘어날수록 대기 시간 증가
                        retry_delay = base_retry_delay * (2 ** attempt)  # 10초, 20초, 40초, 80초...
                        # 최대 60초로 제한
                        retry_delay = min(retry_delay, 60)
                        
                        # 마지막 시도가 아니면 재시도
                        continue
                    else:
                        # 최대 재시도 횟수 초과
                        return {
                            'success': False,
                            'error': f'⚠️ 429 Too Many Requests: Gemini API 할당량이 초과되었습니다.\n\n'
                                    f'재시도 ({max_retries}회) 후에도 실패했습니다.\n\n'
                                    f'**무료 티어 제한:**\n'
                                    f'- 분당 요청 수 제한\n'
                                    f'- 일일 토큰 수 제한\n\n'
                                    f'**해결 방법:**\n'
                                    f'1. 5-10분 후 다시 시도 (할당량이 리셋될 때까지 대기)\n'
                                    f'2. Google Cloud Console에서 할당량 확인: https://ai.dev/usage\n'
                                    f'3. 요청 간격을 두고 사용 (너무 빠르게 연속 요청하지 않기)\n'
                                    f'4. 유료 플랜으로 업그레이드 (더 높은 할당량)'
                        }
                else:
                    # 다른 오류인 경우 즉시 실패 (재시도 안 함)
                    raise
        
        if not summary:
            return {
                'success': False,
                'error': 'Gemini로부터 요약을 받지 못했습니다.'
            }
        
        return {
            'success': True,
            'summary': summary,
            'model': model_name,
            'data_count': len(potholes)
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # API 키 오류인 경우
        if 'API_KEY' in error_msg or '401' in error_msg or '403' in error_msg:
            error_msg = 'Gemini API 키가 유효하지 않습니다. API 키를 확인하세요.'
        # 429 Too Many Requests 또는 할당량 초과 오류인 경우
        elif '429' in error_msg or 'quota' in error_msg.lower() or 'Quota exceeded' in error_msg or 'Too Many Requests' in error_msg:
            error_msg = ('⚠️ 429 Too Many Requests: Gemini API 할당량이 초과되었습니다.\n\n'
                        '무료 티어는 제한이 있습니다. 5-10분 후 다시 시도하거나 Google Cloud Console에서 할당량을 확인하세요.')
        
        return {
            'success': False,
            'error': f'요약 생성 중 오류 발생: {error_msg}'
        }


def generate_daily_summary() -> Dict:
    """
    오늘의 포트홀 데이터 요약 생성
    
    Returns:
        dict: 요약 결과
    """
    try:
        # Django ORM import
        import sys
        import os
        import django
        
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
        
        from django_app.models import Pothole
        from django.db.models import Q
        
        # 오늘 날짜의 데이터 조회
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        potholes = list(Pothole.objects.filter(
            detected_at__gte=today_start,
            detected_at__lt=today_end,
            approved_for_training=True
        ).order_by('-priority_score')[:50])  # 최대 50개
        
        return generate_summary_with_gemini(potholes)
        
    except Exception as e:
        return {
            'success': False,
            'error': f'데이터 조회 중 오류 발생: {str(e)}'
        }


def generate_custom_summary(days: int = 7, limit: int = 100, min_priority: float = 0.0) -> Dict:
    """
    사용자 지정 조건으로 포트홀 데이터 요약 생성
    
    Args:
        days: 최근 N일 데이터
        limit: 최대 조회 개수
        min_priority: 최소 우선순위 점수
        
    Returns:
        dict: 요약 결과
    """
    try:
        # Django ORM import
        import sys
        import os
        import django
        
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
        
        from django_app.models import Pothole
        from django.db.models import Q
        
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 데이터 조회
        queryset = Pothole.objects.filter(
            detected_at__gte=start_date,
            detected_at__lte=end_date,
            approved_for_training=True,
            priority_score__gte=min_priority
        ).order_by('-priority_score')[:limit]
        
        potholes = list(queryset)
        
        return generate_summary_with_gemini(potholes)
        
    except Exception as e:
        return {
            'success': False,
            'error': f'데이터 조회 중 오류 발생: {str(e)}'
        }


"""
Ollama를 사용한 포트홀 데이터 요약 기능
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama가 설치되지 않았습니다. pip install ollama를 실행하세요.")


def get_ollama_base_url():
    """Ollama 서버 URL 가져오기"""
    # Docker 컨테이너에서는 host.docker.internal 사용
    default_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    # Docker 환경에서 localhost를 host.docker.internal로 변환
    if 'localhost' in default_url and os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true':
        default_url = default_url.replace('localhost', 'host.docker.internal')
    return default_url


def check_ollama_connection() -> bool:
    """Ollama 서버 연결 확인"""
    if not OLLAMA_AVAILABLE:
        return False
    
    try:
        import requests
        base_url = get_ollama_base_url()
        # Docker 컨테이너에서 호스트 접근을 위한 URL 처리
        if base_url.startswith('http://localhost'):
            # Docker 컨테이너에서는 host.docker.internal 사용
            base_url = base_url.replace('localhost', 'host.docker.internal')
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Ollama 연결 확인 실패: {str(e)}")
        return False


def get_default_model() -> str:
    """기본 Ollama 모델 이름"""
    return os.getenv('OLLAMA_MODEL', 'llama3.2:1b')  # 작은 모델로 빠른 응답


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
    
    # 최근 상위 5개 포트홀 상세 정보
    lines.append("\n=== 주요 포트홀 (우선순위 상위 5개) ===")
    sorted_potholes = sorted(
        potholes, 
        key=lambda x: float(getattr(x, 'priority_score', 0)) if hasattr(x, 'priority_score') else float(x.get('priority_score', 0)),
        reverse=True
    )[:5]
    
    for i, p in enumerate(sorted_potholes, 1):
        priority = float(getattr(p, 'priority_score', 0)) if hasattr(p, 'priority_score') else float(p.get('priority_score', 0))
        risk = getattr(p, 'risk_level', 'medium') if hasattr(p, 'risk_level') else p.get('risk_level', 'medium')
        loc_type = getattr(p, 'location_type', 'general') if hasattr(p, 'location_type') else p.get('location_type', 'general')
        depth = float(getattr(p, 'depth_ratio', 0)) if hasattr(p, 'depth_ratio') else float(p.get('depth_ratio', 0))
        
        lines.append(f"{i}. 우선순위: {priority:.2f}, 위험도: {risk}, 위치: {loc_type}, 깊이: {depth:.3f}")
    
    return "\n".join(lines)


def generate_summary_with_ollama(potholes: List, model: Optional[str] = None) -> Dict:
    """
    Ollama를 사용하여 포트홀 데이터 요약 생성
    
    Args:
        potholes: Pothole 객체 리스트
        model: 사용할 Ollama 모델 (None이면 기본값 사용)
        
    Returns:
        dict: {'success': bool, 'summary': str, 'error': str}
    """
    if not OLLAMA_AVAILABLE:
        return {
            'success': False,
            'error': 'Ollama가 설치되지 않았습니다. pip install ollama를 실행하세요.'
        }
    
    if not check_ollama_connection():
        return {
            'success': False,
            'error': 'Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요.'
        }
    
    if not potholes:
        return {
            'success': False,
            'error': '요약할 포트홀 데이터가 없습니다.'
        }
    
    try:
        # 데이터 포맷팅
        formatted_data = format_pothole_data_for_summary(potholes)
        
        # 프롬프트 생성
        prompt = f"""다음은 포트홀 탐지 시스템에서 수집한 데이터입니다. 
이 데이터를 바탕으로 간단하고 명확한 요약을 한국어로 작성해주세요.
요약에는 주요 통계, 위험도 분석, 주의가 필요한 포트홀 정보를 포함해주세요.

데이터:
{formatted_data}

요약 (3-5줄):"""
        
        # Ollama API 호출
        model_name = model or get_default_model()
        base_url = get_ollama_base_url()
        
        # ollama Client 사용 (base_url 설정 지원)
        try:
            # ollama.Client를 사용하여 base_url 설정
            client = ollama.Client(host=base_url)
            response = client.generate(
                model=model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'num_predict': 300,  # 최대 토큰 수
                }
            )
            summary = response.get('response', '').strip()
        except (AttributeError, TypeError):
            # Client가 없거나 다른 방식인 경우 기본 방법 사용
            response = ollama.generate(
                model=model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'num_predict': 300,
                }
            )
            summary = response.get('response', '').strip() if isinstance(response, dict) else str(response).strip()
        
        if not summary:
            return {
                'success': False,
                'error': 'Ollama로부터 요약을 받지 못했습니다.'
            }
        
        return {
            'success': True,
            'summary': summary,
            'model': model_name,
            'data_count': len(potholes)
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f'요약 생성 중 오류 발생: {str(e)}\n{traceback.format_exc()}'
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
        
        return generate_summary_with_ollama(potholes)
        
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
        
        return generate_summary_with_ollama(potholes)
        
    except Exception as e:
        return {
            'success': False,
            'error': f'데이터 조회 중 오류 발생: {str(e)}'
        }


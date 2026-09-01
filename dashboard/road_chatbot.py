"""
도로 포트홀 데이터 대화형 질의응답 챗봇
SLM (Small Language Model)을 사용하여 자연어로 포트홀 데이터 조회 및 답변
"""

import os
import sys
import django
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# Django setup
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    django_app_path_in_container = '/app/django_app'
    if os.path.exists(django_app_path_in_container):
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
    else:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
    django.setup()

from django_app.models import Pothole, User
from django.db.models import Q, Count, Avg, Max, Min
from django.db.models.functions import TruncDate

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama가 설치되지 않았습니다. pip install ollama를 실행하세요.")


class RoadChatbot:
    """도로 포트홀 데이터 대화형 챗봇"""
    
    def __init__(self, model_name: str = "llama3.2", ollama_url: Optional[str] = None):
        """
        Args:
            model_name: 사용할 Ollama 모델 이름 (기본값: llama3.2)
            ollama_url: Ollama 서버 URL (기본값: http://localhost:11434)
        """
        self.model_name = model_name or os.getenv('OLLAMA_MODEL', 'llama3.2')
        self.ollama_url = ollama_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.available = OLLAMA_AVAILABLE
        
        if self.available:
            try:
                # Ollama 연결 테스트
                ollama.list()
                self.available = True
            except Exception as e:
                # 연결 실패해도 초기화는 성공
                pass
    
    def check_connection(self) -> bool:
        """Ollama 연결 확인"""
        if not self.available:
            return False
            try:
                ollama.list()
                return True
            except Exception as e:
                return False
    
    def get_today_detections(self) -> List:
        """오늘 탐지된 포트홀 데이터 조회"""
        today = datetime.now().date()
        return Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).order_by('-priority_score')
    
    def get_most_dangerous_today(self) -> Optional[Dict]:
        """오늘 가장 위험한 포트홀 조회"""
        today_detections = self.get_today_detections()
        if not today_detections.exists():
            return None
        
        most_dangerous = today_detections.first()
        return {
            'id': most_dangerous.id,
            'risk_level': most_dangerous.risk_level,
            'priority_score': float(most_dangerous.priority_score),
            'depth_ratio': float(most_dangerous.depth_ratio),
            'location_description': most_dangerous.location_description or f"위도: {most_dangerous.latitude}, 경도: {most_dangerous.longitude}",
            'image_path': most_dangerous.image_path,
            'detected_at': most_dangerous.detected_at
        }
    
    def get_statistics_today(self) -> Dict:
        """오늘 통계 데이터 조회"""
        today = datetime.now().date()
        
        total_count = Pothole.objects.filter(detected_at__date=today).count()
        validated_count = Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).count()
        
        risk_distribution = Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).values('risk_level').annotate(count=Count('id'))
        
        avg_depth = Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).aggregate(avg_depth=Avg('depth_ratio'))['avg_depth'] or 0.0
        
        max_priority = Pothole.objects.filter(
            detected_at__date=today,
            validation_result=True
        ).aggregate(max_priority=Max('priority_score'))['max_priority'] or 0.0
        
        return {
            'total_count': total_count,
            'validated_count': validated_count,
            'risk_distribution': {item['risk_level']: item['count'] for item in risk_distribution},
            'avg_depth_ratio': float(avg_depth) if avg_depth else 0.0,
            'max_priority_score': float(max_priority) if max_priority else 0.0
        }
    
    def get_data_by_location(self, location_keyword: str) -> List[Dict]:
        """위치 키워드로 포트홀 데이터 조회"""
        query = Q(validation_result=True)
        
        # 위치 설명에서 검색
        if location_keyword:
            query &= Q(location_description__icontains=location_keyword)
        
        potholes = Pothole.objects.filter(query).order_by('-priority_score')[:10]
        
        return [{
            'id': p.id,
            'location': p.location_description or f"위도: {p.latitude}, 경도: {p.longitude}",
            'risk_level': p.risk_level,
            'priority_score': float(p.priority_score),
            'depth_ratio': float(p.depth_ratio),
            'detected_at': p.detected_at
        } for p in potholes]
    
    def format_context_for_llm(self, question: str, relevant_data: Dict = None) -> str:
        """
        LLM에 제공할 컨텍스트 데이터 포맷팅 (조회된 데이터 기반)
        
        Args:
            question: 사용자 질문
            relevant_data: query_relevant_data()로 조회된 데이터 (없으면 자동 조회)
        """
        if relevant_data is None:
            relevant_data = self.query_relevant_data(question)
        
        context_parts = []
        
        if relevant_data['stats']:
            stats = relevant_data['stats']
            context_parts.append(f"오늘 탐지된 포트홀 통계:")
            context_parts.append(f"- 총 탐지 건수: {stats['total_count']}건")
            context_parts.append(f"- 검증 통과: {stats['validated_count']}건")
            context_parts.append(f"- 평균 깊이 비율: {stats['avg_depth_ratio']:.3f}")
            context_parts.append(f"- 최대 우선순위 점수: {stats['max_priority_score']:.2f}")
            
            if stats['risk_distribution']:
                context_parts.append(f"\n위험도 분포:")
                for risk, count in stats['risk_distribution'].items():
                    context_parts.append(f"- {risk}: {count}건")
        
        if relevant_data['most_dangerous']:
            md = relevant_data['most_dangerous']
            context_parts.append(f"\n가장 위험한 포트홀 (오늘):")
            context_parts.append(f"- ID: {md['id']}")
            context_parts.append(f"- 위험도: {md['risk_level']}")
            context_parts.append(f"- 우선순위 점수: {md['priority_score']:.2f}")
            context_parts.append(f"- 깊이 비율: {md['depth_ratio']:.3f}")
            context_parts.append(f"- 위치: {md['location_description']}")
            if md.get('image_path'):
                context_parts.append(f"- 이미지: {md['image_path']}")
        
        if relevant_data['relevant_potholes']:
            context_parts.append(f"\n관련 포트홀:")
            for p in relevant_data['relevant_potholes'][:5]:  # 최대 5개만
                context_parts.append(f"- 위치: {p['location']}, 위험도: {p['risk_level']}, 점수: {p['priority_score']:.2f}")
        
        return "\n".join(context_parts) if context_parts else "데이터 없음"
    
    def extract_keywords_from_question(self, question: str) -> Dict:
        """
        질문에서 키워드를 추출하여 적절한 데이터 조회 전략 결정
        
        Returns:
            {
                'query_type': 'today_stats' | 'most_dangerous' | 'location' | 'general',
                'keywords': ['키워드1', '키워드2'],
                'time_filter': 'today' | 'week' | 'month' | 'all'
            }
        """
        question_lower = question.lower()
        
        # 시간 키워드 추출
        time_filter = 'today'  # 기본값
        if any(kw in question_lower for kw in ['오늘', '금일', 'today']):
            time_filter = 'today'
        elif any(kw in question_lower for kw in ['어제', 'yesterday']):
            time_filter = 'yesterday'
        elif any(kw in question_lower for kw in ['이번 주', '주간', 'week']):
            time_filter = 'week'
        elif any(kw in question_lower for kw in ['이번 달', '월간', 'month']):
            time_filter = 'month'
        
        # 질문 유형 판단
        query_type = 'general'
        keywords = []
        
        # 가장 위험한 포트홀 관련
        if any(kw in question_lower for kw in ['가장 위험', '가장 심각', '가장 심각한', '최고 위험', '최악']):
            query_type = 'most_dangerous'
            keywords.append('위험')
        
        # 위치 관련
        if any(kw in question_lower for kw in ['어디', '위치', '장소', '곳', '어느']):
            query_type = 'location'
            keywords.append('위치')
        
        # 통계 관련
        if any(kw in question_lower for kw in ['몇 개', '개수', '통계', '통계', '얼마나', '개수']):
            query_type = 'today_stats'
        
        # 위험도 관련
        if any(kw in question_lower for kw in ['critical', 'high', 'medium', 'low', '위험도']):
            keywords.append('위험도')
        
        return {
            'query_type': query_type,
            'keywords': keywords,
            'time_filter': time_filter
        }
    
    def query_relevant_data(self, question: str) -> Dict:
        """
        질문에 관련된 데이터를 직접 조회
        
        Returns:
            {
                'stats': 통계 데이터,
                'most_dangerous': 가장 위험한 포트홀,
                'relevant_potholes': 관련 포트홀 리스트,
                'summary': 요약 텍스트
            }
        """
        keywords_info = self.extract_keywords_from_question(question)
        result = {
            'stats': None,
            'most_dangerous': None,
            'relevant_potholes': [],
            'summary': ''
        }
        
        # 통계 데이터 (항상 수집)
        result['stats'] = self.get_statistics_today()
        
        # 가장 위험한 포트홀 (위험 관련 질문인 경우)
        if keywords_info['query_type'] in ['most_dangerous', 'location']:
            result['most_dangerous'] = self.get_most_dangerous_today()
        
        # 위치 관련 질문인 경우 추가 검색
        if keywords_info['query_type'] == 'location' and keywords_info['keywords']:
            # 질문에서 위치 키워드 추출 시도
            location_keywords = ['정문', '대학', '학교', '군산', '서울', '부산']
            for kw in location_keywords:
                if kw in question:
                    location_data = self.get_data_by_location(kw)
                    if location_data:
                        result['relevant_potholes'] = location_data
                        break
        
        return result
    
    def answer_question(self, question: str) -> Dict:
        """
        사용자 질문에 답변 생성
        
        Args:
            question: 사용자 질문
            
        Returns:
            {
                'answer': 답변 텍스트,
                'data': 관련 데이터 (있을 경우),
                'image_path': 관련 이미지 경로 (있을 경우)
            }
        """
        if not self.available:
            return {
                'answer': '죄송합니다. AI 챗봇이 현재 사용할 수 없습니다. Ollama가 설치되어 있고 실행 중인지 확인해주세요.',
                'data': None,
                'image_path': None
            }
        
        try:
            # 1. 먼저 질문에서 키워드 추출 및 관련 데이터 직접 조회
            relevant_data = self.query_relevant_data(question)
            
            # 2. 조회된 데이터를 기반으로 컨텍스트 생성
            context = self.format_context_for_llm(question, relevant_data)
            
            # 프롬프트 생성
            prompt = f"""당신은 도로 포트홀 탐지 시스템의 AI 어시스턴트입니다. 
사용자의 질문에 대해 제공된 데이터를 바탕으로 친절하고 정확하게 답변해주세요.

포트홀 데이터:
{context}

사용자 질문: {question}

답변 요구사항:
1. 한국어로 자연스럽고 친절하게 답변
2. 구체적인 숫자와 위치 정보 포함
3. 위험도나 우선순위가 높은 경우 강조
4. 이미지가 있는 경우 "사진을 확인해드릴까요?" 같은 제안 포함
5. 간결하고 명확하게 (3-5문장)

답변:"""
            
            # Ollama API 호출
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': '당신은 도로 포트홀 탐지 시스템의 AI 어시스턴트입니다. 제공된 데이터를 바탕으로 사용자의 질문에 정확하고 친절하게 답변합니다.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            answer_text = response['message']['content'].strip()
            
            # 조회된 관련 데이터 사용
            data = None
            image_path = None
            
            if relevant_data['most_dangerous']:
                data = relevant_data['most_dangerous']
                image_path = relevant_data['most_dangerous'].get('image_path')
            elif relevant_data['relevant_potholes'] and len(relevant_data['relevant_potholes']) > 0:
                # 첫 번째 관련 포트홀 사용
                data = relevant_data['relevant_potholes'][0]
                # image_path는 relevant_potholes에 포함되어 있지 않으므로 None
            
            return {
                'answer': answer_text,
                'data': data,
                'image_path': image_path
            }
            
        except Exception as e:
            return {
                'answer': f'죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}',
                'data': None,
                'image_path': None
            }
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 Ollama 모델 목록 조회"""
        if not self.available:
            return []
        
        try:
            models = ollama.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception:
            return []


def check_ollama_connection() -> bool:
    """Ollama 연결 확인"""
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def get_default_model() -> str:
    """기본 Ollama 모델 이름"""
    return os.getenv('OLLAMA_MODEL', 'llama3.2')

